"""
State synchronization for WebSocket connections.

Provides mechanisms for keeping client state synchronized with server state.
"""

from typing import Dict, Any, Optional, List, Set, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import json
from enum import Enum
import hashlib

from .connection_manager import ConnectionManager, ConnectionInfo
from .event_propagator import EventPropagator, Event, EventPriority, BroadcastScope


class SyncStrategy(Enum):
    """State synchronization strategies."""
    FULL = "full"           # Send complete state
    DELTA = "delta"         # Send only changes
    OPTIMISTIC = "optimistic"  # Client-side prediction with reconciliation
    PASSIVE = "passive"     # No active sync, rely on events


@dataclass
class StateSnapshot:
    """Represents a state snapshot."""
    entity_type: str
    entity_id: str
    version: int
    state: Dict[str, Any]
    checksum: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_state(
        cls,
        entity_type: str,
        entity_id: str,
        version: int,
        state: Dict[str, Any]
    ) -> 'StateSnapshot':
        """Create snapshot from state."""
        # Calculate checksum
        state_json = json.dumps(state, sort_keys=True)
        checksum = hashlib.sha256(state_json.encode()).hexdigest()[:8]
        
        return cls(
            entity_type=entity_type,
            entity_id=entity_id,
            version=version,
            state=state,
            checksum=checksum
        )


@dataclass
class StateDelta:
    """Represents a state change."""
    entity_type: str
    entity_id: str
    from_version: int
    to_version: int
    operations: List[Dict[str, Any]]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ISyncStrategy(ABC):
    """Interface for synchronization strategies."""
    
    @abstractmethod
    async def sync_state(
        self,
        connection: ConnectionInfo,
        entity_type: str,
        entity_id: str,
        current_state: Dict[str, Any],
        client_version: Optional[int] = None
    ) -> None:
        """Synchronize state with client."""
        pass
    
    @abstractmethod
    async def handle_conflict(
        self,
        connection: ConnectionInfo,
        entity_type: str,
        entity_id: str,
        client_state: Dict[str, Any],
        server_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle state conflict."""
        pass


class FullSync(ISyncStrategy):
    """
    Full state synchronization strategy.
    
    Always sends complete state to client.
    """
    
    def __init__(
        self,
        connection_manager: ConnectionManager,
        event_propagator: EventPropagator
    ):
        """Initialize full sync strategy."""
        self.connection_manager = connection_manager
        self.event_propagator = event_propagator
    
    async def sync_state(
        self,
        connection: ConnectionInfo,
        entity_type: str,
        entity_id: str,
        current_state: Dict[str, Any],
        client_version: Optional[int] = None
    ) -> None:
        """Send full state to client."""
        # Create state snapshot
        snapshot = StateSnapshot.from_state(
            entity_type,
            entity_id,
            current_state.get('version', 0),
            current_state
        )
        
        # Send to client
        await self.connection_manager.send_to_connection(
            connection.connection_id,
            {
                "type": "state_sync",
                "strategy": "full",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "version": snapshot.version,
                "state": snapshot.state,
                "checksum": snapshot.checksum,
                "timestamp": snapshot.timestamp.isoformat()
            }
        )
    
    async def handle_conflict(
        self,
        connection: ConnectionInfo,
        entity_type: str,
        entity_id: str,
        client_state: Dict[str, Any],
        server_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Server state always wins in full sync."""
        # Send server state to client
        await self.sync_state(
            connection,
            entity_type,
            entity_id,
            server_state
        )
        
        return server_state


class DeltaSync(ISyncStrategy):
    """
    Delta synchronization strategy.
    
    Sends only changes between versions.
    """
    
    def __init__(
        self,
        connection_manager: ConnectionManager,
        event_propagator: EventPropagator,
        delta_storage: Optional[Dict[str, List[StateDelta]]] = None
    ):
        """Initialize delta sync strategy."""
        self.connection_manager = connection_manager
        self.event_propagator = event_propagator
        self.delta_storage = delta_storage or {}
    
    async def sync_state(
        self,
        connection: ConnectionInfo,
        entity_type: str,
        entity_id: str,
        current_state: Dict[str, Any],
        client_version: Optional[int] = None
    ) -> None:
        """Send delta or full state based on client version."""
        server_version = current_state.get('version', 0)
        
        # If no client version or too far behind, send full state
        if client_version is None or client_version < server_version - 10:
            await self._send_full_state(
                connection,
                entity_type,
                entity_id,
                current_state
            )
            return
        
        # If client is up to date
        if client_version >= server_version:
            return
        
        # Send deltas
        deltas = self._get_deltas(
            entity_type,
            entity_id,
            client_version,
            server_version
        )
        
        if deltas:
            await self._send_deltas(connection, deltas)
        else:
            # No deltas available, send full state
            await self._send_full_state(
                connection,
                entity_type,
                entity_id,
                current_state
            )
    
    async def handle_conflict(
        self,
        connection: ConnectionInfo,
        entity_type: str,
        entity_id: str,
        client_state: Dict[str, Any],
        server_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Try to merge changes or fall back to server state."""
        # Simple last-write-wins for now
        # In production, would implement proper conflict resolution
        
        await self.sync_state(
            connection,
            entity_type,
            entity_id,
            server_state,
            client_state.get('version')
        )
        
        return server_state
    
    def record_delta(
        self,
        entity_type: str,
        entity_id: str,
        from_version: int,
        to_version: int,
        operations: List[Dict[str, Any]]
    ) -> None:
        """Record a state delta."""
        key = f"{entity_type}:{entity_id}"
        
        if key not in self.delta_storage:
            self.delta_storage[key] = []
        
        delta = StateDelta(
            entity_type=entity_type,
            entity_id=entity_id,
            from_version=from_version,
            to_version=to_version,
            operations=operations
        )
        
        self.delta_storage[key].append(delta)
        
        # Keep only recent deltas
        self.delta_storage[key] = self.delta_storage[key][-50:]
    
    def _get_deltas(
        self,
        entity_type: str,
        entity_id: str,
        from_version: int,
        to_version: int
    ) -> List[StateDelta]:
        """Get deltas between versions."""
        key = f"{entity_type}:{entity_id}"
        deltas = self.delta_storage.get(key, [])
        
        # Filter relevant deltas
        relevant = [
            delta for delta in deltas
            if delta.from_version >= from_version and delta.to_version <= to_version
        ]
        
        return relevant
    
    async def _send_full_state(
        self,
        connection: ConnectionInfo,
        entity_type: str,
        entity_id: str,
        state: Dict[str, Any]
    ) -> None:
        """Send full state to client."""
        snapshot = StateSnapshot.from_state(
            entity_type,
            entity_id,
            state.get('version', 0),
            state
        )
        
        await self.connection_manager.send_to_connection(
            connection.connection_id,
            {
                "type": "state_sync",
                "strategy": "full",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "version": snapshot.version,
                "state": snapshot.state,
                "checksum": snapshot.checksum,
                "timestamp": snapshot.timestamp.isoformat()
            }
        )
    
    async def _send_deltas(
        self,
        connection: ConnectionInfo,
        deltas: List[StateDelta]
    ) -> None:
        """Send deltas to client."""
        for delta in deltas:
            await self.connection_manager.send_to_connection(
                connection.connection_id,
                {
                    "type": "state_sync",
                    "strategy": "delta",
                    "entity_type": delta.entity_type,
                    "entity_id": delta.entity_id,
                    "from_version": delta.from_version,
                    "to_version": delta.to_version,
                    "operations": delta.operations,
                    "timestamp": delta.timestamp.isoformat()
                }
            )


class OptimisticSync(ISyncStrategy):
    """
    Optimistic synchronization with client-side prediction.
    
    Allows clients to make changes optimistically and reconciles conflicts.
    """
    
    def __init__(
        self,
        connection_manager: ConnectionManager,
        event_propagator: EventPropagator,
        conflict_resolver: Optional[Callable] = None
    ):
        """Initialize optimistic sync strategy."""
        self.connection_manager = connection_manager
        self.event_propagator = event_propagator
        self.conflict_resolver = conflict_resolver or self._default_conflict_resolver
        
        # Track pending client operations
        self._pending_ops: Dict[str, List[Dict[str, Any]]] = {}
    
    async def sync_state(
        self,
        connection: ConnectionInfo,
        entity_type: str,
        entity_id: str,
        current_state: Dict[str, Any],
        client_version: Optional[int] = None
    ) -> None:
        """Sync with acknowledgment of client operations."""
        # Get pending operations for this connection
        key = f"{connection.connection_id}:{entity_type}:{entity_id}"
        pending = self._pending_ops.get(key, [])
        
        # Send sync with acknowledgments
        await self.connection_manager.send_to_connection(
            connection.connection_id,
            {
                "type": "state_sync",
                "strategy": "optimistic",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "version": current_state.get('version', 0),
                "state": current_state,
                "acknowledged_ops": [op['id'] for op in pending],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Clear acknowledged operations
        self._pending_ops[key] = []
    
    async def handle_conflict(
        self,
        connection: ConnectionInfo,
        entity_type: str,
        entity_id: str,
        client_state: Dict[str, Any],
        server_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve conflicts using configured resolver."""
        resolved_state = await self.conflict_resolver(
            client_state,
            server_state,
            entity_type,
            entity_id
        )
        
        # Send resolution to client
        await self.connection_manager.send_to_connection(
            connection.connection_id,
            {
                "type": "conflict_resolution",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "resolved_state": resolved_state,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return resolved_state
    
    async def handle_client_operation(
        self,
        connection: ConnectionInfo,
        entity_type: str,
        entity_id: str,
        operation: Dict[str, Any]
    ) -> None:
        """Handle optimistic client operation."""
        # Track pending operation
        key = f"{connection.connection_id}:{entity_type}:{entity_id}"
        
        if key not in self._pending_ops:
            self._pending_ops[key] = []
        
        self._pending_ops[key].append(operation)
        
        # Send immediate acknowledgment
        await self.connection_manager.send_to_connection(
            connection.connection_id,
            {
                "type": "operation_ack",
                "operation_id": operation.get('id'),
                "status": "pending",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def _default_conflict_resolver(
        self,
        client_state: Dict[str, Any],
        server_state: Dict[str, Any],
        entity_type: str,
        entity_id: str
    ) -> Dict[str, Any]:
        """Default conflict resolution - server wins."""
        return server_state


class StateSynchronizer:
    """
    Main state synchronization manager.
    
    Features:
    - Multiple sync strategies
    - Connection state tracking
    - Automatic sync triggers
    - Conflict detection and resolution
    """
    
    def __init__(
        self,
        connection_manager: ConnectionManager,
        event_propagator: EventPropagator,
        default_strategy: SyncStrategy = SyncStrategy.DELTA
    ):
        """Initialize state synchronizer."""
        self.connection_manager = connection_manager
        self.event_propagator = event_propagator
        self.default_strategy = default_strategy
        
        # Strategy implementations
        self.strategies = {
            SyncStrategy.FULL: FullSync(connection_manager, event_propagator),
            SyncStrategy.DELTA: DeltaSync(connection_manager, event_propagator),
            SyncStrategy.OPTIMISTIC: OptimisticSync(connection_manager, event_propagator)
        }
        
        # Connection sync preferences
        self._connection_strategies: Dict[str, SyncStrategy] = {}
        self._sync_subscriptions: Dict[str, Set[tuple[str, str]]] = {}
        
        # State tracking
        self._last_sync: Dict[str, datetime] = {}
        self._client_versions: Dict[str, Dict[str, int]] = {}
    
    async def set_connection_strategy(
        self,
        connection_id: str,
        strategy: SyncStrategy
    ) -> None:
        """Set sync strategy for a connection."""
        self._connection_strategies[connection_id] = strategy
    
    async def subscribe_to_sync(
        self,
        connection_id: str,
        entity_type: str,
        entity_id: str
    ) -> None:
        """Subscribe connection to state sync."""
        if connection_id not in self._sync_subscriptions:
            self._sync_subscriptions[connection_id] = set()
        
        self._sync_subscriptions[connection_id].add((entity_type, entity_id))
    
    async def unsubscribe_from_sync(
        self,
        connection_id: str,
        entity_type: str,
        entity_id: str
    ) -> None:
        """Unsubscribe from state sync."""
        if connection_id in self._sync_subscriptions:
            self._sync_subscriptions[connection_id].discard((entity_type, entity_id))
    
    async def sync_state(
        self,
        entity_type: str,
        entity_id: str,
        current_state: Dict[str, Any],
        target_connections: Optional[List[str]] = None
    ) -> None:
        """
        Synchronize state to connections.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity identifier
            current_state: Current server state
            target_connections: Specific connections to sync (None for all subscribed)
        """
        # Determine target connections
        if target_connections is None:
            target_connections = []
            
            # Find all subscribed connections
            for conn_id, subscriptions in self._sync_subscriptions.items():
                if (entity_type, entity_id) in subscriptions:
                    target_connections.append(conn_id)
        
        # Sync to each connection
        for conn_id in target_connections:
            connection = await self.connection_manager.registry.get_connection(conn_id)
            if not connection:
                continue
            
            # Get connection's strategy
            strategy_type = self._connection_strategies.get(
                conn_id,
                self.default_strategy
            )
            strategy = self.strategies[strategy_type]
            
            # Get client version
            client_version = self._get_client_version(conn_id, entity_type, entity_id)
            
            # Perform sync
            await strategy.sync_state(
                connection,
                entity_type,
                entity_id,
                current_state,
                client_version
            )
            
            # Update last sync time
            sync_key = f"{conn_id}:{entity_type}:{entity_id}"
            self._last_sync[sync_key] = datetime.utcnow()
    
    async def handle_sync_request(
        self,
        connection_id: str,
        entity_type: str,
        entity_id: str,
        client_version: Optional[int] = None,
        client_checksum: Optional[str] = None
    ) -> None:
        """Handle explicit sync request from client."""
        # Update client version
        self._set_client_version(connection_id, entity_type, entity_id, client_version)
        
        # Get current state (would come from repository)
        current_state = await self._get_entity_state(entity_type, entity_id)
        
        if not current_state:
            await self.connection_manager.send_to_connection(
                connection_id,
                {
                    "type": "sync_error",
                    "error": "entity_not_found",
                    "entity_type": entity_type,
                    "entity_id": entity_id
                }
            )
            return
        
        # Check if sync needed
        if client_checksum:
            server_checksum = self._calculate_checksum(current_state)
            if client_checksum == server_checksum:
                # Client is up to date
                await self.connection_manager.send_to_connection(
                    connection_id,
                    {
                        "type": "sync_status",
                        "status": "up_to_date",
                        "entity_type": entity_type,
                        "entity_id": entity_id
                    }
                )
                return
        
        # Perform sync
        await self.sync_state(
            entity_type,
            entity_id,
            current_state,
            [connection_id]
        )
    
    async def cleanup_connection(self, connection_id: str) -> None:
        """Clean up sync state for disconnected connection."""
        self._connection_strategies.pop(connection_id, None)
        self._sync_subscriptions.pop(connection_id, None)
        
        # Clean up version tracking
        if connection_id in self._client_versions:
            del self._client_versions[connection_id]
        
        # Clean up last sync times
        keys_to_remove = [
            key for key in self._last_sync
            if key.startswith(f"{connection_id}:")
        ]
        for key in keys_to_remove:
            del self._last_sync[key]
    
    def _get_client_version(
        self,
        connection_id: str,
        entity_type: str,
        entity_id: str
    ) -> Optional[int]:
        """Get tracked client version."""
        if connection_id not in self._client_versions:
            return None
        
        key = f"{entity_type}:{entity_id}"
        return self._client_versions[connection_id].get(key)
    
    def _set_client_version(
        self,
        connection_id: str,
        entity_type: str,
        entity_id: str,
        version: Optional[int]
    ) -> None:
        """Update tracked client version."""
        if version is None:
            return
        
        if connection_id not in self._client_versions:
            self._client_versions[connection_id] = {}
        
        key = f"{entity_type}:{entity_id}"
        self._client_versions[connection_id][key] = version
    
    async def _get_entity_state(
        self,
        entity_type: str,
        entity_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get current entity state from repository."""
        # This would integrate with repositories
        # For now, return mock state
        return {
            "id": entity_id,
            "type": entity_type,
            "version": 1,
            "data": {}
        }
    
    def _calculate_checksum(self, state: Dict[str, Any]) -> str:
        """Calculate state checksum."""
        state_json = json.dumps(state, sort_keys=True)
        return hashlib.sha256(state_json.encode()).hexdigest()[:8]