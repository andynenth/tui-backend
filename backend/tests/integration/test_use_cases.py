# tests/integration/test_use_cases.py
"""
Integration tests for application use cases.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from application.commands import (
    CreateRoomCommand,
    JoinRoomCommand,
    StartGameCommand,
    PlayTurnCommand,
    DeclareCommand
)
from application.use_cases import (
    CreateRoomUseCase,
    JoinRoomUseCase,
    StartGameUseCase,
    PlayTurnUseCase,
    DeclarePilesUseCase
)
from infrastructure import (
    RoomRepository,
    InMemoryGameRepository,
    InMemoryEventPublisher,
    SimpleAuthAdapter
)
from infrastructure.websocket.notification_adapter import WebSocketNotificationAdapter
from infrastructure.state_machine import StateMachineRepository
from domain.events.game_events import GameStartedEvent
from domain.events.player_events import PlayerJoinedEvent


class MockNotificationService:
    """Mock notification service for testing."""
    
    def __init__(self):
        self.notifications = []
    
    async def notify_room(self, room_id: str, event_type: str, data: dict):
        self.notifications.append({
            "room_id": room_id,
            "event_type": event_type,
            "data": data
        })
    
    async def notify_player(self, player_id: str, event_type: str, data: dict):
        self.notifications.append({
            "player_id": player_id,
            "event_type": event_type,  
            "data": data
        })


class TestCreateRoomUseCase:
    """Test room creation use case."""
    
    @pytest.mark.asyncio
    async def test_create_room_success(self):
        """Test successful room creation."""
        # Setup dependencies
        room_repo = RoomRepository()
        auth_service = SimpleAuthAdapter()
        event_publisher = InMemoryEventPublisher()
        notification_service = MockNotificationService()
        
        use_case = CreateRoomUseCase(
            room_repository=room_repo,
            auth_service=auth_service,
            event_publisher=event_publisher,
            notification_service=notification_service
        )
        
        # Execute
        command = CreateRoomCommand(
            host_name="Player1",
            room_settings={
                "max_players": 4,
                "max_score": 50
            }
        )
        
        result = await use_case.handle(command)
        
        # Verify
        assert result.success
        assert result.data.room_id is not None
        assert result.data.join_code is not None
        
        # Check room was created
        room = await room_repo.get(result.data.room_id)
        assert room is not None
        assert room.host == "Player1"
        assert len(room.players) == 1
    
    @pytest.mark.asyncio
    async def test_create_room_invalid_name(self):
        """Test room creation with invalid host name."""
        room_repo = RoomRepository()
        auth_service = SimpleAuthAdapter()
        event_publisher = InMemoryEventPublisher()
        notification_service = MockNotificationService()
        
        use_case = CreateRoomUseCase(
            room_repository=room_repo,
            auth_service=auth_service,
            event_publisher=event_publisher,
            notification_service=notification_service
        )
        
        command = CreateRoomCommand(
            host_name="",  # Invalid
            room_settings={}
        )
        
        result = await use_case.handle(command)
        
        assert not result.success
        assert "Host name is required" in result.error


class TestJoinRoomUseCase:
    """Test room joining use case."""
    
    @pytest.mark.asyncio
    async def test_join_room_success(self):
        """Test successful room joining."""
        # Setup - create a room first
        room_repo = RoomRepository()
        game_repo = InMemoryGameRepository()
        auth_service = SimpleAuthAdapter()
        event_publisher = InMemoryEventPublisher()
        notification_service = MockNotificationService()
        
        # Create room
        room = await room_repo.create("Host")
        room_id = room.id
        
        # Setup use case
        use_case = JoinRoomUseCase(
            room_repository=room_repo,
            game_repository=game_repo,
            auth_service=auth_service,
            event_publisher=event_publisher,
            notification_service=notification_service
        )
        
        # Execute
        command = JoinRoomCommand(
            room_id=room_id,
            player_name="Player2"
        )
        
        result = await use_case.handle(command)
        
        # Verify
        assert result.success
        assert result.data.room_id == room_id
        assert result.data.player_name == "Player2"
        
        # Check player was added
        room = await room_repo.get(room_id)
        assert len(room.players) == 2
        assert any(p.name == "Player2" for p in room.players)
    
    @pytest.mark.asyncio
    async def test_join_room_not_found(self):
        """Test joining non-existent room."""
        room_repo = RoomRepository()
        game_repo = InMemoryGameRepository()
        auth_service = SimpleAuthAdapter()
        event_publisher = InMemoryEventPublisher()
        notification_service = MockNotificationService()
        
        use_case = JoinRoomUseCase(
            room_repository=room_repo,
            game_repository=game_repo,
            auth_service=auth_service,
            event_publisher=event_publisher,
            notification_service=notification_service
        )
        
        command = JoinRoomCommand(
            room_id="non-existent",
            player_name="Player2"
        )
        
        result = await use_case.handle(command)
        
        assert not result.success
        assert "Room not found" in result.error
    
    @pytest.mark.asyncio
    async def test_join_full_room(self):
        """Test joining a full room."""
        room_repo = RoomRepository()
        game_repo = InMemoryGameRepository()
        auth_service = SimpleAuthAdapter()
        event_publisher = InMemoryEventPublisher()
        notification_service = MockNotificationService()
        
        # Create and fill room
        room = await room_repo.create("Host")
        room.settings["max_players"] = 2
        room.add_player("Player2", is_bot=False)
        await room_repo.save(room)
        
        use_case = JoinRoomUseCase(
            room_repository=room_repo,
            game_repository=game_repo,
            auth_service=auth_service,
            event_publisher=event_publisher,
            notification_service=notification_service
        )
        
        command = JoinRoomCommand(
            room_id=room.id,
            player_name="Player3"
        )
        
        result = await use_case.handle(command)
        
        assert not result.success
        assert "Room is full" in result.error


class TestStartGameUseCase:
    """Test game start use case."""
    
    @pytest.mark.asyncio
    async def test_start_game_success(self):
        """Test successful game start."""
        # Setup
        room_repo = RoomRepository()
        game_repo = InMemoryGameRepository()
        auth_service = SimpleAuthAdapter()
        event_publisher = InMemoryEventPublisher()
        notification_service = MockNotificationService()
        state_machine_factory = Mock()
        state_machine_factory.create = AsyncMock()
        
        # Create room with players
        room = await room_repo.create("Host")
        room.add_player("Player2", is_bot=False)
        room.add_player("Player3", is_bot=False)
        room.add_player("Player4", is_bot=False)
        await room_repo.save(room)
        
        # Create token for host
        token = await auth_service.create_token("Host", {"room_id": room.id})
        
        use_case = StartGameUseCase(
            room_repository=room_repo,
            game_repository=game_repo,
            auth_service=auth_service,
            event_publisher=event_publisher,
            notification_service=notification_service,
            state_machine_factory=state_machine_factory
        )
        
        command = StartGameCommand(
            room_id=room.id,
            host_id="Host"
        )
        
        result = await use_case.handle(command)
        
        assert result.success
        assert result.data.game_id is not None
        
        # Check game was created
        game = await game_repo.get(result.data.game_id)
        assert game is not None
        assert len(game.players) == 4
        assert game.is_started
    
    @pytest.mark.asyncio
    async def test_start_game_not_enough_players(self):
        """Test starting game with too few players."""
        room_repo = RoomRepository()
        game_repo = InMemoryGameRepository()
        auth_service = SimpleAuthAdapter()
        event_publisher = InMemoryEventPublisher()
        notification_service = MockNotificationService()
        state_machine_factory = Mock()
        
        # Create room with only host
        room = await room_repo.create("Host")
        await room_repo.save(room)
        
        use_case = StartGameUseCase(
            room_repository=room_repo,
            game_repository=game_repo,
            auth_service=auth_service,
            event_publisher=event_publisher,
            notification_service=notification_service,
            state_machine_factory=state_machine_factory
        )
        
        command = StartGameCommand(
            room_id=room.id,
            host_id="Host"
        )
        
        result = await use_case.handle(command)
        
        assert not result.success
        assert "at least 2 players" in result.error