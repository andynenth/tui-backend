"""
Turn-related domain events.

These events represent turn actions and outcomes during gameplay.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from .base import GameEvent


@dataclass(frozen=True)
class TurnStarted(GameEvent):
    """A new turn has started."""

    game_id: str
    turn_number: int
    current_player_id: str
    current_player_name: str
    required_piece_count: Optional[int] = None

    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update(
            {
                "game_id": self.game_id,
                "turn_number": self.turn_number,
                "current_player_id": self.current_player_id,
                "current_player_name": self.current_player_name,
                "required_piece_count": self.required_piece_count,
            }
        )
        return data


@dataclass(frozen=True)
class TurnCompleted(GameEvent):
    """A turn has been completed."""

    game_id: str
    turn_number: int
    winner_id: str
    winner_name: str
    pieces_won: int
    next_player_id: Optional[str] = None

    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update(
            {
                "game_id": self.game_id,
                "turn_number": self.turn_number,
                "winner_id": self.winner_id,
                "winner_name": self.winner_name,
                "pieces_won": self.pieces_won,
                "next_player_id": self.next_player_id,
            }
        )
        return data


@dataclass(frozen=True)
class TurnWinnerDetermined(GameEvent):
    """The winner of a turn has been determined."""

    game_id: str
    turn_number: int
    winner_id: str
    winner_name: str
    winning_play: List[Dict[str, Any]]
    defeated_plays: List[Dict[str, Any]]

    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update(
            {
                "game_id": self.game_id,
                "turn_number": self.turn_number,
                "winner_id": self.winner_id,
                "winner_name": self.winner_name,
                "winning_play": self.winning_play,
                "defeated_plays": self.defeated_plays,
            }
        )
        return data
