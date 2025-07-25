"""
Game flow and game action domain events.

These events represent the main game lifecycle and player actions.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from .base import GameEvent


# Game Flow Events

@dataclass(frozen=True)
class GameStarted(GameEvent):
    """A game has started."""
    round_number: int
    player_names: List[str]
    started_by_id: str
    started_by_name: str
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'round_number': self.round_number,
            'player_names': self.player_names,
            'started_by_id': self.started_by_id,
            'started_by_name': self.started_by_name
        })
        return data


@dataclass(frozen=True)
class GameEnded(GameEvent):
    """A game has ended."""
    final_scores: Dict[str, int]
    winner_name: str
    total_rounds: int
    end_reason: str  # "score_limit", "round_limit", "all_players_left"
    
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
    dealer_name: str
    starter_name: str
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'round_number': self.round_number,
            'dealer_name': self.dealer_name,
            'starter_name': self.starter_name
        })
        return data


@dataclass(frozen=True)
class RoundCompleted(GameEvent):
    """A round has been completed."""
    round_number: int
    round_scores: Dict[str, int]
    total_scores: Dict[str, int]
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'round_number': self.round_number,
            'round_scores': self.round_scores,
            'total_scores': self.total_scores
        })
        return data


@dataclass(frozen=True)
class PhaseChanged(GameEvent):
    """The game phase has changed."""
    old_phase: str
    new_phase: str
    phase_data: Dict[str, Any]
    reason: str
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'old_phase': self.old_phase,
            'new_phase': self.new_phase,
            'phase_data': self.phase_data,
            'reason': self.reason
        })
        return data


# Game Action Events

@dataclass(frozen=True)
class PiecesDealt(GameEvent):
    """Pieces have been dealt to players."""
    round_number: int
    player_pieces: Dict[str, List[str]]  # player_name -> pieces
    
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
class RedealRequested(GameEvent):
    """A player has requested a redeal."""
    player_id: str
    player_name: str
    round_number: int
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'player_id': self.player_id,
            'player_name': self.player_name,
            'round_number': self.round_number
        })
        return data


@dataclass(frozen=True)
class RedealDecisionMade(GameEvent):
    """A player has made a redeal decision."""
    player_id: str
    player_name: str
    decision: str  # "accept" or "decline"
    round_number: int
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'player_id': self.player_id,
            'player_name': self.player_name,
            'decision': self.decision,
            'round_number': self.round_number
        })
        return data


@dataclass(frozen=True)
class RedealExecuted(GameEvent):
    """Cards have been redealt."""
    round_number: int
    acceptors: List[str]
    decliners: List[str]
    new_starter_name: Optional[str]
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'round_number': self.round_number,
            'acceptors': self.acceptors,
            'decliners': self.decliners,
            'new_starter_name': self.new_starter_name
        })
        return data


@dataclass(frozen=True)
class DeclarationMade(GameEvent):
    """A player has made their pile count declaration."""
    player_id: str
    player_name: str
    declared_count: int
    round_number: int
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'player_id': self.player_id,
            'player_name': self.player_name,
            'declared_count': self.declared_count,
            'round_number': self.round_number
        })
        return data


@dataclass(frozen=True)
class PiecesPlayed(GameEvent):
    """A player has played pieces in their turn."""
    player_id: str
    player_name: str
    pieces: List[str]
    piece_indices: List[int]
    turn_number: int
    round_number: int
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'player_id': self.player_id,
            'player_name': self.player_name,
            'pieces': self.pieces,
            'piece_indices': self.piece_indices,
            'turn_number': self.turn_number,
            'round_number': self.round_number
        })
        return data


@dataclass(frozen=True)
class TurnCompleted(GameEvent):
    """A turn has been completed."""
    turn_number: int
    round_number: int
    plays: Dict[str, List[str]]  # player_name -> pieces played
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'turn_number': self.turn_number,
            'round_number': self.round_number,
            'plays': self.plays
        })
        return data


@dataclass(frozen=True)
class TurnWinnerDetermined(GameEvent):
    """The winner of a turn has been determined."""
    turn_number: int
    round_number: int
    winner_name: str
    winning_play: List[str]
    all_plays: Dict[str, List[str]]
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'turn_number': self.turn_number,
            'round_number': self.round_number,
            'winner_name': self.winner_name,
            'winning_play': self.winning_play,
            'all_plays': self.all_plays
        })
        return data


@dataclass(frozen=True)
class PlayerReadyForNext(GameEvent):
    """A player has signaled they're ready for the next phase."""
    player_id: str
    player_name: str
    current_phase: str
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'player_id': self.player_id,
            'player_name': self.player_name,
            'current_phase': self.current_phase
        })
        return data


@dataclass(frozen=True)
class CustomGameEvent(GameEvent):
    """Event for custom game-specific events that don't fit other categories."""
    custom_event_type: str
    data: Dict[str, Any]
    
    def _get_event_data(self) -> Dict[str, Any]:
        base_data = super()._get_event_data()
        base_data.update({
            'custom_event_type': self.custom_event_type,
            'data': self.data
        })
        return base_data