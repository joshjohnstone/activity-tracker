import json
from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Exercise, Activity
from app.constants import (
    ACTIVITY_CATEGORIES,
    LIFT_CATEGORIES,
    TRACKING_TYPES,
    DISPLAY_FIELDS_BY_TRACKING_TYPE,
    DISPLAY_FIELDS_BY_CATEGORY,
    DEFAULT_EXERCISES
)
from app.utils import parse_duration_to_seconds

bp = Blueprint("main", __name__)

def summarize_activity_details(details):
    tracking_type = details.get("tracking_type")

    if tracking_type == "weighted_reps":
        sets = details.get("sets", [])

        parts = []
        for s in sets:
            reps = s.get("reps")
            weight = s.get("weight")
            if reps or weight:
                parts.append(f"{reps} reps × {weight} lbs")

        return parts

    if tracking_type == "bodyweight_reps":
        sets = details.get("sets", [])

        parts = []
        for s in sets:
            reps = s.get("reps")
            if reps:
                parts.append(f"{reps} reps")

        return parts

    if tracking_type == "timed_hold":
        sets = details.get("sets", [])

        parts = []
        for s in sets:
            seconds = s.get("duration_seconds")
            if seconds:
                minutes = int(seconds) // 60
                remainder = int(seconds) % 60
                parts.append(f"{minutes}:{remainder:02d}")

        return parts

    if tracking_type == "distance_duration":
        distance = details.get("distance")
        unit = details.get("distance_unit") or "miles"
        duration_seconds = details.get("duration_seconds")
        pace = details.get("pace")

        parts = []

        if distance:
            parts.append(f"Distance: {distance} {unit}")

        if duration_seconds:
            minutes = int(duration_seconds) // 60
            seconds = int(duration_seconds) % 60
            parts.append(f"Duration: {minutes}:{seconds:02d}")

        if pace:
            pace_minutes = int(pace)
            pace_seconds = int(round((pace - pace_minutes) * 60))
            parts.append(f"Pace: {pace_minutes}:{pace_seconds:02d} / mile")

        return parts

    if tracking_type == "duration_only":
        seconds = details.get("duration_seconds")
        notes = details.get("notes")

        parts = []

        if seconds:
            minutes = int(seconds) // 60
            remainder = int(seconds) % 60
            parts.append(f"Duration: {minutes}:{remainder:02d}")

        if notes:
            parts.append(f"Notes: {notes}")

        return parts

    return []


@bp.route("/")
@login_required
def home():
    today = date.today().isoformat()

    exercises = (
        Exercise.query
        .filter_by(user_id=current_user.id)
        .order_by(
            Exercise.activity_category,
            Exercise.lift_category,
            Exercise.name
        )
    ) 

    return render_template(
        "index.html", 
        today=today, 
        exercises=exercises,
        LIFT_CATEGORIES=LIFT_CATEGORIES,
        ACTIVITY_CATEGORIES=ACTIVITY_CATEGORIES
    )

@bp.route("/submit", methods=["POST"])
@login_required
def submit():

    form = request.form

    activity_date = form.get("date")
    exercise_id = form.get("exercise_id")

    exercise_obj = Exercise.query.filter_by(
        id=exercise_id,
        user_id=current_user.id
    ).first_or_404()

    activity_category = exercise_obj.activity_category
    tracking_type = exercise_obj.tracking_type

    details = {
        "exercise_id": exercise_obj.id,
        "exercise": exercise_obj.name,
        "activity_category": exercise_obj.activity_category,
        "lift_category": exercise_obj.lift_category,
        "tracking_type": exercise_obj.tracking_type,
    }

    if tracking_type == "weighted_reps":

        reps_list = form.getlist("reps")
        weight_list = form.getlist("weight")

        sets = []

        for reps, weight in zip(reps_list, weight_list):
            if reps or weight:
                sets.append({
                    "reps": reps,
                    "weight": weight
                })

        details["sets"] = sets

    elif tracking_type == "bodyweight_reps":

        reps_list = form.getlist("reps")

        sets = []

        for reps in reps_list:
            if reps:
                sets.append({
                    "reps": reps
                })

        details["sets"] = sets

    elif tracking_type == "timed_hold":

        duration_list = form.getlist("duration")

        sets = []

        for duration in duration_list:
            if duration:
                sets.append({
                    "duration_seconds": parse_duration_to_seconds(duration)
                })

        details["sets"] = sets

    elif tracking_type == "duration_only":

        duration = form.get("duration")

        details["duration_seconds"] = parse_duration_to_seconds(duration)
        details["notes"] = form.get("notes")

    elif tracking_type == "distance_duration":

        distance = float(form.get("distance") or 0)
        duration_seconds = parse_duration_to_seconds(
            form.get("duration")
        )

        pace = None
        if distance > 0 and duration_seconds:
            # pace in minutes per mile
            pace = (duration_seconds / 60) / distance

        details.update({
            "distance": distance,
            "duration_seconds": duration_seconds,
            "pace": pace,
            "run_location": form.get("run_location"),
            "distance_unit": form.get("distance_unit"),
            "strokes": form.get("strokes"),
        })

    elif tracking_type == "notes_only":

        details["notes"] = form.get("notes")

    activity = Activity(
        date=activity_date,
        category=activity_category,
        exercise_id=exercise_obj.id,
        details=json.dumps(details),
        user_id=current_user.id
    )

    db.session.add(activity)
    db.session.commit()

    flash(f"{exercise_obj.name} activity saved successfully.")
    return redirect(url_for("main.home"))

@bp.route("/last_activity/<int:exercise_id>")
@login_required
def last_activity(exercise_id):

    exercise = Exercise.query.filter_by(
        id=exercise_id,
        user_id=current_user.id
    ).first_or_404()

    activity = (
        Activity.query
        .filter_by(
            user_id=current_user.id,
            exercise_id=exercise.id
        )
        .order_by(
            Activity.date.desc(),
            Activity.id.desc()
        )
        .first()
    )
    
    if not activity:
        legacy_activities = (
            Activity.query
            .filter_by(user_id=current_user.id)
            .order_by(
                Activity.date.desc(),
                Activity.id.desc()
            )
            .all()
        )

        for candidate in legacy_activities:
            try:
                details = json.loads(candidate.details or "{}")
            except json.JSONDecodeError:
                continue

            if details.get("exercise") == exercise.name:
                activity = candidate
                break

    if not activity:
        return jsonify({
            "found": False,
            "message": f"No previous {exercise.name} activity found."
        })

    details = json.loads(activity.details)

    return jsonify({
        "found": True,
        "exercise": exercise.name,
        "date": activity.date,
        "tracking_type": details.get("tracking_type"),
        "summary": summarize_activity_details(details)
    })

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
        tracking_type = details.get("tracking_type")

        if tracking_type:
            allowed_fields = DISPLAY_FIELDS_BY_TRACKING_TYPE.get(
                tracking_type,
                []
            )
        else:
            # Legacy fallback for older activities
            allowed_fields = DISPLAY_FIELDS_BY_CATEGORY.get(
                category,
                []
            )

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
        ACTIVITY_CATEGORIES=ACTIVITY_CATEGORIES,
        LIFT_CATEGORIES=LIFT_CATEGORIES,
        TRACKING_TYPES=TRACKING_TYPES
    )

@bp.route("/add_exercise", methods=["POST"])
@login_required
def add_exercise():

    name = request.form.get("name")
    activity_category = request.form.get("activity_category")
    lift_category = request.form.get("lift_category") or None
    tracking_type = request.form.get("tracking_type")

    exercise = Exercise(
        name=name,
        activity_category=activity_category,
        lift_category=lift_category,
        tracking_type=tracking_type,
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

        for name, activity_category, lift_category, tracking_type in DEFAULT_EXERCISES:
            db.session.add(
                Exercise(
                    name=name,
                    activity_category=activity_category,
                    lift_category=lift_category,
                    tracking_type=tracking_type,
                    user_id=user.id
                )
            )

        db.session.commit()

        print("Seeded exercise count:", Exercise.query.count())  

        flash(f"User {email} successfully registered.")
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