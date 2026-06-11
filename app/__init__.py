from flask import Flask
from flask_migrate import Migrate
from app.utils import format_pace
import os
from app.models import db

def create_app():

    base_dir = os.path.abspath(os.path.dirname(__file__))  # /app

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "..", "templates"),
        static_folder=os.path.join(base_dir, "..", "static")
    )

    # configuration will go here later (Postgres, secret key, etc.)
    app.config["SECRET_KEY"] = "dev"

    db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "activities.db"
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    migrate = Migrate(app, db)

    #with app.app_context():
        #db.create_all()

    # register routes
    from app.routes import bp
    app.register_blueprint(bp)

    app.jinja_env.globals.update(format_pace=format_pace)

    print(app.template_folder)

    return app