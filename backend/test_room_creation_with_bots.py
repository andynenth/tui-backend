#!/usr/bin/env python3
"""
Test script to verify room creation with automatic bot assignment.
Tests the complete flow through clean architecture adapters.
"""

import asyncio
import json
import logging
from unittest.mock import MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_room_creation():
    """Test room creation through clean architecture with bot assignment."""
    # Import after event loop is created
    from api.adapters.room_adapters import _handle_create_room
    from shared_instances import shared_room_manager
    from infrastructure.dependencies import get_unit_of_work
    
    print("\n" + "="*60)
    print("Testing Room Creation with Automatic Bot Assignment")
    print("="*60)
    
    # Create mock websocket
    mock_websocket = MagicMock()
    mock_websocket.send_json = MagicMock()
    
    # Create room creation message
    message = {
        "action": "create_room",
        "data": {
            "player_name": "TestPlayer",
            "room_name": "Test Room",
            "max_players": 4
        }
    }
    
    print(f"\n1. Creating room with message: {json.dumps(message, indent=2)}")
    
    # Execute room creation
    response = await _handle_create_room(mock_websocket, message, None, None)
    
    print(f"\n2. Adapter response: {json.dumps(response, indent=2)}")
    
    if response.get("event") == "room_created":
        room_id = response["data"]["room_id"]
        print(f"\n3. Room created successfully with ID: {room_id}")
        
        # Check clean architecture repository
        print("\n4. Checking clean architecture repository...")
        uow = get_unit_of_work()
        async with uow:
            clean_room = await uow.rooms.get(room_id)
            if clean_room:
                print(f"   ✓ Room found in clean architecture")
                print(f"   - Host: {clean_room.host_name}")
                print(f"   - Slots filled: {len([s for s in clean_room.slots if s])}/{clean_room.max_slots}")
                print(f"   - Players:")
                for i, slot in enumerate(clean_room.slots):
                    if slot:
                        print(f"     Slot {i}: {slot.player_name} (Bot: {slot.is_bot})")
            else:
                print(f"   ✗ Room NOT found in clean architecture!")
        
        # Check legacy room manager (bridge sync)
        print("\n5. Checking legacy room manager (bridge sync)...")
        legacy_room = shared_room_manager.rooms.get(room_id)
        if legacy_room:
            print(f"   ✓ Room found in legacy manager (bridge worked!)")
            print(f"   - Host: {legacy_room.host_name}")
            print(f"   - Players: {len(legacy_room.players)}")
            for player in legacy_room.players:
                print(f"     - {player['name']} (Bot: {player.get('is_bot', False)})")
        else:
            print(f"   ✗ Room NOT found in legacy manager (bridge failed)")
        
        # Check bot assignment
        print("\n6. Bot Assignment Analysis:")
        if "room_info" in response["data"]:
            players = response["data"]["room_info"]["players"]
            bots = [p for p in players if p["is_bot"]]
            humans = [p for p in players if not p["is_bot"]]
            print(f"   - Total players: {len(players)}")
            print(f"   - Human players: {len(humans)}")
            print(f"   - Bot players: {len(bots)}")
            
            if len(bots) == 3:  # Should have 3 bots for a 4-player room with 1 human
                print(f"   ✓ Correct number of bots assigned!")
            else:
                print(f"   ✗ Expected 3 bots, but found {len(bots)}")
    else:
        print(f"\n✗ Room creation failed: {response}")
    
    print("\n" + "="*60)
    print("Test Complete")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_room_creation())