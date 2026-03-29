from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import shutil
from pydantic import BaseModel
from datetime import datetime, timezone
import sqlite3
import os
import sys
from pathlib import Path

# Add utils directory to path
# We are moving utils/ into backend/ for better Docker context support
utils_path = Path(__file__).parent / "utils"
sys.path.append(str(utils_path))

from video_clipper import clip_video

# Database setup
# Use /app/data/ as the primary directory for production (Docker)
# Fallback to local 'data' directory for development
DB_DIR = Path(os.getenv("DB_DIR", "/app/data" if os.path.exists("/app") else str(Path(__file__).parent / "data")))
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = os.getenv("DB_PATH", str(DB_DIR / "motion_logs.db"))


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

# Add CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()


# Create clips directory for serving generated videos
# In production on Railway, we might want to use a persistent volume for this if we want clips to persist.
# Using /app/clips for Docker persistence, fallback to local 'clips'
CLIPS_DIR = Path(os.getenv("CLIPS_DIR", "/app/clips" if os.path.exists("/app") else str(Path(__file__).parent / "clips")))
CLIPS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/clips", StaticFiles(directory=str(CLIPS_DIR)), name="clips")


@app.post("/process-video")
async def process_video(video: UploadFile = File(...), start_time: str = Form(...)):
    """Process uploaded video and generate clips based on motion events during video duration."""
    # Save uploaded file temporarily
    # Using /app/temp for Docker, fallback to local 'temp'
    TEMP_DIR = Path(os.getenv("TEMP_DIR", "/app/temp" if os.path.exists("/app") else str(Path(__file__).parent / "temp")))
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    temp_file_path = TEMP_DIR / video.filename

    try:
        # Write uploaded file to temp location
        with open(temp_file_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)

        # Process video using our clipper utility
        clip_paths = clip_video(str(temp_file_path), start_time)

        # Move clips to the served directory and prepare response
        clips_response = []
        for path_str in clip_paths:
            path = Path(path_str)
            target_path = CLIPS_DIR / path.name
            # Move the clip from temp location to CLIPS_DIR
            shutil.move(str(path), str(target_path))

            # Use relative URL for the frontend
            clips_response.append({
                "name": path.name,
                "url": f"/clips/{path.name}"
            })

        return {"clips": clips_response}

    except Exception as e:
        print(f"Error processing video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up temp file
        if temp_file_path.exists():
            temp_file_path.unlink()


@app.post("/log-event")
def log_event():
    """Save the current server time to the motion_logs table."""
    now = datetime.now(timezone.utc)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO motion_logs (event_timestamp) VALUES (?)", (now,))
    conn.commit()
    conn.close()
    return {"id": c.lastrowid, "event_timestamp": now.isoformat()}


@app.get("/health")
def health_check():
    return {"status": "online"}


# Optional: get logs for testing
@app.get("/logs")
def get_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, event_timestamp FROM motion_logs ORDER BY event_timestamp")
    rows = c.fetchall()
    conn.close()
    return [{"id": row[0], "event_timestamp": row[1]} for row in rows]
