import logging

logger = logging.getLogger(__name__)

def chunk_transcript(
    transcript_segments: list[dict],
    chunk_size: int = 800,
    chunk_overlap: int = 150,
    video_name: str = "unknown"
) -> list[dict]:
    """
    Splits transcript segments into overlapping text chunks, preserving start and end timestamps.
    Each returned chunk has:
      - text: aggregated chunk text
      - start_time: start timestamp in seconds (float)
      - end_time: end timestamp in seconds (float)
      - video_name: video filename source
    """
    logger.info(f"Chunking transcript for {video_name} with chunk_size={chunk_size}, overlap={chunk_overlap}")
    chunks = []
    current_segments = []
    current_length = 0

    for seg in transcript_segments:
        text = seg.get("text", "").strip()
        if not text:
            continue
        current_segments.append(seg)
        current_length += len(text)

        while current_length > chunk_size:
            # Build current chunk
            chunk_text = " ".join([s.get("text", "").strip() for s in current_segments])
            chunks.append({
                "text": chunk_text,
                "start_time": current_segments[0].get("start", 0.0),
                "end_time": current_segments[-1].get("end", 0.0),
                "video_name": video_name
            })
            
            # Pop segment from front to maintain overlap
            removed = current_segments.pop(0)
            current_length -= len(removed.get("text", "").strip())
            
            # If we've popped everything, we stop
            if not current_segments:
                break

    # Process remaining segments
    if current_segments:
        chunk_text = " ".join([s.get("text", "").strip() for s in current_segments])
        chunks.append({
            "text": chunk_text,
            "start_time": current_segments[0].get("start", 0.0),
            "end_time": current_segments[-1].get("end", 0.0),
            "video_name": video_name
        })

    logger.info(f"Generated {len(chunks)} chunks for {video_name}")
    return chunks
