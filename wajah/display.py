"""wajah/display.py — Driver layar ST7789 1.3" (240x240) via SPI.

Pakai library https://github.com/pkkirilov/ST7789 (bukan pimoroni st7789)
— cocok untuk modul ST7789 7-pin tanpa CS pin yang dipakai robot ini.
Library ini tidak ada di PyPI, jadi harus di-vendor manual ke venv (lihat
setup.sh) dan bergantung pada Adafruit_GPIO untuk akses SPI/GPIO.

Kalau hardware SPI/ST7789 atau dependency-nya tidak terdeteksi (mis.
dijalankan di dev machine tanpa layar fisik), driver otomatis masuk mode
simulasi: semua method jadi no-op supaya modul lain tetap bisa jalan &
ditest.
"""

import logging

from PIL import Image

from config import DisplayConfig

logger = logging.getLogger(__name__)

PWM_FREQ_HZ = 1000


class DisplayDriver:
    def __init__(self, config: DisplayConfig):
        self.config = config
        self._device = None
        self._gpio = None
        self._pwm = None
        self._simulated = False
        self._backlight_level = 100

    def init(self) -> None:
        """SPI init + backlight on."""
        try:
            import Adafruit_GPIO.SPI as SPI
            import ST7789

            spi = SPI.SpiDev(
                self.config.SPI_PORT,
                self.config.SPI_CS,
                max_speed_hz=self.config.SPI_SPEED_HZ,
            )
            self._device = ST7789.ST7789(
                spi=spi,
                rst=self.config.RST_PIN,
                dc=self.config.DC_PIN,
                led=self.config.BL_PIN,
                width=self.config.WIDTH,
                height=self.config.HEIGHT,
            )
            self._device.begin()
            self._device.clear()
            logger.info("ST7789 display initialized (pkkirilov driver)")
        except Exception:
            logger.warning(
                "ST7789 hardware/driver tidak terdeteksi — jalan dalam mode simulasi (tanpa layar fisik)"
            )
            self._simulated = True

        self._init_backlight_pwm()
        self.on()

    def show(self, image: Image.Image) -> None:
        """Render PIL image ke layar."""
        if self._simulated or self._device is None:
            return
        if self.config.ROTATION:
            image = image.rotate(self.config.ROTATION)
        self._device.display(image)

    def brightness(self, level: int) -> None:
        """0-100%."""
        self._backlight_level = max(0, min(100, level))
        if self._simulated:
            return
        if self._pwm is not None:
            self._pwm.ChangeDutyCycle(self._backlight_level)
        elif self._gpio is not None:
            self._gpio.output(self.config.BL_PIN, self._backlight_level > 0)

    def off(self) -> None:
        """Matikan backlight."""
        self.brightness(0)

    def on(self) -> None:
        self.brightness(100)

    def _init_backlight_pwm(self) -> None:
        """Setup software PWM di BL_PIN untuk brightness bertahap (0-100%).

        Driver ST7789 sendiri cuma nyalain backlight ON penuh lewat pin
        biasa saat begin(); untuk dukung brightness() kita ambil alih pin
        BL_PIN itu langsung pakai RPi.GPIO PWM (dipanggil setelah begin()
        supaya tidak bentrok dengan setup pin awal si driver).
        """
        if self._simulated:
            return
        try:
            import RPi.GPIO as GPIO

            self._gpio = GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self.config.BL_PIN, GPIO.OUT)
            self._pwm = GPIO.PWM(self.config.BL_PIN, PWM_FREQ_HZ)
            self._pwm.start(100)
        except Exception:
            logger.warning("PWM backlight tidak tersedia — brightness() jadi on/off saja")
            self._pwm = None
