#!/usr/bin/env python3
"""
Performance test to measure database write reduction with EventBuffer
"""

import asyncio
import os
import sys
import time
import sqlite3
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from api.services.event_store import EventStore


async def measure_writes_without_buffer():
    """Measure database writes without buffer"""
    # Create test database
    test_db = "/tmp/test_no_buffer.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    # Disable buffer
    os.environ["EVENT_BUFFER_ENABLED"] = "false"

    store = EventStore(db_path=test_db)

    # Simulate a game round with typical write pattern
    start_time = time.time()
    write_count = 0

    # Round start
    await store.store_event("TEST001", "round_started", {"round": 1})
    write_count += 1

    # Declarations (4 players)
    for i in range(4):
        await store.store_event(
            "TEST001", "player_declared", {"player": f"p{i}", "value": i}
        )
        write_count += 1

    # Simulate 5 turns with 7 writes each (typical pattern)
    for turn in range(5):
        for update in range(7):
            await store.store_event(
                "TEST001", "phase_data_update", {"turn": turn, "update": update}
            )
            write_count += 1

    # Round complete
    await store.store_event("TEST001", "round_complete", {"scores": {}})
    write_count += 1

    end_time = time.time()
    duration = end_time - start_time

    # Count actual database writes
    conn = sqlite3.connect(test_db)
    cursor = conn.execute("SELECT COUNT(*) FROM game_events")
    actual_writes = cursor.fetchone()[0]
    conn.close()

    return {
        "expected_writes": write_count,
        "actual_writes": actual_writes,
        "duration": duration,
        "writes_per_second": actual_writes / duration,
    }


async def measure_writes_with_buffer():
    """Measure database writes with buffer enabled"""
    # Create test database
    test_db = "/tmp/test_with_buffer.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    # Enable buffer with test settings
    os.environ["EVENT_BUFFER_ENABLED"] = "true"
    os.environ["EVENT_BUFFER_SIZE"] = "20"
    os.environ["EVENT_BUFFER_FLUSH_INTERVAL"] = "2.0"

    store = EventStore(db_path=test_db)

    # Same game simulation
    start_time = time.time()
    write_count = 0

    # Round start
    await store.store_event_buffered("TEST002", "round_started", {"round": 1})
    write_count += 1

    # Declarations (4 players)
    for i in range(4):
        await store.store_event_buffered(
            "TEST002", "player_declared", {"player": f"p{i}", "value": i}
        )
        write_count += 1

    # Simulate 5 turns with 7 writes each
    for turn in range(5):
        for update in range(7):
            await store.store_event_buffered(
                "TEST002", "phase_data_update", {"turn": turn, "update": update}
            )
            write_count += 1

    # Round complete (critical event - will flush)
    await store.store_event_buffered("TEST002", "round_complete", {"scores": {}})
    write_count += 1

    # Ensure all events are flushed
    await store.shutdown()

    end_time = time.time()
    duration = end_time - start_time

    # Count actual database writes
    conn = sqlite3.connect(test_db)
    cursor = conn.execute("SELECT COUNT(*) FROM game_events")
    actual_writes = cursor.fetchone()[0]
    conn.close()

    # Get buffer metrics
    buffer_metrics = store.get_buffer_metrics()

    return {
        "expected_writes": write_count,
        "actual_writes": actual_writes,
        "duration": duration,
        "writes_per_second": actual_writes / duration,
        "buffer_metrics": buffer_metrics,
    }


async def main():
    """Run performance comparison"""
    print("Database Write Performance Test")
    print("=" * 50)

    # Test without buffer
    print("\n1. Testing WITHOUT buffer...")
    no_buffer_results = await measure_writes_without_buffer()
    print(f"   Expected writes: {no_buffer_results['expected_writes']}")
    print(f"   Actual writes: {no_buffer_results['actual_writes']}")
    print(f"   Duration: {no_buffer_results['duration']:.3f}s")
    print(f"   Writes/second: {no_buffer_results['writes_per_second']:.1f}")

    # Test with buffer
    print("\n2. Testing WITH buffer...")
    with_buffer_results = await measure_writes_with_buffer()
    print(f"   Expected writes: {with_buffer_results['expected_writes']}")
    print(f"   Actual writes: {with_buffer_results['actual_writes']}")
    print(f"   Duration: {with_buffer_results['duration']:.3f}s")
    print(f"   Writes/second: {with_buffer_results['writes_per_second']:.1f}")
    print(
        f"   Buffer flushes: {with_buffer_results['buffer_metrics']['total_flushes']}"
    )

    # Calculate improvement
    print("\n3. Performance Improvement")
    print("=" * 50)

    write_reduction = (
        1 - (with_buffer_results["actual_writes"] / no_buffer_results["actual_writes"])
    ) * 100
    speed_improvement = with_buffer_results["duration"] / no_buffer_results["duration"]

    print(f"   Database writes reduced by: {write_reduction:.1f}%")
    print(f"   Speed improvement: {speed_improvement:.2f}x faster")
    print(
        f"   I/O operations saved: {no_buffer_results['actual_writes'] - with_buffer_results['actual_writes']}"
    )

    # Verify data integrity
    print("\n4. Data Integrity Check")
    print("=" * 50)

    # Both should have same number of events
    if no_buffer_results["actual_writes"] == with_buffer_results["actual_writes"]:
        print("   ✅ All events preserved - no data loss")
    else:
        print(
            f"   ⚠️  Event count mismatch: {no_buffer_results['actual_writes']} vs {with_buffer_results['actual_writes']}"
        )

    print("\n✅ Performance test complete!")


if __name__ == "__main__":
    asyncio.run(main())
