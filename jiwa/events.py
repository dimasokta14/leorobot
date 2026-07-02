"""jiwa/events.py — Definisi semua event type + EventHandler.

Tabel event (trigger -> efek mood) sesuai PRD:

| Event            | Trigger dari              | Efek mood            |
|------------------|----------------------------|-----------------------|
| FACE_DETECTED    | mata/detector.py           | -> happy              |
| FACE_LOST        | mata/detector.py           | -> sad / bored        |
| FACE_RECOGNIZED  | mata/recognizer.py         | -> happy + show name  |
| TOUCHED_HEAD     | telinga/touch.py           | -> excited            |
| TOUCHED_BODY     | telinga/touch.py           | -> curious            |
| OBJECT_CLOSE     | telinga/proximity.py       | -> surprised          |
| CLAP_DETECTED    | telinga/microphone.py      | -> surprised          |
| VOICE_COMMAND    | telinga/voice_trigger.py   | -> curious + listen   |
| SPEAKING_START   | mulut/tts.py                | -> talking animation on  |
| SPEAKING_END     | mulut/tts.py                | -> talking animation off |
| BATTERY_LOW      | nyawa/power.py              | -> sleepy             |
| SHUTDOWN         | nyawa/system.py             | -> sad + bye sound    |
"""

import logging
import threading
from typing import Optional

from nyawa.event_bus import EventBus

logger = logging.getLogger(__name__)

# Semua event type yang dikenali sistem
FACE_DETECTED = "FACE_DETECTED"
FACE_LOST = "FACE_LOST"
FACE_RECOGNIZED = "FACE_RECOGNIZED"
TOUCHED_HEAD = "TOUCHED_HEAD"
TOUCHED_BODY = "TOUCHED_BODY"
OBJECT_CLOSE = "OBJECT_CLOSE"
CLAP_DETECTED = "CLAP_DETECTED"
VOICE_COMMAND = "VOICE_COMMAND"
SPEAKING_START = "SPEAKING_START"
SPEAKING_END = "SPEAKING_END"
BATTERY_LOW = "BATTERY_LOW"
SHUTDOWN = "SHUTDOWN"

ALL_EVENTS = [
    FACE_DETECTED,
    FACE_LOST,
    FACE_RECOGNIZED,
    TOUCHED_HEAD,
    TOUCHED_BODY,
    OBJECT_CLOSE,
    CLAP_DETECTED,
    VOICE_COMMAND,
    SPEAKING_START,
    SPEAKING_END,
    BATTERY_LOW,
    SHUTDOWN,
]

# Efek mood per event — dipakai oleh MoodEngine.trigger()
EVENT_MOOD_MAP = {
    FACE_DETECTED: "happy",
    FACE_LOST: ("sad", "bored"),
    FACE_RECOGNIZED: "happy",
    TOUCHED_HEAD: "excited",
    TOUCHED_BODY: "curious",
    OBJECT_CLOSE: "surprised",
    CLAP_DETECTED: "surprised",
    VOICE_COMMAND: "curious",
    BATTERY_LOW: "sleepy",
    SHUTDOWN: "sad",
}

# Sound effect yang diputar untuk tiap event (lihat mulut/sounds.py)
EVENT_SOUND_MAP = {
    FACE_DETECTED: "happy",
    FACE_LOST: "sad",
    FACE_RECOGNIZED: "greeting",
    TOUCHED_HEAD: "excited",
    TOUCHED_BODY: "touched",
    OBJECT_CLOSE: "surprised",
    CLAP_DETECTED: "surprised",
    BATTERY_LOW: "sleepy",
    SHUTDOWN: "shutdown",
}


class EventHandler(threading.Thread):
    """Loop utama pemroses event: update mood + trigger sound/animasi."""

    def __init__(self, event_bus: EventBus, mood_engine, speaker, tts, animator):
        super().__init__(daemon=True, name="EventHandler")
        self._bus = event_bus
        self._mood = mood_engine
        self._speaker = speaker
        self._tts = tts
        self._animator = animator
        self._running = False

    def start(self) -> None:
        self._running = True
        super().start()
        logger.info("EventHandler started")

    def stop(self) -> None:
        self._running = False
        # Bangunkan thread yang sedang blocking di subscribe()
        self._bus.publish(None)  # type: ignore[arg-type]

    def run(self) -> None:
        while self._running:
            event = self._bus.subscribe()
            if event is None or not self._running:
                break
            try:
                self._handle(event)
            except Exception:
                logger.exception("Gagal proses event %s", event)

    def _handle(self, event) -> None:
        etype = event.type

        if etype in EVENT_MOOD_MAP:
            self._mood.trigger(etype)

        if etype == SPEAKING_START:
            if self._animator is not None:
                self._animator.set_talking(True, event.data or 1.0)
            return

        if etype == SPEAKING_END:
            if self._animator is not None:
                self._animator.set_talking(False, 0.0)
            return

        if etype == FACE_RECOGNIZED and self._animator is not None:
            name = event.data or ""
            self._animator.show_name(name, duration=3.0)

        sound_id = EVENT_SOUND_MAP.get(etype)
        if sound_id and self._speaker is not None:
            self._speaker.play(sound_id)

        if etype == SHUTDOWN:
            self._running = False
