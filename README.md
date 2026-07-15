# 🎬 Video RAG Chatbot Agent

A Python-based Retrieval-Augmented Generation (RAG) chatbot that allows users to upload one or more MP4 videos and ask questions about their content. The chatbot answers questions strictly using the video transcripts and quotes timestamps, preventing hallucination by refusing to answer questions whose context is missing.

Recently updated with a **Vercel-ready Next.js Frontend**, **JWT Authentication (Login & Register)**, and **AWS EC2 Production Deployment**!

---

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.11+) hosted on AWS EC2
- **Security**: JWT & Bcrypt (Token-based authentication with registration)
- **Frontend**: Next.js (React) hosted on Vercel with custom Vanilla CSS
- **Proxy**: Next.js API Rewrites (Resolves Mixed Content HTTP/HTTPS issues)
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
├── .env                        # Local configurations (Gemini key, paths, models, admin credentials)
├── .env.example                # Configuration template
├── user-data.sh                # AWS EC2 Bootstrap script (Ignored by Git)
│
├── backend/
│   ├── auth.py                 # JWT Authentication, Bcrypt hashing, & User Registration logic
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
├── frontend/                   # 🌟 Vercel-ready Next.js Web App
│   ├── next.config.ts          # Configures API Proxy rewrites to EC2 backend
│   ├── src/app/
│   │   ├── page.tsx            # Main Chat & Video Upload Interface
│   │   ├── login/page.tsx      # JWT Login & Registration Portal
│   │   └── globals.css         # Premium Vanilla CSS styling
│   └── package.json            
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

## 🚀 Setup & Installation (Local Development)

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
2. Open `.env` and fill in your Google AI Studio API key and secure Admin credentials:
   ```ini
   GEMINI_API_KEY=AIzaSy...
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your_secure_password_here
   ```

### 4. Install Frontend Dependencies
Navigate to the Next.js frontend directory and install the Node packages:
```bash
cd frontend
npm install
```

---

## 💻 Running the Application

To run the full stack, you need to start both the FastAPI backend and the Next.js frontend.

### 1. Start the FastAPI Backend
Launch the API server from the root directory:
```bash
python app.py
```
The secure backend server runs on `http://localhost:8000`.

### 2. Start the Next.js Frontend
In a new terminal window, navigate to the frontend folder and start the development server:
```bash
cd frontend
npm run dev
```
The web app opens automatically in your browser at `http://localhost:3000`. 
*(Note: You can register a new account directly from the login page, or sign in using the `ADMIN_USERNAME` configured in your `.env` file).*

---

## 🌍 Production Deployment (AWS & Vercel)

This project has been fully upgraded for production deployment, separating the heavy Machine Learning backend from the fast React frontend.

### 1. AWS EC2 Backend Deployment
Machine Learning libraries (PyTorch, Whisper, FAISS) require significant RAM and disk space, making them unsuitable for standard serverless platforms.
- The backend is designed to be hosted on an **AWS EC2 Instance** (minimum `t3.small` / 2GB RAM).
- A `user-data.sh` bash script is used to automatically install Python, FFmpeg, clone the repository, and start FastAPI as a permanent `systemd` background service (`videorag.service`).
- **Security**: The AWS `.pem` keys and `.env` secrets are strictly ignored via `.gitignore`. You must manually SSH into the EC2 instance to inject the `.env` file!

### 2. Vercel Frontend Deployment
The Next.js frontend is designed to be instantly deployed to Vercel:
```bash
cd frontend
vercel --prod -b NEXT_PUBLIC_API_URL="" --yes
```

#### The Mixed Content Proxy Solution 🔐
When hosting a frontend on Vercel (`https://`) and a backend on a raw EC2 IP address (`http://`), browsers will strictly block all requests due to "Mixed Content" security policies. 
To elegantly solve this without requiring a custom domain and SSL certificate on the EC2 server, we utilize a **Next.js API Rewrite Proxy**. 

In `frontend/next.config.ts`, all traffic sent to `/api/*` is securely forwarded from the Vercel server directly to the EC2 server. The browser only ever communicates with Vercel over HTTPS, completely bypassing the browser's Mixed Content block!

---

## 🧩 Key Features & Behaviors

1. **User Registration & Secure Access**: All endpoints are protected by robust JWT token authentication. Users can register new accounts seamlessly from the UI, with passwords securely hashed via Bcrypt.
2. **API Proxying**: Built-in Vercel proxying to solve HTTP/HTTPS cross-origin and mixed-content issues.
3. **Transcript Caching**: Whisper transcription runs locally. The app caches transcripts in `data/transcripts/` using the video file's hash/name. Re-uploading the same video processes instantaneously.
4. **Collapsible Citations**: Every generated text chunk retains the start and end timestamp of its underlying audio segments. The frontend deduplicates overlapping chunks and displays precise, collapsible dropdown citations for every answer.
5. **Retrieval-Augmented Prompting**: During queries, the top-K relevant blocks are injected into the prompt.
6. **Strict Context Enforcement**: If the retrieved text blocks do not contain the answer, Gemini is instructed to refuse hallucination.
