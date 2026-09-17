from pathlib import Path

from backend.database.session import SessionLocal
from backend.models.meeting import Meeting
from backend.services.transcript_service import (
    TranscriptService,
)
from transcription.whisper_service import (
    WhisperTranscriptionService,
)


TEST_AUDIO_PATH = Path(
    "storage/my_voice_test_30s.wav"
)


def test_transcript_service() -> None:
    """
    Test the complete TranscriptService workflow
    using an existing speech recording.
    """

    if not TEST_AUDIO_PATH.exists():
        raise FileNotFoundError(
            f"Test audio file was not found: "
            f"{TEST_AUDIO_PATH}"
        )

    session = SessionLocal()

    test_meeting = None

    try:
        # --------------------------------------------------
        # CREATE TEST MEETING
        # --------------------------------------------------

        test_meeting = Meeting(
            title="Transcript Service Test",
            audio_path=str(TEST_AUDIO_PATH),
        )

        session.add(test_meeting)
        session.commit()
        session.refresh(test_meeting)

        print(
            f"Created test meeting: {test_meeting.id}"
        )

        # --------------------------------------------------
        # CREATE WHISPER SERVICE
        # --------------------------------------------------

        transcription_service = (
            WhisperTranscriptionService(
                model_size="base",
                device="cpu",
                compute_type="int8",
            )
        )

        # --------------------------------------------------
        # CREATE TRANSCRIPT SERVICE
        # --------------------------------------------------

        service = TranscriptService(
            session=session,
            transcription_service=(
                transcription_service
            ),
        )

        # --------------------------------------------------
        # TRANSCRIBE MEETING
        # --------------------------------------------------

        transcript = service.transcribe_meeting(
            meeting_id=test_meeting.id
        )

        print(
            f"Created transcript: {transcript.id}"
        )

        print(
            f"Language: {transcript.language}"
        )

        print(
            "Language probability: "
            f"{transcript.language_probability}"
        )

        print()
        print("Transcript:")
        print("-" * 60)
        print(transcript.full_text)
        print("-" * 60)

        # --------------------------------------------------
        # VALIDATE TRANSCRIPT
        # --------------------------------------------------

        if transcript.id is None:
            raise RuntimeError(
                "Transcript ID was not created."
            )

        if transcript.meeting_id != test_meeting.id:
            raise RuntimeError(
                "Transcript meeting ID is incorrect."
            )

        if not transcript.full_text.strip():
            raise RuntimeError(
                "Transcript text is empty."
            )

        print()
        print(
            "TRANSCRIBE: "
            "Transcript generated successfully"
        )

        # --------------------------------------------------
        # GET TRANSCRIPT BY ID
        # --------------------------------------------------

        retrieved = service.get_transcript(
            transcript_id=transcript.id
        )

        if retrieved is None:
            raise RuntimeError(
                "Transcript could not be retrieved."
            )

        if retrieved.id != transcript.id:
            raise RuntimeError(
                "Retrieved transcript ID is incorrect."
            )

        print(
            "GET TRANSCRIPT: "
            "Transcript retrieved successfully"
        )

        # --------------------------------------------------
        # GET TRANSCRIPT BY MEETING ID
        # --------------------------------------------------

        meeting_transcript = (
            service.get_meeting_transcript(
                meeting_id=test_meeting.id
            )
        )

        if meeting_transcript is None:
            raise RuntimeError(
                "Meeting transcript could not be retrieved."
            )

        if meeting_transcript.id != transcript.id:
            raise RuntimeError(
                "Retrieved meeting transcript "
                "ID does not match."
            )

        if (
            meeting_transcript.meeting_id
            != test_meeting.id
        ):
            raise RuntimeError(
                "Retrieved meeting transcript "
                "has incorrect meeting ID."
            )

        print(
            "GET MEETING TRANSCRIPT: "
            "Transcript retrieved successfully"
        )

        # --------------------------------------------------
        # FINAL SUCCESS
        # --------------------------------------------------

        print()
        print(
            "Transcript service test "
            "completed successfully."
        )

    finally:
        # --------------------------------------------------
        # CLEANUP
        # --------------------------------------------------

        if test_meeting is not None:

            # Retrieve and delete the transcript first.
            cleanup_service = TranscriptService(
                session=session
            )

            transcript = (
                cleanup_service
                .get_meeting_transcript(
                    meeting_id=test_meeting.id
                )
            )

            if transcript is not None:
                cleanup_service.repository.delete(
                    transcript
                )

            # Delete the test meeting.
            session.delete(test_meeting)
            session.commit()

            print(
                f"Cleanup completed for meeting "
                f"{test_meeting.id}"
            )

        session.close()


if __name__ == "__main__":
    test_transcript_service()