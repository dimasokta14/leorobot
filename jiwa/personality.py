"""jiwa/personality.py — Karakter dan nama robot."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Personality:
    name: str = "Leo"
    character: str = "ceria, penasaran, dan hangat"
    preferred_responses: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "greeting": ["Halo! Aku {name}!", "Hai, senang bertemu denganmu!"],
            "happy": ["Yeay!", "Aku senang!"],
            "sad": ["Yah...", "Sedih rasanya."],
            "curious": ["Hmm, apa itu?", "Menarik!"],
            "sleepy": ["Ngantuk...", "Zzz..."],
            "bye": ["Sampai jumpa!", "Dadah!"],
        }
    )

    def say(self, mood: str) -> str:
        """Ambil salah satu preferred response acak sesuai mood."""
        import random

        options = self.preferred_responses.get(mood, [])
        if not options:
            return ""
        return random.choice(options).format(name=self.name)
