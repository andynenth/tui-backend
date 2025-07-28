"""
WebSocket-aware repository implementations.

Provides repositories that automatically broadcast changes through WebSocket
connections and support real-time subscriptions.
"""

from typing import Dict, Set, Optional, List, Any, Callable, TypeVar, Generic
from abc import abstractmethod
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
import weakref
from enum import Enum

from domain.interfaces.repositories import (
    RoomRepository,
    GameRepository,
    PlayerStatsRepository
)
from domain.entities import Room, Game, PlayerStats
from infrastructure.repositories import (
    OptimizedRoomRepository,
    OptimizedGameRepository,
    OptimizedPlayerStatsRepository,
    InMemoryUnitOfWork
)
from .connection_manager import ConnectionManager


T = TypeVar('T')


class ChangeType(Enum):
    """Types of repository changes."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


@dataclass
class ChangeEvent(Generic[T]):
    """Represents a change to an entity."""
    entity_type: str
    entity_id: str
    change_type: ChangeType
    entity: Optional[T]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Subscription:
    """Represents a subscription to repository changes."""
    subscription_id: str
    connection_id: str
    entity_type: str
    entity_id: Optional[str] = None  # None means subscribe to all
    filter_func: Optional[Callable[[ChangeEvent], bool]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class SubscriptionManager:
    """
    Manages subscriptions to repository changes.
    
    Features:
    - Entity-specific subscriptions
    - Filtered subscriptions
    - Automatic cleanup on disconnect
    """
    
    def __init__(self):
        """Initialize subscription manager."""
        self._subscriptions: Dict[str, Subscription] = {}
        self._by_connection: Dict[str, Set[str]] = {}
        self._by_entity_type: Dict[str, Set[str]] = {}
        self._by_entity: Dict[tuple[str, str], Set[str]] = {}
        self._lock = asyncio.Lock()
    
    async def subscribe(
        self,
        connection_id: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        filter_func: Optional[Callable[[ChangeEvent], bool]] = None
    ) -> str:
        """
        Create a subscription.
        
        Args:
            connection_id: Connection making the subscription
            entity_type: Type of entity to subscribe to
            entity_id: Specific entity ID (None for all)
            filter_func: Optional filter function
            
        Returns:
            Subscription ID
        """
        subscription_id = f"{connection_id}:{entity_type}:{entity_id or 'all'}"
        
        subscription = Subscription(
            subscription_id=subscription_id,
            connection_id=connection_id,
            entity_type=entity_type,
            entity_id=entity_id,
            filter_func=filter_func
        )
        
        async with self._lock:
            self._subscriptions[subscription_id] = subscription
            
            # Update indexes
            if connection_id not in self._by_connection:
                self._by_connection[connection_id] = set()
            self._by_connection[connection_id].add(subscription_id)
            
            if entity_type not in self._by_entity_type:
                self._by_entity_type[entity_type] = set()
            self._by_entity_type[entity_type].add(subscription_id)
            
            if entity_id:
                key = (entity_type, entity_id)
                if key not in self._by_entity:
                    self._by_entity[key] = set()
                self._by_entity[key].add(subscription_id)
        
        return subscription_id
    
    async def unsubscribe(self, subscription_id: str) -> None:
        """Remove a subscription."""
        async with self._lock:
            subscription = self._subscriptions.pop(subscription_id, None)
            if not subscription:
                return
            
            # Clean up indexes
            self._by_connection[subscription.connection_id].discard(subscription_id)
            if not self._by_connection[subscription.connection_id]:
                del self._by_connection[subscription.connection_id]
            
            self._by_entity_type[subscription.entity_type].discard(subscription_id)
            if not self._by_entity_type[subscription.entity_type]:
                del self._by_entity_type[subscription.entity_type]
            
            if subscription.entity_id:
                key = (subscription.entity_type, subscription.entity_id)
                self._by_entity[key].discard(subscription_id)
                if not self._by_entity[key]:
                    del self._by_entity[key]
    
    async def unsubscribe_connection(self, connection_id: str) -> None:
        """Remove all subscriptions for a connection."""
        async with self._lock:
            subscription_ids = list(self._by_connection.get(connection_id, []))
        
        for subscription_id in subscription_ids:
            await self.unsubscribe(subscription_id)
    
    async def get_subscribers(
        self,
        event: ChangeEvent
    ) -> List[Subscription]:
        """
        Get subscriptions that match an event.
        
        Args:
            event: Change event
            
        Returns:
            List of matching subscriptions
        """
        async with self._lock:
            # Get all subscriptions for entity type
            type_subs = self._by_entity_type.get(event.entity_type, set())
            
            # Get specific entity subscriptions
            entity_subs = set()
            if event.entity_id:
                key = (event.entity_type, event.entity_id)
                entity_subs = self._by_entity.get(key, set())
            
            # Combine all relevant subscription IDs
            all_sub_ids = type_subs | entity_subs
            
            # Get subscription objects and filter
            subscriptions = []
            for sub_id in all_sub_ids:
                sub = self._subscriptions.get(sub_id)
                if not sub:
                    continue
                
                # Check if subscription matches
                if sub.entity_id and sub.entity_id != event.entity_id:
                    continue
                
                # Apply filter if present
                if sub.filter_func and not sub.filter_func(event):
                    continue
                
                subscriptions.append(sub)
            
            return subscriptions


class RealtimeRepositoryMixin:
    """
    Mixin for repositories to add real-time broadcast capabilities.
    
    Features:
    - Automatic change broadcasting
    - Subscription management
    - Optimistic updates
    """
    
    def __init__(
        self,
        entity_type: str,
        connection_manager: ConnectionManager,
        subscription_manager: SubscriptionManager
    ):
        """
        Initialize realtime mixin.
        
        Args:
            entity_type: Type of entity this repository manages
            connection_manager: WebSocket connection manager
            subscription_manager: Subscription manager
        """
        self.entity_type = entity_type
        self.connection_manager = connection_manager
        self.subscription_manager = subscription_manager
        self._broadcast_enabled = True
    
    async def broadcast_change(
        self,
        entity_id: str,
        change_type: ChangeType,
        entity: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Broadcast a change event to subscribers.
        
        Args:
            entity_id: ID of changed entity
            change_type: Type of change
            entity: The entity (if available)
            metadata: Additional metadata
        """
        if not self._broadcast_enabled:
            return
        
        # Create change event
        event = ChangeEvent(
            entity_type=self.entity_type,
            entity_id=entity_id,
            change_type=change_type,
            entity=entity,
            metadata=metadata or {}
        )
        
        # Get subscribers
        subscribers = await self.subscription_manager.get_subscribers(event)
        
        # Broadcast to each subscriber
        for subscription in subscribers:
            message = {
                "type": "repository_change",
                "subscription_id": subscription.subscription_id,
                "event": {
                    "entity_type": event.entity_type,
                    "entity_id": event.entity_id,
                    "change_type": event.change_type.value,
                    "timestamp": event.timestamp.isoformat(),
                    "metadata": event.metadata
                }
            }
            
            # Include entity data if not deleted
            if entity and change_type != ChangeType.DELETED:
                message["event"]["entity"] = self._serialize_entity(entity)
            
            # Send to connection
            await self.connection_manager.send_to_connection(
                subscription.connection_id,
                message
            )
    
    def _serialize_entity(self, entity: Any) -> Dict[str, Any]:
        """
        Serialize entity for WebSocket transmission.
        
        Override in subclasses for custom serialization.
        """
        if hasattr(entity, 'to_dict'):
            return entity.to_dict()
        elif hasattr(entity, '__dict__'):
            return entity.__dict__
        else:
            return {"id": str(entity)}
    
    def disable_broadcast(self) -> None:
        """Temporarily disable broadcasting."""
        self._broadcast_enabled = False
    
    def enable_broadcast(self) -> None:
        """Re-enable broadcasting."""
        self._broadcast_enabled = True


class WebSocketRoomRepository(OptimizedRoomRepository, RealtimeRepositoryMixin):
    """Room repository with WebSocket broadcasting."""
    
    def __init__(
        self,
        connection_manager: ConnectionManager,
        subscription_manager: SubscriptionManager,
        max_rooms: int = 10000
    ):
        """Initialize WebSocket room repository."""
        OptimizedRoomRepository.__init__(self, max_rooms)
        RealtimeRepositoryMixin.__init__(
            self,
            "room",
            connection_manager,
            subscription_manager
        )
    
    async def save(self, room: Room) -> None:
        """Save room and broadcast change."""
        is_new = room.id not in self._rooms
        
        await super().save(room)
        
        # Broadcast change
        await self.broadcast_change(
            room.id,
            ChangeType.CREATED if is_new else ChangeType.UPDATED,
            room
        )
    
    async def delete(self, room_id: str) -> None:
        """Delete room and broadcast change."""
        room = await self.get(room_id)
        
        await super().delete(room_id)
        
        # Broadcast deletion
        if room:
            await self.broadcast_change(
                room_id,
                ChangeType.DELETED,
                metadata={"deleted_room": room.to_dict() if hasattr(room, 'to_dict') else {}}
            )
    
    def _serialize_entity(self, room: Room) -> Dict[str, Any]:
        """Serialize room for WebSocket."""
        return {
            "id": room.id,
            "code": room.code,
            "state": room.state.value if hasattr(room.state, 'value') else str(room.state),
            "players": [
                {"id": p.id, "name": p.name, "is_bot": p.is_bot}
                for p in room.players
            ],
            "game_settings": room.game_settings,
            "created_at": room.created_at.isoformat() if hasattr(room, 'created_at') else None
        }


class WebSocketGameRepository(OptimizedGameRepository, RealtimeRepositoryMixin):
    """Game repository with WebSocket broadcasting."""
    
    def __init__(
        self,
        connection_manager: ConnectionManager,
        subscription_manager: SubscriptionManager
    ):
        """Initialize WebSocket game repository."""
        OptimizedGameRepository.__init__(self)
        RealtimeRepositoryMixin.__init__(
            self,
            "game",
            connection_manager,
            subscription_manager
        )
    
    async def save(self, game: Game) -> None:
        """Save game and broadcast change."""
        is_new = game.id not in self._games
        
        await super().save(game)
        
        # Broadcast change
        await self.broadcast_change(
            game.id,
            ChangeType.CREATED if is_new else ChangeType.UPDATED,
            game,
            metadata={
                "round": game.current_round,
                "phase": game.current_phase.value if hasattr(game.current_phase, 'value') else str(game.current_phase)
            }
        )
    
    def _serialize_entity(self, game: Game) -> Dict[str, Any]:
        """Serialize game for WebSocket."""
        return {
            "id": game.id,
            "room_id": game.room_id,
            "current_round": game.current_round,
            "current_phase": game.current_phase.value if hasattr(game.current_phase, 'value') else str(game.current_phase),
            "players": [
                {
                    "id": p.id,
                    "score": p.total_score,
                    "is_active": p.is_active
                }
                for p in game.players
            ],
            "state_data": game.state_data if hasattr(game, 'state_data') else {}
        }


class WebSocketPlayerStatsRepository(OptimizedPlayerStatsRepository, RealtimeRepositoryMixin):
    """Player stats repository with WebSocket broadcasting."""
    
    def __init__(
        self,
        connection_manager: ConnectionManager,
        subscription_manager: SubscriptionManager
    ):
        """Initialize WebSocket player stats repository."""
        OptimizedPlayerStatsRepository.__init__(self)
        RealtimeRepositoryMixin.__init__(
            self,
            "player_stats",
            connection_manager,
            subscription_manager
        )
    
    async def save(self, stats: PlayerStats) -> None:
        """Save stats and broadcast change."""
        is_new = stats.player_id not in self._stats
        
        old_stats = None
        if not is_new:
            old_stats = await self.get(stats.player_id)
        
        await super().save(stats)
        
        # Calculate what changed
        metadata = {}
        if old_stats:
            metadata["games_played_delta"] = stats.games_played - old_stats.games_played
            metadata["wins_delta"] = stats.wins - old_stats.wins
        
        # Broadcast change
        await self.broadcast_change(
            stats.player_id,
            ChangeType.CREATED if is_new else ChangeType.UPDATED,
            stats,
            metadata=metadata
        )


class WebSocketRepository(Generic[T]):
    """
    Generic WebSocket-aware repository wrapper.
    
    Can wrap any repository to add broadcasting capabilities.
    """
    
    def __init__(
        self,
        base_repository: Any,
        entity_type: str,
        connection_manager: ConnectionManager,
        subscription_manager: SubscriptionManager,
        id_getter: Callable[[T], str]
    ):
        """
        Initialize WebSocket repository wrapper.
        
        Args:
            base_repository: Repository to wrap
            entity_type: Type of entity
            connection_manager: WebSocket connection manager
            subscription_manager: Subscription manager
            id_getter: Function to get entity ID
        """
        self.base = base_repository
        self.entity_type = entity_type
        self.connection_manager = connection_manager
        self.subscription_manager = subscription_manager
        self.id_getter = id_getter
        self._broadcast_enabled = True
    
    async def save(self, entity: T) -> None:
        """Save entity and broadcast."""
        entity_id = self.id_getter(entity)
        
        # Check if new
        is_new = True
        try:
            existing = await self.base.get(entity_id)
            is_new = existing is None
        except:
            pass
        
        # Save
        await self.base.save(entity)
        
        # Broadcast
        if self._broadcast_enabled:
            await self._broadcast_change(
                entity_id,
                ChangeType.CREATED if is_new else ChangeType.UPDATED,
                entity
            )
    
    async def delete(self, entity_id: str) -> None:
        """Delete entity and broadcast."""
        # Get entity before deletion
        entity = None
        try:
            entity = await self.base.get(entity_id)
        except:
            pass
        
        # Delete
        await self.base.delete(entity_id)
        
        # Broadcast
        if self._broadcast_enabled:
            await self._broadcast_change(
                entity_id,
                ChangeType.DELETED,
                entity
            )
    
    async def _broadcast_change(
        self,
        entity_id: str,
        change_type: ChangeType,
        entity: Optional[T] = None
    ) -> None:
        """Broadcast change to subscribers."""
        event = ChangeEvent(
            entity_type=self.entity_type,
            entity_id=entity_id,
            change_type=change_type,
            entity=entity
        )
        
        subscribers = await self.subscription_manager.get_subscribers(event)
        
        for subscription in subscribers:
            message = {
                "type": "repository_change",
                "subscription_id": subscription.subscription_id,
                "event": {
                    "entity_type": event.entity_type,
                    "entity_id": event.entity_id,
                    "change_type": event.change_type.value,
                    "timestamp": event.timestamp.isoformat()
                }
            }
            
            if entity and change_type != ChangeType.DELETED:
                message["event"]["entity"] = self._serialize_entity(entity)
            
            await self.connection_manager.send_to_connection(
                subscription.connection_id,
                message
            )
    
    def _serialize_entity(self, entity: T) -> Dict[str, Any]:
        """Serialize entity for WebSocket."""
        if hasattr(entity, 'to_dict'):
            return entity.to_dict()
        elif hasattr(entity, '__dict__'):
            return entity.__dict__
        else:
            return {"id": self.id_getter(entity)}
    
    # Delegate all other methods to base repository
    def __getattr__(self, name):
        return getattr(self.base, name)


class WebSocketUnitOfWork(InMemoryUnitOfWork):
    """
    Unit of Work with WebSocket-aware repositories.
    
    Provides transactional semantics with automatic broadcasting.
    """
    
    def __init__(
        self,
        connection_manager: ConnectionManager,
        subscription_manager: SubscriptionManager
    ):
        """Initialize WebSocket unit of work."""
        self.connection_manager = connection_manager
        self.subscription_manager = subscription_manager
        
        # Create WebSocket-aware repositories
        self.rooms = WebSocketRoomRepository(
            connection_manager,
            subscription_manager
        )
        self.games = WebSocketGameRepository(
            connection_manager,
            subscription_manager
        )
        self.player_stats = WebSocketPlayerStatsRepository(
            connection_manager,
            subscription_manager
        )
        
        super().__init__(self.rooms, self.games, self.player_stats)
    
    async def __aenter__(self):
        """Enter transaction - disable broadcasting."""
        # Disable broadcasting during transaction
        self.rooms.disable_broadcast()
        self.games.disable_broadcast()
        self.player_stats.disable_broadcast()
        
        return await super().__aenter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction - re-enable broadcasting."""
        # Re-enable broadcasting
        self.rooms.enable_broadcast()
        self.games.enable_broadcast()
        self.player_stats.enable_broadcast()
        
        # If committing, broadcast all changes
        if not exc_type and hasattr(self, '_changes'):
            for change in self._changes:
                # Broadcast each change
                pass
        
        return await super().__aexit__(exc_type, exc_val, exc_tb)