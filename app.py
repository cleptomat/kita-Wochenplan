from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime, timedelta
import rtc

app = Flask(__name__)
DB_PATH = 'database.db'

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
DISPLAY_DAYS = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
EN_TO_DE = {
    'Monday': 'Montag', 'Tuesday': 'Dienstag', 'Wednesday': 'Mittwoch',
    'Thursday': 'Donnerstag', 'Friday': 'Freitag', 'Saturday': 'Samstag', 'Sunday': 'Sonntag'
}

STANDARD_EVENTS = [
    ("Frühstück", "08:00", "09:30", "#B3E5FC"),
    ("Morgentreff", "09:30", "10:00", "#EFA59F"),
    ("Mittagessen", "12:00", "13:30", "#B3E5FC"),
]
TURNEN_EVENT = ("Turnen", "08:30", "10:00", "#C8E6C9")

START_HOUR = 8
END_HOUR = 15
SLOT_COUNT = (END_HOUR - START_HOUR) * 4  # 15-min slots

def init_db():
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS day_notes (
            date TEXT PRIMARY KEY,
            note TEXT NOT NULL DEFAULT ''
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS week_meals (
            date TEXT PRIMARY KEY,
            meal TEXT NOT NULL DEFAULT ''
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turnen_removed (
            week_monday TEXT PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()

init_db()

def hhmm_to_minutes(hhmm):
    h, m = map(int, hhmm.split(':'))
    return h * 60 + m

def minutes_to_hhmm(minutes):
    minutes = int(minutes)
    return f"{minutes // 60:02}:{minutes % 60:02}"

def get_week_dates(week_offset=0):
    today = rtc.today()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    return [monday + timedelta(days=i) for i in range(7)]

def get_events_by_day(week_offset=0):
    week_dates = get_week_dates(week_offset)
    date_strings = [d.strftime('%Y%m%d') for d in week_dates]
    week_monday = week_dates[0].strftime('%Y%m%d')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    placeholders = ','.join('?' for _ in date_strings)
    cursor.execute(f"""
        SELECT id, title, date, start_time, end_time, image, color
        FROM events
        WHERE date IN ({placeholders})
    """, date_strings)
    rows = cursor.fetchall()

    cursor.execute("SELECT date, meal FROM week_meals WHERE date IN ({})".format(placeholders), date_strings)
    meals_rows = cursor.fetchall()
    meals_by_date = {row[0]: row[1] for row in meals_rows}

    cursor.execute("SELECT date, note FROM day_notes WHERE date IN ({})".format(placeholders), date_strings)
    notes_rows = cursor.fetchall()
    notes_by_date = {row[0]: row[1] for row in notes_rows}

    cursor.execute("SELECT 1 FROM turnen_removed WHERE week_monday=?", (week_monday,))
    turnen_removed = cursor.fetchone() is not None

    conn.close()

    events_by_day = {day: [] for day in DAYS}
    date_to_day = {d.strftime('%Y%m%d'): d.strftime('%A') for d in week_dates}

    for row in rows:
        date_key = row[2]
        if date_key not in date_to_day:
            continue
        weekday = date_to_day[date_key]
        event = {
            'id': row[0],
            'title': row[1],
            'subtitle': '',
            'date': datetime.strptime(row[2], '%Y%m%d').strftime('%Y-%m-%d'),
            'start_time': minutes_to_hhmm(row[3]),
            'end_time': minutes_to_hhmm(row[4]),
            'image': row[5],
            'color': row[6]
        }
        events_by_day[weekday].append(event)

    for i, weekday in enumerate(DAYS[:5]):
        date_obj = week_dates[i]
        date_key = date_obj.strftime('%Y%m%d')

        for title, start, end, color in STANDARD_EVENTS:
            meal_text = ''
            if title == 'Mittagessen':
                meal_text = meals_by_date.get(date_key, '')
            events_by_day[weekday].append({
                'id': None,
                'title': title,
                'subtitle': meal_text if title == 'Mittagessen' else '',
                'date': date_obj.strftime('%Y-%m-%d'),
                'start_time': start,
                'end_time': end,
                'image': None,
                'color': color
            })

        if weekday == 'Tuesday' and not turnen_removed:
            events_by_day[weekday].append({
                'id': None,
                'title': TURNEN_EVENT[0],
                'subtitle': '',
                'date': date_obj.strftime('%Y-%m-%d'),
                'start_time': TURNEN_EVENT[1],
                'end_time': TURNEN_EVENT[2],
                'image': None,
                'color': TURNEN_EVENT[3]
            })

    for day in events_by_day:
        events_by_day[day].sort(key=lambda e: hhmm_to_minutes(e['start_time']))

    return events_by_day, meals_by_date, notes_by_date, turnen_removed, week_dates


@app.route('/', methods=['GET', 'POST'])
def index():
    week_offset = int(request.args.get('week', 0))
    if week_offset not in (0, 1):
        week_offset = 0

    if request.method == 'POST':
        event_id = request.form.get('id')
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
            cursor.execute("""
                UPDATE events SET title=?, date=?, start_time=?, end_time=?, image=?, color=?
                WHERE id=?
            """, (title, date_db, start_minutes, end_minutes, image, color, event_id))
        else:
            cursor.execute("""
                INSERT INTO events (title, date, start_time, end_time, image, color)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, date_db, start_minutes, end_minutes, image, color))
        conn.commit()
        conn.close()
        return redirect(url_for('index', week=week_offset))

    events_by_day, meals_by_date, notes_by_date, turnen_removed, week_dates = get_events_by_day(week_offset)

    display_days = []
    display_dates = []
    day_keys = []

    for i, day in enumerate(DAYS[:5]):
        display_days.append(f"{EN_TO_DE[day]}\n{week_dates[i].strftime('%d.%m.%Y')}")
        display_dates.append(week_dates[i].strftime('%d.%m.%Y'))
        day_keys.append(day)

    if events_by_day['Saturday'] or events_by_day['Sunday']:
        display_days.append(f"{EN_TO_DE['Saturday']}\n{week_dates[5].strftime('%d.%m.%Y')}")
        display_dates.append(week_dates[5].strftime('%d.%m.%Y'))
        day_keys.append('Saturday')
    if events_by_day['Sunday']:
        display_days.append(f"{EN_TO_DE['Sunday']}\n{week_dates[6].strftime('%d.%m.%Y')}")
        display_dates.append(week_dates[6].strftime('%d.%m.%Y'))
        day_keys.append('Sunday')

    day_key_map = {display_days[i]: day_keys[i] for i in range(len(display_days))}

    # Map display_day label -> date string (YYYYMMDD) for notes/meals lookup
    day_date_map = {}
    for i, day_label in enumerate(display_days):
        day_name = day_key_map[day_label]
        idx = DAYS.index(day_name)
        day_date_map[day_label] = week_dates[idx].strftime('%Y%m%d')

    # Build ordered meals list (Mon–Fri) for the meal modal
    meals_list = []
    for i in range(5):
        date_key = week_dates[i].strftime('%Y%m%d')
        meals_list.append({
            'date': date_key,
            'day': EN_TO_DE[DAYS[i]],
            'meal': meals_by_date.get(date_key, '')
        })

    # Allowed date range for event modal (current week Mon – next week Sun)
    today = rtc.today()
    cur_monday = today - timedelta(days=today.weekday())
    min_date = cur_monday.strftime('%Y-%m-%d')
    max_date = (cur_monday + timedelta(days=13)).strftime('%Y-%m-%d')

    current_time = rtc.now().strftime('%H:%M')
    week_monday_key = week_dates[0].strftime('%Y%m%d')

    return render_template(
        'index.html',
        events=events_by_day,
        days=DAYS,
        display_days=display_days,
        display_dates=display_dates,
        day_key_map=day_key_map,
        day_date_map=day_date_map,
        notes_by_date=notes_by_date,
        meals_list=meals_list,
        turnen_removed=turnen_removed,
        week_monday_key=week_monday_key,
        week_offset=week_offset,
        min_date=min_date,
        max_date=max_date,
        current_time=current_time,
        start_hour=START_HOUR,
        end_hour=END_HOUR,
        slot_count=SLOT_COUNT,
    )

def find_events(events, minute):
    all_events = []
    for event in events:
        start = max(START_HOUR * 60, hhmm_to_minutes(event['start_time']))
        end = min(END_HOUR * 60, hhmm_to_minutes(event['end_time']))
        if end <= start:
            continue
        all_events.append({'event': event, 'start': start, 'end': end})

    all_events.sort(key=lambda x: (x['start'], x['start'] - x['end']))

    event_columns = {}
    columns_in_use = []

    for evt in all_events:
        columns_in_use = [col for col in columns_in_use if col['end'] > evt['start']]
        used_column_nums = [col['column'] for col in columns_in_use]
        column_num = 0
        while column_num in used_column_nums:
            column_num += 1
        event_columns[evt['event']['title'] + str(evt['start'])] = column_num
        columns_in_use.append({'event_key': evt['event']['title'] + str(evt['start']), 'column': column_num, 'end': evt['end']})

    # For each event, compute the max concurrent count over its entire duration.
    # If it ever shares a slot with another event, it gets that max width for ALL its slots.
    event_max_concurrent = {}
    for evt in all_events:
        key = evt['event']['title'] + str(evt['start'])
        peak = 0
        for t in range(evt['start'], evt['end'], 15):
            concurrent = sum(1 for other in all_events if other['start'] <= t < other['end'])
            peak = max(peak, concurrent)
        event_max_concurrent[key] = peak

    active_events = []
    for event in events:
        start = max(START_HOUR * 60, hhmm_to_minutes(event['start_time']))
        end = min(END_HOUR * 60, hhmm_to_minutes(event['end_time']))
        if end <= start:
            continue
        if start <= minute < end:
            event_key = event['title'] + str(start)
            column = event_columns.get(event_key, 0)
            max_concurrent = event_max_concurrent.get(event_key, 1)
            offset = minute - start
            subtitle_line = (offset // 15) - 1 if offset >= 15 else -1
            active_events.append({
                'event': event,
                'start': start,
                'end': end,
                'is_start_time': offset < 15,
                'subtitle_line': subtitle_line,
                'column': column,
                'max_concurrent': max_concurrent
            })

    active_events.sort(key=lambda x: x['column'])

    # Use the maximum of all active events' max_concurrent to decide how many
    # columns to render for this slot (keeps widths consistent within a slot)
    slot_columns = max((e['max_concurrent'] for e in active_events), default=0)

    result_events = []
    for col in range(slot_columns):
        found = False
        for evt in active_events:
            if evt['column'] == col:
                result_events.append(evt)
                found = True
                break
        if not found:
            result_events.append({
                'event': {'title': '', 'color': 'transparent', 'start_time': '', 'end_time': '', 'id': None},
                'is_start_time': False,
                'column': col,
                'max_concurrent': slot_columns,
                'is_placeholder': True
            })

    return result_events


@app.route('/delete/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    week_offset = int(request.args.get('week', 0))
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
    return '', 204


@app.route('/save_meals', methods=['POST'])
def save_meals():
    data = request.get_json()
    week_offset = int(data.get('week', 0))
    meals = data.get('meals', {})
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for date_key, meal_text in meals.items():
        cursor.execute("""
            INSERT INTO week_meals (date, meal) VALUES (?, ?)
            ON CONFLICT(date) DO UPDATE SET meal=excluded.meal
        """, (date_key, meal_text))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/save_note', methods=['POST'])
def save_note():
    data = request.get_json()
    date_key = data.get('date')
    note = data.get('note', '')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO day_notes (date, note) VALUES (?, ?)
        ON CONFLICT(date) DO UPDATE SET note=excluded.note
    """, (date_key, note))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/toggle_turnen', methods=['POST'])
def toggle_turnen():
    data = request.get_json()
    week_monday = data.get('week_monday')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM turnen_removed WHERE week_monday=?", (week_monday,))
    if cursor.fetchone():
        cursor.execute("DELETE FROM turnen_removed WHERE week_monday=?", (week_monday,))
        removed = False
    else:
        cursor.execute("INSERT OR IGNORE INTO turnen_removed (week_monday) VALUES (?)", (week_monday,))
        removed = True
    conn.commit()
    conn.close()
    return jsonify({'removed': removed})


def is_current_day(day_name):
    return rtc.today().strftime('%A') == day_name

app.jinja_env.globals.update(find_events=find_events, is_current_day=is_current_day)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
