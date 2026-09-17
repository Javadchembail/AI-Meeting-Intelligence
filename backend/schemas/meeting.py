from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MeetingCreate(BaseModel):
    """
    Request schema used when creating a new meeting.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Title of the meeting.",
    )


class MeetingResponse(BaseModel):
    """
    Response schema representing a meeting.
    """

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    title: str
    started_at: datetime | None
    ended_at: datetime | None
    duration_seconds: int | None
    audio_path: str | None
    created_at: datetime