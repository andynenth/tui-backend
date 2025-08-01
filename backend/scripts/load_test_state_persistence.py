#!/usr/bin/env python3
"""
Load testing with state persistence enabled.

This script runs comprehensive load tests with state persistence
features enabled to measure performance impact.
"""

import os
import sys
import json
import time
import asyncio
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import aiohttp
import numpy as np
from tqdm import tqdm
import concurrent.futures

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class LoadTestScenario:
    """Load test scenario configuration."""
    
    name: str
    description: str
    duration_minutes: int
    concurrent_users: int
    ramp_up_seconds: int
    operations_per_user_per_minute: int
    state_persistence_config: Dict[str, Any]
    workload_pattern: str = "steady"  # steady, burst, wave
    
    def get_users_at_time(self, elapsed_seconds: int) -> int:
        """Get number of active users at given time."""
        if elapsed_seconds < self.ramp_up_seconds:
            # Linear ramp-up
            return int((elapsed_seconds / self.ramp_up_seconds) * self.concurrent_users)
        return self.concurrent_users


@dataclass
class LoadTestResult:
    """Results from a load test scenario."""
    
    scenario: LoadTestScenario
    start_time: datetime
    end_time: datetime
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    latencies: List[float] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
        
    @property
    def error_rate(self) -> float:
        return 100 - self.success_rate
        
    @property
    def avg_latency(self) -> float:
        return np.mean(self.latencies) if self.latencies else 0
        
    @property
    def p50_latency(self) -> float:
        return np.percentile(self.latencies, 50) if self.latencies else 0
        
    @property
    def p90_latency(self) -> float:
        return np.percentile(self.latencies, 90) if self.latencies else 0
        
    @property
    def p95_latency(self) -> float:
        return np.percentile(self.latencies, 95) if self.latencies else 0
        
    @property
    def p99_latency(self) -> float:
        return np.percentile(self.latencies, 99) if self.latencies else 0


class StatePersistenceLoadTester:
    """Load tester for state persistence features."""
    
    def __init__(self, base_url: str):
        """Initialize load tester."""
        self.base_url = base_url
        self.session = None
        self.current_result: Optional[LoadTestResult] = None
        self._request_counter = 0
        self._active_users = 0
        
    async def run_scenario(self, scenario: LoadTestScenario) -> LoadTestResult:
        """
        Run a load test scenario.
        
        Args:
            scenario: Load test scenario to run
            
        Returns:
            Test results
        """
        print(f"\n🚀 Running scenario: {scenario.name}")
        print(f"   {scenario.description}")
        print(f"   Duration: {scenario.duration_minutes} minutes")
        print(f"   Users: {scenario.concurrent_users}")
        print(f"   Ramp-up: {scenario.ramp_up_seconds} seconds")
        print("=" * 60)
        
        self.session = aiohttp.ClientSession()
        self.current_result = LoadTestResult(
            scenario=scenario,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow()
        )
        
        try:
            # Configure state persistence
            await self._configure_state_persistence(scenario.state_persistence_config)
            
            # Run the load test
            await self._execute_scenario()
            
            # Generate report
            return self._generate_report()
            
        finally:
            if self.session:
                await self.session.close()
                
    async def _configure_state_persistence(self, config: Dict[str, Any]):
        """Configure state persistence for the test."""
        print("\n⚙️  Configuring state persistence...")
        
        for flag_name, settings in config.items():
            try:
                if isinstance(settings, bool):
                    # Simple toggle
                    await self._toggle_flag(flag_name, settings)
                elif isinstance(settings, dict):
                    # Advanced configuration
                    await self._configure_flag(flag_name, settings)
                    
            except Exception as e:
                print(f"❌ Failed to configure {flag_name}: {e}")
                
    async def _toggle_flag(self, flag_name: str, enabled: bool):
        """Toggle a feature flag."""
        async with self.session.post(
            f"{self.base_url}/api/feature-flags/toggle",
            json={"flag": flag_name, "enabled": enabled}
        ) as response:
            if response.status == 200:
                print(f"✅ {flag_name}: {'enabled' if enabled else 'disabled'}")
            else:
                print(f"❌ Failed to toggle {flag_name}")
                
    async def _configure_flag(self, flag_name: str, settings: Dict[str, Any]):
        """Configure advanced flag settings."""
        async with self.session.put(
            f"{self.base_url}/api/feature-flags/{flag_name}",
            json=settings
        ) as response:
            if response.status == 200:
                print(f"✅ {flag_name}: configured with {settings}")
            else:
                print(f"❌ Failed to configure {flag_name}")
                
    async def _execute_scenario(self):
        """Execute the load test scenario."""
        scenario = self.current_result.scenario
        end_time = datetime.utcnow() + timedelta(minutes=scenario.duration_minutes)
        
        # Progress tracking
        progress_task = asyncio.create_task(self._show_progress(end_time))
        
        # Metrics collection
        metrics_task = asyncio.create_task(self._collect_metrics(end_time))
        
        # User spawning
        spawn_task = asyncio.create_task(self._spawn_users(end_time))
        
        # Wait for completion
        await asyncio.gather(
            progress_task,
            metrics_task,
            spawn_task,
            return_exceptions=True
        )
        
        self.current_result.end_time = datetime.utcnow()
        
    async def _spawn_users(self, end_time: datetime):
        """Spawn users according to scenario."""
        scenario = self.current_result.scenario
        start_time = datetime.utcnow()
        user_tasks = []
        
        while datetime.utcnow() < end_time:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            target_users = scenario.get_users_at_time(elapsed)
            current_users = len(user_tasks)
            
            # Spawn new users if needed
            if target_users > current_users:
                for i in range(current_users, target_users):
                    user_task = asyncio.create_task(
                        self._simulate_user(f"load-user-{i}", end_time)
                    )
                    user_tasks.append(user_task)
                    self._active_users += 1
                    
            await asyncio.sleep(1)
            
        # Wait for all users to complete
        await asyncio.gather(*user_tasks, return_exceptions=True)
        
    async def _simulate_user(self, user_id: str, end_time: datetime):
        """Simulate a single user's behavior."""
        scenario = self.current_result.scenario
        
        try:
            while datetime.utcnow() < end_time:
                # Apply workload pattern
                if scenario.workload_pattern == "burst":
                    # Burst pattern: alternating high/low activity
                    if random.random() < 0.3:  # 30% chance of burst
                        operations = scenario.operations_per_user_per_minute * 3
                    else:
                        operations = scenario.operations_per_user_per_minute // 2
                elif scenario.workload_pattern == "wave":
                    # Wave pattern: sinusoidal activity
                    elapsed = (datetime.utcnow() - self.current_result.start_time).total_seconds()
                    wave_factor = (np.sin(elapsed / 60) + 1) / 2  # 0 to 1
                    operations = int(scenario.operations_per_user_per_minute * wave_factor)
                else:
                    # Steady pattern
                    operations = scenario.operations_per_user_per_minute
                    
                # Execute operations
                delay = 60 / max(1, operations)  # Seconds between operations
                
                # Game lifecycle with state persistence stress
                room_id = await self._execute_operation(
                    "create_room",
                    self._create_room,
                    user_id
                )
                
                if room_id:
                    # Multiple state changes to stress persistence
                    for i in range(3):
                        await self._execute_operation(
                            "join_room",
                            self._join_room,
                            room_id,
                            f"bot-{i}"
                        )
                        
                    if await self._execute_operation("start_game", self._start_game, room_id):
                        # Rapid state changes
                        for turn in range(10):
                            await self._execute_operation(
                                "play_turn",
                                self._play_turn,
                                room_id,
                                user_id
                            )
                            
                            # Frequent state reads
                            await self._execute_operation(
                                "get_state",
                                self._get_game_state,
                                room_id
                            )
                            
                            # Add some chaos - concurrent modifications
                            if random.random() < 0.1:  # 10% chance
                                asyncio.create_task(
                                    self._execute_operation(
                                        "concurrent_update",
                                        self._play_turn,
                                        room_id,
                                        f"bot-{random.randint(0, 2)}"
                                    )
                                )
                                
                            await asyncio.sleep(delay)
                            
                        # End game
                        await self._execute_operation(
                            "end_game",
                            self._end_game,
                            room_id
                        )
                        
                # Small delay between games
                await asyncio.sleep(delay * 2)
                
        finally:
            self._active_users -= 1
            
    async def _execute_operation(
        self,
        operation_name: str,
        operation_func,
        *args,
        **kwargs
    ):
        """Execute an operation and record metrics."""
        start_time = time.time()
        self._request_counter += 1
        self.current_result.total_requests += 1
        
        try:
            result = await operation_func(*args, **kwargs)
            
            # Record success
            latency_ms = (time.time() - start_time) * 1000
            self.current_result.successful_requests += 1
            self.current_result.latencies.append(latency_ms)
            
            return result
            
        except asyncio.TimeoutError:
            self.current_result.timeout_requests += 1
            self.current_result.errors.append({
                "type": "timeout",
                "operation": operation_name,
                "timestamp": datetime.utcnow().isoformat()
            })
            return None
            
        except Exception as e:
            self.current_result.failed_requests += 1
            self.current_result.errors.append({
                "type": "error",
                "operation": operation_name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            return None
            
    # Operation implementations
    async def _create_room(self, user_id: str) -> Optional[str]:
        """Create a room."""
        async with self.session.post(
            f"{self.base_url}/api/rooms/create",
            json={
                "name": f"load-room-{user_id}-{time.time()}",
                "capacity": 4,
                "is_public": False
            },
            timeout=10
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("id")
            return None
            
    async def _join_room(self, room_id: str, player_name: str) -> bool:
        """Join a room."""
        async with self.session.post(
            f"{self.base_url}/api/rooms/{room_id}/join",
            json={"player_name": player_name},
            timeout=10
        ) as response:
            return response.status == 200
            
    async def _start_game(self, room_id: str) -> bool:
        """Start a game."""
        async with self.session.post(
            f"{self.base_url}/api/games/start",
            json={"room_id": room_id},
            timeout=10
        ) as response:
            return response.status == 200
            
    async def _play_turn(self, room_id: str, player_id: str) -> bool:
        """Play a turn."""
        async with self.session.post(
            f"{self.base_url}/api/games/{room_id}/turn",
            json={
                "player_id": player_id,
                "action": "play",
                "card": {
                    "suit": random.choice(["hearts", "diamonds", "clubs", "spades"]),
                    "rank": random.choice(["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"])
                }
            },
            timeout=10
        ) as response:
            return response.status == 200
            
    async def _get_game_state(self, room_id: str) -> bool:
        """Get game state."""
        async with self.session.get(
            f"{self.base_url}/api/games/{room_id}/state",
            timeout=10
        ) as response:
            return response.status == 200
            
    async def _end_game(self, room_id: str) -> bool:
        """End a game."""
        async with self.session.post(
            f"{self.base_url}/api/games/{room_id}/end",
            timeout=10
        ) as response:
            return response.status == 200
            
    async def _collect_metrics(self, end_time: datetime):
        """Collect system metrics during test."""
        while datetime.utcnow() < end_time:
            try:
                # Collect health metrics
                async with self.session.get(
                    f"{self.base_url}/health/detailed",
                    timeout=5
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Could store these for analysis
                        
            except Exception:
                pass  # Ignore metrics collection errors
                
            await asyncio.sleep(10)
            
    async def _show_progress(self, end_time: datetime):
        """Show test progress."""
        start_time = self.current_result.start_time
        scenario = self.current_result.scenario
        
        with tqdm(total=100, desc="Progress") as pbar:
            last_pct = 0
            
            while datetime.utcnow() < end_time:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                total = (end_time - start_time).total_seconds()
                pct = int((elapsed / total) * 100)
                
                if pct > last_pct:
                    pbar.update(pct - last_pct)
                    last_pct = pct
                    
                # Update description with live stats
                if self.current_result.total_requests > 0:
                    pbar.set_description(
                        f"Progress (Users: {self._active_users}, "
                        f"RPS: {self._request_counter/max(1, elapsed):.1f}, "
                        f"Errors: {self.current_result.error_rate:.1f}%)"
                    )
                    
                await asyncio.sleep(1)
                
            pbar.update(100 - last_pct)
            
    def _generate_report(self) -> LoadTestResult:
        """Generate load test report."""
        result = self.current_result
        
        # Save detailed report
        report = {
            "scenario": {
                "name": result.scenario.name,
                "description": result.scenario.description,
                "duration_minutes": result.scenario.duration_minutes,
                "concurrent_users": result.scenario.concurrent_users,
                "workload_pattern": result.scenario.workload_pattern,
                "state_persistence_config": result.scenario.state_persistence_config
            },
            "execution": {
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat(),
                "duration_seconds": (result.end_time - result.start_time).total_seconds()
            },
            "results": {
                "total_requests": result.total_requests,
                "successful_requests": result.successful_requests,
                "failed_requests": result.failed_requests,
                "timeout_requests": result.timeout_requests,
                "success_rate": round(result.success_rate, 2),
                "error_rate": round(result.error_rate, 2)
            },
            "latency": {
                "avg_ms": round(result.avg_latency, 2),
                "p50_ms": round(result.p50_latency, 2),
                "p90_ms": round(result.p90_latency, 2),
                "p95_ms": round(result.p95_latency, 2),
                "p99_ms": round(result.p99_latency, 2),
                "min_ms": round(min(result.latencies), 2) if result.latencies else 0,
                "max_ms": round(max(result.latencies), 2) if result.latencies else 0
            },
            "errors": result.errors[:100]  # First 100 errors
        }
        
        report_file = f"load_test_{result.scenario.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
            
        # Print summary
        self._print_summary(result)
        
        print(f"\n📄 Report saved: {report_file}")
        
        return result
        
    def _print_summary(self, result: LoadTestResult):
        """Print load test summary."""
        print("\n" + "=" * 60)
        print(f"📊 LOAD TEST SUMMARY: {result.scenario.name}")
        print("=" * 60)
        
        duration = (result.end_time - result.start_time).total_seconds()
        rps = result.total_requests / max(1, duration)
        
        print(f"\n📈 Performance Metrics:")
        print(f"  Total Requests: {result.total_requests}")
        print(f"  Successful: {result.successful_requests}")
        print(f"  Failed: {result.failed_requests}")
        print(f"  Timeouts: {result.timeout_requests}")
        print(f"  Success Rate: {result.success_rate:.2f}%")
        print(f"  Error Rate: {result.error_rate:.2f}%")
        print(f"  Throughput: {rps:.2f} requests/second")
        
        print(f"\n⏱️  Latency Statistics (ms):")
        print(f"  Average: {result.avg_latency:.2f}")
        print(f"  P50: {result.p50_latency:.2f}")
        print(f"  P90: {result.p90_latency:.2f}")
        print(f"  P95: {result.p95_latency:.2f}")
        print(f"  P99: {result.p99_latency:.2f}")
        
        if result.errors:
            print(f"\n❌ Error Summary:")
            error_types = {}
            for error in result.errors:
                error_type = error.get("type", "unknown")
                error_types[error_type] = error_types.get(error_type, 0) + 1
                
            for error_type, count in error_types.items():
                print(f"  {error_type}: {count}")


# Predefined test scenarios
def get_test_scenarios() -> List[LoadTestScenario]:
    """Get predefined test scenarios."""
    return [
        LoadTestScenario(
            name="light_load",
            description="Light load with basic state persistence",
            duration_minutes=10,
            concurrent_users=10,
            ramp_up_seconds=30,
            operations_per_user_per_minute=10,
            state_persistence_config={
                "use_state_persistence": True,
                "enable_state_snapshots": False,
                "enable_state_recovery": False
            },
            workload_pattern="steady"
        ),
        LoadTestScenario(
            name="medium_load",
            description="Medium load with snapshots enabled",
            duration_minutes=20,
            concurrent_users=50,
            ramp_up_seconds=60,
            operations_per_user_per_minute=20,
            state_persistence_config={
                "use_state_persistence": True,
                "enable_state_snapshots": True,
                "enable_state_recovery": False
            },
            workload_pattern="steady"
        ),
        LoadTestScenario(
            name="heavy_load",
            description="Heavy load with full persistence features",
            duration_minutes=30,
            concurrent_users=100,
            ramp_up_seconds=120,
            operations_per_user_per_minute=30,
            state_persistence_config={
                "use_state_persistence": True,
                "enable_state_snapshots": True,
                "enable_state_recovery": True
            },
            workload_pattern="steady"
        ),
        LoadTestScenario(
            name="burst_load",
            description="Burst pattern to test recovery",
            duration_minutes=15,
            concurrent_users=75,
            ramp_up_seconds=30,
            operations_per_user_per_minute=40,
            state_persistence_config={
                "use_state_persistence": True,
                "enable_state_snapshots": True,
                "enable_state_recovery": True
            },
            workload_pattern="burst"
        ),
        LoadTestScenario(
            name="stress_test",
            description="Stress test with extreme load",
            duration_minutes=10,
            concurrent_users=200,
            ramp_up_seconds=60,
            operations_per_user_per_minute=50,
            state_persistence_config={
                "use_state_persistence": True,
                "enable_state_snapshots": True,
                "enable_state_recovery": True
            },
            workload_pattern="wave"
        )
    ]


async def run_all_scenarios(base_url: str) -> Dict[str, LoadTestResult]:
    """Run all predefined scenarios."""
    tester = StatePersistenceLoadTester(base_url)
    results = {}
    
    for scenario in get_test_scenarios():
        print(f"\n{'='*60}")
        result = await tester.run_scenario(scenario)
        results[scenario.name] = result
        
        # Cool down between scenarios
        print("\n⏳ Cooling down for 2 minutes...")
        await asyncio.sleep(120)
        
    return results


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load test state persistence")
    parser.add_argument(
        "--base-url",
        default=os.getenv("TEST_URL", "http://localhost:8000"),
        help="Base URL for testing"
    )
    parser.add_argument(
        "--scenario",
        choices=["all"] + [s.name for s in get_test_scenarios()],
        default="all",
        help="Scenario to run (default: all)"
    )
    
    args = parser.parse_args()
    
    if args.scenario == "all":
        results = await run_all_scenarios(args.base_url)
        
        # Generate comparison report
        comparison_file = f"load_test_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        comparison = {
            "timestamp": datetime.utcnow().isoformat(),
            "scenarios": {}
        }
        
        for name, result in results.items():
            comparison["scenarios"][name] = {
                "success_rate": result.success_rate,
                "error_rate": result.error_rate,
                "avg_latency_ms": result.avg_latency,
                "p99_latency_ms": result.p99_latency,
                "total_requests": result.total_requests
            }
            
        with open(comparison_file, "w") as f:
            json.dump(comparison, f, indent=2)
            
        print(f"\n📊 Comparison report saved: {comparison_file}")
        
    else:
        # Run specific scenario
        scenarios = {s.name: s for s in get_test_scenarios()}
        scenario = scenarios[args.scenario]
        
        tester = StatePersistenceLoadTester(args.base_url)
        await tester.run_scenario(scenario)


if __name__ == "__main__":
    asyncio.run(main())