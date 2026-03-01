"""
DS3231 RTC reader via I2C (smbus2).

The DS3231 sits at I2C address 0x68 on bus 1 (SDA=GPIO2/pin3, SCL=GPIO3/pin5).
Registers 0x00–0x06 hold: seconds, minutes, hours, weekday, day, month, year
All values are BCD-encoded.

If the RTC cannot be reached (I2C not yet enabled, module missing, wiring issue),
every function transparently falls back to the system clock so the app keeps running.
"""

import os
import signal
from datetime import datetime

DS3231_ADDR  = 0x68
I2C_BUS      = 1        # /dev/i2c-1 after dtparam=i2c_arm=on + reboot
I2C_DEV      = f'/dev/i2c-{I2C_BUS}'
I2C_TIMEOUT  = 2        # hard timeout in seconds

def _bcd_to_int(bcd: int) -> int:
    return (bcd >> 4) * 10 + (bcd & 0x0F)

def _timeout_handler(signum, frame):
    raise TimeoutError('I2C read timed out')

def _read_ds3231() -> datetime:
    """Read current datetime directly from DS3231 registers.
    Raises OSError/TimeoutError if the bus or device is unavailable.
    """
    if not os.path.exists(I2C_DEV):
        raise OSError(f'{I2C_DEV} not found – I2C not enabled yet')

    from smbus2 import SMBus

    # Use SIGALRM to enforce a hard timeout so a stuck bus never blocks the app
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(I2C_TIMEOUT)
    try:
        with SMBus(I2C_BUS) as bus:
            data = bus.read_i2c_block_data(DS3231_ADDR, 0x00, 7)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

    second   = _bcd_to_int(data[0] & 0x7F)
    minute   = _bcd_to_int(data[1] & 0x7F)
    hour_reg = data[2]
    if hour_reg & 0x40:                        # 12-hour mode
        hour = _bcd_to_int(hour_reg & 0x1F)
        hour = (hour % 12) + (12 if (hour_reg & 0x20) else 0)
    else:
        hour = _bcd_to_int(hour_reg & 0x3F)   # 24-hour mode

    day   = _bcd_to_int(data[4] & 0x3F)
    month = _bcd_to_int(data[5] & 0x1F)
    year  = _bcd_to_int(data[6]) + 2000

    return datetime(year, month, day, hour, minute, second)


def now() -> datetime:
    """Return current datetime from DS3231, falling back to system clock."""
    try:
        return _read_ds3231()
    except Exception:
        return datetime.now()


def today() -> datetime:
    """Return current date (midnight) from DS3231, falling back to system clock."""
    try:
        dt = _read_ds3231()
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    except Exception:
        return datetime.today()
