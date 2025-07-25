"""
Integration tests for the clean architecture implementation.

These tests verify that all layers work together correctly
without relying on external dependencies like WebSocket.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import uuid

from domain.entities import Room, Game, Player
from domain.value_objects import RoomId, GameId, PlayerId, PieceValue, PieceKind
from domain.events.room_events import RoomCreated, PlayerJoinedRoom
from domain.events.game_events import GameStarted

from application.use_cases.room_management.create_room import CreateRoomUseCase
from application.use_cases.room_management.join_room import JoinRoomUseCase
from application.use_cases.game.start_game import StartGameUseCase
from application.dto.room_management import (
    CreateRoomRequest,
    CreateRoomResponse,
    JoinRoomRequest,
    JoinRoomResponse
)
from application.dto.game import StartGameRequest, StartGameResponse

from infrastructure.unit_of_work import InMemoryUnitOfWork
from infrastructure.events.application_event_publisher import InMemoryEventPublisher
from infrastructure.feature_flags import FeatureFlags


class TestCleanArchitectureIntegration:
    """Test the integration of all clean architecture layers."""
    
    @pytest.fixture
    def uow(self):
        """Create unit of work."""
        return InMemoryUnitOfWork()
    
    @pytest.fixture
    def event_publisher(self):
        """Create event publisher."""
        return InMemoryEventPublisher()
    
    @pytest.fixture
    def feature_flags(self):
        """Create feature flags with clean architecture enabled."""
        flags = FeatureFlags()
        flags.override(FeatureFlags.USE_CLEAN_ARCHITECTURE, True)
        flags.override(FeatureFlags.USE_DOMAIN_EVENTS, True)
        flags.override(FeatureFlags.USE_APPLICATION_LAYER, True)
        return flags
    
    @pytest.mark.asyncio
    async def test_create_and_join_room_flow(self, uow, event_publisher):
        """Test creating a room and joining it."""
        # Create room
        create_use_case = CreateRoomUseCase(uow, event_publisher)
        create_request = CreateRoomRequest(
            host_player_id="player1",
            host_player_name="Host Player",
            room_name="Test Room",
            max_players=4
        )
        
        create_response = await create_use_case.execute(create_request)
        
        assert create_response.success is True
        assert create_response.room_id is not None
        assert create_response.room_code is not None
        
        # Verify room was persisted
        async with uow:
            room = await uow.rooms.get_by_id(RoomId(create_response.room_id))
            assert room is not None
            assert room.name == "Test Room"
            assert len(room.players) == 1
        
        # Join room
        join_use_case = JoinRoomUseCase(uow, event_publisher, Mock())
        join_request = JoinRoomRequest(
            player_id="player2",
            player_name="Player 2",
            room_code=create_response.room_code
        )
        
        join_response = await join_use_case.execute(join_request)
        
        assert join_response.success is True
        assert join_response.room_id == create_response.room_id
        
        # Verify player was added
        async with uow:
            room = await uow.rooms.get_by_id(RoomId(create_response.room_id))
            assert len(room.players) == 2
            player_ids = [p.player_id.value for p in room.players]
            assert "player2" in player_ids
        
        # Verify events were published
        published_events = event_publisher.get_published_events()
        assert len(published_events) >= 2
        
        # Check event types
        event_types = [type(e).__name__ for e in published_events]
        assert "RoomCreated" in event_types
        assert "PlayerJoinedRoom" in event_types
    
    @pytest.mark.asyncio
    async def test_start_game_flow(self, uow, event_publisher):
        """Test starting a game."""
        # First create a room with players
        async with uow:
            room = Room(
                room_id=RoomId("room1"),
                room_code="TEST1",
                name="Game Room"
            )
            room.add_player(Player(PlayerId("p1"), "Player 1"))
            room.add_player(Player(PlayerId("p2"), "Player 2"))
            room.add_player(Player(PlayerId("p3"), "Player 3"))
            room.add_player(Player(PlayerId("p4"), "Player 4"))
            await uow.rooms.add(room)
            await uow.commit()
        
        # Start game
        start_use_case = StartGameUseCase(uow, event_publisher)
        start_request = StartGameRequest(
            room_id="room1",
            requesting_player_id="p1"
        )
        
        start_response = await start_use_case.execute(start_request)
        
        assert start_response.success is True
        assert start_response.game_id is not None
        
        # Verify game was created
        async with uow:
            game = await uow.games.get_by_id(GameId(start_response.game_id))
            assert game is not None
            assert game.room_id == RoomId("room1")
            assert game.is_active is True
            
            # Verify room is in game
            room = await uow.rooms.get_by_id(RoomId("room1"))
            assert room.is_in_game is True
        
        # Verify events
        published_events = event_publisher.get_published_events()
        game_started_events = [e for e in published_events if isinstance(e, GameStarted)]
        assert len(game_started_events) == 1
    
    @pytest.mark.asyncio
    async def test_unit_of_work_transaction_rollback(self, uow):
        """Test that unit of work properly rolls back on error."""
        # Add initial data
        async with uow:
            room = Room(
                room_id=RoomId("room1"),
                room_code="ROLL1",
                name="Rollback Test"
            )
            await uow.rooms.add(room)
            await uow.commit()
        
        # Try to make changes that will fail
        try:
            async with uow:
                room = await uow.rooms.get_by_id(RoomId("room1"))
                room.name = "Modified Name"
                await uow.rooms.update(room)
                
                # Simulate error before commit
                raise ValueError("Simulated error")
                
        except ValueError:
            pass
        
        # Verify changes were rolled back
        async with uow:
            room = await uow.rooms.get_by_id(RoomId("room1"))
            assert room.name == "Rollback Test"  # Original name
    
    @pytest.mark.asyncio
    async def test_repository_isolation(self, uow):
        """Test that repositories maintain isolation between transactions."""
        # Transaction 1: Add room
        async with uow:
            room = Room(
                room_id=RoomId("iso1"),
                room_code="ISO1",
                name="Isolation Test"
            )
            await uow.rooms.add(room)
            await uow.commit()
        
        # Transaction 2: Read and modify (don't commit)
        async with uow:
            room = await uow.rooms.get_by_id(RoomId("iso1"))
            room.add_player(Player(PlayerId("p1"), "Player 1"))
            await uow.rooms.update(room)
            # No commit - changes should not persist
        
        # Transaction 3: Verify no changes
        async with uow:
            room = await uow.rooms.get_by_id(RoomId("iso1"))
            assert len(room.players) == 0  # No players added
    
    @pytest.mark.asyncio
    async def test_event_publisher_ordering(self, event_publisher):
        """Test that events are published in order."""
        # Publish multiple events
        events = []
        for i in range(10):
            event = RoomCreated(
                room_id=f"room{i}",
                room_code=f"CODE{i}",
                host_id=f"host{i}",
                timestamp=datetime.utcnow()
            )
            events.append(event)
            await event_publisher.publish(event)
        
        # Verify order preserved
        published = event_publisher.get_published_events()
        assert len(published) == 10
        
        for i, event in enumerate(published):
            assert event.room_id == f"room{i}"
    
    @pytest.mark.asyncio
    async def test_feature_flag_integration(self, feature_flags):
        """Test feature flag integration with use cases."""
        # This would test actual feature flag usage in production
        # For now, verify flags are set correctly
        assert feature_flags.is_enabled(FeatureFlags.USE_CLEAN_ARCHITECTURE) is True
        assert feature_flags.is_enabled(FeatureFlags.USE_DOMAIN_EVENTS) is True
        assert feature_flags.is_enabled(FeatureFlags.USE_APPLICATION_LAYER) is True
    
    @pytest.mark.asyncio
    async def test_concurrent_room_operations(self, uow, event_publisher):
        """Test handling concurrent operations on same room."""
        # Create room
        async with uow:
            room = Room(
                room_id=RoomId("concurrent1"),
                room_code="CONC1",
                name="Concurrent Test"
            )
            room.add_player(Player(PlayerId("host"), "Host"))
            await uow.rooms.add(room)
            await uow.commit()
        
        # Simulate concurrent joins
        join_use_case = JoinRoomUseCase(uow, event_publisher, Mock())
        
        # Join 1
        response1 = await join_use_case.execute(JoinRoomRequest(
            player_id="p1",
            player_name="Player 1",
            room_id="concurrent1"
        ))
        assert response1.success is True
        
        # Join 2
        response2 = await join_use_case.execute(JoinRoomRequest(
            player_id="p2",
            player_name="Player 2",
            room_id="concurrent1"
        ))
        assert response2.success is True
        
        # Verify both players added
        async with uow:
            room = await uow.rooms.get_by_id(RoomId("concurrent1"))
            assert len(room.players) == 3  # Host + 2 players


class TestInMemoryEventPublisher:
    """Test the in-memory event publisher."""
    
    @pytest.mark.asyncio
    async def test_publish_single_event(self):
        """Test publishing a single event."""
        publisher = InMemoryEventPublisher()
        
        event = RoomCreated(
            room_id="room1",
            room_code="ABC123",
            host_id="player1",
            timestamp=datetime.utcnow()
        )
        
        await publisher.publish(event)
        
        events = publisher.get_published_events()
        assert len(events) == 1
        assert events[0] == event
    
    @pytest.mark.asyncio
    async def test_publish_batch_events(self):
        """Test publishing multiple events at once."""
        publisher = InMemoryEventPublisher()
        
        events = [
            RoomCreated(
                room_id=f"room{i}",
                room_code=f"CODE{i}",
                host_id=f"host{i}",
                timestamp=datetime.utcnow()
            )
            for i in range(5)
        ]
        
        await publisher.publish_batch(events)
        
        published = publisher.get_published_events()
        assert len(published) == 5
        assert published == events
    
    @pytest.mark.asyncio
    async def test_clear_events(self):
        """Test clearing published events."""
        publisher = InMemoryEventPublisher()
        
        # Publish some events
        for i in range(3):
            await publisher.publish(RoomCreated(
                room_id=f"room{i}",
                room_code=f"CODE{i}",
                host_id=f"host{i}",
                timestamp=datetime.utcnow()
            ))
        
        assert len(publisher.get_published_events()) == 3
        
        # Clear
        publisher.clear()
        assert len(publisher.get_published_events()) == 0