# domain/__init__.py
"""
Domain layer of the Liap Tui game.

This layer contains:
- Entities: Core business objects (Game, Player, Piece)
- Value Objects: Immutable domain values
- Services: Domain logic and business rules
- Events: Domain events for decoupling
- Interfaces: Contracts for infrastructure

The domain layer has no dependencies on infrastructure or application layers.
"""

# Make key domain concepts easily importable
from .entities.game import Game
from .entities.player import Player
from .entities.piece import Piece, PieceDeck

from .value_objects.game_state import GameState, GamePhase
from .value_objects.play_result import PlayResult
from .value_objects.turn_play import TurnPlay

from .services.game_rules import GameRules
from .services.scoring import ScoringService, RoundScore
from .services.turn_resolution import TurnResolutionService, TurnResult

from .events.base import DomainEvent
from .events.game_events import (
    GameCreatedEvent,
    GameStartedEvent,
    RoundStartedEvent,
    TurnPlayedEvent,
    GameEndedEvent
)
from .events.player_events import (
    PlayerJoinedEvent,
    PlayerLeftEvent
)

__all__ = [
    # Entities
    'Game',
    'Player', 
    'Piece',
    'PieceDeck',
    
    # Value Objects
    'GameState',
    'GamePhase',
    'PlayResult',
    'TurnPlay',
    
    # Services
    'GameRules',
    'ScoringService',
    'RoundScore',
    'TurnResolutionService',
    'TurnResult',
    
    # Events
    'DomainEvent',
    'GameCreatedEvent',
    'GameStartedEvent',
    'RoundStartedEvent',
    'TurnPlayedEvent',
    'GameEndedEvent',
    'PlayerJoinedEvent',
    'PlayerLeftEvent',
]