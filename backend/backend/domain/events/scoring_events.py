"""
Scoring and game completion domain events.
"""

from dataclasses import dataclass
from typing import Dict, Any
from .base import GameEvent


@dataclass(frozen=True)
class ScoresCalculated(GameEvent):
    """Scores have been calculated for a round."""
    round_number: int
    declarations: Dict[str, int]  # player_name -> declared_count
    actual_piles: Dict[str, int]  # player_name -> actual_count
    round_scores: Dict[str, int]  # player_name -> score
    total_scores: Dict[str, int]  # player_name -> total_score
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'round_number': self.round_number,
            'declarations': self.declarations,
            'actual_piles': self.actual_piles,
            'round_scores': self.round_scores,
            'total_scores': self.total_scores
        })
        return data


@dataclass(frozen=True)
class WinnerDetermined(GameEvent):
    """A winner has been determined for the game."""
    winner_name: str
    winning_score: int
    final_scores: Dict[str, int]
    total_rounds_played: int
    win_condition: str  # "score_limit" or "round_limit"
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'winner_name': self.winner_name,
            'winning_score': self.winning_score,
            'final_scores': self.final_scores,
            'total_rounds_played': self.total_rounds_played,
            'win_condition': self.win_condition
        })
        return data


@dataclass(frozen=True)
class GameOverTriggered(GameEvent):
    """Game over conditions have been met."""
    trigger_reason: str  # "score_limit_reached", "round_limit_reached", "all_players_left"
    final_round_number: int
    highest_scorer: str
    highest_score: int
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'trigger_reason': self.trigger_reason,
            'final_round_number': self.final_round_number,
            'highest_scorer': self.highest_scorer,
            'highest_score': self.highest_score
        })
        return data