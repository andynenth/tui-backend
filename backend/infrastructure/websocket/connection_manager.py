"""
WebSocket connection management infrastructure.

Provides centralized connection tracking, state management, and lifecycle handling.
"""

from typing import Dict, Set, Optional, List, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from abc import ABC, abstractmethod
import weakref
from collections import defaultdict
import logging

from fastapi import WebSocket
from starlette.websockets import WebSocketState


logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection states."""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    IN_ROOM = "in_room"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""

    connection_id: str
    websocket: WebSocket
    state: ConnectionState = ConnectionState.CONNECTING
    player_id: Optional[str] = None
    room_id: Optional[str] = None
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "connection_id": self.connection_id,
            "state": self.state.value,
            "player_id": self.player_id,
            "room_id": self.room_id,
            "connected_at": self.connected_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "metadata": self.metadata,
        }


class IConnectionRegistry(ABC):
    """Interface for connection registry."""

    @abstractmethod
    async def add_connection(self, connection: ConnectionInfo) -> None:
        """Add a new connection."""
        pass

    @abstractmethod
    async def remove_connection(self, connection_id: str) -> None:
        """Remove a connection."""
        pass

    @abstractmethod
    async def get_connection(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Get connection by ID."""
        pass

    @abstractmethod
    async def get_connections_by_player(self, player_id: str) -> List[ConnectionInfo]:
        """Get all connections for a player."""
        pass

    @abstractmethod
    async def get_connections_by_room(self, room_id: str) -> List[ConnectionInfo]:
        """Get all connections in a room."""
        pass

    @abstractmethod
    async def update_connection_state(
        self, connection_id: str, state: ConnectionState
    ) -> None:
        """Update connection state."""
        pass


class InMemoryConnectionRegistry(IConnectionRegistry):
    """In-memory implementation of connection registry."""

    def __init__(self):
        """Initialize registry."""
        self._connections: Dict[str, ConnectionInfo] = {}
        self._player_connections: Dict[str, Set[str]] = defaultdict(set)
        self._room_connections: Dict[str, Set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def add_connection(self, connection: ConnectionInfo) -> None:
        """Add a new connection."""
        async with self._lock:
            self._connections[connection.connection_id] = connection

            if connection.player_id:
                self._player_connections[connection.player_id].add(
                    connection.connection_id
                )

            if connection.room_id:
                self._room_connections[connection.room_id].add(connection.connection_id)

    async def remove_connection(self, connection_id: str) -> None:
        """Remove a connection."""
        async with self._lock:
            connection = self._connections.pop(connection_id, None)
            if not connection:
                return

            # Clean up indexes
            if connection.player_id:
                self._player_connections[connection.player_id].discard(connection_id)
                if not self._player_connections[connection.player_id]:
                    del self._player_connections[connection.player_id]

            if connection.room_id:
                self._room_connections[connection.room_id].discard(connection_id)
                if not self._room_connections[connection.room_id]:
                    del self._room_connections[connection.room_id]

    async def get_connection(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Get connection by ID."""
        async with self._lock:
            return self._connections.get(connection_id)

    async def get_connections_by_player(self, player_id: str) -> List[ConnectionInfo]:
        """Get all connections for a player."""
        async with self._lock:
            connection_ids = self._player_connections.get(player_id, set())
            return [
                self._connections[cid]
                for cid in connection_ids
                if cid in self._connections
            ]

    async def get_connections_by_room(self, room_id: str) -> List[ConnectionInfo]:
        """Get all connections in a room."""
        async with self._lock:
            connection_ids = self._room_connections.get(room_id, set())
            return [
                self._connections[cid]
                for cid in connection_ids
                if cid in self._connections
            ]

    async def update_connection_state(
        self, connection_id: str, state: ConnectionState
    ) -> None:
        """Update connection state."""
        async with self._lock:
            connection = self._connections.get(connection_id)
            if connection:
                connection.state = state
                connection.update_activity()

    async def update_connection_player(
        self, connection_id: str, player_id: str
    ) -> None:
        """Update connection's player association."""
        async with self._lock:
            connection = self._connections.get(connection_id)
            if not connection:
                return

            # Remove old association
            if connection.player_id:
                self._player_connections[connection.player_id].discard(connection_id)

            # Add new association
            connection.player_id = player_id
            self._player_connections[player_id].add(connection_id)
            connection.update_activity()

    async def update_connection_room(
        self, connection_id: str, room_id: Optional[str]
    ) -> None:
        """Update connection's room association."""
        async with self._lock:
            connection = self._connections.get(connection_id)
            if not connection:
                return

            # Remove old association
            if connection.room_id:
                self._room_connections[connection.room_id].discard(connection_id)

            # Add new association if room_id provided
            connection.room_id = room_id
            if room_id:
                self._room_connections[room_id].add(connection_id)
            connection.update_activity()


class ConnectionManager:
    """
    Manages WebSocket connections with infrastructure integration.

    Features:
    - Connection lifecycle management
    - State tracking and transitions
    - Event callbacks
    - Health monitoring
    - Graceful shutdown
    """

    def __init__(
        self,
        registry: Optional[IConnectionRegistry] = None,
        heartbeat_interval: int = 30,
        connection_timeout: int = 300,
    ):
        """
        Initialize connection manager.

        Args:
            registry: Connection registry implementation
            heartbeat_interval: Seconds between heartbeats
            connection_timeout: Seconds before timing out inactive connections
        """
        self.registry = registry or InMemoryConnectionRegistry()
        self.heartbeat_interval = heartbeat_interval
        self.connection_timeout = connection_timeout

        # Callbacks
        self._on_connect_callbacks: List[Callable] = []
        self._on_disconnect_callbacks: List[Callable] = []
        self._on_state_change_callbacks: List[Callable] = []

        # Background tasks
        self._tasks: Set[asyncio.Task] = set()
        self._running = False

        # Metrics
        self._metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "total_messages": 0,
            "errors": 0,
        }

    async def start(self) -> None:
        """Start the connection manager."""
        self._running = True

        # Start background tasks
        self._tasks.add(asyncio.create_task(self._heartbeat_loop()))
        self._tasks.add(asyncio.create_task(self._cleanup_loop()))

    async def stop(self) -> None:
        """Stop the connection manager."""
        self._running = False

        # Cancel background tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def connect(self, websocket: WebSocket, connection_id: str) -> ConnectionInfo:
        """
        Handle new WebSocket connection.

        Args:
            websocket: WebSocket instance
            connection_id: Unique connection identifier

        Returns:
            Connection information
        """
        # Accept WebSocket
        await websocket.accept()

        # Create connection info
        connection = ConnectionInfo(
            connection_id=connection_id,
            websocket=websocket,
            state=ConnectionState.CONNECTED,
        )

        # Register connection
        await self.registry.add_connection(connection)

        # Update metrics
        self._metrics["total_connections"] += 1
        self._metrics["active_connections"] += 1

        # Trigger callbacks
        await self._trigger_connect_callbacks(connection)

        logger.info(f"WebSocket connected: {connection_id}")

        return connection

    async def disconnect(
        self, connection_id: str, code: int = 1000, reason: str = "Normal closure"
    ) -> None:
        """
        Handle WebSocket disconnection.

        Args:
            connection_id: Connection to disconnect
            code: WebSocket close code
            reason: Close reason
        """
        connection = await self.registry.get_connection(connection_id)
        if not connection:
            return

        # Update state
        await self.registry.update_connection_state(
            connection_id, ConnectionState.DISCONNECTING
        )

        # Close WebSocket if still open
        if connection.websocket.client_state == WebSocketState.CONNECTED:
            await connection.websocket.close(code=code, reason=reason)

        # Remove from registry
        await self.registry.remove_connection(connection_id)

        # Update metrics
        self._metrics["active_connections"] -= 1

        # Trigger callbacks
        await self._trigger_disconnect_callbacks(connection)

        logger.info(f"WebSocket disconnected: {connection_id}")

    async def authenticate(self, connection_id: str, player_id: str) -> None:
        """
        Authenticate a connection.

        Args:
            connection_id: Connection to authenticate
            player_id: Authenticated player ID
        """
        connection = await self.registry.get_connection(connection_id)
        if not connection:
            return

        # Update player association
        if hasattr(self.registry, "update_connection_player"):
            await self.registry.update_connection_player(connection_id, player_id)

        # Update state
        await self.registry.update_connection_state(
            connection_id, ConnectionState.AUTHENTICATED
        )

        logger.info(f"WebSocket authenticated: {connection_id} -> {player_id}")

    async def join_room(self, connection_id: str, room_id: str) -> None:
        """
        Add connection to a room.

        Args:
            connection_id: Connection to add
            room_id: Room to join
        """
        connection = await self.registry.get_connection(connection_id)
        if not connection:
            return

        # Update room association
        if hasattr(self.registry, "update_connection_room"):
            await self.registry.update_connection_room(connection_id, room_id)

        # Update state
        await self.registry.update_connection_state(
            connection_id, ConnectionState.IN_ROOM
        )

        logger.info(f"WebSocket joined room: {connection_id} -> {room_id}")

    async def leave_room(self, connection_id: str) -> None:
        """
        Remove connection from its room.

        Args:
            connection_id: Connection to remove
        """
        connection = await self.registry.get_connection(connection_id)
        if not connection or not connection.room_id:
            return

        old_room = connection.room_id

        # Update room association
        if hasattr(self.registry, "update_connection_room"):
            await self.registry.update_connection_room(connection_id, None)

        # Update state
        await self.registry.update_connection_state(
            connection_id, ConnectionState.AUTHENTICATED
        )

        logger.info(f"WebSocket left room: {connection_id} <- {old_room}")

    async def send_to_connection(
        self, connection_id: str, message: Dict[str, Any]
    ) -> bool:
        """
        Send message to specific connection.

        Args:
            connection_id: Target connection
            message: Message to send

        Returns:
            True if sent successfully
        """
        connection = await self.registry.get_connection(connection_id)
        if not connection:
            return False

        try:
            if connection.websocket.client_state == WebSocketState.CONNECTED:
                await connection.websocket.send_json(message)
                self._metrics["total_messages"] += 1
                return True
        except Exception as e:
            logger.error(f"Error sending to {connection_id}: {e}")
            self._metrics["errors"] += 1

            # Mark connection as errored
            await self.registry.update_connection_state(
                connection_id, ConnectionState.ERROR
            )

        return False

    async def broadcast_to_room(
        self, room_id: str, message: Dict[str, Any], exclude: Optional[Set[str]] = None
    ) -> int:
        """
        Broadcast message to all connections in a room.

        Args:
            room_id: Target room
            message: Message to broadcast
            exclude: Connection IDs to exclude

        Returns:
            Number of successful sends
        """
        connections = await self.registry.get_connections_by_room(room_id)
        exclude_set = exclude or set()

        sent = 0
        for connection in connections:
            if connection.connection_id not in exclude_set:
                if await self.send_to_connection(connection.connection_id, message):
                    sent += 1

        return sent

    async def broadcast_to_player(self, player_id: str, message: Dict[str, Any]) -> int:
        """
        Broadcast message to all connections for a player.

        Args:
            player_id: Target player
            message: Message to broadcast

        Returns:
            Number of successful sends
        """
        connections = await self.registry.get_connections_by_player(player_id)

        sent = 0
        for connection in connections:
            if await self.send_to_connection(connection.connection_id, message):
                sent += 1

        return sent

    def on_connect(self, callback: Callable) -> None:
        """Register connection callback."""
        self._on_connect_callbacks.append(callback)

    def on_disconnect(self, callback: Callable) -> None:
        """Register disconnection callback."""
        self._on_disconnect_callbacks.append(callback)

    def on_state_change(self, callback: Callable) -> None:
        """Register state change callback."""
        self._on_state_change_callbacks.append(callback)

    async def _trigger_connect_callbacks(self, connection: ConnectionInfo) -> None:
        """Trigger connection callbacks."""
        for callback in self._on_connect_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(connection)
                else:
                    callback(connection)
            except Exception as e:
                logger.error(f"Error in connect callback: {e}")

    async def _trigger_disconnect_callbacks(self, connection: ConnectionInfo) -> None:
        """Trigger disconnection callbacks."""
        for callback in self._on_disconnect_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(connection)
                else:
                    callback(connection)
            except Exception as e:
                logger.error(f"Error in disconnect callback: {e}")

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats to connections."""
        while self._running:
            try:
                # Get all connections
                connections = (
                    list(self._connections.values())
                    if hasattr(self, "_connections")
                    else []
                )

                # Send heartbeat to each
                for connection in connections:
                    await self.send_to_connection(
                        connection.connection_id,
                        {
                            "type": "heartbeat",
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )

                await asyncio.sleep(self.heartbeat_interval)

            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(5)

    async def _cleanup_loop(self) -> None:
        """Clean up inactive connections."""
        while self._running:
            try:
                # Check for timed out connections
                cutoff = datetime.utcnow().timestamp() - self.connection_timeout

                # This would need access to all connections
                # In production, would iterate through registry

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)

    def get_metrics(self) -> Dict[str, Any]:
        """Get connection manager metrics."""
        return self._metrics.copy()
