# backend/tests/test_realtime_system_integration.py

import pytest
import pytest_asyncio
import asyncio
import time
import os
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.realtime_game_system import (
    RealtimeGameSystem,
    initialize_realtime_system,
    shutdown_realtime_system
)
from backend.services.game_cache import GameCache
from backend.services.historical_writer import HistoricalWriter
from backend.engine.game import Game
from backend.engine.player import Player


class TestRealtimeSystemIntegration:
    """
    Integration tests for Phase 4 Real-time Cache System.
    
    Tests the complete integration of:
    - GameCache for in-memory storage
    - CachedEventStore for write-through caching
    - HistoricalWriter for async batch processing
    - CachedGameRecovery for fast game recovery
    """
    
    @pytest_asyncio.fixture
    async def realtime_system(self):
        """Create and initialize a test realtime system."""
        # Set test configuration
        os.environ["REALTIME_CACHE_ENABLED"] = "true"
        os.environ["ASYNC_HISTORICAL_WRITES"] = "true"
        os.environ["GAME_CACHE_SIZE"] = "10"
        os.environ["GAME_CACHE_TTL"] = "300"
        os.environ["HISTORICAL_BATCH_SIZE"] = "5"
        os.environ["HISTORICAL_BATCH_INTERVAL"] = "1.0"
        
        system = RealtimeGameSystem()
        await system.initialize()
        
        yield system
        
        await system.shutdown()
    
    @pytest.fixture
    def sample_game_state(self) -> Dict[str, Any]:
        """Create sample game state for testing."""
        return {
            "room_id": "test-room-123",
            "status": "active",
            "players": [
                {"player_name": "Alice", "player_type": "human"},
                {"player_name": "Bob", "player_type": "ai"},
                {"player_name": "Charlie", "player_type": "ai"},
                {"player_name": "David", "player_type": "ai"}
            ],
            "round_number": 1,
            "current_phase": "PREPARATION",
            "phase_data": {
                "starter": "Alice",
                "hands_dealt": True
            },
            "scores": {"Alice": 0, "Bob": 0, "Charlie": 0, "David": 0},
            "started_at": "2024-01-01T12:00:00"
        }
    
    @pytest.mark.asyncio
    async def test_system_initialization(self, realtime_system):
        """Test that all system components initialize correctly."""
        assert realtime_system._initialized
        assert realtime_system.cache is not None
        assert realtime_system.cached_store is not None
        assert realtime_system.historical_writer is not None
        assert realtime_system.recovery_service is not None
        
        # Check metrics
        metrics = realtime_system.get_metrics()
        assert metrics["initialized"] is True
        assert metrics["cache_enabled"] is True
        assert metrics["async_writes"] is True
    
    @pytest.mark.asyncio
    async def test_realtime_event_storage(self, realtime_system):
        """Test storing real-time critical events."""
        room_id = "test-room-123"
        
        # Store a real-time event (phase change)
        await realtime_system.store_game_event(
            room_id,
            "phase_change",
            {
                "old_phase": "PREPARATION",
                "new_phase": "DECLARATION",
                "phase_data": {"declarations": {}}
            }
        )
        
        # Should be immediately available in cache
        state = await realtime_system.get_game_state(room_id)
        assert state is not None
        assert state["current_phase"] == "DECLARATION"
        
        # Check cache metrics
        cache_metrics = realtime_system.cached_store.cache.get_metrics()
        assert cache_metrics["hits"] == 1  # Cache hit
        assert cache_metrics["size"] == 1   # One game cached
    
    @pytest.mark.asyncio
    async def test_historical_event_queuing(self, realtime_system):
        """Test that non-critical events are queued for async writing."""
        room_id = "test-room-123"
        
        # Store a historical event
        await realtime_system.store_game_event(
            room_id,
            "player_joined",  # Not a real-time critical event
            {
                "player_name": "Eve",
                "timestamp": "2024-01-01T12:05:00"
            }
        )
        
        # Check that it was queued
        writer_metrics = realtime_system.historical_writer.get_metrics()
        assert writer_metrics["events_queued"] >= 1
        
        # Wait for batch interval
        await asyncio.sleep(1.5)
        
        # Check that batch was written
        writer_metrics = realtime_system.historical_writer.get_metrics()
        assert writer_metrics["batches_written"] >= 1
    
    @pytest.mark.asyncio
    async def test_cache_hit_performance(self, realtime_system, sample_game_state):
        """Test that cache provides <100ms response times."""
        room_id = sample_game_state["room_id"]
        
        # Pre-populate cache
        await realtime_system.cached_store.cache.set(room_id, sample_game_state)
        
        # Measure cache hit time
        start_time = time.time()
        state = await realtime_system.get_game_state(room_id)
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert state is not None
        assert elapsed_ms < 100  # Should be well under 100ms for cache hit
        
        # Verify it was a cache hit
        metrics = realtime_system.cached_store.get_metrics()
        assert metrics["cache_hit_rate"] > 0
    
    @pytest.mark.asyncio
    async def test_game_recovery_with_cache(self, realtime_system, sample_game_state):
        """Test game recovery using cached data."""
        room_id = sample_game_state["room_id"]
        
        # Store game state in cache
        await realtime_system.cached_store.cache.set(room_id, sample_game_state)
        
        # Recover game
        with patch('backend.services.cached_game_recovery.CachedGameRecoveryService._reconstruct_game') as mock_reconstruct:
            mock_game = MagicMock(spec=Game)
            mock_game.round_number = 1
            mock_game.current_phase = "PREPARATION"
            mock_reconstruct.return_value = mock_game
            
            recovered_game = await realtime_system.recover_game(room_id)
            
            assert recovered_game is not None
            assert recovered_game.round_number == 1
            assert recovered_game.current_phase == "PREPARATION"
            
            # Verify cache was used
            recovery_metrics = realtime_system.recovery_service.get_metrics()
            assert recovery_metrics["cache_hits"] > 0
    
    @pytest.mark.asyncio
    async def test_cache_eviction(self, realtime_system):
        """Test LRU cache eviction when cache is full."""
        # Set small cache size
        realtime_system.cached_store.cache.max_size = 3
        
        # Fill cache beyond capacity
        for i in range(5):
            await realtime_system.store_game_event(
                f"room-{i}",
                "game_started",
                {"players": [], "started_at": f"2024-01-01T12:0{i}:00"}
            )
        
        # Check cache metrics
        cache_metrics = realtime_system.cached_store.cache.get_metrics()
        assert cache_metrics["size"] == 3  # Only 3 games cached
        assert cache_metrics["evictions"] >= 2  # At least 2 evictions
        
        # Oldest rooms should be evicted
        state = await realtime_system.get_game_state("room-0")
        assert state is None or realtime_system.cached_store._cache_reads < realtime_system.cached_store._db_reads
    
    @pytest.mark.asyncio
    async def test_priority_event_handling(self, realtime_system):
        """Test that priority events are processed first."""
        room_id = "test-room-123"
        
        # Queue several normal events
        for i in range(5):
            await realtime_system.store_game_event(
                room_id,
                "chat_message",  # Non-critical
                {"message": f"Hello {i}"},
                priority=False
            )
        
        # Queue a priority event
        await realtime_system.store_game_event(
            room_id,
            "game_abandoned",  # Critical event
            {"reason": "player_disconnected"},
            priority=True
        )
        
        # Check queue state
        writer = realtime_system.historical_writer
        async with writer._lock:
            # Priority queue should have the critical event
            assert len(writer._priority_queue) == 1
            assert len(writer._normal_queue) == 5
    
    @pytest.mark.asyncio
    async def test_system_health_check(self, realtime_system, sample_game_state):
        """Test system health monitoring."""
        # Populate some data
        await realtime_system.store_game_event(
            "room-1",
            "game_started",
            sample_game_state
        )
        
        # Perform health check
        health = await realtime_system.health_check()
        
        assert health["status"] == "healthy"
        assert "cache" in health["components"]
        assert health["components"]["cache"]["status"] == "healthy"
        
        if "historical_writer" in health["components"]:
            assert health["components"]["historical_writer"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, realtime_system):
        """Test system behavior under concurrent access."""
        room_id = "concurrent-test"
        
        async def store_event(event_num: int):
            await realtime_system.store_game_event(
                room_id,
                "player_action",
                {"action": f"move_{event_num}", "timestamp": time.time()}
            )
        
        # Store multiple events concurrently
        tasks = [store_event(i) for i in range(10)]
        await asyncio.gather(*tasks)
        
        # All events should be handled
        writer_metrics = realtime_system.historical_writer.get_metrics()
        cache_metrics = realtime_system.cached_store.cache.get_metrics()
        
        # Some events written to cache, some queued
        assert writer_metrics["events_queued"] + cache_metrics["writes"] >= 10
    
    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, realtime_system):
        """Test that cached entries expire after TTL."""
        room_id = "ttl-test"
        
        # Set short TTL for testing
        realtime_system.cached_store.cache.ttl_seconds = 1
        
        # Store game state
        await realtime_system.store_game_event(
            room_id,
            "game_started",
            {"players": [], "started_at": "2024-01-01T12:00:00"}
        )
        
        # Verify it's cached
        state = await realtime_system.get_game_state(room_id)
        assert state is not None
        
        # Wait for TTL to expire
        await asyncio.sleep(2)
        
        # Trigger cleanup
        await realtime_system.cached_store.cache._cleanup_expired()
        
        # Should be evicted from cache
        cache_metrics = realtime_system.cached_store.cache.get_metrics()
        assert cache_metrics["evictions"] >= 1
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, realtime_system):
        """Test that system shuts down gracefully with pending events."""
        # Queue some events
        for i in range(3):
            await realtime_system.store_game_event(
                f"shutdown-test-{i}",
                "test_event",
                {"data": f"test_{i}"}
            )
        
        # Shutdown should flush pending events
        await realtime_system.shutdown()
        
        # System should be marked as not initialized
        assert not realtime_system._initialized
        
        # Metrics should still be available
        metrics = realtime_system.get_metrics()
        assert metrics["initialized"] is False


@pytest.mark.asyncio
async def test_global_system_lifecycle():
    """Test global system initialization and shutdown."""
    # Initialize global system
    system = await initialize_realtime_system()
    assert system is not None
    assert system._initialized
    
    # Store some test data
    await system.store_game_event(
        "global-test",
        "game_started",
        {"players": [], "started_at": "2024-01-01T12:00:00"}
    )
    
    # Shutdown global system
    await shutdown_realtime_system()
    
    # Should be able to reinitialize
    system2 = await initialize_realtime_system()
    assert system2 is not None
    assert system2._initialized
    
    # Cleanup
    await shutdown_realtime_system()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])