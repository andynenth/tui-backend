"""
Player-related domain events.

These events are emitted when player state changes.
"""

from dataclasses import dataclass
from typing import List, Any, Dict
from .base import GameEvent


@dataclass(frozen=True)
class PlayerHandUpdated(GameEvent):
    """A player's hand has been updated."""

    player_id: str
    player_name: str
    old_hand: List[str]  # List of piece kinds
    new_hand: List[str]  # List of piece kinds

    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update(
            {
                "player_id": self.player_id,
                "player_name": self.player_name,
                "old_hand": self.old_hand,
                "new_hand": self.new_hand,
                "pieces_added": [p for p in self.new_hand if p not in self.old_hand],
                "pieces_removed": [p for p in self.old_hand if p not in self.new_hand],
            }
        )
        return data


@dataclass(frozen=True)
class PlayerDeclaredPiles(GameEvent):
    """A player has declared their target pile count."""

    player_id: str
    player_name: str
    declared_count: int
    zero_streak: int  # How many consecutive zero declarations

    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update(
            {
                "player_id": self.player_id,
                "player_name": self.player_name,
                "declared_count": self.declared_count,
                "zero_streak": self.zero_streak,
            }
        )
        return data


@dataclass(frozen=True)
class PlayerCapturedPiles(GameEvent):
    """A player has captured piles."""

    player_id: str
    player_name: str
    piles_captured: int  # Number captured in this action
    total_captured: int  # Total for the round

    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update(
            {
                "player_id": self.player_id,
                "player_name": self.player_name,
                "piles_captured": self.piles_captured,
                "total_captured": self.total_captured,
            }
        )
        return data


@dataclass(frozen=True)
class PlayerScoreUpdated(GameEvent):
    """A player's score has been updated."""

    player_id: str
    player_name: str
    old_score: int
    new_score: int
    points_change: int
    reason: str

    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update(
            {
                "player_id": self.player_id,
                "player_name": self.player_name,
                "old_score": self.old_score,
                "new_score": self.new_score,
                "points_change": self.points_change,
                "reason": self.reason,
            }
        )
        return data


@dataclass(frozen=True)
class PlayerStatUpdated(GameEvent):
    """A player statistic has been updated."""

    player_id: str
    player_name: str
    stat_name: str
    old_value: Any
    new_value: Any

    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update(
            {
                "player_id": self.player_id,
                "player_name": self.player_name,
                "stat_name": self.stat_name,
                "old_value": self.old_value,
                "new_value": self.new_value,
            }
        )
        return data
