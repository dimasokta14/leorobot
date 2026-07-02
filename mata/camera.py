"""mata/camera.py — Pi Camera init + capture. Status: Phase 2 — stub."""

from typing import Optional

import numpy as np

from config import CameraConfig


class Camera:  # Phase 2
    def __init__(self, config: CameraConfig):
        pass

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def capture(self) -> Optional[np.ndarray]:
        return None
