from services.api_client import APIClient


MEETING_ID = 40


def test_diarization_api() -> None:
    """
    Test the speaker diarization API using an
    existing completed meeting recording.

    This test intentionally does not create a new
    recording because diarization requires an
    already completed audio file.
    """

    client = APIClient(
        base_url="http://127.0.0.1:8000"
    )

    print()
    print("=" * 60)
    print("AI MEETING INTELLIGENCE - DIARIZATION TEST")
    print("=" * 60)

    # --------------------------------------------------
    # CHECK MEETING
    # --------------------------------------------------

    print()
    print(
        f"Checking meeting {MEETING_ID}..."
    )

    meeting = client.get_meeting(
        MEETING_ID
    )

    print(
        f"Meeting found: {meeting['id']}"
    )

    print(
        f"Title: {meeting['title']}"
    )

    print(
        f"Audio path: {meeting['audio_path']}"
    )

    if not meeting["audio_path"]:
        raise RuntimeError(
            "Meeting does not contain an audio recording."
        )

    # --------------------------------------------------
    # RUN DIARIZATION
    # --------------------------------------------------

    print()
    print("=" * 60)
    print("SPEAKER DIARIZATION")
    print("=" * 60)

    print()
    print(
        "Starting speaker diarization..."
    )

    print(
        "Pyannote will analyze the meeting audio."
    )

    print(
        "This may take some time."
    )

    print()

    diarization = client.diarize_meeting(
        MEETING_ID
    )

    # --------------------------------------------------
    # DISPLAY RESULT
    # --------------------------------------------------

    print()
    print("=" * 60)
    print("DIARIZATION RESULT")
    print("=" * 60)

    print()

    print(
        f"Meeting ID: "
        f"{diarization['meeting_id']}"
    )

    print(
        f"Duration: "
        f"{diarization['duration_seconds']:.2f} seconds"
    )

    print(
        f"Number of speakers: "
        f"{len(diarization['speakers'])}"
    )

    print()

    print("SPEAKERS")
    print("-" * 60)

    for speaker in diarization["speakers"]:
        print(
            f"• {speaker}"
        )

    # --------------------------------------------------
    # DISPLAY SEGMENTS
    # --------------------------------------------------

    print()
    print("SPEAKER SEGMENTS")
    print("-" * 60)

    segments = diarization["segments"]

    for index, segment in enumerate(
        segments,
        start=1,
    ):
        print(
            f"{index:03d}. "
            f"{segment['speaker']} | "
            f"{segment['start']:.2f}s → "
            f"{segment['end']:.2f}s | "
            f"duration: "
            f"{segment['end'] - segment['start']:.2f}s"
        )

    # --------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------

    if diarization["meeting_id"] != MEETING_ID:
        raise RuntimeError(
            "Returned meeting ID does not match."
        )

    if not segments:
        raise RuntimeError(
            "Diarization returned no speaker segments."
        )

    if not diarization["speakers"]:
        raise RuntimeError(
            "Diarization returned no speakers."
        )

    # --------------------------------------------------
    # VERIFY PERSISTED RESULT
    # --------------------------------------------------

    print()
    print("=" * 60)
    print("VERIFYING DATABASE RETRIEVAL")
    print("=" * 60)

    print()

    retrieved = client.get_meeting_diarization(
        MEETING_ID
    )

    if retrieved["meeting_id"] != MEETING_ID:
        raise RuntimeError(
            "Retrieved diarization meeting ID "
            "does not match."
        )

    if not retrieved["segments"]:
        raise RuntimeError(
            "No persisted diarization segments "
            "were returned."
        )

    if len(retrieved["segments"]) != len(
        diarization["segments"]
    ):
        raise RuntimeError(
            "Persisted segment count does not "
            "match the diarization result."
        )

    print(
        "Diarization retrieval: SUCCESS"
    )

    # --------------------------------------------------
    # SUCCESS
    # --------------------------------------------------

    print()
    print("=" * 60)
    print("DIARIZATION TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)

    print()

    print(
        "🎙️ Audio recording: SUCCESS"
    )

    print(
        "🧠 Speaker diarization: SUCCESS"
    )

    print(
        "🗄️ PostgreSQL speaker segments: SUCCESS"
    )

    print(
        "🔌 FastAPI communication: SUCCESS"
    )

    print()

    print(
        f"Meeting ID: {MEETING_ID}"
    )

    print(
        f"Speakers detected: "
        f"{len(diarization['speakers'])}"
    )

    print(
        f"Segments detected: "
        f"{len(diarization['segments'])}"
    )


if __name__ == "__main__":
    test_diarization_api()