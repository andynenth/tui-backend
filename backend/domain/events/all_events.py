"""
Consolidated imports for all domain events.

This module provides a single import point for all domain events in the system.
"""

# Base classes
from .base import DomainEvent, GameEvent, EventMetadata
from .event_types import EventType

# Connection events
from .connection_events import (
    PlayerConnected,
    PlayerDisconnected,
    PlayerReconnected,
    ConnectionHeartbeat,
    ClientReady
)

# Room events
from .room_events import (
    RoomCreated,
    PlayerJoinedRoom,
    PlayerLeftRoom,
    RoomClosed,
    HostChanged,
    BotAdded,
    PlayerRemoved,
    RoomStateRequested
)

# Lobby events
from .lobby_events import (
    RoomListRequested,
    RoomListUpdated
)

# Game flow and action events
from .game_events import (
    # Game flow
    GameStarted,
    GameEnded,
    RoundStarted,
    RoundCompleted,
    RoundEnded,
    PhaseChanged,
    # Game actions
    PiecesDealt,
    WeakHandDetected,
    RedealRequested,
    RedealDecisionMade,
    RedealExecuted,
    DeclarationMade,
    PiecesPlayed,
    PlayerReadyForNext,
    CustomGameEvent
)

# Turn events
from .turn_events import (
    TurnStarted,
    TurnCompleted,
    TurnWinnerDetermined
)

# Scoring events
from .scoring_events import (
    ScoresCalculated,
    WinnerDetermined,
    GameOverTriggered
)

# Error events
from .error_events import (
    InvalidActionAttempted,
    ErrorOccurred
)

# Export all events
__all__ = [
    # Base classes
    'DomainEvent',
    'GameEvent',
    'EventMetadata',
    'EventType',
    
    # Connection events
    'PlayerConnected',
    'PlayerDisconnected',
    'PlayerReconnected',
    'ConnectionHeartbeat',
    'ClientReady',
    
    # Room events
    'RoomCreated',
    'PlayerJoinedRoom',
    'PlayerLeftRoom',
    'RoomClosed',
    'HostChanged',
    'BotAdded',
    'PlayerRemoved',
    'RoomStateRequested',
    
    # Lobby events
    'RoomListRequested',
    'RoomListUpdated',
    
    # Game flow events
    'GameStarted',
    'GameEnded',
    'RoundStarted',
    'RoundCompleted',
    'RoundEnded',
    'PhaseChanged',
    
    # Turn events
    'TurnStarted',
    
    # Game action events
    'PiecesDealt',
    'WeakHandDetected',
    'RedealRequested',
    'RedealDecisionMade',
    'RedealExecuted',
    'DeclarationMade',
    'PiecesPlayed',
    'TurnCompleted',
    'TurnWinnerDetermined',
    'PlayerReadyForNext',
    'CustomGameEvent',
    
    # Scoring events
    'ScoresCalculated',
    'WinnerDetermined',
    'GameOverTriggered',
    
    # Error events
    'InvalidActionAttempted',
    'ErrorOccurred'
]