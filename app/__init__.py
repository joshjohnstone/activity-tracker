from flask import Flask
from app.utils import format_pace
import os

def create_app():

    base_dir = os.path.abspath(os.path.dirname(__file__))  # /app

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "..", "templates"),
        static_folder=os.path.join(base_dir, "..", "static")
    )

    # configuration will go here later (Postgres, secret key, etc.)
    app.config["SECRET_KEY"] = "dev"

    # register routes
    from app.routes import bp
    app.register_blueprint(bp)

    app.jinja_env.globals.update(format_pace=format_pace)

    print(app.template_folder)

    return app