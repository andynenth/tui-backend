#!/usr/bin/env python3
"""
Simple integration test for room management system.
"""

import asyncio
from datetime import datetime
from application.dto.room_management import CreateRoomRequest, GetRoomStateRequest
from application.dto.lobby import GetRoomListRequest
from application.use_cases.room_management import CreateRoomUseCase, GetRoomStateUseCase
from application.use_cases.lobby import GetRoomListUseCase
from infrastructure.repositories.in_memory_room_repository import InMemoryRoomRepository
from infrastructure.repositories.in_memory_game_repository import InMemoryGameRepository
from infrastructure.unit_of_work import InMemoryUnitOfWork
from infrastructure.events.application_event_publisher import ApplicationEventPublisher

async def test_room_management():
    """Test the complete room management flow."""
    print("🧪 Starting Simple Room Management Integration Test\n")
    
    # Create dependencies manually
    room_repo = InMemoryRoomRepository()
    game_repo = InMemoryGameRepository()
    uow = InMemoryUnitOfWork(room_repo, game_repo)
    event_publisher = ApplicationEventPublisher()
    
    # Test 1: Create a room
    print("📋 Test 1: Create Room")
    create_use_case = CreateRoomUseCase(uow, event_publisher)
    create_request = CreateRoomRequest(
        host_player_id="alice123",
        host_player_name="Alice",
        room_name="Alice's Game Room",
        max_players=4,
        win_condition_type="score",
        win_condition_value=50,
        is_private=False
    )
    
    try:
        create_response = await create_use_case.execute(create_request)
        print(f"✅ Room created successfully!")
        print(f"   Room ID: {create_response.room_info.room_id}")
        print(f"   Join Code: {create_response.join_code}")
        print(f"   Host: {create_response.room_info.room_name}")
        room_id = create_response.room_info.room_id
    except Exception as e:
        print(f"❌ Failed to create room: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Get room state
    print("\n📋 Test 2: Get Room State")
    get_state_use_case = GetRoomStateUseCase(uow)
    state_request = GetRoomStateRequest(
        room_id=room_id,
        requesting_player_id="alice123"
    )
    
    try:
        state_response = await get_state_use_case.execute(state_request)
        print(f"✅ Room state retrieved successfully!")
        print(f"   Players: {len(state_response.room_info.players)}/{state_response.room_info.max_players}")
        print(f"   Status: {state_response.room_info.status}")
        for i, player in enumerate(state_response.room_info.players):
            print(f"   Player {i+1}: {player.player_name} {'(Host)' if player.is_host else ''}")
    except Exception as e:
        print(f"❌ Failed to get room state: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: List rooms in lobby
    print("\n📋 Test 3: List Rooms in Lobby")
    list_use_case = GetRoomListUseCase(uow)
    list_request = GetRoomListRequest(
        player_id="bob456",
        include_full=False,
        include_in_game=False
    )
    
    try:
        list_response = await list_use_case.execute(list_request)
        print(f"✅ Room list retrieved successfully!")
        print(f"   Total rooms: {list_response.total_items}")
        for room in list_response.rooms:
            print(f"   - {room.room_name} ({room.player_count}/{room.max_players} players)")
            print(f"     Room ID: {room.room_id}")
            print(f"     Host: {room.host_name}")
    except Exception as e:
        print(f"❌ Failed to list rooms: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_room_management())