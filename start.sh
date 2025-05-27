#!/bin/bash

# -------------------------------
# 🚀 Liap Tui Dev Launcher
# -------------------------------

# Start FastAPI backend
echo "▶️ Starting backend on http://localhost:5050 ..."
PYTHONPATH=backend uvicorn api.main:app --reload --port 5050 &

# Store backend PID so we can kill it later if needed
BACKEND_PID=$!

# Wait a bit to make sure backend starts first
sleep 1

# Start frontend server
echo "🌐 Starting frontend on http://localhost:3000 ..."
cd frontend
python3 -m http.server 3000

# If frontend is stopped (Ctrl+C), kill backend too
echo "🛑 Shutting down backend (PID: $BACKEND_PID)..."
kill $BACKEND_PID

