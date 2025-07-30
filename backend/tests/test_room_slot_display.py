#!/usr/bin/env python3
"""
Test script to verify room slot display fixes.

Tests:
1. Create a room
2. Connect to the room
3. Send client_ready event
4. Verify room state is returned with correct player/bot information
"""

import asyncio
import json
import websockets
import uuid

# Server URL
LOBBY_URL = "ws://localhost:5050/ws/lobby"
ROOM_URL_TEMPLATE = "ws://localhost:5050/ws/{room_id}"


async def test_room_creation_and_slots():
    """Test room creation and slot display"""
    print("🧪 Testing room creation and slot display...")

    room_id = None
    player_name = f"TestPlayer_{uuid.uuid4().hex[:6]}"

    try:
        # Step 1: Connect to lobby
        print(f"\n1️⃣ Connecting to lobby as {player_name}...")
        async with websockets.connect(LOBBY_URL) as lobby_ws:
            print("✅ Connected to lobby")

            # Send client_ready for lobby
            await lobby_ws.send(
                json.dumps(
                    {
                        "event": "client_ready",
                        "data": {"version": "1.0.0", "player_name": player_name},
                    }
                )
            )

            response = await lobby_ws.recv()
            data = json.loads(response)
            print(f"📥 Lobby client_ready response: {data.get('event')}")

            # Step 2: Create a room
            print(f"\n2️⃣ Creating room...")
            await lobby_ws.send(
                json.dumps(
                    {
                        "event": "create_room",
                        "data": {
                            "player_name": player_name,
                            "room_name": f"{player_name}'s Room",
                            "max_players": 4,
                            "auto_fill_bots": True,
                        },
                    }
                )
            )

            # Wait for room_created response
            response = await lobby_ws.recv()
            data = json.loads(response)

            if data.get("event") == "room_created":
                room_id = data.get("data", {}).get("room_id")
                room_info = data.get("data", {}).get("room_info", {})
                print(f"✅ Room created: {room_id}")
                print(f"📋 Room info:")
                print(f"   - Host: {room_info.get('host_id')}")
                print(f"   - Players: {len(room_info.get('players', []))}")

                # Display player slots
                for player in room_info.get("players", []):
                    print(
                        f"   - Slot {player.get('seat_position')}: {player.get('name')} ({'Bot' if player.get('is_bot') else 'Human'})"
                    )
            else:
                print(f"❌ Unexpected response: {data}")
                return

        # Step 3: Connect to the room
        if room_id:
            print(f"\n3️⃣ Connecting to room {room_id}...")
            room_url = ROOM_URL_TEMPLATE.format(room_id=room_id)

            async with websockets.connect(room_url) as room_ws:
                print("✅ Connected to room")

                # Step 4: Send client_ready with player name
                print(f"\n4️⃣ Sending client_ready for room...")
                await room_ws.send(
                    json.dumps(
                        {
                            "event": "client_ready",
                            "data": {"version": "1.0.0", "player_name": player_name},
                        }
                    )
                )

                # Wait for client_ready_ack
                response = await room_ws.recv()
                data = json.loads(response)

                if data.get("event") == "client_ready_ack":
                    print("✅ Client ready acknowledged")
                    room_state = data.get("data", {}).get("room_state")

                    if room_state:
                        print(f"\n📋 Room state received:")
                        print(f"   - Room ID: {room_state.get('room_id')}")
                        print(f"   - Status: {room_state.get('status')}")
                        print(f"   - Players:")

                        for player in room_state.get("players", []):
                            host_tag = " (HOST)" if player.get("is_host") else ""
                            bot_tag = " [BOT]" if player.get("is_bot") else " [HUMAN]"
                            print(
                                f"     - Slot {player.get('seat_position')}: {player.get('name')}{bot_tag}{host_tag}"
                            )

                        # Verify slots are properly filled
                        players = room_state.get("players", [])
                        if len(players) == 4:
                            print("\n✅ All 4 slots are filled!")

                            # Check if host is in slot 0
                            if players[0].get("name") == player_name and not players[
                                0
                            ].get("is_bot"):
                                print("✅ Host is correctly in slot 0")
                            else:
                                print("❌ Host is not in slot 0")

                            # Check if other slots have bots
                            bot_count = sum(1 for p in players if p.get("is_bot"))
                            if bot_count == 3:
                                print("✅ 3 bots are in the room")
                            else:
                                print(f"❌ Expected 3 bots, found {bot_count}")
                        else:
                            print(f"❌ Expected 4 players, found {len(players)}")
                    else:
                        print("❌ No room state in response")
                else:
                    print(f"❌ Unexpected response: {data}")

                # Step 5: Test get_room_state event
                print(f"\n5️⃣ Testing get_room_state event...")
                await room_ws.send(json.dumps({"event": "get_room_state", "data": {}}))

                response = await room_ws.recv()
                data = json.loads(response)

                if data.get("event") == "room_state":
                    print("✅ Room state event received")
                else:
                    print(f"❌ Unexpected response: {data}")

        print("\n✅ Test completed!")

    except Exception as e:
        print(f"❌ Error during test: {e}")


async def main():
    """Run the test"""
    print("🚀 Starting Room Slot Display Test")
    print("=" * 50)

    await test_room_creation_and_slots()

    print("\n" + "=" * 50)
    print("🏁 Test finished!")


if __name__ == "__main__":
    asyncio.run(main())
