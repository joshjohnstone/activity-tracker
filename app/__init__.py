from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from app.utils import format_pace
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

    app.jinja_env.globals.update(format_pace=format_pace)

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

    return app