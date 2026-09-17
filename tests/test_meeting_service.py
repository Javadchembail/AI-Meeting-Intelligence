import time
from pathlib import Path

from backend.database.session import SessionLocal
from backend.services.meeting_service import MeetingService


def test_meeting_service() -> None:
    """
    Test the complete meeting lifecycle including
    microphone recording and audio storage.
    """

    session = SessionLocal()
    service = MeetingService(session)

    meeting = None

    try:
        # START MEETING
        print("Starting meeting...")

        meeting = service.start_meeting(
            title="Meeting Audio Service Test"
        )

        print("START: Meeting created successfully")
        print(f"Meeting ID: {meeting.id}")
        print(f"Meeting title: {meeting.title}")
        print(f"Started at: {meeting.started_at}")

        if meeting.started_at is None:
            raise RuntimeError(
                "Meeting start time was not created."
            )

        if not service.audio_recorder.is_recording:
            raise RuntimeError(
                "Audio recording did not start."
            )

        print("AUDIO: Recording is active")

        # RECORD FOR 10 SECONDS
        print("Speak normally for 10 seconds...")

        time.sleep(10)

        # END MEETING
        completed_meeting = service.end_meeting(
            meeting.id
        )

        print("END: Meeting ended successfully")
        print(
            f"Ended at: {completed_meeting.ended_at}"
        )

        print(
            "Duration:",
            completed_meeting.duration_seconds,
            "seconds",
        )

        # VERIFY TIMESTAMPS
        if completed_meeting.ended_at is None:
            raise RuntimeError(
                "Meeting end time was not created."
            )

        # VERIFY DURATION
        if completed_meeting.duration_seconds is None:
            raise RuntimeError(
                "Meeting duration was not calculated."
            )

        if completed_meeting.duration_seconds < 1:
            raise RuntimeError(
                "Meeting duration should be at least 1 second."
            )

        print(
            "VERIFY: Meeting duration is correct"
        )

        # VERIFY AUDIO PATH
        if not completed_meeting.audio_path:
            raise RuntimeError(
                "Audio path was not saved."
            )

        print(
            "AUDIO PATH:",
            completed_meeting.audio_path,
        )

        audio_path = Path(
            completed_meeting.audio_path
        )

        if not audio_path.exists():
            raise RuntimeError(
                "Saved audio file does not exist."
            )

        if audio_path.stat().st_size <= 0:
            raise RuntimeError(
                "Saved audio file is empty."
            )

        print(
            "AUDIO: Recording file verified"
        )

        print(
            f"Audio file size: "
            f"{audio_path.stat().st_size} bytes"
        )

        # VERIFY DATABASE VALUE
        retrieved_meeting = service.get_meeting(
            meeting.id
        )

        if retrieved_meeting is None:
            raise RuntimeError(
                "Meeting could not be retrieved."
            )

        if retrieved_meeting.audio_path != str(
            audio_path
        ):
            raise RuntimeError(
                "Audio path was not persisted correctly."
            )

        print(
            "DATABASE: Audio path persisted successfully"
        )

        # CLEANUP
        service.delete_meeting(
            meeting.id
        )

        print(
            "CLEANUP: Meeting and audio deleted"
        )

        if audio_path.exists():
            raise RuntimeError(
                "Audio file still exists after cleanup."
            )

        print(
            "VERIFY: Audio file cleanup successful"
        )

        print(
            "Meeting audio service test "
            "completed successfully."
        )

    finally:
        session.close()


if __name__ == "__main__":
    test_meeting_service()