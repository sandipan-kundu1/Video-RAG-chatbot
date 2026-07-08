# 🎬 Video RAG Chatbot Agent

A Python-based Retrieval-Augmented Generation (RAG) chatbot that allows users to upload one or more MP4 videos and ask questions about their content. The chatbot answers questions strictly using the video transcripts and quotes timestamps, preventing hallucination by refusing to answer questions whose context is missing.

---

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: Streamlit
- **LLM**: Google Gemini API (`gemini-2.5-flash` model via the new `google-genai` SDK)
- **Speech-to-Text**: OpenAI Whisper (Local transcription)
- **Embeddings**: SentenceTransformers (`all-MiniLM-L6-v2` model)
- **Vector Database**: FAISS (Flat IP / Cosine similarity)
- **Video/Audio processing**: FFmpeg

---

## 📂 Project Architecture

```text
video-rag-chatbot/
│
├── app.py                      # FastAPI server (Endpoints, CORS, orchestrator)
├── requirements.txt            # Python dependencies
├── README.md                   # Setup and usage guide
├── .env                        # Local configurations (Gemini key, paths, models)
├── .env.example                # Configuration template
│
├── backend/
│   ├── extractor.py            # FFmpeg audio extractor subprocess
│   ├── transcriber.py          # Whisper speech-to-text with JSON cached transcripts
│   ├── chunker.py              # Custom overlapping sliding-window chunker with timestamps
│   ├── embeddings.py           # SentenceTransformers embedder generator
│   ├── vector_store.py         # FAISS Flat index manager and metadata mapping
│   ├── retriever.py            # Query vector searcher
│   ├── chatbot.py              # Google GenAI client manager and chat router
│   ├── prompts.py              # Strictly defined Gemini system instructions
│   └── utils.py                # Logger setups, directory creation, timestamp formatters
│
├── frontend/
│   └── streamlit_app.py        # Streamlit premium chat interface
│
├── data/                       # Local directory structure (Automatically created)
│   ├── videos/                 # Uploaded raw MP4 files
│   ├── audio/                  # Extracted MP3 audio files
│   ├── transcripts/            # Cached Whisper transcripts (JSON)
│   ├── chunks/                 # Cached text chunk maps (JSON)
│   └── indexes/                # Persisted FAISS index (.index and _metadata.json)
│
└── logs/
    └── app.log                 # Server and application logs
```

---

## 🚀 Setup & Installation

### 1. Install FFmpeg
The transcribing and extraction modules require FFmpeg. Install it on your machine:
- **Windows** (via winget):
  ```powershell
  winget install Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
  ```
- **macOS** (via Homebrew):
  ```bash
  brew install ffmpeg
  ```
- **Linux** (via apt):
  ```bash
  sudo apt update && sudo apt install -y ffmpeg
  ```

### 2. Install Python Dependencies
Install the required packages in your Python environment:
```bash
pip install -r requirements.txt
```

### 3. Configure the Environment
1. Copy the template `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in your Google AI Studio API key:
   ```ini
   GEMINI_API_KEY=AIzaSy...
   ```

---

## 💻 Running the Application

To run the full stack, you need to start both the FastAPI backend and the Streamlit frontend.

### 1. Start the FastAPI Backend
Launch the API server from the root directory:
```bash
python app.py
```
The backend server runs on `http://localhost:8000`.

### 2. Start the Streamlit Frontend
In a new terminal window, start the Streamlit dashboard:
```bash
streamlit run frontend/streamlit_app.py
```
The web app opens automatically in your browser (usually at `http://localhost:8501`).

---

## 🧩 Key Features & Behaviors

1. **Transcript Caching**: Whisper transcription runs locally and can be slow on CPU. The app caches transcripts in `data/transcripts/` using the video file's hash/name. Re-uploading the same video processes instantaneously.
2. **Timestamp Preservation**: Every generated text chunk retains the start and end timestamp of its underlying audio segments.
3. **Retrieval-Augmented Prompting**: During queries, the top-K relevant blocks are injected into the prompt.
4. **Strict Context Enforcement**: If the retrieved text blocks do not contain the answer, Gemini is instructed to respond:
   > "The uploaded video does not contain enough information to answer this question."
5. **Session Chat History**: Streamlit session state stores messages and references, sending conversational history along with each query to provide context-aware chat.
