"""
Value objects - Immutable objects without identity.

Value objects are defined by their attributes, not identity.
Two value objects with the same attributes are considered equal.
"""

from .piece import Piece
from .declaration import Declaration
from .hand_strength import HandStrength
from .identifiers import PlayerId, RoomId, GameId
from .connection_status import ConnectionStatus
from .room_status import RoomStatus
from .player_role import PlayerRole

__all__ = [
    "Piece",
    "Declaration",
    "HandStrength",
    "PlayerId",
    "RoomId",
    "GameId",
    "ConnectionStatus",
    "RoomStatus",
    "PlayerRole"
]