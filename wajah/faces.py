"""wajah/faces.py — Fungsi render ekspresi wajah robot.

Semua fungsi mengembalikan PIL.Image 240x240 RGB. Gaya visual: layar
hitam pekat + "mata digital" bergaya HUD minimalis (garis/ikon tebal
kontras tinggi), terinspirasi robot ekspresif seperti EMO — dipilih
karena jauh lebih terbaca di layar 1.3" 240x240 dibanding wajah kartun
detail. Digambar dengan primitif PIL.ImageDraw supaya ringan dijalankan
di Raspberry Pi Zero 2W.
"""

import math
import time

from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH = 240
HEIGHT = 240
BG_COLOR = (0, 0, 0)
EYE_COLOR = (60, 210, 255)  # cyan elektrik — warna utama "mata"
SPARKLE_COLOR = (255, 205, 60)  # aksen hangat khusus mood excited
BOOT_TEXT = "LEO ROBOT"

_EYE_L_X = 80
_EYE_R_X = 160
_EYE_Y = 100
_EYE_W = 34  # lebar pill mata standar
_EYE_H = 58  # tinggi pill mata standar

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


# --- Primitif bentuk mata ("digital eye") -----------------------------


def _pill_eyes(draw: ImageDraw.ImageDraw, w: int = _EYE_W, h: int = _EYE_H, dy: int = 0, fill=EYE_COLOR) -> None:
    """Mata bar vertikal membulat — ekspresi netral/default."""
    for cx in (_EYE_L_X, _EYE_R_X):
        draw.rounded_rectangle(
            (cx - w // 2, _EYE_Y - h // 2 + dy, cx + w // 2, _EYE_Y + h // 2 + dy),
            radius=w // 2,
            fill=fill,
        )


def _blink_eyes(draw: ImageDraw.ImageDraw) -> None:
    """Mata menutup — garis tipis horizontal."""
    for cx in (_EYE_L_X, _EYE_R_X):
        draw.rounded_rectangle(
            (cx - _EYE_W // 2, _EYE_Y - 4, cx + _EYE_W // 2, _EYE_Y + 4),
            radius=4,
            fill=EYE_COLOR,
        )


def _smile_eyes(draw: ImageDraw.ImageDraw, width: int = 46, height: int = 34) -> None:
    """Mata "⌣ ⌣" — kurva senang, ujung terbuka ke atas."""
    for cx in (_EYE_L_X, _EYE_R_X):
        draw.arc(
            (cx - width // 2, _EYE_Y - height // 2, cx + width // 2, _EYE_Y + height // 2),
            20,
            160,
            fill=EYE_COLOR,
            width=9,
        )


def _frown_eyes(draw: ImageDraw.ImageDraw, width: int = 42, height: int = 30) -> None:
    """Mata "⌢ ⌢" — kurva sedih, ujung terbuka ke bawah."""
    for cx in (_EYE_L_X, _EYE_R_X):
        draw.arc(
            (cx - width // 2, _EYE_Y - height // 2, cx + width // 2, _EYE_Y + height // 2),
            200,
            340,
            fill=EYE_COLOR,
            width=9,
        )


def _sparkle(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int, fill) -> None:
    """Ikon bintang 4 arah (sparkle) — dipakai untuk mood excited."""
    draw.line((cx - size, cy, cx + size, cy), fill=fill, width=4)
    draw.line((cx, cy - size, cx, cy + size), fill=fill, width=4)
    half = int(size * 0.55)
    draw.line((cx - half, cy - half, cx + half, cy + half), fill=fill, width=3)
    draw.line((cx - half, cy + half, cx + half, cy - half), fill=fill, width=3)


def _draw_mouth_bar(draw: ImageDraw.ImageDraw, height: int, width: int = 56) -> None:
    """Bar mulut horizontal membulat — dipakai idle/talking."""
    cx, cy = WIDTH // 2, 168
    height = max(4, height)
    draw.rounded_rectangle(
        (cx - width // 2, cy - height // 2, cx + width // 2, cy + height // 2),
        radius=height // 2,
        fill=EYE_COLOR,
    )


# --- Ekspresi mood ------------------------------------------------------


def face_happy(tick: int, blink: bool) -> Image.Image:
    img = _canvas()
    draw = ImageDraw.Draw(img)
    if blink:
        _blink_eyes(draw)
    else:
        _smile_eyes(draw)
    _draw_mouth_bar(draw, height=6, width=44)
    return img


def face_sad(tick: int) -> Image.Image:
    img = _canvas()
    draw = ImageDraw.Draw(img)
    droop = int(4 * math.sin(tick * 0.05)) + 4
    for cx in (_EYE_L_X, _EYE_R_X):
        draw.arc(
            (cx - 21, _EYE_Y - 15 + droop, cx + 21, _EYE_Y + 15 + droop),
            200,
            340,
            fill=EYE_COLOR,
            width=9,
        )
    # tetesan kecil di sudut mata kanan — detail "sedih"
    dx, dy = _EYE_R_X + 16, _EYE_Y + 10 + droop
    draw.polygon([(dx, dy), (dx - 5, dy + 10), (dx + 5, dy + 10)], fill=EYE_COLOR)
    draw.ellipse((dx - 5, dy + 6, dx + 5, dy + 16), fill=EYE_COLOR)
    return img


def face_curious(tick: int) -> Image.Image:
    """Mata kiri normal, mata kanan diganti tanda tanya (bukan ditumpuk)."""
    img = _canvas()
    draw = ImageDraw.Draw(img)
    bob = int(6 * math.sin(tick * 0.08))
    draw.rounded_rectangle(
        (_EYE_L_X - 13, _EYE_Y - 22, _EYE_L_X + 13, _EYE_Y + 22),
        radius=13,
        fill=EYE_COLOR,
    )
    font = _font(36)
    bbox = draw.textbbox((0, 0), "?", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = _EYE_R_X - tw / 2 - bbox[0]
    ty = _EYE_Y - th / 2 - bbox[1] + bob
    draw.text((tx, ty), "?", fill=EYE_COLOR, font=font)
    _draw_mouth_bar(draw, height=4, width=30)
    return img


def face_sleepy(tick: int) -> Image.Image:
    img = _canvas()
    draw = ImageDraw.Draw(img)
    # kelopak mata tertutup bergaya "sleep mask" melengkung
    draw.arc((50, _EYE_Y - 20, 190, _EYE_Y + 30), 200, 340, fill=EYE_COLOR, width=8)
    # huruf "Z" melayang naik, animasi lewat tick
    font_small = _font(16)
    font_big = _font(24)
    for i, font in enumerate((font_small, font_big)):
        phase = (tick * 0.03 + i * 0.5) % 1.0
        zx = _EYE_R_X + 20 + i * 14
        zy = _EYE_Y - 35 - int(phase * 30) - i * 10
        alpha = 1.0 - phase
        color = tuple(int(c * alpha) for c in EYE_COLOR)
        draw.text((zx, zy), "Z", fill=color, font=font)
    return img


def face_excited(tick: int) -> Image.Image:
    img = _canvas()
    draw = ImageDraw.Draw(img)
    pulse = 15 + int(4 * math.sin(tick * 0.5))
    for cx in (_EYE_L_X, _EYE_R_X):
        _sparkle(draw, cx, _EYE_Y, pulse, SPARKLE_COLOR)
    _draw_mouth_bar(draw, height=10 + int(4 * abs(math.sin(tick * 0.5))), width=50)
    return img


def face_surprised(tick: int) -> Image.Image:
    img = _canvas()
    draw = ImageDraw.Draw(img)
    r = 26
    for cx in (_EYE_L_X, _EYE_R_X):
        draw.ellipse((cx - r, _EYE_Y - r, cx + r, _EYE_Y + r), fill=EYE_COLOR)
        draw.ellipse((cx - r + 8, _EYE_Y - r + 8, cx - r + 18, _EYE_Y - r + 18), fill=BG_COLOR)
    _draw_mouth_bar(draw, height=22, width=26)
    return img


def face_bored(tick: int) -> Image.Image:
    img = _canvas()
    draw = ImageDraw.Draw(img)
    for cx in (_EYE_L_X, _EYE_R_X):
        draw.rounded_rectangle((cx - 18, _EYE_Y - 4, cx + 18, _EYE_Y + 4), radius=4, fill=EYE_COLOR)
    _draw_mouth_bar(draw, height=4, width=30)
    return img


def face_idle(tick: int) -> Image.Image:
    """Ekspresi netral default (state 'idle') — mata pill + napas halus."""
    img = _canvas()
    draw = ImageDraw.Draw(img)
    breathe = int(3 * math.sin(tick * 0.04))
    _pill_eyes(draw, h=_EYE_H + breathe)
    _draw_mouth_bar(draw, height=4, width=36)
    return img


def face_talking(tick: int, intensity: float) -> Image.Image:
    """Mata normal + mulut animasi sesuai intensity suara (0.0 - 1.0)."""
    img = _canvas()
    draw = ImageDraw.Draw(img)
    _pill_eyes(draw)
    intensity = max(0.0, min(1.0, intensity))
    amplitude = 8 + int(28 * intensity)
    open_amount = int(abs(math.sin(tick * 0.6)) * amplitude)
    _draw_mouth_bar(draw, height=open_amount, width=48)
    return img


def _alpha_scaled(layer: Image.Image, factor: float) -> Image.Image:
    """Kembalikan salinan layer RGBA dengan channel alpha dikalikan factor."""
    r, g, b, a = layer.split()
    a = a.point(lambda v: int(v * factor))
    return Image.merge("RGBA", (r, g, b, a))


def face_loading() -> Image.Image:
    """Boot screen — teks "LEO ROBOT" bergaya neon glow, dipanggil
    main.py sebelum mood engine aktif.

    Tiga lapis: halo lebar redup, halo sempit lebih terang, dan inti
    teks tajam solid di atasnya — intensitas berdenyut halus lewat
    time.time() (bukan parameter tick) supaya tetap kompatibel
    dipanggil berkali-kali dalam loop tanpa argumen.
    """
    t = time.time()
    pulse = 0.7 + 0.3 * abs(math.sin(t * 2.2))

    text_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    font = _font(34)
    bbox = text_draw.textbbox((0, 0), BOOT_TEXT, font=font)
    tx = (WIDTH - (bbox[2] - bbox[0])) / 2 - bbox[0]
    ty = (HEIGHT - (bbox[3] - bbox[1])) / 2 - bbox[1]
    text_draw.text((tx, ty), BOOT_TEXT, font=font, fill=(*EYE_COLOR, 255))

    halo_wide = text_layer.filter(ImageFilter.GaussianBlur(14))
    halo_tight = text_layer.filter(ImageFilter.GaussianBlur(5))

    img = _canvas().convert("RGBA")
    img = Image.alpha_composite(img, _alpha_scaled(halo_wide, 0.55 * pulse))
    img = Image.alpha_composite(img, _alpha_scaled(halo_tight, 0.85 * pulse))
    img = Image.alpha_composite(img, text_layer)

    return img.convert("RGB")
