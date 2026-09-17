from pydantic import BaseModel, Field


class SpeakerSegmentResponse(BaseModel):
    """
    API response representing one speaker segment.
    """

    speaker: str = Field(
        ...,
        description="Speaker identifier.",
    )

    start: float = Field(
        ...,
        ge=0.0,
        description="Segment start time in seconds.",
    )

    end: float = Field(
        ...,
        gt=0.0,
        description="Segment end time in seconds.",
    )


class DiarizationResponse(BaseModel):
    """
    API response containing speaker diarization
    results for a meeting.
    """

    meeting_id: int

    speakers: list[str] = Field(
        default_factory=list,
        description="Unique speakers detected.",
    )

    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Duration of the diarized audio.",
    )

    segments: list[SpeakerSegmentResponse] = Field(
        default_factory=list,
        description="Speaker-labeled audio segments.",
    )
