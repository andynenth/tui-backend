"""
Enumeration of all domain event types in the system.

This provides a centralized registry of all events for easy reference
and helps prevent typos in event type strings.
"""

from enum import Enum, auto


class EventType(Enum):
    """All domain event types in the system."""

    # Connection Events
    PLAYER_CONNECTED = auto()
    PLAYER_DISCONNECTED = auto()
    PLAYER_RECONNECTED = auto()
    CONNECTION_HEARTBEAT = auto()
    CLIENT_READY = auto()

    # Room Management Events
    ROOM_CREATED = auto()
    PLAYER_JOINED_ROOM = auto()
    PLAYER_LEFT_ROOM = auto()
    ROOM_CLOSED = auto()
    HOST_CHANGED = auto()
    BOT_ADDED = auto()
    PLAYER_REMOVED = auto()
    ROOM_STATE_REQUESTED = auto()

    # Lobby Events
    ROOM_LIST_REQUESTED = auto()
    ROOM_LIST_UPDATED = auto()

    # Game Flow Events
    GAME_STARTED = auto()
    GAME_ENDED = auto()
    ROUND_STARTED = auto()
    ROUND_COMPLETED = auto()
    PHASE_CHANGED = auto()

    # Game Action Events
    PIECES_DEALT = auto()
    WEAK_HAND_DETECTED = auto()
    REDEAL_REQUESTED = auto()
    REDEAL_DECISION_MADE = auto()
    REDEAL_EXECUTED = auto()
    DECLARATION_MADE = auto()
    PIECES_PLAYED = auto()
    TURN_COMPLETED = auto()
    TURN_WINNER_DETERMINED = auto()
    PLAYER_READY_FOR_NEXT = auto()

    # Scoring Events
    SCORES_CALCULATED = auto()
    WINNER_DETERMINED = auto()
    GAME_OVER_TRIGGERED = auto()

    # Error Events
    INVALID_ACTION_ATTEMPTED = auto()
    ERROR_OCCURRED = auto()

    @property
    def event_name(self) -> str:
        """Get the event name as a string."""
        return self.name
