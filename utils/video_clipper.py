import sqlite3
import subprocess
import os
from datetime import datetime, timezone
from typing import List, Tuple, Optional
import boto3
from botocore.exceptions import NoCredentialsError

DB_PATH = os.getenv("DB_PATH", "../backend/motion_logs.db")


def get_video_start_time(video_start_time_str: str) -> datetime:
    """
    Parse the video start time string into a datetime object.
    Expected format: "YYYY-MM-DD HH:MM:SS" or ISO format.
    """
    try:
        # Try parsing as ISO format first
        return datetime.fromisoformat(video_start_time_str.replace("Z", "+00:00"))
    except ValueError:
        # Try common format
        try:
            return datetime.strptime(video_start_time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError(
                "Unable to parse video start time. Use format: YYYY-MM-DD HH:MM:SS"
            )


def get_video_duration(file_path: str) -> float:
    """
    Get the duration of a video file in seconds using ffprobe.
    """
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "show_entries",
        "format=duration",
        "of",
        "default=noprint_wrappers=1:nokey=1",
        file_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        return duration
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get video duration: {e.stderr}")
    except ValueError:
        raise RuntimeError("Invalid duration output from ffprobe")


def get_motion_logs_during_video(
    video_start: datetime, video_duration_seconds: float
) -> List[Tuple[int, datetime]]:
    """
    Query the database for motion logs that occurred during the video's duration.

    Args:
        video_start: The start time of the video recording
        video_duration_seconds: Duration of the video in seconds

    Returns:
        List of tuples (id, event_timestamp) for logs during the video
    """
    video_end = video_start.timestamp() + video_duration_seconds

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Query for logs between video start and video end
    c.execute(
        """
        SELECT id, event_timestamp 
        FROM motion_logs 
        WHERE strftime('%s', event_timestamp) BETWEEN ? AND ?
        ORDER BY event_timestamp
    """,
        (video_start.timestamp(), video_end),
    )

    rows = c.fetchall()
    conn.close()

    # Convert timestamp strings back to datetime objects
    result = []
    for row in rows:
        log_id = row[0]
        log_time = datetime.fromisoformat(row[1].replace("Z", "+00:00"))
        result.append((log_id, log_time))

    return result


def calculate_relative_offset(video_start: datetime, event_time: datetime) -> float:
    """
    Calculate the relative offset in seconds from video start to event time.

    Args:
        video_start: The start time of the video recording
        event_time: The timestamp of the motion event

    Returns:
        Offset in seconds (can be negative if event happened before video start)
    """
    return (event_time - video_start).total_seconds()


def _upload_to_vultr(local_file_path: str, object_name: str) -> str:
    """
    Upload a file to Vultr Object Storage and return the public URL.

    Args:
        local_file_path: Path to the local file to upload
        object_name: Name/key for the object in the bucket

    Returns:
        Public URL of the uploaded file
    """
    # Get Vultr credentials from environment
    access_key = os.getenv("VULTR_ACCESS_KEY")
    secret_key = os.getenv("VULTR_SECRET_KEY")
    hostname = os.getenv("VULTR_HOSTNAME")
    bucket_name = os.getenv("VULTR_BUCKET_NAME")

    # Validate environment variables
    if not all([access_key, secret_key, hostname, bucket_name]):
        missing = []
        if not access_key:
            missing.append("VULTR_ACCESS_KEY")
        if not secret_key:
            missing.append("VULTR_SECRET_KEY")
        if not hostname:
            missing.append("VULTR_HOSTNAME")
        if not bucket_name:
            missing.append("VULTR_BUCKET_NAME")
        raise ValueError(
            f"Missing Vultr Object Storage environment variables: {', '.join(missing)}"
        )

    # Create S3 client for Vultr
    s3_client = boto3.client(
        "s3",
        endpoint_url=f"https://{hostname}",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    try:
        # Upload file with public-read ACL and video/mp4 content type
        s3_client.upload_file(
            local_file_path,
            bucket_name,
            object_name,
            ExtraArgs={"ACL": "public-read", "ContentType": "video/mp4"},
        )
    except NoCredentialsError:
        raise RuntimeError("Vultr credentials not available or invalid")
    except Exception as e:
        raise RuntimeError(f"Failed to upload to Vultr: {str(e)}")

    # Construct and return public URL
    return f"https://{hostname}/{bucket_name}/{object_name}"


def clip_video(file_path: str, start_time_str: str) -> List[str]:
    """
    Clip video based on motion events logged during the video's duration.
    After creating each clip, upload it to Vultr Object Storage and delete the local copy.

    Args:
        file_path: Path to the input video file
        start_time_str: String representing when the video started recording

    Returns:
        List of public Vultr URLs for the generated clips
    """
    # Check for Vultr environment variables early
    access_key = os.getenv("VULTR_ACCESS_KEY")
    secret_key = os.getenv("VULTR_SECRET_KEY")
    hostname = os.getenv("VULTR_HOSTNAME")
    bucket_name = os.getenv("VULTR_BUCKET_NAME")

    if not all([access_key, secret_key, hostname, bucket_name]):
        missing = []
        if not access_key:
            missing.append("VULTR_ACCESS_KEY")
        if not secret_key:
            missing.append("VULTR_SECRET_KEY")
        if not hostname:
            missing.append("VULTR_HOSTNAME")
        if not bucket_name:
            missing.append("VULTR_BUCKET_NAME")
        raise ValueError(
            f"Missing Vultr Object Storage environment variables: {', '.join(missing)}. "
            "Please set VULTR_ACCESS_KEY, VULTR_SECRET_KEY, VULTR_HOSTNAME, VULTR_BUCKET_NAME"
        )

    # Parse video start time
    video_start = get_video_start_time(start_time_str)

    # Get video duration from file
    video_duration = get_video_duration(file_path)

    # Get motion logs during the video
    motion_logs = get_motion_logs_during_video(video_start, video_duration)

    if not motion_logs:
        print("No motion events found during video duration")
        return []

    upload_urls = []
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_dir = os.path.dirname(file_path)

    for log_id, event_time in motion_logs:
        # Calculate relative offset
        offset_seconds = calculate_relative_offset(video_start, event_time)

        # Calculate FFmpeg start point (10 seconds before event)
        ffmpeg_start = max(0, offset_seconds - 10)  # Don't go negative

        # Create output filename
        output_filename = f"{base_name}_clip_{log_id}_{int(offset_seconds)}s.mp4"
        output_path = os.path.join(output_dir, output_filename)

        # Run FFmpeg command
        cmd = [
            "ffmpeg",
            "-ss",
            str(ffmpeg_start),
            "-t",
            "30",
            "-i",
            file_path,
            "-c",
            "copy",
            output_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"Created clip: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error creating clip for log {log_id}: {e.stderr}")
            continue  # Skip to next log if FFmpeg fails

        # Upload the clip to Vultr
        try:
            public_url = _upload_to_vultr(output_path, output_filename)
            upload_urls.append(public_url)
            # Delete local clip after successful upload
            os.remove(output_path)
            print(f"Uploaded and removed local clip: {output_filename}")
        except Exception as e:
            print(f"Failed to upload clip {output_filename}: {str(e)}")
            # Keep local file for debugging if upload fails
            continue

    return upload_urls


if __name__ == "__main__":
    # Example usage
    print("Video Clipper Utility with Vultr Integration")
    print("===========================================")
