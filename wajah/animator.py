"""wajah/animator.py — Engine animasi frame-by-frame.

Loop terpisah (thread) yang tiap frame: update mood engine, pilih
fungsi render wajah sesuai mood, terapkan overlay (nama/baterai), lalu
kirim ke DisplayDriver.
"""

import logging
import random
import threading
import time
from typing import Optional

from PIL import ImageDraw

from wajah import faces
from wajah.display import DisplayDriver

logger = logging.getLogger(__name__)

_FACE_FUNCS = {
    "idle": lambda tick, blink: faces.face_idle(tick),
    "happy": lambda tick, blink: faces.face_happy(tick, blink),
    "sad": lambda tick, blink: faces.face_sad(tick),
    "curious": lambda tick, blink: faces.face_curious(tick),
    "sleepy": lambda tick, blink: faces.face_sleepy(tick),
    "excited": lambda tick, blink: faces.face_excited(tick),
    "surprised": lambda tick, blink: faces.face_surprised(tick),
    "bored": lambda tick, blink: faces.face_bored(tick),
}


class Animator:
    def __init__(self, display: DisplayDriver, mood_engine):
        self._display = display
        self._mood = mood_engine
        self._thread: Optional[threading.Thread] = None
        self._running = False

        self._manual_mood: Optional[str] = None
        self._force_blink = False
        self._next_blink_at = 0.0

        self._talking = False
        self._talking_intensity = 0.0

        self._name_overlay: Optional[str] = None
        self._name_overlay_until = 0.0

        self._battery_level: Optional[int] = None
        self._last_activity = time.time()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._next_blink_at = time.time() + random.uniform(
            self._display.config.BLINK_INTERVAL_MIN, self._display.config.BLINK_INTERVAL_MAX
        )
        self._thread = threading.Thread(target=self._run, daemon=True, name="Animator")
        self._thread.start()
        logger.info("Animator started (%s FPS)", self._display.config.FPS)

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2)

    def set_mood(self, mood: str) -> None:
        """Override manual mood yang ditampilkan (di luar MoodEngine)."""
        self._manual_mood = mood
        self._last_activity = time.time()

    def trigger_blink(self) -> None:
        self._force_blink = True

    def set_talking(self, active: bool, intensity: float) -> None:
        self._talking = active
        self._talking_intensity = intensity
        self._last_activity = time.time()

    def show_name(self, name: str, duration: float) -> None:
        self._name_overlay = name
        self._name_overlay_until = time.time() + duration
        self._last_activity = time.time()

    def show_battery(self, level: int) -> None:
        self._battery_level = level

    def _run(self) -> None:
        cfg = self._display.config
        period = 1.0 / max(1, cfg.FPS)
        while self._running:
            frame_start = time.time()
            self._mood.update()
            image = self._render_frame()
            self._apply_overlays(image)
            self._display.show(image)
            elapsed = time.time() - frame_start
            time.sleep(max(0.0, period - elapsed))

    def _render_frame(self):
        tick = self._mood.tick
        if self._talking:
            return faces.face_talking(tick, self._talking_intensity)

        mood_name = self._manual_mood or self._mood.mood
        blink = self._should_blink()
        face_fn = _FACE_FUNCS.get(mood_name, _FACE_FUNCS["idle"])
        return face_fn(tick, blink)

    def _should_blink(self) -> bool:
        now = time.time()
        cfg = self._display.config
        if self._force_blink:
            self._force_blink = False
            self._next_blink_at = now + random.uniform(cfg.BLINK_INTERVAL_MIN, cfg.BLINK_INTERVAL_MAX)
            return True
        if now >= self._next_blink_at:
            self._next_blink_at = now + random.uniform(cfg.BLINK_INTERVAL_MIN, cfg.BLINK_INTERVAL_MAX)
            return True
        return False

    def _apply_overlays(self, image) -> None:
        draw = ImageDraw.Draw(image)
        if self._name_overlay and time.time() < self._name_overlay_until:
            draw.text((10, 10), self._name_overlay, fill=(255, 255, 255))
        elif self._name_overlay and time.time() >= self._name_overlay_until:
            self._name_overlay = None

        if self._battery_level is not None:
            text = f"{self._battery_level}%"
            draw.text((image.width - 40, 8), text, fill=(200, 200, 200))
