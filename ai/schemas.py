from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    """
    Represents an actionable task identified
    from a meeting.
    """

    task: str = Field(
        ...,
        description="The task that needs to be completed.",
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
        description="Task priority: low, medium, or high.",
    )


class MeetingAnalysis(BaseModel):
    """
    Structured AI-generated analysis of a meeting.
    """

    summary: str = Field(
        ...,
        description="Concise summary of the meeting.",
    )

    key_points: list[str] = Field(
        default_factory=list,
        description="Important points discussed.",
    )

    decisions: list[str] = Field(
        default_factory=list,
        description="Decisions made during the meeting.",
    )

    action_items: list[ActionItem] = Field(
        default_factory=list,
        description="Tasks identified from the meeting.",
    )

    next_steps: list[str] = Field(
        default_factory=list,
        description="Recommended or explicitly mentioned next steps.",
    )