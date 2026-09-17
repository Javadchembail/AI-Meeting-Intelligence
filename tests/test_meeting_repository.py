from datetime import datetime, timezone

from backend.database.session import SessionLocal
from backend.repositories.meeting_repository import MeetingRepository


def test_meeting_repository() -> None:
    """
    Test the basic MeetingRepository CRUD workflow.
    """

    session = SessionLocal()

    try:
        repository = MeetingRepository(session)

        # CREATE
        meeting = repository.create(
            title="Repository Test Meeting",
            started_at=datetime.now(timezone.utc),
        )

        print("CREATE: Meeting created")
        print(f"Meeting ID: {meeting.id}")
        print(f"Meeting title: {meeting.title}")

        # READ
        retrieved_meeting = repository.get_by_id(
            meeting.id
        )

        if retrieved_meeting is None:
            raise RuntimeError(
                "Meeting could not be retrieved."
            )

        print("READ: Meeting retrieved")
        print(f"Retrieved title: {retrieved_meeting.title}")

        # UPDATE
        retrieved_meeting.title = (
            "Updated Repository Test Meeting"
        )

        updated_meeting = repository.update(
            retrieved_meeting
        )

        print("UPDATE: Meeting updated")
        print(f"Updated title: {updated_meeting.title}")

        # READ AGAIN
        verified_meeting = repository.get_by_id(
            updated_meeting.id
        )

        if verified_meeting is None:
            raise RuntimeError(
                "Updated meeting could not be retrieved."
            )

        print("VERIFY: Updated meeting retrieved")
        print(f"Verified title: {verified_meeting.title}")

        # DELETE
        repository.delete(verified_meeting)

        print("DELETE: Test meeting deleted")
        print("Repository CRUD test completed successfully.")

    finally:
        session.close()


if __name__ == "__main__":
    test_meeting_repository()