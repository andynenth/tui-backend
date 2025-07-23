#!/usr/bin/env python3
"""
Direct test of AsyncRoomManager to diagnose the issue
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared_instances import shared_room_manager


async def test_room_manager():
    """Test AsyncRoomManager directly"""
    print("🧪 Testing AsyncRoomManager directly...")
    
    # Create a room
    room_id = await shared_room_manager.create_room("TestHost")
    print(f"✅ Created room: {room_id}")
    
    # Try to get the room
    room = await shared_room_manager.get_room(room_id)
    if room:
        print(f"✅ Retrieved room: {room_id}")
        print(f"   Host: {room.host_name}")
        print(f"   Players: {room.players}")
    else:
        print(f"❌ Could not retrieve room {room_id}")
    
    # List all rooms
    rooms = await shared_room_manager.list_rooms()
    print(f"\n📋 Total rooms: {len(rooms)}")
    for room_data in rooms:
        print(f"   - {room_data}")
    
    # Check the internal rooms dict
    print(f"\n🔍 Direct check of rooms dict:")
    print(f"   Keys: {list(shared_room_manager.rooms.keys())}")
    print(f"   Room count: {len(shared_room_manager.rooms)}")


if __name__ == "__main__":
    asyncio.run(test_room_manager())