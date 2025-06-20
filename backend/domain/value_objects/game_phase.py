"""
Game Phase Value Object - Represents phases in Liap Tui game
This file should have ZERO external dependencies!
"""
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass


class GamePhase(Enum):
    """
    Phases of the Liap Tui game
    
    Value Object: These phases are immutable and defined by their value.
    Two REDEAL phases are equivalent regardless of where they exist in memory.
    """
    WAITING = "waiting"           # Waiting for players to join
    REDEAL = "redeal"            # Players decide whether to redeal
    DECLARATION = "declaration"   # Players declare their strategy
    PLAYING = "playing"          # Main game play
    FINISHED = "finished"        # Game completed
    ABANDONED = "abandoned"      # Game was abandoned
    
    @property
    def is_active(self) -> bool:
        """Is the game actively being played?"""
        return self in [GamePhase.REDEAL, GamePhase.DECLARATION, GamePhase.PLAYING]
    
    @property
    def is_waiting_for_players(self) -> bool:
        """Is the game waiting for player input?"""
        return self == GamePhase.WAITING
    
    @property
    def is_completed(self) -> bool:
        """Has the game reached a final state?"""
        return self in [GamePhase.FINISHED, GamePhase.ABANDONED]
    
    @property
    def display_name(self) -> str:
        """Human-readable phase name"""
        return self.value.replace("_", " ").title()
    
    def can_transition_to(self, next_phase: 'GamePhase') -> bool:
        """
        Domain logic: Valid phase transitions
        This encodes the business rules about game flow
        """
        valid_transitions = {
            GamePhase.WAITING: [GamePhase.REDEAL, GamePhase.ABANDONED],
            GamePhase.REDEAL: [GamePhase.DECLARATION, GamePhase.ABANDONED],
            GamePhase.DECLARATION: [GamePhase.PLAYING, GamePhase.ABANDONED],
            GamePhase.PLAYING: [GamePhase.FINISHED, GamePhase.ABANDONED],
            GamePhase.FINISHED: [],  # Terminal state
            GamePhase.ABANDONED: []  # Terminal state
        }
        
        return next_phase in valid_transitions.get(self, [])
    
    @classmethod
    def get_initial_phase(cls) -> 'GamePhase':
        """Get the starting phase for a new game"""
        return cls.WAITING
    
    @classmethod
    def get_all_active_phases(cls) -> List['GamePhase']:
        """Get all phases where the game is active"""
        return [phase for phase in cls if phase.is_active]


@dataclass(frozen=True)
class PhaseTransition:
    """
    Value Object representing a transition between game phases
    Useful for logging, events, and validation
    """
    from_phase: GamePhase
    to_phase: GamePhase
    reason: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        """Is this a valid transition?"""
        return self.from_phase.can_transition_to(self.to_phase)
    
    @property
    def description(self) -> str:
        """Human-readable transition description"""
        reason_text = f" ({self.reason})" if self.reason else ""
        return f"{self.from_phase.display_name} → {self.to_phase.display_name}{reason_text}"
    
    def __str__(self) -> str:
        """String representation"""
        return self.description


# Quick tests to ensure it works
if __name__ == "__main__":
    # Test basic phase functionality
    current_phase = GamePhase.WAITING
    print(f"Current phase: {current_phase.display_name}")
    print(f"Is active? {current_phase.is_active}")
    print(f"Is waiting? {current_phase.is_waiting_for_players}")
    
    # Test phase transitions
    next_phase = GamePhase.REDEAL
    can_transition = current_phase.can_transition_to(next_phase)
    print(f"Can transition from {current_phase.display_name} to {next_phase.display_name}? {can_transition}")
    
    # Test invalid transition
    invalid_transition = current_phase.can_transition_to(GamePhase.FINISHED)
    print(f"Can skip to finished? {invalid_transition}")
    
    # Test transition object
    transition = PhaseTransition(
        from_phase=GamePhase.WAITING,
        to_phase=GamePhase.REDEAL,
        reason="All players joined"
    )
    print(f"Transition: {transition}")
    print(f"Is valid? {transition.is_valid}")
    
    # Test all active phases
    active_phases = GamePhase.get_all_active_phases()
    print(f"Active phases: {[p.display_name for p in active_phases]}")
    
    print("✅ GamePhase value object works!")