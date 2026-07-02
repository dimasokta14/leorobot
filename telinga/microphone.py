"""telinga/microphone.py — Capture audio USB mic, streaming + clap detect.

Kalau pyaudio / USB mic tidak tersedia (dev machine), listener jalan
dalam mode simulasi (thread idle, tidak crash) supaya main.py tetap
bisa start.
"""

import audioop
import logging
import threading
from typing import Optional

from config import MicConfig
from nyawa.event_bus import Event, EventBus

logger = logging.getLogger(__name__)

try:
    import pyaudio

    HAS_PYAUDIO = True
except ImportError:  # pragma: no cover - dev machine tanpa pyaudio
    pyaudio = None
    HAS_PYAUDIO = False


class MicrophoneListener:
    def __init__(self, event_bus: EventBus, config: MicConfig):
        self._bus = event_bus
        self._config = config
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._pa = None
        self._stream = None

    def start(self) -> None:
        if self._running:
            return
        if not HAS_PYAUDIO:
            logger.warning("pyaudio tidak tersedia — MicrophoneListener jalan dalam mode simulasi")
            return
        try:
            self._pa = pyaudio.PyAudio()
            self._stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=self._config.CHANNELS,
                rate=self._config.SAMPLE_RATE,
                input=True,
                input_device_index=self._config.DEVICE_INDEX,
                frames_per_buffer=self._config.CHUNK_SIZE,
            )
        except Exception:
            logger.exception("Gagal membuka USB microphone")
            self._stream = None
            return

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="MicrophoneListener")
        self._thread.start()
        logger.info("MicrophoneListener started")

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2)
        if self._stream is not None:
            self._stream.stop_stream()
            self._stream.close()
        if self._pa is not None:
            self._pa.terminate()

    def record_clip(self, duration: float) -> bytes:
        """Capture audio untuk STT (dipakai Phase 3)."""
        if not HAS_PYAUDIO or self._stream is None:
            return b""
        frames = []
        n_chunks = int(self._config.SAMPLE_RATE / self._config.CHUNK_SIZE * duration)
        for _ in range(n_chunks):
            frames.append(self._stream.read(self._config.CHUNK_SIZE, exception_on_overflow=False))
        return b"".join(frames)

    def _run(self) -> None:
        while self._running:
            try:
                chunk = self._stream.read(self._config.CHUNK_SIZE, exception_on_overflow=False)
            except Exception:
                continue
            if self._detect_clap(chunk):
                self._bus.publish(Event(type="CLAP_DETECTED", source="telinga.microphone"))

    def _detect_clap(self, chunk: bytes) -> bool:
        """Internal: amplitude check terhadap CLAP_THRESHOLD."""
        if not chunk:
            return False
        amplitude = audioop.rms(chunk, 2)
        return amplitude >= self._config.CLAP_THRESHOLD
