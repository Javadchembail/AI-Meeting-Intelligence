from pathlib import Path

from pyannote.audio import Pipeline

from config.settings import settings
from core.exceptions import AudioProcessingError
from diarization.base import DiarizationProvider
from diarization.schemas import (
    DiarizationResult,
    SpeakerSegment,
)


class PyannoteDiarizationProvider(DiarizationProvider):
    """
    Speaker diarization provider powered by pyannote.audio.
    """

    MODEL_NAME = (
        "pyannote/speaker-diarization-community-1"
    )

    def __init__(self) -> None:
        """
        Initialize the provider.

        The pyannote pipeline is intentionally loaded lazily
        when diarization is actually requested.
        """

        self._pipeline = None

    def _load_pipeline(self) -> Pipeline:
        """
        Load the pyannote diarization pipeline.

        Returns:
            Pipeline: Loaded pyannote pipeline.

        Raises:
            AudioProcessingError: If the Hugging Face token
                is missing or the model cannot be loaded.
        """

        if self._pipeline is not None:
            return self._pipeline

        token = getattr(
            settings,
            "huggingface_token",
            "",
        )

        if not token:
            raise AudioProcessingError(
                "HUGGINGFACE_TOKEN is not configured. "
                "Please configure Hugging Face access "
                "before using speaker diarization."
            )

        try:
            self._pipeline = Pipeline.from_pretrained(
                self.MODEL_NAME,
                token=token,
            )

        except Exception as exc:
            raise AudioProcessingError(
                "Unable to load the pyannote speaker "
                "diarization model."
            ) from exc

        return self._pipeline

    def diarize(
        self,
        audio_path: str,
    ) -> DiarizationResult:
        """
        Perform speaker diarization on an audio file.

        Args:
            audio_path: Path to the audio recording.

        Returns:
            DiarizationResult containing speaker segments.
        """

        path = Path(audio_path)

        if not path.exists():
            raise AudioProcessingError(
                f"Audio file was not found: {audio_path}"
            )

        if not path.is_file():
            raise AudioProcessingError(
                f"Audio path is not a file: {audio_path}"
            )

        pipeline = self._load_pipeline()

        try:
            result = pipeline(
                str(path)
            )

        except Exception as exc:
            raise AudioProcessingError(
                "Speaker diarization failed."
            ) from exc

        try:
            diarization = result.speaker_diarization

            segments: list[SpeakerSegment] = []
            speakers: set[str] = set()
            duration_seconds = 0.0

            for turn, _, speaker in diarization.itertracks(
                yield_label=True
            ):
                start = float(turn.start)
                end = float(turn.end)

                segments.append(
                    SpeakerSegment(
                        speaker=str(speaker),
                        start=start,
                        end=end,
                    )
                )

                speakers.add(
                    str(speaker)
                )

                duration_seconds = max(
                    duration_seconds,
                    end,
                )

        except Exception as exc:
            raise AudioProcessingError(
                "Unable to parse the pyannote "
                "speaker diarization result."
            ) from exc

        return DiarizationResult(
            segments=segments,
            speakers=sorted(speakers),
            duration_seconds=duration_seconds,
        )
