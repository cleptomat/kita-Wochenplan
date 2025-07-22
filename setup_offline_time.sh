#!/bin/bash

# Setup hardware clock for offline operation
# Run this once while internet is available

# Install fake-hwclock for better offline time keeping
sudo apt update
sudo apt install -y fake-hwclock

# Sync time now
sudo ntpdate -s time.nist.gov
sudo hwclock --systohc

# Enable hardware clock sync on boot
echo "# Sync hardware clock on boot" | sudo tee -a /etc/rc.local > /dev/null
echo "hwclock --hctosys" | sudo tee -a /etc/rc.local > /dev/null

# Configure fake-hwclock to save time every hour
echo "*/60 * * * * root fake-hwclock save" | sudo tee -a /etc/crontab > /dev/null

echo "Hardware clock setup complete!"
echo "Current time: $(date)"
echo "Hardware clock: $(sudo hwclock -r)"
