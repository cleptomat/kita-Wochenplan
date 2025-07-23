from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
import os

app = Flask(__name__)
DB_PATH = 'database.db'

def init_db():
    """Initialize database with events table if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            start_time INTEGER NOT NULL,
            end_time INTEGER NOT NULL,
            image TEXT,
            color TEXT
        )
    """)
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
DISPLAY_DAYS = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
STANDARD_EVENTS = [
    ("Frühstück", "08:00", "09:30", "#f8d7da"),
    ("Morgentreff", "09:30", "10:00", "#d1ecf1"),
    ("Mittagessen", "12:00", "13:30", "#d4edda"),
]

def hhmm_to_minutes(hhmm):
    h, m = map(int, hhmm.split(':'))
    return h * 60 + m

def minutes_to_hhmm(minutes):
    minutes = int(minutes)
    return f"{minutes // 60:02}:{minutes % 60:02}"

def get_current_week_dates():
    today = datetime.today()
    monday = today - timedelta(days=today.weekday())
    return [monday + timedelta(days=i) for i in range(7)]  # Mon to Sun

def get_events_by_day():
    week_dates = get_current_week_dates()
    date_strings = [d.strftime('%Y%m%d') for d in week_dates]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    placeholders = ','.join('?' for _ in date_strings)
    cursor.execute(f"""
        SELECT id, title, date, start_time, end_time, image, color
        FROM events
        WHERE date IN ({placeholders})
    """, date_strings)
    rows = cursor.fetchall()
    conn.close()

    events_by_day = {day: [] for day in DAYS}

    # Map date string -> day name
    date_to_day = {d.strftime('%Y%m%d'): d.strftime('%A') for d in week_dates}

    for row in rows:
        date_key = row[2]
        if date_key not in date_to_day:
            continue
        weekday = date_to_day[date_key]

        event = {
            'id': row[0],
            'title': row[1],
            'date': datetime.strptime(row[2], '%Y%m%d').strftime('%Y-%m-%d'),
            'start_time': minutes_to_hhmm(row[3]),
            'end_time': minutes_to_hhmm(row[4]),
            'image': row[5],
            'color': row[6]
        }
        events_by_day[weekday].append(event)

    # Add standard events to each day
    for i, weekday in enumerate(DAYS[:5]):
        date_obj = week_dates[i]
        for title, start, end, color in STANDARD_EVENTS:
            events_by_day[weekday].append({
                'id': None,
                'title': title,
                'date': date_obj.strftime('%Y-%m-%d'),
                'start_time': start,
                'end_time': end,
                'image': None,
                'color': color
            })

    # Sort each day's events by start time
    for day in events_by_day:
        events_by_day[day].sort(key=lambda e: hhmm_to_minutes(e['start_time']))
    

    return events_by_day

def assign_event_layout(events):
    """
    Given a list of events for one day, assign each event:
    - col_index: its horizontal position in overlapping group
    - total_cols: total number of overlapping columns (group width)
    """
    # Convert times to numeric minutes
    for e in events:
        e['_start'] = hhmm_to_minutes(e['start_time'])
        e['_end'] = hhmm_to_minutes(e['end_time'])

    events.sort(key=lambda e: e['_start'])

    active = []
    for e in events:
        # Remove ended events from active
        active = [a for a in active if a['_end'] > e['_start']]

        # Find available column index
        used_cols = [a['col_index'] for a in active if 'col_index' in a]
        col = 0
        while col in used_cols:
            col += 1

        # Assign column index and update
        e['col_index'] = col
        active.append(e)

        # Store how many overlaps exist at this point
        max_col = max(a['col_index'] for a in active)
        for a in active:
            a['total_cols'] = max(a.get('total_cols', 1), max_col + 1)

    return events

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        event_id = request.form.get('id')  # may be empty for new events
        title = request.form['title']
        date_str = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        image = request.form.get('image') or None
        color = request.form.get('color') or None

        date_db = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y%m%d')
        start_minutes = hhmm_to_minutes(start_time)
        end_minutes = hhmm_to_minutes(end_time)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if event_id:
            # Update existing event
            cursor.execute("""
                UPDATE events
                SET title=?, date=?, start_time=?, end_time=?, image=?, color=?
                WHERE id=?
            """, (title, date_db, start_minutes, end_minutes, image, color, event_id))
        else:
            # Insert new event
            cursor.execute("""
                INSERT INTO events (title, date, start_time, end_time, image, color)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, date_db, start_minutes, end_minutes, image, color))

        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    events_by_day = get_events_by_day()
    week_dates = get_current_week_dates()
    EN_TO_DE = {
    'Monday': 'Montag',
    'Tuesday': 'Dienstag',
    'Wednesday': 'Mittwoch',
    'Thursday': 'Donnerstag',
    'Friday': 'Freitag',
    'Saturday': 'Samstag',
    'Sunday': 'Sonntag'
    }

    # Create display information
    display_days = []
    display_dates = []
    day_keys = []
    
    # Create display days with dates for weekdays
    for i, day in enumerate(DAYS[:5]):
        display_days.append(f"{EN_TO_DE[day]}\n{week_dates[i].strftime('%d.%m.%Y')}")
        display_dates.append(week_dates[i].strftime('%d.%m.%Y'))
        day_keys.append(day)  # Keep original English day name for lookup

    # Add weekend if there are Sunday events
    if events_by_day['Sunday']:
        display_days.append(f"{EN_TO_DE['Saturday']}\n{week_dates[5].strftime('%d.%m.%Y')}")
        display_days.append(f"{EN_TO_DE['Sunday']}\n{week_dates[6].strftime('%d.%m.%Y')}")
        display_dates.extend([week_dates[5].strftime('%d.%m.%Y'), week_dates[6].strftime('%d.%m.%Y')])
        day_keys.extend(['Saturday', 'Sunday'])

    # Create mapping from display labels back to English day names
    day_key_map = {}
    for i, display_day in enumerate(display_days):
        day_key_map[display_day] = day_keys[i]
    # Get current time for display
    current_time = datetime.now().strftime('%H:%M')
    
    return render_template(
        'index.html',
        events=events_by_day,
        days=DAYS,
        display_days=display_days,
        display_dates=display_dates,
        day_key_map=day_key_map,
        current_time=current_time
    )

def find_events(events, minute):
    def overlaps(e1_start, e1_end, e2_start, e2_end):
        return e1_start < e2_end and e2_start < e1_end

    # Step 1: Create a mapping of events to their consistent column positions
    # First, get all events that might overlap throughout the day
    all_events = []
    for event in events:
        start = max(480, hhmm_to_minutes(event['start_time']))  # 8:00 AM minimum
        end = hhmm_to_minutes(event['end_time'])
        all_events.append({
            'event': event,
            'start': start,
            'end': end
        })
    
    # Sort by start time, then by duration (longer events first)
    all_events.sort(key=lambda x: (x['start'], x['start'] - x['end']))
    
    # Assign consistent column positions
    event_columns = {}
    columns_in_use = []
    
    for evt in all_events:
        # Remove events that have ended from active columns
        columns_in_use = [col for col in columns_in_use if col['end'] > evt['start']]
        
        # Find the first available column
        used_column_nums = [col['column'] for col in columns_in_use]
        column_num = 0
        while column_num in used_column_nums:
            column_num += 1
        
        # Assign this event to the column
        event_columns[evt['event']['title'] + str(evt['start'])] = column_num
        columns_in_use.append({
            'event_key': evt['event']['title'] + str(evt['start']),
            'column': column_num,
            'end': evt['end']
        })
    
    # Calculate maximum concurrent events for the day
    max_concurrent = 0
    for t in range(480, 18*60, 15):  # Check every 15 minutes from 8 AM to 6 PM
        concurrent = 0
        for evt in all_events:
            if evt['start'] <= t < evt['end']:
                concurrent += 1
        max_concurrent = max(max_concurrent, concurrent)

    # Step 2: Find events active at the current minute
    active_events = []
    for event in events:
        start = max(480, hhmm_to_minutes(event['start_time']))
        end = hhmm_to_minutes(event['end_time'])

        if start <= minute < end:
            event_key = event['title'] + str(start)
            column = event_columns.get(event_key, 0)
            
            active_events.append({
                'event': event,
                'start': start,
                'end': end,
                'is_start_time': minute - start < 15,
                'column': column,
                'max_concurrent': max_concurrent
            })

    # Sort by column position to maintain consistent ordering
    active_events.sort(key=lambda x: x['column'])
    
    # Fill in empty columns to maintain layout consistency
    result_events = []
    used_columns = [evt['column'] for evt in active_events]
    
    for col in range(max_concurrent):
        found = False
        for evt in active_events:
            if evt['column'] == col:
                result_events.append(evt)
                found = True
                break
        if not found:
            # Add placeholder for empty column
            result_events.append({
                'event': {'title': '', 'color': 'transparent', 'start_time': '', 'end_time': '', 'id': None},
                'is_start_time': False,
                'column': col,
                'max_concurrent': max_concurrent,
                'is_placeholder': True
            })

    return result_events

@app.route('/delete/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
    return '', 204  # No Content response

def hhmm_to_minutes(hhmm):
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m

def is_current_day(day_name):
    """Check if the given day name is today"""
    today = datetime.today().strftime('%A')  # Get current day name in English
    return day_name == today

app.jinja_env.globals.update(find_events=find_events, is_current_day=is_current_day)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
