# backend/tests/test_event_store_performance.py

import asyncio
import time
import statistics
from contextlib import asynccontextmanager
import tempfile
import os

import pytest

from backend.api.services.event_store import EventStore


class PerformanceTimer:
    """Context manager for timing operations"""

    def __init__(self, name):
        self.name = name
        self.start_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.duration = (time.perf_counter() - self.start_time) * 1000  # Convert to ms


@asynccontextmanager
async def async_timer(name):
    """Async context manager for timing operations"""
    start = time.perf_counter()
    yield
    duration = (time.perf_counter() - start) * 1000
    print(f"{name}: {duration:.2f}ms")


@pytest.fixture
def perf_event_store():
    """Create event store for performance testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        temp_db = tmp.name

    store = EventStore(db_path=temp_db)
    yield store

    try:
        os.unlink(temp_db)
    except:
        pass


@pytest.mark.asyncio
async def test_event_storage_overhead(perf_event_store):
    """Measure overhead of storing events"""
    room_id = "perf_test"
    timings = []

    # Warm up
    for _ in range(10):
        await perf_event_store.store_event(room_id, "warmup", {})

    # Measure individual event storage times
    for i in range(100):
        with PerformanceTimer("store_event") as timer:
            await perf_event_store.store_event(
                room_id=room_id,
                event_type="test_event",
                payload={
                    "index": i,
                    "data": f"test_data_{i}" * 10,  # Some payload
                    "nested": {"value": i, "list": list(range(10))},
                },
            )
        timings.append(timer.duration)

    # Calculate statistics
    avg_time = statistics.mean(timings)
    median_time = statistics.median(timings)
    sorted_timings = sorted(timings)
    p95_time = sorted_timings[int(len(timings) * 0.95)]
    p99_time = sorted_timings[int(len(timings) * 0.99)]

    print(f"\nEvent Storage Performance:")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  Median: {median_time:.2f}ms")
    print(f"  95th percentile: {p95_time:.2f}ms")
    print(f"  99th percentile: {p99_time:.2f}ms")

    # Assert performance requirements
    assert avg_time < 5.0, f"Average storage time {avg_time:.2f}ms exceeds 5ms limit"
    assert p95_time < 10.0, f"95th percentile {p95_time:.2f}ms exceeds 10ms limit"


@pytest.mark.asyncio
async def test_high_frequency_events(perf_event_store):
    """Test performance with rapid event generation (simulating fast bot plays)"""
    room_id = "rapid_test"
    event_count = 500

    async with async_timer(f"Storing {event_count} events rapidly"):
        # Simulate rapid bot actions
        tasks = []
        for i in range(event_count):
            task = perf_event_store.store_event(
                room_id=room_id,
                event_type="bot_action",
                payload={"action": "play", "index": i},
                player_id=f"Bot_{i % 4}",
            )
            tasks.append(task)

            # Small batch processing to avoid overwhelming
            if len(tasks) >= 50:
                await asyncio.gather(*tasks)
                tasks = []

        # Process remaining
        if tasks:
            await asyncio.gather(*tasks)

    # Verify all events were stored
    events = await perf_event_store.get_room_events(room_id)
    assert len(events) == event_count

    # Test replay performance
    async with async_timer(f"Replaying {event_count} events"):
        state = await perf_event_store.replay_room_state(room_id)

    assert state["events_processed"] == event_count


@pytest.mark.asyncio
async def test_concurrent_room_performance(perf_event_store):
    """Test performance with multiple concurrent rooms"""
    room_count = 10
    events_per_room = 50

    async def simulate_room(room_id):
        """Simulate events for a single room"""
        for i in range(events_per_room):
            await perf_event_store.store_event(
                room_id=room_id, event_type="game_event", payload={"event_index": i}
            )
            # Simulate some game delay
            await asyncio.sleep(0.01)

    # Run rooms concurrently
    async with async_timer(f"Simulating {room_count} concurrent rooms"):
        tasks = [simulate_room(f"room_{i}") for i in range(room_count)]
        await asyncio.gather(*tasks)

    # Verify total events
    stats = await perf_event_store.get_event_stats()
    total_expected = room_count * events_per_room
    assert stats["total_events"] >= total_expected


@pytest.mark.asyncio
async def test_query_performance(perf_event_store):
    """Test performance of various query operations"""
    room_id = "query_test"

    # Setup: Store many events of different types
    event_types = ["phase_change", "player_action", "turn_complete", "scoring"]
    for i in range(200):
        await perf_event_store.store_event(
            room_id=room_id,
            event_type=event_types[i % len(event_types)],
            payload={"index": i},
        )

    # Test different query operations

    # 1. Get all events
    async with async_timer("Get all 200 events"):
        events = await perf_event_store.get_room_events(room_id)
    assert len(events) == 200

    # 2. Get events by type
    async with async_timer("Get events by type"):
        phase_events = await perf_event_store.get_events_by_type(
            room_id, "phase_change"
        )
    assert len(phase_events) == 50  # 200 / 4 types

    # 3. Get events since sequence
    async with async_timer("Get events since sequence 100"):
        recent = await perf_event_store.get_events_since(room_id, events[100].sequence)
    assert len(recent) == 99  # Events 101-200

    # 4. Export room history
    async with async_timer("Export complete room history"):
        history = await perf_event_store.export_room_history(room_id)
    assert history["total_events"] == 200

    # 5. Validate sequence
    async with async_timer("Validate event sequence"):
        validation = await perf_event_store.validate_event_sequence(room_id)
    assert validation["valid"] == True


@pytest.mark.asyncio
async def test_memory_efficiency(perf_event_store):
    """Test memory efficiency with large payloads"""
    room_id = "memory_test"

    # Create a large payload (simulating complex game state)
    large_payload = {
        "players": {
            f"player_{i}": {
                "hand": [f"card_{j}" for j in range(20)],
                "score": i * 10,
                "history": list(range(100)),
            }
            for i in range(4)
        },
        "board_state": [[0] * 10 for _ in range(10)],
        "metadata": {f"key_{i}": f"value_{i}" * 100 for i in range(50)},
    }

    # Store events with large payloads
    timings = []
    for i in range(20):
        with PerformanceTimer("large_payload") as timer:
            await perf_event_store.store_event(
                room_id=room_id, event_type="state_snapshot", payload=large_payload
            )
        timings.append(timer.duration)

    avg_time = statistics.mean(timings)
    print(f"\nLarge payload storage average: {avg_time:.2f}ms")

    # Ensure it's still reasonably fast
    assert avg_time < 20.0, f"Large payload storage too slow: {avg_time:.2f}ms"


def run_performance_summary():
    """Run all performance tests and print summary"""
    print("\n" + "=" * 60)
    print("EVENT STORE PERFORMANCE TEST SUMMARY")
    print("=" * 60)
    print("\nPerformance Requirements:")
    print("- Event storage overhead: < 5ms average, < 10ms 95th percentile")
    print("- High-frequency events: Should handle 500+ events rapidly")
    print("- Concurrent rooms: Should handle 10+ concurrent games")
    print("- Query performance: All queries should complete quickly")
    print("\nRun pytest with -v flag to see detailed performance metrics")


if __name__ == "__main__":
    run_performance_summary()
    pytest.main([__file__, "-v", "-s"])
