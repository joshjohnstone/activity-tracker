import sqlite3
from app.constants import DEFAULT_EXERCISES

DB_PATH = "activities.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def seed_exercises(cur):
    for name, category in DEFAULT_EXERCISES:
        cur.execute(
            """
            INSERT OR IGNORE INTO exercises (name, category)
            VALUES (?, ?)
            """,
            (name, category)
        )

def init_db():
    conn = sqlite3.connect("activities.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            details TEXT NOT NULL
        )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT
    )
    """)

    seed_exercises(cur)

    conn.commit()
    conn.close()
