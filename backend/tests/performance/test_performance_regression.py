"""
Performance regression tests for state persistence.

These tests ensure that state persistence features don't degrade
performance beyond acceptable thresholds.
"""

import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any, Callable
from datetime import datetime

from infrastructure.state_persistence.manager import StatePersistenceManager
from infrastructure.state_persistence.config import PersistenceConfig, PersistenceStrategy
from infrastructure.feature_flags import feature_flags
from domain.use_cases.start_game import StartGameUseCase
from domain.use_cases.play_turn import PlayTurnUseCase


class PerformanceThresholds:
    """Performance thresholds for regression testing."""
    
    # Maximum acceptable latency increase (percentage)
    MAX_LATENCY_INCREASE_PERCENT = 15.0
    
    # Maximum acceptable P99 latency (milliseconds)
    MAX_P99_LATENCY_MS = {
        "save_state": 50,
        "load_state": 30,
        "create_snapshot": 100,
        "restore_snapshot": 80,
        "use_case_execution": 150
    }
    
    # Minimum acceptable throughput (operations per second)
    MIN_THROUGHPUT_OPS = {
        "save_state": 1000,
        "load_state": 2000,
        "state_transitions": 500
    }
    
    # Maximum memory overhead (MB)
    MAX_MEMORY_OVERHEAD_MB = 100


class PerformanceMeasurement:
    """Helper class for performance measurements."""
    
    def __init__(self, name: str):
        self.name = name
        self.samples: List[float] = []
        
    def add_sample(self, duration_ms: float):
        """Add a latency sample."""
        self.samples.append(duration_ms)
        
    @property
    def count(self) -> int:
        return len(self.samples)
        
    @property
    def mean(self) -> float:
        return statistics.mean(self.samples) if self.samples else 0
        
    @property
    def p50(self) -> float:
        return statistics.median(self.samples) if self.samples else 0
        
    @property
    def p99(self) -> float:
        if not self.samples:
            return 0
        sorted_samples = sorted(self.samples)
        index = int(len(sorted_samples) * 0.99)
        return sorted_samples[min(index, len(sorted_samples) - 1)]
        
    @property
    def throughput(self) -> float:
        """Calculate operations per second."""
        if not self.samples:
            return 0
        total_time_seconds = sum(self.samples) / 1000  # Convert to seconds
        return self.count / total_time_seconds if total_time_seconds > 0 else 0


@pytest.fixture
def performance_manager():
    """Create performance test manager."""
    config = PersistenceConfig(
        strategy=PersistenceStrategy.HYBRID,
        enable_compression=True,
        enable_encryption=False  # Disable for performance tests
    )
    return StatePersistenceManager(config)


async def measure_operation(
    operation: Callable,
    samples: int = 100,
    warmup: int = 10
) -> PerformanceMeasurement:
    """
    Measure performance of an operation.
    
    Args:
        operation: Async function to measure
        samples: Number of samples to collect
        warmup: Number of warmup iterations
        
    Returns:
        Performance measurement
    """
    measurement = PerformanceMeasurement(operation.__name__)
    
    # Warmup
    for _ in range(warmup):
        await operation()
        
    # Collect samples
    for _ in range(samples):
        start = time.perf_counter()
        await operation()
        end = time.perf_counter()
        
        duration_ms = (end - start) * 1000
        measurement.add_sample(duration_ms)
        
    return measurement


class TestStatePersistencePerformance:
    """Performance regression tests for state persistence."""
    
    @pytest.mark.performance
    async def test_save_state_performance(self, performance_manager):
        """Test state saving performance."""
        # Prepare test data
        test_state = {
            "game_id": "perf-test-123",
            "players": ["player1", "player2", "player3", "player4"],
            "deck": list(range(52)),
            "scores": {"player1": 10, "player2": 20, "player3": 15, "player4": 5},
            "metadata": {"timestamp": datetime.utcnow().isoformat()}
        }
        
        async def save_operation():
            await performance_manager.save_state("test-state", test_state)
            
        # Measure performance
        measurement = await measure_operation(save_operation, samples=100)
        
        # Assert thresholds
        assert measurement.p99 < PerformanceThresholds.MAX_P99_LATENCY_MS["save_state"], \
            f"Save state P99 latency {measurement.p99:.2f}ms exceeds threshold"
            
        assert measurement.throughput > PerformanceThresholds.MIN_THROUGHPUT_OPS["save_state"], \
            f"Save state throughput {measurement.throughput:.2f} ops/s below threshold"
            
        print(f"\nSave State Performance:")
        print(f"  Mean: {measurement.mean:.2f} ms")
        print(f"  P50: {measurement.p50:.2f} ms")
        print(f"  P99: {measurement.p99:.2f} ms")
        print(f"  Throughput: {measurement.throughput:.2f} ops/s")
        
    @pytest.mark.performance
    async def test_load_state_performance(self, performance_manager):
        """Test state loading performance."""
        # Prepare test data
        state_id = "load-test-state"
        test_state = {
            "game_id": "perf-test-456",
            "data": "x" * 1000  # 1KB of data
        }
        
        # Save state first
        await performance_manager.save_state(state_id, test_state)
        
        async def load_operation():
            await performance_manager.load_state(state_id)
            
        # Measure performance
        measurement = await measure_operation(load_operation, samples=100)
        
        # Assert thresholds
        assert measurement.p99 < PerformanceThresholds.MAX_P99_LATENCY_MS["load_state"], \
            f"Load state P99 latency {measurement.p99:.2f}ms exceeds threshold"
            
        assert measurement.throughput > PerformanceThresholds.MIN_THROUGHPUT_OPS["load_state"], \
            f"Load state throughput {measurement.throughput:.2f} ops/s below threshold"
            
        print(f"\nLoad State Performance:")
        print(f"  Mean: {measurement.mean:.2f} ms")
        print(f"  P50: {measurement.p50:.2f} ms")
        print(f"  P99: {measurement.p99:.2f} ms")
        print(f"  Throughput: {measurement.throughput:.2f} ops/s")
        
    @pytest.mark.performance
    async def test_snapshot_performance(self, performance_manager):
        """Test snapshot creation and restoration performance."""
        # Prepare test data
        state_id = "snapshot-test"
        test_state = {
            "game_id": "snap-test",
            "board": [[0] * 10 for _ in range(10)],  # 10x10 board
            "history": list(range(100))  # 100 moves
        }
        
        await performance_manager.save_state(state_id, test_state)
        
        # Test snapshot creation
        async def create_snapshot():
            if hasattr(performance_manager, 'create_snapshot'):
                await performance_manager.create_snapshot(state_id)
                
        create_measurement = await measure_operation(create_snapshot, samples=50)
        
        # Test snapshot restoration
        async def restore_snapshot():
            if hasattr(performance_manager, 'restore_latest_snapshot'):
                await performance_manager.restore_latest_snapshot(state_id)
                
        restore_measurement = await measure_operation(restore_snapshot, samples=50)
        
        # Assert thresholds
        assert create_measurement.p99 < PerformanceThresholds.MAX_P99_LATENCY_MS["create_snapshot"], \
            f"Create snapshot P99 latency {create_measurement.p99:.2f}ms exceeds threshold"
            
        assert restore_measurement.p99 < PerformanceThresholds.MAX_P99_LATENCY_MS["restore_snapshot"], \
            f"Restore snapshot P99 latency {restore_measurement.p99:.2f}ms exceeds threshold"
            
        print(f"\nSnapshot Performance:")
        print(f"  Create - Mean: {create_measurement.mean:.2f} ms, P99: {create_measurement.p99:.2f} ms")
        print(f"  Restore - Mean: {restore_measurement.mean:.2f} ms, P99: {restore_measurement.p99:.2f} ms")
        
    @pytest.mark.performance
    async def test_concurrent_access_performance(self, performance_manager):
        """Test performance under concurrent access."""
        num_concurrent = 10
        operations_per_task = 20
        
        async def concurrent_operations(task_id: int):
            """Simulate concurrent state operations."""
            latencies = []
            
            for i in range(operations_per_task):
                state_id = f"concurrent-{task_id}-{i}"
                state_data = {"task": task_id, "operation": i}
                
                # Save
                start = time.perf_counter()
                await performance_manager.save_state(state_id, state_data)
                save_latency = (time.perf_counter() - start) * 1000
                
                # Load
                start = time.perf_counter()
                await performance_manager.load_state(state_id)
                load_latency = (time.perf_counter() - start) * 1000
                
                latencies.extend([save_latency, load_latency])
                
            return latencies
            
        # Run concurrent tasks
        start_time = time.perf_counter()
        
        tasks = [
            concurrent_operations(i)
            for i in range(num_concurrent)
        ]
        
        results = await asyncio.gather(*tasks)
        
        total_time = time.perf_counter() - start_time
        
        # Analyze results
        all_latencies = [lat for result in results for lat in result]
        mean_latency = statistics.mean(all_latencies)
        p99_latency = sorted(all_latencies)[int(len(all_latencies) * 0.99)]
        
        total_operations = num_concurrent * operations_per_task * 2  # save + load
        throughput = total_operations / total_time
        
        print(f"\nConcurrent Access Performance:")
        print(f"  Concurrent Tasks: {num_concurrent}")
        print(f"  Total Operations: {total_operations}")
        print(f"  Mean Latency: {mean_latency:.2f} ms")
        print(f"  P99 Latency: {p99_latency:.2f} ms")
        print(f"  Throughput: {throughput:.2f} ops/s")
        
        # Assert reasonable performance under load
        assert p99_latency < 200, f"P99 latency {p99_latency:.2f}ms too high under concurrent load"
        assert throughput > 100, f"Throughput {throughput:.2f} ops/s too low under concurrent load"
        
    @pytest.mark.performance
    @pytest.mark.integration
    async def test_use_case_performance_impact(self):
        """Test performance impact on actual use cases."""
        # Test with and without state persistence
        
        async def measure_use_case_performance(enabled: bool) -> Dict[str, float]:
            """Measure use case performance with/without persistence."""
            # Toggle feature flag
            original_value = feature_flags._flags.get("use_state_persistence", False)
            feature_flags._flags["use_state_persistence"] = enabled
            
            try:
                # Create use case instances
                start_game_use_case = StartGameUseCase()
                play_turn_use_case = PlayTurnUseCase()
                
                # Measure StartGame
                async def start_game_op():
                    await start_game_use_case.execute(
                        room_id="perf-room",
                        players=["p1", "p2", "p3", "p4"]
                    )
                    
                start_game_perf = await measure_operation(start_game_op, samples=50)
                
                # Measure PlayTurn
                game_id = "perf-game"
                
                async def play_turn_op():
                    await play_turn_use_case.execute(
                        game_id=game_id,
                        player_id="p1",
                        card={"suit": "hearts", "rank": "7"}
                    )
                    
                play_turn_perf = await measure_operation(play_turn_op, samples=50)
                
                return {
                    "start_game_mean": start_game_perf.mean,
                    "start_game_p99": start_game_perf.p99,
                    "play_turn_mean": play_turn_perf.mean,
                    "play_turn_p99": play_turn_perf.p99
                }
                
            finally:
                # Restore original value
                feature_flags._flags["use_state_persistence"] = original_value
                
        # Measure baseline (without persistence)
        baseline_metrics = await measure_use_case_performance(False)
        
        # Measure with persistence
        persistence_metrics = await measure_use_case_performance(True)
        
        # Calculate impact
        start_game_impact = (
            (persistence_metrics["start_game_mean"] - baseline_metrics["start_game_mean"]) 
            / baseline_metrics["start_game_mean"] * 100
        )
        
        play_turn_impact = (
            (persistence_metrics["play_turn_mean"] - baseline_metrics["play_turn_mean"]) 
            / baseline_metrics["play_turn_mean"] * 100
        )
        
        print(f"\nUse Case Performance Impact:")
        print(f"  StartGame:")
        print(f"    Baseline: {baseline_metrics['start_game_mean']:.2f} ms (P99: {baseline_metrics['start_game_p99']:.2f} ms)")
        print(f"    With Persistence: {persistence_metrics['start_game_mean']:.2f} ms (P99: {persistence_metrics['start_game_p99']:.2f} ms)")
        print(f"    Impact: {start_game_impact:+.1f}%")
        print(f"  PlayTurn:")
        print(f"    Baseline: {baseline_metrics['play_turn_mean']:.2f} ms (P99: {baseline_metrics['play_turn_p99']:.2f} ms)")
        print(f"    With Persistence: {persistence_metrics['play_turn_mean']:.2f} ms (P99: {persistence_metrics['play_turn_p99']:.2f} ms)")
        print(f"    Impact: {play_turn_impact:+.1f}%")
        
        # Assert impact is within acceptable range
        assert start_game_impact < PerformanceThresholds.MAX_LATENCY_INCREASE_PERCENT, \
            f"StartGame latency increase {start_game_impact:.1f}% exceeds threshold"
            
        assert play_turn_impact < PerformanceThresholds.MAX_LATENCY_INCREASE_PERCENT, \
            f"PlayTurn latency increase {play_turn_impact:.1f}% exceeds threshold"
            
        # Assert P99 thresholds
        assert persistence_metrics["start_game_p99"] < PerformanceThresholds.MAX_P99_LATENCY_MS["use_case_execution"], \
            f"StartGame P99 {persistence_metrics['start_game_p99']:.2f}ms exceeds threshold"
            
        assert persistence_metrics["play_turn_p99"] < PerformanceThresholds.MAX_P99_LATENCY_MS["use_case_execution"], \
            f"PlayTurn P99 {persistence_metrics['play_turn_p99']:.2f}ms exceeds threshold"


@pytest.mark.performance
class TestMemoryPerformance:
    """Test memory usage and performance."""
    
    async def test_memory_overhead(self, performance_manager):
        """Test memory overhead of state persistence."""
        import psutil
        import gc
        
        # Force garbage collection
        gc.collect()
        
        # Get baseline memory
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create many state entries
        num_states = 1000
        state_size = 1024  # 1KB per state
        
        for i in range(num_states):
            state_data = {
                "id": i,
                "data": "x" * state_size,
                "metadata": {"index": i, "timestamp": time.time()}
            }
            await performance_manager.save_state(f"memory-test-{i}", state_data)
            
        # Force garbage collection
        gc.collect()
        
        # Measure memory after
        after_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_overhead = after_memory - baseline_memory
        
        print(f"\nMemory Performance:")
        print(f"  Baseline Memory: {baseline_memory:.2f} MB")
        print(f"  After {num_states} States: {after_memory:.2f} MB")
        print(f"  Memory Overhead: {memory_overhead:.2f} MB")
        print(f"  Per-State Overhead: {memory_overhead / num_states * 1024:.2f} KB")
        
        # Assert memory overhead is reasonable
        assert memory_overhead < PerformanceThresholds.MAX_MEMORY_OVERHEAD_MB, \
            f"Memory overhead {memory_overhead:.2f} MB exceeds threshold"
            
        # Cleanup
        for i in range(num_states):
            if hasattr(performance_manager, 'delete_state'):
                await performance_manager.delete_state(f"memory-test-{i}")


# Performance benchmark runner
async def run_performance_benchmarks():
    """Run all performance benchmarks and generate report."""
    print("🏃 Running State Persistence Performance Benchmarks")
    print("=" * 60)
    
    # Create test instance
    test_suite = TestStatePersistencePerformance()
    memory_suite = TestMemoryPerformance()
    
    # Create manager
    config = PersistenceConfig(strategy=PersistenceStrategy.HYBRID)
    manager = StatePersistenceManager(config)
    
    # Run tests
    results = {}
    
    try:
        # Basic operations
        print("\n📊 Testing Basic Operations...")
        await test_suite.test_save_state_performance(manager)
        await test_suite.test_load_state_performance(manager)
        
        # Snapshots
        print("\n📸 Testing Snapshot Operations...")
        await test_suite.test_snapshot_performance(manager)
        
        # Concurrent access
        print("\n🔄 Testing Concurrent Access...")
        await test_suite.test_concurrent_access_performance(manager)
        
        # Use case impact
        print("\n🎮 Testing Use Case Impact...")
        await test_suite.test_use_case_performance_impact()
        
        # Memory performance
        print("\n💾 Testing Memory Performance...")
        await memory_suite.test_memory_overhead(manager)
        
        print("\n✅ All performance benchmarks passed!")
        
    except AssertionError as e:
        print(f"\n❌ Performance regression detected: {e}")
        raise
        
    except Exception as e:
        print(f"\n❌ Benchmark error: {e}")
        raise


if __name__ == "__main__":
    # Run benchmarks
    asyncio.run(run_performance_benchmarks())