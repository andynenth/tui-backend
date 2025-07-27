"""
Tests for WebSocket infrastructure integration.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any, List

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from infrastructure.websocket import (
    # Connection Management
    ConnectionManager,
    ConnectionInfo,
    ConnectionState,
    InMemoryConnectionRegistry,
    
    # Repositories
    WebSocketRoomRepository,
    WebSocketGameRepository,
    SubscriptionManager,
    ChangeType,
    
    # Event Propagation
    EventPropagator,
    WebSocketEventBus,
    Event,
    EventPriority,
    BroadcastScope,
    RoomBroadcast,
    
    # Middleware
    WebSocketInfrastructureMiddleware,
    ConnectionTrackingMiddleware,
    RateLimitingMiddleware,
    ObservabilityMiddleware,
    ErrorHandlingMiddleware,
    
    # State Sync
    StateSynchronizer,
    SyncStrategy,
    FullSync,
    DeltaSync,
    
    # Recovery
    ConnectionRecoveryManager,
    ReconnectionHandler,
    RecoveryConfig
)

from domain.entities import Room, Game, Player
from domain.value_objects import RoomState


# Test Fixtures

@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket."""
    ws = Mock(spec=WebSocket)
    ws.client_state = WebSocketState.CONNECTED
    ws.send_json = AsyncMock()
    ws.accept = AsyncMock()
    ws.close = AsyncMock()
    ws.headers = {"user-agent": "test-agent"}
    ws.client = Mock(host="127.0.0.1")
    ws.query_params = {}
    return ws


@pytest.fixture
async def connection_manager():
    """Create a connection manager."""
    manager = ConnectionManager()
    await manager.start()
    yield manager
    await manager.stop()


@pytest.fixture
def subscription_manager():
    """Create a subscription manager."""
    return SubscriptionManager()


@pytest.fixture
async def event_propagator(connection_manager):
    """Create an event propagator."""
    propagator = EventPropagator(connection_manager)
    await propagator.start()
    yield propagator
    await propagator.stop()


# Connection Management Tests

class TestConnectionManager:
    """Test connection management functionality."""
    
    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, connection_manager, mock_websocket):
        """Test basic connection lifecycle."""
        # Connect
        connection = await connection_manager.connect(
            mock_websocket,
            "test-connection-1"
        )
        
        assert connection.connection_id == "test-connection-1"
        assert connection.state == ConnectionState.CONNECTED
        assert connection_manager._metrics['active_connections'] == 1
        
        # Authenticate
        await connection_manager.authenticate(
            "test-connection-1",
            "player-123"
        )
        
        connection = await connection_manager.registry.get_connection("test-connection-1")
        assert connection.player_id == "player-123"
        assert connection.state == ConnectionState.AUTHENTICATED
        
        # Join room
        await connection_manager.join_room(
            "test-connection-1",
            "room-456"
        )
        
        connection = await connection_manager.registry.get_connection("test-connection-1")
        assert connection.room_id == "room-456"
        assert connection.state == ConnectionState.IN_ROOM
        
        # Disconnect
        await connection_manager.disconnect("test-connection-1")
        
        assert connection_manager._metrics['active_connections'] == 0
        mock_websocket.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_broadcasting(self, connection_manager, mock_websocket):
        """Test message broadcasting."""
        # Create multiple connections
        connections = []
        for i in range(3):
            ws = Mock(spec=WebSocket)
            ws.client_state = WebSocketState.CONNECTED
            ws.send_json = AsyncMock()
            ws.accept = AsyncMock()
            
            conn = await connection_manager.connect(ws, f"conn-{i}")
            await connection_manager.join_room(f"conn-{i}", "room-1")
            connections.append((ws, conn))
        
        # Broadcast to room
        message = {"type": "test", "data": "hello"}
        sent = await connection_manager.broadcast_to_room("room-1", message)
        
        assert sent == 3
        for ws, _ in connections:
            ws.send_json.assert_called_with(message)
    
    @pytest.mark.asyncio
    async def test_connection_registry(self):
        """Test connection registry operations."""
        registry = InMemoryConnectionRegistry()
        
        # Add connection
        connection = ConnectionInfo(
            connection_id="test-1",
            websocket=Mock(),
            player_id="player-1",
            room_id="room-1"
        )
        
        await registry.add_connection(connection)
        
        # Get by ID
        retrieved = await registry.get_connection("test-1")
        assert retrieved == connection
        
        # Get by player
        player_connections = await registry.get_connections_by_player("player-1")
        assert len(player_connections) == 1
        assert player_connections[0] == connection
        
        # Get by room
        room_connections = await registry.get_connections_by_room("room-1")
        assert len(room_connections) == 1
        assert room_connections[0] == connection
        
        # Remove connection
        await registry.remove_connection("test-1")
        assert await registry.get_connection("test-1") is None


# WebSocket Repository Tests

class TestWebSocketRepositories:
    """Test WebSocket-aware repository functionality."""
    
    @pytest.mark.asyncio
    async def test_room_repository_broadcasting(
        self,
        connection_manager,
        subscription_manager,
        mock_websocket
    ):
        """Test room repository with broadcasting."""
        # Create repository
        repo = WebSocketRoomRepository(
            connection_manager,
            subscription_manager
        )
        
        # Subscribe to room changes
        connection = await connection_manager.connect(mock_websocket, "test-conn")
        await subscription_manager.subscribe(
            "test-conn",
            "room",
            "room-1"
        )
        
        # Create room
        room = Room(
            id="room-1",
            code="ABC123",
            players=[],
            state=RoomState.WAITING,
            game_settings={}
        )
        
        await repo.save(room)
        
        # Should broadcast creation
        mock_websocket.send_json.assert_called()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args['type'] == "repository_change"
        assert call_args['event']['change_type'] == "created"
        assert call_args['event']['entity_id'] == "room-1"
    
    @pytest.mark.asyncio
    async def test_subscription_filtering(self, subscription_manager):
        """Test subscription filtering."""
        # Subscribe with filter
        def only_created(event):
            return event.change_type == ChangeType.CREATED
        
        sub_id = await subscription_manager.subscribe(
            "conn-1",
            "room",
            filter_func=only_created
        )
        
        # Test matching event
        created_event = ChangeEvent(
            entity_type="room",
            entity_id="room-1",
            change_type=ChangeType.CREATED,
            entity=None
        )
        
        subscribers = await subscription_manager.get_subscribers(created_event)
        assert len(subscribers) == 1
        
        # Test non-matching event
        updated_event = ChangeEvent(
            entity_type="room",
            entity_id="room-1",
            change_type=ChangeType.UPDATED,
            entity=None
        )
        
        subscribers = await subscription_manager.get_subscribers(updated_event)
        assert len(subscribers) == 0


# Event Propagation Tests

class TestEventPropagation:
    """Test event propagation functionality."""
    
    @pytest.mark.asyncio
    async def test_event_broadcasting(
        self,
        connection_manager,
        event_propagator,
        mock_websocket
    ):
        """Test basic event broadcasting."""
        # Create connections in a room
        for i in range(2):
            ws = Mock(spec=WebSocket)
            ws.client_state = WebSocketState.CONNECTED
            ws.send_json = AsyncMock()
            ws.accept = AsyncMock()
            
            await connection_manager.connect(ws, f"conn-{i}")
            await connection_manager.join_room(f"conn-{i}", "room-1")
        
        # Create and propagate event
        event = Event(
            event_type="game_started",
            payload={"game_id": "game-1"},
            scope=BroadcastScope.ROOM,
            target_id="room-1"
        )
        
        recipients = await event_propagator.propagate(event)
        assert recipients == 2
        
        # Wait for async processing
        await asyncio.sleep(0.1)
    
    @pytest.mark.asyncio
    async def test_event_priority_queuing(self, connection_manager, event_propagator):
        """Test event priority handling."""
        # Track sent events
        sent_events = []
        
        async def mock_send(conn_id, msg):
            sent_events.append(msg)
            return True
        
        connection_manager.send_to_connection = mock_send
        
        # Create connection
        await connection_manager.registry.add_connection(
            ConnectionInfo("test-conn", Mock())
        )
        
        # Send events with different priorities
        events = [
            Event("low", {}, priority=EventPriority.LOW),
            Event("critical", {}, priority=EventPriority.CRITICAL),
            Event("normal", {}, priority=EventPriority.NORMAL),
            Event("high", {}, priority=EventPriority.HIGH)
        ]
        
        for event in events:
            await event_propagator._queue_event(event, "test-conn")
        
        # Critical events should be processed first
        # (Implementation would need priority queue support)
    
    @pytest.mark.asyncio
    async def test_event_bus(self, connection_manager):
        """Test high-level event bus."""
        bus = WebSocketEventBus(connection_manager)
        await bus.start()
        
        # Register handler
        handled_events = []
        
        def handler(payload):
            handled_events.append(payload)
        
        bus.on("test_event", handler)
        
        # Handle event
        await bus.handle_event("test_event", {"data": "test"})
        
        assert len(handled_events) == 1
        assert handled_events[0]["data"] == "test"
        
        await bus.stop()


# Middleware Tests

class TestMiddleware:
    """Test WebSocket middleware functionality."""
    
    @pytest.mark.asyncio
    async def test_middleware_chain(self, connection_manager, mock_websocket):
        """Test middleware chaining."""
        # Create middleware
        tracking = ConnectionTrackingMiddleware(connection_manager)
        
        # Create infrastructure middleware
        infra = WebSocketInfrastructureMiddleware(connection_manager)
        infra.add_middleware(tracking)
        
        # Handle connection
        connection = await infra.handle_connection(
            mock_websocket,
            "test-conn"
        )
        
        assert connection is not None
        assert 'user_agent' in connection.metadata
        assert connection.metadata['user_agent'] == "test-agent"
    
    @pytest.mark.asyncio
    async def test_rate_limiting_middleware(self, mock_websocket):
        """Test rate limiting middleware."""
        limiter = RateLimitingMiddleware()
        
        connection = ConnectionInfo(
            connection_id="test-conn",
            websocket=mock_websocket,
            player_id="player-1"
        )
        
        # Process messages up to limit
        for i in range(10):
            message = {"type": "play_piece", "data": i}
            result = await limiter.process_message(connection, message)
            assert result is not None
        
        # Next message should be rate limited
        # (Would need actual rate limiter implementation)
    
    @pytest.mark.asyncio
    async def test_error_handling_middleware(self, mock_websocket):
        """Test error handling middleware."""
        error_handler = ErrorHandlingMiddleware()
        
        connection = ConnectionInfo(
            connection_id="test-conn",
            websocket=mock_websocket
        )
        
        # Valid message
        valid_message = {"type": "test", "data": "valid"}
        result = await error_handler.process_message(connection, valid_message)
        assert result == valid_message
        
        # Invalid message
        invalid_message = "not a dict"
        result = await error_handler.process_message(connection, invalid_message)
        assert result is None
        
        # Check error was sent
        mock_websocket.send_json.assert_called()
        error_msg = mock_websocket.send_json.call_args[0][0]
        assert error_msg['type'] == "error"


# State Synchronization Tests

class TestStateSynchronization:
    """Test state synchronization functionality."""
    
    @pytest.mark.asyncio
    async def test_full_sync_strategy(
        self,
        connection_manager,
        event_propagator,
        mock_websocket
    ):
        """Test full sync strategy."""
        connection = ConnectionInfo("test-conn", mock_websocket)
        await connection_manager.registry.add_connection(connection)
        
        sync = FullSync(connection_manager, event_propagator)
        
        # Sync state
        state = {
            "version": 5,
            "data": {"field": "value"}
        }
        
        await sync.sync_state(
            connection,
            "room",
            "room-1",
            state
        )
        
        # Check message sent
        mock_websocket.send_json.assert_called()
        sync_msg = mock_websocket.send_json.call_args[0][0]
        assert sync_msg['type'] == "state_sync"
        assert sync_msg['strategy'] == "full"
        assert sync_msg['version'] == 5
    
    @pytest.mark.asyncio
    async def test_delta_sync_strategy(
        self,
        connection_manager,
        event_propagator,
        mock_websocket
    ):
        """Test delta sync strategy."""
        connection = ConnectionInfo("test-conn", mock_websocket)
        await connection_manager.registry.add_connection(connection)
        
        sync = DeltaSync(connection_manager, event_propagator)
        
        # Record some deltas
        sync.record_delta(
            "room",
            "room-1",
            1,
            2,
            [{"op": "add", "path": "/players/0", "value": "player1"}]
        )
        
        # Sync from version 1
        state = {"version": 2, "data": {}}
        await sync.sync_state(
            connection,
            "room",
            "room-1",
            state,
            client_version=1
        )
        
        # Should send delta
        mock_websocket.send_json.assert_called()
    
    @pytest.mark.asyncio
    async def test_state_synchronizer(
        self,
        connection_manager,
        event_propagator,
        mock_websocket
    ):
        """Test main state synchronizer."""
        synchronizer = StateSynchronizer(
            connection_manager,
            event_propagator
        )
        
        # Add connection
        connection = ConnectionInfo("test-conn", mock_websocket)
        await connection_manager.registry.add_connection(connection)
        
        # Subscribe to sync
        await synchronizer.subscribe_to_sync(
            "test-conn",
            "room",
            "room-1"
        )
        
        # Sync state
        state = {"version": 1, "data": {}}
        await synchronizer.sync_state(
            "room",
            "room-1",
            state
        )
        
        # Should sync to subscribed connection
        mock_websocket.send_json.assert_called()


# Recovery Tests

class TestConnectionRecovery:
    """Test connection recovery functionality."""
    
    @pytest.mark.asyncio
    async def test_recovery_token_generation(self, connection_manager):
        """Test recovery token generation."""
        handler = ReconnectionHandler(
            connection_manager,
            RecoveryConfig()
        )
        
        # Generate token
        token = await handler.generate_recovery_token("conn-1")
        assert token is not None
        assert len(token) == 36  # UUID format
        
        # Token should map to connection
        assert handler._recovery_tokens[token] == "conn-1"
    
    @pytest.mark.asyncio
    async def test_successful_recovery(
        self,
        connection_manager,
        mock_websocket
    ):
        """Test successful connection recovery."""
        handler = ReconnectionHandler(
            connection_manager,
            RecoveryConfig()
        )
        
        # Create original connection
        old_conn = ConnectionInfo(
            connection_id="old-conn",
            websocket=Mock(),
            player_id="player-1",
            room_id="room-1"
        )
        
        # Handle disconnection
        context = await handler.handle_disconnection(old_conn)
        token = context.recovery_token
        
        # Create new connection
        new_conn = ConnectionInfo(
            connection_id="new-conn",
            websocket=mock_websocket
        )
        await connection_manager.registry.add_connection(new_conn)
        
        # Attempt recovery
        success = await handler.attempt_recovery(token, new_conn)
        
        assert success is True
        assert new_conn.player_id == "player-1"
        assert new_conn.room_id == "room-1"
        
        # Should send recovery success message
        mock_websocket.send_json.assert_called()
        msg = mock_websocket.send_json.call_args[0][0]
        assert msg['type'] == "recovery_success"
    
    @pytest.mark.asyncio
    async def test_recovery_manager(
        self,
        connection_manager,
        event_propagator,
        mock_websocket
    ):
        """Test full recovery manager."""
        state_sync = StateSynchronizer(connection_manager, event_propagator)
        
        recovery_manager = ConnectionRecoveryManager(
            connection_manager,
            state_sync,
            event_propagator
        )
        
        await recovery_manager.start()
        
        # Handle connection with recovery
        ws = Mock(spec=WebSocket)
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.client_state = WebSocketState.CONNECTED
        
        connection = await recovery_manager.handle_connection(
            ws,
            "new-conn",
            recovery_token=None  # No recovery
        )
        
        assert connection is not None
        assert connection.connection_id == "new-conn"
        
        await recovery_manager.stop()


# Integration Tests

class TestWebSocketIntegration:
    """Test full WebSocket infrastructure integration."""
    
    @pytest.mark.asyncio
    async def test_full_game_flow(self, connection_manager, subscription_manager):
        """Test complete game flow with WebSocket infrastructure."""
        # Create components
        event_bus = WebSocketEventBus(connection_manager)
        await event_bus.start()
        
        room_repo = WebSocketRoomRepository(
            connection_manager,
            subscription_manager
        )
        
        # Create players
        players = []
        for i in range(2):
            ws = Mock(spec=WebSocket)
            ws.client_state = WebSocketState.CONNECTED
            ws.send_json = AsyncMock()
            ws.accept = AsyncMock()
            
            conn = await connection_manager.connect(ws, f"player-{i}")
            await connection_manager.authenticate(f"player-{i}", f"player-{i}")
            
            # Subscribe to room updates
            await subscription_manager.subscribe(
                f"player-{i}",
                "room"
            )
            
            players.append((ws, conn))
        
        # Create room
        room = Room(
            id="game-room",
            code="GAME123",
            players=[
                Player(id="player-0", name="Player 0"),
                Player(id="player-1", name="Player 1")
            ],
            state=RoomState.WAITING,
            game_settings={}
        )
        
        await room_repo.save(room)
        
        # All players should receive room creation
        for ws, _ in players:
            ws.send_json.assert_called()
        
        # Join room
        for i, (ws, conn) in enumerate(players):
            await connection_manager.join_room(f"player-{i}", "game-room")
        
        # Broadcast game start event
        await event_bus.emit_to_room(
            "game-room",
            "game_started",
            {"game_id": "game-1"}
        )
        
        # Wait for event processing
        await asyncio.sleep(0.1)
        
        await event_bus.stop()
    
    @pytest.mark.asyncio
    async def test_middleware_integration(self, connection_manager):
        """Test full middleware stack."""
        # Create middleware stack
        infra = WebSocketInfrastructureMiddleware(connection_manager)
        infra.add_middleware(ConnectionTrackingMiddleware(connection_manager))
        infra.add_middleware(RateLimitingMiddleware())
        infra.add_middleware(ObservabilityMiddleware())
        infra.add_middleware(ErrorHandlingMiddleware())
        
        # Create WebSocket
        ws = Mock(spec=WebSocket)
        ws.client_state = WebSocketState.CONNECTED
        ws.send_json = AsyncMock()
        ws.accept = AsyncMock()
        ws.headers = {"user-agent": "test"}
        ws.client = Mock(host="127.0.0.1")
        ws.query_params = {}
        
        # Connect through middleware
        connection = await infra.handle_connection(ws, "test-conn")
        assert connection is not None
        
        # Process message through middleware
        message = {"type": "test_action", "data": "test"}
        processed = await infra.handle_message(connection, message)
        assert processed is not None
        
        # Disconnect through middleware
        await infra.handle_disconnect(connection)