import sqlite3
import subprocess
import os
from datetime import datetime, timezone
from typing import List, Tuple, Optional

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
        "-show_entries",
        "format=duration",
        "-of",
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


def clip_video(file_path: str, start_time_str: str) -> List[str]:
    """
    Clip video based on motion events logged during the video's duration.

    Args:
        file_path: Path to the input video file
        start_time_str: String representing when the video started recording

    Returns:
        List of output file paths that were created
    """
    # Parse video start time
    video_start = get_video_start_time(start_time_str)

    # Get video duration from file
    video_duration = get_video_duration(file_path)

    # Get motion logs during the video
    motion_logs = get_motion_logs_during_video(video_start, video_duration)

    if not motion_logs:
        print("No motion events found during video duration")
        return []

    output_files = []
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
            output_files.append(output_path)
        except subprocess.CalledProcessError as e:
            print(f"Error creating clip for log {log_id}: {e.stderr}")

    return output_files


if __name__ == "__main__":
    # Example usage
    print("Video Clipper Utility")
    print("=====================")
