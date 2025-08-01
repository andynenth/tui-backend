#!/usr/bin/env python3
"""
Performance testing script for state persistence.

This script runs load tests to measure the performance impact
of state persistence and validates it meets requirements.
"""

import os
import sys
import time
import asyncio
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import aiohttp
import concurrent.futures
from tqdm import tqdm

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class PerformanceMetrics:
    """Performance test metrics."""
    
    operation: str
    samples: List[float] = field(default_factory=list)
    errors: int = 0
    
    @property
    def count(self) -> int:
        return len(self.samples)
        
    @property
    def mean(self) -> float:
        return statistics.mean(self.samples) if self.samples else 0
        
    @property
    def median(self) -> float:
        return statistics.median(self.samples) if self.samples else 0
        
    @property
    def p95(self) -> float:
        if not self.samples:
            return 0
        sorted_samples = sorted(self.samples)
        index = int(len(sorted_samples) * 0.95)
        return sorted_samples[index]
        
    @property
    def p99(self) -> float:
        if not self.samples:
            return 0
        sorted_samples = sorted(self.samples)
        index = int(len(sorted_samples) * 0.99)
        return sorted_samples[index]
        
    @property
    def error_rate(self) -> float:
        total = self.count + self.errors
        return (self.errors / total * 100) if total > 0 else 0


@dataclass
class TestConfig:
    """Performance test configuration."""
    
    base_url: str
    duration_seconds: int = 300  # 5 minutes
    concurrent_users: int = 50
    games_per_user: int = 10
    operations_per_game: int = 20
    state_persistence_enabled: bool = True
    warmup_duration: int = 30
    
    @classmethod
    def from_args(cls, args) -> "TestConfig":
        """Create config from command line args."""
        return cls(
            base_url=args.base_url,
            duration_seconds=args.duration,
            concurrent_users=args.users,
            games_per_user=args.games_per_user,
            operations_per_game=args.ops_per_game,
            state_persistence_enabled=args.with_state,
            warmup_duration=args.warmup
        )


class PerformanceTestRunner:
    """Runs performance tests for state persistence."""
    
    def __init__(self, config: TestConfig):
        """Initialize test runner."""
        self.config = config
        self.metrics: Dict[str, PerformanceMetrics] = {
            "create_room": PerformanceMetrics("create_room"),
            "join_room": PerformanceMetrics("join_room"),
            "start_game": PerformanceMetrics("start_game"),
            "play_turn": PerformanceMetrics("play_turn"),
            "get_state": PerformanceMetrics("get_state"),
            "end_game": PerformanceMetrics("end_game"),
        }
        self.start_time = None
        self.session = None
        
    async def run(self) -> Dict[str, Any]:
        """Run the performance test."""
        print(f"🏃 Performance Test - State Persistence {'ON' if self.config.state_persistence_enabled else 'OFF'}")
        print("=" * 60)
        print(f"Duration: {self.config.duration_seconds}s")
        print(f"Users: {self.config.concurrent_users}")
        print(f"Games per user: {self.config.games_per_user}")
        print(f"Operations per game: {self.config.operations_per_game}")
        print()
        
        # Initialize session
        self.session = aiohttp.ClientSession()
        
        try:
            # Enable/disable state persistence
            await self._configure_state_persistence()
            
            # Warmup phase
            if self.config.warmup_duration > 0:
                print(f"🔥 Warming up for {self.config.warmup_duration}s...")
                await self._warmup_phase()
                
            # Main test phase
            print("\n🚀 Starting main test phase...")
            self.start_time = time.time()
            
            # Run concurrent users
            tasks = []
            with tqdm(total=self.config.concurrent_users, desc="Users") as pbar:
                for user_id in range(self.config.concurrent_users):
                    task = asyncio.create_task(self._simulate_user(f"user-{user_id}", pbar))
                    tasks.append(task)
                    
                    # Stagger user start times
                    await asyncio.sleep(0.1)
                    
            # Wait for all users to complete or timeout
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Generate report
            return await self._generate_report()
            
        finally:
            if self.session:
                await self.session.close()
                
    async def _configure_state_persistence(self):
        """Configure state persistence for the test."""
        try:
            async with self.session.post(
                f"{self.config.base_url}/api/feature-flags/toggle",
                json={
                    "flag": "use_state_persistence",
                    "enabled": self.config.state_persistence_enabled
                }
            ) as response:
                if response.status != 200:
                    print(f"⚠️  Failed to configure state persistence: {response.status}")
                else:
                    print(f"✅ State persistence {'enabled' if self.config.state_persistence_enabled else 'disabled'}")
                    
        except Exception as e:
            print(f"⚠️  Error configuring state persistence: {e}")
            
    async def _warmup_phase(self):
        """Warmup phase to stabilize the system."""
        warmup_users = min(5, self.config.concurrent_users)
        
        tasks = []
        for i in range(warmup_users):
            task = asyncio.create_task(self._simulate_user(f"warmup-{i}", None, warmup=True))
            tasks.append(task)
            
        # Wait for warmup to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Clear warmup metrics
        for metric in self.metrics.values():
            metric.samples.clear()
            metric.errors = 0
            
    async def _simulate_user(self, user_id: str, pbar: Optional[tqdm] = None, warmup: bool = False):
        """Simulate a single user playing games."""
        try:
            if warmup:
                # Simple warmup operations
                for _ in range(5):
                    await self._create_room(f"{user_id}-warmup")
                    await asyncio.sleep(0.5)
                return
                
            # Main test operations
            end_time = time.time() + self.config.duration_seconds
            games_played = 0
            
            while time.time() < end_time and games_played < self.config.games_per_user:
                # Play a complete game
                room_id = await self._create_room(f"{user_id}-game-{games_played}")
                
                if room_id:
                    # Join with bot players
                    for i in range(3):
                        await self._join_room(room_id, f"bot-{i}")
                        
                    # Start game
                    game_started = await self._start_game(room_id)
                    
                    if game_started:
                        # Play turns
                        for turn in range(self.config.operations_per_game):
                            await self._play_turn(room_id, user_id)
                            await self._get_game_state(room_id)
                            
                            # Small delay between operations
                            await asyncio.sleep(0.1)
                            
                        # End game
                        await self._end_game(room_id)
                        
                games_played += 1
                
                # Delay between games
                await asyncio.sleep(1)
                
            if pbar:
                pbar.update(1)
                
        except Exception as e:
            print(f"\n❌ User {user_id} error: {e}")
            
    async def _timed_operation(self, operation: str, func, *args, **kwargs):
        """Execute a timed operation and record metrics."""
        start = time.time()
        
        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.time() - start) * 1000
            self.metrics[operation].samples.append(duration_ms)
            return result
            
        except Exception as e:
            self.metrics[operation].errors += 1
            raise
            
    async def _create_room(self, room_name: str) -> Optional[str]:
        """Create a room and return room ID."""
        try:
            async def create():
                async with self.session.post(
                    f"{self.config.base_url}/api/rooms/create",
                    json={
                        "name": room_name,
                        "capacity": 4,
                        "is_public": False
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("id")
                    return None
                    
            return await self._timed_operation("create_room", create)
            
        except Exception:
            return None
            
    async def _join_room(self, room_id: str, player_name: str) -> bool:
        """Join a room."""
        try:
            async def join():
                async with self.session.post(
                    f"{self.config.base_url}/api/rooms/{room_id}/join",
                    json={"player_name": player_name}
                ) as response:
                    return response.status == 200
                    
            return await self._timed_operation("join_room", join)
            
        except Exception:
            return False
            
    async def _start_game(self, room_id: str) -> bool:
        """Start a game."""
        try:
            async def start():
                async with self.session.post(
                    f"{self.config.base_url}/api/games/start",
                    json={"room_id": room_id}
                ) as response:
                    return response.status == 200
                    
            return await self._timed_operation("start_game", start)
            
        except Exception:
            return False
            
    async def _play_turn(self, room_id: str, player_id: str) -> bool:
        """Play a turn."""
        try:
            async def play():
                async with self.session.post(
                    f"{self.config.base_url}/api/games/{room_id}/turn",
                    json={
                        "player_id": player_id,
                        "action": "play",
                        "card": {"suit": "hearts", "rank": "7"}
                    }
                ) as response:
                    return response.status == 200
                    
            return await self._timed_operation("play_turn", play)
            
        except Exception:
            return False
            
    async def _get_game_state(self, room_id: str) -> bool:
        """Get game state."""
        try:
            async def get_state():
                async with self.session.get(
                    f"{self.config.base_url}/api/games/{room_id}/state"
                ) as response:
                    return response.status == 200
                    
            return await self._timed_operation("get_state", get_state)
            
        except Exception:
            return False
            
    async def _end_game(self, room_id: str) -> bool:
        """End a game."""
        try:
            async def end():
                async with self.session.post(
                    f"{self.config.base_url}/api/games/{room_id}/end"
                ) as response:
                    return response.status == 200
                    
            return await self._timed_operation("end_game", end)
            
        except Exception:
            return False
            
    async def _generate_report(self) -> Dict[str, Any]:
        """Generate performance test report."""
        duration = time.time() - self.start_time
        
        report = {
            "test_config": {
                "duration_seconds": self.config.duration_seconds,
                "concurrent_users": self.config.concurrent_users,
                "games_per_user": self.config.games_per_user,
                "operations_per_game": self.config.operations_per_game,
                "state_persistence_enabled": self.config.state_persistence_enabled
            },
            "actual_duration": duration,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {}
        }
        
        # Calculate metrics for each operation
        total_operations = 0
        total_errors = 0
        
        for operation, metric in self.metrics.items():
            report["metrics"][operation] = {
                "count": metric.count,
                "errors": metric.errors,
                "error_rate": f"{metric.error_rate:.2f}%",
                "latency_ms": {
                    "mean": round(metric.mean, 2),
                    "median": round(metric.median, 2),
                    "p95": round(metric.p95, 2),
                    "p99": round(metric.p99, 2)
                }
            }
            
            total_operations += metric.count
            total_errors += metric.errors
            
        # Overall statistics
        report["overall"] = {
            "total_operations": total_operations,
            "total_errors": total_errors,
            "error_rate": f"{(total_errors / (total_operations + total_errors) * 100):.2f}%" if total_operations > 0 else "0%",
            "throughput_ops_per_sec": round(total_operations / duration, 2) if duration > 0 else 0
        }
        
        # Save report
        report_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
            
        # Print summary
        self._print_summary(report)
        
        print(f"\n📄 Full report saved: {report_file}")
        
        return report
        
    def _print_summary(self, report: Dict[str, Any]):
        """Print performance test summary."""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE TEST SUMMARY")
        print("=" * 60)
        
        print(f"\nState Persistence: {'ENABLED' if self.config.state_persistence_enabled else 'DISABLED'}")
        print(f"Total Operations: {report['overall']['total_operations']}")
        print(f"Total Errors: {report['overall']['total_errors']}")
        print(f"Error Rate: {report['overall']['error_rate']}")
        print(f"Throughput: {report['overall']['throughput_ops_per_sec']} ops/sec")
        
        print("\n📈 Latency by Operation (ms):")
        print(f"{'Operation':<15} {'Mean':<8} {'Median':<8} {'P95':<8} {'P99':<8} {'Errors'}")
        print("-" * 60)
        
        for operation, metrics in report["metrics"].items():
            latency = metrics["latency_ms"]
            print(
                f"{operation:<15} "
                f"{latency['mean']:<8.1f} "
                f"{latency['median']:<8.1f} "
                f"{latency['p95']:<8.1f} "
                f"{latency['p99']:<8.1f} "
                f"{metrics['errors']}"
            )


async def compare_with_without_state_persistence(config: TestConfig) -> Dict[str, Any]:
    """Run tests with and without state persistence and compare."""
    print("🔬 Running comparison test (with vs without state persistence)")
    print("=" * 60)
    
    # Test without state persistence
    config.state_persistence_enabled = False
    runner_without = PerformanceTestRunner(config)
    print("\n1️⃣ Testing WITHOUT state persistence...")
    report_without = await runner_without.run()
    
    # Wait between tests
    print("\n⏳ Waiting 30 seconds before next test...")
    await asyncio.sleep(30)
    
    # Test with state persistence
    config.state_persistence_enabled = True
    runner_with = PerformanceTestRunner(config)
    print("\n2️⃣ Testing WITH state persistence...")
    report_with = await runner_with.run()
    
    # Compare results
    comparison = {
        "timestamp": datetime.utcnow().isoformat(),
        "without_state": report_without,
        "with_state": report_with,
        "impact": {}
    }
    
    # Calculate impact
    for operation in report_without["metrics"]:
        without_p99 = report_without["metrics"][operation]["latency_ms"]["p99"]
        with_p99 = report_with["metrics"][operation]["latency_ms"]["p99"]
        
        if without_p99 > 0:
            impact_percent = ((with_p99 - without_p99) / without_p99) * 100
        else:
            impact_percent = 0
            
        comparison["impact"][operation] = {
            "p99_without": without_p99,
            "p99_with": with_p99,
            "impact_percent": round(impact_percent, 2),
            "impact_ms": round(with_p99 - without_p99, 2)
        }
        
    # Save comparison report
    comparison_file = f"performance_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(comparison_file, "w") as f:
        json.dump(comparison, f, indent=2)
        
    # Print comparison summary
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE COMPARISON SUMMARY")
    print("=" * 60)
    print("\n📈 P99 Latency Impact:")
    print(f"{'Operation':<15} {'Without':<10} {'With':<10} {'Impact':<10} {'Percent'}")
    print("-" * 60)
    
    for operation, impact in comparison["impact"].items():
        print(
            f"{operation:<15} "
            f"{impact['p99_without']:<10.1f} "
            f"{impact['p99_with']:<10.1f} "
            f"{impact['impact_ms']:<10.1f} "
            f"{impact['impact_percent']:>6.1f}%"
        )
        
    print(f"\n📄 Comparison report saved: {comparison_file}")
    
    return comparison


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance test for state persistence")
    parser.add_argument(
        "--base-url",
        default=os.getenv("TEST_URL", "http://localhost:8000"),
        help="Base URL for testing"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=300,
        help="Test duration in seconds (default: 300)"
    )
    parser.add_argument(
        "--users",
        type=int,
        default=50,
        help="Number of concurrent users (default: 50)"
    )
    parser.add_argument(
        "--games-per-user",
        type=int,
        default=10,
        help="Games per user (default: 10)"
    )
    parser.add_argument(
        "--ops-per-game",
        type=int,
        default=20,
        help="Operations per game (default: 20)"
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=30,
        help="Warmup duration in seconds (default: 30)"
    )
    parser.add_argument(
        "--with-state",
        action="store_true",
        help="Test with state persistence enabled"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run comparison test (with vs without)"
    )
    
    args = parser.parse_args()
    
    # Create test config
    config = TestConfig.from_args(args)
    
    # Run tests
    if args.compare:
        asyncio.run(compare_with_without_state_persistence(config))
    else:
        runner = PerformanceTestRunner(config)
        asyncio.run(runner.run())


if __name__ == "__main__":
    main()