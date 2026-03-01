#!/bin/bash
# =============================================================================
# setup_offline_time.sh
# One-time setup script to configure the DS3231 RTC for offline operation.
#
# Hardware wiring:
#   DS3231 VCC  → Pin 1  (3.3 V)
#   DS3231 SDA  → Pin 3  (GPIO 2)
#   DS3231 SCL  → Pin 5  (GPIO 3)
#   DS3231 GND  → Pin 9  (GND)
#
# Run once as root after first boot:
#   sudo bash setup_offline_time.sh
# =============================================================================

set -e

echo "=== DS3231 RTC Setup ==="

# 1. Enable I2C kernel module at boot
echo "--- Enabling I2C kernel module ---"
if ! grep -q "^i2c-dev" /etc/modules; then
    echo "i2c-dev" >> /etc/modules
fi
modprobe i2c-dev 2>/dev/null || true

# 2. Install i2c-tools if missing (useful for diagnosis)
if ! command -v i2cdetect &>/dev/null; then
    echo "--- Installing i2c-tools ---"
    apt-get install -y i2c-tools
fi

# 3. Detect DS3231 on bus 1
echo "--- Scanning I2C bus 1 for DS3231 (expect 0x68) ---"
i2cdetect -y 1

# 4. Register the DS3231 as the kernel RTC device
echo "--- Registering DS3231 as kernel RTC ---"
echo ds3231 0x68 > /sys/bus/i2c/devices/i2c-1/new_device 2>/dev/null || \
    echo "(Device may already be registered via device tree overlay — that's fine)"

# Give the kernel a moment to create /dev/rtc0
sleep 1

# 5. Read RTC hardware time and sync to system clock
if [ -e /dev/rtc0 ]; then
    echo "--- Syncing system clock from DS3231 (/dev/rtc0) ---"
    hwclock --hctosys --rtc=/dev/rtc0
    echo "System time is now: $(date)"
else
    echo "WARNING: /dev/rtc0 not found. Check wiring and that dtoverlay=i2c-rtc,ds3231 is in /boot/firmware/config.txt."
fi

# 6. Disable NTP (not available offline) so the system uses the RTC exclusively
echo "--- Disabling NTP service ---"
timedatectl set-ntp false 2>/dev/null || true
systemctl disable systemd-timesyncd 2>/dev/null || true
systemctl stop    systemd-timesyncd 2>/dev/null || true

# 7. Create a systemd service that syncs RTC → system on every boot
echo "--- Installing rtc-sync boot service ---"
cat > /etc/systemd/system/rtc-sync.service <<'EOF'
[Unit]
Description=Sync system clock from DS3231 RTC on boot
After=local-fs.target

[Service]
Type=oneshot
ExecStart=/sbin/hwclock --hctosys --rtc=/dev/rtc0
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable rtc-sync.service
systemctl start  rtc-sync.service

echo ""
echo "=== Setup complete ==="
echo "Current system time : $(date)"
echo "RTC hardware time   : $(hwclock --rtc=/dev/rtc0 2>/dev/null || echo 'unavailable')"
echo ""
echo "To set the RTC to the current system time, run:"
echo "  sudo hwclock --systohc --rtc=/dev/rtc0"
echo ""
echo "A reboot is required to activate the I2C device-tree overlay."
echo "After reboot, run:  sudo hwclock --hctosys --rtc=/dev/rtc0"
