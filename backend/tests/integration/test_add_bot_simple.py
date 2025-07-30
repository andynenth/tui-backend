"""
Simple test for Issue 2: Add bot to specific slot.

Tests the add bot use case directly.
"""

import pytest
import asyncio

from infrastructure.dependencies import get_unit_of_work, get_event_publisher, get_bot_service
from application.use_cases.room_management.add_bot import AddBotUseCase
from application.dto.room_management import AddBotRequest
from domain.entities.room import Room


@pytest.mark.asyncio
async def test_add_bot_to_correct_slot():
    """Test that add bot places bot in the requested slot."""
    
    # Setup
    room_id = "TEST123"
    host_name = "TestHost"
    
    uow = get_unit_of_work()
    event_publisher = get_event_publisher()
    
    # Create room with only host
    async with uow:
        room = Room(room_id=room_id, host_name=host_name)
        # Remove default bots
        room.remove_player("Bot 2")
        room.remove_player("Bot 3")
        room.remove_player("Bot 4")
        await uow.rooms.save(room)
        await uow.commit()
    
    # Create use case
    use_case = AddBotUseCase(
        unit_of_work=uow,
        event_publisher=event_publisher,
        bot_service=get_bot_service()
    )
    
    # Test adding bot to seat_position 2 (0-based, which is slot 3 in UI)
    request = AddBotRequest(
        room_id=room_id,
        requesting_player_id=f"{room_id}_p0",
        seat_position=2,  # 0-based index
        user_id="test_user"
    )
    
    print("\n[TEST] Adding bot to seat_position=2 (slot 3 in UI)")
    response = await use_case.execute(request)
    
    # Verify bot was added to correct position
    async with uow:
        room = await uow.rooms.get_by_id(room_id)
        print(f"[TEST] Slot 0: {room.slots[0].name if room.slots[0] else 'empty'}")
        print(f"[TEST] Slot 1: {room.slots[1].name if room.slots[1] else 'empty'}")
        print(f"[TEST] Slot 2: {room.slots[2].name if room.slots[2] else 'empty'}")
        print(f"[TEST] Slot 3: {room.slots[3].name if room.slots[3] else 'empty'}")
        
        # Verify
        assert room.slots[2] is not None, "Bot should be in slot 2"
        assert room.slots[2].is_bot, "Slot 2 should contain a bot"
        assert room.slots[1] is None, "Slot 1 should be empty"
        assert room.slots[3] is None, "Slot 3 should be empty"


@pytest.mark.asyncio 
async def test_add_bot_without_seat_position():
    """Test that add bot without seat_position fills first empty slot."""
    
    # Setup
    room_id = "TEST456"
    host_name = "TestHost"
    
    uow = get_unit_of_work()
    event_publisher = get_event_publisher()
    
    # Create room with host and one bot in slot 2
    async with uow:
        room = Room(room_id=room_id, host_name=host_name)
        # Remove default bots
        room.remove_player("Bot 2")
        room.remove_player("Bot 3")
        room.remove_player("Bot 4")
        # Add bot to slot 2
        room.add_player("Manual Bot", is_bot=True, slot=2)
        await uow.rooms.save(room)
        await uow.commit()
    
    # Create use case
    use_case = AddBotUseCase(
        unit_of_work=uow,
        event_publisher=event_publisher,
        bot_service=get_bot_service()
    )
    
    # Add bot without specifying position
    request = AddBotRequest(
        room_id=room_id,
        requesting_player_id=f"{room_id}_p0",
        seat_position=None,  # No specific position
        user_id="test_user"
    )
    
    print("\n[TEST] Adding bot without seat_position")
    response = await use_case.execute(request)
    
    # Verify bot was added to first empty slot (slot 1)
    async with uow:
        room = await uow.rooms.get_by_id(room_id)
        print(f"[TEST] Slot 0: {room.slots[0].name if room.slots[0] else 'empty'}")
        print(f"[TEST] Slot 1: {room.slots[1].name if room.slots[1] else 'empty'}")
        print(f"[TEST] Slot 2: {room.slots[2].name if room.slots[2] else 'empty'}")
        print(f"[TEST] Slot 3: {room.slots[3].name if room.slots[3] else 'empty'}")
        
        # Should fill first empty slot
        assert room.slots[1] is not None, "Bot should be in slot 1 (first empty)"
        assert room.slots[1].is_bot, "Slot 1 should contain a bot"