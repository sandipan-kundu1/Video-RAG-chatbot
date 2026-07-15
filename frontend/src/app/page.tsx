"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

// Utility for formatting seconds
function formatSeconds(seconds: number) {
  if (seconds == null) return "00:00";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  if (hours > 0) {
    return `${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  }
  return `${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

export default function Home() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  
  const [status, setStatus] = useState<any>(null);
  const [messages, setMessages] = useState<any[]>([{ role: "assistant", content: "Hello! Please upload a video in the sidebar. Once processed, ask me anything!" }]);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const jwt = localStorage.getItem("token");
    if (!jwt) {
      router.push("/login");
    } else {
      setToken(jwt);
      fetchStatus(jwt);
    }
  }, [router]);

  const fetchStatus = async (jwt: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/status`, {
        headers: { "Authorization": `Bearer ${jwt}` }
      });
      if (res.status === 401) {
        localStorage.removeItem("token");
        router.push("/login");
        return;
      }
      if (res.ok) {
        setStatus(await res.json());
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !token) return;
    
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/upload`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData
      });
      if (res.ok) {
        alert("Video processed successfully!");
        fetchStatus(token);
      } else {
        const err = await res.json();
        alert(`Upload failed: ${err.detail}`);
      }
    } catch (e) {
      alert("Connection error during upload");
    } finally {
      setUploading(false);
    }
  };

  const handleClearDB = async () => {
    if (!token) return;
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/clear`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        setMessages([{ role: "assistant", content: "Database cleared!" }]);
        fetchStatus(token);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || !token) return;

    const newMsg = { role: "user", content: prompt };
    setMessages((prev) => [...prev, newMsg]);
    setPrompt("");
    setLoading(true);

    try {
      const payload = {
        query: newMsg.content,
        chat_history: messages.slice(1).map(m => ({ role: m.role, content: m.content }))
      };

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        setMessages((prev) => [...prev, { role: "assistant", content: data.answer, sources: data.sources }]);
      } else {
        const err = await res.json();
        setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${err.detail}` }]);
      }
    } catch (err) {
      setMessages((prev) => [...prev, { role: "assistant", content: "Failed to connect to backend." }]);
    } finally {
      setLoading(false);
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  };

  if (!token) return null; // Wait for redirect

  return (
    <div className="layout-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div>
          <h2 className="gradient-text" style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>Agent Panel</h2>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Control Center</p>
        </div>
        
        <div className="glass-panel" style={{ padding: "15px" }}>
          <h3 style={{ fontSize: "1rem", marginBottom: "15px" }}>📤 Upload Video</h3>
          <div className="file-upload-wrapper">
            <button className="btn" style={{ width: "100%", opacity: uploading ? 0.7 : 1 }}>
              {uploading ? "Processing..." : "Select MP4 File"}
            </button>
            <input type="file" accept=".mp4" onChange={handleFileUpload} disabled={uploading} />
          </div>
          {status?.processed_videos && status.processed_videos.length > 0 && (
            <div style={{ marginTop: "15px", fontSize: "0.85rem" }}>
              <strong style={{ color: "var(--text-muted)" }}>Processed Videos:</strong>
              <ul style={{ listStyleType: "none", paddingLeft: 0, marginTop: "8px", display: "flex", flexDirection: "column", gap: "6px" }}>
                {status.processed_videos.map((vid: string, idx: number) => (
                  <li key={idx} style={{ background: "rgba(255,255,255,0.05)", padding: "6px 10px", borderRadius: "4px" }}>
                    🎬 {vid}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="glass-panel" style={{ padding: "15px" }}>
          <h3 style={{ fontSize: "1rem", marginBottom: "15px" }}>📊 Stats</h3>
          <p style={{ fontSize: "0.9rem", marginBottom: "8px" }}>
            <strong>Indexed Videos:</strong> {status?.processed_videos?.length || 0}
          </p>
          <p style={{ fontSize: "0.9rem", marginBottom: "8px" }}>
            <strong>Total Chunks:</strong> {status?.total_chunks || 0}
          </p>
          <p style={{ fontSize: "0.9rem" }}>
            <strong>Models:</strong> {status?.whisper_model}, {status?.gemini_model}
          </p>
        </div>

        <div className="glass-panel" style={{ padding: "15px", marginTop: "auto" }}>
          <button className="btn" onClick={handleClearDB} style={{ width: "100%", background: "#ef4444", marginBottom: "10px" }}>
            🗑️ Reset Database
          </button>
          <button className="btn" onClick={handleLogout} style={{ width: "100%", background: "#475569" }}>
            🚪 Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        <div style={{ marginBottom: "20px" }}>
          <h1 className="gradient-text" style={{ fontSize: "2.5rem" }}>Video RAG Chatbot</h1>
          <p style={{ color: "var(--text-muted)" }}>Ask questions based on your video transcripts.</p>
        </div>

        <div className="chat-container glass-panel">
          <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "16px", paddingRight: "10px", marginBottom: "16px" }}>
            <div style={{ maxWidth: "800px", margin: "0 auto", width: "100%", display: "flex", flexDirection: "column", gap: "16px" }}>
              {messages.map((m, i) => (
                <div key={i} className={`message ${m.role}`}>
                  <div>{m.content}</div>
                  {m.sources && m.sources.length > 0 && (() => {
                    const uniqueSources = m.sources.filter((src: any, index: number, self: any[]) => 
                      index === self.findIndex((t) => t.text === src.text)
                    );
                    return (
                      <details style={{ marginTop: "12px", borderTop: "1px solid rgba(255,255,255,0.1)", paddingTop: "12px" }}>
                        <summary style={{ fontSize: "0.85rem", color: "var(--text-muted)", cursor: "pointer", userSelect: "none", fontWeight: 600 }}>
                          🔍 View Citations ({uniqueSources.length})
                        </summary>
                        <div style={{ marginTop: "8px" }}>
                          {uniqueSources.map((src: any, idx: number) => (
                            <div key={idx} className="source-card">
                              <div className="source-meta">
                                <span>{src.video_name}</span>
                                <span>{formatSeconds(src.start_time)} - {formatSeconds(src.end_time)}</span>
                              </div>
                              <div style={{ fontStyle: "italic", opacity: 0.9 }}>"{src.text}"</div>
                            </div>
                          ))}
                        </div>
                      </details>
                    );
                  })()}
                </div>
              ))}
              {loading && (
                <div className="message assistant">
                  <span className="spinner"></span> Thinking...
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
          
          <div style={{ borderTop: "1px solid var(--panel-border)", paddingTop: "16px" }}>
            <form onSubmit={handleSendMessage} style={{ display: "flex", gap: "12px", maxWidth: "800px", margin: "0 auto", width: "100%" }}>
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Ask a question..."
                className="input-field"
                style={{ flex: 1 }}
              />
              <button type="submit" className="btn" disabled={loading || !prompt.trim()}>
                Send
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
