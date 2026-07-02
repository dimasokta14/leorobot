"""jiwa/mood.py — MoodEngine: state machine mood robot.

Mood berpindah dengan dua cara:
1. Natural transition — probabilistic, dipanggil lewat update() tiap tick.
2. External trigger — event dari modul lain lewat trigger(event_type).
"""

import logging
import random
from typing import Dict, List, Tuple

from nyawa.event_bus import EventBus

logger = logging.getLogger(__name__)

MOODS = ["idle", "happy", "sad", "curious", "sleepy", "excited", "surprised", "bored"]

TRANSITIONS: Dict[str, List[Tuple[str, float]]] = {
    "idle": [("happy", 0.3), ("curious", 0.3), ("sleepy", 0.2), ("bored", 0.2)],
    "happy": [("idle", 0.4), ("excited", 0.3), ("curious", 0.3)],
    "sad": [("idle", 0.5), ("curious", 0.3), ("happy", 0.2)],
    "curious": [("idle", 0.4), ("happy", 0.3), ("excited", 0.3)],
    "sleepy": [("idle", 0.6), ("sad", 0.2), ("sleepy", 0.2)],
    "excited": [("happy", 0.4), ("idle", 0.3), ("curious", 0.3)],
    "surprised": [("curious", 0.4), ("happy", 0.3), ("idle", 0.3)],
    "bored": [("idle", 0.5), ("curious", 0.3), ("sleepy", 0.2)],
}

MIN_HOLD_SEC = 4.0
MAX_HOLD_SEC = 10.0


class MoodEngine:
    def __init__(self, event_bus: EventBus, fps: int = 20):
        self._bus = event_bus
        self._fps = fps
        self._mood = "idle"
        self._tick = 0
        self._last_transition_tick = 0
        self._hold_ticks = self._random_hold_ticks()

    def update(self) -> None:
        """Panggil tiap tick (dari Animator loop)."""
        self._tick += 1
        if self._tick - self._last_transition_tick >= self._hold_ticks:
            self._natural_transition()

    def trigger(self, event: str) -> None:
        """External event trigger — override mood langsung."""
        from jiwa.events import EVENT_MOOD_MAP

        target = EVENT_MOOD_MAP.get(event)
        if target is None:
            return
        if isinstance(target, (tuple, list)):
            target = random.choice(target)
        self._set_mood(target)

    @property
    def mood(self) -> str:
        return self._mood

    @property
    def tick(self) -> int:
        return self._tick

    def _natural_transition(self) -> None:
        options = TRANSITIONS.get(self._mood)
        if not options:
            return
        moods, weights = zip(*options)
        next_mood = random.choices(moods, weights=weights, k=1)[0]
        self._set_mood(next_mood)

    def _set_mood(self, mood: str) -> None:
        if mood not in MOODS:
            logger.warning("Mood tidak dikenal: %s", mood)
            return
        if mood != self._mood:
            logger.info("Mood berubah: %s -> %s", self._mood, mood)
        self._mood = mood
        self._last_transition_tick = self._tick
        self._hold_ticks = self._random_hold_ticks()

    def _random_hold_ticks(self) -> int:
        seconds = random.uniform(MIN_HOLD_SEC, MAX_HOLD_SEC)
        return max(1, int(seconds * self._fps))
