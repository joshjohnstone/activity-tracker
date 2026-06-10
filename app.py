from flask import Flask, render_template, request
from datetime import date
import sqlite3
import json
from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, redirect
from collections import defaultdict

app = Flask(__name__)

DISPLAY_FIELDS = {
    "Running": ["distance", "duration", "pace", "run_location"],
    "Strength": ["exercise", "sets"],
    "Mobility": ["mobility_duration", "notes"]
}

DEFAULT_EXERCISES = [
    ("Squat", "Legs"),
    ("Back Squat", "Legs"),
    ("Deadlift", "Pull"),
    ("Romanian Deadlift", "Legs"),
    ("Bench Press", "Push"),
    ("Incline Bench Press", "Push"),
    ("Overhead Press", "Shoulders"),
    ("Pull-Up", "Pull"),
    ("Chin-Up", "Pull"),
    ("Barbell Row", "Pull"),
    ("Dumbbell Bench Press", "Push"),
    ("Dumbbell Row", "Pull"),
    ("Cable Face Pull", "Pull"),
    ("Cable Row", "Pull"),
    ("Cable Pull-Down", "Pull"),
    ("Lunges", "Legs"),
    ("Leg Press", "Legs"),
    ("Hip Thrust", "Legs"),
    ("Bulgarian Split Squat", "Legs"),
    ("Landmine Hack Squat", "Legs"),
    ("Machine Leg Curl", "Legs"),
    ("Machine Leg Extension", "Legs"),
    ("Cable Chest Fly", "Push"),
    ("Tricep Cable Pull-Down", "Arms"),
    ("Overhead Tricep Dumbbell Extension", "Arms"),
    ("Dumbbell Forward Raise", "Arms"),
    ("Dumbbell Lateral Raise", "Arms"),
    ("Dumbbell Hammer Curl", "Arms"),
    ("Dumbbell Concentration Curl", "Arms")
]

EXERCISE_CATEGORIES = [
    "Push",
    "Pull",
    "Legs",
    "Core",
    "Shoulders",
    "Arms",
    "Full Body"
]

def seed_exercises(cur):
    for name, category in DEFAULT_EXERCISES:
        cur.execute(
            """
            INSERT OR IGNORE INTO exercises (name, category)
            VALUES (?, ?)
            """,
            (name, category)
        )

def init_db():
    conn = sqlite3.connect("activities.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            details TEXT NOT NULL
        )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT
    )
    """)

    seed_exercises(cur)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    today = date.today().isoformat()

    conn = sqlite3.connect("activities.db")
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM exercises
        ORDER BY name
    """)

    exercises = cur.fetchall()

    conn.close()

    return render_template(
        "index.html", 
        today=today, 
        exercises=exercises,
        EXERCISE_CATEGORIES=EXERCISE_CATEGORIES
    )


@app.route("/submit", methods=["POST"])
def submit():

    form = request.form.to_dict()

    activity_date = form.get("date")
    category = form.get("category")

    # Remove fields we already store separately
    form.pop("date", None)
    form.pop("category", None)

    # ---- SPECIAL HANDLING FOR STRENGTH ----
    if category == "Strength":

        exercise = form.get("exercise")

        sets = []

        for i in range(1, 4):
            reps = form.get(f"reps_{i}")
            weight = form.get(f"weight_{i}")

            if reps or weight:
                sets.append({
                    "reps": reps,
                    "weight": weight
                })

        details = {
            "exercise": exercise,
            "sets": sets
        }

    # ---- SPECIAL HANDLING FOR RUNNING ----
    elif category == "Running":
        try:
            distance = float(form.get("distance", 0))
            duration = float(form.get("duration", 0))

            # pace = minutes per mile
            pace = None
            if distance > 0:
                pace = duration / distance

            details = {
                "distance": distance,
                "duration": duration,
                "pace": pace 
            }

        except ValueError:
            details = {
                "distance": form.get("distance"),
                "duration": form.get("duration"),
                "pace": None
            }
    else:
        details = form

    # Convert remaining fields into JSON
    details_json = json.dumps(details)

    conn = sqlite3.connect("activities.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO activities (date, category, details)
        VALUES (?, ?, ?)
    """, (activity_date, category, details_json))

    conn.commit()
    conn.close()

    return f"""
    <h2>Saved!</h2>
    <p>Stored {category} activity on {activity_date}</p>
    <a href="/">Back</a>
    """

def format_pace(pace):
    if not pace:
        return None

    minutes = int(pace)
    seconds = int(round((pace - minutes) * 60))

    return f"{minutes}:{seconds:02d} / mi"
app.jinja_env.globals.update(format_pace=format_pace)

@app.route("/history")
def history():

    category = request.args.get("category")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    conn = sqlite3.connect("activities.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = "SELECT * FROM activities WHERE 1=1"
    params = []

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    # ---- GROUP BY DATE ----
    grouped = {}

    for row in rows:

        date_key = row["date"]
        category = row["category"]
        details = json.loads(row["details"])
        weekday = datetime.strptime(date_key, "%Y-%m-%d").strftime("%A")

        # Apply display filter
        allowed_fields = DISPLAY_FIELDS.get(category, [])
        filtered_details = {
            k: v for k, v in details.items()
            if k in allowed_fields
        }

        activity = {
            "id": row["id"],
            "category": category,
            "details": filtered_details
        }

        # Initialize day if needed
        if date_key not in grouped:
            grouped[date_key] = {
                "date": date_key,
                "weekday": weekday,
                "activities": [],
                "summary": {
                    "running_distance": 0.0,
                    "strength_volume": 0.0,
                    "mobility_minutes": 0.0,
                    "counts": {
                        "Running": 0,
                        "Strength": 0,
                        "Mobility": 0
                    }
                }
            }

        day = grouped[date_key]

        day["activities"].append(activity)

        # ---- SUMMARY LOGIC ----
        day["summary"]["counts"][category] += 1

        if category == "Running":
            try:
                day["summary"]["running_distance"] += float(details.get("distance", 0))
            except ValueError:
                pass

        elif category == "Strength":
            try:
                sets_data = details.get("sets", [])

                for s in sets_data:
                    reps = int(s.get("reps", 0) or 0)
                    weight = float(s.get("weight", 0) or 0)

                    day["summary"]["strength_volume"] += reps * weight

            except (ValueError, TypeError):
                pass

        elif category == "Mobility":
            try:
                day["summary"]["mobility_minutes"] += float(details.get("mobility_duration", 0))
            except ValueError:
                pass

    # ---- SORT DAYS (important for consistent display) ----
    grouped_sorted = dict(
        sorted(grouped.items(), reverse=True)
    )

    return render_template(
        "history.html",
        grouped=grouped_sorted,
        category=category,
        start_date=start_date,
        end_date=end_date
    )

@app.route("/analytics")
def analytics():

    exercise_volume = {}
    exercise_frequency = {}
    exercise_time_series = {}

    today = datetime.today().date()

    # Python weekday: Monday=0 ... Sunday=6
    days_since_sunday = (today.weekday() + 1) % 7
    start_of_week = today - timedelta(days=days_since_sunday)

    conn = sqlite3.connect("activities.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM activities")
    rows = cur.fetchall()
    conn.close()

    # Initialize counters
    category_counts = {
        "Running": 0,
        "Strength": 0,
        "Mobility": 0
    }

    weekly_running = {}
    weekly_strength_volume = 0
    exercise_set = set()

    for row in rows:

        category = row["category"]
        category_counts[category] += 1

        details = json.loads(row["details"])
        activity_date = row["date"]

        # Running analytics
        if category == "Running":
            distance = float(details.get("distance", 0))
            weekly_running.setdefault(activity_date, 0)
            weekly_running[activity_date] += distance

        # Strength volume: sets × reps × weight
        if category == "Strength":

            exercise = details.get("exercise", "Unknown")
            date_str = row["date"]

            exercise_set.add(exercise)

            # parse date once (important for weekly filtering)
            activity_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            sets_data = details.get("sets", [])

            daily_volume = 0

            for s in sets_data:
                try:
                    reps = int(s.get("reps") or 0)
                    weight = float(s.get("weight") or 0)
                    daily_volume += reps * weight
                except (ValueError, TypeError):
                    pass

            # ---- TIME SERIES (per exercise) ----
            if exercise not in exercise_time_series:
                exercise_time_series[exercise] = {}

            if date_str not in exercise_time_series[exercise]:
                exercise_time_series[exercise][date_str] = 0

            exercise_time_series[exercise][date_str] += daily_volume

            # ---- WEEKLY TOTAL (FIXED) ----
            if start_of_week <= activity_date <= today:
                weekly_strength_volume += daily_volume

            # ---- OPTIONAL: per-exercise totals ----
            exercise_volume.setdefault(exercise, 0)
            exercise_volume[exercise] += daily_volume

            exercise_frequency.setdefault(exercise, 0)
            exercise_frequency[exercise] += 1

    exercise_list = sorted(list(exercise_set))

    print(exercise_set)
    print(exercise_list)

    return render_template(
        "analytics.html",
        category_counts=category_counts,
        weekly_running=weekly_running,
        weekly_strength_volume=weekly_strength_volume,
        exercise_volume=exercise_volume,
        exercise_frequency=exercise_frequency,
        exercise_time_series=exercise_time_series,
        exercise_list=exercise_list
    )


@app.route("/exercises")
def exercises():

    conn = sqlite3.connect("activities.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM exercises
        ORDER BY name
    """)

    exercises = cur.fetchall()

    conn.close()

    return render_template(
        "exercises.html",
        exercises=exercises,
        EXERCISE_CATEGORIES=EXERCISE_CATEGORIES
    )

@app.route("/add_exercise", methods=["POST"])
def add_exercise():

    name = request.form.get("name")
    category = request.form.get("category")

    conn = sqlite3.connect("activities.db")
    cur = conn.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO exercises (name, category) VALUES (?, ?)",
        (name, category)
    )

    conn.commit()
    conn.close()

    return redirect("/exercises")

@app.route("/delete_exercise/<int:id>")
def delete_exercise(id):

    conn = sqlite3.connect("activities.db")
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM exercises WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/exercises")

init_db()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)