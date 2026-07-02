"""mulut/speaker.py — Playback audio via PAM8406 (pygame.mixer), non-blocking.

Sound diputar lewat worker thread + queue supaya play() tidak pernah
blocking caller, dan sound berikutnya otomatis diqueue kalau sedang ada
yang main.
"""

import logging
import os
import queue
import threading
import time
from typing import Optional

from config import AudioConfig
from mulut.sounds import SoundManager
from nyawa.event_bus import EventBus

logger = logging.getLogger(__name__)


class Speaker:
    def __init__(self, event_bus: EventBus, config: AudioConfig):
        self._bus = event_bus
        self._config = config
        self._sounds = SoundManager(config)
        self._queue: "queue.Queue[tuple]" = queue.Queue()
        self._worker: Optional[threading.Thread] = None
        self._running = False
        self._is_playing = False
        self._available = False
        self._pygame = None
        self._muted = False

    def init(self) -> None:
        try:
            import pygame

            pygame.mixer.init()
            self._pygame = pygame
            self._available = True
        except Exception:
            logger.warning("pygame.mixer tidak tersedia — Speaker jalan dalam mode silent")
            self._available = False

        self._running = True
        self._worker = threading.Thread(target=self._run, daemon=True, name="Speaker")
        self._worker.start()

    def play(self, sound_id: str) -> None:
        """Non-blocking play — diqueue kalau sedang ada sound lain main."""
        if self._muted:
            return
        self._queue.put(("id", sound_id))

    def play_file(self, path: str) -> None:
        if self._muted:
            return
        self._queue.put(("file", path))

    def stop(self) -> None:
        self._running = False
        if self._available and self._pygame is not None:
            self._pygame.mixer.stop()
        with self._queue.mutex:
            self._queue.queue.clear()
        if self._worker is not None:
            self._worker.join(timeout=2)

    def set_volume(self, level: float) -> None:
        """0.0 - 1.0"""
        self._config.VOLUME = max(0.0, min(1.0, level))

    def mute(self, muted: bool) -> None:
        self._muted = muted

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def _run(self) -> None:
        while self._running:
            try:
                kind, value = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            path = self._sounds.path_for(value) if kind == "id" else value
            self._play_blocking(path)

    def _play_blocking(self, path: str) -> None:
        if not self._available or not path or not os.path.exists(path):
            logger.debug("Skip play (audio unavailable / file missing): %s", path)
            return
        self._is_playing = True
        try:
            sound = self._pygame.mixer.Sound(path)
            sound.set_volume(self._config.VOLUME)
            channel = sound.play()
            while channel is not None and channel.get_busy() and self._running:
                time.sleep(0.05)
        except Exception:
            logger.exception("Gagal play sound: %s", path)
        finally:
            self._is_playing = False
