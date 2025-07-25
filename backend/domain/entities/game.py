"""
Game entity - Core game logic and state management.

This is a pure domain entity with no infrastructure dependencies.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random

from domain.entities.player import Player
from domain.value_objects.piece import Piece
from domain.events.base import DomainEvent, EventMetadata
from domain.events.game_events import (
    RoundStarted,
    RoundCompleted,
    TurnStarted,
    TurnCompleted,
    GameStarted,
    GameEnded,
    PiecesDealt,
    WeakHandDetected,
    RedealExecuted,
    PhaseChanged,
    TurnWinnerDetermined
)


class GamePhase(Enum):
    """Game phases."""
    NOT_STARTED = "NOT_STARTED"
    PREPARATION = "PREPARATION"
    DECLARATION = "DECLARATION"
    TURN = "TURN"
    SCORING = "SCORING"
    GAME_OVER = "GAME_OVER"


class WinConditionType(Enum):
    """Types of win conditions."""
    FIRST_TO_REACH_50 = "FIRST_TO_REACH_50"
    HIGHEST_AFTER_20_ROUNDS = "HIGHEST_AFTER_20_ROUNDS"


@dataclass
class TurnPlay:
    """Value object representing a player's turn play."""
    player_name: str
    pieces: List[Piece]
    play_type: Optional[str] = None
    
    @property
    def piece_count(self) -> int:
        """Number of pieces played."""
        return len(self.pieces)
    
    @property
    def total_points(self) -> int:
        """Total point value of played pieces."""
        return sum(p.point for p in self.pieces)
    
    def beats(self, other: "TurnPlay") -> bool:
        """Check if this play beats another play."""
        # Must have same number of pieces
        if self.piece_count != other.piece_count:
            return False
        
        # Higher total points wins
        return self.total_points > other.total_points


@dataclass
class Game:
    """
    Domain entity representing a game.
    
    Manages game state, rules, and emits events for state changes.
    Infrastructure concerns (broadcasting, persistence) are not included.
    """
    room_id: str
    players: List[Player]
    win_condition_type: WinConditionType = WinConditionType.FIRST_TO_REACH_50
    max_score: int = 50
    max_rounds: int = 20
    
    # Game state
    round_number: int = 1
    turn_number: int = 0
    current_phase: GamePhase = GamePhase.NOT_STARTED
    
    # Round state
    redeal_multiplier: float = 1.0
    round_starter: Optional[str] = None
    last_round_winner: Optional[str] = None
    
    # Turn state
    current_turn_plays: List[TurnPlay] = field(default_factory=list)
    required_piece_count: Optional[int] = None
    last_turn_winner: Optional[str] = None
    turn_order: List[str] = field(default_factory=list)
    
    # Events
    _events: List[DomainEvent] = field(default_factory=list, init=False)
    
    @property
    def events(self) -> List[DomainEvent]:
        """Get domain events that have occurred."""
        return self._events.copy()
    
    def clear_events(self) -> None:
        """Clear the event list."""
        self._events.clear()
    
    def _emit_event(self, event: DomainEvent) -> None:
        """Emit a domain event."""
        self._events.append(event)
    
    def start_game(self) -> None:
        """Start a new game."""
        if self.current_phase != GamePhase.NOT_STARTED:
            raise ValueError("Game already started")
        
        self.current_phase = GamePhase.PREPARATION
        
        self._emit_event(GameStarted(
            room_id=self.room_id,
            round_number=self.round_number,
            player_names=[p.name for p in self.players],
            win_condition=self.win_condition_type.value,
            max_score=self.max_score,
            max_rounds=self.max_rounds,
            metadata=EventMetadata()
        ))
        
        self._emit_event(PhaseChanged(
            room_id=self.room_id,
            old_phase=GamePhase.NOT_STARTED.value,
            new_phase=GamePhase.PREPARATION.value,
            round_number=self.round_number,
            turn_number=self.turn_number,
            metadata=EventMetadata()
        ))
    
    def start_round(self) -> None:
        """Start a new round."""
        # Deal pieces to players
        deck = Piece.build_deck()
        random.shuffle(deck)
        
        for i, player in enumerate(self.players):
            player_pieces = deck[i*8:(i+1)*8]
            player.update_hand(player_pieces, self.room_id)
        
        # Determine round starter
        if self.round_number == 1:
            # First round: player with red general starts
            for player in self.players:
                if player.has_red_general():
                    self.round_starter = player.name
                    break
        else:
            # Subsequent rounds: last round winner starts
            self.round_starter = self.last_round_winner or self.players[0].name
        
        self._emit_event(RoundStarted(
            room_id=self.room_id,
            round_number=self.round_number,
            starter_name=self.round_starter,
            player_hands={p.name: [pc.kind for pc in p.hand] for p in self.players},
            metadata=EventMetadata()
        ))
        
        self._emit_event(PiecesDealt(
            room_id=self.room_id,
            round_number=self.round_number,
            player_pieces={p.name: [pc.kind for pc in p.hand] for p in self.players},
            metadata=EventMetadata()
        ))
        
        # Check for weak hands
        weak_players = self.get_weak_hand_players()
        if weak_players:
            self._emit_event(WeakHandDetected(
                room_id=self.room_id,
                round_number=self.round_number,
                weak_hand_players=[p["name"] for p in weak_players],
                metadata=EventMetadata()
            ))
    
    def get_weak_hand_players(self) -> List[Dict]:
        """Find players with weak hands (no piece > 9 points)."""
        weak_players = []
        
        for player in self.players:
            has_strong = any(p.point > 9 for p in player.hand)
            
            if not has_strong:
                hand_strength = sum(p.point for p in player.hand)
                weak_players.append({
                    "name": player.name,
                    "is_bot": player.is_bot,
                    "hand_strength": hand_strength,
                    "hand": [piece.kind for piece in player.hand]
                })
        
        weak_players.sort(key=lambda p: p["hand_strength"])
        return weak_players
    
    def execute_redeal(self, acceptors: List[str], decliners: List[str]) -> None:
        """Execute redeal for accepting players."""
        # Increase multiplier
        self.redeal_multiplier += 0.5
        
        # Redeal for acceptors
        deck = Piece.build_deck()
        random.shuffle(deck)
        deck_index = 0
        
        for player_name in acceptors:
            player = self.get_player(player_name)
            new_hand = deck[deck_index:deck_index+8]
            deck_index += 8
            player.update_hand(new_hand, self.room_id)
        
        # New starter is first decliner (if any), otherwise keep current
        new_starter = decliners[0] if decliners else self.round_starter
        self.round_starter = new_starter
        
        self._emit_event(RedealExecuted(
            room_id=self.room_id,
            round_number=self.round_number,
            acceptors=acceptors,
            decliners=decliners,
            new_starter_name=new_starter,
            new_multiplier=self.redeal_multiplier,
            metadata=EventMetadata()
        ))
    
    def change_phase(self, new_phase: GamePhase) -> None:
        """Change the game phase."""
        old_phase = self.current_phase
        self.current_phase = new_phase
        
        self._emit_event(PhaseChanged(
            room_id=self.room_id,
            old_phase=old_phase.value,
            new_phase=new_phase.value,
            round_number=self.round_number,
            turn_number=self.turn_number,
            metadata=EventMetadata()
        ))
    
    def all_players_declared(self) -> bool:
        """Check if all players have made declarations."""
        return all(p.declared_piles > 0 for p in self.players)
    
    def get_player(self, name: str) -> Player:
        """Get player by name."""
        for player in self.players:
            if player.name == name:
                return player
        raise ValueError(f"Player '{name}' not found")
    
    def get_player_order_from(self, starting_player_name: str) -> List[str]:
        """Get player order starting from a specific player."""
        try:
            start_player = self.get_player(starting_player_name)
            start_index = self.players.index(start_player)
            ordered_players = self.players[start_index:] + self.players[:start_index]
            return [p.name for p in ordered_players]
        except (ValueError, AttributeError):
            return [p.name for p in self.players]
    
    def start_turn(self) -> None:
        """Start a new turn."""
        self.turn_number += 1
        self.current_turn_plays.clear()
        self.required_piece_count = None
        
        # Set turn order based on last turn winner or round starter
        if self.last_turn_winner:
            self.turn_order = self.get_player_order_from(self.last_turn_winner)
        else:
            self.turn_order = self.get_player_order_from(self.round_starter)
        
        self._emit_event(TurnStarted(
            room_id=self.room_id,
            round_number=self.round_number,
            turn_number=self.turn_number,
            turn_order=self.turn_order,
            metadata=EventMetadata()
        ))
    
    def play_turn(self, player_name: str, piece_indices: List[int]) -> TurnPlay:
        """
        Execute a player's turn.
        
        Args:
            player_name: Name of the player
            piece_indices: Indices of pieces to play
            
        Returns:
            TurnPlay object representing the play
            
        Raises:
            ValueError: If play is invalid
        """
        player = self.get_player(player_name)
        
        # Validate indices
        if not all(0 <= i < len(player.hand) for i in piece_indices):
            raise ValueError("Invalid piece indices")
        
        # Get pieces
        pieces = [player.hand[i] for i in piece_indices]
        
        # Set required piece count from first play
        if self.required_piece_count is None:
            self.required_piece_count = len(pieces)
        elif len(pieces) != self.required_piece_count:
            raise ValueError(f"Must play {self.required_piece_count} pieces")
        
        # Remove pieces from hand
        removed_pieces = player.remove_pieces_from_hand(piece_indices, self.room_id)
        
        # Create turn play
        turn_play = TurnPlay(
            player_name=player_name,
            pieces=removed_pieces,
            play_type=self._get_play_type(removed_pieces)
        )
        
        self.current_turn_plays.append(turn_play)
        
        # Check if turn is complete
        if len(self.current_turn_plays) == len(self.players):
            self._complete_turn()
        
        return turn_play
    
    def _get_play_type(self, pieces: List[Piece]) -> str:
        """Determine the type of play (single, pair, triple, etc.)."""
        count = len(pieces)
        if count == 1:
            return "single"
        elif count == 2:
            return "pair"
        elif count == 3:
            return "triple"
        else:
            return f"{count}-combo"
    
    def _complete_turn(self) -> None:
        """Complete the current turn and determine winner."""
        # Find winning play
        winning_play = max(self.current_turn_plays, key=lambda p: p.total_points)
        self.last_turn_winner = winning_play.player_name
        
        # Award pile to winner
        winner = self.get_player(winning_play.player_name)
        winner.capture_piles(1, self.room_id)
        
        self._emit_event(TurnWinnerDetermined(
            room_id=self.room_id,
            round_number=self.round_number,
            turn_number=self.turn_number,
            winner_name=winning_play.player_name,
            winning_play=[p.kind for p in winning_play.pieces],
            all_plays={p.player_name: [pc.kind for pc in p.pieces] for p in self.current_turn_plays},
            metadata=EventMetadata()
        ))
        
        self._emit_event(TurnCompleted(
            room_id=self.room_id,
            round_number=self.round_number,
            turn_number=self.turn_number,
            plays={p.player_name: [pc.kind for pc in p.pieces] for p in self.current_turn_plays},
            metadata=EventMetadata()
        ))
    
    def is_round_complete(self) -> bool:
        """Check if the current round is complete."""
        return all(len(p.hand) == 0 for p in self.players)
    
    def complete_round(self, scores: Dict[str, int]) -> None:
        """Complete the current round."""
        # Update player scores
        for player_name, score in scores.items():
            player = self.get_player(player_name)
            player.update_score(score, self.room_id, f"Round {self.round_number} score")
            
            # Check for perfect round
            if player.declared_piles == player.captured_piles and player.declared_piles > 0:
                player.record_perfect_round(self.room_id)
        
        # Determine round winner (highest score this round)
        round_winner = max(scores.items(), key=lambda x: x[1])[0]
        self.last_round_winner = round_winner
        
        self._emit_event(RoundCompleted(
            room_id=self.room_id,
            round_number=self.round_number,
            round_scores=scores,
            total_scores={p.name: p.score for p in self.players},
            round_winner=round_winner,
            metadata=EventMetadata()
        ))
        
        # Reset for next round
        for player in self.players:
            player.reset_for_next_round()
        
        self.round_number += 1
        self.turn_number = 0
        self.redeal_multiplier = 1.0
    
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        if self.win_condition_type == WinConditionType.FIRST_TO_REACH_50:
            return any(p.score >= self.max_score for p in self.players)
        else:  # HIGHEST_AFTER_20_ROUNDS
            return self.round_number > self.max_rounds
    
    def get_winner(self) -> Optional[str]:
        """Get the game winner."""
        if not self.is_game_over():
            return None
        
        # Find player(s) with highest score
        max_score = max(p.score for p in self.players)
        winners = [p.name for p in self.players if p.score == max_score]
        
        # Return single winner or None if tie
        return winners[0] if len(winners) == 1 else None
    
    def end_game(self) -> None:
        """End the game."""
        if not self.is_game_over():
            raise ValueError("Game is not over yet")
        
        winner = self.get_winner()
        final_scores = {p.name: p.score for p in self.players}
        
        self.current_phase = GamePhase.GAME_OVER
        
        self._emit_event(GameEnded(
            room_id=self.room_id,
            final_scores=final_scores,
            winner_name=winner,
            total_rounds=self.round_number - 1,
            end_reason="score_limit" if self.win_condition_type == WinConditionType.FIRST_TO_REACH_50 else "round_limit",
            metadata=EventMetadata()
        ))
    
    def to_dict(self) -> dict:
        """Convert game to dictionary for serialization."""
        return {
            "room_id": self.room_id,
            "players": [p.to_dict() for p in self.players],
            "win_condition_type": self.win_condition_type.value,
            "max_score": self.max_score,
            "max_rounds": self.max_rounds,
            "round_number": self.round_number,
            "turn_number": self.turn_number,
            "current_phase": self.current_phase.value,
            "redeal_multiplier": self.redeal_multiplier,
            "round_starter": self.round_starter,
            "last_round_winner": self.last_round_winner,
            "last_turn_winner": self.last_turn_winner,
            "required_piece_count": self.required_piece_count
        }