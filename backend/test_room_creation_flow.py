#!/usr/bin/env python3
"""Test room creation flow after fixing all import errors."""
import asyncio
import websockets
import json

async def test_room_creation():
    """Test creating a room via WebSocket."""
    uri = "ws://localhost:5050/ws/lobby"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to lobby")
            
            # Create room
            create_msg = {
                "event": "create_room",
                "data": {
                    "player_name": "TestUser"
                }
            }
            
            await websocket.send(json.dumps(create_msg))
            print("✓ Sent create_room message")
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✓ Received response: {data}")
            
            if data.get("event") == "room_created":
                room_data = data.get("data", {})
                room_id = room_data.get("room_id")
                print(f"✅ Room created successfully: {room_id}")
                
                # Check if room has bots
                room_info = room_data.get("room_info", {})
                players = room_info.get("players", [])
                
                if players:
                    bot_count = sum(1 for p in players if p.get("is_bot"))
                    human_count = sum(1 for p in players if not p.get("is_bot"))
                    print(f"✅ Room has {human_count} human(s) and {bot_count} bot(s)")
                    print(f"✅ Players: {', '.join(p['player_name'] for p in players)}")
                    return bot_count == 3  # Should have 3 bots
                else:
                    print("❌ No player data in response")
                    return False
            else:
                print(f"❌ Unexpected response event: {data.get('event')}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing room creation flow...")
    print("-" * 50)
    
    # Check if server is running
    import requests
    try:
        resp = requests.get("http://localhost:5050/api/health", timeout=1)
        if resp.status_code == 200:
            print("✓ Server is running")
        else:
            print("❌ Server returned non-200 status")
            exit(1)
    except:
        print("❌ Server is not running on port 5050")
        print("Please start the server with: ./start.sh")
        exit(1)
    
    # Run the test
    success = asyncio.run(test_room_creation())
    
    if success:
        print("\n✅ Room creation WITH BOT ASSIGNMENT is working!")
    else:
        print("\n❌ Room creation still has issues")