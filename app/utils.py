def format_pace(pace):
    if not pace:
        return None

    minutes = int(pace)
    seconds = int(round((pace - minutes) * 60))

    return f"{minutes}:{seconds:02d} / mi"

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