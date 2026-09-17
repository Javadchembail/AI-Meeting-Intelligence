import time
from pathlib import Path

from audio.recorder import AudioRecorder


def test_audio_recording() -> None:
    """
    Test microphone recording and WAV file creation.
    """

    output_path = Path(
        "storage/test_recording.wav"
    )

    recorder = AudioRecorder(
        sample_rate=16_000,
        channels=1,
    )

    print("Starting microphone recording...")
    print("Speak normally for 10 seconds.")

    recorder.start_recording()

    try:
        time.sleep(10)

    finally:
        audio = recorder.stop_recording()

    print("Recording stopped.")
    print(f"Captured samples: {len(audio)}")

    saved_path = recorder.save_recording(
        audio=audio,
        output_path=output_path,
    )

    print(
        f"Recording saved successfully: {saved_path}"
    )

    if not saved_path.exists():
        raise RuntimeError(
            "Audio file was not created."
        )

    if saved_path.stat().st_size == 0:
        raise RuntimeError(
            "Audio file was created but is empty."
        )

    print(
        f"Audio file size: "
        f"{saved_path.stat().st_size} bytes"
    )

    print(
        "Audio recorder test completed successfully."
    )


if __name__ == "__main__":
    test_audio_recording()