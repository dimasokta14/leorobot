#!/bin/bash
# EMO Robot — Script install otomatis. Aman dijalankan berulang kali (idempotent).
set -e

echo "=== EMO Robot Setup ==="

# System dependencies (apt install sudah idempotent secara default)
sudo apt update
sudo apt install -y python3-pip python3-venv git i2c-tools \
    espeak-ng alsa-utils portaudio19-dev

# Enable SPI (no-op kalau sudah aktif)
sudo raspi-config nonint do_spi 0

# Create venv hanya kalau belum ada
if [ ! -d venv ]; then
    echo "Membuat virtualenv..."
    python3 -m venv venv
else
    echo "Virtualenv sudah ada, lewati."
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Generate placeholder sound effect kalau belum ada
python generate_sounds.py

# Create log dir kalau belum ada
if [ ! -d /var/log/emorobot ]; then
    sudo mkdir -p /var/log/emorobot
    sudo chown "$USER":"$USER" /var/log/emorobot
fi

# Install systemd service — copy ulang aman, service belum tentu enabled/aktif
sudo cp emorobot.service /etc/systemd/system/emorobot.service
sudo systemctl daemon-reload

if ! sudo systemctl is-enabled --quiet emorobot 2>/dev/null; then
    sudo systemctl enable emorobot
else
    echo "Service emorobot sudah enabled, lewati."
fi

echo "=== Setup selesai! Reboot untuk autostart ==="
