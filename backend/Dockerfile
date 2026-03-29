# Use a slim Python image to keep the build light
FROM python:3.11-slim

# Install system dependencies: FFmpeg and FFprobe are required for video processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . .

# Ensure the clips directory exists
RUN mkdir -p clips

# Expose the port FastAPI runs on
EXPOSE 8000

# Start the server using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
