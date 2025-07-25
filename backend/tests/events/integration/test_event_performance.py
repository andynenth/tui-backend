"""
Performance tests for the event system.

Benchmarks the overhead of the event system compared to direct calls.
"""

import pytest
import asyncio
import time
from typing import Dict, Any, List
from statistics import mean, stdev
from unittest.mock import Mock, AsyncMock, patch

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.adapters.connection_adapters import PingAdapter
from api.adapters.connection_adapters_event import PingAdapterEvent
from api.adapters.unified_adapter_handler import UnifiedAdapterHandler

from backend.domain.events.base import DomainEvent, EventMetadata
from backend.domain.events.all_events import (
    RoomCreated, PlayerJoinedRoom, PiecesPlayed
)
from backend.infrastructure.events.in_memory_event_bus import (
    InMemoryEventBus, get_event_bus, reset_event_bus
)


class MockWebSocket:
    """Mock WebSocket for testing."""
    def __init__(self, player_id: str = "player123"):
        self.id = f"ws_{player_id}"
        self.player_id = player_id
        self.room_id = "room123"


class TestEventSystemPerformance:
    """Performance benchmarks for the event system."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset event bus before each test."""
        reset_event_bus()
    
    @pytest.mark.asyncio
    async def test_event_bus_publish_performance(self):
        """Benchmark event bus publishing performance."""
        bus = InMemoryEventBus()
        
        # Add some handlers
        handler_calls = 0
        
        async def handler1(event: DomainEvent):
            nonlocal handler_calls
            handler_calls += 1
        
        async def handler2(event: DomainEvent):
            nonlocal handler_calls
            handler_calls += 1
        
        async def handler3(event: DomainEvent):
            nonlocal handler_calls
            handler_calls += 1
        
        # Subscribe handlers
        bus.subscribe(RoomCreated, handler1)
        bus.subscribe(RoomCreated, handler2)
        bus.subscribe(RoomCreated, handler3)
        
        # Create test event
        metadata = EventMetadata(user_id="test")
        event = RoomCreated(room_id="room123", host_name="Alice", metadata=metadata)
        
        # Warm up
        for _ in range(100):
            await bus.publish(event)
        
        # Benchmark
        iterations = 1000
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            await bus.publish(event)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Calculate metrics
        avg_time_ms = (total_time / iterations) * 1000
        events_per_second = iterations / total_time
        
        print(f"\nEvent Bus Performance:")
        print(f"  Total events: {iterations}")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Average time per event: {avg_time_ms:.3f}ms")
        print(f"  Events per second: {events_per_second:.0f}")
        print(f"  Total handler calls: {handler_calls}")
        
        # Assert reasonable performance
        assert avg_time_ms < 1.0  # Should be under 1ms per event
        assert events_per_second > 1000  # Should handle >1000 events/sec
    
    @pytest.mark.asyncio
    async def test_adapter_comparison_performance(self):
        """Compare performance of direct vs event-based adapters."""
        websocket = MockWebSocket()
        
        # Test message
        message = {
            "action": "ping",
            "data": {"timestamp": 1234567890}
        }
        
        # Direct adapter
        direct_adapter = PingAdapter()
        
        # Event adapter with minimal handlers
        event_adapter = PingAdapterEvent()
        
        # Warm up both
        for _ in range(100):
            await direct_adapter.handle(websocket, message)
            await event_adapter.handle(websocket, message)
        
        # Benchmark direct adapter
        iterations = 1000
        direct_times = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            await direct_adapter.handle(websocket, message)
            end = time.perf_counter()
            direct_times.append(end - start)
        
        # Benchmark event adapter
        event_times = []
        
        for _ in range(iterations):
            start = time.perf_counter()
            await event_adapter.handle(websocket, message)
            end = time.perf_counter()
            event_times.append(end - start)
        
        # Calculate statistics
        direct_avg_ms = mean(direct_times) * 1000
        event_avg_ms = mean(event_times) * 1000
        
        direct_stdev_ms = stdev(direct_times) * 1000
        event_stdev_ms = stdev(event_times) * 1000
        
        overhead_ms = event_avg_ms - direct_avg_ms
        overhead_percent = (overhead_ms / direct_avg_ms) * 100
        
        print(f"\nAdapter Performance Comparison:")
        print(f"  Iterations: {iterations}")
        print(f"  Direct adapter: {direct_avg_ms:.3f}ms ± {direct_stdev_ms:.3f}ms")
        print(f"  Event adapter: {event_avg_ms:.3f}ms ± {event_stdev_ms:.3f}ms")
        print(f"  Overhead: {overhead_ms:.3f}ms ({overhead_percent:.1f}%)")
        
        # Assert reasonable overhead
        assert overhead_percent < 50  # Should be less than 50% overhead
    
    @pytest.mark.asyncio
    async def test_event_handling_scalability(self):
        """Test how event system scales with many handlers."""
        bus = InMemoryEventBus()
        
        # Test with increasing number of handlers
        handler_counts = [1, 5, 10, 20, 50]
        results = []
        
        for count in handler_counts:
            # Clear handlers
            bus.clear_all_handlers()
            
            # Add handlers
            for i in range(count):
                async def handler(event: DomainEvent, idx=i):
                    pass  # Minimal work
                
                bus.subscribe(PiecesPlayed, handler)
            
            # Create test event
            metadata = EventMetadata(user_id="test")
            event = PiecesPlayed(
                room_id="room123",
                player_name="Alice",
                pieces=["p1", "p2"],
                metadata=metadata
            )
            
            # Benchmark
            iterations = 500
            start_time = time.perf_counter()
            
            for _ in range(iterations):
                await bus.publish(event)
            
            end_time = time.perf_counter()
            avg_time_ms = ((end_time - start_time) / iterations) * 1000
            
            results.append({
                "handlers": count,
                "avg_time_ms": avg_time_ms
            })
        
        print(f"\nEvent Handling Scalability:")
        print(f"  {'Handlers':<10} {'Avg Time (ms)':<15} {'Per Handler (μs)':<20}")
        print(f"  {'-'*45}")
        
        for result in results:
            per_handler_us = (result['avg_time_ms'] / result['handlers']) * 1000
            print(f"  {result['handlers']:<10} {result['avg_time_ms']:<15.3f} {per_handler_us:<20.1f}")
        
        # Check linear scaling
        # Time should scale roughly linearly with handler count
        if len(results) > 1:
            first_per_handler = results[0]['avg_time_ms']
            last_per_handler = results[-1]['avg_time_ms'] / results[-1]['handlers']
            
            # Per-handler time should not increase dramatically
            scaling_factor = last_per_handler / first_per_handler
            assert scaling_factor < 2.0  # Should not double per-handler time
    
    @pytest.mark.asyncio
    async def test_event_bus_memory_usage(self):
        """Test memory efficiency of event storage and handling."""
        bus = InMemoryEventBus()
        
        # Add a handler that stores events
        stored_events = []
        
        async def storage_handler(event: DomainEvent):
            stored_events.append(event)
        
        bus.subscribe(DomainEvent, storage_handler)
        
        # Publish many events
        event_count = 10000
        metadata = EventMetadata(user_id="test")
        
        start_time = time.perf_counter()
        
        for i in range(event_count):
            event = RoomCreated(
                room_id=f"room{i}",
                host_name=f"Host{i}",
                metadata=metadata
            )
            await bus.publish(event)
        
        end_time = time.perf_counter()
        
        # Check performance didn't degrade
        total_time = end_time - start_time
        avg_time_ms = (total_time / event_count) * 1000
        
        print(f"\nMemory Usage Test:")
        print(f"  Events published: {event_count}")
        print(f"  Events stored: {len(stored_events)}")
        print(f"  Average publish time: {avg_time_ms:.3f}ms")
        print(f"  Total time: {total_time:.2f}s")
        
        # Should maintain performance even with many events
        assert avg_time_ms < 1.0
        assert len(stored_events) == event_count
    
    @pytest.mark.asyncio
    async def test_concurrent_event_publishing(self):
        """Test performance with concurrent event publishing."""
        bus = InMemoryEventBus()
        
        # Add some handlers
        handler_count = 0
        
        async def handler(event: DomainEvent):
            nonlocal handler_count
            handler_count += 1
            await asyncio.sleep(0.001)  # Simulate some work
        
        bus.subscribe(DomainEvent, handler)
        
        # Create events
        events = []
        metadata = EventMetadata(user_id="test")
        
        for i in range(100):
            events.append(PlayerJoinedRoom(
                room_id="room123",
                player_name=f"Player{i}",
                slot=i % 4 + 1,
                metadata=metadata
            ))
        
        # Publish concurrently
        start_time = time.perf_counter()
        
        await asyncio.gather(*[bus.publish(event) for event in events])
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        print(f"\nConcurrent Publishing Performance:")
        print(f"  Events published: {len(events)}")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Events per second: {len(events) / total_time:.0f}")
        print(f"  Handler calls: {handler_count}")
        
        # Should handle concurrent publishing efficiently
        assert handler_count == len(events)
        assert total_time < 1.0  # Should complete in under 1 second


class TestPerformanceRegression:
    """Regression tests to ensure performance doesn't degrade."""
    
    @pytest.mark.asyncio
    async def test_baseline_adapter_performance(self):
        """Establish baseline performance metrics."""
        websocket = MockWebSocket()
        message = {"action": "ping", "data": {}}
        
        # Direct adapter baseline
        direct_adapter = PingAdapter()
        
        # Run many iterations
        iterations = 10000
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            await direct_adapter.handle(websocket, message)
        
        end_time = time.perf_counter()
        
        avg_time_us = ((end_time - start_time) / iterations) * 1_000_000
        
        print(f"\nBaseline Performance:")
        print(f"  Direct adapter: {avg_time_us:.1f}μs per call")
        
        # Should be very fast (microseconds)
        assert avg_time_us < 100  # Under 100 microseconds


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])