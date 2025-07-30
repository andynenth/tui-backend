"""
Room status value object for representing the current state of a game room.
"""

from enum import Enum


class RoomStatus(Enum):
    """
    Represents the current status of a game room.

    This enum defines all possible states a room can be in throughout
    its lifecycle from creation to completion.
    """

    WAITING = "waiting"  # Room created, waiting for players
    IN_GAME = "in_game"  # Game is actively being played
    COMPLETED = "completed"  # Game has finished
    ABANDONED = "abandoned"  # Room was abandoned by players

    def __str__(self) -> str:
        """Return the string representation of the room status."""
        return self.value

    @property
    def is_active(self) -> bool:
        """Check if the room is in an active state."""
        return self in (RoomStatus.WAITING, RoomStatus.IN_GAME)

    @property
    def is_finished(self) -> bool:
        """Check if the room has finished (completed or abandoned)."""
        return self in (RoomStatus.COMPLETED, RoomStatus.ABANDONED)

    @property
    def can_join(self) -> bool:
        """Check if players can join this room."""
        return self == RoomStatus.WAITING

    @property
    def is_playing(self) -> bool:
        """Check if the room is currently playing a game."""
        return self == RoomStatus.IN_GAME
