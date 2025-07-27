#!/usr/bin/env python3
"""
Test script to verify that rooms display players correctly after the property name fix.
"""

import asyncio
import json
from websockets import connect
import sys

async def test_room_display():
    """Test that room creation and get_room_state return correct player data."""
    uri = "ws://localhost:5050/ws/lobby"
    
    print("\n" + "="*60)
    print("Testing Room Display Fix")
    print("="*60)
    
    async with connect(uri) as websocket:
        print("\n1. Connected to lobby WebSocket")
        
        # Create a room
        create_msg = {
            "action": "create_room",
            "data": {
                "player_name": "TestPlayer"
            }
        }
        
        print(f"\n2. Sending create_room: {json.dumps(create_msg, indent=2)}")
        await websocket.send(json.dumps(create_msg))
        
        # Wait for room_created response
        response = await websocket.recv()
        room_created = json.loads(response)
        print(f"\n3. Received response: {json.dumps(room_created, indent=2)}")
        
        if room_created.get("event") == "room_created":
            room_id = room_created["data"]["room_id"]
            players = room_created["data"]["room_info"]["players"]
            
            print(f"\n4. Room created with ID: {room_id}")
            print(f"   Players in room_created response: {len(players)}")
            for p in players:
                # Check if using "name" or "player_name"
                player_name = p.get("name") or p.get("player_name", "MISSING")
                print(f"   - {player_name} (bot={p.get('is_bot')}, seat={p.get('seat_position')})")
            
            # Now connect to the room and get room state
            room_uri = f"ws://localhost:5050/ws/{room_id}"
            async with connect(room_uri) as room_ws:
                print(f"\n5. Connected to room {room_id} WebSocket")
                
                # Send get_room_state
                get_state_msg = {
                    "action": "get_room_state",
                    "data": {
                        "room_id": room_id
                    }
                }
                
                print(f"\n6. Sending get_room_state: {json.dumps(get_state_msg, indent=2)}")
                await room_ws.send(json.dumps(get_state_msg))
                
                # Wait for room_state response
                state_response = await room_ws.recv()
                room_state = json.loads(state_response)
                print(f"\n7. Received room_state: {json.dumps(room_state, indent=2)}")
                
                if room_state.get("event") == "room_state":
                    state_players = room_state["data"]["players"]
                    print(f"\n8. Players in room_state response: {len(state_players)}")
                    for p in state_players:
                        # Check if using "name" or "player_name"
                        player_name = p.get("name") or p.get("player_name", "MISSING")
                        print(f"   - {player_name} (bot={p.get('is_bot')}, seat={p.get('seat_position')})")
                    
                    # Verify bots are present
                    bot_count = sum(1 for p in state_players if p.get("is_bot"))
                    human_count = sum(1 for p in state_players if not p.get("is_bot"))
                    
                    print(f"\n9. Summary:")
                    print(f"   - Total players: {len(state_players)}")
                    print(f"   - Human players: {human_count}")
                    print(f"   - Bot players: {bot_count}")
                    
                    # Check if frontend will show "Waiting..." or actual names
                    missing_names = [p for p in state_players if not p.get("name") and not p.get("player_name")]
                    if missing_names:
                        print(f"\n   ❌ ERROR: {len(missing_names)} players missing 'name' property!")
                        print("      Frontend will show 'Waiting...' for these players")
                    elif all(p.get("name") for p in state_players):
                        print(f"\n   ✅ SUCCESS: All players have 'name' property")
                        print("      Frontend should display all players correctly")
                    else:
                        print(f"\n   ⚠️  WARNING: Using inconsistent property names")
    
    print("\n" + "="*60)
    print("Test Complete")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_room_display())