#!/usr/bin/env python3
"""
Manual testing script to identify WebSocket disconnection issues with rate limiting.

This script simulates various scenarios that might trigger rate limit problems:
1. Normal game flow
2. Rapid fire events
3. Multiple concurrent connections
4. Reconnection after rate limiting

Run this script while the backend is running to observe behavior.
"""

import asyncio
import json
import sys
import time
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosed


class RateLimitTester:
    def __init__(self, base_url="ws://localhost:5050"):
        self.base_url = base_url
        self.results = []

    async def test_normal_game_flow(self):
        """Test a normal game flow to ensure it doesn't trigger rate limits."""
        print("\n=== Testing Normal Game Flow ===")

        try:
            # Connect to lobby
            async with websockets.connect(f"{self.base_url}/ws/lobby") as ws:
                print("Connected to lobby")

                # Create room
                await ws.send(
                    json.dumps(
                        {"event": "create_room", "data": {"player_name": "TestPlayer1"}}
                    )
                )

                response = await ws.recv()
                data = json.loads(response)
                print(f"Create room response: {data}")

                if data.get("event") == "room_created":
                    room_id = data["data"]["room_id"]
                    print(f"Room created: {room_id}")

                    # Connect to room
                    async with websockets.connect(
                        f"{self.base_url}/ws/{room_id}"
                    ) as room_ws:
                        print(f"Connected to room {room_id}")

                        # Simulate normal game events
                        events = [
                            {
                                "event": "player_ready",
                                "data": {"player_name": "TestPlayer1"},
                            },
                            {"event": "ping", "data": {"timestamp": time.time()}},
                            {"event": "get_room_state", "data": {}},
                        ]

                        for event in events:
                            await room_ws.send(json.dumps(event))
                            response = await room_ws.recv()
                            print(
                                f"Event: {event['event']}, Response: {json.loads(response)['event']}"
                            )
                            await asyncio.sleep(1)  # Normal pacing

                        self.results.append(
                            {
                                "test": "normal_game_flow",
                                "status": "PASS",
                                "message": "Normal game flow completed without issues",
                            }
                        )

        except ConnectionClosed as e:
            self.results.append(
                {
                    "test": "normal_game_flow",
                    "status": "FAIL",
                    "message": f"Connection closed unexpectedly: {e}",
                }
            )
        except Exception as e:
            self.results.append(
                {"test": "normal_game_flow", "status": "FAIL", "message": f"Error: {e}"}
            )

    async def test_rapid_fire_events(self):
        """Test rapid fire events to trigger rate limiting."""
        print("\n=== Testing Rapid Fire Events ===")

        try:
            async with websockets.connect(f"{self.base_url}/ws/test_room") as ws:
                print("Connected to test room")

                # Send many events rapidly
                event_type = "declare"
                rate_limited = False

                for i in range(20):
                    event = {
                        "event": event_type,
                        "data": {"player_name": "TestPlayer", "pile_count": 3},
                    }

                    await ws.send(json.dumps(event))
                    response = await ws.recv()
                    data = json.loads(response)

                    if data.get("event") == "error" and "rate_limit" in str(
                        data.get("data", {})
                    ):
                        print(f"Rate limited at event #{i+1}")
                        rate_limited = True

                        # Check if connection is still alive
                        await asyncio.sleep(2)

                        # Try a ping to see if connection works
                        await ws.send(
                            json.dumps(
                                {"event": "ping", "data": {"timestamp": time.time()}}
                            )
                        )

                        ping_response = await ws.recv()
                        print(
                            f"Ping after rate limit: {json.loads(ping_response)['event']}"
                        )

                        self.results.append(
                            {
                                "test": "rapid_fire_events",
                                "status": "PASS",
                                "message": f"Rate limiting triggered correctly at event #{i+1}, connection still alive",
                            }
                        )
                        break

                if not rate_limited:
                    self.results.append(
                        {
                            "test": "rapid_fire_events",
                            "status": "WARNING",
                            "message": "Rate limiting not triggered after 20 rapid events",
                        }
                    )

        except ConnectionClosed as e:
            self.results.append(
                {
                    "test": "rapid_fire_events",
                    "status": "FAIL",
                    "message": f"Connection closed when rate limited: {e}",
                }
            )
        except Exception as e:
            self.results.append(
                {
                    "test": "rapid_fire_events",
                    "status": "FAIL",
                    "message": f"Error: {e}",
                }
            )

    async def test_concurrent_connections(self):
        """Test multiple concurrent connections from same client."""
        print("\n=== Testing Concurrent Connections ===")

        try:
            # Create multiple connections
            connections = []
            for i in range(5):
                ws = await websockets.connect(
                    f"{self.base_url}/ws/concurrent_test_room"
                )
                connections.append(ws)
                print(f"Connection {i+1} established")

            # Send events from all connections
            tasks = []
            for i, ws in enumerate(connections):

                async def send_events(ws_conn, conn_id):
                    for j in range(3):
                        event = {
                            "event": "play",
                            "data": {
                                "player_name": f"Player{conn_id}",
                                "pieces": [1, 2],
                            },
                        }
                        await ws_conn.send(json.dumps(event))
                        response = await ws_conn.recv()
                        data = json.loads(response)
                        print(f"Connection {conn_id}, Event {j+1}: {data['event']}")
                        await asyncio.sleep(0.5)

                tasks.append(send_events(ws, i + 1))

            await asyncio.gather(*tasks)

            # Close all connections
            for ws in connections:
                await ws.close()

            self.results.append(
                {
                    "test": "concurrent_connections",
                    "status": "PASS",
                    "message": "Multiple concurrent connections handled correctly",
                }
            )

        except Exception as e:
            self.results.append(
                {
                    "test": "concurrent_connections",
                    "status": "FAIL",
                    "message": f"Error with concurrent connections: {e}",
                }
            )

    async def test_reconnection_after_rate_limit(self):
        """Test reconnection behavior after being rate limited."""
        print("\n=== Testing Reconnection After Rate Limit ===")

        try:
            # First connection - trigger rate limit
            async with websockets.connect(f"{self.base_url}/ws/reconnect_test") as ws:
                print("Initial connection established")

                # Trigger rate limit
                for i in range(10):
                    event = {"event": "create_room", "data": {"player_name": "Spammer"}}
                    await ws.send(json.dumps(event))
                    response = await ws.recv()
                    data = json.loads(response)

                    if data.get("event") == "error" and "rate_limit" in str(
                        data.get("data", {})
                    ):
                        print(f"Rate limited at attempt #{i+1}")
                        retry_after = data["data"].get("retry_after", 60)
                        print(f"Retry after: {retry_after} seconds")
                        break

            # Try immediate reconnection
            print("\nAttempting immediate reconnection...")
            try:
                async with websockets.connect(
                    f"{self.base_url}/ws/reconnect_test"
                ) as ws2:
                    print("Reconnection successful")

                    # Try a normal event
                    await ws2.send(
                        json.dumps(
                            {"event": "ping", "data": {"timestamp": time.time()}}
                        )
                    )

                    response = await ws2.recv()
                    data = json.loads(response)

                    if data.get("event") == "error" and "rate_limit" in str(
                        data.get("data", {})
                    ):
                        self.results.append(
                            {
                                "test": "reconnection_after_rate_limit",
                                "status": "PASS",
                                "message": "Rate limit persists across reconnections (good)",
                            }
                        )
                    else:
                        self.results.append(
                            {
                                "test": "reconnection_after_rate_limit",
                                "status": "WARNING",
                                "message": "Rate limit not enforced on new connection",
                            }
                        )

            except ConnectionClosed as e:
                self.results.append(
                    {
                        "test": "reconnection_after_rate_limit",
                        "status": "FAIL",
                        "message": f"Cannot reconnect after rate limit: {e}",
                    }
                )

        except Exception as e:
            self.results.append(
                {
                    "test": "reconnection_after_rate_limit",
                    "status": "FAIL",
                    "message": f"Error: {e}",
                }
            )

    async def test_websocket_stability_under_rate_limit(self):
        """Test WebSocket stability when rate limited."""
        print("\n=== Testing WebSocket Stability Under Rate Limit ===")

        try:
            async with websockets.connect(f"{self.base_url}/ws/stability_test") as ws:
                print("Connection established")

                # Phase 1: Normal operation
                print("Phase 1: Normal operation")
                for i in range(3):
                    await ws.send(
                        json.dumps(
                            {"event": "ping", "data": {"timestamp": time.time()}}
                        )
                    )
                    response = await ws.recv()
                    print(f"Normal ping {i+1}: OK")
                    await asyncio.sleep(1)

                # Phase 2: Trigger rate limit
                print("\nPhase 2: Triggering rate limit")
                for i in range(10):
                    await ws.send(
                        json.dumps(
                            {
                                "event": "declare",
                                "data": {"player_name": "Test", "pile_count": 3},
                            }
                        )
                    )
                    response = await ws.recv()
                    data = json.loads(response)
                    if data.get("event") == "error":
                        print(f"Rate limited at event #{i+1}")
                        break

                # Phase 3: Test connection after rate limit
                print("\nPhase 3: Testing connection after rate limit")
                await asyncio.sleep(2)

                # Should still be able to send allowed events
                await ws.send(
                    json.dumps({"event": "ping", "data": {"timestamp": time.time()}})
                )
                response = await ws.recv()
                data = json.loads(response)

                if data.get("event") == "pong":
                    print("Connection still functional after rate limit")
                    self.results.append(
                        {
                            "test": "websocket_stability_under_rate_limit",
                            "status": "PASS",
                            "message": "WebSocket remains stable after rate limiting",
                        }
                    )
                else:
                    self.results.append(
                        {
                            "test": "websocket_stability_under_rate_limit",
                            "status": "FAIL",
                            "message": f"Unexpected response after rate limit: {data}",
                        }
                    )

        except ConnectionClosed as e:
            self.results.append(
                {
                    "test": "websocket_stability_under_rate_limit",
                    "status": "FAIL",
                    "message": f"Connection closed during rate limit test: {e}",
                }
            )
        except Exception as e:
            self.results.append(
                {
                    "test": "websocket_stability_under_rate_limit",
                    "status": "FAIL",
                    "message": f"Error: {e}",
                }
            )

    async def run_all_tests(self):
        """Run all rate limit tests."""
        print(f"\n{'='*50}")
        print(f"Rate Limit Testing - {datetime.now()}")
        print(f"{'='*50}")

        tests = [
            self.test_normal_game_flow,
            self.test_rapid_fire_events,
            self.test_concurrent_connections,
            self.test_reconnection_after_rate_limit,
            self.test_websocket_stability_under_rate_limit,
        ]

        for test in tests:
            await test()
            await asyncio.sleep(2)  # Space between tests

        # Print summary
        print(f"\n{'='*50}")
        print("Test Results Summary")
        print(f"{'='*50}")

        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        warnings = sum(1 for r in self.results if r["status"] == "WARNING")

        for result in self.results:
            status_color = {
                "PASS": "\033[92m",  # Green
                "FAIL": "\033[91m",  # Red
                "WARNING": "\033[93m",  # Yellow
            }.get(result["status"], "")
            reset_color = "\033[0m"

            print(
                f"{status_color}[{result['status']}]{reset_color} {result['test']}: {result['message']}"
            )

        print(f"\nTotal: {len(self.results)} tests")
        print(f"Passed: {passed}, Failed: {failed}, Warnings: {warnings}")

        return failed == 0


async def main():
    """Main function to run the tests."""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "ws://localhost:5050"

    print(f"Testing rate limiting on {base_url}")
    print("Make sure the backend is running!")

    tester = RateLimitTester(base_url)
    success = await tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
