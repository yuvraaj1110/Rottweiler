from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import os

# Database setup
DB_PATH = os.getenv("DB_PATH", "motion_logs.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS motion_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_timestamp TIMESTAMP NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# Pydantic model for log event (though we just store current time)
class LogEvent(BaseModel):
    # No input needed; we generate timestamp server-side
    pass


app = FastAPI()


@app.on_event("startup")
def startup_event():
    init_db()


@app.post("/log-event")
def log_event():
    """Save the current server time to the motion_logs table."""
    now = datetime.utcnow()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO motion_logs (event_timestamp) VALUES (?)", (now,))
    conn.commit()
    conn.close()
    return {"id": c.lastrowid, "event_timestamp": now.isoformat() + "Z"}


# Optional: get logs for testing
@app.get("/logs")
def get_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, event_timestamp FROM motion_logs ORDER BY event_timestamp")
    rows = c.fetchall()
    conn.close()
    return [{"id": row[0], "event_timestamp": row[1]} for row in rows]
