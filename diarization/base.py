from abc import ABC, abstractmethod

from diarization.schemas import DiarizationResult


class DiarizationProvider(ABC):
    """
    Abstract interface for speaker diarization providers.

    The application depends on this interface rather than
    directly depending on a specific diarization library.
    """

    @abstractmethod
    def diarize(
        self,
        audio_path: str,
    ) -> DiarizationResult:
        """
        Detect speakers and their time segments
        in an audio recording.

        Args:
            audio_path: Path to the audio file.

        Returns:
            DiarizationResult: Speaker-labeled segments.

        Raises:
            NotImplementedError: If the provider does not
                implement this method.
        """

        raise NotImplementedError