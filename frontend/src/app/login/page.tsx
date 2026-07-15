"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const endpoint = isRegister ? "/api/register" : "/api/login";
      
      const res = await fetch(`${apiUrl}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData.toString(),
      });

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("token", data.access_token);
        router.push("/");
      } else {
        const errData = await res.json();
        setError(errData.detail || "Authentication failed");
      }
    } catch (err) {
      setError("Failed to connect to server");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
      <div className="glass-panel" style={{ width: "100%", maxWidth: "400px", textAlign: "center" }}>
        <h1 className="gradient-text" style={{ fontSize: "2rem", marginBottom: "20px" }}>Video RAG Chatbot</h1>
        <p style={{ color: "var(--text-muted)", marginBottom: "30px" }}>
          {isRegister ? "Create a new account" : "Sign in to continue"}
        </p>

        <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="input-field"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input-field"
            required
          />
          {error && <div style={{ color: "#ef4444", fontSize: "0.9rem" }}>{error}</div>}
          <button type="submit" className="btn" disabled={loading}>
            {loading ? <span className="spinner"></span> : (isRegister ? "Register" : "Sign In")}
          </button>
        </form>
        
        <p style={{ marginTop: "20px", fontSize: "0.9rem", color: "var(--text-muted)" }}>
          {isRegister ? "Already have an account? " : "Don't have an account? "}
          <span 
            style={{ color: "var(--accent)", cursor: "pointer", fontWeight: 600 }}
            onClick={() => { setIsRegister(!isRegister); setError(""); }}
          >
            {isRegister ? "Sign In" : "Register"}
          </span>
        </p>
      </div>
    </div>
  );
}
