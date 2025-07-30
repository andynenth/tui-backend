"""
Connection recovery mechanisms for WebSocket infrastructure.

Provides reconnection handling, state recovery, and resilience features.
"""

from typing import Dict, Any, Optional, List, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import asyncio
import json
import logging
from collections import deque

from .connection_manager import ConnectionManager, ConnectionInfo, ConnectionState
from .state_sync import StateSynchronizer, SyncStrategy
from .event_propagator import EventPropagator, Event, EventPriority


logger = logging.getLogger(__name__)


class RecoveryStatus(Enum):
    """Status of recovery process."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RecoveryContext:
    """Context for connection recovery."""

    connection_id: str
    old_connection_id: Optional[str]
    player_id: Optional[str]
    room_id: Optional[str]
    last_seen: datetime
    missed_events: List[Event] = field(default_factory=list)
    recovery_token: Optional[str] = None
    attempts: int = 0
    status: RecoveryStatus = RecoveryStatus.PENDING


@dataclass
class RecoveryConfig:
    """Configuration for recovery system."""

    max_recovery_time: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    max_reconnect_attempts: int = 3
    event_buffer_size: int = 1000
    event_buffer_time: timedelta = field(default_factory=lambda: timedelta(minutes=10))
    recovery_token_ttl: timedelta = field(default_factory=lambda: timedelta(hours=1))
    enable_state_recovery: bool = True
    enable_event_replay: bool = True


class RecoveryStrategy(ABC):
    """Base class for recovery strategies."""

    @abstractmethod
    async def can_recover(self, context: RecoveryContext) -> bool:
        """Check if recovery is possible."""
        pass

    @abstractmethod
    async def recover(
        self, context: RecoveryContext, new_connection: ConnectionInfo
    ) -> bool:
        """Perform recovery."""
        pass


class ReconnectionHandler:
    """
    Handles WebSocket reconnection logic.

    Features:
    - Automatic reconnection
    - Exponential backoff
    - Connection validation
    """

    def __init__(self, connection_manager: ConnectionManager, config: RecoveryConfig):
        """Initialize reconnection handler."""
        self.connection_manager = connection_manager
        self.config = config

        # Track recovery contexts
        self._recovery_contexts: Dict[str, RecoveryContext] = {}
        self._recovery_tokens: Dict[str, str] = {}  # token -> connection_id

        # Metrics
        self._metrics = {
            "reconnect_attempts": 0,
            "successful_reconnects": 0,
            "failed_reconnects": 0,
            "average_recovery_time": 0.0,
        }

    async def generate_recovery_token(self, connection_id: str) -> str:
        """Generate a recovery token for a connection."""
        import uuid

        token = str(uuid.uuid4())
        self._recovery_tokens[token] = connection_id

        # Schedule token expiry
        asyncio.create_task(self._expire_token(token))

        return token

    async def handle_disconnection(self, connection: ConnectionInfo) -> RecoveryContext:
        """Handle connection disconnection."""
        # Create recovery context
        context = RecoveryContext(
            connection_id=connection.connection_id,
            old_connection_id=connection.connection_id,
            player_id=connection.player_id,
            room_id=connection.room_id,
            last_seen=datetime.utcnow(),
        )

        # Generate recovery token
        context.recovery_token = await self.generate_recovery_token(
            connection.connection_id
        )

        # Store context
        self._recovery_contexts[connection.connection_id] = context

        logger.info(
            f"Created recovery context for {connection.connection_id} "
            f"with token {context.recovery_token}"
        )

        return context

    async def attempt_recovery(
        self, recovery_token: str, new_connection: ConnectionInfo
    ) -> bool:
        """
        Attempt to recover a connection.

        Args:
            recovery_token: Token from disconnected connection
            new_connection: New connection to recover to

        Returns:
            True if recovery successful
        """
        # Validate token
        old_connection_id = self._recovery_tokens.get(recovery_token)
        if not old_connection_id:
            logger.warning(f"Invalid recovery token: {recovery_token}")
            return False

        # Get recovery context
        context = self._recovery_contexts.get(old_connection_id)
        if not context:
            logger.warning(f"No recovery context for {old_connection_id}")
            return False

        # Check if recovery allowed
        if not await self._can_recover(context):
            logger.warning(f"Recovery not allowed for {old_connection_id}")
            return False

        # Update metrics
        self._metrics["reconnect_attempts"] += 1
        context.attempts += 1
        context.status = RecoveryStatus.IN_PROGRESS

        # Perform recovery
        success = await self._perform_recovery(context, new_connection)

        if success:
            self._metrics["successful_reconnects"] += 1
            context.status = RecoveryStatus.COMPLETED

            # Clean up old context
            del self._recovery_contexts[old_connection_id]
            del self._recovery_tokens[recovery_token]

            logger.info(
                f"Successfully recovered {old_connection_id} to {new_connection.connection_id}"
            )
        else:
            self._metrics["failed_reconnects"] += 1
            context.status = RecoveryStatus.FAILED

            logger.error(f"Failed to recover {old_connection_id}")

        return success

    async def _can_recover(self, context: RecoveryContext) -> bool:
        """Check if recovery is allowed."""
        # Check time limit
        elapsed = datetime.utcnow() - context.last_seen
        if elapsed > self.config.max_recovery_time:
            return False

        # Check attempt limit
        if context.attempts >= self.config.max_reconnect_attempts:
            return False

        return True

    async def _perform_recovery(
        self, context: RecoveryContext, new_connection: ConnectionInfo
    ) -> bool:
        """Perform the actual recovery."""
        try:
            start_time = datetime.utcnow()

            # Transfer connection properties
            new_connection.player_id = context.player_id
            new_connection.room_id = context.room_id

            # Update connection state
            await self.connection_manager.registry.update_connection_state(
                new_connection.connection_id,
                (
                    ConnectionState.AUTHENTICATED
                    if context.player_id
                    else ConnectionState.CONNECTED
                ),
            )

            # Rejoin room if needed
            if context.room_id:
                await self.connection_manager.join_room(
                    new_connection.connection_id, context.room_id
                )

            # Send recovery success message
            await self.connection_manager.send_to_connection(
                new_connection.connection_id,
                {
                    "type": "recovery_success",
                    "old_connection_id": context.old_connection_id,
                    "recovered_at": datetime.utcnow().isoformat(),
                },
            )

            # Update average recovery time
            recovery_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_average_recovery_time(recovery_time)

            return True

        except Exception as e:
            logger.error(f"Error during recovery: {e}")
            return False

    async def _expire_token(self, token: str) -> None:
        """Expire a recovery token after TTL."""
        await asyncio.sleep(self.config.recovery_token_ttl.total_seconds())

        # Remove token if still exists
        connection_id = self._recovery_tokens.pop(token, None)
        if connection_id:
            # Clean up context if no longer needed
            context = self._recovery_contexts.get(connection_id)
            if context and context.recovery_token == token:
                del self._recovery_contexts[connection_id]

    def _update_average_recovery_time(self, recovery_time: float) -> None:
        """Update average recovery time metric."""
        total_recoveries = self._metrics["successful_reconnects"]
        if total_recoveries == 0:
            self._metrics["average_recovery_time"] = recovery_time
        else:
            current_avg = self._metrics["average_recovery_time"]
            self._metrics["average_recovery_time"] = (
                current_avg * (total_recoveries - 1) + recovery_time
            ) / total_recoveries


class StateReconciliation:
    """
    Handles state reconciliation after reconnection.

    Features:
    - State comparison
    - Conflict resolution
    - Incremental updates
    """

    def __init__(
        self, state_synchronizer: StateSynchronizer, event_propagator: EventPropagator
    ):
        """Initialize state reconciliation."""
        self.state_synchronizer = state_synchronizer
        self.event_propagator = event_propagator

    async def reconcile_state(
        self,
        connection: ConnectionInfo,
        client_state: Dict[str, Any],
        entity_type: str,
        entity_id: str,
    ) -> bool:
        """
        Reconcile client state with server state.

        Args:
            connection: Connection to reconcile
            client_state: Client's last known state
            entity_type: Type of entity
            entity_id: Entity identifier

        Returns:
            True if reconciliation successful
        """
        try:
            # Get current server state
            server_state = await self._get_server_state(entity_type, entity_id)

            if not server_state:
                logger.warning(f"No server state for {entity_type}:{entity_id}")
                return False

            # Compare versions
            client_version = client_state.get("version", 0)
            server_version = server_state.get("version", 0)

            if client_version == server_version:
                # States are in sync
                await self._send_reconciliation_result(
                    connection, "in_sync", entity_type, entity_id
                )
                return True

            # Perform reconciliation based on strategy
            strategy = self.state_synchronizer._connection_strategies.get(
                connection.connection_id, SyncStrategy.DELTA
            )

            if strategy == SyncStrategy.OPTIMISTIC:
                # Handle optimistic reconciliation
                await self._reconcile_optimistic(
                    connection, client_state, server_state, entity_type, entity_id
                )
            else:
                # Simple server wins
                await self.state_synchronizer.sync_state(
                    entity_type, entity_id, server_state, [connection.connection_id]
                )

            await self._send_reconciliation_result(
                connection, "reconciled", entity_type, entity_id
            )

            return True

        except Exception as e:
            logger.error(f"Error during state reconciliation: {e}")
            return False

    async def _reconcile_optimistic(
        self,
        connection: ConnectionInfo,
        client_state: Dict[str, Any],
        server_state: Dict[str, Any],
        entity_type: str,
        entity_id: str,
    ) -> None:
        """Perform optimistic reconciliation."""
        # Get pending client operations
        client_ops = client_state.get("pending_operations", [])

        if client_ops:
            # Try to reapply client operations
            reconciled_state = await self._reapply_operations(
                server_state, client_ops, entity_type, entity_id
            )

            # Send reconciled state
            await self.state_synchronizer.sync_state(
                entity_type, entity_id, reconciled_state, [connection.connection_id]
            )
        else:
            # No pending operations, use server state
            await self.state_synchronizer.sync_state(
                entity_type, entity_id, server_state, [connection.connection_id]
            )

    async def _reapply_operations(
        self,
        base_state: Dict[str, Any],
        operations: List[Dict[str, Any]],
        entity_type: str,
        entity_id: str,
    ) -> Dict[str, Any]:
        """Reapply client operations to base state."""
        # This would implement operation transformation
        # For now, just return base state
        return base_state

    async def _get_server_state(
        self, entity_type: str, entity_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get current server state."""
        # This would integrate with repositories
        return {"id": entity_id, "type": entity_type, "version": 1, "data": {}}

    async def _send_reconciliation_result(
        self, connection: ConnectionInfo, status: str, entity_type: str, entity_id: str
    ) -> None:
        """Send reconciliation result to client."""
        await connection.websocket.send_json(
            {
                "type": "reconciliation_result",
                "status": status,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


class ConnectionRecoveryManager:
    """
    Main connection recovery manager.

    Features:
    - Coordinated recovery process
    - Event buffering
    - State recovery
    - Metrics tracking
    """

    def __init__(
        self,
        connection_manager: ConnectionManager,
        state_synchronizer: StateSynchronizer,
        event_propagator: EventPropagator,
        config: Optional[RecoveryConfig] = None,
    ):
        """Initialize recovery manager."""
        self.connection_manager = connection_manager
        self.state_synchronizer = state_synchronizer
        self.event_propagator = event_propagator
        self.config = config or RecoveryConfig()

        # Components
        self.reconnection_handler = ReconnectionHandler(connection_manager, self.config)
        self.state_reconciliation = StateReconciliation(
            state_synchronizer, event_propagator
        )

        # Event buffering
        self._event_buffer: deque = deque(maxlen=self.config.event_buffer_size)
        self._connection_event_positions: Dict[str, int] = {}

        # Recovery strategies
        self._strategies: List[RecoveryStrategy] = []

        # Background tasks
        self._tasks: Set[asyncio.Task] = set()
        self._running = False

    async def start(self) -> None:
        """Start the recovery manager."""
        self._running = True

        # Start event buffer cleanup
        task = asyncio.create_task(self._cleanup_event_buffer())
        self._tasks.add(task)

        # Register connection callbacks
        self.connection_manager.on_disconnect(self._on_disconnect)

    async def stop(self) -> None:
        """Stop the recovery manager."""
        self._running = False

        # Cancel tasks
        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    def add_strategy(self, strategy: RecoveryStrategy) -> None:
        """Add a recovery strategy."""
        self._strategies.append(strategy)

    async def handle_connection(
        self, websocket, connection_id: str, recovery_token: Optional[str] = None
    ) -> Optional[ConnectionInfo]:
        """
        Handle new connection with potential recovery.

        Args:
            websocket: WebSocket connection
            connection_id: New connection ID
            recovery_token: Optional recovery token

        Returns:
            Connection info if successful
        """
        # Create new connection
        connection = await self.connection_manager.connect(websocket, connection_id)

        # Attempt recovery if token provided
        if recovery_token:
            success = await self.reconnection_handler.attempt_recovery(
                recovery_token, connection
            )

            if success and self.config.enable_event_replay:
                # Replay missed events
                await self._replay_missed_events(connection)

        return connection

    async def buffer_event(self, event: Event, room_id: Optional[str] = None) -> None:
        """Buffer an event for recovery."""
        # Add to buffer with metadata
        buffered_event = {
            "event": event,
            "timestamp": datetime.utcnow(),
            "room_id": room_id,
            "sequence": len(self._event_buffer),
        }

        self._event_buffer.append(buffered_event)

    async def _on_disconnect(self, connection: ConnectionInfo) -> None:
        """Handle connection disconnection."""
        # Create recovery context
        context = await self.reconnection_handler.handle_disconnection(connection)

        # Record event position for replay
        if self._event_buffer:
            self._connection_event_positions[connection.connection_id] = (
                self._event_buffer[-1]["sequence"]
            )

    async def _replay_missed_events(self, connection: ConnectionInfo) -> None:
        """Replay missed events to recovered connection."""
        # Get last known position
        last_position = self._connection_event_positions.get(
            connection.connection_id, -1
        )

        # Find events to replay
        events_to_replay = []
        for buffered in self._event_buffer:
            if buffered["sequence"] > last_position:
                # Check if event is relevant
                if connection.room_id and buffered["room_id"] == connection.room_id:
                    events_to_replay.append(buffered["event"])

        if events_to_replay:
            # Send replay notification
            await connection.websocket.send_json(
                {"type": "event_replay_start", "count": len(events_to_replay)}
            )

            # Replay events
            for event in events_to_replay:
                await connection.websocket.send_json(event.to_message())

            # Send replay complete
            await connection.websocket.send_json({"type": "event_replay_complete"})

    async def _cleanup_event_buffer(self) -> None:
        """Clean up old events from buffer."""
        while self._running:
            try:
                cutoff = datetime.utcnow() - self.config.event_buffer_time

                # Remove old events
                while (
                    self._event_buffer and self._event_buffer[0]["timestamp"] < cutoff
                ):
                    self._event_buffer.popleft()

                # Clean up old position tracking
                # Would need to track which connections are truly gone

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in event buffer cleanup: {e}")
                await asyncio.sleep(60)

    def get_metrics(self) -> Dict[str, Any]:
        """Get recovery metrics."""
        return {
            "reconnection": self.reconnection_handler._metrics,
            "event_buffer_size": len(self._event_buffer),
            "recovery_contexts": len(self.reconnection_handler._recovery_contexts),
        }
