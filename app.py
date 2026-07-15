import os
import shutil
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Setup logging
from backend.utils import setup_logging, setup_directories
setup_logging()

logger = logging.getLogger("fastapi_app")

from backend.extractor import extract_audio
from backend.transcriber import transcribe_audio
from backend.chunker import chunk_transcript
from backend.embeddings import EmbeddingGenerator
from backend.vector_store import VectorStore
from backend.retriever import Retriever
from backend.chatbot import ChatbotManager
from backend.auth import get_current_user, fake_users_db, verify_password, create_access_token, User, register_user

# App configuration
VIDEO_FOLDER = os.getenv("VIDEO_FOLDER", "data/videos")
AUDIO_FOLDER = os.getenv("AUDIO_FOLDER", "data/audio")
TRANSCRIPT_FOLDER = os.getenv("TRANSCRIPT_FOLDER", "data/transcripts")
CHUNK_FOLDER = os.getenv("CHUNK_FOLDER", "data/chunks")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "data/indexes/faiss_index")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
TOP_K = int(os.getenv("TOP_K", "5"))

# Initialize directories
setup_directories()

logger.info("Initializing Backend Core Components...")
embedding_gen = EmbeddingGenerator(model_name=EMBEDDING_MODEL)

# Embedding dimension for sentence-transformers/all-MiniLM-L6-v2 is 384
vector_store = VectorStore(dimension=384)

# Load existing index if any
if os.path.exists(f"{VECTOR_DB_PATH}.index"):
    vector_store.load(VECTOR_DB_PATH)
else:
    logger.info("No pre-existing vector store index found. Starting fresh.")

retriever = Retriever(vector_store=vector_store, embedding_generator=embedding_gen)
chatbot = ChatbotManager(api_key=GEMINI_API_KEY, model_name=GEMINI_MODEL)

# FastAPI Init
app = FastAPI(title="Video RAG Chatbot Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str
    chat_history: List[ChatMessage] = []

@app.post("/api/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username not in fake_users_db:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user_dict = fake_users_db[form_data.username]
    if not verify_password(form_data.password, user_dict["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user_dict["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/register")
async def register(form_data: OAuth2PasswordRequestForm = Depends()):
    if not form_data.username or not form_data.password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    success = register_user(form_data.username, form_data.password)
    if not success:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Automatically log them in
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/status")
def get_status(current_user: User = Depends(get_current_user)):
    """Returns the processing status of videos and vector store."""
    try:
        videos = []
        if os.path.exists(VIDEO_FOLDER):
            videos = [f for f in os.listdir(VIDEO_FOLDER) if f.lower().endswith(".mp4")]
        
        return {
            "status": "healthy",
            "processed_videos": videos,
            "total_chunks": len(vector_store.metadata),
            "whisper_model": WHISPER_MODEL,
            "embedding_model": EMBEDDING_MODEL,
            "gemini_model": GEMINI_MODEL,
            "api_key_configured": GEMINI_API_KEY not in (None, "", "your_google_ai_studio_api_key")
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """Uploads a video, extracts audio, transcribes, chunks, and builds FAISS index."""
    if not file.filename.lower().endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Only MP4 videos are supported.")
        
    try:
        video_filename = file.filename
        video_path = os.path.join(VIDEO_FOLDER, video_filename)
        
        # 1. Save video file to disk
        logger.info(f"Saving uploaded video to {video_path}...")
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Extract audio
        audio_filename = f"{os.path.splitext(video_filename)[0]}.mp3"
        audio_path = os.path.join(AUDIO_FOLDER, audio_filename)
        extract_audio(video_path, audio_path)
        
        # 3. Transcribe audio
        transcript_result = transcribe_audio(audio_path, model_name=WHISPER_MODEL, transcript_dir=TRANSCRIPT_FOLDER)
        segments = transcript_result.get("segments", [])
        
        # 4. Chunk transcript
        chunks = chunk_transcript(
            transcript_segments=segments,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            video_name=video_filename
        )
        
        if not chunks:
            logger.warning(f"No speech detected or chunks generated for video {video_filename}.")
            return {
                "message": f"Video '{video_filename}' processed, but no transcribable speech was detected.",
                "chunks_count": 0
            }
            
        # Save chunks info to a json for inspectability
        chunks_cache_path = os.path.join(CHUNK_FOLDER, f"{os.path.splitext(video_filename)[0]}_chunks.json")
        import json
        with open(chunks_cache_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
            
        # 5. Generate Embeddings & Index
        chunk_texts = [c["text"] for c in chunks]
        embeddings = embedding_gen.embed_texts(chunk_texts)
        
        # Add to vector store and save
        vector_store.add_chunks(chunks, embeddings)
        vector_store.save(VECTOR_DB_PATH)
        
        return {
            "message": f"Successfully processed and indexed video '{video_filename}'.",
            "chunks_count": len(chunks)
        }
        
    except Exception as e:
        logger.error(f"Failed to process video {file.filename}: {e}")
        # Clean up video file if failed to process
        if 'video_path' in locals() and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/api/chat")
def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """Retrieves relevant transcript chunks and answers using Gemini."""
    try:
        # Check if index has chunks
        if len(vector_store.metadata) == 0:
            return {
                "answer": "No videos have been uploaded and processed yet. Please upload a video first.",
                "sources": []
            }
            
        # 1. Retrieve top K chunks
        retrieved_chunks = retriever.retrieve(request.query, top_k=TOP_K)
        
        # Convert Pydantic history objects to standard dictionary
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.chat_history]
        
        # 2. Get answer from chatbot manager
        answer = chatbot.ask_question(
            query=request.query,
            retrieved_chunks=retrieved_chunks,
            chat_history=history_dicts
        )
        
        return {
            "answer": answer,
            "sources": retrieved_chunks
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat execution failed: {str(e)}")

@app.post("/api/clear")
def clear_data(current_user: User = Depends(get_current_user)):
    """Clears all cached audio, video, transcripts, chunks, and FAISS index."""
    try:
        # Clear vector store in memory
        vector_store.clear()
        
        # Re-save empty index
        vector_store.save(VECTOR_DB_PATH)
        
        # Delete files in video, audio, transcripts, chunks folders
        folders_to_clear = [VIDEO_FOLDER, AUDIO_FOLDER, TRANSCRIPT_FOLDER, CHUNK_FOLDER]
        for folder in folders_to_clear:
            if os.path.exists(folder):
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        logger.warning(f"Failed to delete {file_path}: {e}")
                        
        logger.info("All data and indices have been cleared successfully.")
        return {"message": "All data, cache, and indices cleared successfully."}
    except Exception as e:
        logger.error(f"Clear data failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Allow port to be configurable, default 8000
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
