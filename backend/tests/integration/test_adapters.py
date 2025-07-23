# tests/integration/test_adapters.py
"""
Integration tests for infrastructure adapters.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from infrastructure.websocket import (
    ConnectionManager,
    BroadcastService,
    WebSocketNotificationAdapter
)
from infrastructure.persistence import (
    InMemoryGameRepository,
    RoomRepository,
    InMemoryEventPublisher
)
from infrastructure.bot import SimpleBotStrategyFactory
from infrastructure.auth import SimpleAuthAdapter
from domain.entities.game import Game
from domain.entities.player import Player
from domain.value_objects.bot_strategy import BotDifficulty


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        self.sent_messages = []
        self.closed = False
    
    async def send_json(self, data):
        self.sent_messages.append(data)
    
    async def close(self):
        self.closed = True


class TestWebSocketNotificationAdapter:
    """Test WebSocket notification adapter."""
    
    @pytest.mark.asyncio
    async def test_notify_room(self):
        """Test room notification through adapter."""
        # Setup
        connection_manager = ConnectionManager()
        broadcast_service = BroadcastService()
        
        adapter = WebSocketNotificationAdapter(
            connection_manager=connection_manager,
            broadcast_service=broadcast_service
        )
        
        # Add mock connections
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        await connection_manager.connect("room-123", "player1", ws1)
        await connection_manager.connect("room-123", "player2", ws2)
        
        # Send notification
        await adapter.notify_room("room-123", "test_event", {"data": "value"})
        
        # Verify both connections received message
        assert len(ws1.sent_messages) == 1
        assert len(ws2.sent_messages) == 1
        
        message = ws1.sent_messages[0]
        assert message["type"] == "test_event"
        assert message["data"] == {"data": "value"}
    
    @pytest.mark.asyncio
    async def test_notify_player(self):
        """Test player-specific notification."""
        connection_manager = ConnectionManager()
        broadcast_service = BroadcastService()
        
        adapter = WebSocketNotificationAdapter(
            connection_manager=connection_manager,
            broadcast_service=broadcast_service
        )
        
        # Add connections
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        await connection_manager.connect("room-123", "player1", ws1)
        await connection_manager.connect("room-123", "player2", ws2)
        
        # Send to specific player
        await adapter.notify_player("player1", "private_message", {"secret": "data"})
        
        # Only player1 should receive
        assert len(ws1.sent_messages) == 1
        assert len(ws2.sent_messages) == 0


class TestGameRepository:
    """Test game repository implementations."""
    
    @pytest.mark.asyncio
    async def test_in_memory_repository(self):
        """Test in-memory game repository."""
        repo = InMemoryGameRepository()
        
        # Create game
        mock_publisher = Mock()
        mock_publisher.publish = AsyncMock()
        
        game = Game(
            players=[
                Player("Player1"),
                Player("Player2")
            ],
            event_publisher=mock_publisher
        )
        
        # Save
        await repo.save(game)
        
        # Retrieve
        loaded = await repo.get(game.id)
        assert loaded is not None
        assert loaded.id == game.id
        assert len(loaded.players) == 2
        
        # List all
        all_games = await repo.list_all()
        assert len(all_games) == 1
        
        # Delete
        await repo.delete(game.id)
        assert await repo.get(game.id) is None
    
    @pytest.mark.asyncio
    async def test_repository_not_found(self):
        """Test repository returns None for missing items."""
        repo = InMemoryGameRepository()
        
        result = await repo.get("non-existent")
        assert result is None


class TestRoomRepository:
    """Test room repository."""
    
    @pytest.mark.asyncio
    async def test_room_creation(self):
        """Test room creation and retrieval."""
        repo = RoomRepository()
        
        # Create room
        room = await repo.create("Host")
        
        assert room.id is not None
        assert room.host == "Host"
        assert room.join_code is not None
        assert len(room.join_code) == 6
        
        # Retrieve by ID
        loaded = await repo.get(room.id)
        assert loaded.id == room.id
        
        # Retrieve by join code
        by_code = await repo.get_by_join_code(room.join_code)
        assert by_code.id == room.id
    
    @pytest.mark.asyncio
    async def test_room_join_code_uniqueness(self):
        """Test room join codes are unique."""
        repo = RoomRepository()
        
        rooms = []
        for i in range(10):
            room = await repo.create(f"Host{i}")
            rooms.append(room)
        
        # Check all join codes are unique
        join_codes = [r.join_code for r in rooms]
        assert len(join_codes) == len(set(join_codes))


class TestBotStrategyFactory:
    """Test bot strategy factory."""
    
    def test_create_easy_bot(self):
        """Test creating easy difficulty bot."""
        factory = SimpleBotStrategyFactory()
        
        strategy = factory.create_strategy(BotDifficulty.EASY)
        
        assert strategy is not None
        assert hasattr(strategy, 'make_declaration')
        assert hasattr(strategy, 'choose_pieces_to_play')
    
    def test_create_medium_bot(self):
        """Test creating medium difficulty bot."""
        factory = SimpleBotStrategyFactory()
        
        strategy = factory.create_strategy(BotDifficulty.MEDIUM)
        
        assert strategy is not None
        # Medium should be different from easy
        easy = factory.create_strategy(BotDifficulty.EASY)
        assert type(strategy) != type(easy)
    
    def test_unsupported_difficulty(self):
        """Test unsupported difficulty falls back to easy."""
        factory = SimpleBotStrategyFactory()
        
        # HARD not implemented yet
        strategy = factory.create_strategy(BotDifficulty.HARD)
        
        # Should fall back to easy
        easy = factory.create_strategy(BotDifficulty.EASY)
        assert type(strategy) == type(easy)


class TestAuthAdapter:
    """Test authentication adapter."""
    
    @pytest.mark.asyncio
    async def test_token_creation_and_validation(self):
        """Test token lifecycle."""
        auth = SimpleAuthAdapter()
        
        # Create token
        token = await auth.create_token("player1", {"room_id": "room-123"})
        assert token is not None
        
        # Validate token
        is_valid = await auth.validate_token(token)
        assert is_valid
        
        # Get player
        player_id = await auth.get_player_id(token)
        assert player_id == "player1"
        
        # Check player in room
        in_room = await auth.is_player_in_room(token, "room-123")
        assert in_room
        
        # Wrong room
        in_wrong_room = await auth.is_player_in_room(token, "room-456")
        assert not in_wrong_room
    
    @pytest.mark.asyncio
    async def test_invalid_token(self):
        """Test invalid token handling."""
        auth = SimpleAuthAdapter()
        
        # Invalid token
        is_valid = await auth.validate_token("invalid-token")
        assert not is_valid
        
        # Get player from invalid token
        player_id = await auth.get_player_id("invalid-token")
        assert player_id is None
    
    @pytest.mark.asyncio
    async def test_token_invalidation(self):
        """Test token can be invalidated."""
        auth = SimpleAuthAdapter()
        
        # Create and invalidate
        token = await auth.create_token("player1", {})
        await auth.invalidate_token(token)
        
        # Should no longer be valid
        is_valid = await auth.validate_token(token)
        assert not is_valid