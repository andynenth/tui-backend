#!/bin/bash
# Script to start the server with proper logging to see BOT_SLOT_FIX messages

echo "Starting server with debug logging enabled..."
echo "BOT_SLOT_FIX messages will appear when:"
echo "1. A bot is added using slot_id (frontend format)"
echo "2. An invalid slot_id is provided"
echo ""
echo "To test, use the WebSocket to send:"
echo '{"event": "add_bot", "data": {"slot_id": 2, "difficulty": "medium"}}'
echo ""
echo "Starting server..."
echo "=" * 60

# Start server with debug logging
LOG_LEVEL=DEBUG python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 5050 --reload 2>&1 | grep -E "(BOT_SLOT_FIX|Starting|Uvicorn running|Application startup|ERROR|WARNING)" --line-buffered