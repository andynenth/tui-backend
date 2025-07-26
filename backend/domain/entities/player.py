"""
Player entity - Represents a player in the game.

This is a pure domain entity with no infrastructure dependencies.
"""

from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from domain.value_objects.piece import Piece
from domain.events.base import DomainEvent, EventMetadata
from domain.events.player_events import (
    PlayerDeclaredPiles,
    PlayerCapturedPiles,
    PlayerScoreUpdated,
    PlayerHandUpdated,
    PlayerStatUpdated
)
from domain.events.connection_events import (
    PlayerDisconnected,
    PlayerReconnected,
    BotActivated,
    BotDeactivated
)


@dataclass
class PlayerStats:
    """Value object for player statistics."""
    turns_won: int = 0
    perfect_rounds: int = 0
    zero_declares_in_a_row: int = 0


@dataclass
class Player:
    """
    Domain entity representing a player in the game.
    
    This entity manages player state and emits events for state changes.
    Infrastructure concerns (connection, avatar color) are not included.
    """
    name: str
    is_bot: bool = False
    hand: List[Piece] = field(default_factory=list)
    score: int = 0
    declared_piles: int = 0
    captured_piles: int = 0
    stats: PlayerStats = field(default_factory=PlayerStats)
    
    # Connection tracking
    is_connected: bool = True
    disconnect_time: Optional[datetime] = None
    original_is_bot: bool = field(init=False)
    
    # Events that occurred during the player's lifecycle
    _events: List[DomainEvent] = field(default_factory=list, init=False)
    
    def __post_init__(self):
        """Initialize player."""
        self.original_is_bot = self.is_bot
    
    @property
    def id(self) -> str:
        """Player ID is their name (unique within a game)."""
        return self.name
    
    @property
    def events(self) -> List[DomainEvent]:
        """Get domain events that have occurred."""
        return self._events.copy()
    
    def clear_events(self) -> None:
        """Clear the event list (typically after processing)."""
        self._events.clear()
    
    def _emit_event(self, event: DomainEvent) -> None:
        """Emit a domain event."""
        self._events.append(event)
    
    def update_hand(self, pieces: List[Piece], room_id: str) -> None:
        """
        Update the player's hand.
        
        Args:
            pieces: New pieces for the player's hand
            room_id: The room this player is in
        """
        old_hand = self.hand.copy()
        self.hand = pieces.copy()
        
        self._emit_event(PlayerHandUpdated(
            room_id=room_id,
            player_id=self.id,
            player_name=self.name,
            old_hand=[p.kind for p in old_hand],
            new_hand=[p.kind for p in self.hand],
            metadata=EventMetadata()
        ))
    
    def add_pieces_to_hand(self, pieces: List[Piece], room_id: str) -> None:
        """
        Add pieces to the player's hand.
        
        Args:
            pieces: Pieces to add
            room_id: The room this player is in
        """
        old_hand = self.hand.copy()
        self.hand.extend(pieces)
        
        self._emit_event(PlayerHandUpdated(
            room_id=room_id,
            player_id=self.id,
            player_name=self.name,
            old_hand=[p.kind for p in old_hand],
            new_hand=[p.kind for p in self.hand],
            metadata=EventMetadata()
        ))
    
    def remove_pieces_from_hand(self, piece_indices: List[int], room_id: str) -> List[Piece]:
        """
        Remove pieces from hand by indices.
        
        Args:
            piece_indices: Indices of pieces to remove
            room_id: The room this player is in
            
        Returns:
            List of removed pieces
            
        Raises:
            ValueError: If any index is invalid
        """
        # Validate indices
        for idx in piece_indices:
            if idx < 0 or idx >= len(self.hand):
                raise ValueError(f"Invalid piece index: {idx}")
        
        # Sort indices in descending order to avoid shifting issues
        sorted_indices = sorted(piece_indices, reverse=True)
        
        old_hand = self.hand.copy()
        removed_pieces = []
        
        for idx in sorted_indices:
            removed_pieces.append(self.hand.pop(idx))
        
        # Reverse to maintain original order
        removed_pieces.reverse()
        
        self._emit_event(PlayerHandUpdated(
            room_id=room_id,
            player_id=self.id,
            player_name=self.name,
            old_hand=[p.kind for p in old_hand],
            new_hand=[p.kind for p in self.hand],
            metadata=EventMetadata()
        ))
        
        return removed_pieces
    
    def has_piece(self, piece_kind: str) -> bool:
        """
        Check if player has a specific piece.
        
        Args:
            piece_kind: The piece identifier (e.g., "GENERAL_RED")
            
        Returns:
            True if player has the piece
        """
        return any(p.kind == piece_kind for p in self.hand)
    
    def has_red_general(self) -> bool:
        """Check if the player has the RED GENERAL piece."""
        return self.has_piece("GENERAL_RED")
    
    def declare_piles(self, count: int, room_id: str) -> None:
        """
        Declare how many piles the player aims to capture.
        
        Args:
            count: Number of piles to declare (0-8)
            room_id: The room this player is in
            
        Raises:
            ValueError: If count is invalid
        """
        if count < 0 or count > 8:
            raise ValueError(f"Invalid declaration count: {count}")
        
        old_declared = self.declared_piles
        self.declared_piles = count
        
        # Update zero declaration streak
        if count == 0:
            self.stats.zero_declares_in_a_row += 1
        else:
            self.stats.zero_declares_in_a_row = 0
        
        self._emit_event(PlayerDeclaredPiles(
            room_id=room_id,
            player_id=self.id,
            player_name=self.name,
            declared_count=count,
            zero_streak=self.stats.zero_declares_in_a_row,
            metadata=EventMetadata()
        ))
    
    def capture_piles(self, count: int, room_id: str) -> None:
        """
        Record piles captured by the player.
        
        Args:
            count: Number of piles captured
            room_id: The room this player is in
        """
        old_captured = self.captured_piles
        self.captured_piles += count
        
        self._emit_event(PlayerCapturedPiles(
            room_id=room_id,
            player_id=self.id,
            player_name=self.name,
            piles_captured=count,
            total_captured=self.captured_piles,
            metadata=EventMetadata()
        ))
    
    def update_score(self, points: int, room_id: str, reason: str) -> None:
        """
        Update the player's score.
        
        Args:
            points: Points to add (can be negative)
            room_id: The room this player is in
            reason: Reason for score change
        """
        old_score = self.score
        self.score += points
        
        self._emit_event(PlayerScoreUpdated(
            room_id=room_id,
            player_id=self.id,
            player_name=self.name,
            old_score=old_score,
            new_score=self.score,
            points_change=points,
            reason=reason,
            metadata=EventMetadata()
        ))
    
    def record_turn_won(self, room_id: str) -> None:
        """Record that the player won a turn."""
        self.stats.turns_won += 1
        
        self._emit_event(PlayerStatUpdated(
            room_id=room_id,
            player_id=self.id,
            player_name=self.name,
            stat_name="turns_won",
            old_value=self.stats.turns_won - 1,
            new_value=self.stats.turns_won,
            metadata=EventMetadata()
        ))
    
    def record_perfect_round(self, room_id: str) -> None:
        """Record that the player had a perfect round."""
        self.stats.perfect_rounds += 1
        
        self._emit_event(PlayerStatUpdated(
            room_id=room_id,
            player_id=self.id,
            player_name=self.name,
            stat_name="perfect_rounds",
            old_value=self.stats.perfect_rounds - 1,
            new_value=self.stats.perfect_rounds,
            metadata=EventMetadata()
        ))
    
    def reset_for_next_round(self) -> None:
        """
        Reset player state for the next round.
        
        Note: This doesn't emit events as it's part of round transition.
        The Game entity should emit a RoundStarted event instead.
        """
        self.declared_piles = 0
        self.captured_piles = 0
        self.hand.clear()
    
    def disconnect(self, room_id: str, activate_bot: bool = True) -> None:
        """
        Mark player as disconnected.
        
        Args:
            room_id: The room this player is in
            activate_bot: Whether to activate bot control
        """
        self.is_connected = False
        self.disconnect_time = datetime.utcnow()
        bot_activated = False
        
        # Activate bot if requested and player is human
        if activate_bot and not self.original_is_bot:
            self.is_bot = True
            bot_activated = True
            
            self._emit_event(BotActivated(
                room_id=room_id,
                player_name=self.name,
                activation_time=self.disconnect_time,
                metadata=EventMetadata()
            ))
        
        self._emit_event(PlayerDisconnected(
            room_id=room_id,
            player_name=self.name,
            disconnect_time=self.disconnect_time,
            was_bot_activated=bot_activated,
            game_in_progress=True,  # Caller should set this appropriately
            metadata=EventMetadata()
        ))
    
    def reconnect(self, room_id: str, messages_queued: int = 0) -> None:
        """
        Mark player as reconnected.
        
        Args:
            room_id: The room this player is in
            messages_queued: Number of messages that were queued
        """
        self.is_connected = True
        reconnect_time = datetime.utcnow()
        self.disconnect_time = None
        bot_deactivated = False
        
        # Deactivate bot if it was activated for a human player
        if self.is_bot and not self.original_is_bot:
            self.is_bot = False
            bot_deactivated = True
            
            self._emit_event(BotDeactivated(
                room_id=room_id,
                player_name=self.name,
                deactivation_time=reconnect_time,
                metadata=EventMetadata()
            ))
        
        self._emit_event(PlayerReconnected(
            room_id=room_id,
            player_name=self.name,
            reconnect_time=reconnect_time,
            messages_queued=messages_queued,
            bot_was_deactivated=bot_deactivated,
            metadata=EventMetadata()
        ))
    
    def to_dict(self) -> dict:
        """
        Convert player to dictionary for serialization.
        
        Returns:
            Dictionary representation of player state
        """
        return {
            "name": self.name,
            "is_bot": self.is_bot,
            "hand": [p.to_dict() for p in self.hand],
            "score": self.score,
            "declared_piles": self.declared_piles,
            "captured_piles": self.captured_piles,
            "stats": {
                "turns_won": self.stats.turns_won,
                "perfect_rounds": self.stats.perfect_rounds,
                "zero_declares_in_a_row": self.stats.zero_declares_in_a_row
            },
            "is_connected": self.is_connected,
            "disconnect_time": self.disconnect_time.isoformat() if self.disconnect_time else None,
            "original_is_bot": self.original_is_bot
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        """
        Create player from dictionary.
        
        Args:
            data: Dictionary with player data
            
        Returns:
            New Player instance
        """
        stats = PlayerStats(**data.get("stats", {}))
        hand = [Piece.from_dict(p) for p in data.get("hand", [])]
        
        player = cls(
            name=data["name"],
            is_bot=data.get("is_bot", False),
            hand=hand,
            score=data.get("score", 0),
            declared_piles=data.get("declared_piles", 0),
            captured_piles=data.get("captured_piles", 0),
            stats=stats,
            is_connected=data.get("is_connected", True)
        )
        
        # Handle disconnect time
        if data.get("disconnect_time"):
            player.disconnect_time = datetime.fromisoformat(data["disconnect_time"])
        
        # Set original_is_bot if provided
        if "original_is_bot" in data:
            player.original_is_bot = data["original_is_bot"]
            
        return player