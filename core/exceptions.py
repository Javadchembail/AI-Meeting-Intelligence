class MeetingAssistantException(Exception):
    """Base exception for the AI Meeting Intelligence application."""


class AudioProcessingError(MeetingAssistantException):
    """Raised when audio processing fails."""


class TranscriptionError(MeetingAssistantException):
    """Raised when speech transcription fails."""


class AIProcessingError(MeetingAssistantException):
    """Raised when AI processing fails."""


class DatabaseError(MeetingAssistantException):
    """Raised when a database operation fails."""