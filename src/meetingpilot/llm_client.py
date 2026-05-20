"""OpenAI-compatible LLM client wrapper."""

import json
import re
from typing import Any

from pydantic import ValidationError

try:
    from openai import OpenAI, OpenAIError
except ModuleNotFoundError:  # pragma: no cover - depends on local environment
    OpenAI = None  # type: ignore[assignment]
    OpenAIError = None  # type: ignore[assignment]

from meetingpilot.config import AppConfig
from meetingpilot.models import ActionItem, Decision, MeetingResult, Priority, RiskPoint, Severity, UncertaintyFlag
from meetingpilot.prompts import EXTRACTION_USER_TEMPLATE, MEETING_EXTRACTION_SYSTEM


class ExtractionError(Exception):
    """Raised when LLM extraction fails."""


def create_client(config: AppConfig) -> Any:
    if OpenAI is None:
        raise ExtractionError("当前环境未安装 openai 包，请先运行 `pip install -e .`。")
    return OpenAI(api_key=config.api_key, base_url=config.base_url)


def extract_meeting(client: Any, model: str, transcript: str) -> MeetingResult:
    """Send transcript to the LLM and parse the structured result."""
    user_message = EXTRACTION_USER_TEMPLATE.format(transcript=transcript)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": MEETING_EXTRACTION_SYSTEM},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
        )
    except Exception as exc:
        if OpenAIError is not None and isinstance(exc, OpenAIError):
            raise ExtractionError(
                "模型接口连接失败。请确认网络权限、代理设置、Base URL、模型名和 API Key；"
                "如果是在 Codex 沙箱里启动页面，请用项目脚本或有网络权限的终端重新启动。"
            ) from exc
        raise

    raw = response.choices[0].message.content
    if not raw:
        raise ExtractionError("LLM returned empty response.")

    return _parse_response(raw)


def extract_meeting_fallback(transcript: str) -> MeetingResult:
    """Create a deterministic demo result when no API client is configured."""
    text = transcript.strip()
    people = sorted(set(re.findall(r"\b[A-Z][a-z]+(?=[:：])", text)))
    owner = people[0] if people else None

    decisions: list[Decision] = []
    for line in text.splitlines():
        lowered = line.lower()
        if "decision:" in lowered or "决策" in line:
            decision_text = re.split(r"[:：]", line, maxsplit=1)[-1].strip()
            decisions.append(Decision(description=decision_text, made_by=owner))

    action_items: list[ActionItem] = []
    if any(keyword in text.lower() for keyword in ["finish", "draft", "文案", "草稿"]):
        action_items.append(
            ActionItem(
                task="完成会议中约定的后续交付物，并发送给相关负责人确认。",
                owner="Ben" if "Ben" in people else owner,
                due_date="周四下午" if "Thursday" in text or "周四" in text else None,
                priority=Priority.HIGH if "blocking" in text.lower() or "阻塞" in text else Priority.MEDIUM,
            )
        )

    risks: list[RiskPoint] = []
    if any(word in text.lower() for word in ["risk", "block", "uncertain", "issue"]) or any(
        word in text for word in ["风险", "阻塞", "不确定", "问题"]
    ):
        risks.append(
            RiskPoint(
                description="会议中提到阻塞问题或不确定输入，可能影响发布时间。",
                severity=Severity.MAJOR,
            )
        )

    uncertainties: list[UncertaintyFlag] = []
    if (
        "latest pricing page" in text.lower()
        or "details" in text.lower()
        or "价格页" in text
        or "最新" in text
    ):
        uncertainties.append(
            UncertaintyFlag(
                topic="缺少资料来源",
                reason="负责人需要最新价格页信息后才能完成文案初稿。",
                suggested_clarification="请确认最新价格页详情和来源链接。",
            )
        )
    if not action_items:
        uncertainties.append(
            UncertaintyFlag(
                topic="未识别到明确待办",
                reason="转写文本中没有清晰的任务、负责人、截止时间模式。",
                suggested_clarification="请参会人确认负责人、截止时间和下一步动作。",
            )
        )

    follow_up_questions = [
        flag.suggested_clarification if flag.suggested_clarification.endswith("?") else f"{flag.suggested_clarification}?"
        for flag in uncertainties
    ]

    summary = "本次会议讨论了后续交付、资料依赖和发布时间风险。当前结果由本地演示模式生成，适合用于展示流程、导出和 Bad Case 记录。"

    return MeetingResult(
        title="MeetingPilot 演示纪要",
        date=None,
        summary=summary,
        decisions=decisions,
        action_items=action_items,
        risk_points=risks,
        uncertainty_flags=uncertainties,
        follow_up_questions=follow_up_questions,
        next_steps="请人工复核负责人和截止时间；如果发现遗漏或错误，将其记录为 Bad Case 以便后续优化 Prompt。",
    )


def _parse_response(raw: str) -> MeetingResult:
    """Parse LLM JSON into a MeetingResult, stripping markdown fences if present."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```").strip()
        if text.endswith("```"):
            text = text[:-3].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ExtractionError(f"Failed to parse LLM JSON response: {exc}") from exc

    try:
        return MeetingResult(**data)
    except ValidationError as exc:
        raise ExtractionError(f"LLM JSON did not match MeetingResult schema: {exc}") from exc
