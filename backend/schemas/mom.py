from datetime import datetime

from pydantic import BaseModel, Field


class MoMActionItem(BaseModel):
    """
    Action item included in the Minutes of Meeting.
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
        description="Priority of the action item.",
    )


class MinutesOfMeeting(BaseModel):
    """
    Structured Minutes of Meeting generated
    from the meeting analysis.
    """

    meeting_id: int

    meeting_title: str

    meeting_date: datetime | None = None

    duration_seconds: int | None = None

    summary: str

    key_points: list[str] = Field(
        default_factory=list,
    )

    decisions: list[str] = Field(
        default_factory=list,
    )

    action_items: list[MoMActionItem] = Field(
        default_factory=list,
    )

    next_steps: list[str] = Field(
        default_factory=list,
    )