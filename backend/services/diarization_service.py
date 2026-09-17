from sqlalchemy.orm import Session

from backend.repositories.speaker_segment_repository import (
    SpeakerSegmentRepository,
)
from core.exceptions import AudioProcessingError
from diarization.schemas import DiarizationResult
from diarization.service import DiarizationService


class MeetingDiarizationService:
    """
    Service responsible for running speaker diarization
    and persisting the resulting speaker segments.
    """

    def __init__(
        self,
        session: Session,
        diarization_service: DiarizationService,
    ) -> None:
        self.session = session
        self.diarization_service = diarization_service

        self.repository = SpeakerSegmentRepository(
            session
        )

    def diarize_meeting(
        self,
        meeting_id: int,
        audio_path: str,
    ) -> DiarizationResult:
        """
        Run diarization for a meeting and persist
        the detected speaker segments.

        Args:
            meeting_id: ID of the meeting.
            audio_path: Path to the meeting recording.

        Returns:
            DiarizationResult containing the detected
            speaker segments.

        Raises:
            AudioProcessingError: If diarization fails.
        """

        try:
            result = self.diarization_service.diarize(
                audio_path=audio_path
            )

            self.repository.delete_by_meeting_id(
                meeting_id=meeting_id
            )

            segments = [
                {
                    "speaker": segment.speaker,
                    "start_time": segment.start,
                    "end_time": segment.end,
                }
                for segment in result.segments
            ]

            self.repository.create_many(
                meeting_id=meeting_id,
                segments=segments,
            )

            return result

        except AudioProcessingError:
            raise

        except Exception as exc:
            raise AudioProcessingError(
                "Unable to process and persist "
                "speaker diarization."
            ) from exc
