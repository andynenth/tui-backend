#!/bin/bash

# -------------------------------
# 🚀 Liap Tui Dev Launcher (Local Dev)
# -------------------------------

# Go to script root (project root)
cd "$(dirname "$0")"

# Load environment variables from .env at root
set -a
source .env
set +a

# Ensure static directory exists
mkdir -p "$STATIC_DIR"

# Copy latest index.html to static folder
cp "frontend/$INDEX_FILE" "$STATIC_DIR/$INDEX_FILE"

# Start FastAPI backend with hot reload
echo "▶️ Starting backend on http://${API_HOST}:${API_PORT} ..."
PYTHONPATH=backend uvicorn backend.api.main:app \
  --host "$API_HOST" \
  --port "$API_PORT" \
  --reload &

# Store backend PID
BACKEND_PID=$!

# Wait for backend to boot
sleep 1

# Start esbuild in watch mode
echo "🌐 Starting esbuild in watch mode..."

cd frontend
npm run dev

# When esbuild exits, stop backend too
echo "🛑 Shutting down backend (PID: $BACKEND_PID)..."
kill $BACKEND_PID
