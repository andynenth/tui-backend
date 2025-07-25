"""
End-to-end tests for clean architecture flows.

These tests simulate complete user flows through the clean architecture
without external dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import asyncio

from domain.entities import Room, Game, Player
from domain.value_objects import RoomId, GameId, PlayerId
from domain.exceptions import DomainException

from application.use_cases.room_management import (
    CreateRoomUseCase,
    JoinRoomUseCase,
    LeaveRoomUseCase,
    AddBotUseCase
)
from application.use_cases.game import (
    StartGameUseCase,
    DeclareUseCase,
    PlayUseCase
)
from application.dto.room_management import *
from application.dto.game import *

from infrastructure.unit_of_work import InMemoryUnitOfWork
from infrastructure.events.application_event_publisher import InMemoryEventPublisher
from infrastructure.services.simple_bot_service import SimpleBotService
from infrastructure.feature_flags import FeatureFlags


class TestCompleteGameFlow:
    """Test a complete game flow from room creation to game completion."""
    
    @pytest.fixture
    def setup(self):
        """Set up all required components."""
        uow = InMemoryUnitOfWork()
        publisher = InMemoryEventPublisher()
        bot_service = SimpleBotService()
        metrics = Mock()
        
        return {
            'uow': uow,
            'publisher': publisher,
            'bot_service': bot_service,
            'metrics': metrics
        }
    
    @pytest.mark.asyncio
    async def test_full_game_flow(self, setup):
        """Test complete flow: create room -> join players -> start game -> play."""
        uow = setup['uow']
        publisher = setup['publisher']
        metrics = setup['metrics']
        
        # Step 1: Create Room
        create_use_case = CreateRoomUseCase(uow, publisher)
        create_response = await create_use_case.execute(
            CreateRoomRequest(
                host_player_id="host123",
                host_player_name="Game Host",
                room_name="Test Game Room",
                max_players=4
            )
        )
        
        assert create_response.success is True
        room_id = create_response.room_id
        room_code = create_response.room_code
        
        # Step 2: Join Players
        join_use_case = JoinRoomUseCase(uow, publisher, metrics)
        
        # Join 3 more players
        for i in range(2, 5):
            join_response = await join_use_case.execute(
                JoinRoomRequest(
                    player_id=f"player{i}",
                    player_name=f"Player {i}",
                    room_code=room_code
                )
            )
            assert join_response.success is True
        
        # Verify room has 4 players
        async with uow:
            room = await uow.rooms.get_by_id(RoomId(room_id))
            assert len(room.players) == 4
            assert not room.is_in_game
        
        # Step 3: Start Game
        start_use_case = StartGameUseCase(uow, publisher)
        start_response = await start_use_case.execute(
            StartGameRequest(
                room_id=room_id,
                requesting_player_id="host123"
            )
        )
        
        assert start_response.success is True
        game_id = start_response.game_id
        
        # Verify game started
        async with uow:
            game = await uow.games.get_by_id(GameId(game_id))
            assert game is not None
            assert game.is_active is True
            assert game.current_phase == "PREPARATION"
            
            room = await uow.rooms.get_by_id(RoomId(room_id))
            assert room.is_in_game is True
        
        # Step 4: Verify Events Published
        events = publisher.get_published_events()
        event_types = [type(e).__name__ for e in events]
        
        assert "RoomCreated" in event_types
        assert event_types.count("PlayerJoinedRoom") == 3
        assert "GameStarted" in event_types
    
    @pytest.mark.asyncio
    async def test_room_with_bots(self, setup):
        """Test creating a room and adding bots."""
        uow = setup['uow']
        publisher = setup['publisher']
        bot_service = setup['bot_service']
        
        # Create room
        create_use_case = CreateRoomUseCase(uow, publisher)
        create_response = await create_use_case.execute(
            CreateRoomRequest(
                host_player_id="host123",
                host_player_name="Host",
                room_name="Bot Test Room"
            )
        )
        
        room_id = create_response.room_id
        
        # Add bots
        add_bot_use_case = AddBotUseCase(uow, publisher, bot_service)
        
        # Add 3 bots
        for i in range(3):
            bot_response = await add_bot_use_case.execute(
                AddBotRequest(
                    room_id=room_id,
                    requesting_player_id="host123",
                    bot_difficulty="medium"
                )
            )
            assert bot_response.success is True
        
        # Verify room has 4 players (1 human + 3 bots)
        async with uow:
            room = await uow.rooms.get_by_id(RoomId(room_id))
            assert len(room.players) == 4
            
            bot_count = sum(1 for p in room.players if p.is_bot)
            assert bot_count == 3
    
    @pytest.mark.asyncio
    async def test_player_leaving_and_host_migration(self, setup):
        """Test player leaving and host migration."""
        uow = setup['uow']
        publisher = setup['publisher']
        metrics = setup['metrics']
        
        # Create room with multiple players
        async with uow:
            room = Room(
                room_id=RoomId("migrate_test"),
                room_code="MIGR8",
                name="Migration Test"
            )
            room.add_player(Player(PlayerId("host"), "Host Player"))
            room.add_player(Player(PlayerId("p2"), "Player 2"))
            room.add_player(Player(PlayerId("p3"), "Player 3"))
            await uow.rooms.add(room)
            await uow.commit()
        
        # Host leaves
        leave_use_case = LeaveRoomUseCase(uow, publisher)
        leave_response = await leave_use_case.execute(
            LeaveRoomRequest(
                player_id="host",
                room_id="migrate_test",
                reason="Host disconnected"
            )
        )
        
        assert leave_response.success is True
        
        # Verify host migration
        async with uow:
            room = await uow.rooms.get_by_id(RoomId("migrate_test"))
            assert len(room.players) == 2
            assert room.host_id != PlayerId("host")
            # New host should be one of remaining players
            assert room.host_id in [PlayerId("p2"), PlayerId("p3")]
        
        # Check events
        events = publisher.get_published_events()
        event_types = [type(e).__name__ for e in events]
        assert "PlayerLeftRoom" in event_types
        assert "HostChanged" in event_types
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, setup):
        """Test handling concurrent operations."""
        uow = setup['uow']
        publisher = setup['publisher']
        metrics = setup['metrics']
        
        # Create room
        create_use_case = CreateRoomUseCase(uow, publisher)
        create_response = await create_use_case.execute(
            CreateRoomRequest(
                host_player_id="host",
                host_player_name="Host",
                room_name="Concurrent Test"
            )
        )
        
        room_id = create_response.room_id
        room_code = create_response.room_code
        
        # Simulate concurrent joins
        join_use_case = JoinRoomUseCase(uow, publisher, metrics)
        
        # Create join tasks
        join_tasks = []
        for i in range(3):
            task = join_use_case.execute(
                JoinRoomRequest(
                    player_id=f"player{i}",
                    player_name=f"Player {i}",
                    room_code=room_code
                )
            )
            join_tasks.append(task)
        
        # Execute concurrently
        results = await asyncio.gather(*join_tasks, return_exceptions=True)
        
        # All should succeed
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent join failed: {result}")
            assert result.success is True
        
        # Verify all players added
        async with uow:
            room = await uow.rooms.get_by_id(RoomId(room_id))
            assert len(room.players) == 4  # Host + 3 players
    
    @pytest.mark.asyncio
    async def test_error_handling_in_flow(self, setup):
        """Test error handling in various scenarios."""
        uow = setup['uow']
        publisher = setup['publisher']
        
        # Try to start game with insufficient players
        async with uow:
            room = Room(
                room_id=RoomId("error_test"),
                room_code="ERR01",
                name="Error Test"
            )
            room.add_player(Player(PlayerId("p1"), "Player 1"))
            room.add_player(Player(PlayerId("p2"), "Player 2"))
            await uow.rooms.add(room)
            await uow.commit()
        
        start_use_case = StartGameUseCase(uow, publisher)
        start_response = await start_use_case.execute(
            StartGameRequest(
                room_id="error_test",
                requesting_player_id="p1"
            )
        )
        
        # Should fail - not enough players
        assert start_response.success is False
        assert "players" in start_response.error.lower()
        
        # Verify no game was created
        async with uow:
            games = await uow.games.get_by_room(RoomId("error_test"))
            assert len(games) == 0
    
    @pytest.mark.asyncio
    async def test_feature_flag_rollout(self, setup):
        """Test feature flag based rollout."""
        flags = FeatureFlags()
        
        # Start with clean architecture disabled
        flags.override(FeatureFlags.USE_CLEAN_ARCHITECTURE, False)
        assert flags.is_enabled(FeatureFlags.USE_CLEAN_ARCHITECTURE) is False
        
        # Enable for testing
        flags.override(FeatureFlags.USE_CLEAN_ARCHITECTURE, True)
        assert flags.is_enabled(FeatureFlags.USE_CLEAN_ARCHITECTURE) is True
        
        # Test percentage rollout
        flags._flags['test_rollout'] = 50  # 50% rollout
        
        enabled_count = 0
        for i in range(100):
            if flags.is_enabled('test_rollout', {'user_id': f'user_{i}'}):
                enabled_count += 1
        
        # Should be roughly 50%
        assert 40 <= enabled_count <= 60