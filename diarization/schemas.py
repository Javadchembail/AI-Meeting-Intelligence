from pydantic import BaseModel, Field


class SpeakerSegment(BaseModel):
    """
    Represents a period of audio spoken by one speaker.
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

    @property
    def duration(self) -> float:
        """
        Return the duration of the speaker segment.
        """

        return self.end - self.start


class DiarizationResult(BaseModel):
    """
    Represents the complete speaker diarization result
    for an audio recording.
    """

    segments: list[SpeakerSegment] = Field(
        default_factory=list,
        description="Speaker-labeled audio segments.",
    )

    speakers: list[str] = Field(
        default_factory=list,
        description="Unique speakers detected in the audio.",
    )

    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Total duration of the diarized audio.",
    )