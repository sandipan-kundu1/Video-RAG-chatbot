import os
import logging
from google import genai
from google.genai import types
from backend.prompts import SYSTEM_PROMPT
from backend.utils import format_timestamp

logger = logging.getLogger(__name__)

class ChatbotManager:
    """Manages queries to Google Gemini API using google-genai SDK."""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        if not api_key or api_key == "your_google_ai_studio_api_key":
            logger.warning("No valid GEMINI_API_KEY found. Chatbot responses will fail unless configured.")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)
            logger.info(f"Gemini client initialized with model '{model_name}'.")

    def ask_question(self, query: str, retrieved_chunks: list[dict], chat_history: list[dict]) -> str:
        """
        Sends context, history, and query to Gemini.
        Returns the text response.
        """
        if not self.client:
            return "Error: Google Gemini API key is not configured. Please add your GEMINI_API_KEY to the .env file."
            
        logger.info(f"Formulating answer for query: '{query}'")
        
        # 1. Format context
        if not retrieved_chunks:
            context_str = "No relevant context found from transcripts."
        else:
            context_blocks = []
            for chunk in retrieved_chunks:
                video = chunk.get("video_name", "unknown")
                start = format_timestamp(chunk.get("start_time", 0.0))
                end = format_timestamp(chunk.get("end_time", 0.0))
                text = chunk.get("text", "").strip()
                context_blocks.append(
                    f"--- Source Video: {video} | Timestamps: {start} - {end} ---\n{text}"
                )
            context_str = "\n\n".join(context_blocks)

        # 2. Build API contents list
        contents = []
        
        # Add past chat history
        # Gemini API expects roles: 'user' and 'model'
        for msg in chat_history:
            role = msg.get("role", "user")
            role = "user" if role == "user" else "model"
            content_text = msg.get("content", "")
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=content_text)]
                )
            )
            
        # Add current prompt containing context and query
        prompt = f"Supplied Transcript Context:\n{context_str}\n\nUser Question: {query}"
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            )
        )

        try:
            # 3. Call API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.0
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API request failed: {e}")
            return f"Error contacting Gemini API: {str(e)}"
