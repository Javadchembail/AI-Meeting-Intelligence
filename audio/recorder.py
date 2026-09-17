import threading
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf

from core.exceptions import AudioProcessingError
from core.logging import logger


class AudioRecorder:
    """
    Service responsible for recording microphone audio.

    Supports:
        - Start
        - Pause
        - Resume
        - Stop
        - Automatic audio normalization
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

        # Target average speech loudness.
        self.target_rms = target_rms

        # Safety limit so extremely quiet recordings
        # are not amplified indefinitely.
        self.max_gain = max_gain

        self._recording = False
        self._paused = False

        self._audio_data: list[np.ndarray] = []

        self._lock = threading.Lock()

        self._stream: sd.InputStream | None = None

        # --------------------------------------------------
        # LIVE AUDIO LEVEL
        # --------------------------------------------------

        # Current raw microphone RMS level.
        #
        # This value is updated continuously from the
        # sounddevice callback.
        self._current_rms = 0.0

    # ==================================================
    # STATE
    # ==================================================

    @property
    def is_recording(self) -> bool:
        """Return True when recording is active."""

        return self._recording

    @property
    def is_paused(self) -> bool:
        """Return True when recording is paused."""

        return self._paused

    # ==================================================
    # LIVE AUDIO LEVEL
    # ==================================================

    @property
    def current_rms(self) -> float:
        """
        Return the latest microphone RMS level.

        The value represents the raw microphone signal
        before normalization and peak limiting.

        Returns:
            float: Current RMS audio level.
        """

        with self._lock:
            return float(self._current_rms)

    @property
    def current_audio_level(self) -> float:
        """
        Return a normalized microphone level between 0 and 1.

        This is intended for visualizers.

        Returns:
            float:
                0.0 = silence
                1.0 = very loud input
        """

        rms = self.current_rms

        if rms <= 0.0:
            return 0.0

        # Speech microphones commonly produce relatively
        # small RMS values. Scale the value into a useful
        # visualizer range.
        level = rms / 0.20

        level = max(
            0.0,
            min(
                level,
                1.0,
            ),
        )

        return float(level)

    # ==================================================
    # AUDIO CALLBACK
    # ==================================================

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: sd.CallbackFlags,
    ) -> None:
        """
        Receive microphone audio from sounddevice.

        The callback continuously calculates RMS so the
        UI can later display a microphone-reactive waveform.
        """

        if status:
            logger.warning(
                "Audio recording status: %s",
                status,
            )

        # --------------------------------------------------
        # CALCULATE LIVE MICROPHONE LEVEL
        # --------------------------------------------------

        try:

            rms = float(
                np.sqrt(
                    np.mean(
                        np.square(
                            indata
                        )
                    )
                )
            )

            with self._lock:
                self._current_rms = rms

        except Exception:
            # Never allow visualizer calculation to
            # interrupt microphone capture.
            pass

        # --------------------------------------------------
        # STORE AUDIO
        # --------------------------------------------------

        # Do not store audio when stopped or paused.
        if (
            not self._recording
            or self._paused
        ):
            return

        with self._lock:

            self._audio_data.append(
                indata.copy()
            )

    # ==================================================
    # START
    # ==================================================

    def start_recording(self) -> None:
        """Start a new microphone recording."""

        if self._recording:
            raise AudioProcessingError(
                "Audio recording is already active."
            )

        try:

            with self._lock:

                self._audio_data.clear()

                # Reset live level when a new recording
                # starts.
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

            logger.info(
                "Audio recording started."
            )

        except Exception as exc:

            self._recording = False
            self._paused = False
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
        """
        Pause microphone capture.

        The microphone stream remains open, but
        incoming audio is not stored.
        """

        if not self._recording:
            raise AudioProcessingError(
                "Audio recording is not active."
            )

        if self._paused:
            raise AudioProcessingError(
                "Audio recording is already paused."
            )

        self._paused = True

        # Make the visualizer fall back to silence
        # while the meeting is paused.
        with self._lock:
            self._current_rms = 0.0

        logger.info(
            "Audio recording paused."
        )

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

        logger.info(
            "Audio recording resumed."
        )

    # ==================================================
    # NORMALIZATION
    # ==================================================

    def _normalize_audio(
        self,
        audio: np.ndarray,
    ) -> np.ndarray:
        """
        Normalize recorded speech to a healthy
        listening level while preventing clipping.
        """

        # Remove DC offset.
        audio = audio - np.mean(audio)

        # Calculate RMS.
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
            "Raw audio levels: "
            "RMS=%.4f, Peak=%.4f",
            rms,
            peak,
        )

        # Avoid amplification if the recording
        # contains essentially no signal.
        if rms < 0.0001:

            logger.warning(
                "Audio signal is extremely weak. "
                "Skipping normalization."
            )

            return audio

        # Calculate gain needed to reach target RMS.
        gain = self.target_rms / rms

        # Prevent excessive amplification.
        gain = min(
            gain,
            self.max_gain,
        )

        logger.info(
            "Applying automatic audio gain: %.2fx",
            gain,
        )

        audio = audio * gain

        # ==================================================
        # PEAK LIMITER
        # ==================================================

        peak_after_gain = float(
            np.max(
                np.abs(audio)
            )
        )

        # Keep a little headroom below digital full scale.
        max_peak = 0.95

        if peak_after_gain > max_peak:

            limiter_gain = (
                max_peak
                / peak_after_gain
            )

            audio = (
                audio
                * limiter_gain
            )

            logger.info(
                "Peak limiter applied: %.2fx",
                limiter_gain,
            )

        # Final safety clamp.
        audio = np.clip(
            audio,
            -1.0,
            1.0,
        )

        return audio.astype(
            np.float32
        )

    # ==================================================
    # STOP
    # ==================================================

    def stop_recording(
        self,
    ) -> np.ndarray:
        """
        Stop recording and return the complete
        recorded audio.

        Audio captured during pause periods is
        intentionally excluded.
        """

        if not self._recording:

            raise AudioProcessingError(
                "Audio recording is not active."
            )

        try:

            self._recording = False
            self._paused = False

            if self._stream is not None:

                self._stream.stop()
                self._stream.close()

                self._stream = None

            with self._lock:

                if not self._audio_data:

                    raise AudioProcessingError(
                        "No audio data was captured."
                    )

                audio = np.concatenate(
                    self._audio_data,
                    axis=0,
                )

                self._audio_data.clear()

                # Reset visualizer level after stopping.
                self._current_rms = 0.0

            # Normalize the complete recording.
            audio = self._normalize_audio(
                audio
            )

            logger.info(
                "Audio recording stopped. "
                "Captured %s samples.",
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