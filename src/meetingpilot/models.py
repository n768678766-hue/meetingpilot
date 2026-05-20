"""Pydantic data models for meeting extraction outputs."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueType(str, Enum):
    OWNER_MISSING = "Owner missing"
    DUE_DATE_MISSING = "Due date missing"
    TASK_SPLIT_TOO_BROAD = "Task split too broad"
    DECISION_CONFUSED_WITH_ACTION = "Decision confused with action item"
    RISK_POINT_OMITTED = "Risk point omitted"
    HALLUCINATED_PERSON_OR_DATE = "Hallucinated person or date"
    OTHER = "Other"


class Severity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class ActionItem(BaseModel):
    task: str = Field(description="What needs to be done")
    owner: str | None = Field(default=None, description="Person responsible")
    due_date: str | None = Field(default=None, description="Deadline if mentioned")
    priority: Priority = Field(default=Priority.MEDIUM, description="high, medium, or low")


class Decision(BaseModel):
    description: str = Field(description="What was decided")
    made_by: str | None = Field(default=None, description="Who made or drove the decision")


class RiskPoint(BaseModel):
    description: str = Field(description="The risk, blocker, or concern")
    severity: Severity = Field(default=Severity.MAJOR)


class UncertaintyFlag(BaseModel):
    topic: str = Field(description="What is unclear or missing")
    reason: str = Field(description="Why it matters")
    suggested_clarification: str = Field(description="How to resolve it")


class MeetingResult(BaseModel):
    title: str = Field(description="Short meeting title derived from content")
    date: str | None = Field(default=None, description="Meeting date if mentioned")
    summary: str = Field(description="2-4 sentence meeting summary")
    decisions: list[Decision] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    risk_points: list[RiskPoint] = Field(default_factory=list)
    uncertainty_flags: list[UncertaintyFlag] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    next_steps: str = Field(default="", description="Suggested next steps")


class BadCase(BaseModel):
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds"),
        description="ISO timestamp when the bad case was recorded",
    )
    transcript_excerpt: str = Field(description="Relevant portion of the source transcript")
    expected_output: str = Field(description="What the output should have included")
    actual_output: str = Field(description="What the model actually produced")
    issue_type: IssueType = Field(description="Category of the issue")
    severity: Severity = Field(default=Severity.MAJOR)
    prompt_version: str = Field(default="0.1.0", description="Version of the prompt used")
    notes: str = Field(default="", description="Additional observations")
