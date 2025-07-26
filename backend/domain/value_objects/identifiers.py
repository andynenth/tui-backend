"""
Value objects for entity identifiers.

These provide type safety and validation for various IDs used
throughout the domain model.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PlayerId:
    """
    Player identifier value object.
    
    In this game, player IDs are their names.
    """
    value: str
    
    def __post_init__(self):
        """Validate player ID."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Player ID must be a non-empty string")
        if len(self.value) > 20:
            raise ValueError("Player ID must be 20 characters or less")
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __eq__(self, other: Any) -> bool:
        """Equality comparison."""
        if isinstance(other, PlayerId):
            return self.value == other.value
        return False
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self.value)


@dataclass(frozen=True)
class RoomId:
    """
    Room identifier value object.
    
    Room IDs are 6-character alphanumeric codes.
    """
    value: str
    
    def __post_init__(self):
        """Validate room ID."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Room ID must be a non-empty string")
        if len(self.value) != 6:
            raise ValueError("Room ID must be exactly 6 characters")
        if not self.value.isalnum():
            raise ValueError("Room ID must be alphanumeric")
        if not self.value.isupper():
            raise ValueError("Room ID must be uppercase")
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __eq__(self, other: Any) -> bool:
        """Equality comparison."""
        if isinstance(other, RoomId):
            return self.value == other.value
        return False
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self.value)


@dataclass(frozen=True)
class GameId:
    """
    Game identifier value object.
    
    Games are identified by their room ID.
    """
    value: str
    
    def __post_init__(self):
        """Validate game ID."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Game ID must be a non-empty string")
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __eq__(self, other: Any) -> bool:
        """Equality comparison."""
        if isinstance(other, GameId):
            return self.value == other.value
        return False
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self.value)