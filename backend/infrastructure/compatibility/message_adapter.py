# infrastructure/compatibility/message_adapter.py
"""
Adapts between new event format and legacy WebSocket message format.
"""

import logging
from typing import Dict, Any, Optional

from domain.events.base import DomainEvent
from domain.events.game_events import (
    GameStartedEvent,
    RoundStartedEvent,
    TurnPlayedEvent,
    PhaseChangedEvent,
    PlayerDeclaredEvent,
    RoundEndedEvent,
    GameEndedEvent,
    WeakHandRequestedEvent,
    RedealAcceptedEvent,
    RedealDeclinedEvent
)
from domain.events.player_events import (
    PlayerJoinedEvent,
    PlayerLeftEvent,
    PlayerReadyEvent,
    HostTransferredEvent
)

logger = logging.getLogger(__name__)


class MessageAdapter:
    """
    Ensures backward compatibility by adapting new event formats
    to legacy WebSocket message formats expected by the frontend.
    """
    
    @staticmethod
    def adapt_event(event: DomainEvent) -> Optional[Dict[str, Any]]:
        """
        Adapt a domain event to legacy message format.
        
        Args:
            event: Domain event to adapt
            
        Returns:
            Legacy format message or None if no adapter found
        """
        adapter_method = getattr(
            MessageAdapter,
            f'_adapt_{event.__class__.__name__}',
            None
        )
        
        if adapter_method:
            return adapter_method(event)
        else:
            logger.warning(f"No adapter for event type: {event.__class__.__name__}")
            return None
    
    @staticmethod
    def _adapt_GameStartedEvent(event: GameStartedEvent) -> Dict[str, Any]:
        """Adapt GameStartedEvent to legacy format."""
        return {
            "type": "game_started",
            "room_id": event.aggregate_id,
            "players": event.data["players"],
            "phase": event.data["initial_phase"],
            # Legacy fields
            "game_id": event.aggregate_id,
            "timestamp": event.timestamp.isoformat()
        }
    
    @staticmethod
    def _adapt_RoundStartedEvent(event: RoundStartedEvent) -> Dict[str, Any]:
        """Adapt RoundStartedEvent to legacy format."""
        return {
            "type": "round_started",
            "room_id": event.aggregate_id,
            "round": event.data["round_number"],
            "dealer": event.data["dealer"],
            # Legacy used "round" instead of "round_number"
            "round_number": event.data["round_number"]
        }
    
    @staticmethod
    def _adapt_TurnPlayedEvent(event: TurnPlayedEvent) -> Dict[str, Any]:
        """Adapt TurnPlayedEvent to legacy format."""
        return {
            "type": "turn_played",
            "room_id": event.aggregate_id,
            "player": event.data["player"],
            "pieces": event.data["pieces"],
            "turn_number": event.data.get("turn_number", 0),
            # Legacy fields
            "success": True,
            "next_player": event.data.get("next_player")
        }
    
    @staticmethod
    def _adapt_PhaseChangedEvent(event: PhaseChangedEvent) -> Dict[str, Any]:
        """Adapt PhaseChangedEvent to legacy format."""
        return {
            "type": "phase_change",
            "room_id": event.aggregate_id,
            "old_phase": event.data["old_phase"],
            "new_phase": event.data["new_phase"],
            "phase_data": event.data.get("phase_data", {}),
            # Legacy expected these fields in phase_data
            "current_player": event.data.get("phase_data", {}).get("current_player"),
            "round_number": event.data.get("phase_data", {}).get("round_number")
        }
    
    @staticmethod
    def _adapt_PlayerDeclaredEvent(event: PlayerDeclaredEvent) -> Dict[str, Any]:
        """Adapt PlayerDeclaredEvent to legacy format."""
        return {
            "type": "player_declared",
            "room_id": event.aggregate_id,
            "player": event.data["player"],
            "declared_piles": event.data["declared_piles"],
            # Legacy fields
            "declaration": event.data["declared_piles"],
            "valid": True
        }
    
    @staticmethod
    def _adapt_RoundEndedEvent(event: RoundEndedEvent) -> Dict[str, Any]:
        """Adapt RoundEndedEvent to legacy format."""
        return {
            "type": "round_ended",
            "room_id": event.aggregate_id,
            "round_number": event.data["round_number"],
            "scores": event.data["scores"],
            "total_scores": event.data.get("total_scores", {}),
            # Legacy fields
            "round": event.data["round_number"],
            "round_scores": event.data["scores"]
        }
    
    @staticmethod
    def _adapt_GameEndedEvent(event: GameEndedEvent) -> Dict[str, Any]:
        """Adapt GameEndedEvent to legacy format."""
        return {
            "type": "game_ended",
            "room_id": event.aggregate_id,
            "winner": event.data["winner"],
            "final_scores": event.data["final_scores"],
            "reason": event.data["reason"],
            # Legacy fields
            "game_id": event.aggregate_id,
            "scores": event.data["final_scores"]
        }
    
    @staticmethod
    def _adapt_PlayerJoinedEvent(event: PlayerJoinedEvent) -> Dict[str, Any]:
        """Adapt PlayerJoinedEvent to legacy format."""
        return {
            "type": "player_joined",
            "room_id": event.aggregate_id,
            "player": event.data["player"],
            "players": event.data.get("players", []),
            # Legacy fields
            "player_name": event.data["player"].get("name") 
                          if isinstance(event.data["player"], dict) 
                          else event.data["player"],
            "player_count": len(event.data.get("players", []))
        }
    
    @staticmethod
    def _adapt_PlayerLeftEvent(event: PlayerLeftEvent) -> Dict[str, Any]:
        """Adapt PlayerLeftEvent to legacy format."""
        return {
            "type": "player_left",
            "room_id": event.aggregate_id,
            "player": event.data["player"],
            "reason": event.data.get("reason", "disconnected"),
            "replacement": event.data.get("replacement"),
            # Legacy fields
            "player_name": event.data["player"],
            "was_replaced": event.data.get("replacement") is not None
        }
    
    @staticmethod
    def _adapt_PlayerReadyEvent(event: PlayerReadyEvent) -> Dict[str, Any]:
        """Adapt PlayerReadyEvent to legacy format."""
        return {
            "type": "player_ready",
            "room_id": event.aggregate_id,
            "player": event.data["player"],
            "ready": event.data.get("ready", True),
            # Legacy fields
            "player_name": event.data["player"],
            "is_ready": event.data.get("ready", True)
        }
    
    @staticmethod
    def _adapt_HostTransferredEvent(event: HostTransferredEvent) -> Dict[str, Any]:
        """Adapt HostTransferredEvent to legacy format."""
        return {
            "type": "host_transferred",
            "room_id": event.aggregate_id,
            "old_host": event.data["old_host"],
            "new_host": event.data["new_host"],
            "reason": event.data.get("reason", "manual"),
            # Legacy fields
            "previous_host": event.data["old_host"],
            "current_host": event.data["new_host"]
        }
    
    @staticmethod
    def _adapt_WeakHandRequestedEvent(event: WeakHandRequestedEvent) -> Dict[str, Any]:
        """Adapt WeakHandRequestedEvent to legacy format."""
        return {
            "type": "weak_hand_requested",
            "room_id": event.aggregate_id,
            "player": event.data["player"],
            "round_number": event.data["round_number"],
            # Legacy fields
            "requesting_player": event.data["player"],
            "votes_needed": event.data.get("votes_needed", 4)
        }
    
    @staticmethod
    def ensure_legacy_format(message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure a message conforms to legacy format expectations.
        
        This adds any missing fields that legacy frontend expects.
        """
        # Ensure base structure
        if "type" not in message:
            message["type"] = "unknown"
        
        if "room_id" not in message and "aggregate_id" in message:
            message["room_id"] = message["aggregate_id"]
        
        # Add timestamp if missing
        if "timestamp" not in message:
            from datetime import datetime
            message["timestamp"] = datetime.utcnow().isoformat()
        
        return message