"""telinga/voice_trigger.py — Wake word detection ('Hei Emo').

Status: Phase 1 — stub. Wake word engine offline (vosk/snowboy) belum
diintegrasikan; struktur class dibuat sekarang supaya import tidak
error dan bisa diisi penuh di iterasi berikutnya tanpa mengubah API.
"""

import logging
from typing import Optional

from config import MicConfig
from nyawa.event_bus import EventBus

logger = logging.getLogger(__name__)


class VoiceTrigger:
    def __init__(self, event_bus: EventBus, config: Optional[MicConfig] = None):
        self._bus = event_bus
        self._config = config or MicConfig()
        self._running = False

    def start(self) -> None:
        logger.info("VoiceTrigger: wake word detection belum diimplementasikan (Phase 1 stub)")
        self._running = True

    def stop(self) -> None:
        self._running = False
