import time

from services.api_client import APIClient


RECORDING_DURATION_SECONDS = 30


def test_transcript_api() -> None:
    """
    Test the complete meeting recording and
    transcription API workflow using a 30-second
    microphone recording.
    """

    client = APIClient(
        base_url="http://127.0.0.1:8000"
    )

    meeting_id = None
    audio_path = None

    # --------------------------------------------------
    # CREATE MEETING
    # --------------------------------------------------

    print()
    print("=" * 60)
    print("AI MEETING INTELLIGENCE - 30 SECOND TEST")
    print("=" * 60)

    print()
    print("Creating meeting...")

    meeting = client.start_meeting(
        title="30 Second Voice Transcription Test"
    )

    meeting_id = meeting["id"]

    print(
        f"Meeting created successfully: {meeting_id}"
    )

    # --------------------------------------------------
    # RECORD AUDIO
    # --------------------------------------------------

    print()
    print("=" * 60)
    print("RECORDING STARTED")
    print("=" * 60)

    print()
    print(
        f"You have {RECORDING_DURATION_SECONDS} seconds."
    )
    print("Please speak clearly.")
    print()
    print("Suggested speech:")
    print(
        "This is a thirty second test of the "
        "AI Meeting Intelligence project."
    )
    print(
        "The system is recording my voice, "
        "saving the audio, and converting my "
        "speech into text using Whisper."
    )
    print(
        "Later, the system will generate "
        "summaries, key points, decisions, "
        "action items and minutes of meeting."
    )

    print()

    # Countdown-style progress
    for remaining in range(
        RECORDING_DURATION_SECONDS,
        0,
        -1,
    ):
        print(
            f"\rRecording... {remaining:02d} seconds remaining",
            end="",
            flush=True,
        )

        time.sleep(1)

    print()
    print()
    print("30 seconds completed.")

    # --------------------------------------------------
    # END MEETING
    # --------------------------------------------------

    print()
    print("Stopping recording...")

    completed_meeting = client.end_meeting(
        meeting_id
    )

    audio_path = completed_meeting["audio_path"]

    print()
    print("Recording stopped successfully.")

    print(
        f"Audio file: {audio_path}"
    )

    # --------------------------------------------------
    # TRANSCRIBE
    # --------------------------------------------------

    print()
    print("=" * 60)
    print("WHISPER TRANSCRIPTION")
    print("=" * 60)

    print()
    print(
        "Transcribing with Whisper Base..."
    )
    print(
        "Please wait..."
    )

    transcript = client.transcribe_meeting(
        meeting_id
    )

    # --------------------------------------------------
    # DISPLAY RESULT
    # --------------------------------------------------

    print()
    print("=" * 60)
    print("TRANSCRIPTION RESULT")
    print("=" * 60)

    print()
    print(
        f"Transcript ID: "
        f"{transcript['id']}"
    )

    print(
        f"Language: "
        f"{transcript['language']}"
    )

    print(
        "Language probability: "
        f"{transcript['language_probability']}"
    )

    print()
    print("YOUR VOICE → TEXT")
    print("-" * 60)
    print(
        transcript["full_text"]
    )
    print("-" * 60)

    # --------------------------------------------------
    # VERIFY RETRIEVAL
    # --------------------------------------------------

    print()
    print(
        "Checking transcript retrieval..."
    )

    retrieved = client.get_meeting_transcript(
        meeting_id
    )

    if retrieved["id"] != transcript["id"]:
        raise RuntimeError(
            "Retrieved transcript ID does not match."
        )

    print(
        "Transcript retrieval: SUCCESS"
    )

    # --------------------------------------------------
    # SUCCESS
    # --------------------------------------------------

    print()
    print("=" * 60)
    print("30 SECOND TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)

    print()
    print(
        "🎙️ Audio recording: SUCCESS"
    )

    print(
        "📝 Transcription: SUCCESS"
    )

    print(
        "🗄️ PostgreSQL storage: SUCCESS"
    )

    print(
        "🔌 FastAPI communication: SUCCESS"
    )

    print()
    print(
        "Audio file has been preserved so "
        "you can play your recording."
    )

    print(
        f"Audio path: {audio_path}"
    )

    print()
    print(
        "Meeting ID has NOT been deleted."
    )

    print(
        f"Meeting ID: {meeting_id}"
    )


if __name__ == "__main__":
    test_transcript_api()