"""Export helpers for structured meeting outputs."""

from io import StringIO

import pandas as pd

from meetingpilot.models import MeetingResult, Priority, Severity

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


def _fmt(value: str | None, default: str = "-") -> str:
    return value if value else default


def _table_cell(value: str | None) -> str:
    return _fmt(value, "").replace("|", "\\|").replace("\n", " ")


def to_markdown(result: MeetingResult) -> str:
    """Convert a MeetingResult to a Markdown document."""
    lines: list[str] = []

    lines.append(f"# {result.title}")
    if result.date:
        lines.append(f"**日期：** {result.date}")
    lines.append("")
    lines.append("## 会议摘要")
    lines.append(result.summary)
    lines.append("")

    if result.decisions:
        lines.append("## 决策事项")
        for d in result.decisions:
            owner = f" ({_fmt(d.made_by)})" if d.made_by else ""
            lines.append(f"- {d.description}{owner}")
        lines.append("")

    if result.action_items:
        lines.append("## 待办任务")
        lines.append("| # | 任务 | 负责人 | 截止时间 | 优先级 |")
        lines.append("|---|------|--------|----------|--------|")
        for i, a in enumerate(result.action_items, start=1):
            lines.append(
                f"| {i} | {_table_cell(a.task)} | {_table_cell(a.owner)} | "
                f"{_table_cell(a.due_date)} | {PRIORITY_LABELS.get(a.priority, a.priority.value)} |"
            )
        lines.append("")

    if result.risk_points:
        lines.append("## 风险点")
        for r in result.risk_points:
            lines.append(f"- **[{SEVERITY_LABELS.get(r.severity, r.severity.value)}]** {r.description}")
        lines.append("")

    if result.uncertainty_flags:
        lines.append("## 不确定项")
        for u in result.uncertainty_flags:
            lines.append(f"- **{u.topic}** - {u.reason}")
            lines.append(f"  建议确认：{u.suggested_clarification}")
        lines.append("")

    if result.follow_up_questions:
        lines.append("## 需要追问的问题")
        for question in result.follow_up_questions:
            lines.append(f"- {question}")
        lines.append("")

    if result.next_steps:
        lines.append("## 下一步建议")
        lines.append(result.next_steps)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def action_items_to_csv(result: MeetingResult) -> str:
    """Export action items from a MeetingResult as a CSV string."""
    if not result.action_items:
        return "任务,负责人,截止时间,优先级\n"

    df = pd.DataFrame(
        [
            {
                "任务": a.task,
                "负责人": a.owner or "",
                "截止时间": a.due_date or "",
                "优先级": PRIORITY_LABELS.get(a.priority, a.priority.value),
            }
            for a in result.action_items
        ]
    )
    buf = StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()
