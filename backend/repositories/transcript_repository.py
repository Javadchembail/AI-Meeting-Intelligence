from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.transcript import Transcript


class TranscriptRepository:
    """
    Repository responsible for database operations
    related to meeting transcripts.
    """

    def __init__(
        self,
        session: Session,
    ) -> None:

        self.session = session

    def create(
        self,
        meeting_id: int,
        full_text: str,
        language: str | None = None,
        language_probability: float | None = None,
        word_timestamps: list[
            dict
        ] | None = None,
    ) -> Transcript:

        transcript = Transcript(
            meeting_id=meeting_id,
            full_text=full_text,
            language=language,
            language_probability=language_probability,
            word_timestamps=word_timestamps,
        )

        self.session.add(transcript)

        self.session.commit()

        self.session.refresh(transcript)

        return transcript

    def get_by_id(
        self,
        transcript_id: int,
    ) -> Transcript | None:

        statement = select(
            Transcript
        ).where(
            Transcript.id == transcript_id
        )

        return self.session.scalar(
            statement
        )

    def get_by_meeting_id(
        self,
        meeting_id: int,
    ) -> Transcript | None:

        statement = select(
            Transcript
        ).where(
            Transcript.meeting_id == meeting_id
        )

        return self.session.scalar(
            statement
        )

    def update(
        self,
        transcript: Transcript,
    ) -> Transcript:

        self.session.add(transcript)

        self.session.commit()

        self.session.refresh(transcript)

        return transcript

    def delete(
        self,
        transcript: Transcript,
    ) -> None:

        self.session.delete(
            transcript
        )

        self.session.commit()