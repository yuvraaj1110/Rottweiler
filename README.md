# 🕵️ Rottweiler: High-Depth IoT Security Terminal

Rottweiler is a high-performance, hardware-linked video indexing and security system. It provides a sleek, technical interface for processing video feeds and synchronizing them with motion event logs recorded in an SQLite database.

## 🛠️ System Architecture

The project is divided into three primary layers, each with high technical specificity:

1.  **Frontend (React/Vite):** A minimal, high-contrast UI following the "Midnight Protocol" design system. It uses Tailwind CSS for granular styling and dynamic state management for video uploads and processing feedback.
2.  **Backend (FastAPI/Uvicorn):** A high-throughput Python API that manages video file handling, metadata extraction, and communication with the SQLite storage layer.
3.  **Utils (FFmpeg/FFprobe):** A specialized video processing module that performs precision clipping and duration analysis using external binary tools.

---

## 🎨 Frontend: "Midnight Protocol" Specification

The interface is engineered for high visibility in low-light "Security Terminal" environments, using a custom-defined color palette:

-   **Primary Background:** Deep Charcoal (`#050505`)
-   **Surface/Card Color:** Dark Navy Tint (`#0A1128`)
-   **Primary Accent:** Electric Navy Blue (`#1E3A8A`)
-   **Cobalt Accent:** High-Visibility Blue (`#2563EB`)
-   **Subtext:** Muted Slate (`#94A3B8`)
-   **Typography:** High-end technical Sans-Serif (Inter) configured as the `font-terminal` family.

**Component Engineering:**
-   **Shadow Glows:** Containers use a 1px border and a subtle navy glow (`box-shadow: 0 0 15px rgba(30, 58, 138, 0.2)`).
-   **Gradients:** Buttons feature high-gloss vertical gradients from Cobalt to Electric Navy with brightening hover effects.

---

## ⚙️ Backend: Logic & Storage Layer

The backend uses **SQLite** for motion log storage, with several technical optimizations to ensure synchronization:

-   **SQL Timestamp Casting:** To resolve type-mismatch errors in SQLite (where `strftime` returns strings), the system uses `CAST(strftime('%s', event_timestamp) AS INTEGER)` to perform precise numeric comparisons between Unix epochs.
-   **Absolute Path Resolution:** In production, `DB_PATH` is hardcoded to `/app/data/rottweiler.db` and the clips directory to `/app/clips`, ensuring alignment with Docker volume mounts.
-   **Metadata Handling:** The `/process-video` endpoint accepts `UploadFile` (FastAPI) and handles multi-part form data for `start_time` (ISO8601/UTC).

---

## 🎞️ Video Processing: "Dynamic Clipping Protocol"

The core utility (`backend/utils/video_clipper.py`) uses duration-aware logic to determine how motion clips are extracted:

| Video Duration | Mode | Pre-Event Buffer | Total Clip Duration | Filename Format |
| :--- | :--- | :--- | :--- | :--- |
| < 60 seconds | **Short** | 5 seconds | 10 seconds | `{video_name}_short_{log_id}.mp4` |
| >= 60 seconds | **Long** | 30 seconds | 60 seconds | `{video_name}_long_{log_id}.mp4` |

**Processing Workflow:**
1.  **Duration Check:** System runs `ffprobe` to determine the exact length of the uploaded video.
2.  **SQL Query:** Performs a `BETWEEN` query to find all motion events recorded during the video's timeframe.
3.  **FFmpeg Clipping:** Executes precision clipping via `subprocess.run`, using the `-ss` (start time) and `-t` (duration) flags to extract relevant segments without re-encoding (`-c copy`).
4.  **Filename Synchronization:** The API response is dynamically synchronized with the generated file paths to ensure consistent naming.

---

## 🚀 Production Deployment & Containerization

Rottweiler is production-ready via **Docker** and **Docker Compose**, ensuring that system dependencies like FFmpeg are always present and data remains persistent.

### 🐳 Docker Configuration
-   **Base Image:** `python:3.11-slim`
-   **System Dependencies:** FFmpeg and FFprobe are installed via `apt-get`.
-   **Persistence:** Volumes are used to ensure that SQLite logs and generated video clips persist across container restarts.

### 🛠️ Docker Compose
```yaml
services:
  rottweiler-backend:
    build: .
    volumes:
      - ./clips:/app/clips      # Video persistence
      - ./data:/app/data        # Database persistence
    environment:
      - DB_PATH=/app/data/rottweiler.db
```

---

## 💻 Local Development

### Backend Setup
1.  Navigate to `backend/`.
2.  Install dependencies: `pip install -r requirements.txt`.
3.  Start the server: `uvicorn main:app --reload`.

### Frontend Setup
1.  Navigate to `frontend/`.
2.  Install dependencies: `npm install`.
3.  Set Environment Variable: Create a `.env` file with `VITE_API_URL=http://localhost:8000`.
4.  Start development server: `npm run dev`.

---

## 📡 API Endpoints

-   `GET /health`: Returns `{"status": "online"}`.
-   `POST /process-video`: Uploads an MP4 file and a start time. Returns a JSON list of generated clips.
-   `POST /log-event`: Records the current server time into the motion logs.
-   `GET /logs`: Retrieves a full history of recorded motion events.
-   `GET /clips/{name}`: Serves generated video segments.
