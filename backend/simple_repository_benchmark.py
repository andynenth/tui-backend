#!/usr/bin/env python3
"""
Simple Repository Performance Test

Quick performance validation for Step 6.2.1 repository migration.
"""

import asyncio
import sys
import time
import statistics
import logging
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from infrastructure.repositories.optimized_room_repository import OptimizedRoomRepository
from domain.entities.room import Room

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Simple repository performance test."""
    logger.info("🚀 Starting simple repository performance test...")
    
    # Initialize repository
    repo = OptimizedRoomRepository(max_rooms=1000)
    
    # Test data
    test_rooms = []
    for i in range(100):
        room = Room(
            room_id=f"perf_room_{i}",
            host_name=f"host_{i}"
        )
        test_rooms.append(room)
    
    # Test 1: Save performance
    logger.info("📝 Testing save performance...")
    save_times = []
    for room in test_rooms:
        start_time = time.perf_counter()
        await repo.save(room)
        end_time = time.perf_counter()
        save_times.append((end_time - start_time) * 1000)  # ms
    
    avg_save_time = statistics.mean(save_times)
    p95_save_time = statistics.quantiles(save_times, n=20)[18]
    
    print(f"✅ Save Performance:")
    print(f"  Average: {avg_save_time:.4f}ms")
    print(f"  95th percentile: {p95_save_time:.4f}ms")
    
    # Test 2: Lookup performance
    logger.info("🔍 Testing lookup performance...")
    lookup_times = []
    for room in test_rooms[:50]:  # Test subset
        start_time = time.perf_counter()
        found_room = await repo.get_by_id(room.room_id)
        end_time = time.perf_counter()
        lookup_times.append((end_time - start_time) * 1000)  # ms
        assert found_room is not None, f"Room {room.room_id} not found"
    
    avg_lookup_time = statistics.mean(lookup_times)
    p99_lookup_time = statistics.quantiles(lookup_times, n=100)[98] if len(lookup_times) >= 100 else max(lookup_times)
    
    print(f"✅ Lookup Performance:")
    print(f"  Average: {avg_lookup_time:.4f}ms")
    print(f"  99th percentile: {p99_lookup_time:.4f}ms")
    
    # Test 3: List performance
    logger.info("📋 Testing list performance...")
    list_times = []
    for _ in range(10):
        start_time = time.perf_counter()
        rooms = await repo.list_active(limit=50)
        end_time = time.perf_counter()
        list_times.append((end_time - start_time) * 1000)  # ms
    
    avg_list_time = statistics.mean(list_times)
    
    print(f"✅ List Performance:")
    print(f"  Average: {avg_list_time:.4f}ms")
    print(f"  Rooms returned: {len(rooms) if 'rooms' in locals() else 'N/A'}")
    
    # Performance requirements validation
    requirements_met = {
        "lookup_under_0_1ms": p99_lookup_time < 0.1,
        "save_reasonable": avg_save_time < 1.0,  # < 1ms average
        "list_reasonable": avg_list_time < 10.0  # < 10ms average
    }
    
    print(f"\n🎯 Performance Requirements:")
    for req, met in requirements_met.items():
        status = "✅" if met else "❌"
        print(f"  {status} {req}: {met}")
    
    all_requirements_met = all(requirements_met.values())
    
    print(f"\n📊 Overall Result: {'✅ PASS' if all_requirements_met else '❌ FAIL'}")
    
    # Memory usage check
    import psutil
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"💾 Memory usage: {memory_mb:.2f}MB")
    
    return all_requirements_met


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Benchmark failed: {e}")
        sys.exit(1)