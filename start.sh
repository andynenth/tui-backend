#!/bin/bash

# -------------------------------
# 🚀 Liap Tui Dev Launcher
# -------------------------------

# Start FastAPI backend
echo "▶️ Starting backend on http://localhost:5050 ..."
PYTHONPATH=backend uvicorn api.main:app --reload --port 5050 &

# Store backend PID
BACKEND_PID=$!

# Wait for backend to start
sleep 1

# Start Vite frontend dev server
echo "🌐 Starting frontend on http://localhost:5173 ..."
cd frontend
npm run dev

# When frontend stops (Ctrl+C), kill backend
echo "🛑 Shutting down backend (PID: $BACKEND_PID)..."
kill $BACKEND_PID
