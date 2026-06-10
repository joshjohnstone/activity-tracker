from flask_sqlalchemy import SQLAlchemy

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