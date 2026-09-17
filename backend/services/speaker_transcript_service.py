from sqlalchemy.orm import Session

from backend.repositories.speaker_segment_repository import (
    SpeakerSegmentRepository,
)
from backend.repositories.transcript_repository import (
    TranscriptRepository,
)
from core.exceptions import AudioProcessingError
from diarization.alignment import (
    SpeakerTranscriptAligner,
    SpeakerTranscriptSegment,
)


class SpeakerTranscriptService:
    """
    Service responsible for generating a speaker-aware
    transcript by combining Whisper word timestamps
    with persisted pyannote speaker segments.
    """

    def __init__(
        self,
        session: Session,
        aligner: SpeakerTranscriptAligner | None = None,
    ) -> None:
        self.session = session

        self.transcript_repository = (
            TranscriptRepository(session)
        )

        self.speaker_repository = (
            SpeakerSegmentRepository(session)
        )

        self.aligner = (
            aligner
            if aligner is not None
            else SpeakerTranscriptAligner()
        )

    def get_speaker_transcript(
        self,
        meeting_id: int,
    ) -> tuple[
        list[str],
        float,
        list[SpeakerTranscriptSegment],
    ]:
        """
        Generate a speaker-aware transcript for a meeting.

        Returns:
            A tuple containing:
            - detected speakers
            - duration in seconds
            - speaker transcript segments

        Raises:
            ValueError:
                If the transcript or diarization result
                does not exist.
            AudioProcessingError:
                If alignment fails unexpectedly.
        """

        transcript = (
            self.transcript_repository.get_by_meeting_id(
                meeting_id
            )
        )

        if transcript is None:
            raise ValueError(
                f"Transcript for meeting {meeting_id} "
                "was not found."
            )

        speaker_segments = (
            self.speaker_repository.get_by_meeting_id(
                meeting_id
            )
        )

        if not speaker_segments:
            raise ValueError(
                f"Diarization results for meeting "
                f"{meeting_id} were not found."
            )

        try:
            words = []

            for item in (
                transcript.word_timestamps or []
            ):
                class TranscriptWord:
                    pass

                word = TranscriptWord()

                word.word = item.get(
                    "word",
                    "",
                )

                word.start = float(
                    item.get(
                        "start",
                        0.0,
                    )
                )

                word.end = float(
                    item.get(
                        "end",
                        0.0,
                    )
                )

                word.probability = item.get(
                    "probability"
                )

                words.append(word)

            if not words:
                raise ValueError(
                    f"Transcript for meeting {meeting_id} "
                    "does not contain word timestamps."
                )

            aligned_words = (
                self.aligner.align_words(
                    words=words,
                    speaker_segments=speaker_segments,
                )
            )

            segments = (
                self.aligner.group_by_speaker(
                    aligned_words
                )
            )

            speakers = sorted(
                {
                    segment.speaker
                    for segment in speaker_segments
                    if segment.speaker
                }
            )

            duration_seconds = max(
                float(segment.end_time)
                for segment in speaker_segments
            )

            return (
                speakers,
                duration_seconds,
                segments,
            )

        except ValueError:
            raise

        except Exception as exc:
            raise AudioProcessingError(
                "Unable to generate speaker-aware "
                "transcript."
            ) from exc
