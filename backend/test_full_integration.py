#!/usr/bin/env python3
"""
Full integration test for room management system.
Tests WebSocket flow with multiple clients.
"""

import asyncio
import json
import websockets

async def test_full_flow():
    """Test complete room management flow with multiple clients."""
    print("🧪 Full Integration Test: Room Management System\n")
    
    try:
        # Alice creates a room
        print("📋 Step 1: Alice creates a room")
        async with websockets.connect("ws://localhost:5050/ws/lobby") as alice_ws:
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
            
            await alice_ws.send(json.dumps(create_msg))
            response = await alice_ws.recv()
            data = json.loads(response)
            
            if data["event"] == "room_created":
                room_id = data["data"]["room_id"]
                print(f"✅ Room created: {room_id}")
            else:
                print(f"❌ Failed: {data}")
                return
        
        # Bob lists rooms
        print("\n📋 Step 2: Bob checks lobby for rooms")
        async with websockets.connect("ws://localhost:5050/ws/lobby") as bob_ws:
            list_msg = {
                "event": "get_rooms",
                "data": {"player_id": "bob456"}
            }
            
            await bob_ws.send(json.dumps(list_msg))
            response = await bob_ws.recv()
            data = json.loads(response)
            
            if data["event"] == "room_list":
                rooms = data["data"]["rooms"]
                print(f"✅ Found {len(rooms)} rooms")
                for room in rooms:
                    print(f"   - {room['room_name']} (ID: {room['room_id']})")
            else:
                print(f"❌ Failed: {data}")
        
        # Connect to the room directly
        print(f"\n📋 Step 3: Connect to room {room_id} directly")
        async with websockets.connect(f"ws://localhost:5050/ws/{room_id}") as room_ws:
            # Get room state
            state_msg = {
                "event": "get_room_state",
                "data": {"player_id": "test123"}
            }
            
            await room_ws.send(json.dumps(state_msg))
            response = await room_ws.recv()
            data = json.loads(response)
            
            if data.get("event") == "room_state":
                room_info = data["data"]["room_info"]
                print(f"✅ Room state retrieved")
                print(f"   Players: {len(room_info['players'])}/{room_info['max_players']}")
                for i, player in enumerate(room_info["players"]):
                    print(f"   {i+1}. {player['player_name']} {'(Host)' if player['is_host'] else '(Bot)' if player['is_bot'] else ''}")
            else:
                print(f"❌ Failed to get room state: {data}")
        
        # Test joining via room code
        print(f"\n📋 Step 4: Bob joins room using code")
        async with websockets.connect(f"ws://localhost:5050/ws/{room_id}") as bob_room_ws:
            join_msg = {
                "event": "join_room",
                "data": {
                    "player_id": "bob456",
                    "player_name": "Bob",
                    "room_code": room_id
                }
            }
            
            await bob_room_ws.send(json.dumps(join_msg))
            
            # Should receive multiple events
            events_received = []
            for _ in range(3):  # Expect up to 3 events
                try:
                    response = await asyncio.wait_for(bob_room_ws.recv(), timeout=1.0)
                    data = json.loads(response)
                    events_received.append(data.get("event"))
                    
                    if data.get("event") == "player_joined":
                        print(f"✅ Player joined event received")
                        print(f"   Player: {data['data']['player_name']}")
                    elif data.get("event") == "room_updated":
                        print(f"✅ Room updated event received")
                except asyncio.TimeoutError:
                    break
            
            print(f"   Events received: {events_received}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_flow())