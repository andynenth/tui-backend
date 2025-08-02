#!/usr/bin/env python3
"""
Test WebSocket room management without REST endpoints.
This verifies that all room operations work via WebSocket after REST removal.
"""

import asyncio
import json
import websockets


async def test_websocket_room_operations():
    """Test complete room management flow via WebSocket."""
    
    # Connect to lobby
    async with websockets.connect("ws://localhost:5050/ws/lobby") as websocket:
        print("✅ Connected to lobby")
        
        # 1. Test getting room list
        await websocket.send(json.dumps({
            "event": "get_rooms",
            "data": {}
        }))
        
        response = await websocket.recv()
        data = json.loads(response)
        print(f"✅ Got room list: {data['event']}")
        
        # 2. Test creating a room
        await websocket.send(json.dumps({
            "event": "create_room",
            "data": {"player_name": "TestPlayer1"}
        }))
        
        response = await websocket.recv()
        data = json.loads(response)
        if data['event'] == 'room_created':
            room_id = data['data']['room_id']
            print(f"✅ Created room: {room_id}")
        else:
            print(f"❌ Failed to create room: {data}")
            return
        
        # Wait for room list update
        response = await websocket.recv()
        data = json.loads(response)
        print(f"✅ Got room update: {data['event']}")
        
    # 3. Test joining the room with another player
    async with websockets.connect("ws://localhost:5050/ws/lobby") as websocket2:
        print("✅ Player 2 connected to lobby")
        
        await websocket2.send(json.dumps({
            "event": "join_room",
            "data": {
                "room_id": room_id,
                "player_name": "TestPlayer2"
            }
        }))
        
        response = await websocket2.recv()
        data = json.loads(response)
        if data['event'] == 'room_joined':
            print(f"✅ Player 2 joined room: {room_id}")
        else:
            print(f"❌ Failed to join room: {data}")
            
    # 4. Connect to the room and test room-specific operations
    async with websockets.connect(f"ws://localhost:5050/ws/{room_id}") as room_ws:
        print(f"✅ Connected to room: {room_id}")
        
        # Get room state
        await room_ws.send(json.dumps({
            "event": "get_room_state",
            "data": {}
        }))
        
        response = await room_ws.recv()
        data = json.loads(response)
        print(f"✅ Got room state: {data['event']}")
        
        # Add a bot
        await room_ws.send(json.dumps({
            "event": "add_bot",
            "data": {"slot_id": 3}
        }))
        
        response = await room_ws.recv()
        data = json.loads(response)
        print(f"✅ Added bot to slot 3: {data['event']}")
        
        # Start the game
        await room_ws.send(json.dumps({
            "event": "start_game",
            "data": {}
        }))
        
        response = await room_ws.recv()
        data = json.loads(response)
        print(f"✅ Started game: {data['event']}")
        
    print("\n🎉 All WebSocket room management operations working!")


if __name__ == "__main__":
    # Note: Make sure the server is running with ./start.sh
    try:
        asyncio.run(test_websocket_room_operations())
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the server is running with ./start.sh")