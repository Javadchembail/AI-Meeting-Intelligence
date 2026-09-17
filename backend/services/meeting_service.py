from datetime import datetime, timezone
from threading import Lock

import logfire
from sqlalchemy.orm import Session

from audio.recorder import AudioRecorder
from audio.storage import AudioStorageService
from backend.models.meeting import Meeting
from backend.repositories.meeting_repository import MeetingRepository


class MeetingService:
    """
    Service layer responsible for meeting business logic
    and meeting audio lifecycle.
    """

    _active_recorder: AudioRecorder | None = None
    _active_meeting_id: int | None = None

    # Protects meeting lifecycle state from concurrent
    # FastAPI requests.
    _state_lock = Lock()

    def __init__(
        self,
        session: Session,
        audio_recorder: AudioRecorder | None = None,
        audio_storage: AudioStorageService | None = None,
    ) -> None:
        self.session = session

        self.repository = MeetingRepository(self.session)

        self.audio_storage = (
            audio_storage
            if audio_storage is not None
            else AudioStorageService()
        )

        # Shared active recorder across requests.
        if MeetingService._active_recorder is None:
            MeetingService._active_recorder = (
                audio_recorder
                if audio_recorder is not None
                else AudioRecorder()
            )

        self.audio_recorder = MeetingService._active_recorder

    # ==================================================
    # START MEETING
    # ==================================================

    def start_meeting(self, title: str) -> Meeting:
        """
        Create a meeting and start microphone recording.
        """

        with logfire.span(
            "meeting.start",
            meeting_title=title.strip() if title else "",
        ):
            if not title.strip():
                raise ValueError("Meeting title cannot be empty.")

            with MeetingService._state_lock:
                if MeetingService._active_meeting_id is not None:
                    raise ValueError(
                        "Another meeting is already being recorded."
                    )

                started_at = datetime.now(timezone.utc)

                meeting = self.repository.create(
                    title=title.strip(),
                    started_at=started_at,
                )

                try:
                    with logfire.span(
                        "meeting.start_recording",
                        meeting_id=meeting.id,
                    ):
                        self.audio_recorder.start_recording()

                    # Set active meeting only after recording starts.
                    MeetingService._active_meeting_id = meeting.id

                    logfire.info(
                        "Meeting recording started",
                        meeting_id=meeting.id,
                        started_at=started_at.isoformat(),
                    )

                    return meeting

                except Exception:
                    logfire.exception(
                        "Failed to start meeting recording",
                        meeting_id=meeting.id,
                    )

                    self.session.rollback()

                    try:
                        self.repository.delete(meeting)
                    except Exception:
                        self.session.rollback()

                    MeetingService._active_meeting_id = None
                    raise

    # ==================================================
    # GET MEETING
    # ==================================================

    def get_meeting(self, meeting_id: int) -> Meeting | None:
        """Retrieve a meeting by ID."""

        with logfire.span(
            "meeting.get",
            meeting_id=meeting_id,
        ):
            return self.repository.get_by_id(meeting_id)

    # ==================================================
    # GET ALL MEETINGS
    # ==================================================

    def get_all_meetings(self) -> list[Meeting]:
        """Retrieve all meetings."""

        with logfire.span("meeting.get_all"):
            meetings = self.repository.get_all()

            logfire.info(
                "Retrieved meetings",
                meeting_count=len(meetings),
            )

            return meetings

    # ==================================================
    # GET LIVE AUDIO LEVEL
    # ==================================================

    def get_audio_level(self, meeting_id: int) -> float:
        """
        Return the current microphone audio level.

        This high-frequency endpoint is intentionally
        not wrapped in a Logfire span on every request.
        """

        self._validate_active_meeting(meeting_id)

        if not self.audio_recorder.is_recording:
            raise ValueError("Audio recording is not active.")

        if self.audio_recorder.is_paused:
            return 0.0

        return self.audio_recorder.current_audio_level

    # ==================================================
    # PAUSE MEETING
    # ==================================================

    def pause_meeting(self, meeting_id: int) -> Meeting:
        """Pause the active meeting recording."""

        with logfire.span(
            "meeting.pause",
            meeting_id=meeting_id,
        ):
            self._validate_active_meeting(meeting_id)

            if not self.audio_recorder.is_recording:
                raise ValueError("Audio recording is not active.")

            if self.audio_recorder.is_paused:
                raise ValueError("Meeting is already paused.")

            self.audio_recorder.pause_recording()

            logfire.info(
                "Meeting recording paused",
                meeting_id=meeting_id,
            )

            return self.repository.get_by_id(meeting_id)

    # ==================================================
    # RESUME MEETING
    # ==================================================

    def resume_meeting(self, meeting_id: int) -> Meeting:
        """Resume the active meeting recording."""

        with logfire.span(
            "meeting.resume",
            meeting_id=meeting_id,
        ):
            self._validate_active_meeting(meeting_id)

            if not self.audio_recorder.is_recording:
                raise ValueError("Audio recording is not active.")

            if not self.audio_recorder.is_paused:
                raise ValueError("Meeting is not paused.")

            self.audio_recorder.resume_recording()

            logfire.info(
                "Meeting recording resumed",
                meeting_id=meeting_id,
            )

            return self.repository.get_by_id(meeting_id)

    # ==================================================
    # END MEETING
    # ==================================================

    def end_meeting(self, meeting_id: int) -> Meeting:
        """
        End an active meeting, save its audio and
        calculate duration excluding paused time.
        """

        with logfire.span(
            "meeting.end",
            meeting_id=meeting_id,
        ):
            meeting = self.repository.get_by_id(meeting_id)

            if meeting is None:
                raise ValueError(
                    f"Meeting with ID {meeting_id} was not found."
                )

            if meeting.started_at is None:
                raise ValueError("Meeting has no start time.")

            if meeting.ended_at is not None:
                raise ValueError("Meeting has already ended.")

            if MeetingService._active_meeting_id != meeting_id:
                raise ValueError(
                    "This meeting is not the active recording."
                )

            if not self.audio_recorder.is_recording:
                raise ValueError("Audio recording is not active.")

            ended_at = datetime.now(timezone.utc)

            # Stop recording.
            with logfire.span(
                "meeting.stop_recording",
                meeting_id=meeting_id,
            ):
                audio = self.audio_recorder.stop_recording()

            sample_rate = self.audio_recorder.sample_rate

            # Save audio.
            with logfire.span(
                "meeting.save_audio",
                meeting_id=meeting_id,
                sample_rate=sample_rate,
                audio_sample_count=len(audio),
            ):
                audio_path = self.audio_storage.save_audio(
                    audio=audio,
                    sample_rate=sample_rate,
                    meeting_id=meeting.id,
                )

            meeting.ended_at = ended_at
            meeting.audio_path = str(audio_path)

            # Duration is based on captured audio samples.
            # Paused periods are excluded.
            meeting.duration_seconds = max(
                0,
                int(len(audio) / sample_rate),
            )

            with logfire.span(
                "meeting.update_database",
                meeting_id=meeting_id,
            ):
                completed_meeting = self.repository.update(meeting)

            MeetingService._active_meeting_id = None

            logfire.info(
                "Meeting recording completed",
                meeting_id=meeting_id,
                duration_seconds=meeting.duration_seconds,
                audio_sample_count=len(audio),
                sample_rate=sample_rate,
            )

            return completed_meeting

    # ==================================================
    # DELETE MEETING
    # ==================================================

    def delete_meeting(self, meeting_id: int) -> None:
        """Delete a meeting and its associated audio file."""

        with logfire.span(
            "meeting.delete",
            meeting_id=meeting_id,
        ):
            meeting = self.repository.get_by_id(meeting_id)

            if meeting is None:
                raise ValueError(
                    f"Meeting with ID {meeting_id} was not found."
                )

            if (
                meeting.audio_path
                and self.audio_storage.audio_exists(meeting.audio_path)
            ):
                with logfire.span(
                    "meeting.delete_audio",
                    meeting_id=meeting_id,
                ):
                    self.audio_storage.delete_audio(meeting.audio_path)

            with logfire.span(
                "meeting.delete_database_record",
                meeting_id=meeting_id,
            ):
                self.repository.delete(meeting)

            if MeetingService._active_meeting_id == meeting_id:
                MeetingService._active_meeting_id = None

            logfire.info(
                "Meeting deleted",
                meeting_id=meeting_id,
            )

    # ==================================================
    # VALIDATE ACTIVE MEETING
    # ==================================================

    def _validate_active_meeting(self, meeting_id: int) -> None:
        """Validate that the requested meeting is active."""

        meeting = self.repository.get_by_id(meeting_id)

        if meeting is None:
            raise ValueError(
                f"Meeting with ID {meeting_id} was not found."
            )

        if meeting.ended_at is not None:
            raise ValueError("Meeting has already ended.")

        if MeetingService._active_meeting_id != meeting_id:
            raise ValueError(
                "This meeting is not the active recording."
            )