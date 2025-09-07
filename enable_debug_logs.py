#!/usr/bin/env python3
"""
Enable comprehensive debug logging for WebSocket reconnection debugging
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Configure logging before importing anything else
import logging

# Create debug log file at project root for Claude access
DEBUG_LOG_FILE = os.path.join(os.path.dirname(__file__), 'debug_websocket.log')

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DEBUG_LOG_FILE, mode='w'),  # Overwrite on each run
        logging.StreamHandler(sys.stdout)  # Also print to console
    ]
)

# Set specific loggers to DEBUG
loggers_to_debug = [
    'backend.api.routes.ws',
    'backend.socket_manager',
    'backend.engine.state_machine.game_state_machine',
    'backend.engine.state_machine.base_state',
    'backend.api.websocket.connection_manager',
    'backend.api.websocket.message_queue',
    'uvicorn.access',
    'uvicorn.error'
]

for logger_name in loggers_to_debug:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

print(f"✅ Debug logging enabled to: {DEBUG_LOG_FILE}")
print("🔍 Monitored loggers:")
for name in loggers_to_debug:
    print(f"   - {name}")

# Now import and run the backend
if __name__ == "__main__":
    import uvicorn
    from backend.api.main import app

    print("\n🚀 Starting backend with debug logging...")
    print(f"📄 Logs will be written to: {DEBUG_LOG_FILE}")
    print("💡 Run 'tail -f debug_websocket.log' in another terminal to monitor\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        access_log=True
    )