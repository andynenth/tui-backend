"""
Broadcasting adapter that provides legacy-compatible interface using clean architecture.

This adapter allows gradual migration from socket_manager to clean architecture
by providing the same broadcast interface while using the new infrastructure.
"""

import logging
from typing import Dict, Any, Optional, Set
from fastapi import WebSocket
import asyncio

from infrastructure.websocket import ConnectionManager, InMemoryConnectionRegistry

logger = logging.getLogger(__name__)

# Create singleton instances
_connection_registry = InMemoryConnectionRegistry()
_connection_manager = ConnectionManager(registry=_connection_registry)

# Track WebSocket to connection_id mapping for compatibility
_websocket_to_connection_id: Dict[WebSocket, str] = {}
_connection_id_counter = 0


async def broadcast(room_id: str, event: str, data: Dict[str, Any]) -> None:
    """
    Legacy-compatible broadcast function using clean architecture.
    
    Args:
        room_id: The room to broadcast to
        event: The event type
        data: The event data
    """
    message = {
        "event": event,
        "data": data
    }
    
    try:
        sent_count = await _connection_manager.broadcast_to_room(room_id, message)
        logger.debug(f"Broadcast to room {room_id}: {event} (sent to {sent_count} connections)")
    except Exception as e:
        logger.error(f"Failed to broadcast to room {room_id}: {e}")
        raise


async def register(room_id: str, websocket: WebSocket) -> WebSocket:
    """
    Legacy-compatible register function.
    
    Args:
        room_id: The room to register to
        websocket: The WebSocket connection
        
    Returns:
        The registered WebSocket connection
    """
    global _connection_id_counter
    
    # Generate a connection ID
    _connection_id_counter += 1
    connection_id = f"conn_{_connection_id_counter}"
    
    # Store the mapping
    _websocket_to_connection_id[websocket] = connection_id
    
    # Register with connection manager
    await _connection_manager.register(connection_id, websocket)
    
    # Join the room
    await _connection_manager.join_room(connection_id, room_id)
    
    logger.info(f"WebSocket registered: {connection_id} -> room {room_id}")
    return websocket


def unregister(room_id: str, websocket: WebSocket) -> None:
    """
    Legacy-compatible unregister function.
    
    Args:
        room_id: The room to unregister from
        websocket: The WebSocket connection
    """
    connection_id = _websocket_to_connection_id.get(websocket)
    if not connection_id:
        logger.warning(f"WebSocket not found in mapping for room {room_id}")
        return
    
    # Unregister is synchronous in legacy, but our clean architecture is async
    # Create a task to handle the async unregistration
    asyncio.create_task(_async_unregister(connection_id, websocket))


async def _async_unregister(connection_id: str, websocket: WebSocket) -> None:
    """Handle async unregistration."""
    try:
        await _connection_manager.unregister(connection_id)
        _websocket_to_connection_id.pop(websocket, None)
        logger.info(f"WebSocket unregistered: {connection_id}")
    except Exception as e:
        logger.error(f"Failed to unregister connection {connection_id}: {e}")


def get_connection_manager() -> ConnectionManager:
    """
    Get the singleton connection manager instance.
    
    Returns:
        The global ConnectionManager instance
    """
    return _connection_manager


def get_room_stats(room_id: Optional[str] = None) -> dict:
    """
    Legacy-compatible get_room_stats function.
    
    Args:
        room_id: Optional room ID to get stats for
        
    Returns:
        Statistics dict
    """
    # For now, return basic stats
    # This can be enhanced to match legacy format if needed
    if room_id:
        connections = asyncio.run(_connection_registry.get_connections_by_room(room_id))
        return {
            "active_connections": len(connections),
            "room_id": room_id
        }
    else:
        # Return overall stats
        all_connections = len(_websocket_to_connection_id)
        return {
            "total_active_connections": all_connections,
            "rooms": ["lobby"]  # Will be enhanced when we track rooms properly
        }


def ensure_lobby_ready() -> None:
    """
    Legacy-compatible ensure_lobby_ready function.
    
    In the new architecture, the lobby doesn't need special initialization,
    but we keep this function for compatibility.
    """
    logger.debug("Lobby is always ready in clean architecture")
    pass


# Export module-level functions for drop-in compatibility
__all__ = [
    'broadcast',
    'register', 
    'unregister',
    'get_connection_manager',
    'get_room_stats',
    'ensure_lobby_ready'
]