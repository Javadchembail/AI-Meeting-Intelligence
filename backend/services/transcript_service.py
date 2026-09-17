
import logfire
from sqlalchemy.orm import Session

from backend.models.transcript import Transcript
from backend.repositories.meeting_repository import (
    MeetingRepository,
)
from backend.repositories.transcript_repository import (
    TranscriptRepository,
)
from core.exceptions import TranscriptionError
from core.logging import logger
from rag.chunker import TranscriptChunker
from rag.vector_store import TranscriptVectorStore
from transcription.whisper_service import (
    WhisperTranscriptionService,
)


class TranscriptService:
    """
    Coordinates transcription, persistence, chunking,
    and Qdrant indexing for a meeting.
    """

    def __init__(
        self,
        session: Session,
        transcription_service: (
            WhisperTranscriptionService | None
        ) = None,
        chunker: TranscriptChunker | None = None,
        vector_store: TranscriptVectorStore | None = None,
    ) -> None:

        self.session = session

        self.repository = TranscriptRepository(session)

        self.transcription_service = (
            transcription_service
            if transcription_service is not None
            else WhisperTranscriptionService()
        )

        self.chunker = (
            chunker
            if chunker is not None
            else TranscriptChunker()
        )

        self.vector_store = (
            vector_store
            if vector_store is not None
            else TranscriptVectorStore()
        )

    def transcribe_meeting(
        self,
        meeting_id: int,
    ) -> Transcript:

        with logfire.span(
            "transcript.process_meeting",
            meeting_id=meeting_id,
        ):

            meeting_repository = MeetingRepository(
                self.session
            )

            meeting = meeting_repository.get_by_id(
                meeting_id
            )

            if meeting is None:
                raise ValueError(
                    f"Meeting with ID {meeting_id} "
                    "was not found."
                )

            if not meeting.audio_path:
                raise ValueError(
                    "Meeting does not have an audio recording."
                )

            existing_transcript = (
                self.repository.get_by_meeting_id(
                    meeting_id
                )
            )

            if existing_transcript is not None:
                raise ValueError(
                    "A transcript already exists "
                    "for this meeting."
                )

            try:
                # ------------------------------------------
                # 1. Whisper transcription
                # ------------------------------------------

                logger.info(
                    "Starting transcription for meeting %s.",
                    meeting_id,
                )

                with logfire.span(
                    "transcript.whisper",
                    meeting_id=meeting_id,
                ):
                    result = (
                        self.transcription_service.transcribe(
                            meeting.audio_path
                        )
                    )

                if not result.text.strip():
                    raise TranscriptionError(
                        "Whisper returned an empty transcript."
                    )

                logfire.info(
                    "Whisper transcription completed",
                    meeting_id=meeting_id,
                    language=result.language,
                    word_count=len(result.words),
                )

                # ------------------------------------------
                # 2. Prepare word timestamps
                # ------------------------------------------

                word_timestamps = [
                    {
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                        "probability": word.probability,
                    }
                    for word in result.words
                ]

                # ------------------------------------------
                # 3. Save transcript to PostgreSQL
                # ------------------------------------------

                with logfire.span(
                    "transcript.save_postgres",
                    meeting_id=meeting_id,
                ):
                    transcript = self.repository.create(
                        meeting_id=meeting_id,
                        full_text=result.text,
                        language=result.language,
                        language_probability=(
                            result.language_probability
                        ),
                        word_timestamps=word_timestamps,
                    )

                logger.info(
                    "Transcript saved successfully "
                    "for meeting %s. Words=%s",
                    meeting_id,
                    len(word_timestamps),
                )

                logfire.info(
                    "Transcript saved to PostgreSQL",
                    meeting_id=meeting_id,
                    transcript_id=transcript.id,
                    word_count=len(word_timestamps),
                    language=result.language,
                )

                # ------------------------------------------
                # 4. Split transcript into chunks
                # ------------------------------------------

                with logfire.span(
                    "transcript.chunk",
                    meeting_id=meeting_id,
                ):
                    chunks = self.chunker.split(
                        transcript.full_text
                    )

                logfire.info(
                    "Transcript chunking completed",
                    meeting_id=meeting_id,
                    chunk_count=len(chunks),
                )

                # ------------------------------------------
                # 5. Generate embeddings and index Qdrant
                # ------------------------------------------

                with logfire.span(
                    "transcript.index_qdrant",
                    meeting_id=meeting_id,
                    chunk_count=len(chunks),
                ):
                    indexed_count = (
                        self.vector_store.index_chunks(
                            meeting_id=meeting_id,
                            chunks=chunks,
                        )
                    )

                logger.info(
                    "Transcript indexed successfully "
                    "for meeting %s. Vectors=%s",
                    meeting_id,
                    indexed_count,
                )

                logfire.info(
                    "Transcript indexed in Qdrant",
                    meeting_id=meeting_id,
                    vector_count=indexed_count,
                )

                # ------------------------------------------
                # 6. Return transcript
                # ------------------------------------------

                return transcript

            except TranscriptionError:
                logfire.exception(
                    "Transcription error",
                    meeting_id=meeting_id,
                )
                raise

            except Exception as exc:
                logger.exception(
                    "Failed to transcribe meeting %s.",
                    meeting_id,
                )

                logfire.exception(
                    "Transcript processing failed",
                    meeting_id=meeting_id,
                )

                raise TranscriptionError(
                    "Unable to transcribe meeting audio."
                ) from exc

    def get_transcript(
        self,
        transcript_id: int,
    ) -> Transcript | None:

        return self.repository.get_by_id(
            transcript_id
        )

    def get_meeting_transcript(
        self,
        meeting_id: int,
    ) -> Transcript | None:

        return self.repository.get_by_meeting_id(
            meeting_id
        )