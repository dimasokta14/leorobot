"""nyawa/system.py — Inisialisasi GPIO, signal handler, graceful shutdown."""

import logging
import signal
from types import FrameType
from typing import Optional

from nyawa.event_bus import Event, EventBus

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO  # type: ignore

    HAS_GPIO = True
except ImportError:  # pragma: no cover - dev machine tanpa RPi.GPIO
    GPIO = None
    HAS_GPIO = False

SOFT_POWER_BUTTON_PIN = 3


class SystemManager:
    def __init__(self, event_bus: EventBus):
        self._bus = event_bus
        self._modules = []  # daftar object dengan method stop(), urutan shutdown

    def register_modules(self, *modules) -> None:
        """Daftarkan modul (mulut -> wajah -> telinga, dst) untuk graceful shutdown."""
        self._modules = list(modules)

    def init_gpio(self) -> None:
        if not HAS_GPIO:
            logger.warning("RPi.GPIO tidak tersedia — jalan dalam mode simulasi")
            return
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(SOFT_POWER_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        try:
            GPIO.add_event_detect(
                SOFT_POWER_BUTTON_PIN,
                GPIO.FALLING,
                callback=self._on_power_button,
                bouncetime=300,
            )
        except RuntimeError:
            # Fitur opsional (tombol power fisik belum tentu terpasang).
            # Edge detection bisa gagal karena permission/kernel GPIO
            # interface — jangan sampai bikin seluruh robot gagal boot.
            logger.warning(
                "Gagal setup soft power button (GPIO%d) — fitur ini dilewati, "
                "robot tetap jalan tanpa tombol power fisik",
                SOFT_POWER_BUTTON_PIN,
            )
        logger.info("GPIO initialized")

    def register_shutdown(self) -> None:
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        logger.info("Shutdown handler registered (SIGTERM, SIGINT)")

    def graceful_shutdown(self) -> None:
        logger.info("Graceful shutdown dimulai...")
        self._bus.publish(Event(type="SHUTDOWN", source="nyawa.system"))
        for module in self._modules:
            try:
                module.stop()
            except Exception:
                logger.exception("Gagal stop module %s", module)
        if HAS_GPIO:
            GPIO.cleanup()
        logger.info("Graceful shutdown selesai")

    def reboot(self) -> None:
        import subprocess

        self.graceful_shutdown()
        subprocess.run(["sudo", "reboot"], check=False)

    def _on_power_button(self, channel: int) -> None:
        logger.info("Soft power button ditekan")
        self.graceful_shutdown()

    def _handle_signal(self, signum: int, frame: Optional[FrameType]) -> None:
        logger.info("Menerima signal %s", signum)
        self.graceful_shutdown()
