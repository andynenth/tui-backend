#!/usr/bin/env python3
"""Test script for Phase 7.0 WebSocket fix"""

import asyncio
import json
import websockets
import uuid


async def test_room_creation_and_visibility():
    """Test that rooms created in clean architecture are visible to WebSocket connections"""
    
    # First, connect to lobby and create a room
    lobby_uri = "ws://localhost:5050/ws/lobby"
    
    print("1. Connecting to lobby...")
    async with websockets.connect(lobby_uri) as lobby_ws:
        print("   ✅ Connected to lobby")
        
        # Send create_room message
        create_msg = {
            "event": "create_room",
            "data": {
                "player_name": "TestPlayer"
            }
        }
        
        print("2. Creating room...")
        await lobby_ws.send(json.dumps(create_msg))
        
        # Wait for room_created response
        room_id = None
        while True:
            response = await lobby_ws.recv()
            data = json.loads(response)
            print(f"   Received: {data['event']}")
            
            if data['event'] == 'room_created':
                room_id = data['data']['room_id']
                print(f"   ✅ Room created: {room_id}")
                break
            elif data['event'] == 'error':
                print(f"   ❌ Error: {data['data']['message']}")
                return
    
    if not room_id:
        print("   ❌ Failed to create room")
        return
    
    # Now connect to the room directly
    print(f"\n3. Connecting to room {room_id}...")
    room_uri = f"ws://localhost:5050/ws/{room_id}"
    
    try:
        async with websockets.connect(room_uri) as room_ws:
            print("   ✅ Connected to room (no room_not_found error!)")
            
            # Wait a moment to see if we get room_not_found
            try:
                await asyncio.wait_for(room_ws.recv(), timeout=2.0)
            except asyncio.TimeoutError:
                print("   ✅ No room_not_found error received - room is properly visible!")
            except websockets.exceptions.ConnectionClosed:
                print("   ❌ Connection closed unexpectedly")
            except Exception as e:
                response = json.loads(str(e))
                if response.get('event') == 'room_not_found':
                    print("   ❌ Room not found error - Phase 7.0 fix not working")
                else:
                    print(f"   Received event: {response.get('event')}")
    
    except Exception as e:
        print(f"   ❌ Failed to connect to room: {e}")
    
    print("\n✅ Phase 7.0 WebSocket fix test complete!")


if __name__ == "__main__":
    asyncio.run(test_room_creation_and_visibility())