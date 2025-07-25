"""
Game-related domain events.

These events are emitted when game state changes.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from .base import GameEvent


@dataclass(frozen=True)
class GameStarted(GameEvent):
    """A game has started."""
    round_number: int
    player_names: List[str]
    win_condition: str
    max_score: int
    max_rounds: int
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'round_number': self.round_number,
            'player_names': self.player_names,
            'win_condition': self.win_condition,
            'max_score': self.max_score,
            'max_rounds': self.max_rounds
        })
        return data


@dataclass(frozen=True)
class GameEnded(GameEvent):
    """A game has ended."""
    final_scores: Dict[str, int]
    winner_name: Optional[str]
    total_rounds: int
    end_reason: str  # "score_limit" or "round_limit"
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'final_scores': self.final_scores,
            'winner_name': self.winner_name,
            'total_rounds': self.total_rounds,
            'end_reason': self.end_reason
        })
        return data


@dataclass(frozen=True)
class RoundStarted(GameEvent):
    """A new round has started."""
    round_number: int
    starter_name: str
    player_hands: Dict[str, List[str]]  # player_name -> piece kinds
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'round_number': self.round_number,
            'starter_name': self.starter_name,
            'player_hands': self.player_hands
        })
        return data


@dataclass(frozen=True)
class RoundCompleted(GameEvent):
    """A round has been completed."""
    round_number: int
    round_scores: Dict[str, int]
    total_scores: Dict[str, int]
    round_winner: str
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'round_number': self.round_number,
            'round_scores': self.round_scores,
            'total_scores': self.total_scores,
            'round_winner': self.round_winner
        })
        return data


@dataclass(frozen=True)
class PhaseChanged(GameEvent):
    """The game phase has changed."""
    old_phase: str
    new_phase: str
    round_number: int
    turn_number: int
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'old_phase': self.old_phase,
            'new_phase': self.new_phase,
            'round_number': self.round_number,
            'turn_number': self.turn_number
        })
        return data


@dataclass(frozen=True)
class TurnStarted(GameEvent):
    """A new turn has started."""
    round_number: int
    turn_number: int
    turn_order: List[str]  # Player names in turn order
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'round_number': self.round_number,
            'turn_number': self.turn_number,
            'turn_order': self.turn_order
        })
        return data


@dataclass(frozen=True)
class TurnCompleted(GameEvent):
    """A turn has been completed."""
    round_number: int
    turn_number: int
    plays: Dict[str, List[str]]  # player_name -> pieces played
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'round_number': self.round_number,
            'turn_number': self.turn_number,
            'plays': self.plays
        })
        return data


@dataclass(frozen=True)
class TurnWinnerDetermined(GameEvent):
    """The winner of a turn has been determined."""
    round_number: int
    turn_number: int
    winner_name: str
    winning_play: List[str]  # Piece kinds
    all_plays: Dict[str, List[str]]
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'round_number': self.round_number,
            'turn_number': self.turn_number,
            'winner_name': self.winner_name,
            'winning_play': self.winning_play,
            'all_plays': self.all_plays
        })
        return data


@dataclass(frozen=True)
class PiecesDealt(GameEvent):
    """Pieces have been dealt to players."""
    round_number: int
    player_pieces: Dict[str, List[str]]  # player_name -> piece kinds
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'round_number': self.round_number,
            'player_pieces': self.player_pieces
        })
        return data


@dataclass(frozen=True)
class WeakHandDetected(GameEvent):
    """Weak hands have been detected."""
    round_number: int
    weak_hand_players: List[str]
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'round_number': self.round_number,
            'weak_hand_players': self.weak_hand_players
        })
        return data


@dataclass(frozen=True)
class RedealExecuted(GameEvent):
    """Cards have been redealt."""
    round_number: int
    acceptors: List[str]
    decliners: List[str]
    new_starter_name: str
    new_multiplier: float
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'round_number': self.round_number,
            'acceptors': self.acceptors,
            'decliners': self.decliners,
            'new_starter_name': self.new_starter_name,
            'new_multiplier': self.new_multiplier
        })
        return data