# ── Stage 1: Build the React frontend ────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Install dependencies first (layer-cached unless package files change)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --legacy-peer-deps

# Copy the rest of the frontend source and build
COPY frontend/ ./
RUN npm run build
# Output lands in /app/frontend/dist

# ── Stage 2: Python runtime ───────────────────────────────────────────────────
FROM python:3.11-slim

# FFmpeg + FFprobe are required for video processing
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend source
COPY backend/ ./backend/

# Copy utils alongside backend so the relative import path resolves
COPY utils/ ./backend/utils/

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the compiled frontend assets so FastAPI can serve them
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Persistent-data directories (clips + SQLite DB)
RUN mkdir -p /app/backend/temp /app/backend/clips /app/data

# FastAPI (uvicorn) listens on 8000; Railway will route traffic here
EXPOSE 8000

# Run from the backend directory so relative paths (clips/, temp/) resolve correctly
WORKDIR /app/backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
