"""
Application layer event publisher implementation.

This module provides the concrete implementation of the EventPublisher
interface that integrates with the existing WebSocket infrastructure.
"""

import logging
from typing import Optional, Dict, Any
import asyncio

from application.interfaces import EventPublisher
from backend.domain.events.base import DomainEvent
from backend.infrastructure.events.event_broadcast_mapper import event_broadcast_mapper
from infrastructure.feature_flags import get_feature_flags
from socket_manager import broadcast

logger = logging.getLogger(__name__)


class WebSocketEventPublisher(EventPublisher):
    """
    Event publisher that broadcasts domain events via WebSocket.
    
    This implementation converts domain events to WebSocket messages
    and broadcasts them to connected clients.
    """
    
    def __init__(self):
        """Initialize the event publisher."""
        self._feature_flags = get_feature_flags()
        self._published_count = 0
        self._error_count = 0
        
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish a domain event.
        
        Args:
            event: The domain event to publish
        """
        try:
            # Check if event broadcasting is enabled
            if not self._feature_flags.is_enabled(
                self._feature_flags.USE_DOMAIN_EVENTS,
                {'event_type': event.event_type}
            ):
                logger.debug(f"Event broadcasting disabled for {event.event_type}")
                return
            
            # Get broadcast mapping for the event
            broadcast_info = event_broadcast_mapper.map_event(event)
            
            if not broadcast_info:
                logger.debug(f"No broadcast mapping for event {event.event_type}")
                return
            
            # Extract broadcast details
            event_name = broadcast_info['event_name']
            target_type = broadcast_info['target_type']
            target_id = broadcast_info['target_id']
            data = broadcast_info['data']
            
            # Log if enabled
            if self._feature_flags.is_enabled(self._feature_flags.LOG_ADAPTER_CALLS):
                logger.info(
                    f"Publishing event {event.event_type} as {event_name} "
                    f"to {target_type}:{target_id}"
                )
            
            # Broadcast based on target type
            if target_type == "room" and target_id:
                await broadcast(target_id, event_name, data)
            elif target_type == "player" and target_id:
                # Would need player-specific broadcast
                await self._broadcast_to_player(target_id, event_name, data)
            elif target_type == "lobby":
                await broadcast("lobby", event_name, data)
            elif target_type == "response":
                # Response events are handled differently
                logger.debug(f"Response event {event_name} not broadcast")
            else:
                logger.warning(
                    f"Unknown target type {target_type} for event {event.event_type}"
                )
            
            self._published_count += 1
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"Failed to publish event {event.event_type}: {e}")
            # Don't raise - event publishing should not break business logic
    
    async def _broadcast_to_player(
        self,
        player_id: str,
        event_name: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Broadcast an event to a specific player.
        
        Args:
            player_id: The player to broadcast to
            event_name: The WebSocket event name
            data: The event data
        """
        # This would need integration with socket manager
        # to find player's connection and send directly
        logger.debug(
            f"Player-specific broadcast not yet implemented: "
            f"{event_name} to {player_id}"
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get publisher statistics."""
        return {
            'published_count': self._published_count,
            'error_count': self._error_count,
            'error_rate': (
                self._error_count / max(self._published_count, 1)
            )
        }


class CompositeEventPublisher(EventPublisher):
    """
    Event publisher that delegates to multiple publishers.
    
    Useful for publishing to multiple systems (e.g., WebSocket and event store).
    """
    
    def __init__(self, publishers: list[EventPublisher]):
        """
        Initialize with a list of publishers.
        
        Args:
            publishers: List of event publishers to delegate to
        """
        self._publishers = publishers
        
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish event to all configured publishers.
        
        Args:
            event: The domain event to publish
        """
        # Publish to all publishers concurrently
        tasks = [
            publisher.publish(event)
            for publisher in self._publishers
        ]
        
        # Wait for all to complete, but don't fail if some error
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Publisher {i} failed for event {event.event_type}: {result}"
                )


class EventStorePublisher(EventPublisher):
    """
    Event publisher that stores events in the event store.
    
    This provides event sourcing capabilities.
    """
    
    def __init__(self, event_store):
        """
        Initialize with event store.
        
        Args:
            event_store: The event store to publish to
        """
        self._event_store = event_store
        self._feature_flags = get_feature_flags()
        
    async def publish(self, event: DomainEvent) -> None:
        """
        Store event in the event store.
        
        Args:
            event: The domain event to store
        """
        if not self._feature_flags.is_enabled(
            self._feature_flags.USE_EVENT_SOURCING
        ):
            return
        
        try:
            # Store the event
            await self._event_store.append_event(
                room_id=getattr(event, 'room_id', 'system'),
                event_type=event.event_type,
                event_data=event.to_dict(),
                player_id=getattr(event, 'player_id', None)
            )
        except Exception as e:
            logger.error(f"Failed to store event {event.event_type}: {e}")
            # Don't raise - event storage should not break business logic