import subprocess
import os
import logging
import shutil

logger = logging.getLogger(__name__)

def extract_audio(video_path: str, audio_output_path: str) -> str:
    """
    Extracts audio from a video file using FFmpeg.
    Returns the path to the extracted audio file.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at {video_path}")
        
    logger.info(f"Extracting audio from {video_path} to {audio_output_path}...")
    
    # Check for ffmpeg binary or use WinGet links fallback on Windows
    ffmpeg_bin = "ffmpeg"
    winget_links_ffmpeg = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Links", "ffmpeg.exe")
    if not shutil.which(ffmpeg_bin) and os.path.exists(winget_links_ffmpeg):
        ffmpeg_bin = winget_links_ffmpeg
        logger.info(f"Using WinGet links FFmpeg fallback path: {ffmpeg_bin}")

    # Run ffmpeg command
    cmd = [
        ffmpeg_bin,
        "-y",                     # Overwrite output files
        "-i", video_path,         # Input file
        "-vn",                    # Disable video
        "-acodec", "libmp3lame",  # MP3 audio codec
        "-ar", "16000",           # 16kHz sample rate (optimal for Whisper)
        "-ac", "1",               # Mono channel
        audio_output_path
    ]
    
    try:
        # Run process
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        logger.info(f"Audio successfully extracted to {audio_output_path}")
        return audio_output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr}")
        raise RuntimeError(f"FFmpeg failed to extract audio: {e.stderr}") from e
    except FileNotFoundError as e:
        logger.error("ffmpeg binary not found in system path.")
        raise RuntimeError("FFmpeg binary not found in system path. Please ensure FFmpeg is installed and added to your environment PATH.") from e

