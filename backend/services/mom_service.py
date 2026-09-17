from sqlalchemy.orm import Session

from backend.repositories.meeting_analysis_repository import (
    MeetingAnalysisRepository,
)
from backend.repositories.meeting_repository import MeetingRepository
from backend.schemas.mom import (
    MinutesOfMeeting,
    MoMActionItem,
)


class MoMService:
    """
    Service responsible for generating structured
    Minutes of Meeting from existing meeting data
    and AI analysis.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

        self.meeting_repository = MeetingRepository(
            session
        )

        self.analysis_repository = (
            MeetingAnalysisRepository(session)
        )

    def generate_mom(
        self,
        meeting_id: int,
    ) -> MinutesOfMeeting:
        """
        Generate Minutes of Meeting for a meeting.

        The MoM is assembled from the meeting metadata
        and the AI analysis already stored in PostgreSQL.

        Args:
            meeting_id: ID of the meeting.

        Returns:
            MinutesOfMeeting: Structured MoM.

        Raises:
            ValueError: If the meeting or analysis
                does not exist.
        """

        meeting = self.meeting_repository.get_by_id(
            meeting_id
        )

        if meeting is None:
            raise ValueError(
                f"Meeting with ID {meeting_id} was not found."
            )

        analysis = (
            self.analysis_repository.get_by_meeting_id(
                meeting_id
            )
        )

        if analysis is None:
            raise ValueError(
                f"AI analysis for meeting "
                f"{meeting_id} was not found. "
                f"Analyze the meeting before generating MoM."
            )

        action_items = [
            MoMActionItem(
                task=item.get("task", ""),
                assignee=item.get("assignee"),
                deadline=item.get("deadline"),
                priority=item.get(
                    "priority",
                    "medium",
                ),
            )
            for item in analysis.action_items
        ]

        mom = MinutesOfMeeting(
            meeting_id=meeting.id,
            meeting_title=meeting.title,
            meeting_date=meeting.started_at,
            duration_seconds=meeting.duration_seconds,
            summary=analysis.summary,
            key_points=analysis.key_points,
            decisions=analysis.decisions,
            action_items=action_items,
            next_steps=analysis.next_steps,
        )

        return mom