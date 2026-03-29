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
utils_path = Path(__file__).parent.parent / "utils"
sys.path.append(str(utils_path))

# Database setup
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
DB_PATH = os.getenv("DB_PATH", str(PROJECT_ROOT / "backend" / "motion_logs.db"))


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
clips_dir = Path("./clips")
clips_dir.mkdir(exist_ok=True)
app.mount("/clips", StaticFiles(directory="clips"), name="clips")


@app.post("/process-video")
async def process_video(video: UploadFile = File(...), start_time: str = Form(...)):
    """Process uploaded video and generate clips based on motion events during video duration."""
    # Save uploaded file temporarily
    temp_dir = Path("./temp")
    temp_dir.mkdir(exist_ok=True)
    temp_file_path = temp_dir / video.filename

    try:
        # Write uploaded file to temp location
        with open(temp_file_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)

        # Process video using our clipper utility
        from video_clipper import clip_video

        clip_paths = clip_video(str(temp_file_path), start_time)

        # Move clips to serving directory and prepare response
        clips = []
        for clip_path in clip_paths:
            clip_path_obj = Path(clip_path)
            clip_name = clip_path_obj.name
            # Move clip to serving directory
            serving_path = clips_dir / clip_name
            shutil.move(str(clip_path_obj), str(serving_path))

            clips.append({"name": clip_name, "url": f"/clips/{clip_name}"})

        return {"clips": clips}

    except Exception as e:
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


# Optional: get logs for testing
@app.get("/logs")
def get_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, event_timestamp FROM motion_logs ORDER BY event_timestamp")
    rows = c.fetchall()
    conn.close()
    return [{"id": row[0], "event_timestamp": row[1]} for row in rows]
