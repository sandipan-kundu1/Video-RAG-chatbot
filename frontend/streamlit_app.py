import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load env file
load_dotenv()

BACKEND_URL = "http://localhost:8000"

# Page configurations
st.set_page_config(
    page_title="Video RAG Chatbot Agent",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Utility for formatting seconds to MM:SS or HH:MM:SS
def format_seconds(seconds: float) -> str:
    if seconds is None:
        return "00:00"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

# Custom CSS for premium glassmorphism dark look
st.markdown("""
<style>
    /* Gradient App Title */
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00C6FF, #0072FF, #7E57C2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        text-shadow: 0px 10px 30px rgba(0, 198, 255, 0.15);
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #90A4AE;
        margin-bottom: 2rem;
    }
    
    /* Styled Containers */
    .status-container {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    
    /* Chunks Source Cards */
    .source-card {
        background-color: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-left: 4px solid #00C6FF;
        padding: 14px;
        border-radius: 6px;
        margin-top: 10px;
        margin-bottom: 10px;
        font-size: 0.92rem;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.15);
    }
    
    .source-meta {
        font-weight: 700;
        color: #00C6FF;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Micro interactions */
    div.stButton > button {
        border-radius: 20px;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0px 5px 15px rgba(0, 198, 255, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Main Title Header
st.markdown('<div class="main-title">Video RAG Chatbot Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ask questions from your video transcripts. Handled strictly by local vector storage and Google Gemini.</div>', unsafe_allow_html=True)

# Check Backend Health Status
backend_available = False
backend_status = {}
try:
    response = requests.get(f"{BACKEND_URL}/api/status", timeout=2)
    if response.status_code == 200:
        backend_status = response.json()
        backend_available = True
except Exception:
    backend_available = False

# Sidebar Configuration
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/000000/video-playlist.png", width=100)
    st.markdown("### 🛠️ Control Panel")
    
    # Backend Status Indicator
    if backend_available:
        st.success("🤖 Backend Server: Online")
    else:
        st.error("🚨 Backend Server: Offline")
        st.warning("Please start the FastAPI backend server first. Run: `python app.py` at the project root directory.")
        st.stop()
        
    st.markdown("---")
    
    # Video Upload Form
    st.markdown("#### 📤 Upload Video Files")
    uploaded_files = st.file_uploader(
        "Choose one or more MP4 video files",
        type=["mp4"],
        accept_multiple_files=True,
        key="uploader"
    )
    
    # Process Uploaded Files
    if uploaded_files:
        already_processed = backend_status.get("processed_videos", [])
        
        for file in uploaded_files:
            if file.name not in already_processed:
                st.info(f"New video detected: {file.name}")
                if st.button(f"Process {file.name}", key=f"btn_{file.name}"):
                    with st.spinner(f"Processing '{file.name}'...\n- Saving file\n- Extracting audio\n- Running Whisper model\n- Creating chunks and FAISS database"):
                        try:
                            # Send multi-part file request
                            files = {"file": (file.name, file.getvalue(), "video/mp4")}
                            res = requests.post(f"{BACKEND_URL}/api/upload", files=files)
                            if res.status_code == 200:
                                st.success(f"Successfully processed {file.name}!")
                                # Rerun to update status
                                st.rerun()
                            else:
                                st.error(f"Error processing {file.name}: {res.json().get('detail', res.text)}")
                        except Exception as e:
                            st.error(f"Connection failed: {e}")
            else:
                st.caption(f"✅ {file.name} is indexed.")
                
    st.markdown("---")
    
    # Display Stats
    st.markdown("#### 📊 Database Stats")
    st.markdown(f"**Indexed Videos:** {len(backend_status.get('processed_videos', []))}")
    st.markdown(f"**Total Text Chunks:** {backend_status.get('total_chunks', 0)}")
    st.markdown(f"**Whisper Model:** `{backend_status.get('whisper_model', 'base')}`")
    st.markdown(f"**Gemini Model:** `{backend_status.get('gemini_model', 'gemini-2.5-flash')}`")
    
    # Gemini API Key Status Check
    if backend_status.get("api_key_configured"):
        st.success("API Key Status: Configured")
    else:
        st.warning("API Key Status: Missing key")
        st.info("Please set GEMINI_API_KEY inside the `.env` file at the root of the project to allow chat queries to function.")
        
    st.markdown("---")
    
    # Actions
    st.markdown("#### ⚙️ Database Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Reset DB", help="Clears vector database and all uploaded files"):
            try:
                res = requests.post(f"{BACKEND_URL}/api/clear")
                if res.status_code == 200:
                    st.success("Database cleared!")
                    st.session_state.messages = []
                    st.rerun()
                else:
                    st.error("Failed to clear database.")
            except Exception as e:
                st.error(f"Error: {e}")
    with col2:
        if st.button("🧹 Clear Chat", help="Clears conversation history"):
            st.session_state.messages = []
            st.success("Chat history cleared!")
            st.rerun()

# Main Conversation Panel
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display welcome message if no messages
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(
            "Hello! I am your Video Question Answering assistant. Please upload one or more video files (.mp4) in the sidebar control panel. Once they are processed, you can ask me anything about their content! 🚀"
        )
        if len(backend_status.get("processed_videos", [])) > 0:
            st.markdown(f"**Currently indexed videos in database:**")
            for video in backend_status["processed_videos"]:
                st.markdown(f"- 🎬 `{video}`")

# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Display source expander for assistant messages if present
        if msg.get("role") == "assistant" and msg.get("sources"):
            with st.expander("🔍 Citations & Timestamps"):
                for src in msg["sources"]:
                    st.markdown(f"""
                    <div class="source-card">
                        <div class="source-meta">
                            <span>🎬 <b>{src['video_name']}</b></span>
                            <span>⏱️ <i>{format_seconds(src['start_time'])} - {format_seconds(src['end_time'])}</i></span>
                        </div>
                        <div>"{src['text']}"</div>
                    </div>
                    """, unsafe_allow_html=True)

# User Chat Input
if prompt := st.chat_input("Type your question here..."):
    # Render user query
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Process query
    with st.chat_message("assistant"):
        with st.spinner("Retrieving video clips and generating answer..."):
            try:
                # Format payload with recent history
                payload = {
                    "query": prompt,
                    "chat_history": [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages[:-1]
                    ]
                }
                
                res = requests.post(f"{BACKEND_URL}/api/chat", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    answer = data.get("answer", "")
                    sources = data.get("sources", [])
                    
                    st.markdown(answer)
                    
                    # Display citation expander if sources exist
                    if sources:
                        with st.expander("🔍 Citations & Timestamps"):
                            for src in sources:
                                st.markdown(f"""
                                <div class="source-card">
                                    <div class="source-meta">
                                        <span>🎬 <b>{src['video_name']}</b></span>
                                        <span>⏱️ <i>{format_seconds(src['start_time'])} - {format_seconds(src['end_time'])}</i></span>
                                    </div>
                                    <div>"{src['text']}"</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                    # Record message and citations
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                else:
                    err_msg = res.json().get("detail", "Error contacting server.")
                    st.error(f"Error (status {res.status_code}): {err_msg}")
            except Exception as e:
                st.error(f"Failed to query chatbot backend: {e}")
