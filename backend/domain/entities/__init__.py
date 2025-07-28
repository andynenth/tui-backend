"""
Entities - Core business objects with identity.

Entities have unique identities that persist throughout their lifecycle.
Two entities with the same attributes but different IDs are different entities.
"""

from .room import Room, RoomStatus
from .game import Game, GamePhase
from .player import Player, PlayerStats
from .connection import PlayerConnection
from .message_queue import QueuedMessage

__all__ = [
    'Room', 'RoomStatus',
    'Game', 'GamePhase',
    'Player', 'PlayerStats',
    'PlayerConnection',
    'QueuedMessage'
]