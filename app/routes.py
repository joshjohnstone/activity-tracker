import json
import math
from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Exercise, Activity
from app.constants import (
    ACTIVITY_CATEGORIES,
    LIFT_CATEGORIES,
    TRACKING_TYPES,
    TRACKING_TYPE_LABELS,
    DISPLAY_FIELDS_BY_TRACKING_TYPE,
    DISPLAY_FIELDS_BY_CATEGORY,
    DEFAULT_EXERCISES
)
from app.utils import (
    parse_duration_to_seconds,
    abbreviate_distance_unit,
    apply_dumbbell_pair_multiplier,
    get_period_bounds,
    get_today,
)

bp = Blueprint("main", __name__)

def summarize_activity_details(details):
    tracking_type = details.get("tracking_type")

    if tracking_type == "weighted_reps":
        sets = details.get("sets", [])
        notes = details.get("notes")

        parts = []
        for s in sets:
            reps = s.get("reps")
            weight = s.get("weight")
            if reps or weight:
                parts.append(f"{reps} reps × {weight} lbs")

        if notes:
            parts.append(f"Notes: {notes}")

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
            parts.append(f"Pace: {pace_minutes}:{pace_seconds:02d} / {abbreviate_distance_unit(unit)}")

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
    today = get_today().isoformat()

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
        ACTIVITY_CATEGORIES=ACTIVITY_CATEGORIES,
        selected_activity_category=session.get("last_activity_category", "Strength"),
        selected_lift_category=session.get("last_lift_category", "All")
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

    session["last_activity_category"] = activity_category
    session["last_lift_category"] = exercise_obj.lift_category or "All"

    details = {
        "exercise_id": exercise_obj.id,
        "exercise": exercise_obj.name,
        "activity_category": exercise_obj.activity_category,
        "lift_category": exercise_obj.lift_category,
        "tracking_type": exercise_obj.tracking_type,
        "is_dumbbell_pair": exercise_obj.is_dumbbell_pair,
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
        details["notes"] = form.get("notes")

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

@bp.route("/delete_activity/<int:id>", methods=["POST"])
@login_required
def delete_activity(id):

    activity = Activity.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(activity)
    db.session.commit()

    flash("Activity deleted successfully.")
    return redirect(url_for("main.history"))

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

    if details.get("tracking_type") == "weighted_reps":
        apply_dumbbell_pair_multiplier(details, exercise)

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

    activity_category = request.args.get("activity_category", "All")
    lift_category = request.args.get("lift_category", "All")
    exercise_id = request.args.get("exercise_id", "All")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    exercises = (
        Exercise.query
        .filter_by(user_id=current_user.id)
        .order_by(
            Exercise.activity_category,
            Exercise.lift_category,
            Exercise.name
        )
        .all()
    )

    query = (
        Activity.query
        .outerjoin(Exercise, Activity.exercise_id == Exercise.id)
        .filter(Activity.user_id == current_user.id)
    )

    if activity_category and activity_category != "All":
        query = query.filter(Exercise.activity_category == activity_category)

    if lift_category and lift_category != "All":
        query = query.filter(Exercise.lift_category == lift_category)

    if exercise_id and exercise_id != "All":
        query = query.filter(Activity.exercise_id == int(exercise_id))

    if start_date:
        query = query.filter(Activity.date >= start_date)

    if end_date:
        query = query.filter(Activity.date <= end_date)

    rows = query.order_by(
        Activity.date.desc(),
        Activity.id.desc()
    ).all()

    grouped = {}

    for row in rows:

        date_key = row.date
        details = json.loads(row.details or "{}")
        weekday = datetime.strptime(date_key, "%Y-%m-%d").strftime("%A")

        tracking_type = details.get("tracking_type")
        row_exercise = row.exercise

        if tracking_type == "weighted_reps":
            apply_dumbbell_pair_multiplier(details, row_exercise)

        display_category = (
            details.get("activity_category")
            or getattr(row_exercise, "activity_category", None)
            or row.category
        )

        display_exercise = (
            details.get("exercise")
            or getattr(row_exercise, "name", None)
            or display_category
        )

        display_lift_category = (
            details.get("lift_category")
            or getattr(row_exercise, "lift_category", None)
        )

        if tracking_type:
            allowed_fields = DISPLAY_FIELDS_BY_TRACKING_TYPE.get(
                tracking_type,
                []
            )
        else:
            allowed_fields = DISPLAY_FIELDS_BY_CATEGORY.get(
                row.category,
                []
            )

        filtered_details = {
            k: v for k, v in details.items()
            if k in allowed_fields
        }

        activity = {
            "id": row.id,
            "category": display_category,
            "exercise": display_exercise,
            "lift_category": display_lift_category,
            "tracking_type": tracking_type,
            "details": filtered_details
        }

        if date_key not in grouped:
            grouped[date_key] = {
                "date": date_key,
                "weekday": weekday,
                "activities": [],
                "summary": {
                    "counts": {
                        category: 0 for category in ACTIVITY_CATEGORIES
                    },
                    "strength_volume": 0.0,
                    "cardio_distance": 0.0,
                    "mobility_minutes": 0.0,
                }
            }

        day = grouped[date_key]
        day["activities"].append(activity)

        if display_category not in day["summary"]["counts"]:
            day["summary"]["counts"][display_category] = 0

        day["summary"]["counts"][display_category] += 1

        if tracking_type == "weighted_reps":
            try:
                sets_data = details.get("sets", [])

                for s in sets_data:
                    reps = int(s.get("reps", 0) or 0)
                    weight = float(s.get("weight", 0) or 0)
                    day["summary"]["strength_volume"] += reps * weight

            except (ValueError, TypeError):
                pass

        elif tracking_type == "distance_duration":
            try:
                distance = float(details.get("distance", 0) or 0)
                day["summary"]["cardio_distance"] += distance
            except (ValueError, TypeError):
                pass

        elif tracking_type == "duration_only":
            try:
                duration_seconds = int(details.get("duration_seconds", 0) or 0)
                day["summary"]["mobility_minutes"] += duration_seconds / 60
            except (ValueError, TypeError):
                pass

    grouped_activity_items = sorted(
        grouped.items(),
        reverse=True
    )

    page = request.args.get("page", 1, type=int)
    days_per_page = 14

    total_days = len(grouped_activity_items)
    total_pages = max(1, math.ceil(total_days / days_per_page))

    page = max(1, min(page, total_pages))

    start_index = (page - 1) * days_per_page
    end_index = start_index + days_per_page

    paged_grouped_activities = dict(
        grouped_activity_items[start_index:end_index]
    )

    query_args = request.args.to_dict()

    prev_args = {
        **query_args,
        "page": page - 1,
    }

    next_args = {
        **query_args,
        "page": page + 1,
    }

    pagination = {
        "page": page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_args": prev_args,
        "next_args": next_args,
        "total_days": total_days,
        "days_per_page": days_per_page,
    }

    return render_template(
        "history.html",
        grouped=paged_grouped_activities,
        pagination=pagination,
        exercises=exercises,
        ACTIVITY_CATEGORIES=ACTIVITY_CATEGORIES,
        LIFT_CATEGORIES=LIFT_CATEGORIES,
        activity_category=activity_category,
        lift_category=lift_category,
        exercise_id=exercise_id,
        start_date=start_date,
        end_date=end_date
    )

@bp.route("/analytics")
@login_required
def analytics():

    exercise_volume = {}
    exercise_frequency = {}
    exercise_time_series = {}
    exercise_time_series_by_id = {}
    exercise_metadata_by_id = {}
    recent_sessions_by_exercise_id = {}
    prs_by_exercise_id = {}

    today = get_today()

    # Python weekday: Monday=0 ... Sunday=6
    days_since_sunday = (today.weekday() + 1) % 7
    start_of_week = today - timedelta(days=days_since_sunday)

    previous_week_start = start_of_week - timedelta(days=7)
    previous_week_end = previous_week_start + timedelta(days=days_since_sunday)

    rows = Activity.query.filter_by(user_id=current_user.id).all()

    # Avoid requiring an Activity.exercise relationship.
    # This lets us derive new-model metadata from Exercise when exercise_id exists.
    user_exercises = Exercise.query.filter_by(user_id=current_user.id).all()
    exercise_lookup = {exercise.id: exercise for exercise in user_exercises}

    # Initialize counters from the new broad activity categories:
    # Strength, Cardio, Mobility, Other
    category_counts = {category: 0 for category in ACTIVITY_CATEGORIES}

    weekly_running = {}

    weekly_activity_count = 0
    weekly_activity_counts_by_category = {
        category: 0 for category in ACTIVITY_CATEGORIES
    }

    weekly_strength_volume = 0
    previous_week_strength_volume = 0

    weekly_strength_session_count = 0
    previous_week_strength_session_count = 0

    weekly_strength_volume_by_exercise = {}

    exercise_set = set()

    def parse_details(raw_details):
        if not raw_details:
            return {}

        try:
            return json.loads(raw_details)
        except (TypeError, json.JSONDecodeError):
            return {}

    def normalize_activity_category(category):
        """
        Convert legacy categories into the new broad activity category model.
        """
        if category == "Running":
            return "Cardio"

        if category in ACTIVITY_CATEGORIES:
            return category

        return "Other"

    def infer_tracking_type(category, details):
        """
        Fallback for legacy activities that do not yet have Exercise metadata
        or tracking_type stored in details.

        Prefer detecting the data shape over relying on legacy category names.
        """
        if details.get("tracking_type"):
            return details.get("tracking_type")

        sets_data = details.get("sets", [])

        if isinstance(sets_data, list) and sets_data:
            has_weight = any(
                isinstance(s, dict) and "weight" in s
                for s in sets_data
            )

            has_reps = any(
                isinstance(s, dict) and "reps" in s
                for s in sets_data
            )

            has_duration = any(
                isinstance(s, dict) and (
                    "duration_seconds" in s or
                    "duration" in s
                )
                for s in sets_data
            )

            if has_weight and has_reps:
                return "weighted_reps"

            if has_duration:
                return "timed_hold"

            if has_reps:
                return "bodyweight_reps"

        if details.get("distance") is not None:
            return "distance_duration"

        if (
            details.get("duration_seconds") is not None or
            details.get("mobility_duration") is not None
        ):
            return "duration_only"

        if category in ("Running", "Cardio"):
            return "distance_duration"

        if category in ("Strength", "Push", "Pull", "Legs", "Core", "Shoulders", "Arms"):
            return "weighted_reps"

        if category == "Mobility":
            return "duration_only"

        return "notes_only"

    def coerce_activity_date(value):
        """
        Supports either db.Date objects or legacy string dates.
        """
        if isinstance(value, date):
            return value

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                try:
                    return datetime.fromisoformat(value).date()
                except ValueError:
                    return None

        return None
    
    def format_weighted_set_summary(sets_data):
        """
        Turn weighted set data into a compact display string:
        8×135 lbs, 6×145 lbs, 4×155 lbs
        """
        if not sets_data:
            return "No set details"

        parts = []

        for s in sets_data:
            try:
                reps = int(s.get("reps") or 0)
                weight = float(s.get("weight") or 0)
            except (ValueError, TypeError, AttributeError):
                continue

            if reps <= 0 and weight <= 0:
                continue

            weight_text = f"{weight:g}"
            parts.append(f"{reps}×{weight_text} lbs")

        return ", ".join(parts) if parts else "No set details"

    def empty_weighted_prs():
        return {
            "heaviest_set": None,
            "best_estimated_1rm": None,
            "highest_session_volume": None,
            "most_reps": None,
        }


    def estimate_1rm_epley(weight, reps):
        """
        Epley estimate:
        estimated 1RM = weight * (1 + reps / 30)

        Only estimate when weight and reps are positive.
        """
        if weight <= 0 or reps <= 0:
            return 0

        return weight * (1 + reps / 30)


    def update_weighted_prs(prs, date_str, parsed_sets, daily_volume):
        """
        Update weighted PRs for one exercise using a single logged session.
        """
        # Highest session volume
        if daily_volume > 0:
            current = prs["highest_session_volume"]

            if current is None or daily_volume > current["volume"]:
                prs["highest_session_volume"] = {
                    "date": date_str,
                    "volume": daily_volume,
                }

        for s in parsed_sets:
            reps = s["reps"]
            weight = s["weight"]

            if reps <= 0 and weight <= 0:
                continue

            # Heaviest set
            current = prs["heaviest_set"]

            if (
                current is None
                or weight > current["weight"]
                or (weight == current["weight"] and reps > current["reps"])
            ):
                prs["heaviest_set"] = {
                    "date": date_str,
                    "reps": reps,
                    "weight": weight,
                }

            # Best estimated 1RM
            estimated_1rm = estimate_1rm_epley(weight, reps)
            current = prs["best_estimated_1rm"]

            if current is None or estimated_1rm > current["estimated_1rm"]:
                prs["best_estimated_1rm"] = {
                    "date": date_str,
                    "reps": reps,
                    "weight": weight,
                    "estimated_1rm": estimated_1rm,
                }

            # Most reps in a single set
            current = prs["most_reps"]

            if (
                current is None
                or reps > current["reps"]
                or (reps == current["reps"] and weight > current["weight"])
            ):
                prs["most_reps"] = {
                    "date": date_str,
                    "reps": reps,
                    "weight": weight,
                }

    for row in rows:
        details = parse_details(row.details)

        exercise_obj = exercise_lookup.get(row.exercise_id)

        # Prefer new Exercise metadata. Fall back to details, then legacy Activity.category.
        raw_category = (
            exercise_obj.activity_category
            if exercise_obj and exercise_obj.activity_category
            else details.get("activity_category") or row.category
        )

        activity_category = normalize_activity_category(raw_category)

        tracking_type = (
            exercise_obj.tracking_type
            if exercise_obj and exercise_obj.tracking_type
            else infer_tracking_type(row.category, details)
        )

        exercise_name = (
            exercise_obj.name
            if exercise_obj and exercise_obj.name
            else details.get("exercise", "Unknown")
        )

        activity_date = coerce_activity_date(row.date)

        if activity_date:
            date_str = activity_date.isoformat()
        else:
            date_str = str(row.date)

        # ---- CATEGORY COUNTS ----
        category_counts.setdefault(activity_category, 0)
        category_counts[activity_category] += 1

        # ---- THIS WEEK: ACTIVITY COUNT ----
        if activity_date and start_of_week <= activity_date <= today:
            weekly_activity_count += 1

            weekly_activity_counts_by_category.setdefault(activity_category, 0)
            weekly_activity_counts_by_category[activity_category] += 1

        # ---- CARDIO / RUNNING ANALYTICS ----
        # Keep the old variable name weekly_running so analytics.html does not break.
        if tracking_type == "distance_duration":
            try:
                distance = float(details.get("distance") or 0)
            except (ValueError, TypeError):
                distance = 0

            if activity_date:
                weekly_running.setdefault(date_str, 0)
                weekly_running[date_str] += distance

        # ---- STRENGTH VOLUME: sets × reps × weight ----
        #
        # Weighted strength volume applies only to weighted_reps activities.
        # Bodyweight reps, timed holds, etc. should eventually get separate metrics.
        if tracking_type == "weighted_reps":
            apply_dumbbell_pair_multiplier(details, exercise_obj)

            exercise_set.add(exercise_name)

            sets_data = details.get("sets", [])
            daily_volume = 0
            parsed_sets = []

            for s in sets_data:
                try:
                    reps = int(s.get("reps") or 0)
                    weight = float(s.get("weight") or 0)
                except (ValueError, TypeError, AttributeError):
                    continue

                daily_volume += reps * weight

                parsed_sets.append({
                    "reps": reps,
                    "weight": weight,
                })

            if exercise_obj:
                exercise_id_key = str(exercise_obj.id)

                exercise_metadata_by_id[exercise_id_key] = {
                    "id": exercise_obj.id,
                    "name": exercise_obj.name,
                    "activity_category": activity_category,
                    "lift_category": exercise_obj.lift_category,
                    "tracking_type": tracking_type,
                }

                exercise_time_series_by_id.setdefault(exercise_id_key, {})
                exercise_time_series_by_id[exercise_id_key].setdefault(date_str, 0)
                exercise_time_series_by_id[exercise_id_key][date_str] += daily_volume

            if exercise_obj and activity_date:
                exercise_id_key = str(exercise_obj.id)

                recent_sessions_by_exercise_id.setdefault(exercise_id_key, [])
                recent_sessions_by_exercise_id[exercise_id_key].append({
                    "date": date_str,
                    "summary": format_weighted_set_summary(sets_data),
                    "volume": daily_volume,
                })

            # ---- PERSONAL RECORDS ----
            if exercise_obj and activity_date:
                exercise_id_key = str(exercise_obj.id)

                prs = prs_by_exercise_id.setdefault(
                    exercise_id_key,
                    empty_weighted_prs()
                )

                update_weighted_prs(
                    prs=prs,
                    date_str=date_str,
                    parsed_sets=parsed_sets,
                    daily_volume=daily_volume,
                )

            # ---- TIME SERIES: per exercise ----
            exercise_time_series.setdefault(exercise_name, {})
            exercise_time_series[exercise_name].setdefault(date_str, 0)
            exercise_time_series[exercise_name][date_str] += daily_volume

            # ---- THIS WEEK / PREVIOUS WEEK STRENGTH TOTALS ----
            if activity_date:
                if start_of_week <= activity_date <= today:
                    weekly_strength_volume += daily_volume

                    if daily_volume > 0:
                        weekly_strength_session_count += 1

                    weekly_strength_volume_by_exercise.setdefault(exercise_name, 0)
                    weekly_strength_volume_by_exercise[exercise_name] += daily_volume

                if previous_week_start <= activity_date <= previous_week_end:
                    previous_week_strength_volume += daily_volume

                    if daily_volume > 0:
                        previous_week_strength_session_count += 1

            # ---- PER-EXERCISE TOTALS ----
            exercise_volume.setdefault(exercise_name, 0)
            exercise_volume[exercise_name] += daily_volume

            exercise_frequency.setdefault(exercise_name, 0)
            exercise_frequency[exercise_name] += 1

    exercise_list = sorted(list(exercise_set))

    strength_volume_delta = weekly_strength_volume - previous_week_strength_volume

    if previous_week_strength_volume > 0:
        strength_volume_delta_percent = (
            strength_volume_delta / previous_week_strength_volume
        ) * 100
    else:
        strength_volume_delta_percent = None

    if weekly_strength_volume_by_exercise:
        top_strength_exercise_this_week = max(
            weekly_strength_volume_by_exercise.items(),
            key=lambda item: item[1]
        )
    else:
        top_strength_exercise_this_week = None

    exercise_chart_data = {}

    for exercise_id, date_map in exercise_time_series_by_id.items():
        sorted_points = [
            {
                "date": date,
                "volume": volume,
            }
            for date, volume in sorted(date_map.items())
        ]

        exercise_chart_data[exercise_id] = {
            "exercise": exercise_metadata_by_id[exercise_id],
            "points": sorted_points,
        }

    chart_exercises = sorted(
        exercise_metadata_by_id.values(),
        key=lambda exercise: (
            exercise["activity_category"] or "",
            exercise["lift_category"] or "",
            exercise["name"] or "",
        )
    )

    default_chart_exercise_id = None

    if chart_exercises:
        default_chart_exercise_id = str(chart_exercises[0]["id"])

    # -- For recent sessions -- #
    for exercise_id, sessions in recent_sessions_by_exercise_id.items():
        sessions.sort(key=lambda session: session["date"], reverse=True)
        recent_sessions_by_exercise_id[exercise_id] = sessions[:5]

    # -- ALL THE STATS! -- #
    return render_template(
        "analytics.html",
        category_counts=category_counts,
        weekly_running=weekly_running,

        weekly_activity_count=weekly_activity_count,
        weekly_activity_counts_by_category=weekly_activity_counts_by_category,

        weekly_strength_volume=weekly_strength_volume,
        previous_week_strength_volume=previous_week_strength_volume,
        weekly_strength_session_count=weekly_strength_session_count,
        previous_week_strength_session_count=previous_week_strength_session_count,
        strength_volume_delta=strength_volume_delta,
        strength_volume_delta_percent=strength_volume_delta_percent,
        top_strength_exercise_this_week=top_strength_exercise_this_week,

        start_of_week=start_of_week,
        today=today,

        exercise_volume=exercise_volume,
        exercise_frequency=exercise_frequency,
        exercise_time_series=exercise_time_series,
        exercise_list=exercise_list,

        exercise_chart_data=exercise_chart_data,
        chart_exercises=chart_exercises,
        default_chart_exercise_id=default_chart_exercise_id,

        recent_sessions_by_exercise_id=recent_sessions_by_exercise_id,
        prs_by_exercise_id=prs_by_exercise_id,

        LIFT_CATEGORIES=LIFT_CATEGORIES
    )

@bp.route("/insights")
@login_required
def insights():

    period = request.args.get("period", "week")
    if period not in ("week", "month", "year"):
        period = "week"

    try:
        offset = int(request.args.get("offset", 0))
    except (TypeError, ValueError):
        offset = 0

    offset = max(offset, 0)

    start_date, end_date, label = get_period_bounds(period, offset)

    today = get_today()
    effective_end = min(end_date, today)

    rows = (
        Activity.query
        .filter_by(user_id=current_user.id)
        .filter(Activity.date >= start_date.isoformat())
        .filter(Activity.date <= end_date.isoformat())
        .order_by(Activity.date.asc(), Activity.id.asc())
        .all()
    )

    user_exercises = Exercise.query.filter_by(user_id=current_user.id).all()
    exercise_lookup = {exercise.id: exercise for exercise in user_exercises}

    category_counts = {category: 0 for category in ACTIVITY_CATEGORIES}
    active_dates = set()
    lift_category_volume = {}
    sessions_by_exercise_id = {}
    exercise_names_by_id = {}

    for row in rows:
        try:
            details = json.loads(row.details or "{}")
        except json.JSONDecodeError:
            details = {}

        exercise_obj = exercise_lookup.get(row.exercise_id)

        try:
            activity_date = datetime.strptime(row.date, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            activity_date = None

        if activity_date:
            active_dates.add(activity_date)

        raw_category = (
            exercise_obj.activity_category
            if exercise_obj and exercise_obj.activity_category
            else details.get("activity_category") or row.category
        )

        if raw_category == "Running":
            raw_category = "Cardio"

        activity_category = raw_category if raw_category in ACTIVITY_CATEGORIES else "Other"

        category_counts.setdefault(activity_category, 0)
        category_counts[activity_category] += 1

        tracking_type = (
            exercise_obj.tracking_type
            if exercise_obj and exercise_obj.tracking_type
            else details.get("tracking_type")
        )

        if tracking_type == "weighted_reps":
            apply_dumbbell_pair_multiplier(details, exercise_obj)

            session_volume = 0

            for s in details.get("sets", []):
                try:
                    reps = int(s.get("reps") or 0)
                    weight = float(s.get("weight") or 0)
                except (TypeError, ValueError, AttributeError):
                    continue

                session_volume += reps * weight

            lift_category = (
                exercise_obj.lift_category
                if exercise_obj and exercise_obj.lift_category
                else details.get("lift_category")
            ) or "Uncategorized"

            lift_category_volume.setdefault(lift_category, 0)
            lift_category_volume[lift_category] += session_volume

            if exercise_obj and activity_date:
                exercise_names_by_id[exercise_obj.id] = exercise_obj.name

                sessions_by_exercise_id.setdefault(exercise_obj.id, [])
                sessions_by_exercise_id[exercise_obj.id].append({
                    "date": activity_date,
                    "volume": session_volume,
                })

    total_activities = sum(category_counts.values())

    total_days_in_period = max((effective_end - start_date).days + 1, 1)
    percent_days_logged = (len(active_dates) / total_days_in_period) * 100

    candidates = []

    for exercise_id, sessions in sessions_by_exercise_id.items():
        if len(sessions) < 3:
            continue

        first_volume = sessions[0]["volume"]
        last_volume = sessions[-1]["volume"]

        candidates.append({
            "exercise_name": exercise_names_by_id.get(exercise_id, "Unknown"),
            "first_volume": first_volume,
            "last_volume": last_volume,
            "first_date": sessions[0]["date"].isoformat(),
            "last_date": sessions[-1]["date"].isoformat(),
            "delta": last_volume - first_volume,
        })

    most_improved = None
    least_improved = None

    if len(candidates) >= 2:
        most_improved = max(candidates, key=lambda c: c["delta"])
        least_improved = min(candidates, key=lambda c: c["delta"])

    lift_category_order = {category: i for i, category in enumerate(LIFT_CATEGORIES)}
    sorted_lift_category_volume = dict(
        sorted(
            lift_category_volume.items(),
            key=lambda item: lift_category_order.get(item[0], len(LIFT_CATEGORIES))
        )
    )

    return render_template(
        "insights.html",
        period=period,
        offset=offset,
        label=label,
        prev_offset=offset + 1,
        next_offset=max(offset - 1, 0),
        has_next=offset > 0,

        total_activities=total_activities,
        category_counts=category_counts,

        percent_days_logged=percent_days_logged,
        active_day_count=len(active_dates),
        total_days_in_period=total_days_in_period,

        lift_category_volume=sorted_lift_category_volume,

        most_improved=most_improved,
        least_improved=least_improved,
    )

@bp.route("/exercises")
@login_required
def exercises():
    exercises = (
        Exercise.query
        .filter_by(user_id=current_user.id)
        .order_by(Exercise.activity_category, Exercise.lift_category, Exercise.name)
        .all()
    )

    exercise_items = []

    for exercise in exercises:
        # Prefer new-model fields
        activity_category = exercise.activity_category
        lift_category = exercise.lift_category
        tracking_type = exercise.tracking_type

        # Legacy fallback:
        # Older Exercise.category may contain Push/Pull/Legs/etc.
        if not lift_category and exercise.category in LIFT_CATEGORIES:
            lift_category = exercise.category

        if not activity_category:
            if lift_category in LIFT_CATEGORIES:
                activity_category = "Strength"
            else:
                activity_category = "Other"

        if activity_category not in ACTIVITY_CATEGORIES:
            activity_category = "Other"

        if not tracking_type:
            if activity_category == "Strength":
                tracking_type = "weighted_reps"
            elif activity_category == "Cardio":
                tracking_type = "distance_duration"
            elif activity_category == "Mobility":
                tracking_type = "duration_only"
            else:
                tracking_type = "notes_only"

        exercise_items.append({
            "id": exercise.id,
            "name": exercise.name,
            "activity_category": activity_category,
            "lift_category": lift_category,
            "tracking_type": tracking_type,
            "tracking_type_label": TRACKING_TYPE_LABELS.get(tracking_type, tracking_type),
            "is_dumbbell_pair": exercise.is_dumbbell_pair,
        })

    exercise_groups = []

    for activity_category in ACTIVITY_CATEGORIES:
        category_items = [
            item for item in exercise_items
            if item["activity_category"] == activity_category
        ]

        if not category_items:
            continue

        if activity_category == "Strength":
            subgroups = []

            for lift_category in LIFT_CATEGORIES:
                lift_items = [
                    item for item in category_items
                    if item["lift_category"] == lift_category
                ]

                if lift_items:
                    subgroups.append({
                        "name": lift_category,
                        "items": lift_items,
                    })

            uncategorized_items = [
                item for item in category_items
                if not item["lift_category"]
            ]

            if uncategorized_items:
                subgroups.append({
                    "name": "Uncategorized",
                    "items": uncategorized_items,
                })

        else:
            subgroups = [{
                "name": None,
                "items": category_items,
            }]

        exercise_groups.append({
            "name": activity_category,
            "count": len(category_items),
            "subgroups": subgroups,
        })

    return render_template(
        "exercises.html",
        exercise_groups=exercise_groups,
        ACTIVITY_CATEGORIES=ACTIVITY_CATEGORIES,
        LIFT_CATEGORIES=LIFT_CATEGORIES,
        TRACKING_TYPES=TRACKING_TYPES,
        tracking_type_labels=TRACKING_TYPE_LABELS,
    )

@bp.route("/add_exercise", methods=["POST"])
@login_required
def add_exercise():

    name = request.form.get("name")
    activity_category = request.form.get("activity_category")
    lift_category = request.form.get("lift_category") or None
    tracking_type = request.form.get("tracking_type")
    is_dumbbell_pair = "is_dumbbell_pair" in request.form

    exercise = Exercise(
        name=name,
        activity_category=activity_category,
        lift_category=lift_category,
        tracking_type=tracking_type,
        is_dumbbell_pair=is_dumbbell_pair,
        user_id=current_user.id
    )

    db.session.add(exercise)
    db.session.commit()

    return redirect("/exercises")

@bp.route("/edit_exercise/<int:id>", methods=["GET", "POST"])
@login_required
def edit_exercise(id):

    exercise = Exercise.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":
        exercise.name = request.form.get("name")
        exercise.activity_category = request.form.get("activity_category")
        exercise.lift_category = request.form.get("lift_category") or None
        exercise.tracking_type = request.form.get("tracking_type")
        exercise.is_dumbbell_pair = "is_dumbbell_pair" in request.form

        db.session.commit()

        flash(f"{exercise.name} updated successfully.")
        return redirect("/exercises")

    return render_template(
        "edit_exercise.html",
        exercise=exercise,
        ACTIVITY_CATEGORIES=ACTIVITY_CATEGORIES,
        LIFT_CATEGORIES=LIFT_CATEGORIES,
        TRACKING_TYPES=TRACKING_TYPES,
        tracking_type_labels=TRACKING_TYPE_LABELS,
    )

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

        for name, activity_category, lift_category, tracking_type, is_dumbbell_pair in DEFAULT_EXERCISES:
            db.session.add(
                Exercise(
                    name=name,
                    activity_category=activity_category,
                    lift_category=lift_category,
                    tracking_type=tracking_type,
                    is_dumbbell_pair=is_dumbbell_pair,
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