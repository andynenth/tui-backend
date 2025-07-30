"""
Tests for domain integration components.

These tests verify that the domain layer integrates correctly
with infrastructure components.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

# Domain imports
from domain.entities.room import Room
from domain.entities.player import Player
from domain.value_objects.piece import Piece
from domain.events.game_events import GameStarted
from domain.events.player_events import PlayerDeclaredPiles
from domain.events.base import EventMetadata

# Infrastructure imports
from infrastructure.repositories import InMemoryRoomRepository
from infrastructure.events import InMemoryEventBus
from infrastructure.handlers import WebSocketBroadcastHandler

# Integration imports
from api.adapters.domain_integration import DomainIntegration


class TestInMemoryRoomRepository:
    """Test the in-memory room repository."""

    @pytest.mark.asyncio
    async def test_save_and_find_room(self):
        """Test saving and finding a room."""
        repo = InMemoryRoomRepository()

        # Create a room
        room = Room(room_id="test-room", host_name="alice")
        room.add_player("alice", is_bot=False)

        # Save it
        await repo.save(room)

        # Find it
        found = await repo.find_by_id("test-room")
        assert found is not None
        assert found.room_id == "test-room"
        assert found.host_name == "alice"

    @pytest.mark.asyncio
    async def test_find_by_player_name(self):
        """Test finding a room by player name."""
        repo = InMemoryRoomRepository()

        # Create rooms
        room1 = Room(room_id="room1", host_name="alice")
        room1.add_player("alice", is_bot=False)
        room1.add_player("bob", is_bot=False)

        room2 = Room(room_id="room2", host_name="charlie")
        room2.add_player("charlie", is_bot=False)
        room2.add_player("david", is_bot=False)

        await repo.save(room1)
        await repo.save(room2)

        # Find by player
        found = await repo.find_by_player_name("bob")
        assert found is not None
        assert found.room_id == "room1"

        found = await repo.find_by_player_name("david")
        assert found is not None
        assert found.room_id == "room2"

        found = await repo.find_by_player_name("unknown")
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_room(self):
        """Test deleting a room."""
        repo = InMemoryRoomRepository()

        room = Room(room_id="test-room", host_name="alice")
        await repo.save(room)

        # Verify it exists
        assert await repo.exists("test-room")

        # Delete it
        deleted = await repo.delete("test-room")
        assert deleted is True

        # Verify it's gone
        assert not await repo.exists("test-room")
        assert await repo.find_by_id("test-room") is None


class TestInMemoryEventBus:
    """Test the in-memory event bus."""

    @pytest.mark.asyncio
    async def test_publish_to_handler(self):
        """Test publishing events to handlers."""
        bus = InMemoryEventBus()

        # Create a mock handler
        handler = Mock()
        handler.get_event_types.return_value = ["GameStarted"]
        handler.can_handle.return_value = True
        handler.handle = AsyncMock()

        # Register handler
        bus.register_handler(handler)

        # Create and publish event
        event = GameStarted(
            room_id="test-room",
            round_number=1,
            player_names=["alice", "bob"],
            win_condition="score",
            max_score=50,
            max_rounds=20,
            metadata=EventMetadata(),
        )

        await bus.publish(event)

        # Verify handler was called
        handler.can_handle.assert_called_once()
        handler.handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_global_handler(self):
        """Test global handlers receive all events."""
        bus = InMemoryEventBus()

        # Create a mock global handler
        handler = Mock()
        handler.can_handle.return_value = True
        handler.handle = AsyncMock()

        # Register as global
        bus.register_global_handler(handler)

        # Publish different event types
        event1 = GameStarted(
            room_id="test-room",
            round_number=1,
            player_names=["alice"],
            win_condition="score",
            max_score=50,
            max_rounds=20,
            metadata=EventMetadata(),
        )

        event2 = PlayerDeclaredPiles(
            room_id="test-room",
            player_id="p1",
            player_name="alice",
            declared_count=3,
            zero_streak=0,
            metadata=EventMetadata(),
        )

        await bus.publish(event1)
        await bus.publish(event2)

        # Verify handler was called for both
        assert handler.handle.call_count == 2


class TestWebSocketBroadcastHandler:
    """Test the WebSocket broadcast handler."""

    def test_can_handle_with_room_id(self):
        """Test handler can handle events with room_id."""
        handler = WebSocketBroadcastHandler()

        # Event with room_id
        event = GameStarted(
            room_id="test-room",
            round_number=1,
            player_names=["alice"],
            win_condition="score",
            max_score=50,
            max_rounds=20,
            metadata=EventMetadata(),
        )

        assert handler.can_handle(event) is True

    def test_event_type_mapping(self):
        """Test event type mappings."""
        handler = WebSocketBroadcastHandler()

        # Check some mappings
        assert "GameStarted" in handler._event_mappings
        assert handler._event_mappings["GameStarted"] == "game_started"

        assert "PlayerDeclaredPiles" in handler._event_mappings
        assert handler._event_mappings["PlayerDeclaredPiles"] == "declaration_made"


class TestDomainIntegration:
    """Test the domain integration module."""

    def test_initialization(self):
        """Test integration initializes correctly."""
        integration = DomainIntegration()

        # Check components are set up
        assert integration.room_repository is not None
        assert integration.event_bus is not None
        assert integration.game_adapter is not None

        # Check it's disabled by default
        assert integration.enabled is False

    def test_enable_disable(self):
        """Test enabling and disabling integration."""
        integration = DomainIntegration()

        # Enable
        integration.enable()
        assert integration.enabled is True

        # Disable
        integration.disable()
        assert integration.enabled is False

    @pytest.mark.asyncio
    async def test_handle_message_when_disabled(self):
        """Test message handling returns None when disabled."""
        integration = DomainIntegration()
        integration.disable()

        result = await integration.handle_message(
            Mock(), {"event": "start_game"}, "test-room"
        )

        assert result is None

    def test_get_status(self):
        """Test getting integration status."""
        integration = DomainIntegration()
        integration.enable()

        status = integration.get_status()

        assert status["enabled"] is True
        assert "repositories" in status
        assert "event_bus" in status
        assert "adapters" in status
