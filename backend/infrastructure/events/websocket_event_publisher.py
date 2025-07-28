"""
WebSocket-based implementation of the EventPublisher interface.

This publisher converts domain events into WebSocket messages and
broadcasts them to connected clients.
"""

from typing import List, Dict, Any
from domain.interfaces.events import EventPublisher
from domain.events.base import DomainEvent
import logging

logger = logging.getLogger(__name__)


class WebSocketEventPublisher(EventPublisher):
    """Publishes domain events via WebSocket broadcasts."""
    
    def __init__(self):
        """Initialize the publisher."""
        self._event_mappings = self._create_event_mappings()
    
    def _create_event_mappings(self) -> Dict[str, str]:
        """
        Create mappings from domain event types to WebSocket event names.
        
        Returns:
            Dictionary mapping domain event class names to WebSocket events
        """
        return {
            # Game events
            "GameStarted": "game_started",
            "GameEnded": "game_ended",
            "RoundStarted": "round_started",
            "RoundCompleted": "round_completed",
            "PhaseChanged": "phase_change",
            "TurnStarted": "turn_started",
            "TurnCompleted": "turn_completed",
            "TurnWinnerDetermined": "turn_winner",
            "PiecesDealt": "pieces_dealt",
            "WeakHandDetected": "weak_hand_detected",
            "RedealExecuted": "redeal_executed",
            
            # Player events
            "PlayerHandUpdated": "hand_updated",
            "PlayerDeclaredPiles": "declaration_made",
            "PlayerCapturedPiles": "piles_captured",
            "PlayerScoreUpdated": "score_updated",
            "PlayerStatUpdated": "stat_updated",
            
            # Room events (if we add them)
            "RoomCreated": "room_created",
            "PlayerJoined": "player_joined",
            "PlayerLeft": "player_left",
            "HostMigrated": "host_migrated"
        }
    
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish a single domain event.
        
        Converts the domain event to a WebSocket message and broadcasts it.
        
        Args:
            event: Domain event to publish
        """
        try:
            # Get WebSocket event name
            event_type = event.__class__.__name__
            ws_event_name = self._event_mappings.get(
                event_type,
                event_type.lower()  # Default to lowercase class name
            )
            
            # Convert event to WebSocket format
            event_data = event.to_dict()
            
            # Extract room_id from event data
            room_id = event_data.get("room_id")
            if not room_id:
                logger.warning(f"Event {event_type} missing room_id")
                return
            
            # Prepare WebSocket message
            ws_message = {
                "event": ws_event_name,
                "data": {
                    **event_data,
                    "event_id": event_data.get("event_id"),
                    "timestamp": event_data.get("timestamp")
                }
            }
            
            # Broadcast to room
            from infrastructure.websocket.connection_singleton import broadcast
            await broadcast(room_id, ws_event_name, ws_message["data"])
            
            logger.debug(f"Published {event_type} as {ws_event_name} to room {room_id}")
            
        except Exception as e:
            logger.error(f"Error publishing event {event}: {e}")
            # Don't raise - event publishing should not break the flow
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """
        Publish multiple events as a batch.
        
        Args:
            events: List of domain events to publish
        """
        # For WebSocket, we publish each event individually
        # A more sophisticated implementation might batch them
        for event in events:
            await self.publish(event)