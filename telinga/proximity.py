"""telinga/proximity.py — Sensor ultrasonik HC-SR04, cek jarak tiap 200ms.

PERINGATAN HARDWARE: pin ECHO wajib pakai voltage divider (5V -> 3.3V)
sebelum masuk GPIO Raspberry Pi, kalau tidak bisa merusak board.
"""

import logging
import threading
import time
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

SPEED_OF_SOUND_CM_PER_S = 34300
ECHO_TIMEOUT_SEC = 0.03


class ProximitySensor:
    def __init__(self, event_bus: EventBus, config: Optional[MicConfig] = None):
        self._bus = event_bus
        self._config = config or MicConfig()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._was_close = False

    def start(self) -> None:
        if self._running:
            return
        if HAS_GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self._config.TRIG_PIN, GPIO.OUT)
            GPIO.setup(self._config.ECHO_PIN, GPIO.IN)
            GPIO.output(self._config.TRIG_PIN, False)
        else:
            logger.warning("RPi.GPIO tidak tersedia — ProximitySensor jalan dalam mode simulasi")

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="ProximitySensor")
        self._thread.start()
        logger.info("ProximitySensor started (poll tiap %.0fms)", self._config.PROXIMITY_POLL_SEC * 1000)

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2)

    def read_distance_cm(self) -> Optional[float]:
        """Trigger pulse + ukur lebar pulse echo. None kalau hardware tidak ada / timeout."""
        if not HAS_GPIO:
            return None
        try:
            GPIO.output(self._config.TRIG_PIN, True)
            time.sleep(0.00001)
            GPIO.output(self._config.TRIG_PIN, False)

            timeout_at = time.time() + ECHO_TIMEOUT_SEC
            while GPIO.input(self._config.ECHO_PIN) == 0:
                pulse_start = time.time()
                if pulse_start > timeout_at:
                    return None

            timeout_at = time.time() + ECHO_TIMEOUT_SEC
            while GPIO.input(self._config.ECHO_PIN) == 1:
                pulse_end = time.time()
                if pulse_end > timeout_at:
                    return None

            duration = pulse_end - pulse_start
            return (duration * SPEED_OF_SOUND_CM_PER_S) / 2
        except RuntimeError:
            return None

    def _run(self) -> None:
        while self._running:
            distance = self.read_distance_cm()
            is_close = distance is not None and distance <= self._config.PROXIMITY_CM
            if is_close and not self._was_close:
                self._bus.publish(
                    Event(type="OBJECT_CLOSE", data=distance, source="telinga.proximity")
                )
            self._was_close = is_close
            time.sleep(self._config.PROXIMITY_POLL_SEC)
