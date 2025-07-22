# Kita-Wochenplan (Weekly Schedule for Kindergarten)

A Flask web application designed to run on a Raspberry Pi in kiosk mode, displaying a weekly schedule interface for kindergarten/daycare use.

## Features

- **Weekly Schedule View**: Display events across Monday-Sunday in a time-grid format with dates
- **Event Management**: Add, edit, and delete events with color coding
- **Consistent Layout**: Events maintain visual consistency across overlapping time slots
- **Touch-Friendly**: Optimized for touchscreen interaction in kiosk mode
- **Auto-Start**: Automatically launches in fullscreen kiosk mode on boot
- **Standard Events**: Pre-configured daily events (Frühstück, Morgentreff, Mittagessen)
- **Offline Time Keeping**: Maintains accurate time even without internet connection

## Hardware Requirements

- Raspberry Pi 2B or newer
- MicroSD card (16GB+ recommended)
- Display (HDMI monitor or touchscreen)
- Optional: Keyboard for maintenance access

## Software Requirements

- Raspberry Pi OS (Bookworm or newer)
- Python 3.x with Flask
- Chromium browser
- SQLite3

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/kita-Wochenplan.git
cd kita-Wochenplan
```

### 2. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-flask chromium-browser unclutter xdotool sqlite3

# Make scripts executable
chmod +x *.sh
```

### 3. Database Setup

The application will automatically create the SQLite database on first run. The database schema is:

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    date TEXT NOT NULL,
    start_time INTEGER NOT NULL,
    end_time INTEGER NOT NULL,
    image TEXT,
    color TEXT
);
```

### 4. Kiosk Mode Setup

The application includes automated kiosk mode setup:

- **`kiosk.sh`**: Main kiosk script that starts the Flask app and Chromium
- **`kiosk_with_display_settings.sh`**: Enhanced script with display power management
- **`start_app.sh`**: Flask application startup script

The kiosk mode will automatically start on boot via the desktop autostart entry.

### 4. Time Synchronization Setup (Important for Offline Use)

Before disconnecting from the internet, run the time sync script:

```bash
# Sync time and set up offline time keeping
./sync_time.sh

# Optional: Set up additional offline time persistence
./setup_offline_time.sh
```

This ensures the Pi maintains accurate time even without internet connection.

## Usage

### Normal Operation (Kiosk Mode)

1. Boot the Raspberry Pi
2. The system automatically starts in kiosk mode showing the weekly schedule
3. Use the touch interface to interact with events
4. Click "Optionen" to show edit/delete buttons for events
5. Click "+ Event" to add new events

### Breaking Out of Kiosk Mode

**Keyboard Shortcuts:**
- `Alt + F4` - Close browser
- `Ctrl + Alt + T` - Open terminal
- `Ctrl + Alt + F1-F6` - Switch to text console
- `Ctrl + Alt + F7` - Return to desktop

**SSH Access:**
```bash
ssh admin@[PI_IP_ADDRESS]
```

**Kill Kiosk Processes:**
```bash
pkill chromium
pkill -f "python3 app.py"
```

### Development Mode

To run in development mode (not kiosk):

```bash
cd /path/to/kita-Wochenplan
python3 app.py
```

Then open `http://localhost:5000` in a regular browser.

## File Structure

```
kita-Wochenplan/
├── app.py                              # Main Flask application
├── database.db                         # SQLite database (auto-created)
├── requirements.txt                     # Python dependencies
├── start_app.sh                        # Flask startup script
├── kiosk.sh                            # Basic kiosk mode script
├── kiosk_with_display_settings.sh      # Enhanced kiosk script
├── sync_time.sh                        # Time synchronization script
├── setup_offline_time.sh               # Offline time setup script
├── templates/
│   └── index.html                      # Main HTML template
├── static/
│   ├── jquery-3.7.1.min.js            # jQuery library
│   ├── bootstrap-5.3.7-dist/          # Bootstrap CSS/JS
│   └── uploads/                        # File upload directory
└── README.md                           # This file
```

## Configuration

### Standard Events

Default daily events are configured in `app.py`:

```python
STANDARD_EVENTS = [
    ("Frühstück", "08:00", "09:30", "#f8d7da"),
    ("Morgentreff", "09:30", "10:00", "#d1ecf1"),
    ("Mittagessen", "12:00", "13:30", "#d4edda"),
]
```

### Time Range

The schedule displays from 08:00 to 18:00 in 15-minute intervals. This can be modified in the template and Flask routes.

### Display Days

By default shows Monday-Friday. Weekend days are shown if there are events on Sunday.

## Troubleshooting

### Kiosk Mode Issues

1. **Browser doesn't start**: Check if Chromium is installed
2. **Flask app not accessible**: Ensure Flask is running on port 5000
3. **Screen goes blank**: Display power management might be active

### Database Issues

1. **Events not saving**: Check database permissions
2. **Database corruption**: Delete `database.db` and restart (will lose data)

### Performance on Raspberry Pi 2B

- The Pi 2B has limited resources. Consider:
  - Reducing browser cache size
  - Limiting concurrent events
  - Using lighter weight alternatives if performance is poor

### Common Commands

```bash
# Check if Flask is running
ps aux | grep python3

# Check browser processes
ps aux | grep chromium

# View application logs
python3 app.py  # Run in foreground to see logs

# Restart kiosk mode
/home/admin/Desktop/terminplan/kiosk_with_display_settings.sh

# Enable SSH (if needed)
sudo systemctl enable ssh
sudo systemctl start ssh
```

## Development

### Adding New Features

1. Break out of kiosk mode
2. Edit the code
3. Test in development mode
4. Restart kiosk mode

### Database Schema Changes

If you modify the database schema, you may need to:

1. Backup existing data
2. Delete the database file
3. Restart the application
4. Re-import data

## Security Notes

- The application runs on all interfaces (`0.0.0.0`) for network access
- No authentication is implemented - suitable for internal/kiosk use only
- Consider adding authentication if exposing to broader networks

## License

This project is open source and available under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on actual Raspberry Pi hardware if possible
5. Submit a pull request

## Support

For issues and questions, please use the GitHub Issues page.
