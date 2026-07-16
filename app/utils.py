import calendar
from datetime import date, timedelta

DISTANCE_UNIT_ABBREVIATIONS = {
    "miles": "mi",
    "meters": "m",
    "kilometers": "km",
}

def abbreviate_distance_unit(unit):
    return DISTANCE_UNIT_ABBREVIATIONS.get(unit, "mi")

def format_pace(pace, unit=None):
    if not pace:
        return None

    minutes = int(pace)
    seconds = int(round((pace - minutes) * 60))

    return f"{minutes}:{seconds:02d} / {abbreviate_distance_unit(unit)}"

def format_duration(seconds):
    try:
        total_seconds = int(seconds or 0)
    except (ValueError, TypeError):
        return ""

    if total_seconds <= 0:
        return "0:00"

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    remaining_seconds = total_seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{remaining_seconds:02d}"

    return f"{minutes}:{remaining_seconds:02d}"

def apply_dumbbell_pair_multiplier(details, exercise=None):
    is_paired = details.get("is_dumbbell_pair")

    if is_paired is None and exercise is not None:
        is_paired = bool(exercise.is_dumbbell_pair)

    if not is_paired:
        return

    for s in details.get("sets", []):
        try:
            s["weight"] = float(s.get("weight") or 0) * 2
        except (TypeError, ValueError):
            pass

def get_period_bounds(period_type, offset, today=None):
    """
    Returns (start_date, end_date, label) for the given period_type
    ("week", "month", or "year"), stepped back by offset whole periods
    (0 = current period, 1 = previous, etc).
    """
    if today is None:
        today = date.today()

    if period_type == "week":
        days_since_sunday = (today.weekday() + 1) % 7
        current_week_start = today - timedelta(days=days_since_sunday)
        start_date = current_week_start - timedelta(weeks=offset)
        end_date = start_date + timedelta(days=6)
        label = f"{start_date.strftime('%b %d')} – {end_date.strftime('%b %d, %Y')}"

    elif period_type == "month":
        total_months = today.year * 12 + (today.month - 1) - offset
        year, month0 = divmod(total_months, 12)
        month = month0 + 1

        start_date = date(year, month, 1)
        end_date = date(year, month, calendar.monthrange(year, month)[1])
        label = start_date.strftime("%B %Y")

    elif period_type == "year":
        year = today.year - offset
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        label = str(year)

    else:
        raise ValueError(f"Unknown period_type: {period_type}")

    return start_date, end_date, label

def parse_duration_to_seconds(value):

    if not value:
        return None

    value = str(value).strip()

    if ":" in value:
        parts = value.split(":")

        if len(parts) == 2:
            minutes, seconds = parts
            return int(minutes) * 60 + int(seconds)

        if len(parts) == 3:
            hours, minutes, seconds = parts
            return (
                int(hours) * 3600
                + int(minutes) * 60
                + int(seconds)
            )

    # Fallback: treat plain number as minutes
    return int(float(value) * 60)