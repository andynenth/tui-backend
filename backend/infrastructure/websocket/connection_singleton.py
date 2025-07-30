"""
Singleton WebSocket connection management for clean architecture.

This module provides a singleton ConnectionManager instance and helper functions
for managing WebSocket connections across the application.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import WebSocket

from .connection_manager import ConnectionManager, InMemoryConnectionRegistry

logger = logging.getLogger(__name__)

# Create singleton instances
_connection_registry = InMemoryConnectionRegistry()
_connection_manager = ConnectionManager(registry=_connection_registry)

# Track WebSocket to connection_id mapping for compatibility
_websocket_to_connection_id: Dict[WebSocket, str] = {}
_connection_id_counter = 0


def get_connection_manager() -> ConnectionManager:
    """
    Get the singleton connection manager instance.

    Returns:
        The global ConnectionManager instance
    """
    return _connection_manager


async def broadcast(room_id: str, event: str, data: Dict[str, Any]) -> None:
    """
    Broadcast a message to all connections in a room.

    Args:
        room_id: The room to broadcast to
        event: The event type
        data: The event data
    """
    message = {"event": event, "data": data}

    try:
        sent_count = await _connection_manager.broadcast_to_room(room_id, message)
        logger.debug(
            f"Broadcast to room {room_id}: {event} (sent to {sent_count} connections)"
        )
    except Exception as e:
        logger.error(f"Failed to broadcast to room {room_id}: {e}")
        raise


async def send_to_player(player_id: str, message: Dict[str, Any]) -> None:
    """
    Send a message to a specific player.

    Args:
        player_id: The player to send to
        message: The message dict (should include 'event' and 'data' keys)
    """
    try:
        sent_count = await _connection_manager.broadcast_to_player(player_id, message)
        logger.debug(
            f"Sent message to player {player_id}: {message.get('event')} (sent to {sent_count} connections)"
        )
    except Exception as e:
        logger.error(f"Failed to send message to player {player_id}: {e}")
        raise


async def register(room_id: str, websocket: WebSocket) -> str:
    """
    Register a WebSocket connection and join a room.

    Args:
        room_id: The room to join
        websocket: The WebSocket connection

    Returns:
        The connection ID
    """
    global _connection_id_counter

    # Start connection manager if not already running
    if not _connection_manager._running:
        await _connection_manager.start()

    # Generate a connection ID
    _connection_id_counter += 1
    connection_id = f"conn_{_connection_id_counter}"

    # Store the mapping
    _websocket_to_connection_id[websocket] = connection_id

    # Connect with connection manager
    await _connection_manager.connect(websocket, connection_id)

    # Join the room
    await _connection_manager.join_room(connection_id, room_id)

    logger.info(f"WebSocket registered: {connection_id} -> room {room_id}")
    return connection_id


async def unregister(connection_id: str) -> None:
    """
    Unregister a WebSocket connection.

    Args:
        connection_id: The connection to unregister
    """
    try:
        await _connection_manager.disconnect(connection_id)

        # Remove from mapping
        websocket_to_remove = None
        for ws, cid in _websocket_to_connection_id.items():
            if cid == connection_id:
                websocket_to_remove = ws
                break

        if websocket_to_remove:
            del _websocket_to_connection_id[websocket_to_remove]

        logger.info(f"WebSocket unregistered: {connection_id}")
    except Exception as e:
        logger.error(f"Failed to unregister connection {connection_id}: {e}")


def get_connection_id_for_websocket(websocket: WebSocket) -> Optional[str]:
    """
    Get the connection ID for a WebSocket.

    Args:
        websocket: The WebSocket instance

    Returns:
        The connection ID if found
    """
    return _websocket_to_connection_id.get(websocket)


def get_room_stats(room_id: Optional[str] = None) -> dict:
    """
    Get statistics for rooms and connections.

    Args:
        room_id: Optional room ID to get stats for

    Returns:
        Statistics dictionary
    """
    # For now, return basic stats based on tracked connections
    # This avoids async/sync issues
    if room_id:
        # Count connections in the specified room
        room_connections = 0
        if hasattr(_connection_registry, "_room_connections"):
            room_connections = len(
                _connection_registry._room_connections.get(room_id, set())
            )

        return {"active_connections": room_connections, "room_id": room_id}
    else:
        # Return overall stats
        all_connections = len(_websocket_to_connection_id)
        return {
            "total_active_connections": all_connections,
            "rooms": ["lobby"],  # Will be enhanced when we track rooms properly
        }


# Note: The connection manager will be started when the first connection is made
# This avoids issues with asyncio event loops during import
