"""
Event-based game adapters.

These adapters publish domain events instead of directly returning responses,
enabling complete decoupling from infrastructure concerns.
"""

from typing import Dict, Any, Optional, List
import logging

# Import domain events
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.domain.events.all_events import (
    GameStarted, DeclarationMade, PiecesPlayed, RedealRequested,
    RedealDecisionMade, PlayerReadyForNext, PlayerLeftRoom,
    InvalidActionAttempted, EventMetadata
)
from backend.infrastructure.events.in_memory_event_bus import get_event_bus
from .adapter_event_config import should_adapter_use_events

logger = logging.getLogger(__name__)


class StartGameAdapterEvent:
    """Event-based adapter for starting games"""
    
    def __init__(self, room_manager=None, game_manager=None):
        """Initialize with optional dependencies"""
        self.room_manager = room_manager
        self.game_manager = game_manager
        self.event_bus = get_event_bus()
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle start_game by publishing GameStarted event.
        """
        data = message.get("data", {})
        requester = data.get("player_name")
        
        if not requester:
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            error_event = InvalidActionAttempted(
                player_id=getattr(websocket, 'player_id', str(id(websocket))),
                action="start_game",
                reason="Player name required to start game",
                metadata=metadata
            )
            await self.event_bus.publish(error_event)
            
            return {
                "event": "error",
                "data": {
                    "message": "Player name required to start game",
                    "type": "validation_error"
                }
            }
        
        # Get room ID
        room_id = None
        if room_state:
            room_id = room_state.get("room_id")
        elif hasattr(websocket, 'room_id'):
            room_id = websocket.room_id
        
        if room_id:
            # Create metadata
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            # Publish the event
            event = GameStarted(
                room_id=room_id,
                round_number=1,
                starter_player=requester,
                metadata=metadata
            )
            
            await self.event_bus.publish(event)
        
        # Still return response for compatibility
        return {
            "event": "game_started",
            "data": {
                "success": True,
                "initial_phase": "PREPARATION",
                "round_number": 1,
                "starter_player": requester
            }
        }


class DeclareAdapterEvent:
    """Event-based adapter for pile count declarations"""
    
    def __init__(self, game_manager=None):
        """Initialize with optional dependencies"""
        self.game_manager = game_manager
        self.event_bus = get_event_bus()
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle declare by publishing DeclarationMade event.
        """
        data = message.get("data", {})
        player_name = data.get("player_name")
        pile_count = data.get("pile_count")
        
        if not player_name or pile_count is None:
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            error_event = InvalidActionAttempted(
                player_id=getattr(websocket, 'player_id', str(id(websocket))),
                action="declare",
                reason="Player name and pile count required",
                metadata=metadata
            )
            await self.event_bus.publish(error_event)
            
            return {
                "event": "error",
                "data": {
                    "message": "Player name and pile count required",
                    "type": "validation_error"
                }
            }
        
        # Validate pile count
        if not isinstance(pile_count, int) or pile_count < 0 or pile_count > 8:
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            error_event = InvalidActionAttempted(
                player_id=getattr(websocket, 'player_id', str(id(websocket))),
                action="declare",
                reason="Pile count must be between 0 and 8",
                metadata=metadata
            )
            await self.event_bus.publish(error_event)
            
            return {
                "event": "error",
                "data": {
                    "message": "Pile count must be between 0 and 8",
                    "type": "validation_error"
                }
            }
        
        # Get room ID
        room_id = None
        if room_state:
            room_id = room_state.get("room_id")
        elif hasattr(websocket, 'room_id'):
            room_id = websocket.room_id
        
        if room_id:
            # Create metadata
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            # Publish the event
            event = DeclarationMade(
                room_id=room_id,
                player_name=player_name,
                pile_count=pile_count,
                metadata=metadata
            )
            
            await self.event_bus.publish(event)
        
        # Still return response for compatibility
        return {
            "event": "declaration_made",
            "data": {
                "player_name": player_name,
                "pile_count": pile_count,
                "success": True
            }
        }


class PlayAdapterEvent:
    """Event-based adapter for playing pieces"""
    
    def __init__(self, game_manager=None):
        """Initialize with optional dependencies"""
        self.game_manager = game_manager
        self.event_bus = get_event_bus()
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle play/play_pieces by publishing PiecesPlayed event.
        """
        data = message.get("data", {})
        player_name = data.get("player_name")
        pieces = data.get("pieces", [])
        
        if not player_name:
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            error_event = InvalidActionAttempted(
                player_id=getattr(websocket, 'player_id', str(id(websocket))),
                action="play",
                reason="Player name required",
                metadata=metadata
            )
            await self.event_bus.publish(error_event)
            
            return {
                "event": "error",
                "data": {
                    "message": "Player name required",
                    "type": "validation_error"
                }
            }
        
        if not pieces or not isinstance(pieces, list):
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            error_event = InvalidActionAttempted(
                player_id=getattr(websocket, 'player_id', str(id(websocket))),
                action="play",
                reason="Pieces list required",
                metadata=metadata
            )
            await self.event_bus.publish(error_event)
            
            return {
                "event": "error",
                "data": {
                    "message": "Pieces list required",
                    "type": "validation_error"
                }
            }
        
        # Basic validation
        if len(pieces) < 1 or len(pieces) > 6:
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            error_event = InvalidActionAttempted(
                player_id=getattr(websocket, 'player_id', str(id(websocket))),
                action="play",
                reason="Must play between 1 and 6 pieces",
                metadata=metadata
            )
            await self.event_bus.publish(error_event)
            
            return {
                "event": "error",
                "data": {
                    "message": "Must play between 1 and 6 pieces",
                    "type": "validation_error"
                }
            }
        
        # Get room ID
        room_id = None
        if room_state:
            room_id = room_state.get("room_id")
        elif hasattr(websocket, 'room_id'):
            room_id = websocket.room_id
        
        if room_id:
            # Create metadata
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            # Publish the event
            event = PiecesPlayed(
                room_id=room_id,
                player_name=player_name,
                pieces=pieces,
                metadata=metadata
            )
            
            await self.event_bus.publish(event)
        
        # Still return response for compatibility
        return {
            "event": "play_made",
            "data": {
                "player_name": player_name,
                "pieces_played": pieces,
                "pieces_count": len(pieces),
                "success": True,
                "next_player": "NextPlayer",  # Would be determined by game logic
                "winner": None  # Or player name if they won this turn
            }
        }


class RequestRedealAdapterEvent:
    """Event-based adapter for requesting redeals"""
    
    def __init__(self, game_manager=None):
        """Initialize with optional dependencies"""
        self.game_manager = game_manager
        self.event_bus = get_event_bus()
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle request_redeal by publishing RedealRequested event.
        """
        data = message.get("data", {})
        player_name = data.get("player_name")
        
        if not player_name:
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            error_event = InvalidActionAttempted(
                player_id=getattr(websocket, 'player_id', str(id(websocket))),
                action="request_redeal",
                reason="Player name required",
                metadata=metadata
            )
            await self.event_bus.publish(error_event)
            
            return {
                "event": "error",
                "data": {
                    "message": "Player name required",
                    "type": "validation_error"
                }
            }
        
        # Get room ID
        room_id = None
        if room_state:
            room_id = room_state.get("room_id")
        elif hasattr(websocket, 'room_id'):
            room_id = websocket.room_id
        
        if room_id:
            # Create metadata
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            # Publish the event
            event = RedealRequested(
                room_id=room_id,
                player_name=player_name,
                reason="weak_hand",
                metadata=metadata
            )
            
            await self.event_bus.publish(event)
        
        # Still return response for compatibility
        return {
            "event": "redeal_requested",
            "data": {
                "requesting_player": player_name,
                "reason": "weak_hand",
                "waiting_for_players": ["Player2", "Player3", "Player4"]
            }
        }


class AcceptRedealAdapterEvent:
    """Event-based adapter for accepting redeals"""
    
    def __init__(self, game_manager=None):
        """Initialize with optional dependencies"""
        self.game_manager = game_manager
        self.event_bus = get_event_bus()
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle accept_redeal by publishing RedealAccepted event.
        """
        data = message.get("data", {})
        player_name = data.get("player_name")
        
        if not player_name:
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            error_event = InvalidActionAttempted(
                player_id=getattr(websocket, 'player_id', str(id(websocket))),
                action="accept_redeal",
                reason="Player name required",
                metadata=metadata
            )
            await self.event_bus.publish(error_event)
            
            return {
                "event": "error",
                "data": {
                    "message": "Player name required",
                    "type": "validation_error"
                }
            }
        
        # Get room ID
        room_id = None
        if room_state:
            room_id = room_state.get("room_id")
        elif hasattr(websocket, 'room_id'):
            room_id = websocket.room_id
        
        if room_id:
            # Create metadata
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            # Publish the event
            event = RedealAccepted(
                room_id=room_id,
                player_name=player_name,
                metadata=metadata
            )
            
            await self.event_bus.publish(event)
        
        # Still return response for compatibility
        return {
            "event": "redeal_vote_cast",
            "data": {
                "player_name": player_name,
                "vote": "accept",
                "votes_remaining": 2  # Would track actual votes
            }
        }


class DeclineRedealAdapterEvent:
    """Event-based adapter for declining redeals"""
    
    def __init__(self, game_manager=None):
        """Initialize with optional dependencies"""
        self.game_manager = game_manager
        self.event_bus = get_event_bus()
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle decline_redeal by publishing RedealDeclined event.
        """
        data = message.get("data", {})
        player_name = data.get("player_name")
        
        if not player_name:
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            error_event = InvalidActionAttempted(
                player_id=getattr(websocket, 'player_id', str(id(websocket))),
                action="decline_redeal",
                reason="Player name required",
                metadata=metadata
            )
            await self.event_bus.publish(error_event)
            
            return {
                "event": "error",
                "data": {
                    "message": "Player name required",
                    "type": "validation_error"
                }
            }
        
        # Get room ID
        room_id = None
        if room_state:
            room_id = room_state.get("room_id")
        elif hasattr(websocket, 'room_id'):
            room_id = websocket.room_id
        
        if room_id:
            # Create metadata
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            # Publish the event
            event = RedealDeclined(
                room_id=room_id,
                player_name=player_name,
                metadata=metadata
            )
            
            await self.event_bus.publish(event)
        
        # Still return response for compatibility
        return {
            "event": "redeal_declined",
            "data": {
                "declining_player": player_name,
                "redeal_cancelled": True,
                "next_phase": "DECLARATION"
            }
        }


class PlayerReadyAdapterEvent:
    """Event-based adapter for player ready status"""
    
    def __init__(self, room_manager=None):
        """Initialize with optional dependencies"""
        self.room_manager = room_manager
        self.event_bus = get_event_bus()
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle player_ready by publishing PlayerReadyForNext event.
        """
        data = message.get("data", {})
        player_name = data.get("player_name")
        ready = data.get("ready", True)
        
        if not player_name:
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            error_event = InvalidActionAttempted(
                player_id=getattr(websocket, 'player_id', str(id(websocket))),
                action="player_ready",
                reason="Player name required",
                metadata=metadata
            )
            await self.event_bus.publish(error_event)
            
            return {
                "event": "error",
                "data": {
                    "message": "Player name required",
                    "type": "validation_error"
                }
            }
        
        # Get room ID
        room_id = None
        if room_state:
            room_id = room_state.get("room_id")
        elif hasattr(websocket, 'room_id'):
            room_id = websocket.room_id
        
        if room_id:
            # Create metadata
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            # Publish the event
            event = PlayerReadyForNext(
                room_id=room_id,
                player_id=getattr(websocket, 'player_id', str(id(websocket))),
                player_name=player_name,
                current_phase=room_state.get("game_state", {}).get("phase", "UNKNOWN") if room_state else "UNKNOWN",
                metadata=metadata
            )
            
            await self.event_bus.publish(event)
        
        # Still return response for compatibility
        return {
            "event": "player_ready_update",
            "data": {
                "player_name": player_name,
                "ready": ready,
                "all_ready": False  # Would check actual state
            }
        }


# Factory functions to get the appropriate adapter based on config
def get_start_game_adapter(room_manager=None, game_manager=None):
    """Get start game adapter based on feature flag."""
    if should_adapter_use_events("start_game"):
        return StartGameAdapterEvent(room_manager, game_manager)
    else:
        from .game_adapters import _handle_start_game
        return _handle_start_game


def get_declare_adapter(game_manager=None):
    """Get declare adapter based on feature flag."""
    if should_adapter_use_events("declare"):
        return DeclareAdapterEvent(game_manager)
    else:
        from .game_adapters import _handle_declare
        return _handle_declare


def get_play_adapter(game_manager=None):
    """Get play adapter based on feature flag."""
    if should_adapter_use_events("play"):
        return PlayAdapterEvent(game_manager)
    else:
        from .game_adapters import _handle_play
        return _handle_play


def get_request_redeal_adapter(game_manager=None):
    """Get request redeal adapter based on feature flag."""
    if should_adapter_use_events("request_redeal"):
        return RequestRedealAdapterEvent(game_manager)
    else:
        from .game_adapters import _handle_request_redeal
        return _handle_request_redeal


def get_accept_redeal_adapter(game_manager=None):
    """Get accept redeal adapter based on feature flag."""
    if should_adapter_use_events("accept_redeal"):
        return AcceptRedealAdapterEvent(game_manager)
    else:
        from .game_adapters import _handle_accept_redeal
        return _handle_accept_redeal


def get_decline_redeal_adapter(game_manager=None):
    """Get decline redeal adapter based on feature flag."""
    if should_adapter_use_events("decline_redeal"):
        return DeclineRedealAdapterEvent(game_manager)
    else:
        from .game_adapters import _handle_decline_redeal
        return _handle_decline_redeal


def get_player_ready_adapter(room_manager=None):
    """Get player ready adapter based on feature flag."""
    if should_adapter_use_events("player_ready"):
        return PlayerReadyAdapterEvent(room_manager)
    else:
        from .game_adapters import _handle_player_ready
        return _handle_player_ready