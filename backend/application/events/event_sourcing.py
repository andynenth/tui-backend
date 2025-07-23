# application/events/event_sourcing.py
"""
Event sourcing capabilities for the application.
"""

import logging
from typing import List, Dict, Any, Optional, Type, TypeVar
from datetime import datetime
from dataclasses import dataclass

from domain.events.base import DomainEvent, AggregateEvent
from domain.interfaces.event_publisher import EventStore

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class EventSnapshot:
    """Represents a snapshot of an aggregate at a point in time."""
    aggregate_id: str
    aggregate_type: str
    version: int
    data: Dict[str, Any]
    timestamp: datetime


class EventSourcedRepository:
    """
    Base repository for event-sourced aggregates.
    
    This repository loads and saves aggregates by replaying events.
    """
    
    def __init__(self, event_store: EventStore):
        """Initialize with event store."""
        self._event_store = event_store
    
    async def load(self, aggregate_id: str, aggregate_type: Type[T]) -> Optional[T]:
        """
        Load an aggregate by replaying its events.
        
        Args:
            aggregate_id: ID of the aggregate
            aggregate_type: Type of aggregate to create
            
        Returns:
            Loaded aggregate or None if not found
        """
        events = await self._event_store.get_events(aggregate_id)
        
        if not events:
            return None
        
        # Create new instance
        aggregate = aggregate_type()
        
        # Replay events
        for event in events:
            self._apply_event(aggregate, event)
        
        return aggregate
    
    async def save(self, aggregate: Any, new_events: List[DomainEvent]) -> None:
        """
        Save an aggregate by storing its new events.
        
        Args:
            aggregate: The aggregate to save
            new_events: New events to store
        """
        for event in new_events:
            await self._event_store.append(event)
    
    def _apply_event(self, aggregate: Any, event: DomainEvent) -> None:
        """
        Apply an event to an aggregate.
        
        Override this in subclasses to handle specific event types.
        """
        # Look for handler method
        handler_name = f'_handle_{event.__class__.__name__}'
        handler = getattr(aggregate, handler_name, None)
        
        if handler:
            handler(event)
        else:
            logger.warning(
                f"No handler found for event {event.__class__.__name__} "
                f"on aggregate {aggregate.__class__.__name__}"
            )


class EventProjector:
    """
    Projects events into read models.
    
    Use this to build query-optimized views from events.
    """
    
    def __init__(self):
        """Initialize projector."""
        self._projections: Dict[str, Any] = {}
    
    async def project(self, event: DomainEvent) -> None:
        """
        Project an event into read models.
        
        Override this in subclasses to handle specific projections.
        """
        handler_name = f'_project_{event.__class__.__name__}'
        handler = getattr(self, handler_name, None)
        
        if handler:
            await handler(event)
    
    def get_projection(self, key: str) -> Optional[Any]:
        """Get a projection by key."""
        return self._projections.get(key)


class GameEventProjector(EventProjector):
    """
    Projector for game-related events.
    
    Builds read models for game state queries.
    """
    
    def __init__(self):
        """Initialize with game projections."""
        super().__init__()
        self._projections = {
            'games_by_room': {},  # room_id -> game_state
            'active_games': set(),  # Set of active game IDs
            'player_games': {},  # player_name -> [game_ids]
            'game_scores': {},  # game_id -> {player: score}
        }
    
    async def _project_GameStartedEvent(self, event: AggregateEvent) -> None:
        """Project game started event."""
        room_id = event.aggregate_id
        
        # Create game state projection
        self._projections['games_by_room'][room_id] = {
            'room_id': room_id,
            'players': event.data['players'],
            'started_at': event.timestamp,
            'phase': event.data['initial_phase'],
            'status': 'active'
        }
        
        # Add to active games
        self._projections['active_games'].add(room_id)
        
        # Map players to game
        for player in event.data['players']:
            player_name = player['name']
            if player_name not in self._projections['player_games']:
                self._projections['player_games'][player_name] = []
            self._projections['player_games'][player_name].append(room_id)
    
    async def _project_GameEndedEvent(self, event: AggregateEvent) -> None:
        """Project game ended event."""
        room_id = event.aggregate_id
        
        # Update game state
        if room_id in self._projections['games_by_room']:
            self._projections['games_by_room'][room_id]['status'] = 'ended'
            self._projections['games_by_room'][room_id]['ended_at'] = event.timestamp
            self._projections['games_by_room'][room_id]['winner'] = event.data['winner']
            self._projections['games_by_room'][room_id]['final_scores'] = event.data['final_scores']
        
        # Remove from active games
        self._projections['active_games'].discard(room_id)
        
        # Store final scores
        self._projections['game_scores'][room_id] = event.data['final_scores']
    
    def get_active_games(self) -> List[Dict[str, Any]]:
        """Get all active games."""
        return [
            self._projections['games_by_room'][game_id]
            for game_id in self._projections['active_games']
            if game_id in self._projections['games_by_room']
        ]
    
    def get_player_games(self, player_name: str) -> List[str]:
        """Get all games for a player."""
        return self._projections['player_games'].get(player_name, [])
    
    def get_game_scores(self, room_id: str) -> Dict[str, int]:
        """Get scores for a game."""
        return self._projections['game_scores'].get(room_id, {})


class EventReplayer:
    """
    Replays events for debugging, testing, or recovery.
    """
    
    def __init__(self, event_store: EventStore):
        """Initialize with event store."""
        self._event_store = event_store
    
    async def replay_all(self, handler) -> int:
        """
        Replay all events through a handler.
        
        Args:
            handler: Function to handle each event
            
        Returns:
            Number of events replayed
        """
        events = await self._event_store.get_all_events()
        count = 0
        
        for event in events:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
                count += 1
            except Exception as e:
                logger.error(
                    f"Error replaying event {event.event_id}: {str(e)}",
                    exc_info=True
                )
        
        return count
    
    async def replay_aggregate(
        self,
        aggregate_id: str,
        handler,
        after_version: int = 0
    ) -> int:
        """
        Replay events for a specific aggregate.
        
        Args:
            aggregate_id: ID of aggregate to replay
            handler: Function to handle each event
            after_version: Only replay events after this version
            
        Returns:
            Number of events replayed
        """
        events = await self._event_store.get_events(aggregate_id, after_version)
        count = 0
        
        for event in events:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
                count += 1
            except Exception as e:
                logger.error(
                    f"Error replaying event {event.event_id}: {str(e)}",
                    exc_info=True
                )
        
        return count


import asyncio