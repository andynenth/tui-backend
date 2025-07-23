# domain/events/game_events.py
"""
Domain events related to game lifecycle and gameplay.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import uuid
from .base import AggregateEvent


@dataclass(frozen=True, kw_only=True)
class GameCreatedEvent(AggregateEvent):
    """Event raised when a new game is created."""
    # Event-specific fields
    player_names: List[str]
    max_score: int
    max_rounds: int
    win_condition_type: str
    
    def __post_init__(self):
        object.__setattr__(self, 'aggregate_type', 'Game')


@dataclass(frozen=True, kw_only=True)
class GameStartedEvent(AggregateEvent):
    """Event raised when a game begins."""
    round_number: int
    starting_player: str
    player_order: List[str]
    
    def __post_init__(self):
        object.__setattr__(self, 'aggregate_type', 'Game')


@dataclass(frozen=True, kw_only=True)
class RoundStartedEvent(AggregateEvent):
    """Event raised when a new round begins."""
    round_number: int
    round_starter: str
    redeal_multiplier: int
    
    def __post_init__(self):
        object.__setattr__(self, 'aggregate_type', 'Game')


@dataclass(frozen=True, kw_only=True)
class CardsDealtEvent(AggregateEvent):
    """Event raised when cards are dealt to players."""
    round_number: int
    player_hands: Dict[str, int]  # player_name -> hand_size
    weak_players: List[str]
    
    def __post_init__(self):
        object.__setattr__(self, 'aggregate_type', 'Game')


@dataclass(frozen=True, kw_only=True)
class RedealRequestedEvent(AggregateEvent):
    """Event raised when a player requests a redeal."""
    round_number: int
    player_name: str
    accepted: bool
    new_multiplier: int
    
    def __post_init__(self):
        object.__setattr__(self, 'aggregate_type', 'Game')


@dataclass(frozen=True, kw_only=True)
class PhaseChangedEvent(AggregateEvent):
    """Event raised when game phase changes."""
    old_phase: str
    new_phase: str
    round_number: int
    turn_number: int
    
    def __post_init__(self):
        object.__setattr__(self, 'aggregate_type', 'Game')


@dataclass(frozen=True, kw_only=True)
class DeclarationMadeEvent(AggregateEvent):
    """Event raised when a player makes a pile declaration."""
    round_number: int
    player_name: str
    declared_piles: int
    total_declared: int
    
    def __post_init__(self):
        object.__setattr__(self, 'aggregate_type', 'Game')


@dataclass(frozen=True, kw_only=True)
class TurnPlayedEvent(AggregateEvent):
    """Event raised when a player plays their turn."""
    round_number: int
    turn_number: int
    player_name: str
    pieces_count: int
    play_type: str
    
    def __post_init__(self):
        object.__setattr__(self, 'aggregate_type', 'Game')


@dataclass(frozen=True, kw_only=True)
class TurnResolvedEvent(AggregateEvent):
    """Event raised when a turn is resolved."""
    round_number: int
    turn_number: int
    winner: str
    pieces_won: int
    play_type: str
    
    def __post_init__(self):
        object.__setattr__(self, 'aggregate_type', 'Game')


@dataclass(frozen=True, kw_only=True)
class RoundScoredEvent(AggregateEvent):
    """Event raised when round scoring is complete."""
    round_number: int
    scores: Dict[str, Dict[str, int]]  # player -> {declared, actual, delta, total}
    redeal_multiplier: int
    perfect_rounds: List[str]  # Players who had perfect rounds
    
    def __post_init__(self):
        object.__setattr__(self, 'aggregate_type', 'Game')


@dataclass(frozen=True, kw_only=True)
class RoundEndedEvent(AggregateEvent):
    """Event raised when a round ends."""
    round_number: int
    round_winner: Optional[str]
    next_round_starter: Optional[str]
    is_final_round: bool
    
    def __post_init__(self):
        object.__setattr__(self, 'aggregate_type', 'Game')


@dataclass(frozen=True, kw_only=True)
class GameEndedEvent(AggregateEvent):
    """Event raised when the game ends."""
    final_round: int
    winners: List[str]
    final_scores: Dict[str, int]
    win_condition: str
    duration_seconds: float
    
    def __post_init__(self):
        object.__setattr__(self, 'aggregate_type', 'Game')


# Specialized events for error conditions

@dataclass(frozen=True, kw_only=True)
class InvalidPlayAttemptedEvent(AggregateEvent):
    """Event raised when a player attempts an invalid play."""
    round_number: int
    turn_number: int
    player_name: str
    reason: str
    
    def __post_init__(self):
        object.__setattr__(self, 'aggregate_type', 'Game')


@dataclass(frozen=True, kw_only=True)
class RuleViolationEvent(AggregateEvent):
    """Event raised when a game rule is violated."""
    rule_type: str
    player_name: Optional[str]
    description: str
    
    def __post_init__(self):
        object.__setattr__(self, 'aggregate_type', 'Game')


# Bot-specific events

@dataclass(frozen=True, kw_only=True)
class BotThinkingEvent(AggregateEvent):
    """Event raised when a bot starts thinking."""
    bot_name: str
    action_type: str  # "declaration", "play"
    thinking_duration_ms: int
    
    def __post_init__(self):
        object.__setattr__(self, 'aggregate_type', 'Game')


@dataclass(frozen=True, kw_only=True)
class BotActionEvent(AggregateEvent):
    """Event raised when a bot performs an action."""
    bot_name: str
    action_type: str  # "declaration", "play"
    action_details: Dict[str, Any]
    
    def __post_init__(self):
        object.__setattr__(self, 'aggregate_type', 'Game')