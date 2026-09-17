from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel

from core.exceptions import TranscriptionError
from core.logging import logger


@dataclass
class TranscriptionWord:
    """
    Represents a single word with its audio timing.
    """

    word: str
    start: float
    end: float
    probability: float | None = None


@dataclass
class TranscriptionSegment:
    """
    Represents a transcription segment.
    """

    start: float
    end: float
    text: str
    words: list[TranscriptionWord]


@dataclass
class TranscriptionResult:
    """
    Complete transcription result.
    """

    text: str
    language: str | None
    language_probability: float | None
    segments: list[TranscriptionSegment]
    words: list[TranscriptionWord]


class WhisperTranscriptionService:
    """
    Service responsible for transcribing audio
    using faster-whisper.

    Word-level timestamps are enabled so the UI
    can highlight the currently spoken word while
    the recording is being played.

    VAD is disabled for this diagnostic test.
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:

        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type

        self._model: WhisperModel | None = None

    def _load_model(self) -> WhisperModel:
        """
        Load the Whisper model lazily.
        """

        if self._model is not None:
            return self._model

        try:

            logger.info(
                "Loading Whisper model: %s",
                self.model_size,
            )

            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )

            logger.info(
                "Whisper model loaded successfully."
            )

            return self._model

        except Exception as exc:

            logger.exception(
                "Failed to load Whisper model."
            )

            raise TranscriptionError(
                "Unable to load Whisper model."
            ) from exc

    def transcribe(
        self,
        audio_path: str | Path,
    ) -> TranscriptionResult:
        """
        Transcribe an audio file with word-level
        timestamps.
        """

        path = Path(audio_path)

        if not path.exists():

            raise TranscriptionError(
                f"Audio file was not found: {path}"
            )

        if not path.is_file():

            raise TranscriptionError(
                f"Audio path is not a file: {path}"
            )

        try:

            model = self._load_model()

            logger.info(
                "Starting transcription: %s",
                path,
            )

            segments, info = model.transcribe(
                str(path),
                beam_size=5,

                # VAD disabled for diagnostic testing.
                # This allows Whisper to process the
                # complete recording, including music.
                vad_filter=False,

                word_timestamps=True,
            )

            transcription_segments: list[
                TranscriptionSegment
            ] = []

            all_words: list[
                TranscriptionWord
            ] = []

            text_parts: list[str] = []

            for segment in segments:

                segment_words: list[
                    TranscriptionWord
                ] = []

                segment_text = segment.text.strip()

                if segment_text:

                    text_parts.append(
                        segment_text
                    )

                if segment.words:

                    for word in segment.words:

                        word_text = word.word.strip()

                        if not word_text:
                            continue

                        transcription_word = (
                            TranscriptionWord(
                                word=word_text,
                                start=float(
                                    word.start
                                ),
                                end=float(
                                    word.end
                                ),
                                probability=(
                                    float(
                                        word.probability
                                    )
                                    if word.probability
                                    is not None
                                    else None
                                ),
                            )
                        )

                        segment_words.append(
                            transcription_word
                        )

                        all_words.append(
                            transcription_word
                        )

                transcription_segment = (
                    TranscriptionSegment(
                        start=float(
                            segment.start
                        ),
                        end=float(
                            segment.end
                        ),
                        text=segment_text,
                        words=segment_words,
                    )
                )

                transcription_segments.append(
                    transcription_segment
                )

            full_text = " ".join(
                text_parts
            ).strip()

            logger.info(
                "Transcription completed. "
                "Language=%s, segments=%s, words=%s",
                info.language,
                len(transcription_segments),
                len(all_words),
            )

            return TranscriptionResult(
                text=full_text,
                language=info.language,
                language_probability=float(
                    info.language_probability
                ),
                segments=transcription_segments,
                words=all_words,
            )

        except TranscriptionError:
            raise

        except Exception as exc:

            logger.exception(
                "Transcription failed for: %s",
                path,
            )

            raise TranscriptionError(
                "Unable to transcribe audio."
            ) from exc