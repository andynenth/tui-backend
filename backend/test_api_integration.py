#!/usr/bin/env python3
"""
Test room management through WebSocket API.
"""

import asyncio
import json
import websockets

async def test_room_flow():
    """Test room creation and listing through WebSocket."""
    print("🧪 Testing Room Management via WebSocket API\n")
    
    # Connect to lobby
    uri = "ws://localhost:5050/ws/lobby"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to lobby WebSocket")
            
            # Test 1: Create room
            print("\n📋 Test 1: Create Room")
            create_msg = {
                "event": "create_room",
                "data": {
                    "player_id": "alice123",
                    "player_name": "Alice",
                    "room_settings": {
                        "max_players": 4,
                        "win_condition_type": "score",
                        "win_condition_value": 50
                    }
                }
            }
            
            await websocket.send(json.dumps(create_msg))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get("event") == "room_created":
                print("✅ Room created successfully!")
                room_info = response_data["data"]
                print(f"   Room ID: {room_info['room_id']}")
                print(f"   Join Code: {room_info.get('join_code', room_info['room_id'])}")
                room_id = room_info['room_id']
            else:
                print(f"❌ Failed to create room: {response_data}")
                return
            
            # Test 2: List rooms
            print("\n📋 Test 2: List Rooms")
            list_msg = {
                "event": "get_rooms",
                "data": {
                    "player_id": "bob456"
                }
            }
            
            await websocket.send(json.dumps(list_msg))
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get("event") == "room_list":
                print("✅ Room list retrieved successfully!")
                rooms = response_data["data"]["rooms"]
                print(f"   Total rooms: {len(rooms)}")
                for room in rooms:
                    print(f"   - {room['room_name']} ({room['player_count']}/{room['max_players']} players)")
                    print(f"     Room ID: {room['room_id']}")
                    print(f"     Host: {room['host_name']}")
            else:
                print(f"❌ Failed to list rooms: {response_data}")
            
            print("\n✅ Test completed!")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Make sure the server is running with ./start.sh")

if __name__ == "__main__":
    asyncio.run(test_room_flow())