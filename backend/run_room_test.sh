#!/bin/bash

# Start the server in the background
echo "Starting server..."
cd /Users/nrw/python/tui-project/liap-tui
source venv/bin/activate
cd backend
python -m api.main &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 5

# Run the test
echo "Running room events integration test..."
python test_room_events_integration.py

# Kill the server
echo "Stopping server..."
kill $SERVER_PID

echo "Test complete!"