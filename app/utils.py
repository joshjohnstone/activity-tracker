def format_pace(pace):
    if not pace:
        return None

    minutes = int(pace)
    seconds = int(round((pace - minutes) * 60))

    return f"{minutes}:{seconds:02d} / mi"

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