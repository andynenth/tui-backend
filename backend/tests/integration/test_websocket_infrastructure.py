"""
Integration tests for WebSocket infrastructure
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket, WebSocketDisconnect

from infrastructure.websocket.websocket_server import WebSocketServer
from application.websocket.message_router import MessageRouter
from application.websocket.disconnect_handler import DisconnectHandler


@pytest.fixture
def websocket_components():
    """Create WebSocket components for integration testing."""
    server = WebSocketServer()
    router = MessageRouter()
    disconnect_handler = DisconnectHandler()
    return server, router, disconnect_handler


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing."""
    websocket = AsyncMock(spec=WebSocket)
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.receive_json = AsyncMock()
    websocket._ws_id = "ws_test_123"
    return websocket


class TestWebSocketIntegration:
    """Integration tests for WebSocket message flow."""
    
    @pytest.mark.asyncio
    async def test_full_message_flow(self, websocket_components, mock_websocket):
        """Test full message flow from WebSocket to handlers."""
        server, router, _ = websocket_components
        room_id = "test_room"
        
        # Setup mocks
        with patch('infrastructure.websocket.websocket_server.register') as mock_register:
            with patch('infrastructure.websocket.websocket_server.validate_websocket_message') as mock_validate:
                with patch.object(router, '_route_to_adapter') as mock_route:
                    # Configure mocks
                    mock_register.return_value = "conn_123"
                    mock_validate.return_value = (True, None, {"event": "ping", "data": {}})
                    mock_route.return_value = {"event": "pong", "data": {}}
                    
                    # Accept connection
                    await server.accept_connection(mock_websocket)
                    
                    # Handle connection
                    connection_id = await server.handle_connection(mock_websocket, room_id)
                    assert connection_id == "conn_123"
                    
                    # Receive message
                    mock_websocket.receive_json.return_value = {"event": "ping", "data": {}}
                    message = await server.receive_message(mock_websocket)
                    assert message is not None
                    
                    # Route message
                    response = await router.route_message(mock_websocket, message, room_id)
                    assert response["event"] == "pong"
                    
                    # Send response
                    await server.send_message(mock_websocket, response)
                    mock_websocket.send_json.assert_called_with(response)
                    
    @pytest.mark.asyncio
    async def test_connection_disconnect_flow(self, websocket_components, mock_websocket):
        """Test connection and disconnection flow."""
        server, _, disconnect_handler = websocket_components
        room_id = "ROOM123"
        
        with patch('infrastructure.websocket.websocket_server.register') as mock_register:
            with patch('infrastructure.websocket.websocket_server.unregister') as mock_unregister:
                with patch('infrastructure.websocket.websocket_server.connection_manager') as mock_cm:
                    # Setup connection
                    mock_register.return_value = "conn_123"
                    mock_connection = MagicMock()
                    mock_connection.player_name = "TestPlayer"
                    mock_connection.room_id = room_id
                    mock_cm.get_connection_by_websocket_id.return_value = mock_connection
                    
                    # Connect
                    connection_id = await server.handle_connection(mock_websocket, room_id)
                    
                    # Disconnect
                    returned_id = await server.handle_disconnect(
                        mock_websocket,
                        room_id,
                        mock_websocket._ws_id
                    )
                    
                    assert returned_id == connection_id
                    mock_unregister.assert_called_once_with(connection_id)
                    
    @pytest.mark.asyncio
    async def test_error_handling_flow(self, websocket_components, mock_websocket):
        """Test error handling in message flow."""
        server, router, _ = websocket_components
        room_id = "test_room"
        
        with patch('infrastructure.websocket.websocket_server.validate_websocket_message') as mock_validate:
            # Invalid message
            mock_validate.return_value = (False, "Invalid format", None)
            mock_websocket.receive_json.return_value = {"bad": "message"}
            
            message = await server.receive_message(mock_websocket)
            assert message is None
            
            # Check error sent
            mock_websocket.send_json.assert_called_once()
            error_msg = mock_websocket.send_json.call_args[0][0]
            assert error_msg["event"] == "error"
            assert "Invalid format" in error_msg["data"]["message"]
            
    @pytest.mark.asyncio
    async def test_room_validation_flow(self, websocket_components, mock_websocket):
        """Test room validation flow."""
        _, router, _ = websocket_components
        
        # Test lobby - always valid
        valid = await router.handle_room_validation(mock_websocket, "lobby")
        assert valid is True
        
        # Test non-existent room
        with patch('application.websocket.message_router.get_unit_of_work') as mock_get_uow:
            mock_uow = AsyncMock()
            mock_get_uow.return_value = mock_uow
            mock_uow.rooms.get_by_id.return_value = None
            
            valid = await router.handle_room_validation(mock_websocket, "INVALID")
            assert valid is False
            
            # Check room_not_found sent
            mock_websocket.send_json.assert_called_once()
            msg = mock_websocket.send_json.call_args[0][0]
            assert msg["event"] == "room_not_found"
            
    @pytest.mark.asyncio
    async def test_disconnect_handler_pregame(self, websocket_components):
        """Test disconnect handler for pre-game disconnect."""
        _, _, disconnect_handler = websocket_components
        
        connection_info = {
            "player_name": "TestPlayer",
            "room_id": "ROOM123",
            "websocket_id": "ws_123"
        }
        
        with patch('application.websocket.disconnect_handler.get_unit_of_work') as mock_get_uow:
            with patch('application.websocket.disconnect_handler.broadcast') as mock_broadcast:
                mock_uow = AsyncMock()
                mock_get_uow.return_value = mock_uow
                
                # Setup room without game
                mock_room = MagicMock()
                mock_room.id = "ROOM123"
                mock_room.game = None
                mock_room.host_player_id = "player1"
                
                mock_player = MagicMock()
                mock_player.id = "player1"
                mock_player.name = "TestPlayer"
                mock_room.players = [mock_player]
                
                mock_uow.rooms.get_by_id.return_value = mock_room
                
                await disconnect_handler.handle_player_disconnect(
                    connection_info,
                    "ROOM123"
                )
                
                # Check player_left broadcast
                mock_broadcast.assert_called()
                call_args = mock_broadcast.call_args_list
                assert any(args[0][1] == "player_left" for args in call_args)
                
    @pytest.mark.asyncio
    async def test_disconnect_handler_ingame(self, websocket_components):
        """Test disconnect handler for in-game disconnect."""
        _, _, disconnect_handler = websocket_components
        
        connection_info = {
            "player_name": "TestPlayer",
            "room_id": "ROOM123",
            "websocket_id": "ws_123"
        }
        
        with patch('application.websocket.disconnect_handler.get_unit_of_work') as mock_get_uow:
            with patch('application.websocket.disconnect_handler.broadcast') as mock_broadcast:
                with patch('application.websocket.disconnect_handler.get_bot_service') as mock_get_bot:
                    mock_uow = AsyncMock()
                    mock_get_uow.return_value = mock_uow
                    
                    # Setup room with active game
                    mock_room = MagicMock()
                    mock_room.id = "ROOM123"
                    mock_room.host_player_id = "player1"
                    mock_room.get_human_count.return_value = 1
                    
                    mock_game = MagicMock()
                    mock_game.is_started = True
                    mock_game.is_finished = False
                    mock_game.current_round = 3
                    mock_room.game = mock_game
                    
                    mock_player = MagicMock()
                    mock_player.id = "player1"
                    mock_player.name = "TestPlayer"
                    mock_player.is_bot = False
                    mock_player.is_connected = True
                    mock_room.players = [mock_player]
                    
                    mock_uow.rooms.get_by_id.return_value = mock_room
                    
                    mock_bot_service = MagicMock()
                    mock_get_bot.return_value = mock_bot_service
                    
                    await disconnect_handler.handle_player_disconnect(
                        connection_info,
                        "ROOM123"
                    )
                    
                    # Check bot activation
                    mock_bot_service.activate_bot_for_player.assert_called_once_with(
                        "player1", "ROOM123"
                    )
                    
                    # Check broadcast
                    mock_broadcast.assert_called()
                    call_args = mock_broadcast.call_args_list
                    assert any(args[0][1] == "player_replaced_by_bot" for args in call_args)