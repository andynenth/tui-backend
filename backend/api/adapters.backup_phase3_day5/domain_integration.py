"""
Domain integration module.

This module wires together the domain layer with infrastructure,
providing a clean way to use domain-driven adapters in the WebSocket API.
"""

from typing import Dict, Any, Optional
import logging

# Domain imports
from domain.interfaces.repositories import RoomRepository
from domain.interfaces.events import EventPublisher

# Infrastructure imports
from infrastructure.repositories import InMemoryRoomRepository
from infrastructure.events import InMemoryEventBus, get_event_bus
from infrastructure.handlers import WebSocketBroadcastHandler

# Adapter imports
from .game_adapters_domain import DomainGameAdapter

logger = logging.getLogger(__name__)


class DomainIntegration:
    """
    Central integration point for domain-driven adapters.
    
    This class sets up all the infrastructure needed to use
    the domain layer in the WebSocket API.
    """
    
    def __init__(self):
        """Initialize domain integration."""
        # Set up repositories
        self.room_repository: RoomRepository = InMemoryRoomRepository()
        
        # Set up event bus
        self.event_bus = get_event_bus()
        
        # Set up WebSocket broadcast handler
        self.ws_handler = WebSocketBroadcastHandler()
        self.event_bus.register_global_handler(self.ws_handler)
        
        # Set up domain adapters
        self.game_adapter = DomainGameAdapter(
            room_repository=self.room_repository,
            event_publisher=self.event_bus
        )
        
        # Track if we're enabled
        self._enabled = False
        
        logger.info("Domain integration initialized")
    
    def enable(self):
        """Enable domain integration."""
        self._enabled = True
        logger.info("Domain integration enabled")
    
    def disable(self):
        """Disable domain integration."""
        self._enabled = False
        logger.info("Domain integration disabled")
    
    @property
    def enabled(self) -> bool:
        """Check if domain integration is enabled."""
        return self._enabled
    
    async def handle_message(
        self,
        websocket,
        message: Dict[str, Any],
        room_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Handle a WebSocket message using domain adapters.
        
        Args:
            websocket: WebSocket connection
            message: Incoming message
            room_id: Current room ID
            
        Returns:
            Response if handled, None otherwise
        """
        if not self._enabled:
            return None
        
        event = message.get("event")
        
        # Route to appropriate domain adapter
        if event == "start_game":
            return await self.game_adapter.handle_start_game(
                websocket, message, room_id
            )
        elif event == "declare":
            return await self.game_adapter.handle_declare(
                websocket, message, room_id
            )
        elif event in ["play", "play_pieces"]:
            return await self.game_adapter.handle_play(
                websocket, message, room_id
            )
        elif event == "request_redeal":
            return await self.game_adapter.handle_redeal_request(
                websocket, message, room_id
            )
        elif event in ["accept_redeal", "decline_redeal", "redeal_decision"]:
            return await self.game_adapter.handle_redeal_decision(
                websocket, message, room_id
            )
        
        # Not handled by domain adapters
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of domain integration.
        
        Returns:
            Status information
        """
        return {
            "enabled": self._enabled,
            "repositories": {
                "room": self.room_repository.__class__.__name__
            },
            "event_bus": {
                "type": self.event_bus.__class__.__name__,
                "handlers": len(self.event_bus._global_handlers)
            },
            "adapters": {
                "game": "DomainGameAdapter"
            }
        }


# Singleton instance
_domain_integration: Optional[DomainIntegration] = None


def get_domain_integration() -> DomainIntegration:
    """
    Get the singleton domain integration instance.
    
    Returns:
        The domain integration instance
    """
    global _domain_integration
    if _domain_integration is None:
        _domain_integration = DomainIntegration()
    return _domain_integration