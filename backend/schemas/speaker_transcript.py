from pydantic import BaseModel, Field


class SpeakerTranscriptSegmentResponse(BaseModel):
    """
    Represents a speaker-aware section of a meeting transcript.
    """

    speaker: str = Field(
        ...,
        description="Speaker identifier, such as SPEAKER_00.",
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

    text: str = Field(
        ...,
        min_length=1,
        description="Transcript text spoken during this segment.",
    )


class SpeakerTranscriptResponse(BaseModel):
    """
    Complete speaker-aware transcript for a meeting.
    """

    meeting_id: int

    speakers: list[str] = Field(
        default_factory=list,
        description="Speakers detected in the meeting.",
    )

    duration_seconds: float = Field(
        ...,
        ge=0.0,
        description="Duration covered by the speaker transcript.",
    )

    segments: list[
        SpeakerTranscriptSegmentResponse
    ] = Field(
        default_factory=list,
        description="Speaker-aware transcript segments.",
    )
