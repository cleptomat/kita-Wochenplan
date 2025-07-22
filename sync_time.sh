#!/bin/bash

# Time sync script for Raspberry Pi before going offline
# This should be run while internet is still available

echo "Syncing time from internet..."

# Force immediate time sync
sudo ntpdate -s time.nist.gov

# Alternative backup servers
if [ $? -ne 0 ]; then
    sudo ntpdate -s pool.ntp.org
fi

if [ $? -ne 0 ]; then
    sudo ntpdate -s 0.europe.pool.ntp.org
fi

# Sync system time to hardware clock
sudo hwclock --systohc

# Check current time
echo "Current system time: $(date)"
echo "Hardware clock time: $(sudo hwclock -r)"

echo "Time sync complete. Hardware clock updated."
