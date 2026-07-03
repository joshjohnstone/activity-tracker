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
    ("Squat", "Strength", "Legs", "bodyweight_reps"),
    ("Back Squat", "Strength", "Legs", "weighted_reps"),
    ("Deadlift", "Strength", "Pull", "weighted_reps"),
    ("Romanian Deadlift", "Strength", "Legs", "weighted_reps"),
    ("Bench Press", "Strength", "Push", "weighted_reps"),
    ("Incline Bench Press", "Strength", "Push", "weighted_reps"),
    ("Overhead Press", "Strength", "Shoulders", "weighted_reps"),
    ("Pull-Up", "Strength", "Pull", "bodyweight_reps"),
    ("Chin-Up", "Strength", "Pull", "bodyweight_reps"),
    ("Barbell Row", "Strength", "Pull", "weighted_reps"),
    ("Dumbbell Bench Press", "Strength", "Push", "weighted_reps"),
    ("Dumbbell Row", "Strength", "Pull", "weighted_reps"),
    ("Cable Face Pull", "Strength", "Pull", "weighted_reps"),
    ("Cable Row", "Strength", "Pull", "weighted_reps"),
    ("Cable Pull-Down", "Strength", "Pull", "weighted_reps"),
    ("Lunges", "Strength", "Legs", "weighted_reps"),
    ("Leg Press", "Strength", "Legs", "weighted_reps"),
    ("Hip Thrust", "Strength", "Legs", "weighted_reps"),
    ("Bulgarian Split Squat", "Strength", "Legs", "weighted_reps"),
    ("Landmine Hack Squat", "Strength", "Legs", "weighted_reps"),
    ("Machine Leg Curl", "Strength", "Legs", "weighted_reps"),
    ("Machine Leg Extension", "Strength", "Legs", "weighted_reps"),
    ("Cable Chest Fly", "Strength", "Push", "weighted_reps"),
    ("Tricep Cable Pull-Down", "Strength", "Arms", "weighted_reps"),
    ("Overhead Tricep Dumbbell Extension", "Strength", "Arms", "weighted_reps"),
    ("Dumbbell Forward Raise", "Strength", "Arms", "weighted_reps"),
    ("Dumbbell Lateral Raise", "Strength", "Arms", "weighted_reps"),
    ("Dumbbell Hammer Curl", "Strength", "Arms", "weighted_reps"),
    ("Dumbbell Concentration Curl", "Strength", "Arms", "weighted_reps"),

    ("Running", "Cardio", None, "distance_duration"),
    ("Rowing Machine", "Cardio", None, "distance_duration"),
    ("Cycling", "Cardio", None, "distance_duration"),
    ("Elliptical", "Cardio", None, "distance_duration"),

    ("Yoga", "Mobility", None, "duration_only"),
    ("Stretching", "Mobility", None, "duration_only")
]

LIFT_CATEGORIES = [
    "Push",
    "Pull",
    "Legs",
    "Core",
    "Shoulders",
    "Arms"
]
