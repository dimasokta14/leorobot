"""mulut/tts.py — Text-to-speech offline via espeak-ng.

speak() fire & forget di thread terpisah; speak_sync() blocking.
Emit SPEAKING_START sebelum bicara dan SPEAKING_END setelah selesai,
supaya Animator bisa menganimasikan mulut.
"""

import logging
import subprocess
import threading
from typing import Optional

from config import AudioConfig
from nyawa.event_bus import Event, EventBus

logger = logging.getLogger(__name__)


class TextToSpeech:
    def __init__(self, event_bus: EventBus, config: AudioConfig):
        self._bus = event_bus
        self._config = config
        self._process: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None

    def speak(self, text: str, lang: str = "id") -> None:
        """Fire & forget."""
        self._thread = threading.Thread(
            target=self.speak_sync, args=(text,), daemon=True, name="TTS"
        )
        self._thread.start()

    def speak_sync(self, text: str) -> None:
        """Blocking. espeak-ng -v id+m3 -s 140 -p 60 '{text}'"""
        self._bus.publish(Event(type="SPEAKING_START", data=text, source="mulut.tts"))
        try:
            cmd = [
                "espeak-ng",
                "-v",
                self._config.TTS_VOICE,
                "-s",
                str(self._config.TTS_SPEED),
                "-p",
                str(self._config.TTS_PITCH),
                text,
            ]
            self._process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self._process.wait()
        except FileNotFoundError:
            logger.warning("espeak-ng tidak ditemukan — TTS dilewati: %s", text)
        finally:
            self._process = None
            self._bus.publish(Event(type="SPEAKING_END", source="mulut.tts"))

    def stop(self) -> None:
        if self._process is not None:
            self._process.terminate()
