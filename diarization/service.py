from pathlib import Path

from core.exceptions import AudioProcessingError
from diarization.base import DiarizationProvider
from diarization.schemas import DiarizationResult


class DiarizationService:
    """
    Service responsible for coordinating speaker diarization.

    The service depends on the abstract DiarizationProvider
    rather than directly depending on pyannote.
    """

    def __init__(
        self,
        provider: DiarizationProvider,
    ) -> None:
        self.provider = provider

    def diarize(
        self,
        audio_path: str,
    ) -> DiarizationResult:
        """
        Perform speaker diarization on an audio file.

        Args:
            audio_path: Path to the audio recording.

        Returns:
            DiarizationResult: Speaker-labeled segments.

        Raises:
            AudioProcessingError: If the audio file does not exist
                or diarization fails.
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

        try:
            return self.provider.diarize(
                audio_path=str(path)
            )

        except AudioProcessingError:
            raise

        except Exception as exc:
            raise AudioProcessingError(
                "Speaker diarization service failed."
            ) from exc
