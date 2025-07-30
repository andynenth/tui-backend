"""
Tests for player reconnection functionality.

These tests verify that player reconnection is handled correctly,
including bot deactivation and message restoration.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from domain.entities.player import Player
from domain.entities.room import Room
from domain.entities.game import Game
from domain.entities.connection import PlayerConnection
from domain.entities.message_queue import PlayerQueue, QueuedMessage
from domain.value_objects import PlayerId, RoomId, ConnectionStatus
from domain.events import PlayerReconnected
from application.use_cases.connection import HandlePlayerReconnectUseCase
from application.dto.connection import HandlePlayerReconnectRequest
from infrastructure.unit_of_work import InMemoryUnitOfWork


@pytest.mark.asyncio
async def test_player_reconnect_deactivates_bot():
    """Test that reconnecting player deactivates bot."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()
    metrics = Mock()

    use_case = HandlePlayerReconnectUseCase(uow, event_publisher, metrics)

    # Create room with disconnected player who became bot
    room = Room(room_id="ABC123", host_name="player1")

    # Start game and then disconnect player with bot activation
    room.start_game()
    game = room.game

    # Get player from room and disconnect them
    player = room.get_player("player1")
    player.disconnect("ABC123", activate_bot=True)

    async with uow:
        await uow.rooms.save(room)
        await uow.games.save(game)

    # Act
    request = HandlePlayerReconnectRequest(
        room_id="ABC123", player_name="player1", websocket_id="ws-456"
    )
    response = await use_case.execute(request)

    # Assert
    assert response.success
    assert response.bot_deactivated

    # Verify player state
    async with uow:
        updated_room = await uow.rooms.get_by_id("ABC123")
        updated_player = updated_room.get_player("player1")
        assert not updated_player.is_bot  # Bot deactivated
        assert updated_player.is_connected
        assert updated_player.disconnect_time is None


@pytest.mark.asyncio
async def test_player_reconnect_restores_messages():
    """Test that reconnection restores queued messages."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()
    metrics = Mock()

    use_case = HandlePlayerReconnectUseCase(uow, event_publisher, metrics)

    # Create room with disconnected player
    room = Room(room_id="ABC123", host_name="player1")
    # Get player from room and disconnect them
    player = room.get_player("player1")
    player.disconnect("ABC123")

    # Create message queue with messages
    queue = PlayerQueue(player_id=PlayerId("player1"), room_id=RoomId("ABC123"))
    queue.add_message(
        event_type="game_state_update", data={"turn": 5}, is_critical=True
    )
    queue.add_message(
        event_type="player_action",
        data={"action": "play", "pieces": 2},
        is_critical=False,
    )

    async with uow:
        await uow.rooms.save(room)
        await uow.message_queues.save_queue(queue)

    # Act
    request = HandlePlayerReconnectRequest(
        room_id="ABC123", player_name="player1", websocket_id="ws-456"
    )
    response = await use_case.execute(request)

    # Assert
    assert response.success
    assert response.messages_restored == 2
    assert len(response.queued_messages) == 2

    # Verify messages in correct order
    assert response.queued_messages[0]["event_type"] == "game_state_update"
    assert response.queued_messages[0]["is_critical"] == True
    assert response.queued_messages[1]["event_type"] == "player_action"

    # Verify queue cleared
    async with uow:
        cleared_queue = await uow.message_queues.get_queue("ABC123", "player1")
        assert cleared_queue is None


@pytest.mark.asyncio
async def test_player_reconnect_updates_connection():
    """Test that reconnection updates connection record."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()
    metrics = Mock()

    use_case = HandlePlayerReconnectUseCase(uow, event_publisher, metrics)

    # Create room with player
    room = Room(room_id="ABC123", host_name="player1")
    # Get player from room and disconnect them
    player = room.get_player("player1")
    player.disconnect("ABC123")

    # Create disconnected connection
    connection = PlayerConnection(
        player_id=PlayerId("player1"),
        room_id=RoomId("ABC123"),
        status=ConnectionStatus.DISCONNECTED,
        websocket_id="old-ws-123",
    )

    async with uow:
        await uow.rooms.save(room)
        await uow.connections.save(connection)

    # Act
    request = HandlePlayerReconnectRequest(
        room_id="ABC123", player_name="player1", websocket_id="new-ws-456"
    )
    response = await use_case.execute(request)

    # Assert
    assert response.success

    # Verify connection updated
    async with uow:
        updated_conn = await uow.connections.get("ABC123", "player1")
        assert updated_conn.status == ConnectionStatus.CONNECTED
        assert updated_conn.websocket_id == "new-ws-456"
        assert updated_conn.connection_count > 1  # Reconnected


@pytest.mark.asyncio
async def test_player_reconnect_with_current_game_state():
    """Test that reconnection returns current game state."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()
    metrics = Mock()

    use_case = HandlePlayerReconnectUseCase(uow, event_publisher, metrics)

    # Create room with player
    room = Room(room_id="ABC123", host_name="player1")

    # Start game
    room.start_game()
    game = room.game
    game.turn_number = 10
    game.round_number = 3

    # Get player from room and disconnect them
    player = room.get_player("player1")
    player.disconnect("ABC123")

    async with uow:
        await uow.rooms.save(room)
        await uow.games.save(game)

    # Act
    request = HandlePlayerReconnectRequest(
        room_id="ABC123", player_name="player1", websocket_id="ws-456"
    )
    response = await use_case.execute(request)

    # Assert
    assert response.success
    assert response.current_state is not None
    assert response.current_state["turn_number"] == 10
    assert response.current_state["round_number"] == 3


@pytest.mark.asyncio
async def test_player_reconnect_no_messages():
    """Test reconnection when no messages queued."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()
    metrics = Mock()

    use_case = HandlePlayerReconnectUseCase(uow, event_publisher, metrics)

    # Create room with disconnected player
    room = Room(room_id="ABC123", host_name="player1")
    # Get player from room and disconnect them
    player = room.get_player("player1")
    player.disconnect("ABC123")

    async with uow:
        await uow.rooms.save(room)

    # Act
    request = HandlePlayerReconnectRequest(
        room_id="ABC123", player_name="player1", websocket_id="ws-456"
    )
    response = await use_case.execute(request)

    # Assert
    assert response.success
    assert response.messages_restored == 0
    assert len(response.queued_messages) == 0


@pytest.mark.asyncio
async def test_player_reconnect_already_connected():
    """Test reconnecting an already connected player."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()
    metrics = Mock()

    use_case = HandlePlayerReconnectUseCase(uow, event_publisher, metrics)

    # Create room with connected player
    room = Room(room_id="ABC123", host_name="player1")

    async with uow:
        await uow.rooms.save(room)

    # Act
    request = HandlePlayerReconnectRequest(
        room_id="ABC123", player_name="player1", websocket_id="ws-456"
    )
    response = await use_case.execute(request)

    # Assert
    assert response.success
    assert not response.bot_deactivated  # No bot to deactivate
    assert response.messages_restored == 0


@pytest.mark.asyncio
async def test_player_reconnect_publishes_event():
    """Test that reconnection publishes proper event."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()
    metrics = Mock()

    use_case = HandlePlayerReconnectUseCase(uow, event_publisher, metrics)

    # Create room with player
    room = Room(room_id="ABC123", host_name="player1")
    # Get player from room and disconnect them
    player = room.get_player("player1")
    player.disconnect("ABC123", activate_bot=True)

    # Add some queued messages
    queue = PlayerQueue(player_id=PlayerId("player1"), room_id=RoomId("ABC123"))
    queue.add_message(event_type="test", data={}, is_critical=False)

    async with uow:
        await uow.rooms.save(room)
        await uow.message_queues.save_queue(queue)

    # Act
    request = HandlePlayerReconnectRequest(
        room_id="ABC123", player_name="player1", websocket_id="ws-456"
    )
    await use_case.execute(request)

    # Assert event published
    event_publisher.publish.assert_called()

    # Check that PlayerReconnected event was published
    calls = event_publisher.publish.call_args_list
    reconnect_event = None
    for call in calls:
        event = call[0][0]
        if isinstance(event, PlayerReconnected):
            reconnect_event = event
            break

    assert reconnect_event is not None
    assert reconnect_event.room_id == "ABC123"
    assert reconnect_event.player_name == "player1"
    assert reconnect_event.bot_was_deactivated == True
    assert reconnect_event.messages_queued == 1


@pytest.mark.asyncio
async def test_player_reconnect_invalid_room():
    """Test reconnecting to non-existent room fails."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()
    metrics = Mock()

    use_case = HandlePlayerReconnectUseCase(uow, event_publisher, metrics)

    # Act & Assert
    request = HandlePlayerReconnectRequest(
        room_id="NO_ROO", player_name="player1", websocket_id="ws-456"
    )

    response = await use_case.execute(request)

    # Assert
    assert not response.success
    assert response.error == "Room not found"


@pytest.mark.asyncio
async def test_player_reconnect_metrics_collected():
    """Test that reconnection collects metrics."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()
    metrics = Mock()

    use_case = HandlePlayerReconnectUseCase(uow, event_publisher, metrics)

    # Create room with player
    room = Room(room_id="ABC123", host_name="player1")

    async with uow:
        await uow.rooms.save(room)

    # Act
    request = HandlePlayerReconnectRequest(
        room_id="ABC123", player_name="player1", websocket_id="ws-456"
    )
    await use_case.execute(request)

    # Assert metrics collected
    metrics.increment.assert_called()
