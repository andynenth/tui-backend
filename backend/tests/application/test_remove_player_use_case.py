"""
Tests for RemovePlayer use case.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from application.use_cases.room_management import RemovePlayerUseCase
from application.dto.room_management import RemovePlayerRequest, RemovePlayerResponse
from application.dto.common import RoomInfo, PlayerInfo
from application.interfaces import UnitOfWork, EventPublisher, MetricsCollector
from application.exceptions import (
    ResourceNotFoundException,
    AuthorizationException,
    ConflictException,
)
from domain.entities.room import Room, Player, RoomStatus
from domain.events.room_events import PlayerRemoved
from domain.events.base import EventMetadata


class MockUnitOfWork:
    """Mock unit of work for testing."""

    def __init__(self):
        self.rooms = Mock()
        self.games = Mock()
        self.player_stats = Mock()
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


def create_test_room():
    """Create a test room with players."""
    room = Room(room_id="TEST123", host_name="Alice", max_slots=4)
    # The room's __post_init__ will set host_id and add players
    # Override the slots to have our test data
    room.slots = [
        Player(name="Alice", is_bot=False),
        Player(name="Bot 2", is_bot=True),
        Player(name="Bot 3", is_bot=True),
        Player(name="Bot 4", is_bot=True),
    ]
    room.host_id = "TEST123_p0"
    return room


@pytest.mark.asyncio
async def test_remove_bot_player_success():
    """Test successfully removing a bot player from a room."""
    # Arrange
    uow = MockUnitOfWork()
    room = create_test_room()
    uow.rooms.get_by_id = AsyncMock(return_value=room)
    uow.rooms.save = AsyncMock()

    event_publisher = Mock(spec=EventPublisher)
    event_publisher.publish = AsyncMock()

    metrics = Mock(spec=MetricsCollector)

    use_case = RemovePlayerUseCase(uow, event_publisher, metrics)

    request = RemovePlayerRequest(
        room_id="TEST123",
        requesting_player_id="TEST123_p0",  # Host's player ID
        target_player_id="TEST123_p3",  # Bot 4's player ID
        reason="Removing bot",
    )

    # Act
    response = await use_case.execute(request)

    # Assert
    assert response.removed_player_id == "TEST123_p3"
    assert response.was_bot is True
    assert room.slots[3] is None  # Bot 4 removed

    # Verify method calls
    uow.rooms.get_by_id.assert_called_once_with("TEST123")
    uow.rooms.save.assert_called_once_with(room)

    # Verify event was published
    event_publisher.publish.assert_called_once()
    published_event = event_publisher.publish.call_args[0][0]
    assert isinstance(published_event, PlayerRemoved)
    assert published_event.removed_player_id == "TEST123_p3"
    assert published_event.removed_player_name == "Bot 4"
    assert published_event.removed_player_slot == "P4"
    assert published_event.removed_by_id == "TEST123_p0"
    assert published_event.removed_by_name == "Alice"


@pytest.mark.asyncio
async def test_remove_player_not_authorized():
    """Test that non-hosts cannot remove players."""
    # Arrange
    uow = MockUnitOfWork()
    room = create_test_room()
    uow.rooms.get_by_id = AsyncMock(return_value=room)

    event_publisher = Mock(spec=EventPublisher)
    metrics = Mock(spec=MetricsCollector)

    use_case = RemovePlayerUseCase(uow, event_publisher, metrics)

    request = RemovePlayerRequest(
        room_id="TEST123",
        requesting_player_id="TEST123_p1",  # Not the host
        target_player_id="TEST123_p2",
        reason="Trying to remove another player",
    )

    # Act & Assert
    with pytest.raises(AuthorizationException) as exc_info:
        await use_case.execute(request)

    assert "Not authorized to remove player" in str(exc_info.value)

    # Verify room was not modified
    assert room.slots[2] is not None  # Player not removed
    event_publisher.publish.assert_not_called()


@pytest.mark.asyncio
async def test_remove_player_room_not_found():
    """Test removing player from non-existent room."""
    # Arrange
    uow = MockUnitOfWork()
    uow.rooms.get_by_id = AsyncMock(return_value=None)

    event_publisher = Mock(spec=EventPublisher)
    metrics = Mock(spec=MetricsCollector)

    use_case = RemovePlayerUseCase(uow, event_publisher, metrics)

    request = RemovePlayerRequest(
        room_id="INVALID",
        requesting_player_id="INVALID_p0",
        target_player_id="INVALID_p1",
        reason="Test",
    )

    # Act & Assert
    with pytest.raises(ResourceNotFoundException) as exc_info:
        await use_case.execute(request)

    assert "Room with id 'INVALID' not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_remove_player_not_found():
    """Test removing non-existent player."""
    # Arrange
    uow = MockUnitOfWork()
    room = create_test_room()
    uow.rooms.get_by_id = AsyncMock(return_value=room)

    event_publisher = Mock(spec=EventPublisher)
    metrics = Mock(spec=MetricsCollector)

    use_case = RemovePlayerUseCase(uow, event_publisher, metrics)

    request = RemovePlayerRequest(
        room_id="TEST123",
        requesting_player_id="TEST123_p0",  # Host
        target_player_id="TEST123_p5",  # Invalid slot
        reason="Test",
    )

    # Act & Assert
    with pytest.raises(ResourceNotFoundException) as exc_info:
        await use_case.execute(request)

    assert "Player with id 'TEST123_p5' not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_remove_self_as_host():
    """Test that host cannot remove themselves."""
    # Arrange
    uow = MockUnitOfWork()
    room = create_test_room()
    uow.rooms.get_by_id = AsyncMock(return_value=room)

    event_publisher = Mock(spec=EventPublisher)
    metrics = Mock(spec=MetricsCollector)

    use_case = RemovePlayerUseCase(uow, event_publisher, metrics)

    request = RemovePlayerRequest(
        room_id="TEST123",
        requesting_player_id="TEST123_p0",  # Host
        target_player_id="TEST123_p0",  # Trying to remove self
        reason="Test",
    )

    # Act & Assert
    with pytest.raises(ConflictException) as exc_info:
        await use_case.execute(request)

    assert "Host cannot remove themselves" in str(exc_info.value)


@pytest.mark.asyncio
async def test_remove_player_during_game():
    """Test that players cannot be removed during active game."""
    # Arrange
    uow = MockUnitOfWork()
    room = create_test_room()
    room.status = RoomStatus.IN_GAME
    room.game = Mock()  # Simulate active game
    uow.rooms.get_by_id = AsyncMock(return_value=room)

    event_publisher = Mock(spec=EventPublisher)
    metrics = Mock(spec=MetricsCollector)

    use_case = RemovePlayerUseCase(uow, event_publisher, metrics)

    request = RemovePlayerRequest(
        room_id="TEST123",
        requesting_player_id="TEST123_p0",  # Host
        target_player_id="TEST123_p1",
        reason="Test",
    )

    # Act & Assert
    with pytest.raises(ConflictException) as exc_info:
        await use_case.execute(request)

    assert "Cannot remove players while game is in progress" in str(exc_info.value)


@pytest.mark.asyncio
async def test_remove_human_player_success():
    """Test successfully removing a human player from a room."""
    # Arrange
    uow = MockUnitOfWork()
    room = create_test_room()
    # Add a human player in slot 2
    room.slots[2] = Player(name="Bob", is_bot=False)
    uow.rooms.get_by_id = AsyncMock(return_value=room)
    uow.rooms.save = AsyncMock()

    event_publisher = Mock(spec=EventPublisher)
    event_publisher.publish = AsyncMock()

    metrics = Mock(spec=MetricsCollector)

    use_case = RemovePlayerUseCase(uow, event_publisher, metrics)

    request = RemovePlayerRequest(
        room_id="TEST123",
        requesting_player_id="TEST123_p0",  # Host
        target_player_id="TEST123_p2",  # Bob's player ID
        reason="Removing human player",
    )

    # Act
    response = await use_case.execute(request)

    # Assert
    assert response.removed_player_id == "TEST123_p2"
    assert response.was_bot is False
    assert room.slots[2] is None  # Bob removed

    # Verify event
    published_event = event_publisher.publish.call_args[0][0]
    assert published_event.removed_player_name == "Bob"
    assert published_event.removed_player_slot == "P3"


@pytest.mark.asyncio
async def test_remove_player_with_invalid_player_id_format():
    """Test handling invalid player ID format."""
    # Arrange
    uow = MockUnitOfWork()
    room = create_test_room()
    uow.rooms.get_by_id = AsyncMock(return_value=room)

    event_publisher = Mock(spec=EventPublisher)
    metrics = Mock(spec=MetricsCollector)

    use_case = RemovePlayerUseCase(uow, event_publisher, metrics)

    request = RemovePlayerRequest(
        room_id="TEST123",
        requesting_player_id="TEST123_p0",  # Host
        target_player_id="invalid_format",  # Wrong format
        reason="Test",
    )

    # Act & Assert
    with pytest.raises(ResourceNotFoundException) as exc_info:
        await use_case.execute(request)

    assert "Player with id 'invalid_format' not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_remove_empty_slot():
    """Test removing from an already empty slot."""
    # Arrange
    uow = MockUnitOfWork()
    room = create_test_room()
    room.slots[2] = None  # Empty slot
    uow.rooms.get_by_id = AsyncMock(return_value=room)

    event_publisher = Mock(spec=EventPublisher)
    metrics = Mock(spec=MetricsCollector)

    use_case = RemovePlayerUseCase(uow, event_publisher, metrics)

    request = RemovePlayerRequest(
        room_id="TEST123",
        requesting_player_id="TEST123_p0",  # Host
        target_player_id="TEST123_p2",  # Empty slot
        reason="Test",
    )

    # Act & Assert
    with pytest.raises(ResourceNotFoundException) as exc_info:
        await use_case.execute(request)

    assert "Player with id 'TEST123_p2' not found" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
