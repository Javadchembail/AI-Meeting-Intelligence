from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base

if TYPE_CHECKING:
    from backend.models.meeting_analysis import MeetingAnalysis
    from backend.models.speaker_segment import SpeakerSegment
    from backend.models.transcript import Transcript


class Meeting(Base):
    """
    Database model representing a meeting.
    """

    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    audio_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    transcript: Mapped["Transcript | None"] = relationship(
        back_populates="meeting",
        uselist=False,
        cascade="all, delete-orphan",
    )

    analysis: Mapped[
        "MeetingAnalysis | None"
    ] = relationship(
        back_populates="meeting",
        uselist=False,
        cascade="all, delete-orphan",
    )

    speaker_segments: Mapped[
        list["SpeakerSegment"]
    ] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="SpeakerSegment.start_time",
    )
