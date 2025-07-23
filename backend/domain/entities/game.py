# domain/entities/game.py
"""
Domain entity for the Game.
This is the core game logic without any infrastructure dependencies.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import random

from ..value_objects.game_state import GamePhase
from ..value_objects.turn_play import TurnPlay
from ..value_objects.play_result import PlayResult
from .player import Player
from .piece import Piece


@dataclass
class Game:
    """
    Core game entity representing a game session.
    
    This class contains pure game logic without any infrastructure concerns.
    All state modifications should return new state or raise domain exceptions.
    """
    
    # Core game configuration
    players: List[Player]
    max_score: int = 50
    max_rounds: int = 20
    win_condition_type: str = "FIRST_TO_REACH_50"
    
    # Game state - made private to enforce encapsulation
    _round_number: int = field(default=1, init=False)
    _current_phase: GamePhase = field(default=GamePhase.WAITING, init=False)
    _turn_number: int = field(default=0, init=False)
    _redeal_multiplier: int = field(default=1, init=False)
    
    # Round state
    _current_order: List[Player] = field(default_factory=list, init=False)
    _round_starter: Optional[Player] = field(default=None, init=False)
    _last_round_winner: Optional[Player] = field(default=None, init=False)
    
    # Turn state
    _current_turn_plays: List[TurnPlay] = field(default_factory=list, init=False)
    _required_piece_count: Optional[int] = field(default=None, init=False)
    _turn_order: List[Player] = field(default_factory=list, init=False)
    _last_turn_winner: Optional[Player] = field(default=None, init=False)
    _current_player: Optional[Player] = field(default=None, init=False)
    
    # Player tracking
    _player_declarations: Dict[str, int] = field(default_factory=dict, init=False)
    _pile_counts: Dict[str, int] = field(default_factory=dict, init=False)
    _round_scores: Dict[str, int] = field(default_factory=dict, init=False)
    
    # Timing
    _start_time: Optional[float] = field(default=None, init=False)
    _end_time: Optional[float] = field(default=None, init=False)
    
    def __post_init__(self):
        """Initialize derived state after dataclass initialization."""
        if len(self.players) != 4:
            raise ValueError("Game requires exactly 4 players")
        
        # Initialize pile counts for all players
        for player in self.players:
            self._pile_counts[player.name] = 0
    
    # Public read-only properties
    @property
    def round_number(self) -> int:
        return self._round_number
    
    @property
    def current_phase(self) -> GamePhase:
        return self._current_phase
    
    @property
    def turn_number(self) -> int:
        return self._turn_number
    
    @property
    def redeal_multiplier(self) -> int:
        return self._redeal_multiplier
    
    @property
    def current_player(self) -> Optional[Player]:
        return self._current_player
    
    @property
    def pile_counts(self) -> Dict[str, int]:
        """Return a copy to prevent external modification."""
        return dict(self._pile_counts)
    
    @property
    def player_declarations(self) -> Dict[str, int]:
        """Return a copy to prevent external modification."""
        return dict(self._player_declarations)
    
    # Domain methods - these return results without side effects
    def can_start(self) -> bool:
        """Check if game can be started."""
        return len(self.players) == 4 and self._current_phase == GamePhase.WAITING
    
    def get_player(self, player_name: str) -> Optional[Player]:
        """Get player by name."""
        for player in self.players:
            if player.name == player_name:
                return player
        return None
    
    def get_weak_hand_players(self) -> List[Player]:
        """Get players with weak hands (no piece > 9 points)."""
        weak_players = []
        for player in self.players:
            if player.hand and max(piece.point for piece in player.hand) <= 9:
                weak_players.append(player)
        return weak_players
    
    def get_player_order_from(self, starting_player: str) -> List[str]:
        """Get player order starting from a specific player."""
        player_names = [p.name for p in self.players]
        try:
            start_index = player_names.index(starting_player)
            return player_names[start_index:] + player_names[:start_index]
        except ValueError:
            return player_names
    
    def is_game_over(self) -> bool:
        """Check if game has ended based on win conditions."""
        if self.win_condition_type == "FIRST_TO_REACH_50":
            return any(p.score >= self.max_score for p in self.players)
        elif self.win_condition_type == "FIXED_ROUNDS":
            return self._round_number >= self.max_rounds
        return False
    
    def get_winners(self) -> List[Player]:
        """Get winning players (can be multiple in case of tie)."""
        if not self.is_game_over():
            return []
        
        max_score = max(p.score for p in self.players)
        return [p for p in self.players if p.score == max_score]
    
    # State transition methods - these should be called by use cases
    def start_new_round(self) -> Dict[str, Any]:
        """
        Start a new round. Returns information about the new round.
        This should be called by a use case that handles side effects.
        """
        self._round_number += 1
        self._turn_number = 0
        self._current_turn_plays.clear()
        self._required_piece_count = None
        self._turn_order.clear()
        self._player_declarations.clear()
        self._round_scores.clear()
        
        # Reset pile counts
        for player in self.players:
            self._pile_counts[player.name] = 0
            player.reset_for_next_round()
        
        return {
            "round_number": self._round_number,
            "players": [{"name": p.name, "score": p.score} for p in self.players]
        }
    
    def record_player_declaration(self, player_name: str, declaration: int) -> Dict[str, Any]:
        """
        Record a player's pile declaration.
        Returns the result of the declaration.
        """
        player = self.get_player(player_name)
        if not player:
            raise ValueError(f"Player {player_name} not found")
        
        # Validate declaration is within valid range
        valid_declares = self._get_valid_declares(player)
        if declaration not in valid_declares:
            raise ValueError(f"Invalid declaration {declaration}")
        
        player.record_declaration(declaration)
        self._player_declarations[player_name] = declaration
        
        return {
            "player": player_name,
            "declaration": declaration,
            "total_declared": sum(self._player_declarations.values())
        }
    
    def play_turn(self, player_name: str, piece_indices: List[int]) -> PlayResult:
        """
        Process a player's turn. Returns the result of the play.
        This is a pure function that validates and records the play.
        """
        player = self.get_player(player_name)
        if not player:
            raise ValueError(f"Player {player_name} not found")
        
        # Get pieces from hand
        if not all(0 <= idx < len(player.hand) for idx in piece_indices):
            raise ValueError("Invalid piece indices")
        
        pieces = [player.hand[idx] for idx in piece_indices]
        
        # Validate play (this would use domain service)
        if not self._is_valid_play(pieces):
            raise ValueError("Invalid play")
        
        # Create turn play record
        turn_play = TurnPlay(
            player=player,
            pieces=pieces,
            play_type=self._get_play_type(pieces)
        )
        
        self._current_turn_plays.append(turn_play)
        
        # Check if turn is complete
        if len(self._current_turn_plays) == len(self.players):
            return self._resolve_turn()
        
        return PlayResult(
            status="waiting",
            player=player_name,
            pieces_played=len(pieces),
            next_player=self._get_next_player(player_name)
        )
    
    def increment_turn(self) -> None:
        """Increment the turn number."""
        self._turn_number += 1
    
    def set_redeal_multiplier(self, multiplier: int) -> None:
        """Set the redeal multiplier."""
        if multiplier < 1:
            raise ValueError("Multiplier must be at least 1")
        self._redeal_multiplier = multiplier
    
    def set_current_player(self, player_name: str) -> None:
        """Set the current player."""
        player = self.get_player(player_name)
        if not player:
            raise ValueError(f"Player {player_name} not found")
        self._current_player = player
    
    # Private helper methods
    def _get_valid_declares(self, player: Player) -> List[int]:
        """Get valid declaration values for a player."""
        # This would be moved to a domain service
        base_declares = [0, 1, 2, 3, 4, 5, 6, 7, 8]
        
        # Apply constraints based on game rules
        if player.zero_declares_in_a_row >= 2:
            return [d for d in base_declares if d > 0]
        
        return base_declares
    
    def _is_valid_play(self, pieces: List[Piece]) -> bool:
        """Check if a play is valid. This would use a domain service."""
        # Simplified validation - would be moved to domain service
        if not pieces:
            return False
        
        if self._required_piece_count and len(pieces) != self._required_piece_count:
            return False
        
        return True
    
    def _get_play_type(self, pieces: List[Piece]) -> str:
        """Determine the type of play. This would use a domain service."""
        # Simplified - would be moved to domain service
        count = len(pieces)
        if count == 1:
            return "single"
        elif count == 2:
            return "pair"
        elif count == 3:
            return "triple"
        else:
            return f"{count}_of_a_kind"
    
    def _get_next_player(self, current_player_name: str) -> Optional[str]:
        """Get the next player in turn order."""
        if not self._turn_order:
            return None
        
        player_names = [p.name for p in self._turn_order]
        try:
            current_index = player_names.index(current_player_name)
            next_index = (current_index + 1) % len(player_names)
            return player_names[next_index]
        except ValueError:
            return None
    
    def _resolve_turn(self) -> PlayResult:
        """Resolve the current turn and determine winner."""
        # This would use a domain service for turn resolution
        # Simplified version here
        if not self._current_turn_plays:
            raise ValueError("No plays to resolve")
        
        # Find winning play (simplified)
        winning_play = max(
            self._current_turn_plays,
            key=lambda play: sum(p.point for p in play.pieces)
        )
        
        winner = winning_play.player
        self._last_turn_winner = winner
        
        # Update pile count
        self._pile_counts[winner.name] += len(self._current_turn_plays)
        
        # Clear turn state
        self._current_turn_plays.clear()
        
        return PlayResult(
            status="resolved",
            winner=winner.name,
            pile_count=self._pile_counts[winner.name]
        )