"""nyawa/power.py — Monitoring baterai.

Baca voltage dari power module via ADC (mis. MCP3008/ADS1115) kalau
tersedia. Kalau hardware ADC tidak terdeteksi (dev machine, atau board
tanpa power module), modul degrade jadi selalu melaporkan 100%.
"""

import logging
import threading
import time
from typing import Optional

from config import PowerConfig
from nyawa.event_bus import Event, EventBus

logger = logging.getLogger(__name__)


class PowerMonitor:
    def __init__(self, event_bus: EventBus, config: Optional[PowerConfig] = None):
        self._bus = event_bus
        self._config = config or PowerConfig()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._level = 100.0
        self._low_battery_fired = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="PowerMonitor")
        self._thread.start()
        logger.info("PowerMonitor started")

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2)
        logger.info("PowerMonitor stopped")

    @property
    def level(self) -> float:
        """Persentase baterai 0-100."""
        return self._level

    def _run(self) -> None:
        while self._running:
            self._level = self._read_level()
            if self._level <= self._config.LOW_BATTERY_PERCENT:
                if not self._low_battery_fired:
                    self._low_battery_fired = True
                    self._bus.publish(
                        Event(type="BATTERY_LOW", data=self._level, source="nyawa.power")
                    )
            else:
                self._low_battery_fired = False
            time.sleep(self._config.POLL_INTERVAL_SEC)

    def _read_level(self) -> float:
        """Baca voltage dari ADC dan konversi ke persentase.

        Return 100.0 kalau ADC tidak tersedia (mode simulasi / dev).
        """
        try:
            voltage = self._read_voltage()
        except Exception:
            return 100.0
        vmin, vmax = self._config.VOLTAGE_MIN, self._config.VOLTAGE_MAX
        pct = (voltage - vmin) / (vmax - vmin) * 100.0
        return max(0.0, min(100.0, pct))

    def _read_voltage(self) -> float:
        """Placeholder pembacaan ADC — implementasikan sesuai power module
        yang dipakai (mis. INA219, ADS1115, MCP3008)."""
        raise NotImplementedError("ADC hardware belum dikonfigurasi")
