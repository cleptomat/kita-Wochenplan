#!/bin/bash
# Sync system clock from DS3231 RTC.
# Run manually or call from cron if needed.
# Usage: sudo bash sync_time.sh

if [ -e /dev/rtc0 ]; then
    hwclock --hctosys --rtc=/dev/rtc0
    echo "System time synced from RTC: $(date)"
else
    echo "ERROR: /dev/rtc0 not found. Run setup_offline_time.sh first."
    exit 1
fi
