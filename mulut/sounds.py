"""mulut/sounds.py — Sound effect manager.

Memetakan sound ID logis (dipakai modul lain) ke file .wav fisik di
mulut/assets/sounds/. Daftar ID wajib sesuai tabel PRD.
"""

import os
from typing import List

from config import AudioConfig

# Sound ID -> nama file .wav
SOUND_FILES = {
    "startup": "startup.wav",
    "happy": "happy.wav",
    "sad": "sad.wav",
    "curious": "curious.wav",
    "excited": "excited.wav",
    "sleepy": "sleepy.wav",
    "touched": "touched.wav",
    "surprised": "surprised.wav",
    "shutdown": "shutdown.wav",
    "greeting": "greeting.wav",
}


class SoundManager:
    def __init__(self, config: AudioConfig):
        self._config = config

    def path_for(self, sound_id: str) -> str:
        filename = SOUND_FILES.get(sound_id)
        if filename is None:
            raise KeyError(f"Sound ID tidak dikenal: {sound_id}")
        return os.path.join(self._config.SOUNDS_DIR, filename)

    def exists(self, sound_id: str) -> bool:
        try:
            return os.path.isfile(self.path_for(sound_id))
        except KeyError:
            return False

    def all_ids(self) -> List[str]:
        return list(SOUND_FILES.keys())

    def missing_ids(self) -> List[str]:
        return [sid for sid in self.all_ids() if not self.exists(sid)]
