# backend/tests/test_phase4_performance_benchmark.py

import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any
import os
import tempfile
import json

from backend.services.realtime_game_system import RealtimeGameSystem
from backend.services.event_store_v2 import EventStoreV2
from backend.api.services.event_store import EventStore


class TestPhase4PerformanceBenchmark:
    """
    Performance benchmarks for Phase 4 Real-time Cache implementation.
    
    Validates that the system meets <100ms response time targets.
    """
    
    @pytest.fixture
    async def benchmark_system(self):
        """Create optimized system for benchmarking."""
        # Configure for performance testing
        os.environ["REALTIME_CACHE_ENABLED"] = "true"
        os.environ["ASYNC_HISTORICAL_WRITES"] = "true"
        os.environ["GAME_CACHE_SIZE"] = "100"
        os.environ["GAME_CACHE_TTL"] = "3600"
        os.environ["HISTORICAL_BATCH_SIZE"] = "50"
        os.environ["HISTORICAL_BATCH_INTERVAL"] = "5.0"
        os.environ["DB_V2_PRIMARY"] = "true"
        
        system = RealtimeGameSystem()
        await system.initialize()
        
        yield system
        
        await system.shutdown()
    
    def measure_operation_time(self, times: List[float]) -> Dict[str, float]:
        """Calculate performance statistics."""
        return {
            "min_ms": min(times) * 1000,
            "max_ms": max(times) * 1000,
            "avg_ms": statistics.mean(times) * 1000,
            "median_ms": statistics.median(times) * 1000,
            "p95_ms": statistics.quantiles(times, n=20)[18] * 1000 if len(times) > 20 else max(times) * 1000,
            "p99_ms": statistics.quantiles(times, n=100)[98] * 1000 if len(times) > 100 else max(times) * 1000
        }
    
    @pytest.mark.asyncio
    async def test_cache_hit_performance(self, benchmark_system):
        """Benchmark cache hit response times."""
        print("\n=== Cache Hit Performance ===")
        
        # Pre-populate cache with test games
        for i in range(10):
            room_id = f"cache-test-{i}"
            await benchmark_system.store_game_event(
                room_id,
                "game_started",
                {
                    "players": [
                        {"player_name": f"Player{j}", "player_type": "ai"}
                        for j in range(4)
                    ],
                    "started_at": f"2024-01-01T12:{i:02d}:00"
                }
            )
        
        # Warm up
        for i in range(10):
            await benchmark_system.get_game_state(f"cache-test-{i}")
        
        # Benchmark cache hits
        times = []
        for _ in range(100):
            for i in range(10):
                start = time.time()
                state = await benchmark_system.get_game_state(f"cache-test-{i}")
                elapsed = time.time() - start
                times.append(elapsed)
                assert state is not None
        
        stats = self.measure_operation_time(times)
        print(f"Cache Hit Times: {json.dumps(stats, indent=2)}")
        
        # Verify <100ms target
        assert stats["avg_ms"] < 100, f"Average cache hit time {stats['avg_ms']:.2f}ms exceeds 100ms target"
        assert stats["p95_ms"] < 100, f"P95 cache hit time {stats['p95_ms']:.2f}ms exceeds 100ms target"
    
    @pytest.mark.asyncio
    async def test_game_state_update_performance(self, benchmark_system):
        """Benchmark game state update performance."""
        print("\n=== Game State Update Performance ===")
        
        room_id = "update-test"
        
        # Initialize game
        await benchmark_system.store_game_event(
            room_id,
            "game_started",
            {
                "players": [
                    {"player_name": f"Player{i}", "player_type": "ai"}
                    for i in range(4)
                ],
                "started_at": "2024-01-01T12:00:00"
            }
        )
        
        # Benchmark state updates
        times = []
        for i in range(100):
            start = time.time()
            await benchmark_system.store_game_event(
                room_id,
                "phase_change",
                {
                    "old_phase": "PREPARATION",
                    "new_phase": "DECLARATION",
                    "phase_data": {"turn": i}
                }
            )
            elapsed = time.time() - start
            times.append(elapsed)
        
        stats = self.measure_operation_time(times)
        print(f"State Update Times: {json.dumps(stats, indent=2)}")
        
        # Verify <100ms target for real-time events
        assert stats["avg_ms"] < 100, f"Average update time {stats['avg_ms']:.2f}ms exceeds 100ms target"
        assert stats["p95_ms"] < 150, f"P95 update time {stats['p95_ms']:.2f}ms exceeds 150ms target"
    
    @pytest.mark.asyncio
    async def test_concurrent_access_performance(self, benchmark_system):
        """Benchmark performance under concurrent load."""
        print("\n=== Concurrent Access Performance ===")
        
        async def simulate_game_session(game_id: int):
            """Simulate a complete game session."""
            room_id = f"concurrent-game-{game_id}"
            times = []
            
            # Game start
            start = time.time()
            await benchmark_system.store_game_event(
                room_id,
                "game_started",
                {
                    "players": [
                        {"player_name": f"P{i}", "player_type": "ai"}
                        for i in range(4)
                    ]
                }
            )
            times.append(time.time() - start)
            
            # Multiple phase changes
            for phase in ["PREPARATION", "DECLARATION", "TURN", "SCORING"]:
                start = time.time()
                await benchmark_system.store_game_event(
                    room_id,
                    "phase_change",
                    {"new_phase": phase}
                )
                times.append(time.time() - start)
                
                # Some reads
                start = time.time()
                await benchmark_system.get_game_state(room_id)
                times.append(time.time() - start)
            
            return times
        
        # Run concurrent game sessions
        all_times = []
        tasks = [simulate_game_session(i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        
        for times in results:
            all_times.extend(times)
        
        stats = self.measure_operation_time(all_times)
        print(f"Concurrent Access Times: {json.dumps(stats, indent=2)}")
        
        # Even under load, should maintain reasonable performance
        assert stats["avg_ms"] < 200, f"Average concurrent time {stats['avg_ms']:.2f}ms exceeds 200ms target"
        assert stats["p95_ms"] < 500, f"P95 concurrent time {stats['p95_ms']:.2f}ms exceeds 500ms target"
    
    @pytest.mark.asyncio
    async def test_historical_write_performance(self, benchmark_system):
        """Benchmark historical event writing performance."""
        print("\n=== Historical Write Performance ===")
        
        # Queue many historical events
        queue_times = []
        for i in range(1000):
            start = time.time()
            await benchmark_system.store_game_event(
                f"historical-test-{i % 10}",
                "chat_message",  # Non-critical event
                {"message": f"Test message {i}", "timestamp": time.time()},
                priority=False
            )
            elapsed = time.time() - start
            queue_times.append(elapsed)
        
        queue_stats = self.measure_operation_time(queue_times)
        print(f"Historical Queue Times: {json.dumps(queue_stats, indent=2)}")
        
        # Queueing should be very fast
        assert queue_stats["avg_ms"] < 10, f"Average queue time {queue_stats['avg_ms']:.2f}ms exceeds 10ms target"
        
        # Wait for batch processing
        await asyncio.sleep(6)  # Wait for batch interval
        
        # Check writer metrics
        writer_metrics = benchmark_system.historical_writer.get_metrics()
        print(f"\nHistorical Writer Metrics: {json.dumps(writer_metrics, indent=2)}")
        
        assert writer_metrics["batches_written"] > 0
        assert writer_metrics["write_errors"] == 0
    
    @pytest.mark.asyncio
    async def test_cache_memory_efficiency(self, benchmark_system):
        """Test memory efficiency of the cache."""
        print("\n=== Cache Memory Efficiency ===")
        
        # Fill cache to capacity
        cache_size = 50
        benchmark_system.cached_store.cache.max_size = cache_size
        
        for i in range(cache_size * 2):  # Double the capacity
            await benchmark_system.store_game_event(
                f"memory-test-{i}",
                "game_started",
                {
                    "players": [{"player_name": f"P{j}", "player_type": "ai"} for j in range(4)],
                    "round_data": {"round": 1, "scores": {f"P{j}": 0 for j in range(4)}},
                    "metadata": {"created": time.time(), "index": i}
                }
            )
        
        # Check cache metrics
        cache_metrics = benchmark_system.cached_store.cache.get_metrics()
        print(f"Cache Metrics: {json.dumps(cache_metrics, indent=2)}")
        
        # Cache should respect size limit
        assert cache_metrics["size"] <= cache_size
        assert cache_metrics["evictions"] >= cache_size  # Should have evicted older entries
    
    @pytest.mark.asyncio
    async def test_recovery_performance(self, benchmark_system):
        """Benchmark game recovery performance."""
        print("\n=== Game Recovery Performance ===")
        
        # Create test games
        for i in range(10):
            room_id = f"recovery-test-{i}"
            await benchmark_system.store_game_event(
                room_id,
                "game_started",
                {
                    "players": [{"player_name": f"P{j}", "player_type": "ai"} for j in range(4)],
                    "started_at": f"2024-01-01T12:{i:02d}:00"
                }
            )
        
        # Benchmark recovery from cache
        cache_times = []
        for i in range(10):
            start = time.time()
            game = await benchmark_system.recover_game(f"recovery-test-{i}")
            elapsed = time.time() - start
            if game:  # Only count successful recoveries
                cache_times.append(elapsed)
        
        if cache_times:
            stats = self.measure_operation_time(cache_times)
            print(f"Recovery Times (from cache): {json.dumps(stats, indent=2)}")
            
            # Recovery from cache should be fast
            assert stats["avg_ms"] < 100, f"Average recovery time {stats['avg_ms']:.2f}ms exceeds 100ms target"
    
    @pytest.mark.asyncio
    async def test_phase4_target_metrics(self, benchmark_system):
        """Verify Phase 4 meets all target metrics."""
        print("\n=== Phase 4 Target Metrics Validation ===")
        
        # Simulate realistic game load
        game_count = 20
        operations_per_game = 50
        
        all_response_times = []
        
        # Create games and simulate operations
        for game_id in range(game_count):
            room_id = f"target-test-{game_id}"
            
            # Game creation
            start = time.time()
            await benchmark_system.store_game_event(
                room_id,
                "game_started",
                {"players": [{"player_name": f"P{i}", "player_type": "ai"} for i in range(4)]}
            )
            all_response_times.append(time.time() - start)
            
            # Simulate game operations
            for op in range(operations_per_game):
                # Mix of reads and writes
                if op % 3 == 0:
                    # Read operation
                    start = time.time()
                    await benchmark_system.get_game_state(room_id)
                    all_response_times.append(time.time() - start)
                else:
                    # Write operation
                    start = time.time()
                    await benchmark_system.store_game_event(
                        room_id,
                        "player_action" if op % 5 != 0 else "phase_change",
                        {"action": f"op_{op}", "timestamp": time.time()}
                    )
                    all_response_times.append(time.time() - start)
        
        # Calculate final metrics
        final_stats = self.measure_operation_time(all_response_times)
        print(f"\nFinal Performance Metrics:")
        print(f"  - Average Response Time: {final_stats['avg_ms']:.2f}ms")
        print(f"  - P95 Response Time: {final_stats['p95_ms']:.2f}ms")
        print(f"  - P99 Response Time: {final_stats['p99_ms']:.2f}ms")
        
        # Get system metrics
        system_metrics = benchmark_system.get_metrics()
        cache_metrics = system_metrics.get("event_store", {}).get("cache_metrics", {})
        
        print(f"\nCache Performance:")
        print(f"  - Cache Hit Rate: {cache_metrics.get('hit_rate', 0):.2%}")
        print(f"  - Cache Size: {cache_metrics.get('size', 0)}/{cache_metrics.get('max_size', 0)}")
        
        # Verify Phase 4 targets
        assert final_stats["avg_ms"] < 100, "Phase 4 target: <100ms average response time"
        assert final_stats["p95_ms"] < 200, "Phase 4 target: <200ms P95 response time"
        assert cache_metrics.get("hit_rate", 0) > 0.7, "Phase 4 target: >70% cache hit rate"
        
        print("\n✅ Phase 4 Performance Targets ACHIEVED!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])