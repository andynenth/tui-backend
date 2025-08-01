"""
Configuration for state management integration.

This module defines the configuration settings for state management,
including per-use-case settings and rollout strategies.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional


class StateManagementMode(Enum):
    """State management operation modes."""
    
    DISABLED = "disabled"      # No state management
    SHADOW = "shadow"          # Log only, don't persist
    ENABLED = "enabled"        # Full state persistence
    RECOVERY = "recovery"      # Recovery mode with validation


@dataclass
class UseCaseConfig:
    """Configuration for a specific use case."""
    
    enabled: bool = False
    track_actions: bool = True
    create_snapshots: bool = False
    validate_transitions: bool = True
    persistence_policy: str = "default"


@dataclass
class RolloutPhase:
    """Rollout phase configuration."""
    
    name: str
    percentage: int
    start_date: Optional[str] = None
    use_cases: Optional[List[str]] = None
    mode: StateManagementMode = StateManagementMode.ENABLED


# Default use case configurations
USE_CASE_CONFIGS: Dict[str, UseCaseConfig] = {
    # Game flow use cases
    "StartGameUseCase": UseCaseConfig(
        enabled=True,
        track_actions=False,  # Only track phase changes
        create_snapshots=True,  # Snapshot at game start
        validate_transitions=True
    ),
    
    "DeclareUseCase": UseCaseConfig(
        enabled=True,
        track_actions=True,  # Track each declaration
        create_snapshots=False,
        validate_transitions=True
    ),
    
    "PlayUseCase": UseCaseConfig(
        enabled=True,
        track_actions=True,  # Track each play
        create_snapshots=False,  # Too frequent
        validate_transitions=True
    ),
    
    "RequestRedealUseCase": UseCaseConfig(
        enabled=False,  # Not ready yet
        track_actions=True,
        create_snapshots=True,  # Snapshot before redeal
        validate_transitions=True
    ),
    
    "AcceptRedealUseCase": UseCaseConfig(
        enabled=False,
        track_actions=True,
        create_snapshots=False,
        validate_transitions=True
    ),
    
    "DeclineRedealUseCase": UseCaseConfig(
        enabled=False,
        track_actions=True,
        create_snapshots=False,
        validate_transitions=True
    ),
    
    # Room management use cases
    "CreateRoomUseCase": UseCaseConfig(
        enabled=False,  # No game state yet
        track_actions=False,
        create_snapshots=False,
        validate_transitions=False
    ),
    
    "JoinRoomUseCase": UseCaseConfig(
        enabled=False,  # No game state yet
        track_actions=False,
        create_snapshots=False,
        validate_transitions=False
    ),
}


# Rollout schedule
ROLLOUT_SCHEDULE: List[RolloutPhase] = [
    # Phase 1: Shadow mode for monitoring
    RolloutPhase(
        name="shadow",
        percentage=100,
        mode=StateManagementMode.SHADOW,
        start_date="2024-01-01",
        use_cases=["StartGameUseCase"]
    ),
    
    # Phase 2: Canary with core use cases
    RolloutPhase(
        name="canary",
        percentage=5,
        mode=StateManagementMode.ENABLED,
        start_date="2024-01-08",
        use_cases=["StartGameUseCase", "DeclareUseCase", "PlayUseCase"]
    ),
    
    # Phase 3: Early adopters
    RolloutPhase(
        name="early_adopters",
        percentage=10,
        mode=StateManagementMode.ENABLED,
        start_date="2024-01-15",
        use_cases=["StartGameUseCase", "DeclareUseCase", "PlayUseCase"]
    ),
    
    # Phase 4: Expanded rollout
    RolloutPhase(
        name="expanded",
        percentage=25,
        mode=StateManagementMode.ENABLED,
        start_date="2024-01-22",
        use_cases=None  # All configured use cases
    ),
    
    # Phase 5: Majority rollout
    RolloutPhase(
        name="majority",
        percentage=50,
        mode=StateManagementMode.ENABLED,
        start_date="2024-01-29",
        use_cases=None
    ),
    
    # Phase 6: Near-complete rollout
    RolloutPhase(
        name="near_complete",
        percentage=90,
        mode=StateManagementMode.ENABLED,
        start_date="2024-02-05",
        use_cases=None
    ),
    
    # Phase 7: Full rollout
    RolloutPhase(
        name="full",
        percentage=100,
        mode=StateManagementMode.ENABLED,
        start_date="2024-02-12",
        use_cases=None
    ),
]


# Critical transitions that must be tracked
CRITICAL_TRANSITIONS = {
    ("NOT_STARTED", "PREPARATION"): {
        "track": True,
        "snapshot": True,
        "validate": True,
        "required_fields": ["players", "room_id"]
    },
    
    ("PREPARATION", "DECLARATION"): {
        "track": True,
        "snapshot": False,
        "validate": True,
        "required_fields": ["pieces_dealt"]
    },
    
    ("DECLARATION", "TURN"): {
        "track": True,
        "snapshot": False,
        "validate": True,
        "required_fields": ["all_declared"]
    },
    
    ("TURN", "SCORING"): {
        "track": True,
        "snapshot": True,
        "validate": True,
        "required_fields": ["round_complete"]
    },
    
    ("SCORING", "PREPARATION"): {
        "track": True,
        "snapshot": True,
        "validate": True,
        "required_fields": ["new_round"]
    },
    
    ("SCORING", "GAME_OVER"): {
        "track": True,
        "snapshot": True,
        "validate": True,
        "required_fields": ["game_complete", "final_scores"]
    },
}


# Validation rules
VALIDATION_RULES = {
    "min_players": 2,
    "max_players": 4,
    "max_phase_duration_seconds": {
        "PREPARATION": 60,
        "DECLARATION": 120,
        "TURN": 300,
        "SCORING": 30
    },
    "max_game_duration_minutes": 120,
    "max_rounds": 50,
}


# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "state_tracking_latency_ms": 50,
    "snapshot_creation_latency_ms": 100,
    "recovery_time_seconds": 5,
    "max_memory_per_game_mb": 10,
    "max_transitions_per_game": 10000,
}


def get_use_case_config(use_case_name: str) -> UseCaseConfig:
    """
    Get configuration for a specific use case.
    
    Args:
        use_case_name: Name of the use case
        
    Returns:
        Use case configuration
    """
    return USE_CASE_CONFIGS.get(
        use_case_name,
        UseCaseConfig()  # Default disabled config
    )


def get_current_rollout_phase() -> Optional[RolloutPhase]:
    """
    Get the current rollout phase based on date.
    
    Returns:
        Current rollout phase or None
    """
    from datetime import datetime
    
    today = datetime.now().date()
    
    for phase in reversed(ROLLOUT_SCHEDULE):
        if phase.start_date:
            phase_date = datetime.strptime(phase.start_date, "%Y-%m-%d").date()
            if today >= phase_date:
                return phase
    
    return None


def should_create_snapshot(from_phase: str, to_phase: str) -> bool:
    """
    Check if a snapshot should be created for a phase transition.
    
    Args:
        from_phase: Current phase
        to_phase: New phase
        
    Returns:
        True if snapshot should be created
    """
    transition = (from_phase, to_phase)
    config = CRITICAL_TRANSITIONS.get(transition, {})
    return config.get("snapshot", False)