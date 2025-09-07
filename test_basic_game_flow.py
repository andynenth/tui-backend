#!/usr/bin/env python3
"""Test basic game flow to ensure implementation doesn't break game"""
import asyncio
import json
import random
import string
import time
from websockets import connect

async def test_basic_game_flow():
    """Test creating a room, joining with bots, and playing a game"""
    room_id = None
    player_name = "TestPlayer"
    ws_url = "ws://localhost:5050/ws/lobby"

    print("🧪 Testing basic game flow...")
    print("📍 Step 1: Creating room...")

    # Create a room
    try:
        async with connect(ws_url) as websocket:
            await websocket.send(json.dumps({
                "event": "create_room",
                "data": {
                    "player_name": player_name,
                    "max_players": 4
                }
            }))

            # Wait for room created response
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("event") == "room_created":
                room_id = data.get("data", {}).get("room_id")
                print(f"✅ Room created: {room_id}")
            else:
                print(f"❌ Unexpected response: {data}")
                return
    except Exception as e:
        print(f"❌ Error creating room: {e}")
        return

    # Connect to the room
    room_ws_url = f"ws://localhost:5050/ws/{room_id}"
    print(f"\n📍 Step 2: Connecting to room {room_id}...")

    try:
        async with connect(room_ws_url) as websocket:
            # Send client ready
            await websocket.send(json.dumps({
                "event": "client_ready",
                "data": {
                    "room_id": room_id,
                    "player_name": player_name,
                    "is_reconnection": False
                }
            }))

            print("✅ Connected to room")

            # Wait for initial state
            await asyncio.sleep(1)

            # Add bots
            print("\n📍 Step 3: Adding bots...")
            for i in range(3):
                await websocket.send(json.dumps({
                    "event": "join_room",
                    "data": {
                        "room_id": room_id,
                        "player_name": f"Bot{i+1}",
                        "is_bot": True
                    }
                }))
                await asyncio.sleep(0.5)

            print("✅ Added 3 bots")

            # Start the game
            print("\n📍 Step 4: Starting game...")
            await websocket.send(json.dumps({
                "event": "start_game",
                "data": {}
            }))

            # Process messages for a few seconds
            print("\n📍 Step 5: Processing game messages...")
            start_time = time.time()
            message_count = 0
            phase_changes = 0
            errors = 0

            while time.time() - start_time < 5:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    data = json.loads(response)
                    message_count += 1

                    if data.get("event") == "phase_change":
                        phase_changes += 1
                        phase = data.get('data', {}).get('phase', 'unknown')
                        print(f"  Phase change: {phase} (msg #{message_count})")
                    elif data.get("event") == "error":
                        errors += 1
                        error_msg = data.get('data', {}).get('message', 'Unknown error')
                        print(f"  ❌ Error: {error_msg}")
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"  ❌ Message error: {e}")
                    break

            print(f"\n✅ Game test summary:")
            print(f"  - Total messages: {message_count}")
            print(f"  - Phase changes: {phase_changes}")
            print(f"  - Errors: {errors}")
            print(f"  - Test result: {'PASSED' if errors == 0 and phase_changes > 0 else 'FAILED'}")

    except Exception as e:
        print(f"❌ Game test error: {e}")

    # Check if events were stored
    print("\n📍 Step 6: Checking event storage...")
    import requests

    try:
        response = requests.get(f"http://localhost:5050/api/debug/events/{room_id}?limit=5")
        events = response.json()
        print(f"✅ Events stored: {events['total_events']} total")

        # Check for bot action events
        response = requests.get(f"http://localhost:5050/api/debug/events/{room_id}?event_type=bot_action&limit=5")
        bot_events = response.json()
        print(f"✅ Bot actions stored: {bot_events['total_events']} total")

        if bot_events['events']:
            event = bot_events['events'][0]
            payload = event.get('payload', {})
            if payload and 'action_type' in payload:
                print(f"✅ Event has payload data: {len(payload)} keys")
            else:
                print(f"❌ Event missing payload data")

    except Exception as e:
        print(f"❌ Error checking events: {e}")

if __name__ == "__main__":
    asyncio.run(test_basic_game_flow())
