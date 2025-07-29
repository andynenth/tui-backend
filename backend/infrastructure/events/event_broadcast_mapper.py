"""
Event to broadcast mapping system.

This module provides a centralized mapping between domain events
and their corresponding WebSocket broadcast formats, ensuring
100% compatibility with the existing frontend.
"""

from typing import Dict, Any, Callable, Optional, Type
from dataclasses import dataclass
from domain.events.base import DomainEvent


@dataclass
class BroadcastMapping:
    """Defines how a domain event maps to a WebSocket broadcast."""
    event_name: str  # The WebSocket event name (e.g., "room_update")
    target_type: str  # "room", "player", "lobby", or "response"
    data_mapper: Callable[[DomainEvent, Optional[Dict[str, Any]]], Dict[str, Any]]
    requires_state: bool = False  # Whether room/game state is needed


# Alias for backward compatibility
BroadcastInfo = BroadcastMapping


class EventBroadcastMapper:
    """
    Central registry for event-to-broadcast mappings.
    
    This ensures consistent conversion from domain events to WebSocket messages.
    """
    
    def __init__(self):
        self._mappings: Dict[Type[DomainEvent], BroadcastMapping] = {}
    
    def register(
        self,
        event_type: Type[DomainEvent],
        websocket_event: str,
        target_type: str,
        data_mapper: Callable,
        requires_state: bool = False
    ):
        """Register a mapping for an event type."""
        self._mappings[event_type] = BroadcastMapping(
            event_name=websocket_event,
            target_type=target_type,
            data_mapper=data_mapper,
            requires_state=requires_state
        )
    
    def get_mapping(self, event_type: Type[DomainEvent]) -> Optional[BroadcastMapping]:
        """Get the broadcast mapping for an event type."""
        return self._mappings.get(event_type)
    
    def map_event(
        self,
        event: DomainEvent,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Map a domain event to broadcast format.
        
        Returns:
            Dict with keys: event_name, target_type, target_id, data
            or None if no mapping exists
        """
        mapping = self.get_mapping(type(event))
        if not mapping:
            return None
        
        # Get the data for the broadcast
        data = mapping.data_mapper(event, context)
        
        # Determine target ID based on event type
        target_id = None
        if hasattr(event, 'room_id'):
            target_id = event.room_id
        elif hasattr(event, 'player_id') and mapping.target_type == "player":
            target_id = event.player_id
        elif mapping.target_type == "lobby":
            target_id = "lobby"
        
        return {
            "event_name": mapping.event_name,
            "target_type": mapping.target_type,
            "target_id": target_id,
            "data": data
        }


# Create the global mapper instance
event_broadcast_mapper = EventBroadcastMapper()


# Define all the mapping functions

def map_room_update(event: DomainEvent, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Map room events to room_update broadcast."""
    if not context or 'room_state' not in context:
        # Return minimal data if no context
        return {
            "room_id": event.room_id if hasattr(event, 'room_id') else None,
            "players": [],
            "host_name": None,
            "started": False
        }
    
    return context['room_state']


def map_phase_change(event: 'PhaseChanged', context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Map phase change event to broadcast format."""
    return {
        "phase": event.new_phase,
        "previous_phase": event.old_phase,
        "phase_data": event.phase_data
    }


def map_game_started(event: 'GameStarted', context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Map game started event."""
    return {
        "round_number": event.round_number,
        "players": event.player_names
    }


def map_turn_played(event: 'PiecesPlayed', context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Map pieces played event."""
    # Calculate remaining pieces (8 pieces per round minus played)
    remaining = 8
    if context and 'pieces_played_count' in context:
        remaining = 8 - context['pieces_played_count']
    
    return {
        "player": event.player_name,
        "pieces": event.pieces,
        "pieces_remaining": remaining
    }


def map_declaration(event: 'DeclarationMade', context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Map declaration event."""
    return {
        "player": event.player_name,
        "value": event.declared_count
    }


def map_score_update(event: 'ScoresCalculated', context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Map scores calculated event."""
    return {
        "round_number": event.round_number,
        "round_scores": event.round_scores,
        "total_scores": event.total_scores,
        "declarations": event.declarations,
        "actual_piles": event.actual_piles
    }


def map_error(event: 'InvalidActionAttempted', context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Map invalid action to error broadcast."""
    return {
        "message": event.reason,
        "type": event.action_type,
        "details": event.details or {}
    }


def map_pong(event: 'ConnectionHeartbeat', context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Map heartbeat to pong response."""
    data = {
        "timestamp": event.client_timestamp,
        "server_time": event.server_timestamp
    }
    
    # Add room_id if available in context
    if context and 'room_id' in context:
        data['room_id'] = context['room_id']
    
    return data


def map_room_created(event: 'RoomCreated', context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Map room created event to response."""
    return {
        "room_id": event.room_id,
        "host_name": event.host_name,
        "success": True
    }


def map_room_list(event: 'RoomListUpdated', context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Map room list update."""
    return {
        "rooms": event.rooms,
        "reason": event.reason
    }


# Register all mappings
def register_all_mappings():
    """Register all event-to-broadcast mappings."""
    from domain.events.all_events import (
        # Room events
        RoomCreated, PlayerJoinedRoom, PlayerLeftRoom, HostChanged,
        BotAdded, PlayerRemoved,
        # Game events
        GameStarted, PhaseChanged, PiecesPlayed, DeclarationMade,
        TurnCompleted, TurnWinnerDetermined,
        # Scoring events
        ScoresCalculated, GameEnded,
        # Connection events
        ConnectionHeartbeat,
        # Error events
        InvalidActionAttempted,
        # Lobby events
        RoomListUpdated
    )
    
    # Room management broadcasts
    event_broadcast_mapper.register(
        RoomCreated, "room_created", "response", map_room_created
    )
    event_broadcast_mapper.register(
        PlayerJoinedRoom, "room_update", "room", map_room_update, requires_state=True
    )
    event_broadcast_mapper.register(
        PlayerLeftRoom, "room_update", "room", map_room_update, requires_state=True
    )
    event_broadcast_mapper.register(
        BotAdded, "room_update", "room", map_room_update, requires_state=True
    )
    # PlayerRemoved broadcast is handled directly in the dispatcher with proper room state
    # event_broadcast_mapper.register(
    #     PlayerRemoved, "room_update", "room", map_room_update, requires_state=True
    # )
    event_broadcast_mapper.register(
        HostChanged, "host_changed", "room",
        lambda e, c: {"old_host": e.old_host_name, "new_host": e.new_host_name, "reason": e.reason}
    )
    
    # Game flow broadcasts
    event_broadcast_mapper.register(
        GameStarted, "game_started", "room", map_game_started
    )
    event_broadcast_mapper.register(
        PhaseChanged, "phase_change", "room", map_phase_change
    )
    event_broadcast_mapper.register(
        PiecesPlayed, "turn_played", "room", map_turn_played, requires_state=True
    )
    event_broadcast_mapper.register(
        DeclarationMade, "declare", "room", map_declaration
    )
    event_broadcast_mapper.register(
        TurnCompleted, "turn_complete", "room",
        lambda e, c: {"turn_number": e.turn_number, "plays": e.plays}
    )
    event_broadcast_mapper.register(
        TurnWinnerDetermined, "turn_results", "room",
        lambda e, c: {
            "winner": e.winner_name,
            "winning_play": e.winning_play,
            "all_plays": e.all_plays
        }
    )
    
    # Scoring broadcasts
    event_broadcast_mapper.register(
        ScoresCalculated, "score_update", "room", map_score_update
    )
    event_broadcast_mapper.register(
        GameEnded, "game_ended", "room",
        lambda e, c: {
            "winner": e.winner_name,
            "final_scores": e.final_scores,
            "total_rounds": e.total_rounds,
            "reason": e.end_reason
        }
    )
    
    # Connection broadcasts
    event_broadcast_mapper.register(
        ConnectionHeartbeat, "pong", "response", map_pong
    )
    
    # Error broadcasts
    event_broadcast_mapper.register(
        InvalidActionAttempted, "error", "player", map_error
    )
    
    # Lobby broadcasts
    event_broadcast_mapper.register(
        RoomListUpdated, "room_list_update", "lobby", map_room_list
    )


# Initialize mappings on import
register_all_mappings()