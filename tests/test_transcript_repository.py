from backend.database.session import SessionLocal
from backend.models.meeting import Meeting
from backend.repositories.transcript_repository import (
    TranscriptRepository,
)


def test_transcript_repository() -> None:
    """
    Test transcript repository CRUD operations.
    """

    session = SessionLocal()

    try:
        # CREATE A TEST MEETING
        meeting = Meeting(
            title="Transcript Repository Test"
        )

        session.add(meeting)
        session.commit()
        session.refresh(meeting)

        print(
            f"Created test meeting: {meeting.id}"
        )

        repository = TranscriptRepository(session)

        # CREATE TRANSCRIPT
        transcript = repository.create(
            meeting_id=meeting.id,
            full_text=(
                "This is a test meeting transcript."
            ),
            language="en",
            language_probability=0.98,
        )

        print(
            f"Created transcript: {transcript.id}"
        )

        if transcript.id is None:
            raise RuntimeError(
                "Transcript ID was not created."
            )

        if transcript.meeting_id != meeting.id:
            raise RuntimeError(
                "Transcript meeting ID is incorrect."
            )

        print("CREATE: Transcript created successfully")

        # GET BY ID
        retrieved = repository.get_by_id(
            transcript.id
        )

        if retrieved is None:
            raise RuntimeError(
                "Transcript could not be retrieved by ID."
            )

        if retrieved.full_text != (
            "This is a test meeting transcript."
        ):
            raise RuntimeError(
                "Transcript text is incorrect."
            )

        print("GET BY ID: Transcript retrieved successfully")

        # GET BY MEETING ID
        retrieved_by_meeting = (
            repository.get_by_meeting_id(
                meeting.id
            )
        )

        if retrieved_by_meeting is None:
            raise RuntimeError(
                "Transcript could not be retrieved "
                "by meeting ID."
            )

        print(
            "GET BY MEETING ID: "
            "Transcript retrieved successfully"
        )

        # UPDATE
        retrieved.full_text = (
            "Updated transcript content."
        )

        retrieved.language_probability = 0.99

        updated = repository.update(
            retrieved
        )

        if updated.full_text != (
            "Updated transcript content."
        ):
            raise RuntimeError(
                "Transcript update failed."
            )

        if updated.language_probability != 0.99:
            raise RuntimeError(
                "Transcript confidence update failed."
            )

        print(
            "UPDATE: Transcript updated successfully"
        )

        # DELETE TRANSCRIPT
        repository.delete(updated)

        deleted = repository.get_by_id(
            transcript.id
        )

        if deleted is not None:
            raise RuntimeError(
                "Transcript still exists after deletion."
            )

        print(
            "DELETE: Transcript deleted successfully"
        )

        # DELETE TEST MEETING
        session.delete(meeting)
        session.commit()

        print(
            "CLEANUP: Test meeting deleted"
        )

        print(
            "Transcript repository test "
            "completed successfully."
        )

    finally:
        session.close()


if __name__ == "__main__":
    test_transcript_repository()