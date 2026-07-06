from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from app.utils import format_pace, format_duration
import os
from app.models import db, User

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app():

    base_dir = os.path.abspath(os.path.dirname(__file__))  # /app

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "..", "templates"),
        static_folder=os.path.join(base_dir, "..", "static")
    )

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")

    db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "activities.db"
    )

    database_url = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{db_path}"
    )

    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    migrate = Migrate(app, db)

    #with app.app_context():
        #db.create_all()

    login_manager.init_app(app)
    login_manager.login_view = "main.login"

    # register routes
    from app.routes import bp
    app.register_blueprint(bp)

    app.jinja_env.globals.update(format_pace=format_pace, format_duration=format_duration)

    @app.cli.command("backfill-activity-exercise-ids")
    def backfill_activity_exercise_ids():
        import json
        from app.models import Exercise, Activity

        updated = 0
        skipped = 0

        activities = Activity.query.filter(
            Activity.exercise_id.is_(None)
        ).all()

        for activity in activities:
            try:
                details = json.loads(activity.details or "{}")
            except json.JSONDecodeError:
                skipped += 1
                continue

            exercise_name = details.get("exercise")

            if not exercise_name:
                skipped += 1
                continue

            exercise = Exercise.query.filter_by(
                user_id=activity.user_id,
                name=exercise_name
            ).first()

            if not exercise:
                skipped += 1
                continue

            activity.exercise_id = exercise.id

            details["exercise_id"] = exercise.id
            details["activity_category"] = exercise.activity_category
            details["lift_category"] = exercise.lift_category
            details["tracking_type"] = exercise.tracking_type

            activity.details = json.dumps(details)

            updated += 1

        db.session.commit()

        print(f"Backfilled {updated} activities.")
        print(f"Skipped {skipped} activities.")

    @app.cli.command("seed-default-exercises")
    def seed_default_exercises():
        """
        Add missing DEFAULT_EXERCISES for existing users.

        Also updates missing metadata on existing exercises with matching names.
        This is safe to run multiple times.
        """
        from app.models import db, User, Exercise
        from app.constants import DEFAULT_EXERCISES

        users = User.query.all()

        total_created = 0
        total_updated = 0

        for user in users:
            existing_exercises = Exercise.query.filter_by(user_id=user.id).all()

            existing_by_name = {
                exercise.name.strip().lower(): exercise
                for exercise in existing_exercises
            }

            for name, activity_category, lift_category, tracking_type in DEFAULT_EXERCISES:
                key = name.strip().lower()

                existing = existing_by_name.get(key)

                if existing:
                    changed = False

                    if not existing.activity_category:
                        existing.activity_category = activity_category
                        changed = True

                    if not existing.lift_category and lift_category:
                        existing.lift_category = lift_category
                        changed = True

                    if not existing.tracking_type:
                        existing.tracking_type = tracking_type
                        changed = True

                    # Optional: if legacy Exercise.category is still being used
                    # anywhere old, keep it aligned for strength exercises only.
                    if not existing.category and lift_category:
                        existing.category = lift_category
                        changed = True

                    if changed:
                        total_updated += 1

                else:
                    db.session.add(
                        Exercise(
                            name=name,
                            activity_category=activity_category,
                            lift_category=lift_category,
                            tracking_type=tracking_type,
                            category=lift_category,
                            user_id=user.id,
                        )
                    )
                    total_created += 1

        db.session.commit()

        print(f"Seed complete. Created {total_created} exercises. Updated {total_updated} exercises.")

    return app