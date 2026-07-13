#!/usr/bin/env python3
"""voice_command_test.py — Validasi manual pipeline voice command.

Alur: rekam suara -> transkrip (whisper.cpp, Bahasa Indonesia) -> parse
perintah "putar lagu X" -> cari & putar dari YouTube (yt-dlp + mpv).

INI BUKAN BAGIAN dari main.py. Ini script standalone buat cek dulu apakah
pipeline-nya layak jalan di Raspberry Pi Zero 2W (whisper.cpp tiny model
butuh ~600-700MB RAM, sementara Zero 2W cuma punya 512MB — perlu dibukti
kan jalan standalone dulu sebelum dipikirkan integrasi ke
telinga/voice_trigger.py).

Prasyarat (build manual, lihat README):
  1. git clone https://github.com/ggml-org/whisper.cpp.git ~/whisper.cpp
     cd ~/whisper.cpp && make
     bash ./models/download-ggml-model.sh tiny
  2. pip install yt-dlp        (sudah ada di requirements.txt)
  3. sudo apt install -y mpv

Jalankan:
  python3 voice_command_test.py
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

WHISPER_DIR = Path.home() / "whisper.cpp"
WHISPER_BIN = WHISPER_DIR / "main"
WHISPER_MODEL = WHISPER_DIR / "models" / "ggml-tiny.bin"

RECORD_SECONDS = 5
CAPTURE_DEVICE = "plughw:1,0"  # sesuaikan dengan output `arecord -l` di Pi kamu


def record_audio(raw_path: Path) -> None:
    print(f"Rekam {RECORD_SECONDS} detik, silakan bicara sekarang...")
    subprocess.run(
        [
            "arecord",
            "-D", CAPTURE_DEVICE,
            "-f", "S32_LE",
            "-r", "48000",
            "-c", "2",
            "-d", str(RECORD_SECONDS),
            str(raw_path),
        ],
        check=True,
    )


def convert_for_whisper(raw_path: Path, out_path: Path) -> None:
    """whisper.cpp butuh WAV PCM 16-bit, mono, 16kHz."""
    subprocess.run(
        ["sox", str(raw_path), "-r", "16000", "-c", "1", "-b", "16", str(out_path)],
        check=True,
    )


def transcribe(wav_path: Path) -> str:
    if not WHISPER_BIN.exists():
        sys.exit(f"whisper.cpp binary tidak ditemukan di {WHISPER_BIN} — sudah di-build? (lihat docstring)")
    if not WHISPER_MODEL.exists():
        sys.exit(f"Model tidak ditemukan di {WHISPER_MODEL} — sudah jalankan download-ggml-model.sh tiny?")

    out_prefix = wav_path.with_suffix("")
    subprocess.run(
        [
            str(WHISPER_BIN),
            "-m", str(WHISPER_MODEL),
            "-f", str(wav_path),
            "-l", "id",
            "-otxt",
            "-of", str(out_prefix),
            "-nt",
        ],
        check=True,
        capture_output=True,
    )
    text = out_prefix.with_suffix(".txt").read_text(encoding="utf-8").strip()
    print(f"Transkrip: '{text}'")
    return text


def parse_play_command(text: str) -> Optional[str]:
    match = re.search(r"putar(?:kan)? lagu (.+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def play_from_youtube(query: str) -> None:
    print(f"Mencari & memutar dari YouTube: {query}")
    subprocess.run(["mpv", "--no-video", f"ytsearch1:{query}"])


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        raw_path = Path(tmp) / "raw.wav"
        wav_path = Path(tmp) / "for_whisper.wav"

        record_audio(raw_path)
        convert_for_whisper(raw_path, wav_path)
        text = transcribe(wav_path)

        song = parse_play_command(text)
        if song:
            play_from_youtube(song)
        else:
            print("Tidak terdeteksi perintah 'putar lagu ...' dalam transkrip di atas.")


if __name__ == "__main__":
    main()
