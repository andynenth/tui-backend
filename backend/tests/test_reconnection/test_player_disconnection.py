"""
Tests for player disconnection functionality.

These tests verify that player disconnection is handled correctly,
including bot activation and message queue creation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from domain.entities.player import Player
from domain.entities.room import Room
from domain.entities.game import Game
from domain.value_objects import PlayerId, RoomId, ConnectionStatus
from domain.events import PlayerDisconnected
from application.use_cases.connection import HandlePlayerDisconnectUseCase
from application.dto.connection import HandlePlayerDisconnectRequest
from infrastructure.unit_of_work import InMemoryUnitOfWork


@pytest.mark.asyncio
async def test_player_disconnect_activates_bot():
    """Test that disconnecting player activates bot when game in progress."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()
    metrics = Mock()
    
    use_case = HandlePlayerDisconnectUseCase(uow, event_publisher, metrics)
    
    # Create room with player
    room = Room(room_id="ABC123", host_name="player1")
    
    # Start game in the room  
    room.start_game()
    game = room.game
    
    async with uow:
        await uow.rooms.save(room)
        await uow.games.save(game)
    
    # Act
    request = HandlePlayerDisconnectRequest(
        room_id="ABC123",
        player_name="player1",
        activate_bot=True
    )
    response = await use_case.execute(request)
    
    # Assert
    assert response.success
    assert response.bot_activated
    assert response.queue_created
    
    # Verify player state
    async with uow:
        updated_room = await uow.rooms.get_by_id("ABC123")
        updated_player = updated_room.get_player("player1")
        assert updated_player.is_bot
        assert not updated_player.is_connected
        assert updated_player.disconnect_time is not None
    
    # Verify event published
    event_publisher.publish.assert_called()
    calls = event_publisher.publish.call_args_list
    # Find the PlayerDisconnected event
    player_disconnect_event = None
    for call in calls:
        event = call[0][0]
        if isinstance(event, PlayerDisconnected):
            player_disconnect_event = event
            break
    assert player_disconnect_event is not None
    assert player_disconnect_event.was_bot_activated


@pytest.mark.asyncio
async def test_player_disconnect_no_bot_when_no_game():
    """Test that bot is not activated when no game in progress."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()
    metrics = Mock()
    
    use_case = HandlePlayerDisconnectUseCase(uow, event_publisher, metrics)
    
    # Create room with player but no game
    room = Room(room_id="ABC123", host_name="player1")
    
    async with uow:
        await uow.rooms.save(room)
    
    # Act
    request = HandlePlayerDisconnectRequest(
        room_id="ABC123",
        player_name="player1",
        activate_bot=True
    )
    response = await use_case.execute(request)
    
    # Assert
    assert response.success
    assert not response.bot_activated  # No bot because no game
    assert not response.queue_created   # No queue because no game
    
    # Verify player state
    async with uow:
        updated_room = await uow.rooms.get_by_id("ABC123")
        updated_player = updated_room.get_player("player1")
        assert not updated_player.is_bot  # Still not a bot
        assert not updated_player.is_connected
        assert updated_player.disconnect_time is not None


@pytest.mark.asyncio
async def test_player_disconnect_respects_activate_bot_flag():
    """Test that activate_bot=False prevents bot activation."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()
    metrics = Mock()
    
    use_case = HandlePlayerDisconnectUseCase(uow, event_publisher, metrics)
    
    # Create room with player and game
    room = Room(room_id="ABC123", host_name="player1")
    
    # Start game in the room
    room.start_game()
    game = room.game
    
    async with uow:
        await uow.rooms.save(room)
        await uow.games.save(game)
    
    # Act
    request = HandlePlayerDisconnectRequest(
        room_id="ABC123",
        player_name="player1",
        activate_bot=False  # Explicitly disable bot
    )
    response = await use_case.execute(request)
    
    # Assert
    assert response.success
    assert not response.bot_activated
    assert response.queue_created  # Queue still created
    
    # Verify player state
    async with uow:
        updated_room = await uow.rooms.get_by_id("ABC123")
        updated_player = updated_room.get_player("player1")
        assert not updated_player.is_bot


@pytest.mark.asyncio
async def test_player_disconnect_creates_connection_record():
    """Test that disconnection creates/updates connection record."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()
    metrics = Mock()
    
    use_case = HandlePlayerDisconnectUseCase(uow, event_publisher, metrics)
    
    # Create room with player
    room = Room(room_id="ABC123", host_name="player1")
    
    async with uow:
        await uow.rooms.save(room)
    
    # Act
    request = HandlePlayerDisconnectRequest(
        room_id="ABC123",
        player_name="player1"
    )
    response = await use_case.execute(request)
    
    # Assert
    assert response.success
    
    # Verify connection record
    async with uow:
        connection = await uow.connections.get("ABC123", "player1")
        assert connection is not None
        assert connection.status == ConnectionStatus.DISCONNECTED
        assert connection.disconnect_count == 1


@pytest.mark.asyncio
async def test_player_disconnect_with_existing_bot():
    """Test disconnecting a bot player doesn't double-activate."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()
    metrics = Mock()
    
    use_case = HandlePlayerDisconnectUseCase(uow, event_publisher, metrics)
    
    # Create room with bot player 
    room = Room(room_id="ABC123", host_name="bot1")
    # Make the host a bot
    room.slots[0].is_bot = True
    room.slots[0].original_is_bot = True
    
    # Start game in the room
    room.start_game()
    game = room.game
    
    async with uow:
        await uow.rooms.save(room)
        await uow.games.save(game)
    
    # Act
    request = HandlePlayerDisconnectRequest(
        room_id="ABC123",
        player_name="bot1",
        activate_bot=True
    )
    response = await use_case.execute(request)
    
    # Assert
    assert response.success
    assert not response.bot_activated  # Already was a bot
    
    # Verify player state
    async with uow:
        updated_room = await uow.rooms.get_by_id("ABC123")
        updated_player = updated_room.get_player("bot1")
        assert updated_player.is_bot
        assert updated_player.original_is_bot  # Was originally a bot


@pytest.mark.asyncio
async def test_player_disconnect_invalid_room():
    """Test disconnecting from non-existent room fails."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()
    metrics = Mock()
    
    use_case = HandlePlayerDisconnectUseCase(uow, event_publisher, metrics)
    
    # Act & Assert
    request = HandlePlayerDisconnectRequest(
        room_id="NO_ROO",
        player_name="player1"
    )
    
    response = await use_case.execute(request)
    
    # Assert
    assert not response.success
    assert response.error == "Room not found"


@pytest.mark.asyncio
async def test_player_disconnect_invalid_player():
    """Test disconnecting non-existent player fails."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()
    metrics = Mock()
    
    use_case = HandlePlayerDisconnectUseCase(uow, event_publisher, metrics)
    
    # Create room without the player
    room = Room(room_id="ABC123", host_name="other")
    
    async with uow:
        await uow.rooms.save(room)
    
    # Act & Assert
    request = HandlePlayerDisconnectRequest(
        room_id="ABC123",
        player_name="NO_ROO"
    )
    
    response = await use_case.execute(request)
    
    # Assert  
    assert not response.success
    assert response.error == "Player not found in room"


@pytest.mark.asyncio
async def test_player_disconnect_metrics_collected():
    """Test that disconnection collects metrics."""
    # Arrange
    uow = InMemoryUnitOfWork()
    event_publisher = AsyncMock()
    metrics = Mock()
    
    use_case = HandlePlayerDisconnectUseCase(uow, event_publisher, metrics)
    
    # Create room with player
    room = Room(room_id="ABC123", host_name="player1")
    
    async with uow:
        await uow.rooms.save(room)
    
    # Act
    request = HandlePlayerDisconnectRequest(
        room_id="ABC123",
        player_name="player1"
    )
    await use_case.execute(request)
    
    # Assert metrics collected
    metrics.increment.assert_called()