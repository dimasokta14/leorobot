"""nyawa/logger.py — Logging terpusat: file + console.

Semua modul cukup panggil logging.getLogger(__name__) setelah
setup_logger() dipanggil sekali di main.py.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

DEFAULT_LOG_FILE = "/var/log/emorobot/robot.log"
FALLBACK_LOG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "robot.log"
)
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logger(level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Konfigurasi root logger dengan console handler + file handler.

    Kalau log_file tidak bisa ditulis (mis. jalan di dev machine tanpa
    /var/log/emorobot), otomatis fallback ke ./logs/robot.log supaya
    robot tetap bisa start.
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    target_file = log_file or DEFAULT_LOG_FILE
    file_handler = _build_file_handler(target_file, formatter)
    if file_handler is None and target_file != FALLBACK_LOG_FILE:
        file_handler = _build_file_handler(FALLBACK_LOG_FILE, formatter)
    if file_handler is not None:
        root.addHandler(file_handler)

    return root


def _build_file_handler(path: str, formatter: logging.Formatter):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        handler = RotatingFileHandler(path, maxBytes=5_000_000, backupCount=3)
        handler.setFormatter(formatter)
        return handler
    except OSError:
        return None
