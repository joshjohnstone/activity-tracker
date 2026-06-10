def format_pace(pace):
    if not pace:
        return None

    minutes = int(pace)
    seconds = int(round((pace - minutes) * 60))

    return f"{minutes}:{seconds:02d} / mi"