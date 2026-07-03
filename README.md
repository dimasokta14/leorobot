# Leo Robot

Mini robot ekspresif, berjalan di Raspberry Pi Zero 2W. Wajah ditampilkan
di layar ST7789 1.3", punya mood engine, merespons sentuhan/jarak/suara, dan
bicara lewat text-to-speech offline.

Dibangun sesuai `PRD_ClaudeCode_EMORobot.pdf` — Phase 1 (wajah, jiwa, telinga
touch+proximity, mulut, nyawa) diimplementasikan penuh. Modul `mata/` (kamera
& face recognition) dan `otak/` (AI chat) masih stub untuk Phase 2 & 3.

## Arsitektur

```
~/leorobot/
├── main.py              # Entry point utama
├── config.py             # Semua konfigurasi terpusat (dataclass per modul)
├── requirements.txt
├── setup.sh              # Install otomatis, idempotent
├── leorobot.service      # Systemd autostart
├── generate_sounds.py    # Generate placeholder .wav via espeak-ng
├── wajah/                # Display ST7789 + render ekspresi + animator
├── jiwa/                 # Mood engine (state machine) + personality + events
├── telinga/              # Input: touch, ultrasonik, mikrofon, wake word
├── mulut/                # Output: speaker, sound effect, TTS
├── mata/                 # Kamera + face detection/recognition (Phase 2, stub)
├── otak/                 # AI chat + memory + edukasi (Phase 3, stub)
├── nyawa/                # Event bus, logger, power, system lifecycle
└── tests/                # Unit test per modul
```

Prinsip: setiap modul independen, komunikasi lewat `EventBus`
(`threading.Queue`) di `nyawa/event_bus.py` — tidak ada import silang antar
modul fungsional.

## Instalasi (di Raspberry Pi)

```bash
git clone -b develop https://github.com/dimasokta14/leorobot.git ~/leorobot
cd ~/leorobot
./setup.sh
```

`setup.sh` idempotent — aman dijalankan berulang kali. Yang dilakukan:

1. Install dependency sistem (`espeak-ng`, `portaudio19-dev`, dll)
2. Aktifkan SPI (`raspi-config nonint do_spi 0`)
3. Buat virtualenv `venv/` (kalau belum ada) & install `requirements.txt`
4. Generate placeholder sound effect (`generate_sounds.py`)
5. Buat `/var/log/leorobot/` dan pasang `leorobot.service` sebagai systemd
   service (autostart saat boot)

## Menjalankan

Manual (tanpa systemd, untuk development):

```bash
source venv/bin/activate
python main.py
```

Via systemd (setelah `setup.sh` + reboot, robot langsung jalan):

```bash
sudo systemctl start leorobot     # start manual
sudo systemctl status leorobot    # cek status
journalctl -u leorobot -f         # lihat log realtime
```

## Testing

Semua modul bisa ditest tanpa hardware fisik (GPIO/SPI/mic di-mock atau
otomatis fallback ke mode simulasi):

```bash
source venv/bin/activate
python -m unittest discover -s tests -v
```

## Shutdown

- **Software**: `sudo systemctl stop leorobot`, atau kirim `SIGTERM`/`SIGINT`
  ke proses `main.py` — robot akan `graceful_shutdown()`: putar sound
  `shutdown`, matikan speaker → animator → sensor telinga, baru GPIO cleanup.
- **Tombol fisik**: soft power button di GPIO3 (BCM) memicu shutdown yang sama.
- **Reboot**: `sudo systemctl restart leorobot` atau `sudo reboot`.

## Wiring Layar ST7789

Modul ST7789 1.3" 240x240 7-pin (tanpa CS pin), driver
[pkkirilov/ST7789](https://github.com/pkkirilov/ST7789):

| TFT Pin | Raspberry Pi (BCM) | Raspberry Pi (Physical Pin) |
|---|---|---|
| VCC | 3.3V | Pin 17 |
| GND | GND | Pin 6 |
| SCL / SCK | GPIO11 (SPI0 SCLK) | Pin 23 |
| SDA / MOSI | GPIO10 (SPI0 MOSI) | Pin 19 |
| RES / RST | GPIO22 | Pin 15 |
| DC | GPIO17 | Pin 11 |
| BLK | GPIO27 | Pin 13 |

## Wiring Sensor Lain

| Komponen | Pin | BCM | Physical Pin |
|---|---|---|---|
| Touch sensor TTP223 — head | I/O | GPIO5 | Pin 29 |
| Touch sensor TTP223 — body | I/O | GPIO6 | Pin 31 |
| HC-SR04 — TRIG | TRIG | GPIO23 | Pin 16 |
| HC-SR04 — ECHO | ECHO | GPIO24 | Pin 18 (**wajib voltage divider 5V→3.3V**) |

Semua pin di atas sudah dicek tidak bentrok satu sama lain maupun dengan
pin layar ST7789 di atas — kalau mengubah salah satu di `config.py`,
cek ulang tidak ada GPIO yang dipakai dobel.

## Konfigurasi

Semua parameter (pin GPIO, threshold, FPS, volume, dsb) ada di `config.py`
sebagai dataclass per modul (`DisplayConfig`, `MicConfig`, `AudioConfig`,
`PowerConfig`, dst). Tidak ada nilai hardcode di file modul — ubah perilaku
robot cukup lewat `config.py`.

## Troubleshooting

| Gejala | Kemungkinan penyebab | Solusi |
|---|---|---|
| Layar tetap hitam | SPI belum aktif, atau wiring DC/RST/BL salah | Cek `raspi-config` → Interface Options → SPI aktif; cocokkan wiring dengan tabel pin di bawah |
| Log muncul "mode simulasi" untuk display, tapi tidak ada traceback jelas | Kemungkinan `try/except` di `wajah/display.py` menelan error asli (mis. konflik modul, lihat baris di bawah) | Test manual bypass try/except: lihat skrip diagnostic di bagian Troubleshooting Display di bawah |
| `TypeError: ST7789.__init__() got an unexpected keyword argument 'spi'` atau muncul `DeprecationWarning: Using "import ST7789" is deprecated. Please "import st7789"` | Ada package **pimoroni `st7789`** (pip) yang bentrok nama modul dengan driver vendor **pkkirilov/ST7789** kita — biasa kejadian kalau venv lama (dari testing manual sebelum repo ini) dipakai ulang | `pip uninstall st7789 -y`, lalu pastikan `python3 -c "import ST7789; print(ST7789.__file__)"` menunjuk ke `vendor/ST7789_repo/ST7789/__init__.py`, bukan ke `site-packages` |
| Tidak ada suara sama sekali | PAM8406 belum terhubung, atau `pygame.mixer` gagal init | Cek `aplay -l`, cek volume ALSA (`alsamixer`), pastikan speaker tersambung sebelum boot |
| TTS tidak bersuara | `espeak-ng` belum terpasang | `sudo apt install espeak-ng` |
| Touch sensor tidak merespons | `RPi.GPIO` tidak terpasang, pull-down salah, atau `add_event_detect` gagal (lihat baris kernel GPIO di bawah) | Jalankan di Pi asli (bukan dev machine); cek wiring TTP223 ke pin GPIO5 (head) / GPIO6 (body) sesuai `config.py` |
| `RuntimeError: Failed to add edge detection` di log (soft power button / touch sensor) | `RPi.GPIO` (library lama) tidak kompatibel dengan interface GPIO kernel baru di Raspberry Pi OS versi terkini — fitur terkait otomatis dilewati (lihat log warning), robot tetap jalan | Kalau touch sensor harus benar-benar berfungsi: `pip uninstall RPi.GPIO && pip install rpi-lgpio` (drop-in replacement, nama modul tetap `RPi.GPIO`, tidak perlu ubah kode) |
| Sensor ultrasonik ngaco / GPIO rusak | Lupa pasang voltage divider di pin ECHO | **Wajib** voltage divider 5V→3.3V di ECHO sebelum masuk GPIO |
| `ModuleNotFoundError` saat `python main.py` | Virtualenv belum diaktifkan / dependency belum lengkap | `source venv/bin/activate && pip install -r requirements.txt` |
| Log aplikasi tidak ada di `/var/log/leorobot/robot.log` | Proses tidak punya permission tulis ke `/var/log/leorobot/`, logger otomatis fallback | Cek isi `~/leorobot/logs/robot.log` sebagai gantinya, atau perbaiki permission: `sudo chown $USER:$USER /var/log/leorobot` |
| Service tidak autostart setelah reboot | Service belum di-enable | `sudo systemctl enable leorobot && sudo systemctl daemon-reload` |

### Diagnostic Display (bypass try/except)

`wajah/display.py` sengaja membungkus semua init SPI/ST7789 dengan
`try/except` supaya robot tetap jalan (headless) kalau layar belum
terpasang — konsekuensinya, error asli jadi tidak kelihatan, cuma log
"mode simulasi". Kalau curiga ada masalah display tapi tidak yakin
penyebabnya, jalankan langsung tanpa lapisan try/except itu:

```bash
sudo systemctl stop leorobot   # supaya tidak rebutan akses SPI
cd ~/leorobot
source venv/bin/activate
python3 -c "
import Adafruit_GPIO.SPI as SPI
import ST7789
from config import DisplayConfig
from PIL import Image

cfg = DisplayConfig()
spi = SPI.SpiDev(cfg.SPI_PORT, cfg.SPI_CS, max_speed_hz=cfg.SPI_SPEED_HZ)
disp = ST7789.ST7789(spi=spi, rst=cfg.RST_PIN, dc=cfg.DC_PIN, led=cfg.BL_PIN, width=cfg.WIDTH, height=cfg.HEIGHT)
disp.begin()
disp.clear()
print('ST7789 init OK')

img = Image.new('RGB', (240, 240), (255, 0, 0))
disp.display(img)
print('Frame merah dikirim ke layar — cek fisiknya sekarang!')
"
```

Kalau layar berubah merah solid tanpa traceback, driver + wiring sudah
benar — masalahnya ada di lapisan lain (main.py, service, dst). Kalau
muncul traceback, itu error aslinya, jauh lebih mudah didiagnosa
daripada cuma lihat "mode simulasi" di log.

## Menambah Dependency

Jangan install package di luar `requirements.txt` secara manual di
Raspberry Pi. Kalau butuh package baru: tambahkan ke `requirements.txt`
dengan komentar alasannya, lalu jalankan ulang `pip install -r requirements.txt`.

## Roadmap

- **Phase 1 (aktif)** — wajah, jiwa, telinga (touch + proximity), mulut, nyawa
- **Phase 2** — `mata/`: face detection & recognition (OpenCV + dlib)
- **Phase 3** — `otak/`: integrasi ChatGPT, memory percakapan, mode edukasi anak
