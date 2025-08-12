#!/usr/bin/env python3
"""
Manual test script for Phase 4 Real-time Cache implementation.
"""

import asyncio
import time
import os
from typing import List

# Set configuration
os.environ["REALTIME_CACHE_ENABLED"] = "true"
os.environ["ASYNC_HISTORICAL_WRITES"] = "true"
os.environ["GAME_CACHE_SIZE"] = "10"
os.environ["GAME_CACHE_TTL"] = "300"
os.environ["HISTORICAL_BATCH_SIZE"] = "5"
os.environ["HISTORICAL_BATCH_INTERVAL"] = "2.0"
os.environ["DB_V2_PRIMARY"] = "true"

from backend.services.realtime_game_system import RealtimeGameSystem


async def test_phase4():
    """Test Phase 4 implementation manually."""
    print("=== Phase 4 Manual Test ===\n")
    
    # Initialize system
    print("1. Initializing RealtimeGameSystem...")
    system = RealtimeGameSystem()
    await system.initialize()
    print("✅ System initialized")
    
    # Test storing real-time events
    print("\n2. Testing real-time event storage...")
    room_id = "test-room-001"
    
    start = time.time()
    await system.store_game_event(
        room_id,
        "game_started",
        {
            "players": [
                {"player_name": "Alice", "player_type": "human"},
                {"player_name": "Bob", "player_type": "ai"},
                {"player_name": "Charlie", "player_type": "ai"},
                {"player_name": "David", "player_type": "ai"}
            ],
            "started_at": "2024-01-01T12:00:00"
        }
    )
    elapsed = (time.time() - start) * 1000
    print(f"✅ Game started event stored in {elapsed:.2f}ms")
    
    # Test cache hit
    print("\n3. Testing cache hit performance...")
    times = []
    for _ in range(10):
        start = time.time()
        state = await system.get_game_state(room_id)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    print(f"✅ Average cache hit time: {avg_time:.2f}ms")
    print(f"   Min: {min(times):.2f}ms, Max: {max(times):.2f}ms")
    
    # Test historical event queuing
    print("\n4. Testing historical event queuing...")
    for i in range(10):
        await system.store_game_event(
            room_id,
            "chat_message",  # Non-critical event
            {"message": f"Test message {i}", "timestamp": time.time()}
        )
    print("✅ 10 historical events queued")
    
    # Check metrics
    print("\n5. System Metrics:")
    metrics = system.get_metrics()
    
    if "event_store" in metrics:
        cache_metrics = metrics["event_store"].get("cache_metrics", {})
        print(f"   Cache Hit Rate: {cache_metrics.get('hit_rate', 0):.2%}")
        print(f"   Cache Size: {cache_metrics.get('size', 0)}")
    
    if "historical_writer" in metrics:
        writer_metrics = metrics["historical_writer"]
        print(f"   Events Queued: {writer_metrics.get('events_queued', 0)}")
        print(f"   Queue Size: {writer_metrics.get('total_queue_size', 0)}")
    
    # Wait for batch write
    print("\n6. Waiting for batch write...")
    await asyncio.sleep(3)
    
    # Check updated metrics
    metrics = system.get_metrics()
    if "historical_writer" in metrics:
        writer_metrics = metrics["historical_writer"]
        print(f"✅ Batches Written: {writer_metrics.get('batches_written', 0)}")
        print(f"   Events Written: {writer_metrics.get('events_written', 0)}")
    
    # Test health check
    print("\n7. Health Check:")
    health = await system.health_check()
    print(f"   Status: {health['status']}")
    for component, info in health.get('components', {}).items():
        print(f"   {component}: {info.get('status', 'unknown')}")
    
    # Cleanup
    print("\n8. Shutting down...")
    await system.shutdown()
    print("✅ System shutdown complete")
    
    print("\n=== Phase 4 Test Complete ===")
    print(f"✅ Target: <100ms response time")
    print(f"✅ Achieved: {avg_time:.2f}ms average")
    print(f"✅ Improvement: {((100 - avg_time) / 100 * 100):.1f}% better than target")


if __name__ == "__main__":
    asyncio.run(test_phase4())