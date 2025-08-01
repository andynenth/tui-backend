#!/usr/bin/env python3
"""
Establish baseline metrics without state persistence.

This script runs comprehensive performance tests to establish
baseline metrics before enabling state persistence features.
"""

import os
import sys
import json
import time
import asyncio
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import aiohttp
import numpy as np
from tqdm import tqdm

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class MetricSample:
    """Single metric sample."""
    
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricSeries:
    """Time series of metric samples."""
    
    name: str
    unit: str
    samples: List[MetricSample] = field(default_factory=list)
    
    def add_sample(self, value: float, metadata: Optional[Dict[str, Any]] = None):
        """Add a sample to the series."""
        self.samples.append(MetricSample(
            timestamp=datetime.utcnow(),
            value=value,
            metadata=metadata or {}
        ))
        
    @property
    def count(self) -> int:
        return len(self.samples)
        
    @property
    def values(self) -> List[float]:
        return [s.value for s in self.samples]
        
    @property
    def mean(self) -> float:
        return statistics.mean(self.values) if self.values else 0
        
    @property
    def median(self) -> float:
        return statistics.median(self.values) if self.values else 0
        
    @property
    def stdev(self) -> float:
        return statistics.stdev(self.values) if len(self.values) > 1 else 0
        
    @property
    def p50(self) -> float:
        return np.percentile(self.values, 50) if self.values else 0
        
    @property
    def p90(self) -> float:
        return np.percentile(self.values, 90) if self.values else 0
        
    @property
    def p95(self) -> float:
        return np.percentile(self.values, 95) if self.values else 0
        
    @property
    def p99(self) -> float:
        return np.percentile(self.values, 99) if self.values else 0
        
    @property
    def min(self) -> float:
        return min(self.values) if self.values else 0
        
    @property
    def max(self) -> float:
        return max(self.values) if self.values else 0


class BaselineMetricsCollector:
    """Collects baseline performance metrics."""
    
    def __init__(self, base_url: str):
        """Initialize metrics collector."""
        self.base_url = base_url
        self.metrics: Dict[str, MetricSeries] = {}
        self.session = None
        
        # Define metrics to collect
        self._init_metrics()
        
    def _init_metrics(self):
        """Initialize metric series."""
        metric_definitions = [
            # Latency metrics
            ("create_room_latency", "ms"),
            ("join_room_latency", "ms"),
            ("start_game_latency", "ms"),
            ("play_turn_latency", "ms"),
            ("get_state_latency", "ms"),
            ("end_game_latency", "ms"),
            
            # Throughput metrics
            ("requests_per_second", "rps"),
            ("games_per_minute", "gpm"),
            ("turns_per_second", "tps"),
            
            # Resource metrics
            ("cpu_usage", "percent"),
            ("memory_usage", "mb"),
            ("connection_count", "count"),
            
            # Error metrics
            ("error_rate", "percent"),
            ("timeout_rate", "percent"),
            ("circuit_breaker_trips", "count"),
            
            # Business metrics
            ("concurrent_games", "count"),
            ("active_players", "count"),
            ("game_completion_rate", "percent"),
        ]
        
        for name, unit in metric_definitions:
            self.metrics[name] = MetricSeries(name=name, unit=unit)
            
    async def collect_baseline(
        self,
        duration_minutes: int = 60,
        concurrent_users: int = 100,
        operations_per_minute: int = 1000
    ) -> Dict[str, Any]:
        """
        Collect baseline metrics over specified duration.
        
        Args:
            duration_minutes: How long to collect metrics
            concurrent_users: Number of concurrent users to simulate
            operations_per_minute: Target operations per minute
            
        Returns:
            Baseline metrics report
        """
        print(f"📊 Collecting baseline metrics for {duration_minutes} minutes")
        print(f"   Concurrent users: {concurrent_users}")
        print(f"   Target ops/min: {operations_per_minute}")
        print("=" * 60)
        
        self.session = aiohttp.ClientSession()
        
        try:
            # Ensure state persistence is disabled
            await self._disable_state_persistence()
            
            # Warmup phase
            print("\n🔥 Warming up (2 minutes)...")
            await self._warmup_phase()
            
            # Main collection phase
            print("\n📈 Collecting metrics...")
            start_time = datetime.utcnow()
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Start concurrent tasks
            tasks = []
            
            # User simulation tasks
            for i in range(concurrent_users):
                task = asyncio.create_task(
                    self._simulate_user(f"baseline-user-{i}", end_time)
                )
                tasks.append(task)
                await asyncio.sleep(0.1)  # Stagger starts
                
            # Metrics collection task
            metrics_task = asyncio.create_task(
                self._collect_system_metrics(end_time)
            )
            tasks.append(metrics_task)
            
            # Progress monitoring task
            progress_task = asyncio.create_task(
                self._show_progress(start_time, end_time)
            )
            tasks.append(progress_task)
            
            # Wait for all tasks
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Generate report
            return self._generate_baseline_report()
            
        finally:
            if self.session:
                await self.session.close()
                
    async def _disable_state_persistence(self):
        """Ensure state persistence is disabled."""
        try:
            async with self.session.post(
                f"{self.base_url}/api/feature-flags/toggle",
                json={
                    "flag": "use_state_persistence",
                    "enabled": False
                }
            ) as response:
                if response.status == 200:
                    print("✅ State persistence disabled for baseline")
                else:
                    print("⚠️  Failed to disable state persistence")
                    
        except Exception as e:
            print(f"⚠️  Error disabling state persistence: {e}")
            
    async def _warmup_phase(self):
        """Warmup the system before measurement."""
        warmup_users = 5
        warmup_duration = 120  # 2 minutes
        
        tasks = []
        end_time = datetime.utcnow() + timedelta(seconds=warmup_duration)
        
        for i in range(warmup_users):
            task = asyncio.create_task(
                self._simulate_user(f"warmup-{i}", end_time, warmup=True)
            )
            tasks.append(task)
            
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Clear warmup data
        for metric in self.metrics.values():
            metric.samples.clear()
            
    async def _simulate_user(
        self,
        user_id: str,
        end_time: datetime,
        warmup: bool = False
    ):
        """Simulate a user playing games."""
        while datetime.utcnow() < end_time:
            try:
                # Complete game flow
                room_id = await self._create_room(user_id)
                
                if room_id:
                    # Join with bots
                    for i in range(3):
                        await self._join_room(room_id, f"bot-{i}")
                        
                    # Start game
                    if await self._start_game(room_id):
                        # Play turns
                        for _ in range(20):
                            await self._play_turn(room_id, user_id)
                            await self._get_game_state(room_id)
                            await asyncio.sleep(0.5)
                            
                        # End game
                        await self._end_game(room_id)
                        
                # Delay between games
                await asyncio.sleep(2)
                
            except Exception as e:
                if not warmup:
                    self.metrics["error_rate"].add_sample(1.0)
                    
    async def _measure_operation(
        self,
        metric_name: str,
        operation,
        *args,
        **kwargs
    ):
        """Measure operation latency."""
        start = time.time()
        
        try:
            result = await operation(*args, **kwargs)
            latency_ms = (time.time() - start) * 1000
            
            self.metrics[metric_name].add_sample(latency_ms)
            
            return result
            
        except asyncio.TimeoutError:
            self.metrics["timeout_rate"].add_sample(1.0)
            raise
        except Exception:
            self.metrics["error_rate"].add_sample(1.0)
            raise
            
    async def _create_room(self, user_id: str) -> Optional[str]:
        """Create a room and measure latency."""
        async def create():
            async with self.session.post(
                f"{self.base_url}/api/rooms/create",
                json={
                    "name": f"baseline-room-{user_id}-{time.time()}",
                    "capacity": 4,
                    "is_public": False
                },
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("id")
                return None
                
        return await self._measure_operation(
            "create_room_latency",
            create
        )
        
    async def _join_room(self, room_id: str, player_name: str) -> bool:
        """Join a room and measure latency."""
        async def join():
            async with self.session.post(
                f"{self.base_url}/api/rooms/{room_id}/join",
                json={"player_name": player_name},
                timeout=10
            ) as response:
                return response.status == 200
                
        return await self._measure_operation(
            "join_room_latency",
            join
        )
        
    async def _start_game(self, room_id: str) -> bool:
        """Start a game and measure latency."""
        async def start():
            async with self.session.post(
                f"{self.base_url}/api/games/start",
                json={"room_id": room_id},
                timeout=10
            ) as response:
                return response.status == 200
                
        return await self._measure_operation(
            "start_game_latency",
            start
        )
        
    async def _play_turn(self, room_id: str, player_id: str) -> bool:
        """Play a turn and measure latency."""
        async def play():
            async with self.session.post(
                f"{self.base_url}/api/games/{room_id}/turn",
                json={
                    "player_id": player_id,
                    "action": "play",
                    "card": {"suit": "hearts", "rank": "7"}
                },
                timeout=10
            ) as response:
                return response.status == 200
                
        return await self._measure_operation(
            "play_turn_latency",
            play
        )
        
    async def _get_game_state(self, room_id: str) -> bool:
        """Get game state and measure latency."""
        async def get_state():
            async with self.session.get(
                f"{self.base_url}/api/games/{room_id}/state",
                timeout=10
            ) as response:
                return response.status == 200
                
        return await self._measure_operation(
            "get_state_latency",
            get_state
        )
        
    async def _end_game(self, room_id: str) -> bool:
        """End a game and measure latency."""
        async def end():
            async with self.session.post(
                f"{self.base_url}/api/games/{room_id}/end",
                timeout=10
            ) as response:
                return response.status == 200
                
        return await self._measure_operation(
            "end_game_latency",
            end
        )
        
    async def _collect_system_metrics(self, end_time: datetime):
        """Collect system-level metrics."""
        while datetime.utcnow() < end_time:
            try:
                # Get metrics from system
                async with self.session.get(
                    f"{self.base_url}/health/metrics",
                    timeout=5
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract metrics
                        if "metrics" in data:
                            metrics = data["metrics"]
                            
                            # CPU usage
                            if "cpu_percent" in metrics:
                                self.metrics["cpu_usage"].add_sample(
                                    metrics["cpu_percent"]
                                )
                                
                            # Memory usage
                            if "memory_mb" in metrics:
                                self.metrics["memory_usage"].add_sample(
                                    metrics["memory_mb"]
                                )
                                
                            # Active connections
                            if "active_connections" in metrics:
                                self.metrics["connection_count"].add_sample(
                                    metrics["active_connections"]
                                )
                                
            except Exception as e:
                pass  # Ignore errors in metrics collection
                
            await asyncio.sleep(10)  # Collect every 10 seconds
            
    async def _show_progress(self, start_time: datetime, end_time: datetime):
        """Show collection progress."""
        with tqdm(total=100, desc="Progress") as pbar:
            last_pct = 0
            
            while datetime.utcnow() < end_time:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                total = (end_time - start_time).total_seconds()
                pct = int((elapsed / total) * 100)
                
                if pct > last_pct:
                    pbar.update(pct - last_pct)
                    last_pct = pct
                    
                await asyncio.sleep(1)
                
            pbar.update(100 - last_pct)
            
    def _generate_baseline_report(self) -> Dict[str, Any]:
        """Generate comprehensive baseline report."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "configuration": {
                "state_persistence": "disabled",
                "measurement_type": "baseline"
            },
            "metrics": {},
            "summary": {}
        }
        
        # Process each metric
        for name, series in self.metrics.items():
            if series.count > 0:
                report["metrics"][name] = {
                    "count": series.count,
                    "unit": series.unit,
                    "mean": round(series.mean, 2),
                    "median": round(series.median, 2),
                    "stdev": round(series.stdev, 2),
                    "min": round(series.min, 2),
                    "max": round(series.max, 2),
                    "p50": round(series.p50, 2),
                    "p90": round(series.p90, 2),
                    "p95": round(series.p95, 2),
                    "p99": round(series.p99, 2)
                }
                
        # Generate summary
        report["summary"] = {
            "avg_latency_ms": round(statistics.mean([
                self.metrics["create_room_latency"].mean,
                self.metrics["join_room_latency"].mean,
                self.metrics["start_game_latency"].mean,
                self.metrics["play_turn_latency"].mean,
                self.metrics["get_state_latency"].mean,
                self.metrics["end_game_latency"].mean
            ]), 2),
            "p99_latency_ms": round(max([
                self.metrics["create_room_latency"].p99,
                self.metrics["join_room_latency"].p99,
                self.metrics["start_game_latency"].p99,
                self.metrics["play_turn_latency"].p99,
                self.metrics["get_state_latency"].p99,
                self.metrics["end_game_latency"].p99
            ]), 2),
            "total_operations": sum(
                series.count for series in self.metrics.values()
                if series.name.endswith("_latency")
            ),
            "error_rate_percent": round(
                (self.metrics["error_rate"].count / 
                 max(1, self.metrics["create_room_latency"].count)) * 100,
                2
            ) if self.metrics["error_rate"].count > 0 else 0
        }
        
        # Save report
        report_file = f"baseline_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
            
        # Print summary
        self._print_summary(report)
        
        print(f"\n📄 Baseline report saved: {report_file}")
        
        return report
        
    def _print_summary(self, report: Dict[str, Any]):
        """Print baseline summary."""
        print("\n" + "=" * 60)
        print("📊 BASELINE METRICS SUMMARY")
        print("=" * 60)
        
        summary = report["summary"]
        print(f"\nAverage Latency: {summary['avg_latency_ms']} ms")
        print(f"P99 Latency: {summary['p99_latency_ms']} ms")
        print(f"Total Operations: {summary['total_operations']}")
        print(f"Error Rate: {summary['error_rate_percent']}%")
        
        print("\n📈 Operation Latencies (ms):")
        print(f"{'Operation':<20} {'Mean':<8} {'P50':<8} {'P90':<8} {'P95':<8} {'P99':<8}")
        print("-" * 70)
        
        for name, data in report["metrics"].items():
            if name.endswith("_latency"):
                op_name = name.replace("_latency", "")
                print(
                    f"{op_name:<20} "
                    f"{data['mean']:<8.1f} "
                    f"{data['p50']:<8.1f} "
                    f"{data['p90']:<8.1f} "
                    f"{data['p95']:<8.1f} "
                    f"{data['p99']:<8.1f}"
                )


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Establish baseline metrics")
    parser.add_argument(
        "--base-url",
        default=os.getenv("TEST_URL", "http://localhost:8000"),
        help="Base URL for testing"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Test duration in minutes (default: 60)"
    )
    parser.add_argument(
        "--users",
        type=int,
        default=100,
        help="Number of concurrent users (default: 100)"
    )
    parser.add_argument(
        "--ops-per-minute",
        type=int,
        default=1000,
        help="Target operations per minute (default: 1000)"
    )
    
    args = parser.parse_args()
    
    # Create collector
    collector = BaselineMetricsCollector(args.base_url)
    
    # Collect baseline
    report = await collector.collect_baseline(
        duration_minutes=args.duration,
        concurrent_users=args.users,
        operations_per_minute=args.ops_per_minute
    )
    
    return 0 if report else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))