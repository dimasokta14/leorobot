"""wajah/display.py — Driver layar ST7789 1.3" (240x240) via SPI.

Kalau hardware SPI/ST7789 tidak terdeteksi (mis. dijalankan di dev
machine tanpa layar fisik), driver otomatis masuk mode simulasi: semua
method jadi no-op supaya modul lain tetap bisa jalan & ditest.
"""

import logging

from PIL import Image

from config import DisplayConfig

logger = logging.getLogger(__name__)


class DisplayDriver:
    def __init__(self, config: DisplayConfig):
        self.config = config
        self._device = None
        self._simulated = False
        self._backlight_level = 100

    def init(self) -> None:
        """SPI init + backlight on."""
        try:
            import ST7789

            self._device = ST7789.ST7789(
                port=self.config.SPI_PORT,
                cs=self.config.SPI_CS,
                dc=self.config.DC_PIN,
                rst=self.config.RST_PIN,
                backlight=self.config.BL_PIN,
                width=self.config.WIDTH,
                height=self.config.HEIGHT,
                rotation=self.config.ROTATION,
                spi_speed_hz=self.config.SPI_SPEED_HZ,
            )
            self._device.begin()
            logger.info("ST7789 display initialized")
        except Exception:
            logger.warning(
                "ST7789 hardware tidak terdeteksi — jalan dalam mode simulasi (tanpa layar fisik)"
            )
            self._simulated = True
        self.on()

    def show(self, image: Image.Image) -> None:
        """Render PIL image ke layar."""
        if self._simulated or self._device is None:
            return
        self._device.display(image)

    def brightness(self, level: int) -> None:
        """0-100%."""
        self._backlight_level = max(0, min(100, level))
        if not self._simulated and hasattr(self._device, "set_backlight"):
            self._device.set_backlight(self._backlight_level / 100.0)

    def off(self) -> None:
        """Matikan backlight."""
        self.brightness(0)

    def on(self) -> None:
        self.brightness(100)
