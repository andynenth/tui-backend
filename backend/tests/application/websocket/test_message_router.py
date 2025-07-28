"""
Unit tests for MessageRouter application component
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket

from application.websocket.message_router import MessageRouter


@pytest.fixture
def message_router():
    """Create a MessageRouter instance for testing."""
    return MessageRouter()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing."""
    websocket = AsyncMock(spec=WebSocket)
    websocket.send_json = AsyncMock()
    websocket._ws_id = "ws_123"
    return websocket


class TestMessageRouter:
    """Test MessageRouter application component."""
    
    @pytest.mark.asyncio
    async def test_route_message_missing_event(self, message_router, mock_websocket):
        """Test routing a message without event/action."""
        message = {"data": {}}
        room_id = "test_room"
        
        response = await message_router.route_message(
            mock_websocket,
            message,
            room_id
        )
        
        assert response is not None
        assert response["event"] == "error"
        assert "Missing event/action" in response["data"]["message"]
        assert response["data"]["type"] == "routing_error"
        
    @pytest.mark.asyncio
    async def test_route_message_unsupported_event(self, message_router, mock_websocket):
        """Test routing a message with unsupported event."""
        message = {"event": "unsupported_event", "data": {}}
        room_id = "test_room"
        
        response = await message_router.route_message(
            mock_websocket,
            message,
            room_id
        )
        
        assert response is not None
        assert response["event"] == "error"
        assert "Unsupported event" in response["data"]["message"]
        assert response["data"]["type"] == "unsupported_event"
        
    @pytest.mark.asyncio
    async def test_route_message_supported_event(self, message_router, mock_websocket):
        """Test routing a message with supported event."""
        message = {"event": "ping", "data": {}}
        room_id = "test_room"
        
        with patch.object(message_router, '_route_to_adapter') as mock_route:
            mock_route.return_value = {"event": "pong", "data": {}}
            
            response = await message_router.route_message(
                mock_websocket,
                message,
                room_id
            )
            
            assert response is not None
            assert response["event"] == "pong"
            mock_route.assert_called_once_with(
                mock_websocket,
                message,
                room_id
            )
            
    @pytest.mark.asyncio
    async def test_route_message_with_action(self, message_router, mock_websocket):
        """Test routing a message using 'action' field."""
        message = {"action": "ping", "data": {}}
        room_id = "test_room"
        
        with patch.object(message_router, '_route_to_adapter') as mock_route:
            mock_route.return_value = {"event": "pong", "data": {}}
            
            response = await message_router.route_message(
                mock_websocket,
                message,
                room_id
            )
            
            assert response is not None
            assert response["event"] == "pong"
            
    @pytest.mark.asyncio
    async def test_route_message_exception(self, message_router, mock_websocket):
        """Test routing when an exception occurs."""
        message = {"event": "ping", "data": {}}
        room_id = "test_room"
        
        with patch.object(message_router, '_route_to_adapter') as mock_route:
            mock_route.side_effect = Exception("Test error")
            
            response = await message_router.route_message(
                mock_websocket,
                message,
                room_id
            )
            
            assert response is not None
            assert response["event"] == "error"
            assert "Failed to process ping" in response["data"]["message"]
            assert response["data"]["type"] == "routing_error"
            assert "Test error" in response["data"]["details"]
            
    @pytest.mark.asyncio
    async def test_route_to_adapter_lobby(self, message_router, mock_websocket):
        """Test routing to adapter for lobby room."""
        message = {"event": "get_rooms", "data": {}}
        room_id = "lobby"
        
        with patch.object(message_router.adapter_wrapper, 'try_handle_with_adapter') as mock_adapter:
            mock_adapter.return_value = {"event": "room_list", "data": {"rooms": []}}
            
            response = await message_router._route_to_adapter(
                mock_websocket,
                message,
                room_id
            )
            
            assert response is not None
            assert response["event"] == "room_list"
            
            # Should not fetch room state for lobby
            mock_adapter.assert_called_once_with(
                mock_websocket,
                message,
                room_id,
                None  # No room state for lobby
            )
            
    @pytest.mark.asyncio
    async def test_route_to_adapter_with_room(self, message_router, mock_websocket):
        """Test routing to adapter for regular room."""
        message = {"event": "start_game", "data": {}}
        room_id = "ROOM123"
        
        with patch.object(message_router, '_get_room_state') as mock_get_state:
            with patch.object(message_router.adapter_wrapper, 'try_handle_with_adapter') as mock_adapter:
                mock_room_state = {"room_id": "ROOM123", "players": []}
                mock_get_state.return_value = mock_room_state
                mock_adapter.return_value = {"event": "game_started", "data": {}}
                
                response = await message_router._route_to_adapter(
                    mock_websocket,
                    message,
                    room_id
                )
                
                assert response is not None
                assert response["event"] == "game_started"
                
                mock_get_state.assert_called_once_with(room_id)
                mock_adapter.assert_called_once_with(
                    mock_websocket,
                    message,
                    room_id,
                    mock_room_state
                )
                
    @pytest.mark.asyncio
    async def test_get_room_state(self, message_router, mock_websocket):
        """Test getting room state."""
        room_id = "ROOM123"
        
        with patch('application.websocket.message_router.get_unit_of_work') as mock_get_uow:
            mock_uow = AsyncMock()
            mock_get_uow.return_value = mock_uow
            
            mock_room = MagicMock()
            mock_room.id = room_id
            mock_room.host_player_id = "player1"
            mock_room.max_players = 4
            mock_room.status.value = "waiting"
            mock_room.current_round = 1
            
            mock_player = MagicMock()
            mock_player.id = "player1"
            mock_player.name = "TestPlayer"
            mock_player.is_bot = False
            mock_player.seat_position = 0
            mock_room.players = [mock_player]
            
            mock_uow.rooms.get_by_id.return_value = mock_room
            
            room_state = await message_router._get_room_state(room_id)
            
            assert room_state is not None
            assert room_state["room_id"] == room_id
            assert room_state["host"] == "player1"
            assert len(room_state["players"]) == 1
            assert room_state["players"][0]["name"] == "TestPlayer"
            
    @pytest.mark.asyncio
    async def test_check_message_queue_no_connection(self, message_router, mock_websocket):
        """Test checking message queue when no connection info."""
        mock_websocket._ws_id = None
        room_id = "test_room"
        
        await message_router._check_message_queue(mock_websocket, room_id)
        
        # Should return early without errors
        
    @pytest.mark.asyncio
    async def test_check_message_queue_with_messages(self, message_router, mock_websocket):
        """Test checking message queue with queued messages."""
        room_id = "test_room"
        
        with patch('application.websocket.message_router.connection_manager') as mock_cm:
            with patch('application.websocket.message_router.message_queue_manager') as mock_queue:
                mock_connection = MagicMock()
                mock_connection.player_name = "TestPlayer"
                mock_cm.get_connection_by_websocket_id.return_value = mock_connection
                
                queued_messages = [
                    {"event": "test1", "data": {}},
                    {"event": "test2", "data": {}}
                ]
                mock_queue.get_queued_messages.return_value = queued_messages
                
                await message_router._check_message_queue(mock_websocket, room_id)
                
                # Should send all queued messages
                assert mock_websocket.send_json.call_count == 2
                
    @pytest.mark.asyncio
    async def test_handle_room_validation_lobby(self, message_router, mock_websocket):
        """Test room validation for lobby."""
        room_id = "lobby"
        
        valid = await message_router.handle_room_validation(mock_websocket, room_id)
        
        assert valid is True
        
    @pytest.mark.asyncio
    async def test_handle_room_validation_exists(self, message_router, mock_websocket):
        """Test room validation when room exists."""
        room_id = "ROOM123"
        
        with patch('application.websocket.message_router.get_unit_of_work') as mock_get_uow:
            mock_uow = AsyncMock()
            mock_get_uow.return_value = mock_uow
            
            mock_room = MagicMock()
            mock_uow.rooms.get_by_id.return_value = mock_room
            
            valid = await message_router.handle_room_validation(mock_websocket, room_id)
            
            assert valid is True
            mock_websocket.send_json.assert_not_called()
            
    @pytest.mark.asyncio
    async def test_handle_room_validation_not_exists(self, message_router, mock_websocket):
        """Test room validation when room doesn't exist."""
        room_id = "ROOM123"
        
        with patch('application.websocket.message_router.get_unit_of_work') as mock_get_uow:
            mock_uow = AsyncMock()
            mock_get_uow.return_value = mock_uow
            
            mock_uow.rooms.get_by_id.return_value = None
            
            valid = await message_router.handle_room_validation(mock_websocket, room_id)
            
            assert valid is False
            mock_websocket.send_json.assert_called_once()
            
            # Check room_not_found message sent
            message = mock_websocket.send_json.call_args[0][0]
            assert message["event"] == "room_not_found"
            assert message["data"]["room_id"] == room_id
            
    def test_get_stats(self, message_router):
        """Test getting router statistics."""
        # Simulate some activity
        message_router._message_count = 100
        message_router._error_count = 5
        
        stats = message_router.get_stats()
        
        assert stats["messages_routed"] == 100
        assert stats["errors"] == 5
        assert stats["error_rate"] == 0.05