from pathlib import Path
from uuid import uuid4

import numpy as np
import soundfile as sf

from core.exceptions import AudioProcessingError
from core.logging import logger


class AudioStorageService:
    """
    Service responsible for storing and managing audio files.
    """

    def __init__(
        self,
        storage_directory: str | Path = "storage",
    ) -> None:
        """
        Initialize the audio storage service.

        Args:
            storage_directory: Directory where audio files
                will be stored.
        """

        self.storage_directory = Path(
            storage_directory
        )

        self.storage_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def generate_audio_path(
        self,
        meeting_id: int | None = None,
    ) -> Path:
        """
        Generate a unique path for an audio recording.

        Args:
            meeting_id: Optional meeting ID associated
                with the recording.

        Returns:
            Path: Unique WAV file path.
        """

        unique_id = uuid4().hex

        if meeting_id is not None:
            filename = (
                f"meeting_{meeting_id}_{unique_id}.wav"
            )
        else:
            filename = (
                f"recording_{unique_id}.wav"
            )

        return self.storage_directory / filename

    def save_audio(
        self,
        audio: np.ndarray,
        sample_rate: int,
        meeting_id: int | None = None,
    ) -> Path:
        """
        Save recorded audio as a WAV file.

        Args:
            audio: Audio samples.
            sample_rate: Audio sample rate.
            meeting_id: Optional meeting ID.

        Returns:
            Path: Path to the saved audio file.

        Raises:
            AudioProcessingError: If saving fails.
        """

        output_path = self.generate_audio_path(
            meeting_id=meeting_id
        )

        try:
            sf.write(
                file=output_path,
                data=audio,
                samplerate=sample_rate,
                format="WAV",
            )

            logger.info(
                "Audio saved successfully: %s",
                output_path,
            )

            return output_path

        except Exception as exc:
            logger.exception(
                "Failed to save audio."
            )

            raise AudioProcessingError(
                "Unable to save audio file."
            ) from exc

    def audio_exists(
        self,
        audio_path: str | Path,
    ) -> bool:
        """
        Check whether an audio file exists.

        Args:
            audio_path: Path to the audio file.

        Returns:
            bool: True if the file exists.
        """

        return Path(audio_path).is_file()

    def delete_audio(
        self,
        audio_path: str | Path,
    ) -> None:
        """
        Delete an audio file.

        Args:
            audio_path: Path to the audio file.

        Raises:
            AudioProcessingError: If deletion fails.
        """

        path = Path(audio_path)

        if not path.exists():
            logger.warning(
                "Audio file does not exist: %s",
                path,
            )
            return

        try:
            path.unlink()

            logger.info(
                "Audio file deleted: %s",
                path,
            )

        except Exception as exc:
            logger.exception(
                "Failed to delete audio file."
            )

            raise AudioProcessingError(
                "Unable to delete audio file."
            ) from exc