"""
Contract Implementations for WebSocket Infrastructure

Implements the infrastructure contracts using existing WebSocket components.
"""

from typing import Dict, Any, Optional, Callable, Awaitable, Set
import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect

from infrastructure.interfaces.websocket_infrastructure import (
    IWebSocketConnection,
    IConnectionManager,
    IBroadcaster,
    IWebSocketInfrastructure,
    ConnectionInfo,
)
from infrastructure.websocket.connection_singleton import (
    broadcast as legacy_broadcast,
    register as legacy_register,
    unregister as legacy_unregister,
    get_connection_id_for_websocket,
)
from api.websocket.connection_manager import connection_manager
from api.websocket.message_queue import message_queue_manager

logger = logging.getLogger(__name__)


class FastAPIWebSocketConnection(IWebSocketConnection):
    """Adapter for FastAPI WebSocket to IWebSocketConnection"""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self._connected = True

    async def send_json(self, data: Dict[str, Any]) -> None:
        """Send JSON data through the WebSocket"""
        if self._connected:
            try:
                await self.websocket.send_json(data)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                self._connected = False

    async def receive_json(self) -> Dict[str, Any]:
        """Receive JSON data from the WebSocket"""
        return await self.websocket.receive_json()

    async def accept(self) -> None:
        """Accept the WebSocket connection"""
        await self.websocket.accept()

    async def close(self, code: int = 1000, reason: str = "") -> None:
        """Close the WebSocket connection"""
        self._connected = False
        try:
            await self.websocket.close(code, reason)
        except Exception:
            pass  # Connection might already be closed

    def is_connected(self) -> bool:
        """Check if the WebSocket is still connected"""
        return self._connected


class WebSocketConnectionManager(IConnectionManager):
    """Implementation of IConnectionManager using existing infrastructure"""

    def __init__(self):
        self._connections: Dict[str, IWebSocketConnection] = {}
        self._connection_info: Dict[str, ConnectionInfo] = {}
        self._room_connections: Dict[str, Set[str]] = {}

    async def register_connection(
        self, connection_id: str, websocket: IWebSocketConnection, room_id: str
    ) -> None:
        """Register a new WebSocket connection"""
        self._connections[connection_id] = websocket
        self._connection_info[connection_id] = ConnectionInfo(
            connection_id=connection_id,
            room_id=room_id,
            connected_at=asyncio.get_event_loop().time(),
            last_activity=asyncio.get_event_loop().time(),
        )

        if room_id not in self._room_connections:
            self._room_connections[room_id] = set()
        self._room_connections[room_id].add(connection_id)

        logger.info(f"Registered connection {connection_id} in room {room_id}")

    async def unregister_connection(self, connection_id: str) -> None:
        """Unregister a WebSocket connection"""
        if connection_id in self._connections:
            # Get room ID before removing
            info = self._connection_info.get(connection_id)
            if info and info.room_id in self._room_connections:
                self._room_connections[info.room_id].discard(connection_id)

                # Clean up empty rooms
                if not self._room_connections[info.room_id]:
                    del self._room_connections[info.room_id]

            # Remove connection
            del self._connections[connection_id]
            if connection_id in self._connection_info:
                del self._connection_info[connection_id]

            logger.info(f"Unregistered connection {connection_id}")

    def get_connection(self, connection_id: str) -> Optional[IWebSocketConnection]:
        """Get a WebSocket connection by ID"""
        return self._connections.get(connection_id)

    def get_connections_in_room(self, room_id: str) -> Dict[str, IWebSocketConnection]:
        """Get all connections in a room"""
        result = {}
        if room_id in self._room_connections:
            for conn_id in self._room_connections[room_id]:
                if conn_id in self._connections:
                    result[conn_id] = self._connections[conn_id]
        return result

    def get_connection_info(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Get information about a connection"""
        return self._connection_info.get(connection_id)


class WebSocketBroadcaster(IBroadcaster):
    """Implementation of IBroadcaster"""

    def __init__(self, connection_manager: IConnectionManager):
        self.connection_manager = connection_manager

    async def broadcast_to_room(
        self,
        room_id: str,
        message: Dict[str, Any],
        exclude_connections: Optional[set[str]] = None,
    ) -> int:
        """Broadcast a message to all connections in a room"""
        connections = self.connection_manager.get_connections_in_room(room_id)
        count = 0

        tasks = []
        for conn_id, websocket in connections.items():
            if exclude_connections and conn_id in exclude_connections:
                continue

            tasks.append(self._send_safe(websocket, message))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        count = sum(1 for r in results if r is True)

        logger.debug(
            f"Broadcast to room {room_id}: {count}/{len(connections)} connections"
        )
        return count

    async def send_to_connection(
        self, connection_id: str, message: Dict[str, Any]
    ) -> bool:
        """Send a message to a specific connection"""
        websocket = self.connection_manager.get_connection(connection_id)
        if websocket:
            return await self._send_safe(websocket, message)
        return False

    async def broadcast_to_connections(
        self, connection_ids: set[str], message: Dict[str, Any]
    ) -> int:
        """Broadcast a message to specific connections"""
        count = 0
        tasks = []

        for conn_id in connection_ids:
            websocket = self.connection_manager.get_connection(conn_id)
            if websocket:
                tasks.append(self._send_safe(websocket, message))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        count = sum(1 for r in results if r is True)

        return count

    async def _send_safe(
        self, websocket: IWebSocketConnection, message: Dict[str, Any]
    ) -> bool:
        """Safely send a message to a WebSocket"""
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False


class WebSocketInfrastructure(IWebSocketInfrastructure):
    """Main WebSocket infrastructure implementation"""

    def __init__(self):
        self.connection_manager = WebSocketConnectionManager()
        self.broadcaster = WebSocketBroadcaster(self.connection_manager)

    async def handle_connection(
        self,
        websocket: Any,
        room_id: str,
        message_handler: Callable[
            [Dict[str, Any], str], Awaitable[Optional[Dict[str, Any]]]
        ],
    ) -> None:
        """Handle a WebSocket connection lifecycle"""
        # Create connection wrapper
        ws_connection = FastAPIWebSocketConnection(websocket)

        # Generate connection ID
        import uuid

        connection_id = str(uuid.uuid4())

        # Store connection ID on websocket for compatibility
        websocket._connection_id = connection_id

        # Accept connection
        await ws_connection.accept()

        # Register connection
        await self.connection_manager.register_connection(
            connection_id, ws_connection, room_id
        )

        try:
            # Main message loop
            while ws_connection.is_connected():
                try:
                    # Receive message
                    message = await ws_connection.receive_json()

                    # Handle message
                    response = await message_handler(message, connection_id)

                    # Send response if any
                    if response:
                        await ws_connection.send_json(response)

                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    error_response = {
                        "event": "error",
                        "data": {
                            "message": "Internal server error",
                            "type": "server_error",
                        },
                    }
                    await ws_connection.send_json(error_response)

        finally:
            # Unregister connection
            await self.connection_manager.unregister_connection(connection_id)

    def get_connection_manager(self) -> IConnectionManager:
        """Get the connection manager"""
        return self.connection_manager

    def get_broadcaster(self) -> IBroadcaster:
        """Get the broadcaster"""
        return self.broadcaster

    async def shutdown(self) -> None:
        """Shutdown the infrastructure gracefully"""
        # Close all connections
        for conn_id in list(self.connection_manager._connections.keys()):
            websocket = self.connection_manager.get_connection(conn_id)
            if websocket:
                await websocket.close(1001, "Server shutting down")

        logger.info("WebSocket infrastructure shut down")


# Legacy bridge functions to maintain compatibility
async def bridge_to_legacy_broadcast(
    room_id: str, event: str, data: Dict[str, Any]
) -> None:
    """Bridge function to use legacy broadcast"""
    await legacy_broadcast(room_id, event, data)
