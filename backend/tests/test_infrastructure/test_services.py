"""
Tests for infrastructure service implementations.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from infrastructure.services.websocket_notification_service import (
    WebSocketNotificationService,
)
from infrastructure.services.simple_bot_service import SimpleBotService
from infrastructure.services.in_memory_cache_service import InMemoryCacheService
from infrastructure.services.console_metrics_collector import ConsoleMetricsCollector


class TestWebSocketNotificationService:
    """Test WebSocket notification service."""

    @pytest.mark.asyncio
    async def test_notify_player(self):
        """Test notifying a single player."""
        service = WebSocketNotificationService()

        with patch(
            "infrastructure.services.websocket_notification_service.broadcast"
        ) as mock_broadcast:
            mock_broadcast.return_value = asyncio.create_task(asyncio.sleep(0))

            await service.notify_player("player1", "test_event", {"message": "Hello"})

            mock_broadcast.assert_called_once_with(
                "player1", "test_event", {"message": "Hello"}
            )

    @pytest.mark.asyncio
    async def test_notify_room(self):
        """Test notifying all players in a room."""
        service = WebSocketNotificationService()

        with patch(
            "infrastructure.services.websocket_notification_service.broadcast"
        ) as mock_broadcast:
            mock_broadcast.return_value = asyncio.create_task(asyncio.sleep(0))

            await service.notify_room("room1", "game_update", {"state": "playing"})

            mock_broadcast.assert_called_once_with(
                "room1", "game_update", {"state": "playing"}
            )

    @pytest.mark.asyncio
    async def test_notify_players_multiple(self):
        """Test notifying multiple specific players."""
        service = WebSocketNotificationService()

        with patch(
            "infrastructure.services.websocket_notification_service.broadcast"
        ) as mock_broadcast:
            mock_broadcast.return_value = asyncio.create_task(asyncio.sleep(0))

            await service.notify_players(
                ["player1", "player2", "player3"],
                "announcement",
                {"text": "Game starting soon"},
            )

            # Should broadcast to each player
            assert mock_broadcast.call_count == 3
            calls = mock_broadcast.call_args_list

            assert calls[0][0] == (
                "player1",
                "announcement",
                {"text": "Game starting soon"},
            )
            assert calls[1][0] == (
                "player2",
                "announcement",
                {"text": "Game starting soon"},
            )
            assert calls[2][0] == (
                "player3",
                "announcement",
                {"text": "Game starting soon"},
            )

    @pytest.mark.asyncio
    async def test_broadcast_error_handling(self):
        """Test error handling during broadcast."""
        service = WebSocketNotificationService()

        with patch(
            "infrastructure.services.websocket_notification_service.broadcast"
        ) as mock_broadcast:
            mock_broadcast.side_effect = Exception("Network error")

            # Should not raise exception
            await service.notify_player("player1", "test_event", {"data": "test"})

            # Error should be logged but not raised
            mock_broadcast.assert_called_once()


class TestSimpleBotService:
    """Test simple bot service."""

    @pytest.fixture
    def mock_bot_manager(self):
        """Create mock bot manager."""
        manager = Mock()
        manager.room_manager = Mock()
        manager.room_manager.rooms = {}
        return manager

    @pytest.fixture
    def service(self, mock_bot_manager):
        """Create bot service with mocked manager."""
        with patch(
            "infrastructure.services.simple_bot_service.shared_bot_manager",
            mock_bot_manager,
        ):
            return SimpleBotService()

    @pytest.mark.asyncio
    async def test_should_bot_play_true(self, service, mock_bot_manager):
        """Test checking if bot should play - true case."""
        # Setup room with bot player
        room = Mock()
        slot = Mock()
        slot.name = "bot_player"
        slot.is_bot = True
        room.slots = [slot, None, None, None]

        mock_bot_manager.room_manager.rooms["room1"] = room

        result = await service.should_bot_play("room1", "bot_player", "TURN")
        assert result is True

    @pytest.mark.asyncio
    async def test_should_bot_play_false(self, service, mock_bot_manager):
        """Test checking if bot should play - false case."""
        # Setup room with human player
        room = Mock()
        slot = Mock()
        slot.name = "human_player"
        slot.is_bot = False
        room.slots = [slot, None, None, None]

        mock_bot_manager.room_manager.rooms["room1"] = room

        result = await service.should_bot_play("room1", "human_player", "TURN")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_bot_decision_declaration(self, service):
        """Test bot decision for declaration."""
        decision = await service.get_bot_decision("room1", "bot1", {}, "declaration")

        # Should return a valid declaration (0-7)
        assert isinstance(decision, int)
        assert 0 <= decision <= 7

    @pytest.mark.asyncio
    async def test_get_bot_decision_play(self, service):
        """Test bot decision for playing pieces."""
        decision = await service.get_bot_decision("room1", "bot1", {}, "play")

        # Should return play action
        assert isinstance(decision, dict)
        assert "pieces" in decision
        assert "action" in decision
        assert decision["action"] == "play"

    @pytest.mark.asyncio
    async def test_get_bot_decision_redeal(self, service):
        """Test bot decision for redeal."""
        decision = await service.get_bot_decision("room1", "bot1", {}, "redeal")

        # Should always accept redeal
        assert decision is True

    @pytest.mark.asyncio
    async def test_trigger_bot_action(self, service, mock_bot_manager):
        """Test triggering bot action."""
        mock_bot_manager.schedule_bot_action = AsyncMock()

        await service.trigger_bot_action("room1", "bot1", "declare")

        mock_bot_manager.schedule_bot_action.assert_called_once_with(
            "room1", "bot1", "declare"
        )

    @pytest.mark.asyncio
    async def test_replace_player_with_bot(self, service, mock_bot_manager):
        """Test replacing player with bot."""
        mock_bot_manager.replace_player_with_bot = AsyncMock(return_value=True)

        result = await service.replace_player_with_bot("room1", "player1")

        assert result == "Bot_player1"
        mock_bot_manager.replace_player_with_bot.assert_called_once_with(
            "room1", "player1"
        )

    @pytest.mark.asyncio
    async def test_get_bot_stats(self, service, mock_bot_manager):
        """Test getting bot statistics."""
        # Setup room with mixed players
        room = Mock()
        slot1 = Mock()
        slot1.name = "bot1"
        slot1.is_bot = True

        slot2 = Mock()
        slot2.name = "human1"
        slot2.is_bot = False

        slot3 = Mock()
        slot3.name = "bot2"
        slot3.is_bot = True

        room.slots = [slot1, slot2, slot3, None]

        mock_bot_manager.room_manager.rooms["room1"] = room

        stats = await service.get_bot_stats("room1")

        assert stats["bot_count"] == 2
        assert stats["bot_names"] == ["bot1", "bot2"]
        assert stats["total_players"] == 3


class TestInMemoryCacheService:
    """Test in-memory cache service."""

    @pytest.fixture
    def service(self):
        """Create cache service."""
        return InMemoryCacheService()

    @pytest.mark.asyncio
    async def test_basic_get_set(self, service):
        """Test basic get/set operations."""
        # Set value
        await service.set("key1", "value1")

        # Get value
        value = await service.get("key1")
        assert value == "value1"

        # Get non-existent key
        value = await service.get("non_existent")
        assert value is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, service):
        """Test TTL expiration."""
        # Set with 1 second TTL
        await service.set("expire_key", "expire_value", ttl=1)

        # Should exist immediately
        assert await service.exists("expire_key") is True

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired
        assert await service.exists("expire_key") is False
        assert await service.get("expire_key") is None

    @pytest.mark.asyncio
    async def test_delete_operation(self, service):
        """Test delete operation."""
        # Set value
        await service.set("delete_key", "delete_value")

        # Delete it
        result = await service.delete("delete_key")
        assert result is True

        # Should not exist
        assert await service.exists("delete_key") is False

        # Delete non-existent key
        result = await service.delete("non_existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear_operation(self, service):
        """Test clear operation."""
        # Set multiple values
        await service.set("key1", "value1")
        await service.set("key2", "value2")
        await service.set("key3", "value3")

        # Clear all
        await service.clear()

        # All should be gone
        assert await service.get("key1") is None
        assert await service.get("key2") is None
        assert await service.get("key3") is None

    @pytest.mark.asyncio
    async def test_cache_stats(self, service):
        """Test cache statistics."""
        # Generate some activity
        await service.set("key1", "value1")
        await service.set("key2", "value2")

        # Hits
        await service.get("key1")
        await service.get("key1")

        # Misses
        await service.get("non_existent")

        # Delete
        await service.delete("key2")

        stats = service.get_stats()

        assert stats["entries"] == 1  # Only key1 remains
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["sets"] == 2
        assert stats["deletes"] == 1
        assert stats["hit_rate"] == 2 / 3  # 2 hits out of 3 total requests

    @pytest.mark.asyncio
    async def test_cleanup_task(self, service):
        """Test automatic cleanup of expired entries."""
        # Cancel the default cleanup task to control timing
        service._cleanup_task.cancel()

        # Add entries with short TTL
        await service.set("expire1", "value1", ttl=1)
        await service.set("expire2", "value2", ttl=1)
        await service.set("keep", "value3")  # No TTL

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Manually trigger cleanup
        await service._cleanup_loop.__wrapped__(service)

        # Check that expired entries are gone
        assert len(service._cache) == 1
        assert "keep" in service._cache


class TestConsoleMetricsCollector:
    """Test console metrics collector."""

    @pytest.fixture
    def collector(self):
        """Create metrics collector."""
        return ConsoleMetricsCollector(log_every_n=10)

    def test_increment_counter(self, collector):
        """Test incrementing counters."""
        # Basic increment
        collector.increment("requests")
        collector.increment("requests")
        collector.increment("requests", value=3)

        stats = collector.get_stats()
        assert stats["counters"]["requests"] == 5

        # With tags
        collector.increment("errors", tags={"type": "timeout"})
        collector.increment("errors", tags={"type": "timeout"})
        collector.increment("errors", tags={"type": "invalid"})

        stats = collector.get_stats()
        assert stats["counters"]["errors{type=timeout}"] == 2
        assert stats["counters"]["errors{type=invalid}"] == 1

    def test_gauge_metric(self, collector):
        """Test gauge metrics."""
        # Set gauge values
        collector.gauge("cpu_usage", 45.5)
        collector.gauge("memory_usage", 78.2, tags={"process": "worker"})

        stats = collector.get_stats()
        assert stats["gauges"]["cpu_usage"]["value"] == 45.5
        assert stats["gauges"]["memory_usage{process=worker}"]["value"] == 78.2

        # Update gauge
        collector.gauge("cpu_usage", 52.1)
        stats = collector.get_stats()
        assert stats["gauges"]["cpu_usage"]["value"] == 52.1

    def test_histogram_metric(self, collector):
        """Test histogram metrics."""
        # Record values
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for v in values:
            collector.histogram("response_size", v)

        stats = collector.get_stats()
        hist = stats["histograms"]["response_size"]

        assert hist["count"] == 10
        assert hist["min"] == 10
        assert hist["max"] == 100
        assert hist["p50"] == 55  # Median
        assert hist["p95"] >= 90

    def test_timing_metric(self, collector):
        """Test timing metrics."""
        # Record timings
        timings = [100, 200, 150, 300, 250, 180, 220, 500, 120, 160]
        for t in timings:
            collector.timing("api_latency", t)

        stats = collector.get_stats()
        timing = stats["timings"]["api_latency"]

        assert timing["count"] == 10
        assert timing["min_ms"] == 100
        assert timing["max_ms"] == 500
        assert timing["p50_ms"] == 190  # Median

    def test_slow_operation_warning(self, collector, caplog):
        """Test that slow operations generate warnings."""
        # Record a slow operation (> 1 second)
        collector.timing("slow_operation", 1500)

        # Check that warning was logged
        assert any(
            "Slow operation" in record.message and "1500ms" in record.message
            for record in caplog.records
        )

    def test_tag_sorting(self, collector):
        """Test that tags are sorted consistently."""
        # Add metrics with tags in different orders
        collector.increment("test", tags={"b": "2", "a": "1"})
        collector.increment("test", tags={"a": "1", "b": "2"})

        stats = collector.get_stats()

        # Should have single metric with sorted tags
        assert "test{a=1,b=2}" in stats["counters"]
        assert stats["counters"]["test{a=1,b=2}"] == 2
