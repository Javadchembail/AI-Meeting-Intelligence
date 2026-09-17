"""
SQLAlchemy model package.

Importing the models here ensures that all model classes
are registered with SQLAlchemy's declarative registry.
"""

from backend.models.meeting import Meeting
from backend.models.meeting_analysis import MeetingAnalysis
from backend.models.speaker_segment import SpeakerSegment
from backend.models.transcript import Transcript

__all__ = [
    "Meeting",
    "MeetingAnalysis",
    "SpeakerSegment",
    "Transcript",
]
