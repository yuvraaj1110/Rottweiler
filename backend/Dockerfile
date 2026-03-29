# Use a slim Python image to keep the build light
FROM python:3.11-slim

# Install system dependencies: FFmpeg and FFprobe are required for video processing
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create directory for persistent SQLite database (will be mounted via volume)
RUN mkdir -p /app/data

# Ensure the clips directory exists (for temporary storage during processing)
RUN mkdir -p clips

# Expose the port FastAPI runs on
EXPOSE 8000

# Start the server using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]