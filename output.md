# System Audit & Manifest

## Project Mission
Motion-linked video indexing for theft detection.

## Tech Stack
FastAPI (v.current), React/Vite, SQLite, FFmpeg.

## The "Ghost Trigger" Contract
The `POST /log-event` endpoint is designed to simulate a hardware trigger. When the endpoint is called, the server immediately generates a current UTC timestamp, opens a connection to the SQLite database, and inserts this timestamp into the `motion_logs` table. This creates an immutable record of when the simulated event occurred. The endpoint responds with a JSON payload containing the newly created record's `id` and its `event_timestamp` in ISO format.

## The Math
Clipping logic offset is calculated as follows:
$$Offset = EventTime - VideoStartTime$$

## Database Schema
```sql
CREATE TABLE IF NOT EXISTS motion_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_timestamp TIMESTAMP NOT NULL
)
```

## Last System Audit
- **Timestamp of Successful Ghost Trigger**: 2026-03-29T07:14:00.809592+00:00
- **Count of Logs in Database**: 2

## Troubleshooting Guide

### CORS Errors
If the frontend is unable to communicate with the backend API due to Cross-Origin Resource Sharing (CORS) errors, ensure the `CORSMiddleware` is properly configured in `backend/main.py`. The backend should allow all origins (or the specific frontend origin) during development:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### FFmpeg PATH Requirement
The application relies on `ffmpeg` for video processing and clipping. You must ensure that `ffmpeg` is installed on the host system and is available in the system's `PATH` environment variable. If `ffmpeg` is not found, the backend will fail to generate video clips and will throw an error when executing the subprocess commands.

## Code Logic Summaries

### `backend/main.py`
The FastAPI application manages video uploads, clipping logic, and hardware event logging using an SQLite database.
- **Database Initialization (`init_db`)**: Creates a `motion_logs` table with `id` and `event_timestamp` if it doesn't exist.
- **CORS Configuration**: Sets up `CORSMiddleware` allowing all origins, credentials, methods, and headers.
- **Static Files Serving**: Mounts the `./clips` directory to `/clips` to serve the generated video clips.
- **Endpoints**:
  - `POST /process-video`: Receives a video file and a `start_time` string. Saves the uploaded video to a temporary directory. Calls `clip_video` from the `video_clipper` utility to generate video clips based on motion events. Moves the generated clips to the `clips` directory and returns a JSON list of clip names and URLs. Finally, cleans up the temporary video file.
  - `POST /log-event`: Saves the current server time to the `motion_logs` table. Simulates a hardware trigger. Returns the generated `id` and ISO `event_timestamp`.
  - `GET /logs`: Fetches and returns all motion logs ordered by `event_timestamp`.

### `frontend/src/App.jsx`
The React application acts as a Security Terminal, allowing users to upload videos and specify a real-world UTC start time.
- **State Management**: Uses `useState` to manage `videoFile`, `startTime`, `isProcessing`, `clips`, and `error` states.
- **File Handling**: Provides functions for file selection via click (`handleFileChange`) or drag-and-drop (`handleDrop`).
- **Form Submission (`handleSubmit`)**:
  - Validates if a video and start time are provided.
  - Creates a `FormData` object with the video file and start time.
  - Sends a `POST` request to `http://localhost:8000/process-video` using `axios`.
  - Updates the `clips` state with the returned video URLs upon success, or sets the `error` state if the request fails.
  - Manages the `isProcessing` state to show a loading spinner during the API call.
- **UI Elements**:
  - Displays a themed header ("ROTTWEILER V2.0").
  - A form section with a drag-and-drop area for the video and a `datetime-local` input for the start time.
  - A submit button that shows a processing state.
  - An error message display box.
  - A responsive gallery grid displaying generated clips with a "Download" button for each clip.
