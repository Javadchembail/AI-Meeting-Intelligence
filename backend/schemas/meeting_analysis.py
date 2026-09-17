from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ActionItemResponse(BaseModel):
    """
    API response model for an action item.
    """

    task: str = Field(
        ...,
        description="Task that needs to be completed.",
    )

    assignee: str | None = Field(
        default=None,
        description="Person responsible for the task.",
    )

    deadline: str | None = Field(
        default=None,
        description="Deadline mentioned in the meeting.",
    )

    priority: str = Field(
        default="medium",
        description="Task priority.",
    )


class MeetingAnalysisResponse(BaseModel):
    """
    API response model for AI-generated
    meeting intelligence.
    """

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    meeting_id: int

    summary: str = Field(
        ...,
        description="Concise meeting summary.",
    )

    key_points: list[str] = Field(
        default_factory=list,
        description="Important points discussed.",
    )

    decisions: list[str] = Field(
        default_factory=list,
        description="Decisions made during the meeting.",
    )

    action_items: list[ActionItemResponse] = Field(
        default_factory=list,
        description="Tasks identified from the meeting.",
    )

    next_steps: list[str] = Field(
        default_factory=list,
        description="Next steps from the meeting.",
    )

    created_at: datetime