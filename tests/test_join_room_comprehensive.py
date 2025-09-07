#!/usr/bin/env python3
"""
Comprehensive test suite for join room race condition fix.
Tests all aspects including race conditions, edge cases, and monitoring.
"""

import asyncio
import time
import sqlite3
from typing import List, Dict, Any, Tuple
import logging
import sys
import os
import json

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.engine.async_room import AsyncRoom
from backend.shared_event_store import event_store

# Set up logging to capture detailed information
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path for actual database
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'game_events.db')


class TestResult:
    """Track test results with details."""
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.error = None
        self.details = []
        self.duration_ms = 0

    def add_detail(self, detail: str):
        self.details.append(detail)

    def set_error(self, error: str):
        self.error = error
        self.passed = False

    def set_passed(self):
        self.passed = True


class JoinRoomTestSuite:
    """Comprehensive test suite for join room functionality."""

    def __init__(self):
        self.results: List[TestResult] = []

    async def test_basic_concurrent_joins(self) -> TestResult:
        """Test basic concurrent join scenario with expected behavior."""
        result = TestResult("Basic Concurrent Joins")
        start_time = time.time()

        try:
            # Create room with host
            room = AsyncRoom("test_concurrent_basic", "Host")
            result.add_detail(f"Room created with host: {room.host_name}")

            # Initial state: 1 human (host) + 3 bots
            initial_humans = len([p for p in room.players if p and not p.is_bot])
            initial_bots = len([p for p in room.players if p and p.is_bot])
            result.add_detail(f"Initial state: {initial_humans} humans, {initial_bots} bots")

            # 10 concurrent join attempts
            players = [f"Player{i}" for i in range(1, 11)]

            # Execute concurrent joins
            join_results = await asyncio.gather(
                *[room.join_room(name) for name in players],
                return_exceptions=False
            )

            # Analyze results
            successful = [r for r in join_results if r['success']]
            failed = [r for r in join_results if not r['success']]

            result.add_detail(f"Attempts: {len(join_results)}, Success: {len(successful)}, Failed: {len(failed)}")

            # Verify exactly 3 succeeded (replacing 3 bots)
            if len(successful) != 3:
                result.set_error(f"Expected 3 successful joins, got {len(successful)}")
                return result

            # Verify all slots filled with humans
            final_humans = len([p for p in room.players if p and not p.is_bot])
            if final_humans != 4:
                result.set_error(f"Expected 4 humans in final state, got {final_humans}")
                return result

            # Verify no duplicate players
            player_names = [p.name for p in room.players if p]
            if len(player_names) != len(set(player_names)):
                result.set_error("Found duplicate players in room")
                return result

            # Verify all failed with correct error
            error_types = [f.get('error_type') for f in failed]
            if not all(et == 'room_full' for et in error_types):
                result.set_error(f"Unexpected error types: {set(error_types)}")
                return result

            result.set_passed()

        except Exception as e:
            result.set_error(f"Exception: {str(e)}")

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    async def test_extreme_concurrency(self) -> TestResult:
        """Test with extreme concurrency (100+ simultaneous joins)."""
        result = TestResult("Extreme Concurrency Test")
        start_time = time.time()

        try:
            room = AsyncRoom("test_extreme_concurrency", "Host")

            # Create 100 concurrent join attempts
            players = [f"StressPlayer{i}" for i in range(1, 101)]

            join_start = time.time()
            join_results = await asyncio.gather(
                *[room.join_room(name) for name in players],
                return_exceptions=False
            )
            join_duration = (time.time() - join_start) * 1000

            successful = [r for r in join_results if r['success']]
            failed = [r for r in join_results if not r['success']]

            result.add_detail(f"100 concurrent attempts in {join_duration:.1f}ms")
            result.add_detail(f"Success: {len(successful)}, Failed: {len(failed)}")

            # Should have exactly 3 successful (replacing bots)
            if len(successful) != 3:
                result.set_error(f"Expected 3 successful, got {len(successful)}")
                return result

            # Check performance - should handle 100 requests quickly
            avg_time = join_duration / len(join_results)
            result.add_detail(f"Average time per request: {avg_time:.2f}ms")

            if avg_time > 10:  # More than 10ms average is concerning
                result.add_detail("⚠️ Performance warning: High latency detected")

            # Verify lock wait times from database directly
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.execute(
                """SELECT json_extract(payload, '$.lock_wait_ms') as lock_wait_ms
                   FROM game_events_v2
                   WHERE room_id = ? AND event_type = 'join_attempt'
                   ORDER BY id DESC LIMIT 100""",
                ("test_extreme_concurrency",)
            )
            lock_waits = [row[0] for row in cursor.fetchall() if row[0] is not None]
            conn.close()

            if lock_waits:
                max_wait = max(lock_waits)
                avg_wait = sum(lock_waits) / len(lock_waits)
                result.add_detail(f"Lock wait times: avg={avg_wait:.1f}ms, max={max_wait:.1f}ms")

            result.set_passed()

        except Exception as e:
            result.set_error(f"Exception: {str(e)}")

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    async def test_already_joined_player(self) -> TestResult:
        """Test behavior when same player tries to join multiple times."""
        result = TestResult("Already Joined Player Test")
        start_time = time.time()

        try:
            room = AsyncRoom("test_already_joined", "Host")

            # First join
            result1 = await room.join_room("DuplicatePlayer")
            if not result1['success']:
                result.set_error("First join should succeed")
                return result

            slot1 = result1['slot']
            result.add_detail(f"First join successful, slot: {slot1}")

            # Try to join again
            result2 = await room.join_room("DuplicatePlayer")

            # Should succeed but with already_joined flag
            if not result2['success']:
                result.set_error("Rejoin should succeed")
                return result

            if not result2.get('already_joined'):
                result.set_error("Missing already_joined flag")
                return result

            if result2['slot'] != slot1:
                result.set_error(f"Slot changed from {slot1} to {result2['slot']}")
                return result

            result.add_detail("Rejoin handled correctly with already_joined flag")

            # Verify player count didn't change
            human_count = len([p for p in room.players if p and not p.is_bot])
            if human_count != 2:  # Host + DuplicatePlayer
                result.set_error(f"Expected 2 humans, got {human_count}")
                return result

            result.set_passed()

        except Exception as e:
            result.set_error(f"Exception: {str(e)}")

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    async def test_game_started_rejection(self) -> TestResult:
        """Test that joins are rejected when game has started."""
        result = TestResult("Game Started Rejection Test")
        start_time = time.time()

        try:
            room = AsyncRoom("test_started_rejection", "Host")

            # Mark game as started
            room.started = True
            result.add_detail("Game marked as started")

            # Try to join
            join_result = await room.join_room("LatePlayer")

            if join_result['success']:
                result.set_error("Join should fail for started game")
                return result

            if join_result.get('error_type') != 'game_started':
                result.set_error(f"Wrong error type: {join_result.get('error_type')}")
                return result

            result.add_detail(f"Join correctly rejected: {join_result['error']}")

            # Try multiple concurrent joins to started game
            late_players = [f"Late{i}" for i in range(1, 6)]
            late_results = await asyncio.gather(
                *[room.join_room(name) for name in late_players],
                return_exceptions=False
            )

            # All should fail
            if any(r['success'] for r in late_results):
                result.set_error("Some joins succeeded on started game")
                return result

            result.add_detail(f"All {len(late_results)} concurrent joins correctly rejected")
            result.set_passed()

        except Exception as e:
            result.set_error(f"Exception: {str(e)}")

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    async def test_empty_slots_vs_bot_replacement(self) -> TestResult:
        """Test that empty slots are preferred over bot replacement."""
        result = TestResult("Empty Slots vs Bot Replacement Test")
        start_time = time.time()

        try:
            # Create room with mix of empty and bot slots
            room = AsyncRoom("test_slot_preference", "Host")

            # Manually set some slots to None
            room.players[2] = None  # Make slot 2 empty
            result.add_detail("Created room with empty slot at position 2")

            # Join should take empty slot, not replace bot
            join_result = await room.join_room("NewPlayer")

            if not join_result['success']:
                result.set_error("Join should succeed")
                return result

            if join_result['slot'] != 2:
                result.set_error(f"Should use empty slot 2, got slot {join_result['slot']}")
                return result

            if join_result.get('replaced_bot'):
                result.set_error("Should not replace bot when empty slot available")
                return result

            result.add_detail("Correctly used empty slot instead of replacing bot")

            # Verify bots still in place
            bot_count = len([p for p in room.players if p and p.is_bot])
            if bot_count != 2:  # Should still have 2 bots
                result.set_error(f"Expected 2 bots remaining, got {bot_count}")
                return result

            result.set_passed()

        except Exception as e:
            result.set_error(f"Exception: {str(e)}")

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    async def test_race_condition_verification(self) -> TestResult:
        """Verify no race conditions exist in current implementation."""
        result = TestResult("Race Condition Verification")
        start_time = time.time()

        try:
            room = AsyncRoom("test_race_verification", "Host")

            # Run multiple rounds of concurrent joins
            for round_num in range(5):
                # Reset room
                room = AsyncRoom(f"test_race_round_{round_num}", "Host")

                # 20 concurrent attempts per round
                players = [f"R{round_num}P{i}" for i in range(1, 21)]

                join_results = await asyncio.gather(
                    *[room.join_room(name) for name in players],
                    return_exceptions=False
                )

                successful = [r for r in join_results if r['success']]

                # Should always be exactly 3
                if len(successful) != 3:
                    result.set_error(f"Round {round_num}: Expected 3 successful, got {len(successful)}")
                    return result

                # Check no duplicate slots assigned
                slots = [r['slot'] for r in successful]
                if len(slots) != len(set(slots)):
                    result.set_error(f"Round {round_num}: Duplicate slots assigned: {slots}")
                    return result

                result.add_detail(f"Round {round_num}: ✓ No race conditions detected")

            result.set_passed()

        except Exception as e:
            result.set_error(f"Exception: {str(e)}")

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    async def test_event_store_integration(self) -> TestResult:
        """Test that join attempts are properly stored in event store."""
        result = TestResult("Event Store Integration Test")
        start_time = time.time()

        try:
            room_id = f"test_event_store_{int(time.time())}"
            room = AsyncRoom(room_id, "Host")

            # Make some join attempts
            test_players = ["EventPlayer1", "EventPlayer2", "EventPlayer3"]

            for player in test_players:
                await room.join_room(player)

            # Give event store time to persist
            await asyncio.sleep(0.1)

            # Query events from database directly
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.execute(
                """SELECT id, event_type, payload, player_id
                   FROM game_events_v2
                   WHERE room_id = ? AND event_type = 'join_attempt'""",
                (room_id,)
            )

            events = []
            for row in cursor.fetchall():
                events.append({
                    'id': row[0],
                    'event_type': row[1],
                    'payload': json.loads(row[2]) if row[2] else {},
                    'player_id': row[3]
                })
            conn.close()

            if not events:
                result.set_error("No events found in database")
                return result

            result.add_detail(f"Found {len(events)} join_attempt events")

            # Verify event structure
            for event in events:
                payload = event['payload']
                required_fields = ['player_name', 'success', 'lock_wait_ms', 'total_ms']

                for field in required_fields:
                    if field not in payload:
                        result.set_error(f"Payload missing required field: {field}")
                        return result

            # Verify we can query by player
            player_events = [e for e in events if e.get('player_id') == 'EventPlayer1']
            if not player_events:
                result.set_error("Cannot find events by player_id")
                return result

            result.add_detail("Event structure and storage verified")
            result.set_passed()

        except Exception as e:
            result.set_error(f"Exception: {str(e)}")

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    async def run_all_tests(self) -> Tuple[int, int]:
        """Run all tests and return summary."""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE JOIN ROOM TEST SUITE")
        print("=" * 80 + "\n")

        # Define all test methods
        test_methods = [
            self.test_basic_concurrent_joins,
            self.test_extreme_concurrency,
            self.test_already_joined_player,
            self.test_game_started_rejection,
            self.test_empty_slots_vs_bot_replacement,
            self.test_race_condition_verification,
            self.test_event_store_integration,
        ]

        # Run each test
        for test_method in test_methods:
            print(f"Running: {test_method.__name__}...", end='', flush=True)

            try:
                result = await test_method()
                self.results.append(result)

                if result.passed:
                    print(f" ✅ PASS ({result.duration_ms:.1f}ms)")
                else:
                    print(f" ❌ FAIL ({result.duration_ms:.1f}ms)")
                    print(f"  Error: {result.error}")

                # Print details if any
                for detail in result.details:
                    print(f"    - {detail}")

            except Exception as e:
                print(f" ❌ ERROR: {e}")
                error_result = TestResult(test_method.__name__)
                error_result.set_error(f"Test execution error: {e}")
                self.results.append(error_result)

        # Summary
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        print("\n" + "-" * 80)
        print("TEST SUMMARY")
        print("-" * 80)

        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"{status} | {result.test_name} ({result.duration_ms:.1f}ms)")

        print(f"\nTotal: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Join room implementation is working correctly.")
        else:
            print("\n⚠️ Some tests failed. Review the implementation.")

        return passed, total


async def test_monitoring_queries():
    """Test the SQL monitoring queries."""
    print("\n" + "=" * 80)
    print("TESTING SQL MONITORING QUERIES")
    print("=" * 80 + "\n")

    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        # First, create some test data
        room_id = f"sql_test_{int(time.time())}"
        room = AsyncRoom(room_id, "SQLTestHost")

        # Generate some join attempts
        players = [f"SQLPlayer{i}" for i in range(1, 11)]
        await asyncio.gather(*[room.join_room(p) for p in players])

        # Give time for events to persist
        await asyncio.sleep(0.1)

        print("Testing monitoring queries against database...")

        # Test Query 1: Join success rate
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total_attempts,
                SUM(CASE WHEN json_extract(payload, '$.success') = 1 THEN 1 ELSE 0 END) as successful,
                AVG(json_extract(payload, '$.lock_wait_ms')) as avg_lock_wait_ms
            FROM game_events_v2
            WHERE event_type = 'join_attempt'
              AND room_id = ?
        """, (room_id,))

        row = cursor.fetchone()
        if row and row['total_attempts'] > 0:
            print(f"✅ Query 1 (Success Rate): {row['successful']}/{row['total_attempts']} successful")
        else:
            print("❌ Query 1 failed: No data returned")

        # Test Query 2: Error distribution
        cursor = conn.execute("""
            SELECT
                json_extract(payload, '$.error_type') as error_type,
                COUNT(*) as count
            FROM game_events_v2
            WHERE event_type = 'join_attempt'
              AND json_extract(payload, '$.success') = 0
              AND room_id = ?
            GROUP BY error_type
        """, (room_id,))

        errors = cursor.fetchall()
        if errors:
            print("✅ Query 2 (Error Distribution): Found error types:")
            for error in errors:
                print(f"   - {error['error_type']}: {error['count']}")
        else:
            print("✅ Query 2 (Error Distribution): No errors (all joins successful)")

        # Test Query 3: Lock wait times
        cursor = conn.execute("""
            SELECT
                MIN(json_extract(payload, '$.lock_wait_ms')) as min_wait,
                MAX(json_extract(payload, '$.lock_wait_ms')) as max_wait,
                AVG(json_extract(payload, '$.lock_wait_ms')) as avg_wait
            FROM game_events_v2
            WHERE event_type = 'join_attempt'
              AND room_id = ?
        """, (room_id,))

        row = cursor.fetchone()
        if row:
            print(f"✅ Query 3 (Lock Performance): min={row['min_wait']:.1f}ms, "
                  f"avg={row['avg_wait']:.1f}ms, max={row['max_wait']:.1f}ms")
        else:
            print("❌ Query 3 failed: No data returned")

        conn.close()
        print("\nSQL query tests completed.")

    except Exception as e:
        print(f"❌ SQL test error: {e}")
        import traceback
        traceback.print_exc()


async def test_health_monitor():
    """Test the health monitor functionality."""
    print("\n" + "=" * 80)
    print("TESTING HEALTH MONITOR")
    print("=" * 80 + "\n")

    try:
        # Import health monitor
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'monitoring'))
        from join_room_health_monitor import JoinRoomHealthMonitor

        monitor = JoinRoomHealthMonitor(DB_PATH)

        # Test health check
        health = monitor.check_join_health(window_seconds=3600)  # Last hour
        print(f"Health Status: {health.get('status', 'NO_DATA')}")

        if health.get('total_attempts', 0) > 0:
            print(f"  - Total Attempts: {health['total_attempts']}")
            print(f"  - Success Rate: {health['success_rate']}%")
            print(f"  - Avg Lock Wait: {health['avg_lock_wait_ms']}ms")
            print(f"  - Max Lock Wait: {health['max_lock_wait_ms']}ms")
        else:
            print("  - No recent join attempts")

        # Test race condition detection
        race_conditions = monitor.detect_race_conditions()
        if race_conditions:
            print(f"\n⚠️ Race Conditions Detected: {len(race_conditions)} rooms")
            for rc in race_conditions:
                print(f"  - Room {rc['room_id']}: {rc['same_slot_successes']} conflicts")
        else:
            print("\n✅ No race conditions detected")

        # Test high contention detection
        high_contention = monitor.get_high_contention_rooms(threshold_attempts=5)
        if high_contention:
            print(f"\nHigh Contention Rooms: {len(high_contention)}")
            for room in high_contention[:3]:
                print(f"  - {room['room_id']}: {room['total_attempts']} attempts")
        else:
            print("\nNo high contention rooms found")

        # Generate report
        print("\nGenerating health report...")
        report = monitor.generate_report()
        print("✅ Report generated successfully")

    except Exception as e:
        print(f"❌ Health monitor test error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test runner."""
    # Run comprehensive test suite
    test_suite = JoinRoomTestSuite()
    passed, total = await test_suite.run_all_tests()

    # Test monitoring queries
    await test_monitoring_queries()

    # Test health monitor
    await test_health_monitor()

    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Core Tests: {passed}/{total} passed")
    print("Monitoring: See results above")
    print("=" * 80 + "\n")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
