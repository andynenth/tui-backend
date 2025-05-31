#!/bin/bash

# -------------------------------
# 🚀 Liap Tui Dev Launcher
# -------------------------------

# Load environment variables
set -a
source .env
set +a

# Ensure static directory exists
mkdir -p "$STATIC_DIR"

# Copy latest index.html to static folder
cp "frontend/$INDEX_FILE" "$STATIC_DIR/$INDEX_FILE"

# Start FastAPI backend with hot reload
echo "▶️ Starting backend on http://${API_HOST}:${API_PORT} ..."
PYTHONPATH=backend uvicorn api.main:app \
  --host "$API_HOST" \
  --port "$API_PORT" \
  --reload &

# Store backend PID
BACKEND_PID=$!

# Wait a moment for backend to boot
sleep 1

# Start esbuild in watch mode and output to static folder
echo "🌐 Starting esbuild in watch mode..."
npx esbuild "$ESBUILD_ENTRY" \
  --bundle \
  --outfile="$STATIC_DIR/bundle.js" \
  --watch

# When esbuild stops, kill backend
echo "🛑 Shutting down backend (PID: $BACKEND_PID)..."
kill $BACKEND_PID
