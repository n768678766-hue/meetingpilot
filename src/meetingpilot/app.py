"""Streamlit entrypoint for MeetingPilot."""

from pathlib import Path
import sys

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import streamlit as st
from dotenv import load_dotenv

from meetingpilot.config import load_config
from meetingpilot.exporters import action_items_to_csv, to_markdown
from meetingpilot.llm_client import (
    ExtractionError,
    create_client,
    extract_meeting,
    extract_meeting_fallback,
)
from meetingpilot.models import BadCase, IssueType, MeetingResult, Priority, Severity
from meetingpilot.storage import (
    load_bad_cases,
    load_meeting_history,
    safe_filename_part,
    save_bad_case,
    save_meeting_result,
)

load_dotenv()

st.set_page_config(page_title="MeetingPilot", page_icon="MP", layout="wide")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_PATH = PROJECT_ROOT / "samples" / "sample-meeting.txt"

PRIORITY_LABELS = {
    Priority.HIGH: "高",
    Priority.MEDIUM: "中",
    Priority.LOW: "低",
}

SEVERITY_LABELS = {
    Severity.CRITICAL: "严重",
    Severity.MAJOR: "较高",
    Severity.MINOR: "较低",
}

ISSUE_TYPE_LABELS = {
    IssueType.OWNER_MISSING: "负责人缺失",
    IssueType.DUE_DATE_MISSING: "截止时间缺失",
    IssueType.TASK_SPLIT_TOO_BROAD: "任务拆分过粗",
    IssueType.DECISION_CONFUSED_WITH_ACTION: "决策和待办混淆",
    IssueType.RISK_POINT_OMITTED: "风险点遗漏",
    IssueType.HALLUCINATED_PERSON_OR_DATE: "虚构人物或日期",
    IssueType.OTHER: "其他",
}

# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------

if "config" not in st.session_state:
    st.session_state.config = load_config()
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "result" not in st.session_state:
    st.session_state.result: MeetingResult | None = None
if "client" not in st.session_state:
    cfg = st.session_state.config
    if cfg.api_key:
        try:
            st.session_state.client = create_client(cfg)
            st.session_state.client_error = ""
        except ExtractionError as exc:
            st.session_state.client = None
            st.session_state.client_error = str(exc)
    else:
        st.session_state.client = None
        st.session_state.client_error = ""

cfg = st.session_state.config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_sample() -> None:
    if SAMPLE_PATH.exists():
        st.session_state.transcript = SAMPLE_PATH.read_text(encoding="utf-8")
    else:
        st.error("未找到示例会议文本。")


def _refresh_config() -> None:
    load_dotenv(override=True)
    st.session_state.config = load_config()
    cfg = st.session_state.config
    if cfg.api_key:
        try:
            st.session_state.client = create_client(cfg)
            st.session_state.client_error = ""
            st.success(".env 已重新读取，模型配置已更新。")
        except ExtractionError as exc:
            st.session_state.client = None
            st.session_state.client_error = str(exc)
    else:
        st.session_state.client = None
        st.session_state.client_error = ""
        st.info("当前 .env 中没有 API Key，将继续使用本地演示模式。")


def _estimate_tokens(text: str) -> int:
    """Rough token estimate for mixed Chinese/English text."""
    cn = sum(1 for c in text if "一" <= c <= "鿿")
    other = len(text) - cn
    return int(cn * 1.5 + other * 0.3)


def _transcript_size_feedback(text: str) -> tuple[int, int, str, str]:
    """Return (char_count, token_estimate, status_message, severity)."""
    char_count = len(text)
    token_est = _estimate_tokens(text)

    if char_count == 0:
        return char_count, token_est, "", ""
    elif char_count <= 3000:
        return char_count, token_est, "文本长度适中，适合直接处理。", "info"
    elif char_count <= 10000:
        return (
            char_count,
            token_est,
            "文本较长，费用与延迟可能增加；建议删除无关闲聊或噪音后再处理。",
            "warning",
        )
    else:
        return (
            char_count,
            token_est,
            "文本很长，建议按主题或时间段切分后再逐段处理。",
            "warning",
        )


def _run_extraction() -> None:
    transcript = st.session_state.transcript.strip()
    if not transcript:
        st.error("请先粘贴会议转写文本。")
        return
    with st.spinner("正在生成结构化会议纪要..."):
        try:
            if st.session_state.client:
                result = extract_meeting(st.session_state.client, cfg.model, transcript)
            else:
                result = extract_meeting_fallback(transcript)
                st.info("未配置 API Key，已使用本地演示模式生成结果。")
            st.session_state.result = result
            save_meeting_result(result, DATA_DIR)
        except ExtractionError as exc:
            st.error(f"生成失败：{exc}")


def _record_bad_case(issue_type: IssueType, severity: Severity, expected: str, notes: str) -> None:
    result = st.session_state.result
    if result is None:
        st.error("当前没有可记录的会议结果。")
        return
    bc = BadCase(
        transcript_excerpt=st.session_state.transcript[:2000],
        expected_output=expected,
        actual_output=result.model_dump_json(indent=2),
        issue_type=issue_type,
        severity=severity,
        notes=notes,
    )
    path = save_bad_case(bc, DATA_DIR)
    st.success(f"Bad Case 已保存到 {path}")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("MeetingPilot")
    st.caption("AI 会议纪要与待办抽取助手")

    st.divider()

    st.subheader("模型配置")
    st.text_input("API Key", value="已配置" if cfg.api_key else "未配置", disabled=True)
    st.text_input("接口地址", value=cfg.base_url, disabled=True)
    st.text_input("模型", value=cfg.model, disabled=True)
    st.caption("在项目根目录的 .env 文件中设置。")
    st.button("重新读取 .env", on_click=_refresh_config, use_container_width=True)
    if st.session_state.client_error:
        st.warning(st.session_state.client_error)

    st.divider()

    st.subheader("历史纪要")
    history = load_meeting_history(DATA_DIR)
    if history:
        for i, item in enumerate(history):
            date_str = item.date or "未识别日期"
            with st.expander(f"{item.title} ({date_str})", expanded=False):
                st.text(item.summary[:300])
                if st.button("载入", key=f"load_{i}"):
                    st.session_state.result = item
                    st.rerun()
    else:
        st.caption("暂无已保存纪要。")

    st.divider()

    st.subheader("Bad Case 复盘")
    bad_cases = load_bad_cases(DATA_DIR)
    if bad_cases:
        for i, bc in enumerate(bad_cases):
            issue_label = ISSUE_TYPE_LABELS.get(bc.issue_type, bc.issue_type.value)
            severity_label = SEVERITY_LABELS.get(bc.severity, bc.severity.value)
            with st.expander(f"{issue_label} - {bc.created_at[:16]}", expanded=False):
                st.caption(f"严重程度：**{severity_label}**")
                st.text(f"期望结果：{bc.expected_output[:200]}")
                if bc.notes:
                    st.text(f"备注：{bc.notes[:200]}")
    else:
        st.caption("暂无 Bad Case。")

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

st.title("MeetingPilot")
st.caption("粘贴会议转写文本，自动生成结构化纪要、决策、待办、风险和追问信息。")

# -- Input section
st.header("会议转写文本")
st.caption("V0 版本仅支持粘贴或上传会议转写文本，不支持音频文件。你可以从 Zoom、腾讯会议、飞书等工具导出会议转写文本再粘贴。")

uploaded_file = st.file_uploader(
    "上传转录文件（.txt / .md / .srt / .vtt）",
    type=["txt", "md", "srt", "vtt"],
    label_visibility="visible",
)
if uploaded_file is not None:
    file_id = f"{uploaded_file.name}:{uploaded_file.size}"
    if file_id != st.session_state.get("_last_uploaded_id"):
        try:
            st.session_state.transcript = uploaded_file.getvalue().decode("utf-8")
        except UnicodeDecodeError:
            st.error("文件解码失败：无法以 UTF-8 编码读取该文件。")
        else:
            st.session_state._last_uploaded_id = file_id

col1, col2 = st.columns([4, 1])
with col1:
    st.text_area(
        "会议转写文本",
        key="transcript",
        height=250,
        placeholder="在这里粘贴会议转写文本...",
        label_visibility="collapsed",
    )
with col2:
    st.button("载入示例", on_click=_load_sample, use_container_width=True, type="secondary")
    st.button(
        "生成纪要",
        on_click=_run_extraction,
        use_container_width=True,
        type="primary",
    )

# -- Transcript size feedback
char_count, token_est, size_msg, size_level = _transcript_size_feedback(
    st.session_state.transcript
)
if size_msg:
    if size_level == "info":
        st.info(f"字符数：{char_count}  ·  估算 Token 数：约 {token_est}（仅供参考）\n\n{size_msg}")
    else:
        st.warning(f"字符数：{char_count}  ·  估算 Token 数：约 {token_est}（仅供参考）\n\n{size_msg}")

# -- Results section
result = st.session_state.result
if result is not None:
    st.divider()
    st.header(result.title)
    if result.date:
        st.caption(f"日期：{result.date}")

    st.subheader("会议摘要")
    st.write(result.summary)

    if result.decisions:
        st.subheader("决策事项")
        for d in result.decisions:
            owner = f" - *{d.made_by}*" if d.made_by else ""
            st.markdown(f"- {d.description}{owner}")

    if result.action_items:
        st.subheader("待办任务")
        rows = [
            {
                "任务": a.task,
                "负责人": a.owner or "-",
                "截止时间": a.due_date or "-",
                "优先级": PRIORITY_LABELS.get(a.priority, a.priority.value),
            }
            for a in result.action_items
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)

    if result.risk_points:
        st.subheader("风险点")
        for r in result.risk_points:
            severity_label = SEVERITY_LABELS.get(r.severity, r.severity.value)
            st.markdown(f"- **[{severity_label}]** {r.description}")

    if result.uncertainty_flags:
        st.subheader("不确定项")
        for u in result.uncertainty_flags:
            st.markdown(f"- **{u.topic}** - {u.reason}")
            st.caption(f"建议确认：{u.suggested_clarification}")

    if result.follow_up_questions:
        st.subheader("需要追问的问题")
        for question in result.follow_up_questions:
            st.markdown(f"- {question}")

    if result.next_steps:
        st.subheader("下一步建议")
        st.write(result.next_steps)

    # -- Export buttons
    st.divider()
    st.subheader("导出")
    ec1, ec2 = st.columns(2)
    with ec1:
        st.download_button(
            label="下载 Markdown 纪要",
            data=to_markdown(result),
            file_name=f"{safe_filename_part(result.title)}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with ec2:
        st.download_button(
            label="下载待办 CSV",
            data=action_items_to_csv(result),
            file_name=f"{safe_filename_part(result.title)}-actions.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # -- Bad case form
    st.divider()
    with st.expander("记录 Bad Case", expanded=False):
        st.caption("当 AI 结果有错误、遗漏或不可用时，在这里记录复盘样本。")
        issue_type = st.selectbox(
            "问题类型",
            options=[t for t in IssueType],
            format_func=lambda t: ISSUE_TYPE_LABELS.get(t, t.value),
        )
        severity = st.selectbox(
            "严重程度",
            options=[s for s in Severity],
            format_func=lambda s: SEVERITY_LABELS.get(s, s.value),
        )
        expected = st.text_area(
            "期望结果",
            placeholder="描述 AI 本应输出什么...",
        )
        notes = st.text_area(
            "备注（可选）",
            placeholder="补充观察，例如错因、上下文、后续优化方向...",
        )
        if st.button("保存 Bad Case", type="secondary"):
            if expected.strip():
                _record_bad_case(issue_type, severity, expected, notes)
            else:
                st.error("请先填写期望结果。")
