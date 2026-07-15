import subprocess
import time
import requests
import os
import sys

# Start the FastAPI server
print("Starting backend server...")
server_process = subprocess.Popen([sys.executable, "-m", "uvicorn", "app:app", "--port", "8000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Wait for server to start
time.sleep(20)

# Check if server is up
try:
    response = requests.get("http://localhost:8000/api/status")
    print(f"Status: {response.json()}")
except Exception as e:
    print(f"Failed to connect to server: {e}")
    server_process.kill()
    out, err = server_process.communicate()
    print(f"Server stderr: {err.decode('utf-8')}")
    print(f"Server stdout: {out.decode('utf-8')}")
    sys.exit(1)

# Upload video
video_path = os.path.join("data", "videos", "What Is AI_ _ Learn all about artificial intelligence 360P.mp4")
print(f"Uploading {video_path}...")
try:
    with open(video_path, 'rb') as f:
        files = {'file': (os.path.basename(video_path), f, 'video/mp4')}
        response = requests.post("http://localhost:8000/api/upload", files=files)
        print(f"Upload response: {response.status_code}")
        print(response.json())
except Exception as e:
    print(f"Upload failed: {e}")

# Ask queries
queries = ["What is AGI?", "What is ASI?"]
for query in queries:
    print(f"\nQuerying: {query}")
    payload = {"query": query, "chat_history": []}
    try:
        response = requests.post("http://localhost:8000/api/chat", json=payload)
        print(f"Chat response: {response.status_code}")
        print(response.json()["answer"])
    except Exception as e:
        print(f"Chat failed: {e}")

# Terminate server
print("\nTerminating server...")
server_process.kill()
print("Done.")
