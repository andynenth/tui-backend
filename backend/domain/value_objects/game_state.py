# backend/domain/value_objects/game_state.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional, FrozenSet, Tuple
from uuid import UUID
from datetime import datetime

from .game_phase import GamePhase
from ..entities.piece import Piece


@dataclass(frozen=True)
class PlayerState:
    """
    Value Object: Immutable snapshot of a player's state at a point in time
    
    Used within GameState to capture complete player information
    """
    name: str
    score: int
    hand_size: int  # Don't expose actual cards for privacy
    pieces_played_this_turn: Tuple[Piece, ...] = field(default_factory=tuple)
    has_declared: bool = False
    is_active_turn: bool = False
    position_in_game: int = 0  # 0-based player order


@dataclass(frozen=True)
class TurnState:
    """
    Value Object: Immutable snapshot of current turn information
    """
    current_player_name: str
    turn_number: int
    phase: GamePhase
    can_play_pieces: bool
    can_redeal: bool
    can_declare: bool
    pieces_on_table: Tuple[Piece, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GameState:
    """
    Value Object: Complete immutable snapshot of game state
    
    Purpose:
    - Enable game history/replay functionality
    - Support undo/rollback operations  
    - Provide audit trail for debugging
    - Allow state comparison in tests
    - Foundation for event sourcing patterns
    
    Identity: Based on ALL field values (value-based equality)
    Immutability: Cannot be modified after creation (frozen=True)
    """
    
    # Fields WITHOUT defaults (must come first)
    game_id: UUID
    created_at: datetime
    max_players: int
    
    # Fields WITH defaults (must come after fields without defaults)
    snapshot_at: datetime = field(default_factory=datetime.now)
    is_game_over: bool = False
    game_over_reason: str = ""
    winner_name: Optional[str] = None
    players: Tuple[PlayerState, ...] = field(default_factory=tuple)
    player_count: int = 0
    turn_state: Optional[TurnState] = None
    total_turns_played: int = 0
    last_action: str = ""
    last_action_player: str = ""
    
    def __post_init__(self):
        """Validate game state consistency"""
        # Validate player count matches players list
        if len(self.players) != self.player_count:
            raise ValueError("Player count mismatch with players list")
        
        # Validate max players
        if self.player_count > self.max_players:
            raise ValueError("Player count exceeds max players")
        
        # Validate winner exists if game is over
        if self.is_game_over and self.winner_name:
            player_names = {player.name for player in self.players}
            if self.winner_name not in player_names:
                raise ValueError("Winner must be one of the players")
        
        # Validate active turn player exists
        if self.turn_state and self.turn_state.current_player_name:
            player_names = {player.name for player in self.players}
            if self.turn_state.current_player_name not in player_names:
                raise ValueError("Active player must be one of the players")
    
    # === State Query Methods ===
    
    def get_player_state(self, player_name: str) -> Optional[PlayerState]:
        """Get immutable state for specific player"""
        for player in self.players:
            if player.name == player_name:
                return player
        return None
    
    def get_current_player(self) -> Optional[PlayerState]:
        """Get the player whose turn it is"""
        if not self.turn_state:
            return None
        return self.get_player_state(self.turn_state.current_player_name)
    
    def get_player_scores(self) -> Dict[str, int]:
        """Get all player scores as dictionary"""
        return {player.name: player.score for player in self.players}
    
    def get_leaderboard(self) -> List[Tuple[str, int]]:
        """Get players sorted by score (highest first)"""
        scores = [(player.name, player.score) for player in self.players]
        return sorted(scores, key=lambda x: x[1], reverse=True)
    
    def get_active_players(self) -> Tuple[PlayerState, ...]:
        """Get all players currently in the game"""
        return self.players
    
    # === Game State Comparison ===
    
    def has_scores_changed(self, other: 'GameState') -> bool:
        """Compare if scores have changed between two states"""
        if self.game_id != other.game_id:
            raise ValueError("Cannot compare states from different games")
        
        return self.get_player_scores() != other.get_player_scores()
    
    def has_turn_changed(self, other: 'GameState') -> bool:
        """Compare if turn has changed between two states"""
        if self.game_id != other.game_id:
            raise ValueError("Cannot compare states from different games")
        
        if not self.turn_state or not other.turn_state:
            return self.turn_state != other.turn_state
        
        return (
            self.turn_state.current_player_name != other.turn_state.current_player_name or
            self.turn_state.turn_number != other.turn_state.turn_number or
            self.turn_state.phase != other.turn_state.phase
        )
    
    def has_phase_changed(self, other: 'GameState') -> bool:
        """Compare if game phase has changed between two states"""
        if self.game_id != other.game_id:
            raise ValueError("Cannot compare states from different games")
        
        if not self.turn_state or not other.turn_state:
            return self.turn_state != other.turn_state
        
        return self.turn_state.phase != other.turn_state.phase
    
    # === State Information ===
    
    def is_waiting_for_players(self) -> bool:
        """Check if game is waiting for more players"""
        return self.player_count < 2 and not self.is_game_over
    
    def is_in_progress(self) -> bool:
        """Check if game is actively being played"""
        return (
            self.player_count >= 2 and 
            not self.is_game_over and 
            self.turn_state is not None
        )
    
    def can_action_be_taken(self) -> bool:
        """Check if any player action can be taken"""
        if not self.turn_state or self.is_game_over:
            return False
        
        return (
            self.turn_state.can_play_pieces or 
            self.turn_state.can_redeal or 
            self.turn_state.can_declare
        )
    
    def get_game_duration(self) -> float:
        """Get game duration in seconds"""
        return (self.snapshot_at - self.created_at).total_seconds()
    
    # === Factory Methods for Common States ===
    
    @classmethod
    def create_initial_state(
        cls, 
        game_id: UUID, 
        max_players: int,
        created_at: datetime
    ) -> 'GameState':
        """Create initial empty game state"""
        return cls(
            game_id=game_id,
            created_at=created_at,
            max_players=max_players,
            player_count=0,
            players=tuple(),
            last_action="Game created"
        )
    
    @classmethod 
    def create_game_over_state(
        cls,
        previous_state: 'GameState',
        winner_name: Optional[str],
        reason: str
    ) -> 'GameState':
        """Create game over state from previous state"""
        return cls(
            game_id=previous_state.game_id,
            created_at=previous_state.created_at,
            max_players=previous_state.max_players,
            is_game_over=True,
            game_over_reason=reason,
            winner_name=winner_name,
            players=previous_state.players,
            player_count=previous_state.player_count,
            turn_state=None,  # Clear turn state when game ends
            total_turns_played=previous_state.total_turns_played,
            last_action=f"Game ended: {reason}",
            last_action_player=winner_name or ""
        )
    
    # === Export Methods ===
    
    def to_dict(self) -> Dict:
        """Convert state to dictionary for serialization"""
        return {
            "game_id": str(self.game_id),
            "created_at": self.created_at.isoformat(),
            "snapshot_at": self.snapshot_at.isoformat(),
            "max_players": self.max_players,
            "is_game_over": self.is_game_over,
            "game_over_reason": self.game_over_reason,
            "winner_name": self.winner_name,
            "player_count": self.player_count,
            "players": [
                {
                    "name": p.name,
                    "score": p.score,
                    "hand_size": p.hand_size,
                    "has_declared": p.has_declared,
                    "is_active_turn": p.is_active_turn,
                    "position_in_game": p.position_in_game,
                    "pieces_played": len(p.pieces_played_this_turn)
                }
                for p in self.players
            ],
            "turn_state": {
                "current_player_name": self.turn_state.current_player_name,
                "turn_number": self.turn_state.turn_number,
                "phase": self.turn_state.phase.value,
                "can_play_pieces": self.turn_state.can_play_pieces,
                "can_redeal": self.turn_state.can_redeal,
                "can_declare": self.turn_state.can_declare,
                "pieces_on_table": len(self.turn_state.pieces_on_table)
            } if self.turn_state else None,
            "total_turns_played": self.total_turns_played,
            "last_action": self.last_action,
            "last_action_player": self.last_action_player,
            "game_duration_seconds": self.get_game_duration()
        }
    
    def __str__(self) -> str:
        """Human-readable representation"""
        if self.is_game_over:
            status = f"Game Over - {self.game_over_reason}"
            if self.winner_name:
                status += f" (Winner: {self.winner_name})"
        elif self.is_in_progress():
            current_player = self.turn_state.current_player_name if self.turn_state else "Unknown"
            phase = self.turn_state.phase.value if self.turn_state else "Unknown"
            status = f"In Progress - {current_player}'s turn ({phase})"
        else:
            status = f"Waiting for players ({self.player_count}/{self.max_players})"
        
        return f"GameState({self.game_id.hex[:8]}: {status})"