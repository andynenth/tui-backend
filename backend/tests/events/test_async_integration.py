#!/usr/bin/env python3
"""
Test script to verify Async architecture integration
"""

import asyncio
import websockets
import json
from datetime import datetime

BASE_URL = "ws://127.0.0.1:5050"


async def test_async_room_operations():
    """Test that async room operations work correctly"""

    print("🧪 Testing Async Room Operations...")
    print("-" * 50)

    # Test room creation via WebSocket
    print("\n1️⃣ Testing async room creation via WebSocket...")

    try:
        # Connect to lobby WebSocket
        async with websockets.connect(f"{BASE_URL}/ws/lobby") as websocket:
            # First send client_ready to establish connection
            await websocket.send(
                json.dumps(
                    {
                        "event": "client_ready",
                        "data": {"player_name": "AsyncTestPlayer"},
                    }
                )
            )

            # Wait for response
            response = await websocket.recv()
            print(f"Client ready response: {response}")

            # Create room with player name
            await websocket.send(
                json.dumps(
                    {"event": "create_room", "data": {"player_name": "AsyncTestPlayer"}}
                )
            )

            # Wait for room creation response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Room creation response: {json.dumps(data, indent=2)}")

            if data.get("event") == "room_created":
                room_id = data["data"]["room_id"]
                print(f"✅ Async room creation successful! Room ID: {room_id}")

                # Longer delay to ensure room is fully registered
                await asyncio.sleep(0.5)

                print(f"\n2️⃣ Room {room_id} created, will test direct connection")

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
        # Connect directly to the room WebSocket (not lobby)
        async with websockets.connect(f"{BASE_URL}/ws/{room_id}") as websocket:
            # Send client ready (this also joins the room)
            await websocket.send(
                json.dumps(
                    {"event": "client_ready", "data": {"player_name": "AsyncPlayer2"}}
                )
            )

            # Wait for initial responses
            response = await websocket.recv()
            data = json.loads(response)
            print(f"First response: {json.dumps(data, indent=2)[:200]}...")

            # Check for player_joined event
            if data.get("event") == "player_joined":
                print(f"✅ Async room join successful! Player joined room {room_id}")
            elif data.get("event") == "room_state":
                print(f"✅ Received room state, checking for player...")
                if "AsyncPlayer2" in str(data):
                    print(f"✅ Player successfully joined!")
            else:
                # Try to read another message
                response2 = await websocket.recv()
                data2 = json.loads(response2)
                print(f"Second response: {json.dumps(data2, indent=2)[:200]}...")
                if data2.get("event") == "player_joined":
                    print(f"✅ Async room join successful!")

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
