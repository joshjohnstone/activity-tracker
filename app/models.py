from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, UTC
from flask_login import UserMixin

db = SQLAlchemy()

class Exercise(db.Model):

    __tablename__ = "exercises"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    # Legacy column.
    # Previously used for Push/Pull/Legs/etc.
    # New code should prefer lift_category.   
    category = db.Column(
        db.String(50),
        nullable=False
    )

    activity_category = db.Column(
        db.String(50),
        nullable=False,
        default="Strength",
        server_default="Strength"
    )

    lift_category = db.Column(
        db.String(50),
        nullable=True
    )

    tracking_type = db.Column(
        db.String(50),
        nullable=False,
        default="weighted_reps",
        server_default="weighted_reps"
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

class Activity(db.Model):

    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)

    exercise_id = db.Column(
        db.Integer,
        db.ForeignKey("exercises.id"),
        nullable=True
    )   

    exercise = db.relationship("Exercise")

    date = db.Column(
        db.String(20),
        nullable=False
    )

    category = db.Column(
        db.String(50),
        nullable=False
    )

    details = db.Column(
        db.Text,
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC)
    )

    activities = db.relationship("Activity", backref="user", lazy=True)
    exercises = db.relationship("Exercise", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )