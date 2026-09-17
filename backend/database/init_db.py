from backend.database.base import Base
from backend.database.connection import engine

# Import all models here so SQLAlchemy knows about them
# before creating the database tables.
from backend.models.meeting import Meeting
from backend.models.meeting_analysis import MeetingAnalysis
from backend.models.speaker_segment import SpeakerSegment
from backend.models.transcript import Transcript


def initialize_database() -> None:
    """
    Create all database tables defined by SQLAlchemy models.
    """

    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    initialize_database()
    print("Database tables initialized successfully.")
