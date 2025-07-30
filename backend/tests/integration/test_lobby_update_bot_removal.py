"""
Integration test for lobby update on bot removal.

This test verifies the complete flow from use case to event handler to lobby broadcast.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, call

from infrastructure.dependencies import get_unit_of_work, get_event_publisher
from infrastructure.events.in_memory_event_bus import InMemoryEventBus
from infrastructure.events.broadcast_handlers import handle_player_removed
from domain.events.room_events import PlayerRemoved
from domain.events.base import EventMetadata
from application.use_cases.room_management.remove_player import RemovePlayerUseCase
from application.dto.room_management import RemovePlayerRequest


@pytest.mark.asyncio
async def test_player_removed_event_triggers_lobby_update():
    """Test that PlayerRemoved event triggers lobby update broadcast."""
    
    # Arrange
    broadcast_calls = []
    
    async def mock_broadcast(channel, event, data):
        broadcast_calls.append((channel, event, data))
    
    # Patch the broadcast function in the handler module
    with patch('infrastructure.events.broadcast_handlers.broadcast', mock_broadcast):
        # Create a PlayerRemoved event
        event = PlayerRemoved(
            metadata=EventMetadata(user_id="test_user"),
            room_id="TEST123",
            removed_player_id="TEST123_p2",
            removed_player_name="Bot 3",
            removed_player_slot="P3",
            removed_by_id="TEST123_p0",
            removed_by_name="TestHost"
        )
        
        # Call the handler directly
        await handle_player_removed(event)
        
        # Check that lobby broadcast was called
        lobby_broadcasts = [call for call in broadcast_calls 
                           if call[0] == "lobby" and call[1] == "room_list_update"]
        
        assert len(lobby_broadcasts) > 0, "handle_player_removed should broadcast to lobby"
        
        # Check the broadcast data
        if lobby_broadcasts:
            broadcast_data = lobby_broadcasts[0][2]
            assert "rooms" in broadcast_data
            assert "timestamp" in broadcast_data


@pytest.mark.asyncio
async def test_event_bus_connection():
    """Test that event bus properly connects use case to handler."""
    
    # This test verifies the event bus is properly configured
    event_bus = InMemoryEventBus()
    
    # Check if PlayerRemoved has a handler registered
    handlers = event_bus._handlers.get("PlayerRemoved", [])
    handler_names = [h.__name__ for h in handlers]
    
    assert len(handlers) > 0, "PlayerRemoved should have at least one handler"
    assert "handle_player_removed" in handler_names, "handle_player_removed should be registered"


@pytest.mark.asyncio 
async def test_full_integration_bot_removal_to_lobby_update():
    """Full integration test from use case execution to lobby broadcast."""
    
    # This will test the actual flow with real components
    # but mocked broadcast
    broadcast_calls = []
    
    async def mock_broadcast(channel, event, data):
        broadcast_calls.append((channel, event, data))
        print(f"BROADCAST: {channel} - {event}")
    
    with patch('infrastructure.websocket.connection_singleton.broadcast', mock_broadcast):
        # Get real dependencies
        uow = get_unit_of_work()
        event_publisher = get_event_publisher()
        
        # First create a room with bots
        async with uow:
            from domain.entities.room import Room
            room = Room.create("TEST123", "TestHost")
            # Add 3 bots
            for i in range(1, 4):
                room.add_bot(f"Bot {i+1}")
            await uow.rooms.save(room)
            await uow.commit()
        
        # Create use case
        use_case = RemovePlayerUseCase(
            unit_of_work=uow,
            event_publisher=event_publisher
        )
        
        # Create request to remove bot 3
        request = RemovePlayerRequest(
            room_id="TEST123",
            target_player_id="TEST123_p2",  # Bot 3 is in slot 2 (0-indexed)
            requesting_player_id="TEST123_p0",
            user_id="test_user"
        )
        
        # Execute the use case
        response = await use_case.execute(request)
        
        # Wait for async events to propagate
        await asyncio.sleep(0.5)
        
        # Check broadcasts
        print(f"Total broadcasts: {len(broadcast_calls)}")
        for call in broadcast_calls:
            print(f"  {call[0]} - {call[1]}")
        
        # Verify lobby was notified
        lobby_broadcasts = [call for call in broadcast_calls 
                           if call[0] == "lobby" and call[1] == "room_list_update"]
        
        assert len(lobby_broadcasts) > 0, "Lobby should receive room_list_update after bot removal"