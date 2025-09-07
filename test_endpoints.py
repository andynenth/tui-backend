#!/usr/bin/env python3
"""Test debug endpoints with a simple game"""

import asyncio
import json
import time
import websockets
import requests

async def test_game_and_endpoints():
    """Create a test game and then test debug endpoints"""
    base_url = "http://localhost:5050"
    room_id = None

    # 1. Create a room via WebSocket
    async with websockets.connect("ws://localhost:5050/ws/lobby") as ws:
        # Create room
        await ws.send(json.dumps({
            "event": "create_room",
            "data": {"player_name": "TestPlayer1"}
        }))

        response = await ws.recv()
        data = json.loads(response)
        if data.get("event") == "room_created":
            room_id = data["data"]["room_id"]
            print(f"✅ Created room: {room_id}")
        else:
            print(f"❌ Failed to create room: {data}")
            return

    # 2. Join room with 3 bots
    for i in range(2, 5):
        async with websockets.connect(f"ws://localhost:5050/ws/{room_id}") as ws:
            await ws.send(json.dumps({
                "event": "join_room",
                "data": {
                    "room_id": room_id,
                    "player_name": f"Bot{i}",
                    "is_bot": True
                }
            }))
            response = await ws.recv()
            print(f"Bot{i} joined: {json.loads(response).get('event')}")

    # 3. Start game
    async with websockets.connect(f"ws://localhost:5050/ws/{room_id}") as ws:
        await ws.send(json.dumps({
            "event": "client_ready",
            "data": {
                "room_id": room_id,
                "player_name": "TestPlayer1"
            }
        }))

        await ws.send(json.dumps({
            "event": "start_game",
            "data": {}
        }))

        # Wait a bit for game to process
        await asyncio.sleep(2)

    # 4. Now test the debug endpoints
    print(f"\n🔍 Testing debug endpoints for room {room_id}:")

    endpoints = [
        f"/api/debug/player-activity/{room_id}",
        f"/api/debug/connection-timeline/{room_id}",
        f"/api/debug/bot-control-analysis/{room_id}",
        f"/api/debug/events/{room_id}?limit=10",
        f"/api/debug/room-stats?room_id={room_id}",
        f"/api/rooms/{room_id}/state",
        "/api/debug/hang-diagnostics?limit=5",
        "/api/health/performance"
    ]

    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            print(f"\n📍 {endpoint}")
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                # Show summary of response
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, list):
                            print(f"   {key}: {len(value)} items")
                        elif isinstance(value, dict):
                            print(f"   {key}: {len(value)} keys")
                        else:
                            print(f"   {key}: {value}")
                else:
                    print(f"   Response: {type(data).__name__}")
            else:
                print(f"   Error: {response.text[:200]}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_game_and_endpoints())
