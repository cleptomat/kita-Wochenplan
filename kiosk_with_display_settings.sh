#!/bin/bash
# Disable screen blanking and power management
xset s off
xset -dpms
xset s noblank

# Run the main kiosk script
/home/admin/Desktop/terminplan/kiosk.sh
