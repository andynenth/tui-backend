#!/usr/bin/env python3
"""
Test WebSocket room creation and AsyncRoomManager state
"""

import asyncio
import websockets
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared_instances import shared_room_manager


async def test_room_creation():
    """Test room creation via WebSocket and check AsyncRoomManager"""
    
    print("🧪 Testing WebSocket Room Creation and AsyncRoomManager State...")
    print("-" * 50)
    
    # Connect to lobby
    async with websockets.connect("ws://127.0.0.1:5050/ws/lobby") as websocket:
        # Send client ready
        await websocket.send(json.dumps({
            "event": "client_ready",
            "data": {"player_name": "TestPlayer"}
        }))
        
        # Wait for response
        response = await websocket.recv()
        print(f"Client ready response: {json.loads(response).get('event')}")
        
        # Create room
        await websocket.send(json.dumps({
            "event": "create_room",
            "data": {"player_name": "TestPlayer"}
        }))
        
        # Wait for room creation
        response = await websocket.recv()
        data = json.loads(response)
        
        if data.get("event") == "room_created":
            room_id = data["data"]["room_id"]
            print(f"✅ Room created via WebSocket: {room_id}")
            
            # Check AsyncRoomManager directly
            print(f"\n🔍 Checking AsyncRoomManager state:")
            print(f"   Room manager instance: {shared_room_manager}")
            print(f"   Rooms in manager: {list(shared_room_manager.rooms.keys())}")
            
            # Try to get the room
            room = await shared_room_manager.get_room(room_id)
            if room:
                print(f"✅ Room {room_id} found in AsyncRoomManager!")
                print(f"   Host: {room.host_name}")
                print(f"   Players: {[p.name if p else 'Empty' for p in room.players]}")
            else:
                print(f"❌ Room {room_id} NOT found in AsyncRoomManager")
                print(f"   Current rooms: {list(shared_room_manager.rooms.keys())}")
            
            return room_id
        else:
            print(f"❌ Unexpected response: {data}")
            return None


async def test_direct_connection(room_id):
    """Test connecting directly to the room"""
    print(f"\n🔗 Testing direct connection to room {room_id}...")
    
    try:
        async with websockets.connect(f"ws://127.0.0.1:5050/ws/{room_id}") as websocket:
            print(f"✅ Connected to room {room_id}")
            
            # Send client ready
            await websocket.send(json.dumps({
                "event": "client_ready",
                "data": {"player_name": "TestPlayer2"}
            }))
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Response: {data.get('event')}")
            
            if data.get("event") == "room_not_found":
                print(f"❌ Room not found: {data}")
            else:
                print(f"✅ Successfully connected to room!")
                
    except Exception as e:
        print(f"❌ Connection error: {e}")


async def main():
    """Run the tests"""
    # Test room creation
    room_id = await test_room_creation()
    
    if room_id:
        # Small delay
        await asyncio.sleep(0.5)
        
        # Test direct connection
        await test_direct_connection(room_id)
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(main())