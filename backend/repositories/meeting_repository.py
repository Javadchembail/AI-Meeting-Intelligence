from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.meeting import Meeting


class MeetingRepository:
    """
    Repository responsible for database operations
    related to meetings.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        title: str,
        started_at: datetime | None = None,
    ) -> Meeting:
        meeting = Meeting(
            title=title,
            started_at=started_at,
        )

        self.session.add(meeting)
        self.session.commit()
        self.session.refresh(meeting)

        return meeting

    def get_by_id(
        self,
        meeting_id: int,
    ) -> Meeting | None:
        statement = select(Meeting).where(
            Meeting.id == meeting_id
        )

        return self.session.scalar(statement)

    def get_latest(self) -> Meeting | None:
        """
        Retrieve the newest meeting by creation timestamp.
        Uses the ID as a tie-breaker.
        """

        statement = (
            select(Meeting)
            .order_by(
                Meeting.created_at.desc(),
                Meeting.id.desc(),
            )
            .limit(1)
        )

        return self.session.scalar(statement)

    def get_all(self) -> list[Meeting]:
        statement = (
            select(Meeting)
            .order_by(Meeting.created_at.desc())
        )

        return list(
            self.session.scalars(statement).all()
        )

    def update(self, meeting: Meeting) -> Meeting:
        self.session.add(meeting)
        self.session.commit()
        self.session.refresh(meeting)

        return meeting

    def delete(self, meeting: Meeting) -> None:
        self.session.delete(meeting)
        self.session.commit()
