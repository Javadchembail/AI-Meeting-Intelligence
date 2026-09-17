from sqlalchemy.orm import Session

from ai.analysis_service import AIAnalysisService
from backend.models.meeting_analysis import MeetingAnalysis
from backend.repositories.meeting_analysis_repository import (
    MeetingAnalysisRepository,
)
from backend.repositories.transcript_repository import (
    TranscriptRepository,
)
from core.exceptions import AIProcessingError
from core.logging import logger


class MeetingAnalysisService:
    """
    Service responsible for generating and persisting
    AI-powered meeting analysis.
    """

    def __init__(
        self,
        session: Session,
        ai_service: AIAnalysisService | None = None,
    ) -> None:

        self.session = session

        self.repository = (
            MeetingAnalysisRepository(
                session
            )
        )

        self.transcript_repository = (
            TranscriptRepository(
                session
            )
        )

        self.ai_service = (
            ai_service
            if ai_service is not None
            else AIAnalysisService()
        )

    def analyze_meeting(
        self,
        meeting_id: int,
    ) -> MeetingAnalysis:
        """
        Generate AI analysis from a meeting transcript
        and persist the result in PostgreSQL.
        """

        transcript = (
            self.transcript_repository.get_by_meeting_id(
                meeting_id
            )
        )

        if transcript is None:

            raise ValueError(
                f"No transcript found for meeting "
                f"{meeting_id}."
            )

        existing_analysis = (
            self.repository.get_by_meeting_id(
                meeting_id
            )
        )

        if existing_analysis is not None:

            raise ValueError(
                f"Analysis already exists for meeting "
                f"{meeting_id}."
            )

        if not transcript.full_text.strip():

            raise AIProcessingError(
                "Cannot analyze an empty transcript."
            )

        try:

            logger.info(
                "Starting AI analysis for meeting %s.",
                meeting_id,
            )

            analysis = (
                self.ai_service.analyze_transcript(
                    transcript.full_text
                )
            )

            action_items = [
                item.model_dump()
                for item in analysis.action_items
            ]

            saved_analysis = (
                self.repository.create(
                    meeting_id=meeting_id,
                    summary=analysis.summary,
                    key_points=analysis.key_points,
                    decisions=analysis.decisions,
                    action_items=action_items,
                    next_steps=analysis.next_steps,
                )
            )

            logger.info(
                "AI analysis saved successfully "
                "for meeting %s.",
                meeting_id,
            )

            return saved_analysis

        except AIProcessingError:

            raise

        except Exception as exc:

            logger.exception(
                "Failed to analyze meeting %s.",
                meeting_id,
            )

            raise AIProcessingError(
                "Unable to generate meeting analysis."
            ) from exc

    def get_analysis(
        self,
        analysis_id: int,
    ) -> MeetingAnalysis | None:
        """
        Retrieve an analysis by its ID.
        """

        return self.repository.get_by_id(
            analysis_id
        )

    def get_meeting_analysis(
        self,
        meeting_id: int,
    ) -> MeetingAnalysis | None:
        """
        Retrieve the analysis belonging to a meeting.
        """

        return self.repository.get_by_meeting_id(
            meeting_id
        )