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
        self._active = False

    def start(self) -> None:
        """GPIO interrupt setup + start listener."""
        if not HAS_GPIO:
            logger.warning("RPi.GPIO tidak tersedia — TouchSensor jalan dalam mode simulasi")
            return
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.HEAD_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.BODY_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.HEAD_PIN, GPIO.RISING, callback=self._on_head, bouncetime=300)
        GPIO.add_event_detect(self.BODY_PIN, GPIO.RISING, callback=self._on_body, bouncetime=300)
        self._active = True
        logger.info("TouchSensor started (interrupt-based)")

    def stop(self) -> None:
        if HAS_GPIO and self._active:
            GPIO.remove_event_detect(self.HEAD_PIN)
            GPIO.remove_event_detect(self.BODY_PIN)
        self._active = False

    def _on_head(self, channel: int) -> None:
        logger.debug("Touch terdeteksi di HEAD")
        self._bus.publish(Event(type="TOUCHED_HEAD", source="telinga.touch"))

    def _on_body(self, channel: int) -> None:
        logger.debug("Touch terdeteksi di BODY")
        self._bus.publish(Event(type="TOUCHED_BODY", source="telinga.touch"))
