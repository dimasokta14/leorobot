"""mata/recognizer.py — Face recognition (dlib). Status: Phase 2 — stub."""

from typing import List, Optional


class FaceRecognizer:  # Phase 2
    def train(self, name: str, images: List) -> None:
        pass

    def identify(self, face_img) -> Optional[str]:
        return None
