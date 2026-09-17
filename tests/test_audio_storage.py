from pathlib import Path

import numpy as np

from audio.storage import AudioStorageService


def test_audio_storage() -> None:
    """
    Test saving, checking and deleting an audio file.
    """

    storage = AudioStorageService(
        storage_directory="storage"
    )

    # Create test audio data.
    sample_rate = 16_000

    audio = np.zeros(
        sample_rate,
        dtype=np.float32,
    )

    print("Creating test audio data...")

    # SAVE
    audio_path = storage.save_audio(
        audio=audio,
        sample_rate=sample_rate,
        meeting_id=999,
    )

    print(
        f"Audio saved: {audio_path}"
    )

    # EXISTS
    if not storage.audio_exists(audio_path):
        raise RuntimeError(
            "Saved audio file does not exist."
        )

    print("EXISTS: Audio file verified")

    # FILE SIZE
    file_size = Path(audio_path).stat().st_size

    if file_size <= 0:
        raise RuntimeError(
            "Audio file is empty."
        )

    print(
        f"FILE SIZE: {file_size} bytes"
    )

    # DELETE
    storage.delete_audio(audio_path)

    print("DELETE: Audio file deleted")

    # VERIFY DELETION
    if storage.audio_exists(audio_path):
        raise RuntimeError(
            "Audio file still exists after deletion."
        )

    print(
        "VERIFY: Audio file successfully removed"
    )

    print(
        "Audio storage test completed successfully."
    )


if __name__ == "__main__":
    test_audio_storage()