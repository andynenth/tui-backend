#!/bin/bash
# Monitor debug logs and save recent output for Claude

# Create a rolling buffer of recent logs
tail -f debug_websocket.log | while IFS= read -r line; do
    echo "$line"
    # Also append to a recent log file (keep last 1000 lines)
    echo "$line" >> debug_websocket_recent.log
    tail -n 1000 debug_websocket_recent.log > debug_websocket_recent.log.tmp
    mv debug_websocket_recent.log.tmp debug_websocket_recent.log
done