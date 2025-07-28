"""
Contract Tests for Infrastructure Layer

These tests ensure that infrastructure implementations
correctly implement the defined contracts.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any

from infrastructure.interfaces.websocket_infrastructure import (
    IWebSocketConnection,
    IConnectionManager,
    IBroadcaster,
    IWebSocketInfrastructure,
    ConnectionInfo
)
from infrastructure.websocket.contract_implementations import (
    FastAPIWebSocketConnection,
    WebSocketConnectionManager,
    WebSocketBroadcaster,
    WebSocketInfrastructure
)


class TestWebSocketConnectionContract:
    """Test that FastAPIWebSocketConnection implements IWebSocketConnection correctly"""
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock FastAPI WebSocket"""
        mock = MagicMock()
        mock.send_json = AsyncMock()
        mock.receive_json = AsyncMock()
        mock.accept = AsyncMock()
        mock.close = AsyncMock()
        return mock
    
    @pytest.fixture
    def connection(self, mock_websocket):
        """Create a WebSocket connection"""
        return FastAPIWebSocketConnection(mock_websocket)
    
    @pytest.mark.asyncio
    async def test_send_json(self, connection, mock_websocket):
        """Test send_json implementation"""
        data = {"test": "data"}
        await connection.send_json(data)
        mock_websocket.send_json.assert_called_once_with(data)
    
    @pytest.mark.asyncio
    async def test_receive_json(self, connection, mock_websocket):
        """Test receive_json implementation"""
        expected = {"test": "data"}
        mock_websocket.receive_json.return_value = expected
        
        result = await connection.receive_json()
        assert result == expected
        mock_websocket.receive_json.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_accept(self, connection, mock_websocket):
        """Test accept implementation"""
        await connection.accept()
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close(self, connection, mock_websocket):
        """Test close implementation"""
        await connection.close(1000, "Normal closure")
        mock_websocket.close.assert_called_once_with(1000, "Normal closure")
        assert not connection.is_connected()
    
    def test_is_connected(self, connection):
        """Test is_connected implementation"""
        assert connection.is_connected()
        connection._connected = False
        assert not connection.is_connected()
    
    def test_implements_interface(self, connection):
        """Test that connection implements all required methods"""
        assert isinstance(connection, IWebSocketConnection)
        assert hasattr(connection, 'send_json')
        assert hasattr(connection, 'receive_json')
        assert hasattr(connection, 'accept')
        assert hasattr(connection, 'close')
        assert hasattr(connection, 'is_connected')


class TestConnectionManagerContract:
    """Test that WebSocketConnectionManager implements IConnectionManager correctly"""
    
    @pytest.fixture
    def manager(self):
        """Create a connection manager"""
        return WebSocketConnectionManager()
    
    @pytest.fixture
    def mock_connection(self):
        """Create a mock WebSocket connection"""
        return Mock(spec=IWebSocketConnection)
    
    @pytest.mark.asyncio
    async def test_register_connection(self, manager, mock_connection):
        """Test register_connection implementation"""
        await manager.register_connection("conn1", mock_connection, "room1")
        
        # Verify connection is registered
        assert manager.get_connection("conn1") == mock_connection
        
        # Verify connection info is stored
        info = manager.get_connection_info("conn1")
        assert info is not None
        assert info.connection_id == "conn1"
        assert info.room_id == "room1"
        assert info.is_active
    
    @pytest.mark.asyncio
    async def test_unregister_connection(self, manager, mock_connection):
        """Test unregister_connection implementation"""
        # Register first
        await manager.register_connection("conn1", mock_connection, "room1")
        
        # Then unregister
        await manager.unregister_connection("conn1")
        
        # Verify connection is removed
        assert manager.get_connection("conn1") is None
        assert manager.get_connection_info("conn1") is None
    
    def test_get_connections_in_room(self, manager, mock_connection):
        """Test get_connections_in_room implementation"""
        # Register connections
        asyncio.run(manager.register_connection("conn1", mock_connection, "room1"))
        mock_connection2 = Mock(spec=IWebSocketConnection)
        asyncio.run(manager.register_connection("conn2", mock_connection2, "room1"))
        mock_connection3 = Mock(spec=IWebSocketConnection)
        asyncio.run(manager.register_connection("conn3", mock_connection3, "room2"))
        
        # Get connections in room1
        room1_connections = manager.get_connections_in_room("room1")
        assert len(room1_connections) == 2
        assert "conn1" in room1_connections
        assert "conn2" in room1_connections
        assert room1_connections["conn1"] == mock_connection
        
        # Get connections in room2
        room2_connections = manager.get_connections_in_room("room2")
        assert len(room2_connections) == 1
        assert "conn3" in room2_connections
    
    def test_implements_interface(self, manager):
        """Test that manager implements all required methods"""
        assert isinstance(manager, IConnectionManager)
        assert hasattr(manager, 'register_connection')
        assert hasattr(manager, 'unregister_connection')
        assert hasattr(manager, 'get_connection')
        assert hasattr(manager, 'get_connections_in_room')
        assert hasattr(manager, 'get_connection_info')


class TestBroadcasterContract:
    """Test that WebSocketBroadcaster implements IBroadcaster correctly"""
    
    @pytest.fixture
    def mock_manager(self):
        """Create a mock connection manager"""
        return Mock(spec=IConnectionManager)
    
    @pytest.fixture
    def broadcaster(self, mock_manager):
        """Create a broadcaster"""
        return WebSocketBroadcaster(mock_manager)
    
    @pytest.mark.asyncio
    async def test_broadcast_to_room(self, broadcaster, mock_manager):
        """Test broadcast_to_room implementation"""
        # Setup mock connections
        mock_conn1 = AsyncMock(spec=IWebSocketConnection)
        mock_conn2 = AsyncMock(spec=IWebSocketConnection)
        mock_manager.get_connections_in_room.return_value = {
            "conn1": mock_conn1,
            "conn2": mock_conn2
        }
        
        # Broadcast message
        message = {"event": "test", "data": {}}
        count = await broadcaster.broadcast_to_room("room1", message)
        
        # Verify
        assert count == 2
        mock_conn1.send_json.assert_called_once_with(message)
        mock_conn2.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast_with_exclusions(self, broadcaster, mock_manager):
        """Test broadcast_to_room with exclusions"""
        # Setup mock connections
        mock_conn1 = AsyncMock(spec=IWebSocketConnection)
        mock_conn2 = AsyncMock(spec=IWebSocketConnection)
        mock_manager.get_connections_in_room.return_value = {
            "conn1": mock_conn1,
            "conn2": mock_conn2
        }
        
        # Broadcast with exclusion
        message = {"event": "test", "data": {}}
        count = await broadcaster.broadcast_to_room(
            "room1",
            message,
            exclude_connections={"conn1"}
        )
        
        # Verify only conn2 received message
        assert count == 1
        mock_conn1.send_json.assert_not_called()
        mock_conn2.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_send_to_connection(self, broadcaster, mock_manager):
        """Test send_to_connection implementation"""
        # Setup mock connection
        mock_conn = AsyncMock(spec=IWebSocketConnection)
        mock_manager.get_connection.return_value = mock_conn
        
        # Send message
        message = {"event": "test", "data": {}}
        success = await broadcaster.send_to_connection("conn1", message)
        
        # Verify
        assert success is True
        mock_conn.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_broadcast_to_connections(self, broadcaster, mock_manager):
        """Test broadcast_to_connections implementation"""
        # Setup mock connections
        mock_conn1 = AsyncMock(spec=IWebSocketConnection)
        mock_conn2 = AsyncMock(spec=IWebSocketConnection)
        
        def get_connection_side_effect(conn_id):
            if conn_id == "conn1":
                return mock_conn1
            elif conn_id == "conn2":
                return mock_conn2
            return None
        
        mock_manager.get_connection.side_effect = get_connection_side_effect
        
        # Broadcast to specific connections
        message = {"event": "test", "data": {}}
        count = await broadcaster.broadcast_to_connections(
            {"conn1", "conn2", "conn3"},  # conn3 doesn't exist
            message
        )
        
        # Verify
        assert count == 2
        mock_conn1.send_json.assert_called_once_with(message)
        mock_conn2.send_json.assert_called_once_with(message)
    
    def test_implements_interface(self, broadcaster):
        """Test that broadcaster implements all required methods"""
        assert isinstance(broadcaster, IBroadcaster)
        assert hasattr(broadcaster, 'broadcast_to_room')
        assert hasattr(broadcaster, 'send_to_connection')
        assert hasattr(broadcaster, 'broadcast_to_connections')


class TestWebSocketInfrastructureContract:
    """Test that WebSocketInfrastructure implements IWebSocketInfrastructure correctly"""
    
    @pytest.fixture
    def infrastructure(self):
        """Create WebSocket infrastructure"""
        return WebSocketInfrastructure()
    
    def test_get_connection_manager(self, infrastructure):
        """Test get_connection_manager implementation"""
        manager = infrastructure.get_connection_manager()
        assert isinstance(manager, IConnectionManager)
        assert manager is infrastructure.connection_manager
    
    def test_get_broadcaster(self, infrastructure):
        """Test get_broadcaster implementation"""
        broadcaster = infrastructure.get_broadcaster()
        assert isinstance(broadcaster, IBroadcaster)
        assert broadcaster is infrastructure.broadcaster
    
    @pytest.mark.asyncio
    async def test_handle_connection(self, infrastructure):
        """Test handle_connection implementation"""
        # Create mock websocket
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.receive_json = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.close = AsyncMock()
        
        # Create mock message handler
        async def mock_handler(message: Dict[str, Any], conn_id: str):
            return {"response": "test"}
        
        # Simulate WebSocket disconnect after one message
        mock_ws.receive_json.side_effect = [
            {"event": "test", "data": {}},
            Exception("WebSocket disconnected")
        ]
        
        # Handle connection
        await infrastructure.handle_connection(
            mock_ws,
            "room1",
            mock_handler
        )
        
        # Verify connection lifecycle
        mock_ws.accept.assert_called_once()
        assert mock_ws.receive_json.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_shutdown(self, infrastructure):
        """Test shutdown implementation"""
        # Add a mock connection
        mock_conn = AsyncMock(spec=IWebSocketConnection)
        infrastructure.connection_manager._connections["conn1"] = mock_conn
        
        # Shutdown
        await infrastructure.shutdown()
        
        # Verify connection was closed
        mock_conn.close.assert_called_once_with(1001, "Server shutting down")
    
    def test_implements_interface(self, infrastructure):
        """Test that infrastructure implements all required methods"""
        assert isinstance(infrastructure, IWebSocketInfrastructure)
        assert hasattr(infrastructure, 'handle_connection')
        assert hasattr(infrastructure, 'get_connection_manager')
        assert hasattr(infrastructure, 'get_broadcaster')
        assert hasattr(infrastructure, 'shutdown')