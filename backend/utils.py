import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add local WinGet Links/Packages path to process PATH to ensure FFmpeg is visible to Whisper and subprocesses
import shutil
import glob
if not shutil.which("ffmpeg"):
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    added = False
    # Try finding in WinGet packages
    winget_packages = os.path.join(local_app_data, "Microsoft", "WinGet", "Packages", "Gyan.FFmpeg*", "**", "bin")
    ffmpeg_paths = glob.glob(winget_packages, recursive=True)
    if ffmpeg_paths:
        bin_dir = ffmpeg_paths[0]
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
        added = True
    
    if not added:
        winget_path = os.path.join(local_app_data, "Microsoft", "WinGet", "Links")
        if os.path.exists(winget_path) and winget_path not in os.environ.get("PATH", ""):
            os.environ["PATH"] = winget_path + os.pathsep + os.environ.get("PATH", "")


def setup_directories() -> None:
    """Create project directories if they don't exist."""
    dirs = [
        os.getenv("VIDEO_FOLDER", "data/videos"),
        os.getenv("AUDIO_FOLDER", "data/audio"),
        os.getenv("TRANSCRIPT_FOLDER", "data/transcripts"),
        os.getenv("CHUNK_FOLDER", "data/chunks"),
        os.path.dirname(os.getenv("VECTOR_DB_PATH", "data/indexes/faiss_index")),
        "logs"
    ]
    for d in dirs:
        if d:
            os.makedirs(d, exist_ok=True)

def setup_logging() -> None:
    """Configure logging to both file and console."""
    setup_directories()
    
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("logs/app.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

def format_timestamp(seconds: float) -> str:
    """Format raw float seconds into HH:MM:SS or MM:SS."""
    if seconds is None:
        return "00:00"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"
