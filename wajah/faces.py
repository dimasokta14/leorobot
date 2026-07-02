"""wajah/faces.py — Fungsi render ekspresi wajah robot.

Semua fungsi mengembalikan PIL.Image 240x240 RGB, digambar dengan
primitif PIL.ImageDraw sederhana (mata + mulut) supaya ringan dijalankan
di Raspberry Pi Zero 2W.
"""

import math
import time

from PIL import Image, ImageDraw, ImageFont

WIDTH = 240
HEIGHT = 240
BG_COLOR = (10, 10, 20)
EYE_COLOR = (230, 240, 255)
MOUTH_COLOR = (230, 240, 255)
BOOT_TEXT = "LEO ROBOT"

_EYE_L_CENTER = (80, 100)
_EYE_R_CENTER = (160, 100)
_EYE_RADIUS = 22
_MOUTH_CENTER = (120, 165)

# Font system umum di Raspberry Pi OS (paket fonts-dejavu-core / fonts-freefont-ttf).
# Kalau tidak ada satupun, fallback ke bitmap font default PIL (tetap jalan, cuma kecil).
_FONT_PATHS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
)
_font_cache = {}


def _font(size: int) -> ImageFont.FreeTypeFont:
    if size in _font_cache:
        return _font_cache[size]
    for path in _FONT_PATHS:
        try:
            font = ImageFont.truetype(path, size)
            break
        except Exception:
            continue
    else:
        font = ImageFont.load_default()
    _font_cache[size] = font
    return font


def _canvas() -> Image.Image:
    return Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)


def _draw_centered_text(draw: ImageDraw.ImageDraw, text: str, y: int, size: int = 22, fill=EYE_COLOR) -> None:
    font = _font(size)
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (WIDTH - (bbox[2] - bbox[0])) // 2
    draw.text((x, y), text, fill=fill, font=font)


def _draw_eyes(draw: ImageDraw.ImageDraw, blink: bool = False, squint: bool = False) -> None:
    for cx, cy in (_EYE_L_CENTER, _EYE_R_CENTER):
        if blink:
            draw.line((cx - _EYE_RADIUS, cy, cx + _EYE_RADIUS, cy), fill=EYE_COLOR, width=6)
        elif squint:
            draw.arc(
                (cx - _EYE_RADIUS, cy - _EYE_RADIUS // 2, cx + _EYE_RADIUS, cy + _EYE_RADIUS),
                200,
                340,
                fill=EYE_COLOR,
                width=6,
            )
        else:
            draw.ellipse(
                (cx - _EYE_RADIUS, cy - _EYE_RADIUS, cx + _EYE_RADIUS, cy + _EYE_RADIUS),
                fill=EYE_COLOR,
            )


def _draw_smile(draw: ImageDraw.ImageDraw, width: int = 70, height: int = 40) -> None:
    cx, cy = _MOUTH_CENTER
    draw.arc((cx - width // 2, cy - height // 2, cx + width // 2, cy + height // 2), 20, 160, fill=MOUTH_COLOR, width=6)


def _draw_frown(draw: ImageDraw.ImageDraw, width: int = 60, height: int = 30) -> None:
    cx, cy = _MOUTH_CENTER
    draw.arc((cx - width // 2, cy, cx + width // 2, cy + height), 200, 340, fill=MOUTH_COLOR, width=6)


def _draw_flat_mouth(draw: ImageDraw.ImageDraw, width: int = 50) -> None:
    cx, cy = _MOUTH_CENTER
    draw.line((cx - width // 2, cy, cx + width // 2, cy), fill=MOUTH_COLOR, width=6)


def _draw_o_mouth(draw: ImageDraw.ImageDraw, radius: int = 18) -> None:
    cx, cy = _MOUTH_CENTER
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=MOUTH_COLOR, width=5)


def face_happy(tick: int, blink: bool) -> Image.Image:
    img = _canvas()
    draw = ImageDraw.Draw(img)
    _draw_eyes(draw, blink=blink)
    _draw_smile(draw)
    return img


def face_sad(tick: int) -> Image.Image:
    img = _canvas()
    draw = ImageDraw.Draw(img)
    droop = int(6 * math.sin(tick * 0.05))
    for cx, cy in (_EYE_L_CENTER, _EYE_R_CENTER):
        draw.ellipse(
            (cx - _EYE_RADIUS, cy - _EYE_RADIUS + droop, cx + _EYE_RADIUS, cy + _EYE_RADIUS + droop),
            fill=EYE_COLOR,
        )
    _draw_frown(draw)
    return img


def face_curious(tick: int) -> Image.Image:
    img = _canvas()
    draw = ImageDraw.Draw(img)
    tilt = int(10 * math.sin(tick * 0.08))
    draw.ellipse(
        (
            _EYE_L_CENTER[0] - _EYE_RADIUS,
            _EYE_L_CENTER[1] - _EYE_RADIUS - tilt,
            _EYE_L_CENTER[0] + _EYE_RADIUS,
            _EYE_L_CENTER[1] + _EYE_RADIUS - tilt,
        ),
        fill=EYE_COLOR,
    )
    draw.ellipse(
        (
            _EYE_R_CENTER[0] - _EYE_RADIUS,
            _EYE_R_CENTER[1] - _EYE_RADIUS + tilt,
            _EYE_R_CENTER[0] + _EYE_RADIUS,
            _EYE_R_CENTER[1] + _EYE_RADIUS + tilt,
        ),
        fill=EYE_COLOR,
    )
    _draw_o_mouth(draw, radius=12)
    return img


def face_sleepy(tick: int) -> Image.Image:
    img = _canvas()
    draw = ImageDraw.Draw(img)
    _draw_eyes(draw, squint=True)
    _draw_flat_mouth(draw, width=30)
    return img


def face_excited(tick: int) -> Image.Image:
    img = _canvas()
    draw = ImageDraw.Draw(img)
    bounce = int(4 * math.sin(tick * 0.4))
    for cx, cy in (_EYE_L_CENTER, _EYE_R_CENTER):
        draw.ellipse(
            (
                cx - _EYE_RADIUS,
                cy - _EYE_RADIUS + bounce,
                cx + _EYE_RADIUS,
                cy + _EYE_RADIUS + bounce,
            ),
            fill=EYE_COLOR,
        )
    _draw_o_mouth(draw, radius=22)
    return img


def face_surprised(tick: int) -> Image.Image:
    img = _canvas()
    draw = ImageDraw.Draw(img)
    for cx, cy in (_EYE_L_CENTER, _EYE_R_CENTER):
        draw.ellipse(
            (cx - _EYE_RADIUS - 4, cy - _EYE_RADIUS - 4, cx + _EYE_RADIUS + 4, cy + _EYE_RADIUS + 4),
            fill=EYE_COLOR,
        )
    _draw_o_mouth(draw, radius=20)
    return img


def face_bored(tick: int) -> Image.Image:
    img = _canvas()
    draw = ImageDraw.Draw(img)
    _draw_eyes(draw, squint=True)
    _draw_flat_mouth(draw)
    return img


def face_idle(tick: int) -> Image.Image:
    """Ekspresi netral default (state 'idle')."""
    img = _canvas()
    draw = ImageDraw.Draw(img)
    _draw_eyes(draw)
    _draw_flat_mouth(draw, width=40)
    return img


def face_talking(tick: int, intensity: float) -> Image.Image:
    """Mata normal + mulut animasi sesuai intensity suara (0.0 - 1.0)."""
    img = _canvas()
    draw = ImageDraw.Draw(img)
    _draw_eyes(draw)
    intensity = max(0.0, min(1.0, intensity))
    amplitude = 6 + int(20 * intensity)
    open_amount = abs(math.sin(tick * 0.6)) * amplitude
    cx, cy = _MOUTH_CENTER
    draw.ellipse(
        (cx - 24, cy - int(open_amount / 2), cx + 24, cy + int(open_amount / 2) + 10),
        fill=MOUTH_COLOR,
    )
    return img


def face_loading() -> Image.Image:
    """Boot screen — dipanggil main.py sebelum mood engine aktif.

    Jadi penanda visual robot sudah menyala & autostart berjalan.
    Spinner dianimasikan lewat time.time() (bukan parameter tick) supaya
    tetap kompatibel dipanggil berkali-kali dalam loop tanpa argumen.
    """
    img = _canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH // 2, HEIGHT // 2 - 20
    angle = (time.time() * 220) % 360
    draw.arc((cx - 30, cy - 30, cx + 30, cy + 30), angle, angle + 270, fill=EYE_COLOR, width=6)
    _draw_centered_text(draw, BOOT_TEXT, cy + 50, size=22)
    return img
