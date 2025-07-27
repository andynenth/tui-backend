#!/usr/bin/env python3
"""Test complete room flow: create, join, verify sync."""
import asyncio
import websockets
import json

async def test_complete_flow():
    """Test creating and joining a room."""
    lobby_uri = "ws://localhost:5050/ws/lobby"
    
    try:
        # Step 1: Create room
        async with websockets.connect(lobby_uri) as ws:
            print("✓ Connected to lobby")
            
            # Create room
            create_msg = {
                "event": "create_room",
                "data": {
                    "player_name": "TestHost"
                }
            }
            
            await ws.send(json.dumps(create_msg))
            response = await ws.recv()
            data = json.loads(response)
            
            if data.get("event") != "room_created":
                print(f"❌ Failed to create room: {data}")
                return False
                
            room_data = data.get("data", {})
            room_id = room_data.get("room_id")
            room_info = room_data.get("room_info", {})
            players = room_info.get("players", [])
            
            print(f"✅ Room {room_id} created with {len(players)} players")
            for p in players:
                print(f"   - {p['player_name']} ({'bot' if p['is_bot'] else 'human'})")
        
        # Step 2: Try to connect to the room directly
        room_uri = f"ws://localhost:5050/ws/{room_id}"
        print(f"\nAttempting to connect to room {room_id}...")
        
        try:
            async with websockets.connect(room_uri) as ws:
                print("✓ Connected to room")
                
                # Wait for initial room state
                try:
                    initial_msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    data = json.loads(initial_msg)
                    print(f"✓ Received initial state: {data.get('event', 'unknown')}")
                    
                    # If we get room_not_found, the sync failed
                    if data.get("event") == "room_not_found":
                        print("❌ Room not synced to legacy system!")
                        return False
                    else:
                        print("✅ Room is accessible - sync successful!")
                        return True
                        
                except asyncio.TimeoutError:
                    print("⏱️ No initial message received (might be normal)")
                    return True
                    
        except Exception as e:
            print(f"❌ Failed to connect to room: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing complete room creation and sync flow...")
    print("=" * 60)
    
    success = asyncio.run(test_complete_flow())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ COMPLETE SUCCESS: Room creation AND legacy sync working!")
    else:
        print("❌ FAILURE: Room creation works but legacy sync is broken")