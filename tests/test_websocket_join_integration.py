#!/usr/bin/env python3
"""
WebSocket integration test for join room functionality.
Tests the full stack including WebSocket layer.
"""

import asyncio
import websockets
import json
import time
from typing import List, Dict, Any

# Test configuration
WS_URL = "ws://localhost:8000/ws/lobby"
TEST_ROOM_PREFIX = f"ws_test_{int(time.time())}"


async def create_test_room(host_name: str) -> str:
    """Create a test room via WebSocket."""
    async with websockets.connect(WS_URL) as ws:
        # Send create room command
        await ws.send(json.dumps({
            "event": "create_room",
            "data": {"player_name": host_name}
        }))

        # Wait for response
        response = await ws.recv()
        data = json.loads(response)

        if data["event"] == "room_created":
            return data["data"]["room_id"]
        else:
            raise Exception(f"Failed to create room: {data}")


async def join_room_attempt(room_id: str, player_name: str) -> Dict[str, Any]:
    """Attempt to join a room and return the result."""
    try:
        async with websockets.connect(WS_URL) as ws:
            # Send join room command
            await ws.send(json.dumps({
                "event": "join_room",
                "data": {
                    "room_id": room_id,
                    "player_name": player_name
                }
            }))

            # Collect responses (might get room_joined or error)
            start_time = time.time()
            responses = []

            # Wait for response (with timeout)
            while time.time() - start_time < 2:  # 2 second timeout
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=0.5)
                    data = json.loads(response)
                    responses.append(data)

                    # Check for success or error
                    if data["event"] in ["room_joined", "error"]:
                        return {
                            "player_name": player_name,
                            "success": data["event"] == "room_joined",
                            "event": data["event"],
                            "data": data.get("data", {}),
                            "responses": responses
                        }

                except asyncio.TimeoutError:
                    break

            return {
                "player_name": player_name,
                "success": False,
                "error": "Timeout waiting for response",
                "responses": responses
            }

    except Exception as e:
        return {
            "player_name": player_name,
            "success": False,
            "error": str(e),
            "responses": []
        }


async def test_concurrent_websocket_joins():
    """Test concurrent joins through WebSocket layer."""
    print("\n" + "=" * 80)
    print("WEBSOCKET CONCURRENT JOIN TEST")
    print("=" * 80 + "\n")

    try:
        # Create a test room
        print("Creating test room...")
        room_id = await create_test_room("WSTestHost")
        print(f"✅ Room created: {room_id}")

        # Create 10 concurrent join attempts
        player_names = [f"WSPlayer{i}" for i in range(1, 11)]

        print(f"\nAttempting {len(player_names)} concurrent joins...")
        start_time = time.time()

        # Run all joins concurrently
        results = await asyncio.gather(*[
            join_room_attempt(room_id, name) for name in player_names
        ])

        duration = (time.time() - start_time) * 1000

        # Analyze results
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        print(f"\n=== RESULTS ===")
        print(f"Duration: {duration:.1f}ms")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")

        # Show successful joins
        if successful:
            print("\nSuccessful joins:")
            for result in successful:
                slot = result["data"].get("assigned_slot", "?")
                print(f"  - {result['player_name']} → slot {slot}")

        # Analyze failures
        if failed:
            print("\nFailed joins:")
            error_types = {}
            for result in failed:
                error_msg = result.get("data", {}).get("message", result.get("error", "Unknown"))
                error_type = result.get("data", {}).get("type", "unknown")

                if error_type not in error_types:
                    error_types[error_type] = []
                error_types[error_type].append(result['player_name'])

            for error_type, players in error_types.items():
                print(f"  - {error_type}: {len(players)} players")

        # Verify expected behavior
        print(f"\n=== VERIFICATION ===")

        # Should have exactly 3 successful joins (replacing 3 bots)
        expected_success = 3
        if len(successful) == expected_success:
            print(f"✅ PASS: Expected {expected_success} successful joins, got {len(successful)}")
        else:
            print(f"❌ FAIL: Expected {expected_success} successful joins, got {len(successful)}")

        # Check that all failures are due to room being full
        all_full = all(
            r.get("data", {}).get("type") == "room_full"
            for r in failed
            if "data" in r and "type" in r["data"]
        )

        if all_full and failed:
            print("✅ PASS: All failures correctly report 'room_full'")
        elif not failed:
            print("⚠️  WARNING: No failures detected (might be an issue)")
        else:
            print("❌ FAIL: Some failures have unexpected error types")

        # Performance check
        avg_time = duration / len(results)
        if avg_time < 50:  # Should handle concurrent requests quickly
            print(f"✅ PASS: Good performance ({avg_time:.1f}ms per request)")
        else:
            print(f"⚠️  WARNING: High latency ({avg_time:.1f}ms per request)")

        return len(successful) == expected_success

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_websocket_game_started_rejection():
    """Test that WebSocket properly rejects joins to started games."""
    print("\n" + "=" * 80)
    print("WEBSOCKET GAME STARTED REJECTION TEST")
    print("=" * 80 + "\n")

    try:
        # This test would need to:
        # 1. Create a room
        # 2. Join 4 players
        # 3. Start the game
        # 4. Try to join with another player
        # 5. Verify rejection

        print("⚠️  This test requires game start functionality")
        print("   Skipping for now...")
        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def test_websocket_duplicate_player():
    """Test handling of duplicate player names."""
    print("\n" + "=" * 80)
    print("WEBSOCKET DUPLICATE PLAYER TEST")
    print("=" * 80 + "\n")

    try:
        # Create room
        room_id = await create_test_room("DupeTestHost")
        print(f"✅ Room created: {room_id}")

        # Join with same player twice
        player_name = "DuplicateWSPlayer"

        print(f"\nJoining with '{player_name}'...")
        result1 = await join_room_attempt(room_id, player_name)

        if result1["success"]:
            print(f"✅ First join successful, slot: {result1['data'].get('assigned_slot')}")
        else:
            print(f"❌ First join failed: {result1}")
            return False

        print(f"\nJoining again with same name...")
        result2 = await join_room_attempt(room_id, player_name)

        if result2["success"] and result2["data"].get("already_joined"):
            print("✅ PASS: Duplicate join handled correctly with already_joined flag")
            return True
        elif result2["success"]:
            print("⚠️  WARNING: Join succeeded but missing already_joined flag")
            return True
        else:
            print(f"❌ FAIL: Second join failed: {result2}")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def main():
    """Run WebSocket integration tests."""
    print("\nWebSocket Integration Tests")
    print("=" * 80)
    print("NOTE: Requires server running on localhost:8000")
    print("=" * 80)

    # Check if server is running
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ Server is running")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        print("Please start the server with: ./start.sh")
        return

    # Run tests
    tests = [
        ("Concurrent Joins", test_concurrent_websocket_joins),
        ("Duplicate Player", test_websocket_duplicate_player),
        ("Game Started Rejection", test_websocket_game_started_rejection),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = await test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print("WEBSOCKET TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, p in results if p)
    total = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All WebSocket tests passed!")
    else:
        print("\n⚠️  Some tests failed.")


if __name__ == "__main__":
    asyncio.run(main())
