#!/bin/bash
# Install dependencies
apt-get update
apt-get install -y python3 python3-pip python3-venv ffmpeg git

# Clone the repository
cd /home/ubuntu
git clone https://github.com/sandipan-kundu1/Video-RAG-chatbot.git
cd Video-RAG-chatbot

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service for FastAPI
cat << 'EOF' > /etc/systemd/system/videorag.service
[Unit]
Description=Video RAG FastAPI Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Video-RAG-chatbot
ExecStart=/home/ubuntu/Video-RAG-chatbot/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start and enable the service
systemctl daemon-reload
systemctl start videorag.service
systemctl enable videorag.service
