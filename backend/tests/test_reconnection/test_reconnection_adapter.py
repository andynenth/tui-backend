"""
Tests for the reconnection adapter.

These tests verify that the adapter correctly integrates the clean
architecture reconnection system with the existing WebSocket infrastructure.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from domain.entities.room import Room
from domain.entities.player import Player
from domain.entities.game import Game
from infrastructure.adapters import ReconnectionAdapter
from infrastructure.feature_flags import FeatureFlagService


@pytest.mark.asyncio
async def test_adapter_respects_feature_flag():
    """Test adapter checks feature flag before processing."""
    # Arrange
    feature_flags = Mock(spec=FeatureFlagService)
    feature_flags.is_enabled.return_value = False

    adapter = ReconnectionAdapter(feature_flags)

    # Act
    result = await adapter.handle_disconnect("room-123", "player1")

    # Assert
    assert result["status"] == "skipped"
    assert result["reason"] == "feature_disabled"
    feature_flags.is_enabled.assert_called_with("use_clean_reconnection", "room-123")


@pytest.mark.asyncio
async def test_adapter_handle_disconnect_success():
    """Test successful disconnect handling through adapter."""
    # Arrange
    feature_flags = Mock(spec=FeatureFlagService)
    feature_flags.is_enabled.return_value = True

    adapter = ReconnectionAdapter(feature_flags)

    # Mock the underlying infrastructure
    with patch.object(adapter._uow, "rooms") as mock_rooms, patch.object(
        adapter._uow, "games"
    ) as mock_games:

        # Setup room and game
        room = Room(room_id="room-123", host_name="player1")
        room.add_player(Player("player1"))
        mock_rooms.get_by_id = AsyncMock(return_value=room)
        mock_rooms.save = AsyncMock()

        game = Game(room_id="room-123", players=[])
        mock_games.get_by_room_id = AsyncMock(return_value=game)

        # Act
        result = await adapter.handle_disconnect(
            "room-123", "player1", activate_bot=True
        )

        # Assert
        assert result["status"] == "success"
        assert result["bot_activated"] == True
        assert result["queue_created"] == True


@pytest.mark.asyncio
async def test_adapter_handle_reconnect_success():
    """Test successful reconnect handling through adapter."""
    # Arrange
    feature_flags = Mock(spec=FeatureFlagService)
    feature_flags.is_enabled.return_value = True

    adapter = ReconnectionAdapter(feature_flags)

    # Mock the underlying infrastructure
    with patch.object(adapter._uow, "rooms") as mock_rooms, patch.object(
        adapter._uow, "message_queues"
    ) as mock_queues:

        # Setup disconnected player
        room = Room(room_id="room-123", host_name="player1")
        player = Player("player1")
        player.disconnect("room-123", activate_bot=True)
        room.add_player(player)
        mock_rooms.get_by_id = AsyncMock(return_value=room)
        mock_rooms.save = AsyncMock()

        # No queued messages
        mock_queues.get_queue = AsyncMock(return_value=None)

        # Act
        result = await adapter.handle_reconnect("room-123", "player1", "ws-456")

        # Assert
        assert result["status"] == "success"
        assert result["bot_deactivated"] == True
        assert result["messages_restored"] == 0


@pytest.mark.asyncio
async def test_adapter_queue_message():
    """Test message queueing through adapter."""
    # Arrange
    feature_flags = Mock(spec=FeatureFlagService)
    feature_flags.is_enabled.return_value = True

    adapter = ReconnectionAdapter(feature_flags)

    # Mock the queue creation
    with patch.object(adapter._message_queue_service, "queue_message") as mock_queue:
        mock_queue.return_value = True

        # Act
        result = await adapter.queue_message(
            room_id="room-123",
            player_name="player1",
            event_type="test_event",
            event_data={"test": True},
            is_critical=True,
        )

        # Assert
        assert result == True
        mock_queue.assert_called_once()


@pytest.mark.asyncio
async def test_adapter_get_connection_status():
    """Test getting connection status through adapter."""
    # Arrange
    feature_flags = Mock(spec=FeatureFlagService)
    feature_flags.is_enabled.return_value = True

    adapter = ReconnectionAdapter(feature_flags)

    # Mock the service
    expected_status = [
        {"player_name": "player1", "status": "connected", "health": "healthy"},
        {"player_name": "player2", "status": "disconnected", "health": "disconnected"},
    ]

    with patch.object(
        adapter._reconnection_service, "check_connection_health"
    ) as mock_check:
        mock_check.return_value = expected_status

        # Act
        result = await adapter.get_connection_status("room-123")

        # Assert
        assert result == expected_status
        mock_check.assert_called_once_with("room-123")


@pytest.mark.asyncio
async def test_adapter_cleanup_disconnected_players():
    """Test cleanup through adapter."""
    # Arrange
    feature_flags = Mock(spec=FeatureFlagService)
    feature_flags.is_enabled.return_value = True

    adapter = ReconnectionAdapter(feature_flags)

    # Mock the service
    with patch.object(
        adapter._reconnection_service, "cleanup_disconnected_players"
    ) as mock_cleanup:
        mock_cleanup.return_value = 2  # 2 players cleaned up

        # Act
        result = await adapter.cleanup_disconnected_players(
            "room-123", timeout_minutes=5
        )

        # Assert
        assert result == 2
        mock_cleanup.assert_called_once_with("room-123", 5)


@pytest.mark.asyncio
async def test_adapter_get_queue_stats():
    """Test getting queue stats through adapter."""
    # Arrange
    feature_flags = Mock(spec=FeatureFlagService)
    feature_flags.is_enabled.return_value = True

    adapter = ReconnectionAdapter(feature_flags)

    # Mock the service
    expected_stats = {
        "room_id": "room-123",
        "total_queues": 2,
        "total_messages": 5,
        "players": [],
    }

    with patch.object(adapter._message_queue_service, "get_queue_stats") as mock_stats:
        mock_stats.return_value = expected_stats

        # Act
        result = await adapter.get_queue_stats("room-123")

        # Assert
        assert result == expected_stats
        mock_stats.assert_called_once_with("room-123")


@pytest.mark.asyncio
async def test_adapter_error_handling():
    """Test adapter handles errors gracefully."""
    # Arrange
    feature_flags = Mock(spec=FeatureFlagService)
    feature_flags.is_enabled.return_value = True

    adapter = ReconnectionAdapter(feature_flags)

    # Mock to raise error
    with patch.object(adapter._disconnect_use_case, "execute") as mock_execute:
        mock_execute.side_effect = Exception("Test error")

        # Act
        result = await adapter.handle_disconnect("room-123", "player1")

        # Assert
        assert result["status"] == "error"
        assert "Test error" in result["error"]


@pytest.mark.asyncio
async def test_adapter_is_enabled():
    """Test checking if adapter is enabled."""
    # Arrange
    feature_flags = Mock(spec=FeatureFlagService)
    feature_flags.is_enabled.return_value = True

    adapter = ReconnectionAdapter(feature_flags)

    # Act
    enabled = adapter.is_enabled("room-123")

    # Assert
    assert enabled == True
    feature_flags.is_enabled.assert_called_with("use_clean_reconnection", "room-123")
