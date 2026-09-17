from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TranscriptWordResponse(BaseModel):
    """
    Represents one word and its position in the audio.
    """

    word: str = Field(
        ...,
        description="Transcribed word.",
    )

    start: float = Field(
        ...,
        description="Word start time in seconds.",
    )

    end: float = Field(
        ...,
        description="Word end time in seconds.",
    )

    probability: float | None = Field(
        default=None,
        description="Whisper confidence for the word.",
    )


class TranscriptResponse(BaseModel):
    """
    Response schema representing a stored meeting transcript.
    """

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    meeting_id: int

    full_text: str = Field(
        ...,
        description="Complete meeting transcript.",
    )

    language: str | None = Field(
        default=None,
        description="Detected spoken language.",
    )

    language_probability: float | None = Field(
        default=None,
        description="Whisper language detection confidence.",
    )

    word_timestamps: list[
        TranscriptWordResponse
    ] = Field(
        default_factory=list,
        description=(
            "Word-level timestamps used "
            "for synchronized transcript highlighting."
        ),
    )

    created_at: datetime