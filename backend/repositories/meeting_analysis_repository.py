from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.meeting_analysis import MeetingAnalysis


class MeetingAnalysisRepository:
    """
    Repository for meeting analysis database operations.
    """

    def __init__(
        self,
        session: Session,
    ) -> None:

        self.session = session

    def create(
        self,
        meeting_id: int,
        summary: str,
        key_points: list[str] | None = None,
        decisions: list[str] | None = None,
        action_items: list[dict] | None = None,
        next_steps: list[str] | None = None,
    ) -> MeetingAnalysis:
        """
        Create and persist a meeting analysis.
        """

        analysis = MeetingAnalysis(
            meeting_id=meeting_id,
            summary=summary,
            key_points=(
                key_points
                if key_points is not None
                else []
            ),
            decisions=(
                decisions
                if decisions is not None
                else []
            ),
            action_items=(
                action_items
                if action_items is not None
                else []
            ),
            next_steps=(
                next_steps
                if next_steps is not None
                else []
            ),
        )

        self.session.add(
            analysis
        )

        self.session.commit()

        self.session.refresh(
            analysis
        )

        return analysis

    def get_by_id(
        self,
        analysis_id: int,
    ) -> MeetingAnalysis | None:
        """
        Get an analysis by its ID.
        """

        statement = select(
            MeetingAnalysis
        ).where(
            MeetingAnalysis.id == analysis_id
        )

        return self.session.scalar(
            statement
        )

    def get_by_meeting_id(
        self,
        meeting_id: int,
    ) -> MeetingAnalysis | None:
        """
        Get the analysis belonging to a meeting.
        """

        statement = select(
            MeetingAnalysis
        ).where(
            MeetingAnalysis.meeting_id == meeting_id
        )

        return self.session.scalar(
            statement
        )

    def update(
        self,
        analysis: MeetingAnalysis,
    ) -> MeetingAnalysis:
        """
        Update and persist an existing analysis.
        """

        self.session.add(
            analysis
        )

        self.session.commit()

        self.session.refresh(
            analysis
        )

        return analysis

    def delete(
        self,
        analysis: MeetingAnalysis,
    ) -> None:
        """
        Delete an analysis.
        """

        self.session.delete(
            analysis
        )

        self.session.commit()