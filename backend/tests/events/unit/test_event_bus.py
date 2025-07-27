"""
Unit tests for the event bus implementation.

Tests the core event publishing and subscription functionality.
"""

import pytest
import asyncio
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from domain.events.base import DomainEvent, EventMetadata
from domain.events.all_events import (
    RoomCreated, PlayerJoinedRoom, GameStarted,
    PiecesPlayed, InvalidActionAttempted
)
from infrastructure.events.in_memory_event_bus import (
    InMemoryEventBus, EventHandler, get_event_bus, reset_event_bus
)


class TestEventBus:
    """Test the InMemoryEventBus implementation."""
    
    @pytest.fixture
    def event_bus(self):
        """Create a fresh event bus for each test."""
        bus = InMemoryEventBus()
        yield bus
        # No cleanup needed
    
    @pytest.fixture
    def sample_events(self):
        """Create sample events for testing."""
        metadata = EventMetadata(user_id="test_user")
        
        return {
            'room_created': RoomCreated(
                room_id="room123",
                host_id="host123",
                host_name="Alice",
                metadata=metadata
            ),
            'player_joined': PlayerJoinedRoom(
                room_id="room123",
                player_id="player456",
                player_name="Bob",
                player_slot="P2",
                metadata=metadata
            ),
            'game_started': GameStarted(
                room_id="room123",
                round_number=1,
                player_names=["Alice", "Bob", "Carol", "Dave"],
                started_by_id="host123",
                started_by_name="Alice",
                metadata=metadata
            )
        }
    
    @pytest.mark.asyncio
    async def test_subscribe_and_publish_single_event(self, event_bus, sample_events):
        """Test basic subscribe and publish functionality."""
        handler_called = False
        received_event = None
        
        async def handler(event: RoomCreated):
            nonlocal handler_called, received_event
            handler_called = True
            received_event = event
        
        # Subscribe to RoomCreated events
        event_bus.subscribe(RoomCreated, handler)
        
        # Publish event
        await event_bus.publish(sample_events['room_created'])
        
        # Verify handler was called
        assert handler_called is True
        assert received_event == sample_events['room_created']
    
    @pytest.mark.asyncio
    async def test_multiple_handlers_for_same_event(self, event_bus, sample_events):
        """Test multiple handlers can subscribe to the same event."""
        call_order = []
        
        async def handler1(event: RoomCreated):
            call_order.append('handler1')
        
        async def handler2(event: RoomCreated):
            call_order.append('handler2')
        
        async def handler3(event: RoomCreated):
            call_order.append('handler3')
        
        # Subscribe multiple handlers
        event_bus.subscribe(RoomCreated, handler1)
        event_bus.subscribe(RoomCreated, handler2)
        event_bus.subscribe(RoomCreated, handler3)
        
        # Publish event
        await event_bus.publish(sample_events['room_created'])
        
        # All handlers should be called
        assert len(call_order) == 3
        assert 'handler1' in call_order
        assert 'handler2' in call_order
        assert 'handler3' in call_order
    
    @pytest.mark.asyncio
    async def test_handler_priority_ordering(self, event_bus, sample_events):
        """Test handlers are called in priority order."""
        call_order = []
        
        async def low_priority(event):
            call_order.append('low')
        
        async def medium_priority(event):
            call_order.append('medium')
        
        async def high_priority(event):
            call_order.append('high')
        
        # Subscribe with different priorities
        event_bus.subscribe(RoomCreated, low_priority, priority=10)
        event_bus.subscribe(RoomCreated, high_priority, priority=100)
        event_bus.subscribe(RoomCreated, medium_priority, priority=50)
        
        # Publish event
        await event_bus.publish(sample_events['room_created'])
        
        # Should be called in priority order (high to low)
        assert call_order == ['high', 'medium', 'low']
    
    @pytest.mark.asyncio
    async def test_type_based_subscription(self, event_bus, sample_events):
        """Test handlers only receive events of subscribed type."""
        room_created_called = False
        player_joined_called = False
        
        async def room_handler(event: RoomCreated):
            nonlocal room_created_called
            room_created_called = True
        
        async def player_handler(event: PlayerJoinedRoom):
            nonlocal player_joined_called
            player_joined_called = True
        
        # Subscribe to different event types
        event_bus.subscribe(RoomCreated, room_handler)
        event_bus.subscribe(PlayerJoinedRoom, player_handler)
        
        # Publish RoomCreated
        await event_bus.publish(sample_events['room_created'])
        assert room_created_called is True
        assert player_joined_called is False
        
        # Reset flags
        room_created_called = False
        
        # Publish PlayerJoinedRoom
        await event_bus.publish(sample_events['player_joined'])
        assert room_created_called is False
        assert player_joined_called is True
    
    @pytest.mark.asyncio
    async def test_error_isolation(self, event_bus, sample_events):
        """Test that handler errors don't affect other handlers."""
        handler1_called = False
        handler3_called = False
        
        async def handler1(event):
            nonlocal handler1_called
            handler1_called = True
        
        async def handler2_error(event):
            raise ValueError("Handler 2 error")
        
        async def handler3(event):
            nonlocal handler3_called
            handler3_called = True
        
        # Subscribe handlers (one will error)
        event_bus.subscribe(RoomCreated, handler1)
        event_bus.subscribe(RoomCreated, handler2_error)
        event_bus.subscribe(RoomCreated, handler3)
        
        # Publish event
        await event_bus.publish(sample_events['room_created'])
        
        # Other handlers should still be called
        assert handler1_called is True
        assert handler3_called is True
    
    @pytest.mark.asyncio
    async def test_publish_multiple_events(self, event_bus, sample_events):
        """Test publishing multiple events at once."""
        events_received = []
        
        async def handler(event: DomainEvent):
            events_received.append(event)
        
        # Subscribe to base type to receive all events
        event_bus.subscribe(DomainEvent, handler)
        
        # Publish multiple events
        await event_bus.publish_batch([
            sample_events['room_created'],
            sample_events['player_joined'],
            sample_events['game_started']
        ])
        
        # All events should be received
        assert len(events_received) == 3
        assert sample_events['room_created'] in events_received
        assert sample_events['player_joined'] in events_received
        assert sample_events['game_started'] in events_received
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, event_bus, sample_events):
        """Test unsubscribing handlers."""
        handler_called = False
        
        async def handler(event):
            nonlocal handler_called
            handler_called = True
        
        # Subscribe
        event_bus.subscribe(RoomCreated, handler)
        
        # Unsubscribe
        event_bus.unsubscribe(RoomCreated, handler)
        
        # Publish event
        await event_bus.publish(sample_events['room_created'])
        
        # Handler should not be called
        assert handler_called is False
    
    @pytest.mark.asyncio
    async def test_clear_all_handlers(self, event_bus, sample_events):
        """Test clearing all handlers."""
        handler_called = False
        
        async def handler(event):
            nonlocal handler_called
            handler_called = True
        
        # Subscribe to multiple event types
        event_bus.subscribe(RoomCreated, handler)
        event_bus.subscribe(PlayerJoinedRoom, handler)
        event_bus.subscribe(GameStarted, handler)
        
        # Clear all
        event_bus.clear_all_handlers()
        
        # Publish various events
        await event_bus.publish(sample_events['room_created'])
        await event_bus.publish(sample_events['player_joined'])
        await event_bus.publish(sample_events['game_started'])
        
        # No handlers should be called
        assert handler_called is False
    
    @pytest.mark.asyncio
    async def test_inheritance_based_subscription(self, event_bus):
        """Test that handlers for base types receive derived events."""
        game_events_received = []
        domain_events_received = []
        
        async def game_handler(event: DomainEvent):
            if hasattr(event, 'room_id'):  # GameEvent
                game_events_received.append(event)
        
        async def domain_handler(event: DomainEvent):
            domain_events_received.append(event)
        
        # Subscribe to base types
        event_bus.subscribe(DomainEvent, game_handler)
        event_bus.subscribe(DomainEvent, domain_handler)
        
        # Publish specific event
        metadata = EventMetadata(user_id="test")
        pieces_played = PiecesPlayed(
            room_id="room123",
            player_id="player123",
            player_name="Alice",
            pieces=["piece1", "piece2"],
            piece_indices=[0, 1],
            turn_number=1,
            round_number=1,
            metadata=metadata
        )
        
        await event_bus.publish(pieces_played)
        
        # Both handlers should receive the event
        assert len(game_events_received) == 1
        assert len(domain_events_received) == 1
        assert game_events_received[0] == pieces_played
        assert domain_events_received[0] == pieces_played


class TestEventBusGlobalInstance:
    """Test the global event bus instance functionality."""
    
    @pytest.mark.asyncio
    async def test_get_event_bus_singleton(self):
        """Test that get_event_bus returns the same instance."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        
        assert bus1 is bus2
    
    @pytest.mark.asyncio
    async def test_reset_event_bus(self):
        """Test resetting the global event bus."""
        # Get initial bus
        bus1 = get_event_bus()
        
        # Add a handler to verify it's cleared
        handler_called = False
        
        async def handler(event):
            nonlocal handler_called
            handler_called = True
        
        bus1.subscribe(RoomCreated, handler)
        
        # Reset
        reset_event_bus()
        
        # Get new bus
        bus2 = get_event_bus()
        
        # Should be different instance
        assert bus1 is not bus2
        
        # Old handlers should not exist
        metadata = EventMetadata(user_id="test")
        event = RoomCreated(room_id="room123", host_id="host123", host_name="Alice", metadata=metadata)
        await bus2.publish(event)
        
        assert handler_called is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])