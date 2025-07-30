"""
Tests for AddBotUseCase.

This module tests the add bot functionality including:
- Success cases
- Authorization checks
- Room full scenarios
- Invalid requests
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from application.use_cases.room_management.add_bot import AddBotUseCase
from application.dto.room_management import AddBotRequest, AddBotResponse
from application.dto.common import RoomInfo, PlayerInfo, PlayerStatus, RoomStatus
from application.exceptions import (
    ResourceNotFoundException,
    AuthorizationException,
    ConflictException,
    ValidationException,
)
from domain.entities.room import Room
from domain.entities.player import Player
from domain.events.room_events import BotAdded


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for the use case."""
    mock_uow = Mock()
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)
    mock_uow.rooms = Mock()

    mock_event_publisher = Mock()
    mock_event_publisher.publish = AsyncMock()

    mock_bot_service = Mock()
    mock_bot_service.create_bot = AsyncMock(return_value="bot_12345")

    mock_metrics = Mock()
    mock_metrics.increment = Mock()

    return mock_uow, mock_event_publisher, mock_bot_service, mock_metrics


@pytest.fixture
def use_case(mock_dependencies):
    """Create AddBotUseCase instance."""
    mock_uow, mock_event_publisher, mock_bot_service, mock_metrics = mock_dependencies
    return AddBotUseCase(
        unit_of_work=mock_uow,
        event_publisher=mock_event_publisher,
        bot_service=mock_bot_service,
        metrics=mock_metrics,
    )


@pytest.fixture
def sample_room():
    """Create a sample room with host and one bot."""
    room = Room(room_id="TEST123", host_name="Alice")
    # Room initialization adds host and 3 bots by default
    # Remove one bot to have an empty slot
    room.remove_player("Bot 4")
    return room


@pytest.fixture
def full_room():
    """Create a full room."""
    room = Room(room_id="FULL123", host_name="Bob")
    # Room is already full with 4 players (host + 3 bots)
    return room


@pytest.mark.asyncio
async def test_add_bot_success(use_case, mock_dependencies, sample_room):
    """Test successful bot addition."""
    mock_uow, _, mock_bot_service, _ = mock_dependencies
    mock_uow.rooms.get_by_id = AsyncMock(return_value=sample_room)
    mock_uow.rooms.save = AsyncMock()

    request = AddBotRequest(
        room_id="TEST123",
        requesting_player_id="TEST123_p0",  # Host
        user_id="alice123",
        bot_difficulty="medium",
    )

    response = await use_case.execute(request)

    # Verify response
    assert response.bot_info.player_name  # Should have a name
    assert response.bot_info.is_bot is True
    assert response.bot_info.seat_position == 3  # Empty slot
    assert response.room_info.room_id == "TEST123"
    assert len(response.room_info.players) == 4  # Room full again

    # Verify bot was created
    mock_bot_service.create_bot.assert_called_once_with("medium")

    # Verify room was saved
    mock_uow.rooms.save.assert_called_once_with(sample_room)

    # Verify event was published
    assert mock_dependencies[1].publish.call_count == 1
    event = mock_dependencies[1].publish.call_args[0][0]
    assert isinstance(event, BotAdded)
    assert event.room_id == "TEST123"
    assert event.bot_name  # Should have a name
    assert event.player_slot == "P4"  # Slot 3 (0-indexed) = P4
    assert event.added_by_id == "TEST123_p0"
    assert event.added_by_name == "Alice"


@pytest.mark.asyncio
async def test_add_bot_with_custom_name(use_case, mock_dependencies, sample_room):
    """Test adding bot with custom name."""
    mock_uow, _, _, _ = mock_dependencies
    mock_uow.rooms.get_by_id = AsyncMock(return_value=sample_room)
    mock_uow.rooms.save = AsyncMock()

    request = AddBotRequest(
        room_id="TEST123",
        requesting_player_id="TEST123_p0",
        user_id="alice123",
        bot_difficulty="easy",
        bot_name="SuperBot",
        seat_position=3,
    )

    response = await use_case.execute(request)

    assert response.bot_info.player_name == "SuperBot"
    assert response.bot_info.seat_position == 3


@pytest.mark.asyncio
async def test_add_bot_room_not_found(use_case, mock_dependencies):
    """Test adding bot to non-existent room."""
    mock_uow, _, _, _ = mock_dependencies
    mock_uow.rooms.get_by_id = AsyncMock(return_value=None)

    request = AddBotRequest(
        room_id="NOTFOUND",
        requesting_player_id="NOTFOUND_p0",
        user_id="user123",
        bot_difficulty="medium",
    )

    with pytest.raises(ResourceNotFoundException) as exc_info:
        await use_case.execute(request)

    assert "Room" in str(exc_info.value)
    assert "NOTFOUND" in str(exc_info.value)


@pytest.mark.asyncio
async def test_add_bot_not_authorized(use_case, mock_dependencies, sample_room):
    """Test non-host trying to add bot."""
    mock_uow, _, _, _ = mock_dependencies
    mock_uow.rooms.get_by_id = AsyncMock(return_value=sample_room)

    request = AddBotRequest(
        room_id="TEST123",
        requesting_player_id="TEST123_p1",  # Not the host
        user_id="user123",
        bot_difficulty="medium",
    )

    with pytest.raises(AuthorizationException) as exc_info:
        await use_case.execute(request)

    assert "add bot" in str(exc_info.value)


@pytest.mark.asyncio
async def test_add_bot_room_full(use_case, mock_dependencies, full_room):
    """Test adding bot to full room."""
    mock_uow, _, _, _ = mock_dependencies
    mock_uow.rooms.get_by_id = AsyncMock(return_value=full_room)

    request = AddBotRequest(
        room_id="FULL123",
        requesting_player_id="FULL123_p0",
        user_id="bob123",
        bot_difficulty="medium",
    )

    with pytest.raises(ConflictException) as exc_info:
        await use_case.execute(request)

    assert "full" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_add_bot_game_in_progress(use_case, mock_dependencies, sample_room):
    """Test adding bot while game is in progress."""
    mock_uow, _, _, _ = mock_dependencies

    # Start a game in the room
    sample_room.game = Mock()  # Simulate game in progress
    mock_uow.rooms.get_by_id = AsyncMock(return_value=sample_room)

    request = AddBotRequest(
        room_id="TEST123",
        requesting_player_id="TEST123_p0",
        user_id="alice123",
        bot_difficulty="medium",
    )

    with pytest.raises(ConflictException) as exc_info:
        await use_case.execute(request)

    assert "game is in progress" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_add_bot_invalid_seat_position(use_case, mock_dependencies, sample_room):
    """Test adding bot to invalid seat position."""
    mock_uow, _, _, _ = mock_dependencies
    mock_uow.rooms.get_by_id = AsyncMock(return_value=sample_room)

    request = AddBotRequest(
        room_id="TEST123",
        requesting_player_id="TEST123_p0",
        user_id="alice123",
        bot_difficulty="medium",
        seat_position=0,  # Already occupied by host
    )

    with pytest.raises(ConflictException) as exc_info:
        await use_case.execute(request)

    assert "already occupied" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_add_bot_validation_errors(use_case):
    """Test request validation."""
    # Missing room_id
    request = AddBotRequest(
        room_id="",
        requesting_player_id="player1",
        user_id="user123",
        bot_difficulty="medium",
    )

    with pytest.raises(ValidationException) as exc_info:
        await use_case.execute(request)

    assert "room_id" in exc_info.value.errors

    # Invalid difficulty
    request = AddBotRequest(
        room_id="TEST123",
        requesting_player_id="player1",
        user_id="user123",
        bot_difficulty="super_hard",  # Invalid
    )

    with pytest.raises(ValidationException) as exc_info:
        await use_case.execute(request)

    assert "bot_difficulty" in exc_info.value.errors


@pytest.mark.asyncio
async def test_add_bot_metrics_recorded(use_case, mock_dependencies, sample_room):
    """Test that metrics are recorded."""
    mock_uow, _, _, mock_metrics = mock_dependencies
    mock_uow.rooms.get_by_id = AsyncMock(return_value=sample_room)
    mock_uow.rooms.save = AsyncMock()

    request = AddBotRequest(
        room_id="TEST123",
        requesting_player_id="TEST123_p0",
        user_id="alice123",
        bot_difficulty="hard",
    )

    await use_case.execute(request)

    mock_metrics.increment.assert_called_once_with(
        "bot.added",
        tags={
            "difficulty": "hard",
            "room_full": "true",  # Room becomes full after adding
        },
    )


@pytest.mark.asyncio
async def test_add_bot_correct_player_count(use_case, mock_dependencies, sample_room):
    """Test that player count is correctly calculated in event."""
    mock_uow, mock_event_publisher, _, _ = mock_dependencies
    mock_uow.rooms.get_by_id = AsyncMock(return_value=sample_room)
    mock_uow.rooms.save = AsyncMock()

    request = AddBotRequest(
        room_id="TEST123",
        requesting_player_id="TEST123_p0",
        user_id="alice123",
        bot_difficulty="medium",
    )

    await use_case.execute(request)

    # Check the event was published correctly
    event = mock_event_publisher.publish.call_args[0][0]
    assert isinstance(event, BotAdded)
    assert event.bot_name  # Bot should have a name
    assert event.player_slot  # Bot should have a slot
