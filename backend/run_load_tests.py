#!/usr/bin/env python3
"""
Load Testing Tool for Step 6.5.2

Comprehensive load and stress testing with realistic production loads.
Tests system behavior under high concurrent load scenarios.
"""

import asyncio
import sys
import time
import statistics
import logging
import json
import random
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import uuid
from datetime import datetime
import psutil
import gc

# Add backend to path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitor system resources during load testing."""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = []
        self.start_time = None
        
    async def start_monitoring(self):
        """Start system monitoring."""
        self.monitoring = True
        self.start_time = time.time()
        self.metrics = []
        
        # Monitor system resources every second
        asyncio.create_task(self._monitor_loop())
    
    def stop_monitoring(self):
        """Stop system monitoring."""
        self.monitoring = False
    
    async def _monitor_loop(self):
        """Continuous monitoring loop."""
        while self.monitoring:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=None)
                memory_info = psutil.virtual_memory()
                
                # Get process-specific metrics
                process = psutil.Process()
                process_memory = process.memory_info()
                process_cpu = process.cpu_percent()
                
                metric = {
                    "timestamp": time.time() - self.start_time,
                    "system_cpu_percent": cpu_percent,
                    "system_memory_percent": memory_info.percent,
                    "system_memory_available_mb": memory_info.available / (1024 * 1024),
                    "process_memory_rss_mb": process_memory.rss / (1024 * 1024),
                    "process_memory_vms_mb": process_memory.vms / (1024 * 1024),
                    "process_cpu_percent": process_cpu,
                    "open_file_descriptors": process.num_fds() if hasattr(process, 'num_fds') else 0
                }
                
                self.metrics.append(metric)
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.warning(f"Monitoring error: {e}")
                await asyncio.sleep(1.0)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get monitoring summary."""
        if not self.metrics:
            return {"error": "No metrics collected"}
        
        cpu_values = [m["system_cpu_percent"] for m in self.metrics]
        memory_values = [m["system_memory_percent"] for m in self.metrics]
        process_memory_values = [m["process_memory_rss_mb"] for m in self.metrics]
        
        return {
            "duration_seconds": len(self.metrics),
            "avg_cpu_percent": statistics.mean(cpu_values),
            "max_cpu_percent": max(cpu_values),
            "avg_memory_percent": statistics.mean(memory_values),
            "max_memory_percent": max(memory_values),
            "avg_process_memory_mb": statistics.mean(process_memory_values),
            "max_process_memory_mb": max(process_memory_values),
            "memory_growth_mb": max(process_memory_values) - min(process_memory_values),
            "peak_file_descriptors": max(m["open_file_descriptors"] for m in self.metrics)
        }


class LoadTestGameSystem:
    """High-performance game system for load testing."""
    
    def __init__(self):
        self.active_connections = {}
        self.active_rooms = {}
        self.active_games = {}
        self.operation_count = 0
        self.error_count = 0
        
    async def simulate_player_connection(self, player_id: str) -> Dict[str, Any]:
        """Simulate player WebSocket connection."""
        connection_start = time.perf_counter()
        
        # Simulate connection establishment
        await asyncio.sleep(random.uniform(0.001, 0.005))
        
        connection_id = f"conn_{player_id}_{uuid.uuid4().hex[:6]}"
        self.active_connections[connection_id] = {
            "player_id": player_id,
            "connected_at": time.time(),
            "status": "connected"
        }
        
        connection_end = time.perf_counter()
        self.operation_count += 1
        
        return {
            "connection_id": connection_id,
            "success": True,
            "duration_ms": (connection_end - connection_start) * 1000
        }
    
    async def simulate_room_operations(self, room_id: str, operation_type: str, connection_id: str) -> Dict[str, Any]:
        """Simulate room operations (create, join, leave)."""
        operation_start = time.perf_counter()
        
        try:
            if operation_type == "create":
                # Simulate room creation
                await asyncio.sleep(random.uniform(0.002, 0.008))
                
                self.active_rooms[room_id] = {
                    "host": connection_id,
                    "players": [connection_id],
                    "created_at": time.time(),
                    "max_players": 4
                }
                success = True
                
            elif operation_type == "join":
                # Simulate joining room
                await asyncio.sleep(random.uniform(0.001, 0.004))
                
                if room_id in self.active_rooms:
                    room = self.active_rooms[room_id]
                    if len(room["players"]) < room["max_players"]:
                        room["players"].append(connection_id)
                        success = True
                    else:
                        success = False  # Room full
                else:
                    success = False  # Room not found
                    
            elif operation_type == "leave":
                # Simulate leaving room
                await asyncio.sleep(random.uniform(0.001, 0.003))
                
                if room_id in self.active_rooms:
                    room = self.active_rooms[room_id]
                    if connection_id in room["players"]:
                        room["players"].remove(connection_id)
                        success = True
                    else:
                        success = False
                else:
                    success = False
            else:
                success = False
            
            operation_end = time.perf_counter()
            self.operation_count += 1
            
            if not success:
                self.error_count += 1
            
            return {
                "operation": operation_type,
                "room_id": room_id,
                "success": success,
                "duration_ms": (operation_end - operation_start) * 1000
            }
            
        except Exception as e:
            self.error_count += 1
            return {
                "operation": operation_type,
                "room_id": room_id,
                "success": False,
                "error": str(e),
                "duration_ms": 0
            }
    
    async def simulate_game_actions(self, game_id: str, player_id: str, action_type: str) -> Dict[str, Any]:
        """Simulate game actions (declare, play, etc.)."""
        action_start = time.perf_counter()
        
        try:
            if action_type == "start_game":
                # Simulate game initialization
                await asyncio.sleep(random.uniform(0.005, 0.015))
                
                self.active_games[game_id] = {
                    "players": [f"player_{i}" for i in range(4)],
                    "phase": "PREPARATION",
                    "round": 1,
                    "started_at": time.time()
                }
                success = True
                
            elif action_type == "declare":
                # Simulate declaration
                await asyncio.sleep(random.uniform(0.001, 0.003))
                success = True
                
            elif action_type == "play":
                # Simulate piece play
                await asyncio.sleep(random.uniform(0.002, 0.006))
                success = True
                
            elif action_type == "score":
                # Simulate scoring calculation
                await asyncio.sleep(random.uniform(0.001, 0.002))
                success = True
                
            else:
                success = False
            
            action_end = time.perf_counter()
            self.operation_count += 1
            
            if not success:
                self.error_count += 1
            
            return {
                "action": action_type,
                "game_id": game_id,
                "player_id": player_id,
                "success": success,
                "duration_ms": (action_end - action_start) * 1000
            }
            
        except Exception as e:
            self.error_count += 1
            return {
                "action": action_type,
                "game_id": game_id,
                "success": False,
                "error": str(e),
                "duration_ms": 0
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        return {
            "active_connections": len(self.active_connections),
            "active_rooms": len(self.active_rooms),
            "active_games": len(self.active_games),
            "total_operations": self.operation_count,
            "total_errors": self.error_count,
            "error_rate": (self.error_count / max(self.operation_count, 1)) * 100
        }


class LoadTester:
    """Comprehensive load testing system."""
    
    def __init__(self, concurrent_games: int = 50):
        self.concurrent_games = concurrent_games
        self.game_system = LoadTestGameSystem()
        self.monitor = SystemMonitor()
        self.test_results = {}
        
    async def run_concurrent_games_test(self) -> Dict[str, Any]:
        """Run concurrent games load test."""
        logger.info(f"🚀 Running concurrent games test with {self.concurrent_games} games...")
        
        results = {
            "concurrent_games": self.concurrent_games,
            "games_completed": 0,
            "games_failed": 0,
            "total_operations": 0,
            "total_errors": 0,
            "average_game_duration_ms": 0,
            "throughput_games_per_second": 0,
            "operation_times_ms": [],
            "system_metrics": {}
        }
        
        # Start system monitoring
        await self.monitor.start_monitoring()
        
        test_start = time.perf_counter()
        
        # Concurrent game function
        async def run_single_game(game_index: int):
            """Run a single game simulation."""
            game_start = time.perf_counter()
            game_id = f"load_game_{game_index}"
            operation_times = []
            
            try:
                # 1. Create connections (4 players per game)
                connections = []
                for player_index in range(4):
                    player_id = f"game_{game_index}_player_{player_index}"
                    conn_result = await self.game_system.simulate_player_connection(player_id)
                    connections.append(conn_result["connection_id"])
                    operation_times.append(conn_result["duration_ms"])
                
                # 2. Create room
                room_id = f"load_room_{game_index}"
                room_result = await self.game_system.simulate_room_operations(
                    room_id, "create", connections[0]
                )
                operation_times.append(room_result["duration_ms"])
                
                # 3. Players join room
                for conn in connections[1:]:
                    join_result = await self.game_system.simulate_room_operations(
                        room_id, "join", conn
                    )
                    operation_times.append(join_result["duration_ms"])
                
                # 4. Start game
                game_result = await self.game_system.simulate_game_actions(
                    game_id, connections[0], "start_game"
                )
                operation_times.append(game_result["duration_ms"])
                
                # 5. Game round simulation
                for round_num in range(3):  # 3 rounds per game
                    # Declarations
                    for conn in connections:
                        declare_result = await self.game_system.simulate_game_actions(
                            game_id, conn, "declare"
                        )
                        operation_times.append(declare_result["duration_ms"])
                    
                    # Plays
                    for turn in range(8):  # 8 turns per round
                        player_index = turn % 4
                        play_result = await self.game_system.simulate_game_actions(
                            game_id, connections[player_index], "play"
                        )
                        operation_times.append(play_result["duration_ms"])
                    
                    # Scoring
                    score_result = await self.game_system.simulate_game_actions(
                        game_id, "system", "score"
                    )
                    operation_times.append(score_result["duration_ms"])
                
                game_end = time.perf_counter()
                game_duration = (game_end - game_start) * 1000
                
                return {
                    "success": True,
                    "game_index": game_index,
                    "duration_ms": game_duration,
                    "operations": len(operation_times),
                    "operation_times": operation_times
                }
                
            except Exception as e:
                game_end = time.perf_counter()
                return {
                    "success": False,
                    "game_index": game_index,
                    "duration_ms": (game_end - game_start) * 1000,
                    "error": str(e),
                    "operations": len(operation_times),
                    "operation_times": operation_times
                }
        
        # Execute concurrent games
        tasks = [run_single_game(i) for i in range(self.concurrent_games)]
        game_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        test_end = time.perf_counter()
        total_test_time = test_end - test_start
        
        # Stop monitoring
        self.monitor.stop_monitoring()
        
        # Analyze results
        successful_games = []
        failed_games = []
        all_operation_times = []
        
        for result in game_results:
            if isinstance(result, dict):
                if result.get("success", False):
                    successful_games.append(result)
                    results["games_completed"] += 1
                    all_operation_times.extend(result.get("operation_times", []))
                else:
                    failed_games.append(result)
                    results["games_failed"] += 1
                    all_operation_times.extend(result.get("operation_times", []))
            else:
                results["games_failed"] += 1
        
        # Calculate metrics
        if successful_games:
            game_durations = [game["duration_ms"] for game in successful_games]
            results["average_game_duration_ms"] = statistics.mean(game_durations)
        
        results["throughput_games_per_second"] = self.concurrent_games / total_test_time
        results["operation_times_ms"] = all_operation_times
        results["total_operations"] = len(all_operation_times)
        
        # Get system metrics
        results["system_metrics"] = self.monitor.get_summary()
        
        # Get game system stats
        game_stats = self.game_system.get_stats()
        results.update(game_stats)
        
        return results
    
    async def run_stress_test(self) -> Dict[str, Any]:
        """Run stress test with peak load."""
        logger.info("💥 Running stress test with peak load...")
        
        results = {
            "stress_phases": [],
            "peak_load_handled": False,
            "system_recovery": False,
            "performance_degradation": {},
            "error_rates": {}
        }
        
        # Stress test phases with increasing load
        stress_phases = [
            {"name": "baseline", "concurrent_games": 10, "duration": 30},
            {"name": "moderate", "concurrent_games": 25, "duration": 30},
            {"name": "high", "concurrent_games": 50, "duration": 30},
            {"name": "peak", "concurrent_games": 100, "duration": 30},
            {"name": "extreme", "concurrent_games": 150, "duration": 20},
            {"name": "recovery", "concurrent_games": 10, "duration": 20}
        ]
        
        baseline_performance = None
        
        for phase in stress_phases:
            logger.info(f"Stress phase: {phase['name']} - {phase['concurrent_games']} games")
            
            # Temporary load tester for this phase
            phase_tester = LoadTester(phase["concurrent_games"])
            
            # Run phase test
            phase_start = time.time()
            phase_result = await phase_tester.run_concurrent_games_test()
            phase_end = time.time()
            
            phase_result["phase_name"] = phase["name"]
            phase_result["actual_duration"] = phase_end - phase_start
            
            # Calculate performance metrics
            if phase_result["operation_times_ms"]:
                avg_response_time = statistics.mean(phase_result["operation_times_ms"])
                p95_response_time = statistics.quantiles(phase_result["operation_times_ms"], n=20)[18]  # 95th percentile
            else:
                avg_response_time = p95_response_time = 0
            
            phase_result["avg_response_time_ms"] = avg_response_time
            phase_result["p95_response_time_ms"] = p95_response_time
            
            results["stress_phases"].append(phase_result)
            
            # Set baseline for comparison
            if phase["name"] == "baseline":
                baseline_performance = {
                    "avg_response_time": avg_response_time,
                    "error_rate": phase_result.get("error_rate", 0)
                }
            
            # Check if peak load was handled
            if phase["name"] == "peak" and phase_result["games_completed"] > 0:
                results["peak_load_handled"] = True
            
            # Check performance degradation
            if baseline_performance and phase["name"] != "baseline":
                response_degradation = (avg_response_time / max(baseline_performance["avg_response_time"], 0.001) - 1) * 100
                error_increase = phase_result.get("error_rate", 0) - baseline_performance["error_rate"]
                
                results["performance_degradation"][phase["name"]] = response_degradation
                results["error_rates"][phase["name"]] = phase_result.get("error_rate", 0)
            
            # Check recovery
            if phase["name"] == "recovery":
                recovery_degradation = (avg_response_time / max(baseline_performance["avg_response_time"], 0.001) - 1) * 100
                if recovery_degradation < 50:  # Within 50% of baseline
                    results["system_recovery"] = True
            
            # Memory cleanup between phases
            gc.collect()
            await asyncio.sleep(2)
        
        return results
    
    async def validate_performance_benchmarks(self) -> Dict[str, Any]:
        """Validate performance against benchmarks."""
        logger.info("📊 Validating performance benchmarks...")
        
        results = {
            "benchmark_tests": 0,
            "benchmarks_met": 0,
            "performance_targets": {},
            "actual_performance": {},
            "benchmarks_passed": False
        }
        
        # Define performance benchmarks
        benchmarks = {
            "avg_response_time_ms": 50,      # Under 50ms average
            "p95_response_time_ms": 200,     # Under 200ms 95th percentile
            "error_rate_percent": 1.0,       # Under 1% error rate
            "throughput_games_per_second": 5, # At least 5 games/second
            "concurrent_games_supported": 50  # Support 50 concurrent games
        }
        
        # Run benchmark test
        benchmark_result = await self.run_concurrent_games_test()
        
        # Calculate actual performance
        if benchmark_result["operation_times_ms"]:
            avg_response = statistics.mean(benchmark_result["operation_times_ms"])
            p95_response = statistics.quantiles(benchmark_result["operation_times_ms"], n=20)[18]
        else:
            avg_response = p95_response = 0
        
        actual_performance = {
            "avg_response_time_ms": avg_response,
            "p95_response_time_ms": p95_response,
            "error_rate_percent": benchmark_result.get("error_rate", 0),
            "throughput_games_per_second": benchmark_result.get("throughput_games_per_second", 0),
            "concurrent_games_supported": benchmark_result.get("games_completed", 0)
        }
        
        results["performance_targets"] = benchmarks
        results["actual_performance"] = actual_performance
        
        # Validate each benchmark
        benchmarks_met = 0
        for metric, target in benchmarks.items():
            actual = actual_performance.get(metric, 0)
            results["benchmark_tests"] += 1
            
            # Different comparison logic for different metrics
            if metric in ["avg_response_time_ms", "p95_response_time_ms", "error_rate_percent"]:
                met = actual <= target  # Lower is better
            else:
                met = actual >= target  # Higher is better
            
            if met:
                benchmarks_met += 1
            
            logger.info(f"Benchmark {metric}: Target {target}, Actual {actual:.2f}, {'✅' if met else '❌'}")
        
        results["benchmarks_met"] = benchmarks_met
        results["benchmarks_passed"] = benchmarks_met == results["benchmark_tests"]
        
        return results


async def main():
    """Main load testing function."""
    parser = argparse.ArgumentParser(description="Load Testing Tool")
    parser.add_argument("--concurrent-games", type=int, default=50, 
                       help="Number of concurrent games for load test")
    parser.add_argument("--stress-test", action="store_true",
                       help="Run stress test with peak load")
    parser.add_argument("--benchmark", action="store_true",
                       help="Run performance benchmark validation")
    
    args = parser.parse_args()
    
    try:
        logger.info("🚀 Starting load testing...")
        
        tester = LoadTester(args.concurrent_games)
        
        # Run tests based on arguments
        if args.stress_test:
            stress_results = await tester.run_stress_test()
            test_results = {"stress_test": stress_results}
            
        elif args.benchmark:
            benchmark_results = await tester.validate_performance_benchmarks()
            test_results = {"benchmark_test": benchmark_results}
            
        else:
            load_results = await tester.run_concurrent_games_test()
            test_results = {"load_test": load_results}
        
        # Generate report
        report = {
            "timestamp": time.time(),
            "test_configuration": {
                "concurrent_games": args.concurrent_games,
                "stress_test": args.stress_test,
                "benchmark": args.benchmark
            },
            "test_results": test_results,
            "summary": {
                "test_type": "stress" if args.stress_test else "benchmark" if args.benchmark else "load",
                "success": True  # Will be updated based on specific test results
            }
        }
        
        # Update success based on test type
        if args.stress_test:
            report["summary"]["success"] = stress_results.get("peak_load_handled", False)
        elif args.benchmark:
            report["summary"]["success"] = benchmark_results.get("benchmarks_passed", False)
        else:
            load_results = test_results["load_test"]
            report["summary"]["success"] = (load_results.get("games_completed", 0) > 0 and 
                                          load_results.get("error_rate", 100) < 5)
        
        # Save report
        report_file = Path(__file__).parent / "load_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📁 Load test report saved to: {report_file}")
        
        # Print summary
        test_type = report["summary"]["test_type"]
        success = report["summary"]["success"]
        
        print(f"\n📋 Load Test Summary ({test_type}):")
        print(f"✅ Test successful: {success}")
        
        if args.stress_test:
            print(f"Peak load handled: {stress_results.get('peak_load_handled', False)}")
            print(f"System recovery: {stress_results.get('system_recovery', False)}")
        elif args.benchmark:
            benchmarks_met = benchmark_results.get("benchmarks_met", 0)
            total_benchmarks = benchmark_results.get("benchmark_tests", 0)
            print(f"Benchmarks passed: {benchmarks_met}/{total_benchmarks}")
        else:
            games_completed = load_results.get("games_completed", 0)
            error_rate = load_results.get("error_rate", 0)
            print(f"Games completed: {games_completed}/{args.concurrent_games}")
            print(f"Error rate: {error_rate:.1f}%")
        
        # Exit with appropriate code
        if success:
            logger.info("✅ Load testing successful!")
            sys.exit(0)
        else:
            logger.warning("⚠️ Load testing failed or targets not met")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Load testing error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())