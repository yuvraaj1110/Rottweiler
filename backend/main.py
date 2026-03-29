import os
import tempfile
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import the clipper utility
from utils.video_clipper import clip_video

app = FastAPI(title="Rottweiler Backend")

# 1. Setup local storage directory
CLIPS_DIR = Path("clips")
CLIPS_DIR.mkdir(exist_ok=True)

# 2. Mount the directory so files are accessible via URL
# Example: https://your-app.up.railway.app/clips/video.mp4
app.mount("/clips", StaticFiles(directory=CLIPS_DIR), name="clips")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process-video")
async def process_video(
    video: UploadFile = File(...), 
    start_time: str = Form(...)
):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = Path(temp_dir) / video.filename
        
        try:
            with open(temp_file_path, "wb") as buffer:
                content = await video.read()
                buffer.write(content)
            
            # The clipper will now save files to our local CLIPS_DIR
            generated_filenames = clip_video(str(temp_file_path), start_time, str(CLIPS_DIR))
            
            if not generated_filenames:
                return {"message": "No motion events found.", "clips": []}

            # Prepare URLs relative to this server
            clips_metadata = []
            for filename in generated_filenames:
                clips_metadata.append({
                    "name": filename,
                    "url": f"/clips/{filename}"
                })

            return {"clips": clips_metadata}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "online"}
