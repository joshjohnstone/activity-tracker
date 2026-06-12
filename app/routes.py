import json
from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.constants import EXERCISE_CATEGORIES, DISPLAY_FIELDS, DEFAULT_EXERCISES
from app.models import db, User, Exercise, Activity

bp = Blueprint("main", __name__)

@bp.route("/")
@login_required
def home():
    today = date.today().isoformat()

    exercises = (
        Exercise.query
        .order_by(Exercise.name)
        .filter_by(user_id=current_user.id)
    )   

    return render_template(
        "index.html", 
        today=today, 
        exercises=exercises,
        EXERCISE_CATEGORIES=EXERCISE_CATEGORIES
    )

@bp.route("/submit", methods=["POST"])
@login_required
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

    activity = Activity(
        date=activity_date,
        category=category,
        details=json.dumps(details),
        user_id=current_user.id
    )

    db.session.add(activity)
    db.session.commit()   

    return f"""
    <h2>Saved!</h2>
    <p>Stored {category} activity on {activity_date}</p>
    <a href="/">Back</a>
    """

@bp.route("/history")
@login_required
def history():

    category = request.args.get("category")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")



    if category and category != "All":
        query = query.filter(Activity.category == category)

    if start_date:
        query = query.filter(Activity.date >= start_date)

    if end_date:
        query = query.filter(Activity.date <= end_date)

    rows = Activity.query.order_by(
        Activity.date.desc()).filter_by(user_id=current_user.id
    )

    # ---- GROUP BY DATE ----
    grouped = {}

    for row in rows:

        date_key = row.date
        category = row.category
        details = json.loads(row.details)
        weekday = datetime.strptime(date_key, "%Y-%m-%d").strftime("%A")

        # Apply display filter
        allowed_fields = DISPLAY_FIELDS.get(category, [])
        filtered_details = {
            k: v for k, v in details.items()
            if k in allowed_fields
        }

        activity = {
            "id": row.id,
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

@bp.route("/analytics")
@login_required
def analytics():

    exercise_volume = {}
    exercise_frequency = {}
    exercise_time_series = {}

    today = datetime.today().date()

    # Python weekday: Monday=0 ... Sunday=6
    days_since_sunday = (today.weekday() + 1) % 7
    start_of_week = today - timedelta(days=days_since_sunday)

    rows = Activity.query.filter_by(user_id=current_user.id)

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

        category = row.category
        category_counts[category] += 1

        details = json.loads(row.details)
        activity_date = row.date

        # Running analytics
        if category == "Running":
            distance = float(details.get("distance", 0))
            weekly_running.setdefault(activity_date, 0)
            weekly_running[activity_date] += distance

        # Strength volume: sets × reps × weight
        if category == "Strength":

            exercise = details.get("exercise", "Unknown")
            date_str = row.date

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


@bp.route("/exercises")
@login_required
def exercises():
    exercises = (
        Exercise.query
        .order_by(Exercise.name)
        .filter_by(user_id=current_user.id)
    )   

    return render_template(
        "exercises.html",
        exercises=exercises,
        EXERCISE_CATEGORIES=EXERCISE_CATEGORIES
    )

@bp.route("/add_exercise", methods=["POST"])
@login_required
def add_exercise():

    name = request.form.get("name")
    category = request.form.get("category")

    exercise = Exercise(
        name=name,
        category=category,
        user_id=current_user.id
    )

    db.session.add(exercise)
    db.session.commit()

    return redirect("/exercises")

@bp.route("/delete_exercise/<int:id>")
@login_required
def delete_exercise(id):

    exercise = Exercise.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(exercise)
    db.session.commit()

    return redirect("/exercises")

@bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("User already exists")
            return redirect(url_for("main.register"))

        user = User(email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        for name, category in DEFAULT_EXERCISES:
            db.session.add(
                Exercise(
                    name=name,
                    category=category,
                    user_id=user.id
                )
            )

        db.session.commit()

        print("Seeded exercise count:", Exercise.query.count())  

        return redirect(url_for("main.login"))

    return render_template("register.html")

@bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.home"))

        flash("Invalid credentials")

    return render_template("login.html")

@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.login"))

@bp.route("/whoami")
def whoami():
    return {
        "authenticated": current_user.is_authenticated,
        "user_id": current_user.get_id() if current_user.is_authenticated else None,
        "email": getattr(current_user, "email", None)
    }