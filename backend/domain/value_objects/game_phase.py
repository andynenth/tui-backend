"""
Unified GamePhase enum - Single source of truth for game phases.

This replaces the duplicate enums in:
- domain/entities/game.py (6 phases)
- engine/state_machine/core.py (11 phases)

The unified enum includes all phases from both systems with clear documentation.
"""

from enum import Enum
from typing import List, Set


class UnifiedGamePhase(Enum):
    """
    Unified game phase enum combining domain and state machine phases.
    
    This enum serves as the single source of truth for game phases across
    the entire system, bridging clean architecture and state machine.
    """
    
    # Core phases (exist in both systems)
    NOT_STARTED = "NOT_STARTED"
    PREPARATION = "PREPARATION"
    DECLARATION = "DECLARATION" 
    TURN = "TURN"
    SCORING = "SCORING"
    GAME_OVER = "GAME_OVER"
    
    # State machine specific phases (for granular control)
    WAITING = "WAITING"           # Waiting for players to join
    ROUND_START = "ROUND_START"   # Beginning of a round
    TURN_END = "TURN_END"         # End of a turn
    ROUND_END = "ROUND_END"       # End of a round
    ERROR = "ERROR"               # Error state
    
    @classmethod
    def domain_phases(cls) -> Set['UnifiedGamePhase']:
        """Get phases used by domain entities."""
        return {
            cls.NOT_STARTED,
            cls.PREPARATION,
            cls.DECLARATION,
            cls.TURN,
            cls.SCORING,
            cls.GAME_OVER
        }
    
    @classmethod
    def state_machine_phases(cls) -> Set['UnifiedGamePhase']:
        """Get all phases used by state machine."""
        return set(cls)
    
    @classmethod
    def transition_phases(cls) -> Set['UnifiedGamePhase']:
        """Get transitional phases (state machine only)."""
        return cls.state_machine_phases() - cls.domain_phases()
    
    def is_domain_phase(self) -> bool:
        """Check if this is a core domain phase."""
        return self in self.domain_phases()
    
    def is_transition_phase(self) -> bool:
        """Check if this is a transitional state machine phase."""
        return self in self.transition_phases()
    
    def next_phases(self) -> List['UnifiedGamePhase']:
        """Get valid next phases from current phase."""
        transitions = {
            self.NOT_STARTED: [self.WAITING, self.PREPARATION],
            self.WAITING: [self.PREPARATION],
            self.PREPARATION: [self.DECLARATION, self.PREPARATION],  # Can re-deal
            self.ROUND_START: [self.DECLARATION],
            self.DECLARATION: [self.TURN],
            self.TURN: [self.TURN_END, self.TURN],  # Multiple turns
            self.TURN_END: [self.TURN, self.SCORING],
            self.SCORING: [self.ROUND_END],
            self.ROUND_END: [self.ROUND_START, self.GAME_OVER],
            self.GAME_OVER: [],
            self.ERROR: [self.NOT_STARTED],  # Can restart
        }
        return transitions.get(self, [])
    
    def can_transition_to(self, target: 'UnifiedGamePhase') -> bool:
        """Check if transition to target phase is valid."""
        return target in self.next_phases()
    
    @classmethod
    def from_domain_phase(cls, domain_value: str) -> 'UnifiedGamePhase':
        """Convert from domain phase string."""
        try:
            return cls(domain_value)
        except ValueError:
            # Handle any legacy values
            mapping = {
                # Add any legacy mappings here if needed
            }
            if domain_value in mapping:
                return mapping[domain_value]
            raise ValueError(f"Unknown domain phase: {domain_value}")
    
    @classmethod
    def from_state_machine_phase(cls, state_value: str) -> 'UnifiedGamePhase':
        """Convert from state machine phase string."""
        try:
            return cls(state_value)
        except ValueError:
            # Handle any legacy values
            mapping = {
                # Add any legacy mappings here if needed
            }
            if state_value in mapping:
                return mapping[state_value]
            raise ValueError(f"Unknown state machine phase: {state_value}")
    
    def to_domain_phase(self) -> str:
        """
        Convert to domain phase string.
        
        For transition phases, returns the nearest domain phase.
        """
        if self.is_domain_phase():
            return self.value
            
        # Map transition phases to nearest domain phase
        mapping = {
            self.WAITING: self.NOT_STARTED.value,
            self.ROUND_START: self.PREPARATION.value,
            self.TURN_END: self.TURN.value,
            self.ROUND_END: self.SCORING.value,
            self.ERROR: self.GAME_OVER.value,
        }
        return mapping.get(self, self.value)
    
    def to_state_machine_phase(self) -> str:
        """Convert to state machine phase string."""
        return self.value
    
    def __str__(self) -> str:
        """String representation."""
        return self.value


# Alias for backward compatibility during migration
GamePhase = UnifiedGamePhase


# Migration helper functions
def migrate_domain_phase(old_phase) -> UnifiedGamePhase:
    """
    Migrate from old domain GamePhase to unified phase.
    
    Args:
        old_phase: Old domain GamePhase enum value
        
    Returns:
        Unified game phase
    """
    if hasattr(old_phase, 'value'):
        return UnifiedGamePhase.from_domain_phase(old_phase.value)
    return UnifiedGamePhase.from_domain_phase(str(old_phase))


def migrate_state_machine_phase(old_phase) -> UnifiedGamePhase:
    """
    Migrate from old state machine GamePhase to unified phase.
    
    Args:
        old_phase: Old state machine GamePhase enum value
        
    Returns:
        Unified game phase
    """
    if hasattr(old_phase, 'value'):
        return UnifiedGamePhase.from_state_machine_phase(old_phase.value)
    return UnifiedGamePhase.from_state_machine_phase(str(old_phase))