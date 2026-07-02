#!/usr/bin/env python3
"""EMO Robot — Main Entry Point"""

import logging
import time

from config import Config
from jiwa.events import EventHandler
from jiwa.mood import MoodEngine
from mulut.speaker import Speaker
from mulut.tts import TextToSpeech
from nyawa.event_bus import EventBus
from nyawa.logger import setup_logger
from nyawa.power import PowerMonitor
from nyawa.system import SystemManager
from telinga.microphone import MicrophoneListener
from telinga.proximity import ProximitySensor
from telinga.touch import TouchSensor
from wajah import faces
from wajah.animator import Animator
from wajah.display import DisplayDriver

BOOT_ANIMATION_SEC = 1.5
BOOT_ANIMATION_FPS = 15


def _play_boot_animation(display: DisplayDriver, duration: float = BOOT_ANIMATION_SEC) -> None:
    """Tampilkan splash 'LEO ROBOT' berputar — penanda visual autostart berjalan."""
    period = 1.0 / BOOT_ANIMATION_FPS
    deadline = time.time() + duration
    while time.time() < deadline:
        display.show(faces.face_loading())
        time.sleep(period)


def main():
    cfg = Config()
    setup_logger(cfg.LOG_LEVEL, cfg.LOG_FILE)
    bus = EventBus()

    # Init semua modul
    system = SystemManager(bus)
    display = DisplayDriver(cfg.display)
    speaker = Speaker(bus, cfg.audio)
    tts = TextToSpeech(bus, cfg.audio)
    mood = MoodEngine(bus, fps=cfg.display.FPS)
    anim = Animator(display, mood)
    touch = TouchSensor(bus, cfg.mic)
    prox = ProximitySensor(bus, cfg.mic)
    mic = MicrophoneListener(bus, cfg.mic)
    power = PowerMonitor(bus, cfg.power)
    handler = EventHandler(bus, mood, speaker, tts, anim)

    # Urutan shutdown: mulut -> wajah -> telinga -> nyawa
    system.register_modules(speaker, anim, touch, prox, mic, power)

    # Start semua
    system.init_gpio()
    display.init()
    display.show(faces.face_loading())  # feedback instan: layar nyala duluan
    speaker.init()
    touch.start()
    prox.start()
    mic.start()
    power.start()
    _play_boot_animation(display)  # animasikan splash "LEO ROBOT" sebelum mood engine ambil alih
    anim.start()  # 20 FPS animation loop
    handler.start()  # Event processing loop
    speaker.play("startup")
    logging.info("EMO Robot ready!")
    system.register_shutdown()
    handler.join()  # Block sampai shutdown


if __name__ == "__main__":
    main()
