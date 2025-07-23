#!/usr/bin/env python3
"""
Test script to verify Async architecture integration
"""

import asyncio
import websockets
import json
from datetime import datetime

BASE_URL = "ws://localhost:5050"


async def test_async_room_operations():
    """Test that async room operations work correctly"""
    
    print("🧪 Testing Async Room Operations...")
    print("-" * 50)
    
    # Test room creation via WebSocket
    print("\n1️⃣ Testing async room creation via WebSocket...")
    
    try:
        # Connect to lobby WebSocket
        async with websockets.connect(f"{BASE_URL}/ws/lobby") as websocket:
            # Register player
            await websocket.send(json.dumps({
                "event": "register",
                "data": {"player_name": "AsyncTestPlayer"}
            }))
            
            # Wait for registration response
            response = await websocket.recv()
            print(f"Registration response: {response}")
            
            # Create room
            await websocket.send(json.dumps({
                "event": "create_room",
                "data": {}
            }))
            
            # Wait for room creation response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Room creation response: {json.dumps(data, indent=2)}")
            
            if data.get("event") == "room_created":
                room_id = data["data"]["room_id"]
                print(f"✅ Async room creation successful! Room ID: {room_id}")
                
                # Get room list to verify
                await websocket.send(json.dumps({
                    "event": "get_rooms",
                    "data": {}
                }))
                
                response = await websocket.recv()
                rooms_data = json.loads(response)
                print(f"\n2️⃣ Room list (async list_rooms): {json.dumps(rooms_data, indent=2)[:300]}...")
                
                if rooms_data.get("event") == "room_list":
                    print(f"✅ Async list_rooms successful! Found {len(rooms_data['data']['rooms'])} rooms")
                
                return room_id
            else:
                print(f"❌ Unexpected response: {data}")
                return None
                
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return None


async def test_async_room_join(room_id):
    """Test joining a room with async operations"""
    
    print(f"\n3️⃣ Testing async room join for room {room_id}...")
    
    try:
        # Connect with a different player
        async with websockets.connect(f"{BASE_URL}/ws/lobby") as websocket:
            # Register player
            await websocket.send(json.dumps({
                "event": "register",
                "data": {"player_name": "AsyncPlayer2"}
            }))
            
            response = await websocket.recv()
            print(f"Player 2 registration: {response}")
            
            # Join room
            await websocket.send(json.dumps({
                "event": "join_room",
                "data": {"room_id": room_id}
            }))
            
            # Wait for join response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Join room response: {json.dumps(data, indent=2)}")
            
            if data.get("event") == "room_joined":
                print(f"✅ Async room join successful!")
            else:
                print(f"❌ Join failed: {data}")
                
    except Exception as e:
        print(f"❌ Join error: {e}")


async def main():
    """Run the async integration tests"""
    print(f"🚀 Starting Async Integration Test at {datetime.now()}")
    
    # Test room creation
    room_id = await test_async_room_operations()
    
    if room_id:
        # Test room joining
        await test_async_room_join(room_id)
    
    print("\n✅ Async integration test completed!")


if __name__ == "__main__":
    asyncio.run(main())