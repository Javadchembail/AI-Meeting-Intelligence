
import threading
from pathlib import Path

import numpy as np
import soundfile as sf

from core.exceptions import AudioProcessingError
from core.logging import logger


def _load_sounddevice():
    """
    Load sounddevice only when microphone recording is requested.

    This prevents the FastAPI application from crashing during
    startup on servers without PortAudio.
    """
    try:
        import sounddevice as sd
        return sd
    except (ImportError, OSError) as exc:
        raise AudioProcessingError(
            "Microphone recording is unavailable in this environment. "
            "Run the application on a machine with audio support."
        ) from exc


class AudioRecorder:
    """
    Service responsible for recording microphone audio.

    Supports:
        - Start
        - Pause
        - Resume
        - Stop
        - Audio normalization
        - Peak limiting
        - Real-time microphone RMS level
    """

    def __init__(
        self,
        sample_rate: int = 16_000,
        channels: int = 1,
        target_rms: float = 0.10,
        max_gain: float = 4.0,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.target_rms = target_rms
        self.max_gain = max_gain

        self._recording = False
        self._paused = False

        self._audio_data: list[np.ndarray] = []
        self._lock = threading.Lock()

        # Do not initialize microphone hardware here.
        self._stream = None
        self._current_rms = 0.0

    # ==================================================
    # STATE
    # ==================================================

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def is_paused(self) -> bool:
        return self._paused

    # ==================================================
    # LIVE AUDIO LEVEL
    # ==================================================

    @property
    def current_rms(self) -> float:
        with self._lock:
            return float(self._current_rms)

    @property
    def current_audio_level(self) -> float:
        rms = self.current_rms

        if rms <= 0.0:
            return 0.0

        return float(max(0.0, min(rms / 0.20, 1.0)))

    # ==================================================
    # AUDIO CALLBACK
    # ==================================================

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: object,
    ) -> None:
        """Receive microphone audio and update the live RMS level."""

        if status:
            logger.warning(
                "Audio recording status: %s",
                status,
            )

        try:
            rms = float(
                np.sqrt(
                    np.mean(
                        np.square(indata)
                    )
                )
            )

            with self._lock:
                self._current_rms = rms

        except Exception:
            # A visualizer calculation must not interrupt capture.
            pass

        if not self._recording or self._paused:
            return

        with self._lock:
            self._audio_data.append(indata.copy())

    # ==================================================
    # START
    # ==================================================

    def start_recording(self) -> None:
        """Start a new microphone recording."""

        if self._recording:
            raise AudioProcessingError(
                "Audio recording is already active."
            )

        # Import sounddevice only when recording is requested.
        sd = _load_sounddevice()

        try:
            with self._lock:
                self._audio_data.clear()
                self._current_rms = 0.0

            self._paused = False
            self._recording = True

            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                callback=self._audio_callback,
            )

            self._stream.start()

            logger.info("Audio recording started.")

        except AudioProcessingError:
            self._recording = False
            self._paused = False
            raise

        except Exception as exc:
            self._recording = False
            self._paused = False

            if self._stream is not None:
                try:
                    self._stream.close()
                except Exception:
                    pass

            self._stream = None

            with self._lock:
                self._current_rms = 0.0

            logger.exception(
                "Failed to start audio recording."
            )

            raise AudioProcessingError(
                "Unable to start microphone recording."
            ) from exc

    # ==================================================
    # PAUSE
    # ==================================================

    def pause_recording(self) -> None:
        """Pause capture without closing the microphone stream."""

        if not self._recording:
            raise AudioProcessingError(
                "Audio recording is not active."
            )

        if self._paused:
            raise AudioProcessingError(
                "Audio recording is already paused."
            )

        self._paused = True

        with self._lock:
            self._current_rms = 0.0

        logger.info("Audio recording paused.")

    # ==================================================
    # RESUME
    # ==================================================

    def resume_recording(self) -> None:
        """Resume microphone capture."""

        if not self._recording:
            raise AudioProcessingError(
                "Audio recording is not active."
            )

        if not self._paused:
            raise AudioProcessingError(
                "Audio recording is not paused."
            )

        self._paused = False

        logger.info("Audio recording resumed.")

    # ==================================================
    # NORMALIZATION
    # ==================================================

    def _normalize_audio(
        self,
        audio: np.ndarray,
    ) -> np.ndarray:
        """Normalize recorded speech while preventing clipping."""

        audio = audio - np.mean(audio)

        rms = float(
            np.sqrt(
                np.mean(
                    np.square(audio)
                )
            )
        )

        peak = float(
            np.max(
                np.abs(audio)
            )
        )

        logger.info(
            "Raw audio levels: RMS=%.4f, Peak=%.4f",
            rms,
            peak,
        )

        if rms < 0.0001:
            logger.warning(
                "Audio signal is extremely weak. "
                "Skipping normalization."
            )
            return audio.astype(np.float32)

        gain = min(
            self.target_rms / rms,
            self.max_gain,
        )

        logger.info(
            "Applying automatic audio gain: %.2fx",
            gain,
        )

        audio = audio * gain

        peak_after_gain = float(
            np.max(
                np.abs(audio)
            )
        )

        max_peak = 0.95

        if peak_after_gain > max_peak:
            limiter_gain = max_peak / peak_after_gain
            audio = audio * limiter_gain

            logger.info(
                "Peak limiter applied: %.2fx",
                limiter_gain,
            )

        return np.clip(
            audio,
            -1.0,
            1.0,
        ).astype(np.float32)

    # ==================================================
    # STOP
    # ==================================================

    def stop_recording(self) -> np.ndarray:
        """Stop recording and return the captured audio."""

        if not self._recording:
            raise AudioProcessingError(
                "Audio recording is not active."
            )

        self._recording = False
        self._paused = False

        try:
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
                self._stream = None

            with self._lock:
                if not self._audio_data:
                    self._current_rms = 0.0
                    raise AudioProcessingError(
                        "No audio data was captured."
                    )

                audio = np.concatenate(
                    self._audio_data,
                    axis=0,
                )

                self._audio_data.clear()
                self._current_rms = 0.0

            audio = self._normalize_audio(audio)

            logger.info(
                "Audio recording stopped. Captured %s samples.",
                len(audio),
            )

            return audio

        except AudioProcessingError:
            raise

        except Exception as exc:
            logger.exception(
                "Failed to stop audio recording."
            )

            raise AudioProcessingError(
                "Unable to stop microphone recording."
            ) from exc

    # ==================================================
    # SAVE
    # ==================================================

    def save_recording(
        self,
        audio: np.ndarray,
        output_path: str | Path,
    ) -> Path:
        """Save recorded audio as a WAV file."""

        path = Path(output_path)

        try:
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            sf.write(
                file=path,
                data=audio,
                samplerate=self.sample_rate,
                format="WAV",
            )

            logger.info(
                "Audio recording saved: %s",
                path,
            )

            return path

        except Exception as exc:
            logger.exception(
                "Failed to save audio recording."
            )

            raise AudioProcessingError(
                "Unable to save audio recording."
            ) from exc