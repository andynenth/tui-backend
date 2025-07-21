#!/usr/bin/env python3
"""
Load testing suite for rate limiting functionality.

This script simulates heavy load to test:
- Rate limiting effectiveness under stress
- System stability with many concurrent connections
- Memory usage and performance impact
- Proper enforcement of limits across multiple clients

Usage:
    python load_test_rate_limits.py [options]

Options:
    --clients N      Number of concurrent clients (default: 50)
    --duration S     Test duration in seconds (default: 300)
    --api-only       Test only REST API endpoints
    --ws-only        Test only WebSocket connections
    --aggressive     Use aggressive testing patterns
"""

import asyncio
import time
import json
import argparse
import statistics
import psutil
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import aiohttp
import websockets
from collections import defaultdict
import random


@dataclass
class LoadTestConfig:
    """Configuration for load testing."""

    base_url: str = "http://localhost:5050"
    ws_base_url: str = "ws://localhost:5050"
    num_clients: int = 50
    test_duration: int = 300  # 5 minutes
    api_only: bool = False
    ws_only: bool = False
    aggressive: bool = False

    # Test patterns
    normal_delay_range: tuple = (1, 3)  # seconds between requests
    aggressive_delay_range: tuple = (0.1, 0.5)
    burst_size: int = 10  # requests in a burst
    burst_probability: float = 0.1  # 10% chance of burst


@dataclass
class TestMetrics:
    """Metrics collected during testing."""

    total_requests: int = 0
    successful_requests: int = 0
    rate_limited_requests: int = 0
    failed_requests: int = 0
    warnings_received: int = 0

    response_times: List[float] = field(default_factory=list)
    rate_limit_times: List[float] = field(default_factory=list)

    # Per-endpoint/event metrics
    endpoint_stats: Dict[str, Dict[str, int]] = field(
        default_factory=lambda: defaultdict(
            lambda: {"total": 0, "success": 0, "rate_limited": 0, "failed": 0}
        )
    )

    # System metrics
    cpu_usage: List[float] = field(default_factory=list)
    memory_usage: List[float] = field(default_factory=list)

    # WebSocket specific
    ws_connections_created: int = 0
    ws_connections_failed: int = 0
    ws_messages_sent: int = 0
    ws_disconnections: int = 0


class LoadTestClient:
    """Base class for load test clients."""

    def __init__(self, client_id: int, config: LoadTestConfig, metrics: TestMetrics):
        self.client_id = client_id
        self.config = config
        self.metrics = metrics
        self.active = True

    def get_delay(self) -> float:
        """Get delay between requests based on test mode."""
        if self.config.aggressive:
            return random.uniform(*self.config.aggressive_delay_range)
        return random.uniform(*self.config.normal_delay_range)

    def should_burst(self) -> bool:
        """Decide if client should send a burst of requests."""
        return random.random() < self.config.burst_probability


class APILoadTestClient(LoadTestClient):
    """REST API load test client."""

    async def run(self):
        """Run API load test for this client."""
        endpoints = ["/api/health", "/api/rooms", "/api/health/detailed"]

        async with aiohttp.ClientSession() as session:
            while self.active:
                endpoint = random.choice(endpoints)

                if self.should_burst():
                    # Send burst of requests
                    for _ in range(self.config.burst_size):
                        await self._make_request(session, endpoint)
                        await asyncio.sleep(0.1)  # Small delay between burst requests
                else:
                    # Normal request
                    await self._make_request(session, endpoint)

                await asyncio.sleep(self.get_delay())

    async def _make_request(self, session: aiohttp.ClientSession, endpoint: str):
        """Make a single API request and record metrics."""
        url = f"{self.config.base_url}{endpoint}"
        start_time = time.time()

        try:
            async with session.get(url) as response:
                response_time = time.time() - start_time
                self.metrics.response_times.append(response_time)
                self.metrics.total_requests += 1

                if response.status == 200:
                    self.metrics.successful_requests += 1
                    self.metrics.endpoint_stats[endpoint]["success"] += 1
                elif response.status == 429:
                    self.metrics.rate_limited_requests += 1
                    self.metrics.endpoint_stats[endpoint]["rate_limited"] += 1
                    self.metrics.rate_limit_times.append(response_time)

                    # Check for retry-after header
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        await asyncio.sleep(min(int(retry_after), 5))
                else:
                    self.metrics.failed_requests += 1
                    self.metrics.endpoint_stats[endpoint]["failed"] += 1

                self.metrics.endpoint_stats[endpoint]["total"] += 1

        except Exception as e:
            self.metrics.failed_requests += 1
            self.metrics.endpoint_stats[endpoint]["failed"] += 1
            print(f"Client {self.client_id} request failed: {e}")


class WebSocketLoadTestClient(LoadTestClient):
    """WebSocket load test client."""

    async def run(self):
        """Run WebSocket load test for this client."""
        room_id = f"load_test_room_{self.client_id % 10}"  # Distribute across 10 rooms

        try:
            await self._test_websocket_connection(room_id)
        except Exception as e:
            print(f"WebSocket client {self.client_id} error: {e}")
            self.metrics.ws_connections_failed += 1

    async def _test_websocket_connection(self, room_id: str):
        """Test a WebSocket connection with various events."""
        url = f"{self.config.ws_base_url}/ws/{room_id}"

        try:
            async with websockets.connect(url) as websocket:
                self.metrics.ws_connections_created += 1

                # Test different event patterns
                event_patterns = [
                    self._pattern_normal_game,
                    self._pattern_rapid_declarations,
                    self._pattern_ping_spam,
                    self._pattern_mixed_events,
                ]

                pattern = random.choice(event_patterns)
                await pattern(websocket)

        except websockets.exceptions.ConnectionClosed:
            self.metrics.ws_disconnections += 1
        except Exception as e:
            self.metrics.ws_connections_failed += 1
            raise

    async def _pattern_normal_game(self, websocket):
        """Simulate normal game play pattern."""
        player_name = f"LoadTestPlayer{self.client_id}"

        # Join room
        await self._send_event(websocket, "join_room", {"player_name": player_name})
        await asyncio.sleep(1)

        # Ready up
        await self._send_event(websocket, "player_ready", {"player_name": player_name})
        await asyncio.sleep(2)

        # Game loop
        start_time = time.time()
        while self.active and (time.time() - start_time) < 60:  # 1 minute of gameplay
            # Occasional ping
            if random.random() < 0.1:
                await self._send_event(websocket, "ping", {"timestamp": time.time()})

            # Play pieces
            await self._send_event(
                websocket,
                "play_pieces",
                {
                    "player_name": player_name,
                    "pieces": [
                        random.randint(1, 13) for _ in range(random.randint(1, 3))
                    ],
                },
            )

            await asyncio.sleep(self.get_delay())

    async def _pattern_rapid_declarations(self, websocket):
        """Test rapid declaration spam."""
        player_name = f"Spammer{self.client_id}"

        for i in range(20):
            await self._send_event(
                websocket,
                "declare",
                {"player_name": player_name, "pile_count": random.randint(0, 8)},
            )
            await asyncio.sleep(0.5)  # Rapid but not instant

    async def _pattern_ping_spam(self, websocket):
        """Test ping flood."""
        for i in range(200):
            await self._send_event(websocket, "ping", {"timestamp": time.time()})
            await asyncio.sleep(0.1)

    async def _pattern_mixed_events(self, websocket):
        """Mixed event pattern."""
        events = [
            ("get_room_state", {}),
            ("get_rooms", {}),
            ("ping", {"timestamp": time.time()}),
            ("play", {"pieces": [1, 2, 3]}),
            ("declare", {"pile_count": 3}),
        ]

        for _ in range(50):
            event_type, data = random.choice(events)
            await self._send_event(websocket, event_type, data)
            await asyncio.sleep(self.get_delay())

    async def _send_event(self, websocket, event_type: str, data: dict):
        """Send an event and handle the response."""
        message = json.dumps({"event": event_type, "data": data})

        try:
            await websocket.send(message)
            self.metrics.ws_messages_sent += 1
            self.metrics.endpoint_stats[f"ws_{event_type}"]["total"] += 1

            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)

            if response_data.get("event") == "error":
                error_data = response_data.get("data", {})
                if "rate_limit" in str(error_data):
                    self.metrics.rate_limited_requests += 1
                    self.metrics.endpoint_stats[f"ws_{event_type}"]["rate_limited"] += 1
                else:
                    self.metrics.failed_requests += 1
                    self.metrics.endpoint_stats[f"ws_{event_type}"]["failed"] += 1
            elif response_data.get("event") == "rate_limit_warning":
                self.metrics.warnings_received += 1
                # Don't count as failure, just a warning
                self.metrics.successful_requests += 1
                self.metrics.endpoint_stats[f"ws_{event_type}"]["success"] += 1
            else:
                self.metrics.successful_requests += 1
                self.metrics.endpoint_stats[f"ws_{event_type}"]["success"] += 1

        except asyncio.TimeoutError:
            self.metrics.failed_requests += 1
            self.metrics.endpoint_stats[f"ws_{event_type}"]["failed"] += 1
        except Exception as e:
            self.metrics.failed_requests += 1
            self.metrics.endpoint_stats[f"ws_{event_type}"]["failed"] += 1


class LoadTestRunner:
    """Main load test orchestrator."""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.metrics = TestMetrics()
        self.clients: List[LoadTestClient] = []
        self.start_time = None
        self.end_time = None

    async def run(self):
        """Run the load test."""
        print(f"Starting load test with {self.config.num_clients} clients")
        print(f"Test duration: {self.config.test_duration} seconds")
        print(f"Mode: {'Aggressive' if self.config.aggressive else 'Normal'}")
        print("-" * 60)

        self.start_time = time.time()

        # Create monitoring task
        monitor_task = asyncio.create_task(self._monitor_system())

        # Create client tasks
        tasks = []

        if not self.config.ws_only:
            # Create API clients
            api_clients = min(self.config.num_clients // 2, self.config.num_clients)
            for i in range(api_clients):
                client = APILoadTestClient(i, self.config, self.metrics)
                self.clients.append(client)
                tasks.append(asyncio.create_task(client.run()))

        if not self.config.api_only:
            # Create WebSocket clients
            ws_clients_start = (
                0 if self.config.ws_only else self.config.num_clients // 2
            )
            ws_clients_count = (
                self.config.num_clients
                if self.config.ws_only
                else self.config.num_clients - ws_clients_start
            )

            for i in range(ws_clients_count):
                client = WebSocketLoadTestClient(
                    ws_clients_start + i, self.config, self.metrics
                )
                self.clients.append(client)
                tasks.append(asyncio.create_task(client.run()))

        # Run for specified duration
        await asyncio.sleep(self.config.test_duration)

        # Stop all clients
        print("\nStopping clients...")
        for client in self.clients:
            client.active = False

        # Wait for clients to finish
        await asyncio.gather(*tasks, return_exceptions=True)

        # Stop monitoring
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

        self.end_time = time.time()

        # Print results
        self._print_results()

    async def _monitor_system(self):
        """Monitor system metrics during the test."""
        process = psutil.Process(os.getpid())

        while True:
            try:
                # CPU usage
                cpu_percent = process.cpu_percent(interval=1)
                self.metrics.cpu_usage.append(cpu_percent)

                # Memory usage
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                self.metrics.memory_usage.append(memory_mb)

                # Print progress
                elapsed = time.time() - self.start_time
                progress = (elapsed / self.config.test_duration) * 100

                print(
                    f"\rProgress: {progress:.1f}% | "
                    f"Requests: {self.metrics.total_requests} | "
                    f"Rate Limited: {self.metrics.rate_limited_requests} | "
                    f"Failed: {self.metrics.failed_requests} | "
                    f"CPU: {cpu_percent:.1f}% | "
                    f"Memory: {memory_mb:.1f}MB",
                    end="",
                )

                await asyncio.sleep(5)  # Update every 5 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"\nMonitoring error: {e}")

    def _print_results(self):
        """Print comprehensive test results."""
        duration = self.end_time - self.start_time

        print("\n\n" + "=" * 60)
        print("LOAD TEST RESULTS")
        print("=" * 60)

        print(f"\nTest Duration: {duration:.1f} seconds")
        print(f"Total Clients: {self.config.num_clients}")

        # Request statistics
        print("\n--- Request Statistics ---")
        print(f"Total Requests: {self.metrics.total_requests}")
        print(
            f"Successful: {self.metrics.successful_requests} ({self._percentage(self.metrics.successful_requests, self.metrics.total_requests)}%)"
        )
        print(
            f"Rate Limited: {self.metrics.rate_limited_requests} ({self._percentage(self.metrics.rate_limited_requests, self.metrics.total_requests)}%)"
        )
        print(
            f"Failed: {self.metrics.failed_requests} ({self._percentage(self.metrics.failed_requests, self.metrics.total_requests)}%)"
        )
        print(f"Warnings Received: {self.metrics.warnings_received}")

        # Performance metrics
        if self.metrics.response_times:
            print("\n--- Performance Metrics ---")
            print(
                f"Avg Response Time: {statistics.mean(self.metrics.response_times)*1000:.1f}ms"
            )
            print(f"Min Response Time: {min(self.metrics.response_times)*1000:.1f}ms")
            print(f"Max Response Time: {max(self.metrics.response_times)*1000:.1f}ms")
            print(
                f"P95 Response Time: {self._percentile(self.metrics.response_times, 95)*1000:.1f}ms"
            )
            print(
                f"P99 Response Time: {self._percentile(self.metrics.response_times, 99)*1000:.1f}ms"
            )

        # WebSocket specific
        if not self.config.api_only:
            print("\n--- WebSocket Statistics ---")
            print(f"Connections Created: {self.metrics.ws_connections_created}")
            print(f"Connections Failed: {self.metrics.ws_connections_failed}")
            print(f"Messages Sent: {self.metrics.ws_messages_sent}")
            print(f"Disconnections: {self.metrics.ws_disconnections}")

        # Per-endpoint statistics
        print("\n--- Per-Endpoint Statistics ---")
        for endpoint, stats in sorted(self.metrics.endpoint_stats.items()):
            if stats["total"] > 0:
                print(f"\n{endpoint}:")
                print(f"  Total: {stats['total']}")
                print(
                    f"  Success: {stats['success']} ({self._percentage(stats['success'], stats['total'])}%)"
                )
                print(
                    f"  Rate Limited: {stats['rate_limited']} ({self._percentage(stats['rate_limited'], stats['total'])}%)"
                )
                print(
                    f"  Failed: {stats['failed']} ({self._percentage(stats['failed'], stats['total'])}%)"
                )

        # System metrics
        if self.metrics.cpu_usage:
            print("\n--- System Resource Usage ---")
            print(f"Avg CPU Usage: {statistics.mean(self.metrics.cpu_usage):.1f}%")
            print(f"Max CPU Usage: {max(self.metrics.cpu_usage):.1f}%")
            print(
                f"Avg Memory Usage: {statistics.mean(self.metrics.memory_usage):.1f}MB"
            )
            print(f"Max Memory Usage: {max(self.metrics.memory_usage):.1f}MB")

        # Summary
        print("\n--- Summary ---")
        requests_per_second = self.metrics.total_requests / duration
        print(f"Average RPS: {requests_per_second:.1f}")

        if self.metrics.rate_limited_requests > 0:
            print(f"Rate limiting is working correctly!")
            print(
                f"Rate limit enforcement rate: {self._percentage(self.metrics.rate_limited_requests, self.metrics.total_requests)}%"
            )
        else:
            print("Warning: No rate limiting observed. Check configuration.")

        print("\n" + "=" * 60)

    def _percentage(self, part: int, whole: int) -> float:
        """Calculate percentage."""
        return (part / whole * 100) if whole > 0 else 0

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Load test rate limiting implementation"
    )
    parser.add_argument(
        "--clients", type=int, default=50, help="Number of concurrent clients"
    )
    parser.add_argument(
        "--duration", type=int, default=300, help="Test duration in seconds"
    )
    parser.add_argument("--api-only", action="store_true", help="Test only REST API")
    parser.add_argument("--ws-only", action="store_true", help="Test only WebSocket")
    parser.add_argument(
        "--aggressive", action="store_true", help="Use aggressive test patterns"
    )
    parser.add_argument(
        "--base-url", default="http://localhost:5050", help="Base URL for API"
    )
    parser.add_argument(
        "--ws-base-url", default="ws://localhost:5050", help="Base URL for WebSocket"
    )

    args = parser.parse_args()

    config = LoadTestConfig(
        base_url=args.base_url,
        ws_base_url=args.ws_base_url,
        num_clients=args.clients,
        test_duration=args.duration,
        api_only=args.api_only,
        ws_only=args.ws_only,
        aggressive=args.aggressive,
    )

    runner = LoadTestRunner(config)

    try:
        await runner.run()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        runner._print_results()


if __name__ == "__main__":
    asyncio.run(main())
