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

# 🏗️ Clean Architecture Feature Flags (Default: Enabled)
# Phase 6 migration is complete - clean architecture is now the default
export FF_USE_CLEAN_ARCHITECTURE=true
export FF_USE_DOMAIN_EVENTS=true
export FF_USE_APPLICATION_LAYER=true
export FF_USE_NEW_REPOSITORIES=true
export FF_USE_CONNECTION_ADAPTERS=true
export FF_USE_ROOM_ADAPTERS=true
export FF_USE_GAME_ADAPTERS=true
export FF_USE_LOBBY_ADAPTERS=true

# 🚦 Adapter Traffic Routing (Enable clean architecture traffic routing)
export ADAPTER_ENABLED=true
export ADAPTER_ROLLOUT_PERCENTAGE=100

echo "✅ Clean Architecture activated (8/8 feature flags enabled)"
echo "🚦 Adapter routing enabled (100% traffic to clean architecture)"

# Ensure static directory exists
mkdir -p "$STATIC_DIR"

# Copy latest index.html to static folder
cp "frontend/$INDEX_FILE" "$STATIC_DIR/"

# Start FastAPI backend with hot reload
echo "▶️ Starting backend on http://${API_HOST}:${API_PORT} ..."
PYTHONPATH=backend python -m uvicorn backend.api.main:app \
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
