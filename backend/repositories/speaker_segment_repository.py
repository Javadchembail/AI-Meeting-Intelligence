from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.models.speaker_segment import SpeakerSegment


class SpeakerSegmentRepository:
    """
    Repository responsible for database operations
    related to speaker segments.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        meeting_id: int,
        speaker: str,
        start_time: float,
        end_time: float,
    ) -> SpeakerSegment:
        """
        Create and persist a single speaker segment.
        """

        segment = SpeakerSegment(
            meeting_id=meeting_id,
            speaker=speaker,
            start_time=start_time,
            end_time=end_time,
        )

        self.session.add(segment)
        self.session.commit()
        self.session.refresh(segment)

        return segment

    def create_many(
        self,
        meeting_id: int,
        segments: list[dict],
    ) -> list[SpeakerSegment]:
        """
        Create and persist multiple speaker segments
        in a single database transaction.
        """

        speaker_segments = [
            SpeakerSegment(
                meeting_id=meeting_id,
                speaker=segment["speaker"],
                start_time=segment["start_time"],
                end_time=segment["end_time"],
            )
            for segment in segments
        ]

        if not speaker_segments:
            return []

        self.session.add_all(
            speaker_segments
        )

        self.session.commit()

        for segment in speaker_segments:
            self.session.refresh(segment)

        return speaker_segments

    def get_by_meeting_id(
        self,
        meeting_id: int,
    ) -> list[SpeakerSegment]:
        """
        Get all speaker segments for a meeting,
        ordered chronologically.
        """

        statement = (
            select(SpeakerSegment)
            .where(
                SpeakerSegment.meeting_id
                == meeting_id
            )
            .order_by(
                SpeakerSegment.start_time
            )
        )

        return list(
            self.session.scalars(
                statement
            ).all()
        )

    def delete_by_meeting_id(
        self,
        meeting_id: int,
    ) -> None:
        """
        Delete all speaker segments associated
        with a meeting.
        """

        statement = delete(
            SpeakerSegment
        ).where(
            SpeakerSegment.meeting_id
            == meeting_id
        )

        self.session.execute(statement)
        self.session.commit()
