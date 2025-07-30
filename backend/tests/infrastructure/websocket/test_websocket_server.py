"""
Unit tests for WebSocketServer infrastructure component
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import WebSocket

from infrastructure.websocket.websocket_server import WebSocketServer


@pytest.fixture
def websocket_server():
    """Create a WebSocketServer instance for testing."""
    return WebSocketServer()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing."""
    websocket = AsyncMock(spec=WebSocket)
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.receive_json = AsyncMock()
    return websocket


class TestWebSocketServer:
    """Test WebSocketServer infrastructure component."""

    @pytest.mark.asyncio
    async def test_accept_connection(self, websocket_server, mock_websocket):
        """Test accepting a WebSocket connection."""
        await websocket_server.accept_connection(mock_websocket)
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_connection(self, websocket_server, mock_websocket):
        """Test handling WebSocket connection lifecycle."""
        room_id = "test_room"

        with patch(
            "infrastructure.websocket.websocket_server.register"
        ) as mock_register:
            mock_register.return_value = "conn_123"

            connection_id = await websocket_server.handle_connection(
                mock_websocket, room_id
            )

            # Check connection ID generated
            assert hasattr(mock_websocket, "_ws_id")
            assert mock_websocket._connection_id == "conn_123"
            assert connection_id == "conn_123"

            # Check register called
            mock_register.assert_called_once_with(room_id, mock_websocket)

    @pytest.mark.asyncio
    async def test_receive_valid_message(self, websocket_server, mock_websocket):
        """Test receiving a valid message."""
        valid_message = {"event": "ping", "data": {}}
        mock_websocket.receive_json.return_value = valid_message

        with patch(
            "infrastructure.websocket.websocket_server.validate_websocket_message"
        ) as mock_validate:
            mock_validate.return_value = (True, None, valid_message)

            message = await websocket_server.receive_message(mock_websocket)

            assert message == valid_message
            mock_validate.assert_called_once_with(valid_message)

    @pytest.mark.asyncio
    async def test_receive_invalid_message(self, websocket_server, mock_websocket):
        """Test receiving an invalid message."""
        invalid_message = {"invalid": "format"}
        mock_websocket.receive_json.return_value = invalid_message

        with patch(
            "infrastructure.websocket.websocket_server.validate_websocket_message"
        ) as mock_validate:
            mock_validate.return_value = (False, "Missing event field", None)

            message = await websocket_server.receive_message(mock_websocket)

            assert message is None
            mock_websocket.send_json.assert_called_once()

            # Check error message sent
            error_call = mock_websocket.send_json.call_args[0][0]
            assert error_call["event"] == "error"
            assert "Missing event field" in error_call["data"]["message"]

    @pytest.mark.asyncio
    async def test_send_message(self, websocket_server, mock_websocket):
        """Test sending a message."""
        message = {"event": "pong", "data": {}}

        await websocket_server.send_message(mock_websocket, message)

        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_error(self, websocket_server, mock_websocket):
        """Test sending an error message."""
        await websocket_server.send_error(mock_websocket, "Test error", "test_error")

        mock_websocket.send_json.assert_called_once()
        error_message = mock_websocket.send_json.call_args[0][0]

        assert error_message["event"] == "error"
        assert error_message["data"]["message"] == "Test error"
        assert error_message["data"]["type"] == "test_error"

    @pytest.mark.asyncio
    async def test_check_rate_limit_disabled(self, websocket_server, mock_websocket):
        """Test rate limiting when disabled."""
        websocket_server.rate_limit_config = {"enabled": False}

        is_limited = await websocket_server.check_rate_limit(
            mock_websocket, "test_event", "ws_123"
        )

        assert is_limited is False

    @pytest.mark.asyncio
    async def test_check_rate_limit_not_limited(self, websocket_server, mock_websocket):
        """Test rate limiting when not limited."""
        websocket_server.rate_limit_config = {"enabled": True}

        with patch(
            "infrastructure.websocket.websocket_server.check_websocket_rate_limit"
        ) as mock_check:
            mock_check.return_value = False

            is_limited = await websocket_server.check_rate_limit(
                mock_websocket, "test_event", "ws_123"
            )

            assert is_limited is False
            mock_check.assert_called_once_with("test_event", "ws_123")

    @pytest.mark.asyncio
    async def test_check_rate_limit_limited(self, websocket_server, mock_websocket):
        """Test rate limiting when limited."""
        websocket_server.rate_limit_config = {"enabled": True}

        with patch(
            "infrastructure.websocket.websocket_server.check_websocket_rate_limit"
        ) as mock_check:
            with patch(
                "infrastructure.websocket.websocket_server.send_rate_limit_error"
            ) as mock_send_error:
                mock_check.return_value = True

                is_limited = await websocket_server.check_rate_limit(
                    mock_websocket, "test_event", "ws_123"
                )

                assert is_limited is True
                mock_send_error.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_handle_disconnect(self, websocket_server, mock_websocket):
        """Test handling disconnection."""
        room_id = "test_room"
        websocket_id = "ws_123"
        mock_websocket._ws_id = websocket_id
        mock_websocket._connection_id = "conn_123"

        with patch(
            "infrastructure.websocket.websocket_server.connection_manager"
        ) as mock_cm:
            with patch(
                "infrastructure.websocket.websocket_server.unregister"
            ) as mock_unregister:
                mock_connection = MagicMock()
                mock_connection.player_name = "TestPlayer"
                mock_connection.room_id = room_id
                mock_cm.get_connection_by_websocket_id.return_value = mock_connection

                connection_id = await websocket_server.handle_disconnect(
                    mock_websocket, room_id, websocket_id
                )

                assert connection_id == "conn_123"
                mock_unregister.assert_called_once_with("conn_123")

    @pytest.mark.asyncio
    async def test_handle_disconnect_no_connection_id(
        self, websocket_server, mock_websocket
    ):
        """Test handling disconnection when no connection ID found."""
        room_id = "test_room"

        with patch(
            "infrastructure.websocket.websocket_server.get_connection_id_for_websocket"
        ) as mock_get_id:
            mock_get_id.return_value = None

            connection_id = await websocket_server.handle_disconnect(
                mock_websocket, room_id, None
            )

            assert connection_id is None
