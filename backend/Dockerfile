# Use a slim Python image to keep the build light
FROM python:3.11-slim

# Install system dependencies: FFmpeg and FFprobe are required for video processing
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the backend and utils directories from the project root
COPY backend/ ./backend/
COPY utils/ ./backend/utils/

# Set working directory to backend
WORKDIR /app/backend

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories: temp for uploads, data for persistent SQLite database
RUN mkdir -p /app/backend/temp /app/data

# Expose the port FastAPI runs on
EXPOSE 8000

# Start the server using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]