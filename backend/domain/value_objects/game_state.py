# domain/value_objects/game_state.py
"""
Value objects for game state representation.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class GamePhase(Enum):
    """Enumeration of game phases."""
    WAITING = "waiting"
    PREPARATION = "preparation"
    ROUND_START = "round_start"
    DECLARATION = "declaration"
    TURN = "turn"
    TURN_RESULTS = "turn_results"
    SCORING = "scoring"
    GAME_OVER = "game_over"


@dataclass(frozen=True)
class GameState:
    """
    Immutable representation of game state at a point in time.
    This can be used for event sourcing or state snapshots.
    """
    round_number: int
    phase: GamePhase
    turn_number: int
    redeal_multiplier: int
    current_player: Optional[str]
    
    def __str__(self) -> str:
        return f"GameState(round={self.round_number}, phase={self.phase.value}, turn={self.turn_number})"