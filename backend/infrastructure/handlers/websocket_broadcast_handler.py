"""
Event handler that broadcasts domain events via WebSocket.

This handler subscribes to all domain events and converts them
to WebSocket broadcasts for real-time client updates.
"""

from typing import List
from domain.interfaces.events import EventHandler
from domain.events.base import DomainEvent
from socket_manager import broadcast
import logging

logger = logging.getLogger(__name__)


class WebSocketBroadcastHandler(EventHandler):
    """
    Handles domain events by broadcasting them via WebSocket.
    
    This handler acts as a bridge between the domain layer and
    the WebSocket infrastructure, ensuring clients receive
    real-time updates when domain state changes.
    """
    
    def __init__(self):
        """Initialize the handler."""
        self._event_mappings = self._create_event_mappings()
    
    def _create_event_mappings(self) -> dict:
        """Create mappings from domain events to WebSocket events."""
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
            "PlayerStatUpdated": "stat_updated"
        }
    
    def can_handle(self, event: DomainEvent) -> bool:
        """
        Check if this handler can process the event.
        
        Args:
            event: Event to check
            
        Returns:
            True if this handler can process the event
        """
        # This handler can process any event that has a room_id
        event_data = event.to_dict()
        return "room_id" in event_data
    
    async def handle(self, event: DomainEvent) -> None:
        """
        Handle a domain event by broadcasting via WebSocket.
        
        Args:
            event: Event to handle
        """
        try:
            event_type = event.__class__.__name__
            event_data = event.to_dict()
            
            # Get room_id
            room_id = event_data.get("room_id")
            if not room_id:
                logger.warning(f"Event {event_type} missing room_id")
                return
            
            # Get WebSocket event name
            ws_event_name = self._event_mappings.get(
                event_type,
                self._camel_to_snake(event_type)
            )
            
            # Prepare broadcast data
            broadcast_data = self._prepare_broadcast_data(event_data)
            
            # Broadcast to room
            await broadcast(room_id, ws_event_name, broadcast_data)
            
            logger.debug(f"Broadcasted {event_type} as {ws_event_name} to room {room_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting event {event}: {e}")
    
    def get_event_types(self) -> List[str]:
        """
        Get list of event types this handler processes.
        
        Returns:
            List of event type names
        """
        # Return all mapped event types
        return list(self._event_mappings.keys())
    
    def _camel_to_snake(self, name: str) -> str:
        """Convert CamelCase to snake_case."""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _prepare_broadcast_data(self, event_data: dict) -> dict:
        """
        Prepare event data for broadcasting.
        
        Removes internal fields and formats for client consumption.
        
        Args:
            event_data: Raw event data
            
        Returns:
            Cleaned data for broadcasting
        """
        # Remove internal fields
        broadcast_data = {
            k: v for k, v in event_data.items()
            if not k.startswith('_') and k not in ['event_id', 'timestamp']
        }
        
        # Add metadata
        broadcast_data['timestamp'] = event_data.get('timestamp')
        
        return broadcast_data