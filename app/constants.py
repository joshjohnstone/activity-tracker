ACTIVITY_CATEGORIES = [
    "Strength",
    "Cardio",
    "Mobility",
    "Other"
]

DISPLAY_FIELDS_BY_CATEGORY = {
    "Running": ["distance", "duration", "pace", "run_location"],
    "Strength": ["exercise", "sets"],
    "Mobility": ["mobility_duration", "notes"]
}

DISPLAY_FIELDS_BY_TRACKING_TYPE = {
    "weighted_reps": ["exercise", "tracking_type", "sets"],
    "bodyweight_reps": ["exercise", "tracking_type", "sets"],
    "timed_hold": ["exercise", "tracking_type", "sets"],
    "duration_only": ["exercise", "tracking_type", "duration_seconds", "notes"],
    "distance_duration": [
        "exercise",
        "tracking_type",
        "distance",
        "duration_seconds",
        "pace",
        "run_location",
        "distance_unit",
        "strokes",
    ],
    "notes_only": ["exercise", "tracking_type", "notes"],
}

TRACKING_TYPES = [
    "weighted_reps",
    "bodyweight_reps",
    "timed_hold",
    "duration_only",
    "distance_duration",
    "notes_only"
]

DEFAULT_EXERCISES = [
    ("Squat", "Strength", "Legs", "bodyweight_reps", False),
    ("Back Squat", "Strength", "Legs", "weighted_reps", False),
    ("Deadlift", "Strength", "Pull", "weighted_reps", False),
    ("Romanian Deadlift", "Strength", "Legs", "weighted_reps", False),
    ("Bench Press", "Strength", "Push", "weighted_reps", False),
    ("Incline Bench Press", "Strength", "Push", "weighted_reps", False),
    ("Overhead Press", "Strength", "Shoulders", "weighted_reps", False),
    ("Pull-Up", "Strength", "Pull", "bodyweight_reps", False),
    ("Chin-Up", "Strength", "Pull", "bodyweight_reps", False),
    ("Barbell Row", "Strength", "Pull", "weighted_reps", False),
    ("Dumbbell Bench Press", "Strength", "Push", "weighted_reps", True),
    ("Dumbbell Row", "Strength", "Pull", "weighted_reps", True),
    ("Cable Face Pull", "Strength", "Pull", "weighted_reps", False),
    ("Cable Row", "Strength", "Pull", "weighted_reps", False),
    ("Cable Pull-Down", "Strength", "Pull", "weighted_reps", False),
    ("Lunges", "Strength", "Legs", "weighted_reps", False),
    ("Leg Press", "Strength", "Legs", "weighted_reps", False),
    ("Hip Thrust", "Strength", "Legs", "weighted_reps", False),
    ("Bulgarian Split Squat", "Strength", "Legs", "weighted_reps", False),
    ("Landmine Hack Squat", "Strength", "Legs", "weighted_reps", False),
    ("Machine Leg Curl", "Strength", "Legs", "weighted_reps", False),
    ("Machine Leg Extension", "Strength", "Legs", "weighted_reps", False),
    ("Cable Chest Fly", "Strength", "Push", "weighted_reps", False),
    ("Tricep Cable Pull-Down", "Strength", "Arms", "weighted_reps", False),
    ("Overhead Tricep Dumbbell Extension", "Strength", "Arms", "weighted_reps", False),
    ("Dumbbell Forward Raise", "Strength", "Arms", "weighted_reps", True),
    ("Dumbbell Lateral Raise", "Strength", "Arms", "weighted_reps", True),
    ("Dumbbell Hammer Curl", "Strength", "Arms", "weighted_reps", True),
    ("Dumbbell Concentration Curl", "Strength", "Arms", "weighted_reps", True),

    ("Running", "Cardio", None, "distance_duration", False),
    ("Rowing Machine", "Cardio", None, "distance_duration", False),
    ("Cycling", "Cardio", None, "distance_duration", False),
    ("Elliptical", "Cardio", None, "distance_duration", False),

    ("Yoga", "Mobility", None, "duration_only", False),
    ("Stretching", "Mobility", None, "duration_only", False)
]

TRACKING_TYPE_LABELS = {
    "weighted_reps": "Weighted reps",
    "bodyweight_reps": "Bodyweight reps",
    "timed_hold": "Timed hold",
    "duration_only": "Duration only",
    "distance_duration": "Distance + duration",
    "notes_only": "Notes only",
}

LIFT_CATEGORIES = [
    "Push",
    "Pull",
    "Legs",
    "Core",
    "Shoulders",
    "Arms"
]
