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