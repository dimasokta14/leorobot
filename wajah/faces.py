"""wajah/faces.py — Fungsi render ekspresi wajah robot.

Semua fungsi mengembalikan PIL.Image 240x240 RGB, digambar dengan
primitif PIL.ImageDraw sederhana (mata + mulut) supaya ringan dijalankan
di Raspberry Pi Zero 2W.
"""

import math

from PIL import Image, ImageDraw

WIDTH = 240
HEIGHT = 240
BG_COLOR = (10, 10, 20)
EYE_COLOR = (230, 240, 255)
MOUTH_COLOR = (230, 240, 255)

_EYE_L_CENTER = (80, 100)
_EYE_R_CENTER = (160, 100)
_EYE_RADIUS = 22
_MOUTH_CENTER = (120, 165)


def _canvas() -> Image.Image:
    return Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)


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
    """Boot screen — dipanggil sebelum mood engine aktif."""
    img = _canvas()
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH // 2, HEIGHT // 2
    draw.arc((cx - 30, cy - 30, cx + 30, cy + 30), 0, 270, fill=EYE_COLOR, width=6)
    text = "EMO"
    draw.text((cx - 18, cy + 40), text, fill=EYE_COLOR)
    return img
