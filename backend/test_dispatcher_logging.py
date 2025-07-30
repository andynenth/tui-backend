#!/usr/bin/env python
"""Direct test of the dispatcher to see BOT_SLOT_FIX logging"""

import asyncio
import logging
import sys
from unittest.mock import Mock, AsyncMock

# Set up logging to capture all messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - [%(levelname)s] %(message)s',
    stream=sys.stdout
)

# Import the dispatcher
sys.path.insert(0, '/Users/nrw/python/tui-project/liap-tui/backend')
from application.websocket.use_case_dispatcher import UseCaseDispatcher, DispatchContext

async def test_bot_slot_logging():
    """Test the dispatcher directly to see BOT_SLOT_FIX logging"""
    
    # Need to ensure event loop is set up properly
    try:
        # Create dispatcher
        dispatcher = UseCaseDispatcher()
    except Exception as e:
        print(f"Error creating dispatcher: {e}")
        # Try manual initialization
        from infrastructure.dependencies import init_dependencies
        init_dependencies()
        dispatcher = UseCaseDispatcher()
    
    # Create mock context
    context = DispatchContext(
        websocket=Mock(),
        room_id="TEST123",
        room_state={
            "room_id": "TEST123",
            "players": [
                {"name": "Host", "player_id": "TEST123_p0", "seat_position": 0, "is_bot": False}
            ]
        },
        player_id="TEST123_p0",
        player_name="Host"
    )
    
    print("\n=== TEST 1: add_bot with slot_id (frontend format) ===")
    # Test with slot_id (should trigger BOT_SLOT_FIX logging)
    data = {
        "slot_id": 2,  # Frontend uses 1-based indexing
        "difficulty": "medium",
        "bot_name": "TestBot_SlotID"
    }
    
    try:
        result = await dispatcher._handle_add_bot(data, context)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== TEST 2: add_bot with invalid slot_id ===")
    # Test with invalid slot_id
    data = {
        "slot_id": 5,  # Invalid - only 1-4 are valid
        "difficulty": "medium"
    }
    
    try:
        result = await dispatcher._handle_add_bot(data, context)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== TEST 3: add_bot with seat_position (backend format) ===")
    # Test with seat_position directly
    data = {
        "seat_position": 2,  # Backend uses 0-based indexing
        "difficulty": "hard",
        "bot_name": "TestBot_Seat"
    }
    
    try:
        result = await dispatcher._handle_add_bot(data, context)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Starting direct dispatcher test...")
    print("Looking for [BOT_SLOT_FIX] log messages...")
    print("-" * 60)
    asyncio.run(test_bot_slot_logging())
    print("-" * 60)
    print("Test complete! Check output above for [BOT_SLOT_FIX] messages")