import os
import json
import logging
import backend.utils  # Ensures ffmpeg path is added to PATH if needed
import whisper

logger = logging.getLogger(__name__)

def transcribe_audio(audio_path: str, model_name: str = "base", transcript_dir: str = "data/transcripts") -> dict:
    """
    Transcribes audio using OpenAI Whisper.
    Caches results in a JSON file to avoid re-transcription.
    Returns the transcript dictionary structure.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found at {audio_path}")

    # Build cache path
    audio_filename = os.path.basename(audio_path)
    video_name, _ = os.path.splitext(audio_filename)
    cache_path = os.path.join(transcript_dir, f"{video_name}_transcript.json")

    # Check cache
    if os.path.exists(cache_path):
        logger.info(f"Loading cached transcript from {cache_path}...")
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read cached transcript {cache_path}: {e}. Re-transcribing...")

    # Load model and transcribe
    logger.info(f"Loading Whisper model '{model_name}' and transcribing {audio_path}...")
    try:
        model = whisper.load_model(model_name)
        result = model.transcribe(audio_path)
        
        # Save transcript to cache
        os.makedirs(transcript_dir, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Transcript successfully cached at {cache_path}")
        return result
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        raise RuntimeError(f"Transcription failed: {e}") from e
