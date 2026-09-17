from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base

if TYPE_CHECKING:
    from backend.models.meeting import Meeting


class MeetingAnalysis(Base):
    """
    Database model representing AI-generated
    intelligence for a meeting.
    """

    __tablename__ = "meeting_analyses"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    meeting_id: Mapped[int] = mapped_column(
        ForeignKey(
            "meetings.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    key_points: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    decisions: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    action_items: Mapped[
        list[dict[str, Any]]
    ] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    next_steps: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    meeting: Mapped["Meeting"] = relationship(
        back_populates="analysis",
    )
