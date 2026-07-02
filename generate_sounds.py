#!/usr/bin/env python3
"""generate_sounds.py — Generate placeholder .wav untuk semua sound effect ID.

Dipakai saat setup pertama kali (dipanggil dari setup.sh) supaya
mulut/assets/sounds/ terisi sebelum ada file rekaman/asset asli.
Menggunakan espeak-ng offline TTS untuk sintesis suara pendek per mood.
Idempotent — file yang sudah ada tidak ditimpa ulang kecuali --force.
"""

import argparse
import os
import subprocess
import sys

from config import AudioConfig
from mulut.sounds import SoundManager

PHRASES = {
    "startup": "Halo, aku Emo!",
    "happy": "Yeay!",
    "sad": "Yah...",
    "curious": "Hmm?",
    "excited": "Woohoo!",
    "sleepy": "Ngantuk...",
    "touched": "Hihi!",
    "surprised": "Wah!",
    "shutdown": "Sampai jumpa!",
    "greeting": "Hai, senang bertemu!",
}


def generate(force: bool = False) -> int:
    config = AudioConfig()
    manager = SoundManager(config)
    os.makedirs(config.SOUNDS_DIR, exist_ok=True)

    generated, skipped, failed = 0, 0, 0
    for sound_id in manager.all_ids():
        path = manager.path_for(sound_id)
        if os.path.exists(path) and not force:
            print(f"[skip]  {sound_id} -> sudah ada ({path})")
            skipped += 1
            continue

        text = PHRASES.get(sound_id, sound_id)
        cmd = [
            "espeak-ng",
            "-v",
            config.TTS_VOICE,
            "-s",
            str(config.TTS_SPEED),
            "-p",
            str(config.TTS_PITCH),
            "-w",
            path,
            text,
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[ok]    {sound_id} -> {path}")
            generated += 1
        except FileNotFoundError:
            print("espeak-ng tidak ditemukan. Install dulu: sudo apt install espeak-ng", file=sys.stderr)
            return 1
        except subprocess.CalledProcessError:
            print(f"[fail]  {sound_id} -> gagal generate", file=sys.stderr)
            failed += 1

    print(f"\nSelesai: {generated} dibuat, {skipped} dilewati, {failed} gagal.")
    return 1 if failed else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force", action="store_true", help="Timpa ulang file .wav yang sudah ada"
    )
    args = parser.parse_args()
    sys.exit(generate(force=args.force))
