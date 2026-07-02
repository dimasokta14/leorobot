"""EMO Robot — Konfigurasi terpusat.

Semua konfigurasi modul didefinisikan di sini sebagai dataclass.
Tidak boleh ada nilai hardcode di file modul manapun — modul hanya
menerima instance config lewat constructor.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@dataclass
class DisplayConfig:
    """Konfigurasi layar ST7789 1.3" (wajah/display.py)."""

    SPI_PORT: int = 0
    SPI_CS: int = 0  # GPIO8 (Pin 24)
    DC_PIN: int = 17  # GPIO17 (Pin 11)
    RST_PIN: int = 22  # GPIO22 (Pin 15)
    BL_PIN: int = 27  # GPIO27 (Pin 13)
    WIDTH: int = 240
    HEIGHT: int = 240
    SPI_SPEED_HZ: int = 4_000_000
    ROTATION: int = 90
    FPS: int = 20
    BLINK_INTERVAL_MIN: float = 3.0  # detik
    BLINK_INTERVAL_MAX: float = 7.0
    BG_COLOR: Tuple[int, int, int] = (10, 10, 20)
    IDLE_SCREENSAVER_SEC: float = 300.0  # 5 menit


@dataclass
class MicConfig:
    """Konfigurasi mikrofon, touch sensor, dan ultrasonik (telinga/)."""

    DEVICE_INDEX: Optional[int] = None  # Auto-detect USB mic
    SAMPLE_RATE: int = 44100
    CHUNK_SIZE: int = 1024
    CHANNELS: int = 1  # Mono
    CLAP_THRESHOLD: int = 3000  # Amplitude threshold
    PROXIMITY_CM: float = 15.0  # Jarak 'terlalu dekat' (cm)
    PROXIMITY_POLL_SEC: float = 0.2  # cek jarak tiap 200ms
    TOUCH_HEAD_PIN: int = 17  # GPIO BCM
    TOUCH_BODY_PIN: int = 27
    TRIG_PIN: int = 23  # HC-SR04 TRIG
    ECHO_PIN: int = 24  # HC-SR04 ECHO — wajib pakai voltage divider!
    WAKE_WORD: str = "hei emo"


@dataclass
class AudioConfig:
    """Konfigurasi speaker, sound effect, dan TTS (mulut/)."""

    SOUNDS_DIR: str = os.path.join(BASE_DIR, "mulut", "assets", "sounds")
    VOLUME: float = 0.8  # 0.0 - 1.0
    TTS_LANG: str = "id"
    TTS_VOICE: str = "id+m3"
    TTS_SPEED: int = 140
    TTS_PITCH: int = 60
    LOW_BATTERY_MUTE: bool = True


@dataclass
class CameraConfig:
    """Konfigurasi kamera & face detection — Phase 2 (mata/)."""

    WIDTH: int = 640
    HEIGHT: int = 480
    FRAMERATE: int = 30


@dataclass
class ChatConfig:
    """Konfigurasi AI chat & memory — Phase 3 (otak/)."""

    API_KEY: str = ""
    MODEL: str = "gpt-4o-mini"
    MAX_HISTORY: int = 20


@dataclass
class PowerConfig:
    """Konfigurasi monitoring baterai (nyawa/power.py)."""

    ADC_CHANNEL: int = 0
    POLL_INTERVAL_SEC: float = 30.0
    LOW_BATTERY_PERCENT: float = 20.0
    CRITICAL_BATTERY_PERCENT: float = 5.0
    VOLTAGE_MAX: float = 4.2
    VOLTAGE_MIN: float = 3.0


@dataclass
class Config:
    """Root config object — dipakai oleh main.py."""

    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/var/log/emorobot/robot.log"
    ROBOT_NAME: str = "Emo"

    display: DisplayConfig = field(default_factory=DisplayConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    mic: MicConfig = field(default_factory=MicConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    chat: ChatConfig = field(default_factory=ChatConfig)
    power: PowerConfig = field(default_factory=PowerConfig)
