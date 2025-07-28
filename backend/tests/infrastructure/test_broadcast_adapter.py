"""
Unit tests for the broadcast adapter that bridges legacy and clean architecture.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from fastapi import WebSocket
from starlette.websockets import WebSocketState

from infrastructure.websocket.broadcast_adapter import (
    broadcast,
    register,
    unregister,
    get_connection_manager,
    get_room_stats,
    ensure_lobby_ready
)


@pytest.mark.asyncio
async def test_broadcast_adapter_broadcast():
    """Test that broadcast function works correctly."""
    # Create mock for broadcast_to_room
    connection_manager = get_connection_manager()
    connection_manager.broadcast_to_room = AsyncMock(return_value=3)
    
    # Test broadcast
    await broadcast("test_room", "test_event", {"test": "data"})
    
    # Verify call
    connection_manager.broadcast_to_room.assert_called_once_with(
        "test_room",
        {
            "event": "test_event",
            "data": {"test": "data"}
        }
    )


@pytest.mark.asyncio
async def test_broadcast_adapter_register():
    """Test WebSocket registration."""
    # Create mock WebSocket
    mock_websocket = Mock(spec=WebSocket)
    mock_websocket.client_state = WebSocketState.CONNECTED
    
    # Mock connection manager methods
    connection_manager = get_connection_manager()
    connection_manager.register = AsyncMock()
    connection_manager.join_room = AsyncMock()
    
    # Test registration
    result = await register("test_room", mock_websocket)
    
    # Verify WebSocket is returned
    assert result == mock_websocket
    
    # Verify connection manager was called
    connection_manager.register.assert_called_once()
    connection_manager.join_room.assert_called_once()
    
    # Verify room_id is correct
    call_args = connection_manager.join_room.call_args[0]
    assert call_args[1] == "test_room"


def test_broadcast_adapter_unregister():
    """Test WebSocket unregistration."""
    # Create mock WebSocket
    mock_websocket = Mock(spec=WebSocket)
    
    # First register it to create mapping
    from infrastructure.websocket.broadcast_adapter import _websocket_to_connection_id
    _websocket_to_connection_id[mock_websocket] = "test_connection_1"
    
    # Test unregistration
    unregister("test_room", mock_websocket)
    
    # Since unregister creates an async task, we can't easily verify
    # But we can check that no exception was raised
    assert True  # If we got here, no exception


def test_get_room_stats():
    """Test room statistics retrieval."""
    # Test with no room specified
    stats = get_room_stats()
    assert isinstance(stats, dict)
    assert "total_active_connections" in stats
    assert "rooms" in stats
    
    # Test with specific room
    room_stats = get_room_stats("test_room")
    assert isinstance(room_stats, dict)
    assert "active_connections" in room_stats
    assert "room_id" in room_stats
    assert room_stats["room_id"] == "test_room"


def test_ensure_lobby_ready():
    """Test ensure_lobby_ready function."""
    # This should not raise any exception
    ensure_lobby_ready()
    
    # Verify no exception was raised
    assert True


@pytest.mark.asyncio
async def test_broadcast_error_handling():
    """Test broadcast error handling."""
    # Mock connection manager to raise exception
    connection_manager = get_connection_manager()
    connection_manager.broadcast_to_room = AsyncMock(
        side_effect=Exception("Test error")
    )
    
    # Test that broadcast raises the exception
    with pytest.raises(Exception) as exc_info:
        await broadcast("test_room", "test_event", {"test": "data"})
    
    assert str(exc_info.value) == "Test error"


@pytest.mark.asyncio
async def test_multiple_websocket_registration():
    """Test registering multiple WebSockets."""
    # Create mock WebSockets
    ws1 = Mock(spec=WebSocket)
    ws2 = Mock(spec=WebSocket)
    ws3 = Mock(spec=WebSocket)
    
    # Mock connection manager
    connection_manager = get_connection_manager()
    connection_manager.register = AsyncMock()
    connection_manager.join_room = AsyncMock()
    
    # Register multiple WebSockets
    await register("room1", ws1)
    await register("room1", ws2)
    await register("room2", ws3)
    
    # Verify all were registered
    assert connection_manager.register.call_count == 3
    assert connection_manager.join_room.call_count == 3


def test_connection_manager_singleton():
    """Test that connection manager is a singleton."""
    cm1 = get_connection_manager()
    cm2 = get_connection_manager()
    
    # Should be the same instance
    assert cm1 is cm2


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_broadcast_adapter_broadcast())
    asyncio.run(test_broadcast_adapter_register())
    test_broadcast_adapter_unregister()
    test_get_room_stats()
    test_ensure_lobby_ready()
    asyncio.run(test_broadcast_error_handling())
    asyncio.run(test_multiple_websocket_registration())
    test_connection_manager_singleton()
    
    print("✅ All broadcast adapter tests passed!")