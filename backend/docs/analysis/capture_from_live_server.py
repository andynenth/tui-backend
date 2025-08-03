#!/usr/bin/env python3
"""
Capture golden masters from a live WebSocket server.
This provides more accurate captures than simulation.
"""

import asyncio
import json
import websockets
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import sys

from tests.contracts.golden_master import GoldenMasterCapture, GoldenMasterRecord
from tests.contracts.websocket_contracts import get_all_contracts


class LiveServerCapture:
    """Capture golden masters from a running server"""

    def __init__(self, server_url: str = "ws://localhost:8000"):
        self.server_url = server_url
        self.capture = GoldenMasterCapture()
        self.captured_count = 0
        self.failed_count = 0

    async def capture_message_type(
        self, action: str, test_data: Dict[str, Any]
    ) -> bool:
        """Capture response for a specific message type"""
        try:
            # Connect to WebSocket
            endpoint = f"{self.server_url}/ws/lobby"  # Start in lobby

            async with websockets.connect(endpoint) as websocket:
                # Send test message
                message = {"action": action, "data": test_data}

                await websocket.send(json.dumps(message))

                # Capture response
                response = None
                broadcasts = []
                start_time = asyncio.get_event_loop().time()

                # Wait for response (with timeout)
                try:
                    response_text = await asyncio.wait_for(
                        websocket.recv(), timeout=5.0
                    )
                    response = json.loads(response_text)
                except asyncio.TimeoutError:
                    print(
                        f"   ⚠️  No direct response for {action} (might be broadcast-only)"
                    )

                # Capture any broadcasts (wait briefly)
                try:
                    while True:
                        broadcast_text = await asyncio.wait_for(
                            websocket.recv(), timeout=0.5
                        )
                        broadcasts.append(json.loads(broadcast_text))
                except asyncio.TimeoutError:
                    pass  # Expected when no more messages

                end_time = asyncio.get_event_loop().time()

                # Create golden master record
                record = GoldenMasterRecord(
                    test_id=f"live_{action}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    message_name=action,
                    input_message=message,
                    response=response,
                    broadcasts=broadcasts,
                    state_changes={},  # Would need state tracking
                    timing={"duration_ms": (end_time - start_time) * 1000},
                    timestamp=datetime.now().isoformat(),
                    system_version="current_live",
                )

                # Save golden master
                filepath = self.capture.save_golden_master(record)
                print(f"   ✅ Captured: {action} -> {filepath.name}")
                self.captured_count += 1
                return True

        except Exception as e:
            print(f"   ❌ Failed to capture {action}: {e}")
            self.failed_count += 1
            return False

    async def run_capture_suite(self):
        """Run full capture suite against live server"""
        print(f"Connecting to server at: {self.server_url}")
        print("=" * 60)

        # Test scenarios for each message type
        test_scenarios = {
            "ping": {"timestamp": 1234567890},
            "create_room": {"player_name": "TestPlayer"},
            "client_ready": {"player_name": "TestPlayer"},
            "request_room_list": {},
            "get_rooms": {},
            # Add more as needed based on your contracts
        }

        # First, test server connectivity
        print("\nTesting server connection...")
        try:
            async with websockets.connect(f"{self.server_url}/ws/lobby") as ws:
                await ws.send(json.dumps({"action": "ping", "data": {}}))
                await asyncio.wait_for(ws.recv(), timeout=2.0)
                print("✅ Server is responsive")
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            print("\nMake sure the server is running:")
            print("  cd backend && python -m api.main")
            return

        # Capture each message type
        print("\nCapturing golden masters...")
        for action, test_data in test_scenarios.items():
            await self.capture_message_type(action, test_data)
            await asyncio.sleep(0.1)  # Brief pause between captures

        # Summary
        print("\n" + "=" * 60)
        print(f"Capture Summary:")
        print(f"  ✅ Successful: {self.captured_count}")
        print(f"  ❌ Failed: {self.failed_count}")
        print(f"\nGolden masters saved to: tests/contracts/golden_masters/")


class InteractiveLiveCapture:
    """Interactive mode for capturing specific scenarios"""

    def __init__(self, server_url: str = "ws://localhost:8000"):
        self.server_url = server_url
        self.capture = GoldenMasterCapture()
        self.websocket = None
        self.room_id = None

    async def start(self):
        """Start interactive capture session"""
        print("Interactive Golden Master Capture")
        print("=" * 60)
        print("This mode lets you manually test scenarios and capture responses.")
        print(
            "Commands: connect, create_room, join_room, start_game, declare, play, quit"
        )
        print()

        while True:
            try:
                command = input("> ").strip().lower()

                if command == "quit":
                    break
                elif command == "connect":
                    await self.connect()
                elif command == "create_room":
                    await self.create_room()
                elif command == "join_room":
                    await self.join_room()
                elif command == "start_game":
                    await self.start_game()
                elif command == "declare":
                    await self.declare()
                elif command == "play":
                    await self.play()
                else:
                    print(f"Unknown command: {command}")

            except Exception as e:
                print(f"Error: {e}")

        if self.websocket:
            await self.websocket.close()

    async def connect(self):
        """Connect to server"""
        endpoint = input("Endpoint (lobby/room_id): ").strip()
        if not endpoint:
            endpoint = "lobby"

        url = f"{self.server_url}/ws/{endpoint}"
        print(f"Connecting to {url}...")

        try:
            self.websocket = await websockets.connect(url)
            print("✅ Connected")

            # Start listener
            asyncio.create_task(self.listen())
        except Exception as e:
            print(f"❌ Connection failed: {e}")

    async def listen(self):
        """Listen for messages from server"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                print(f"\n📥 Received: {json.dumps(data, indent=2)}")

                # Auto-capture interesting events
                if data.get("event") in [
                    "room_created",
                    "game_started",
                    "phase_change",
                ]:
                    self.capture_event(data)
        except Exception as e:
            print(f"\n❌ Listener error: {e}")

    def capture_event(self, event_data: Dict[str, Any]):
        """Capture an interesting event"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"interactive_{event_data.get('event')}_{timestamp}.json"
        filepath = Path("tests/contracts/golden_masters") / filename

        with open(filepath, "w") as f:
            json.dump(event_data, f, indent=2)

        print(f"💾 Captured to: {filename}")

    async def create_room(self):
        """Create a room"""
        name = input("Player name: ").strip()
        if not name:
            name = "TestPlayer"

        message = {"action": "create_room", "data": {"player_name": name}}

        await self.send_and_capture(message)

    async def send_and_capture(self, message: Dict[str, Any]):
        """Send message and capture response"""
        if not self.websocket:
            print("❌ Not connected")
            return

        print(f"📤 Sending: {json.dumps(message, indent=2)}")
        await self.websocket.send(json.dumps(message))

        # Response is captured by listener

    async def join_room(self):
        """Join a room"""
        room_id = input("Room ID: ").strip()
        name = input("Player name: ").strip()

        message = {
            "action": "join_room",
            "data": {"room_id": room_id, "player_name": name},
        }

        await self.send_and_capture(message)

    async def start_game(self):
        """Start the game"""
        message = {"action": "start_game", "data": {}}
        await self.send_and_capture(message)

    async def declare(self):
        """Make a declaration"""
        name = input("Player name: ").strip()
        value = int(input("Declaration value (0-8): ").strip())

        message = {"action": "declare", "data": {"player_name": name, "value": value}}

        await self.send_and_capture(message)

    async def play(self):
        """Play pieces"""
        name = input("Player name: ").strip()
        indices = input("Piece indices (comma-separated): ").strip()
        indices = [int(i.strip()) for i in indices.split(",")]

        message = {"action": "play", "data": {"player_name": name, "indices": indices}}

        await self.send_and_capture(message)


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Capture golden masters from live server"
    )
    parser.add_argument(
        "--url", default="ws://localhost:8000", help="WebSocket server URL"
    )
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")

    args = parser.parse_args()

    if args.interactive:
        capture = InteractiveLiveCapture(args.url)
        await capture.start()
    else:
        capture = LiveServerCapture(args.url)
        await capture.run_capture_suite()


if __name__ == "__main__":
    asyncio.run(main())
