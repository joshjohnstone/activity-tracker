from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, UTC

db = SQLAlchemy()

class Exercise(db.Model):

    __tablename__ = "exercises"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    category = db.Column(
        db.String(50),
        nullable=False
    )

class Activity(db.Model):

    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)

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

class User(db.Model):

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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )