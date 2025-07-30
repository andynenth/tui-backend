#!/usr/bin/env python
"""Test BOT_SLOT_FIX logging directly"""

import logging
import sys

# Configure logging to show all messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - [%(levelname)s] %(name)s - %(message)s',
    stream=sys.stdout,
    force=True
)

# Get logger that would be used in the dispatcher
logger = logging.getLogger('application.websocket.use_case_dispatcher')

print("Testing BOT_SLOT_FIX logging...")
print("-" * 60)

# Test the exact log messages from the dispatcher
slot_id = 2
seat_position = slot_id - 1
logger.info(f"[BOT_SLOT_FIX] Converted slot_id {slot_id} to seat_position {seat_position}")

slot_id = 5
logger.warning(f"[BOT_SLOT_FIX] Invalid slot_id received: {slot_id}")

print("-" * 60)
print("If you see the [BOT_SLOT_FIX] messages above, logging is working correctly.")
print("\nTo see these logs in the actual server:")
print("1. Make sure the server is running with LOG_LEVEL=DEBUG or INFO")
print("2. The logs should appear in the server console output")
print("3. If using uvicorn, logs go to stderr by default")