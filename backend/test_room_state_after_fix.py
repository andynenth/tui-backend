#!/usr/bin/env python3
"""
Test that get_room_state works after the AttributeError fixes.
"""

import asyncio
import json
from websockets import connect

async def test_room_state():
    """Test room creation and state retrieval."""
    print("\n" + "="*60)
    print("Testing Room State After Fixes")
    print("="*60)
    
    # Connect to lobby
    lobby_uri = "ws://localhost:5050/ws/lobby"
    
    try:
        async with connect(lobby_uri) as websocket:
            print("\n1. Connected to lobby")
            
            # Create room
            create_msg = {
                "action": "create_room",
                "data": {
                    "player_name": "TestPlayer"
                }
            }
            
            await websocket.send(json.dumps(create_msg))
            print("\n2. Sent create_room request")
            
            # Get response
            response = await websocket.recv()
            room_created = json.loads(response)
            
            if room_created.get("event") == "room_created":
                room_id = room_created["data"]["room_id"]
                print(f"\n3. Room created: {room_id}")
                
                # Check players in creation response
                players = room_created["data"]["room_info"]["players"]
                print(f"\n4. Players in room_created response: {len(players)}")
                for p in players:
                    print(f"   - {p.get('name', 'NO_NAME')} (bot={p.get('is_bot')}, seat={p.get('seat_position')})")
                
                # Now connect to room and get state
                room_uri = f"ws://localhost:5050/ws/{room_id}"
                async with connect(room_uri) as room_ws:
                    print(f"\n5. Connected to room {room_id}")
                    
                    # Request room state
                    state_msg = {
                        "action": "get_room_state",
                        "data": {
                            "room_id": room_id
                        }
                    }
                    
                    await room_ws.send(json.dumps(state_msg))
                    print("\n6. Sent get_room_state request")
                    
                    # Get response
                    state_response = await room_ws.recv()
                    room_state = json.loads(state_response)
                    
                    if room_state.get("event") == "room_state":
                        print("\n7. ✅ SUCCESS: Received room_state response")
                        
                        # Check players
                        state_players = room_state["data"]["players"]
                        print(f"\n8. Players in room_state: {len(state_players)}")
                        for p in state_players:
                            print(f"   - {p.get('name', 'NO_NAME')} (bot={p.get('is_bot')}, seat={p.get('seat_position')})")
                        
                        # Summary
                        bot_count = sum(1 for p in state_players if p.get('is_bot'))
                        human_count = len(state_players) - bot_count
                        
                        print(f"\n9. Summary:")
                        print(f"   - Total players: {len(state_players)}")
                        print(f"   - Humans: {human_count}")
                        print(f"   - Bots: {bot_count}")
                        
                        if len(state_players) == 4 and bot_count == 3:
                            print("\n   ✅ PASS: Room has correct number of players and bots!")
                        else:
                            print("\n   ❌ FAIL: Incorrect player/bot count")
                            
                    elif room_state.get("event") == "error":
                        print(f"\n7. ❌ ERROR: {room_state['data']['message']}")
                    else:
                        print(f"\n7. ❓ Unexpected response: {room_state}")
                        
            else:
                print(f"\n3. Failed to create room: {room_created}")
                
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(test_room_state())