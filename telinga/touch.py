"""telinga/touch.py — Touch sensor TTP223, interrupt-based (bukan polling)."""

import logging
from typing import Optional

from config import MicConfig
from nyawa.event_bus import Event, EventBus

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO  # type: ignore

    HAS_GPIO = True
except ImportError:  # pragma: no cover - dev machine tanpa RPi.GPIO
    GPIO = None
    HAS_GPIO = False


class TouchSensor:
    HEAD_PIN = 5  # GPIO5 (Pin 29) — touch sensor 1
    BODY_PIN = 6  # GPIO6 (Pin 31) — touch sensor 2

    def __init__(self, event_bus: EventBus, config: Optional[MicConfig] = None):
        self._bus = event_bus
        cfg = config or MicConfig()
        self.HEAD_PIN = cfg.TOUCH_HEAD_PIN
        self.BODY_PIN = cfg.TOUCH_BODY_PIN
        self._head_active = False
        self._body_active = False

    def start(self) -> None:
        """GPIO interrupt setup + start listener."""
        if not HAS_GPIO:
            logger.warning("RPi.GPIO tidak tersedia — TouchSensor jalan dalam mode simulasi")
            return
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.HEAD_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.BODY_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self._head_active = self._add_event_detect(self.HEAD_PIN, self._on_head, "HEAD")
        self._body_active = self._add_event_detect(self.BODY_PIN, self._on_body, "BODY")
        logger.info("TouchSensor started (interrupt-based)")

    def _add_event_detect(self, pin: int, callback, label: str) -> bool:
        try:
            GPIO.add_event_detect(pin, GPIO.RISING, callback=callback, bouncetime=300)
            return True
        except RuntimeError:
            # Sensor belum tentu terpasang di fase development sekarang —
            # jangan sampai bikin seluruh robot gagal boot.
            logger.warning(
                "Gagal setup edge detection touch %s (GPIO%d) — sensor ini dilewati",
                label,
                pin,
            )
            return False

    def stop(self) -> None:
        if HAS_GPIO and self._head_active:
            GPIO.remove_event_detect(self.HEAD_PIN)
        if HAS_GPIO and self._body_active:
            GPIO.remove_event_detect(self.BODY_PIN)
        self._head_active = False
        self._body_active = False

    def _on_head(self, channel: int) -> None:
        logger.debug("Touch terdeteksi di HEAD")
        self._bus.publish(Event(type="TOUCHED_HEAD", source="telinga.touch"))

    def _on_body(self, channel: int) -> None:
        logger.debug("Touch terdeteksi di BODY")
        self._bus.publish(Event(type="TOUCHED_BODY", source="telinga.touch"))
