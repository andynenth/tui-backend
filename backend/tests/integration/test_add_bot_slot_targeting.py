"""
Integration test for Issue 2: Add bot to specific slot.

This test verifies that when frontend sends slot_id, the bot is added to the correct slot.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import json

# Import to ensure handlers are registered
import infrastructure.events.broadcast_handlers
from infrastructure.dependencies import get_unit_of_work, get_event_publisher
from application.websocket.use_case_dispatcher import UseCaseDispatcher
from domain.entities.room import Room


@pytest.mark.asyncio
async def test_add_bot_to_specific_slot():
    """
    Test that add_bot with slot_id correctly places bot in the right slot.
    
    Frontend sends slot_id (1-based), backend should convert to 0-based index.
    """
    # Arrange
    room_id = "TEST123"
    host_name = "TestHost"
    
    # Get real dependencies
    uow = get_unit_of_work()
    
    # Create a room with only host (remove all bots)
    async with uow:
        room = Room(room_id=room_id, host_name=host_name)
        # Room starts with 4 players, remove the 3 bots
        room.remove_player("Bot 2")
        room.remove_player("Bot 3")
        room.remove_player("Bot 4")
        await uow.rooms.save(room)
        await uow.commit()
    
    # Verify initial state - only host in slot 0
    async with uow:
        room = await uow.rooms.get_by_id(room_id)
        assert room.slots[0] and room.slots[0].name == host_name
        assert room.slots[1] is None
        assert room.slots[2] is None
        assert room.slots[3] is None
    
    # Create dispatcher
    dispatcher = UseCaseDispatcher()
    
    # Mock WebSocket to capture responses
    mock_websocket = AsyncMock()
    mock_websocket.room_id = room_id
    mock_websocket.player_id = f"{room_id}_p0"  # Host
    
    # Test 1: Add bot to slot 3 (frontend sends slot_id=3)
    print("\n[TEST] Adding bot to slot 3 (slot_id=3)")
    response = await dispatcher.dispatch(
        mock_websocket,
        {
            "type": "add_bot",
            "data": {"slot_id": 3}  # Frontend 1-based index
        }
    )
    
    # Check the bot was added to the correct slot
    async with uow:
        room = await uow.rooms.get_by_id(room_id)
        print(f"[TEST] Slot 0: {room.slots[0].name if room.slots[0] else 'empty'}")
        print(f"[TEST] Slot 1: {room.slots[1].name if room.slots[1] else 'empty'}")
        print(f"[TEST] Slot 2: {room.slots[2].name if room.slots[2] else 'empty'}")
        print(f"[TEST] Slot 3: {room.slots[3].name if room.slots[3] else 'empty'}")
        
        # slot_id=3 should place bot in slots[2] (0-based index)
        assert room.slots[2] is not None, "Bot should be in slot 2 (0-based) when slot_id=3"
        assert room.slots[2].is_bot
        assert room.slots[1] is None, "Slot 1 should still be empty"
        assert room.slots[3] is None, "Slot 3 should still be empty"
    
    # Test 2: Add bot to slot 2 (frontend sends slot_id=2)
    print("\n[TEST] Adding bot to slot 2 (slot_id=2)")
    response = await dispatcher.dispatch(
        mock_websocket,
        {
            "type": "add_bot",
            "data": {"slot_id": 2}
        }
    )
    
    async with uow:
        room = await uow.rooms.get_by_id(room_id)
        print(f"[TEST] Slot 0: {room.slots[0].name if room.slots[0] else 'empty'}")
        print(f"[TEST] Slot 1: {room.slots[1].name if room.slots[1] else 'empty'}")
        print(f"[TEST] Slot 2: {room.slots[2].name if room.slots[2] else 'empty'}")
        print(f"[TEST] Slot 3: {room.slots[3].name if room.slots[3] else 'empty'}")
        
        # slot_id=2 should place bot in slots[1] (0-based index)
        assert room.slots[1] is not None, "Bot should be in slot 1 (0-based) when slot_id=2"
        assert room.slots[1].is_bot
    
    # Test 3: Add bot to slot 4 (frontend sends slot_id=4)
    print("\n[TEST] Adding bot to slot 4 (slot_id=4)")
    response = await dispatcher.dispatch(
        mock_websocket,
        {
            "type": "add_bot",
            "data": {"slot_id": 4}
        }
    )
    
    async with uow:
        room = await uow.rooms.get_by_id(room_id)
        print(f"[TEST] Slot 0: {room.slots[0].name if room.slots[0] else 'empty'}")
        print(f"[TEST] Slot 1: {room.slots[1].name if room.slots[1] else 'empty'}")
        print(f"[TEST] Slot 2: {room.slots[2].name if room.slots[2] else 'empty'}")
        print(f"[TEST] Slot 3: {room.slots[3].name if room.slots[3] else 'empty'}")
        
        # slot_id=4 should place bot in slots[3] (0-based index)
        assert room.slots[3] is not None, "Bot should be in slot 3 (0-based) when slot_id=4"
        assert room.slots[3].is_bot


@pytest.mark.asyncio
async def test_add_bot_fills_first_empty_slot():
    """
    Test what happens when no slot_id is specified - should fill first empty slot.
    """
    # Arrange
    room_id = "TEST456"
    host_name = "TestHost"
    
    # Get real dependencies
    uow = get_unit_of_work()
    
    # Create a room with host in slot 0 and bot in slot 2
    async with uow:
        room = Room(room_id=room_id, host_name=host_name)
        # Remove all default bots
        room.remove_player("Bot 2")
        room.remove_player("Bot 3")
        room.remove_player("Bot 4")
        # Add a bot specifically to slot 2
        room.add_player("Custom Bot", is_bot=True, slot=2)
        await uow.rooms.save(room)
        await uow.commit()
    
    # Create dispatcher
    dispatcher = UseCaseDispatcher()
    
    # Mock WebSocket
    mock_websocket = AsyncMock()
    mock_websocket.room_id = room_id
    mock_websocket.player_id = f"{room_id}_p0"  # Host
    
    # Add bot without specifying slot
    print("\n[TEST] Adding bot without slot_id")
    response = await dispatcher.dispatch(
        mock_websocket,
        {
            "type": "add_bot",
            "data": {}  # No slot_id
        }
    )
    
    async with uow:
        room = await uow.rooms.get_by_id(room_id)
        print(f"[TEST] Slot 0: {room.slots[0].name if room.slots[0] else 'empty'}")
        print(f"[TEST] Slot 1: {room.slots[1].name if room.slots[1] else 'empty'}")
        print(f"[TEST] Slot 2: {room.slots[2].name if room.slots[2] else 'empty'}")
        print(f"[TEST] Slot 3: {room.slots[3].name if room.slots[3] else 'empty'}")
        
        # Should fill first empty slot (slot 1)
        assert room.slots[1] is not None, "Bot should be added to first empty slot (slot 1)"
        assert room.slots[1].is_bot