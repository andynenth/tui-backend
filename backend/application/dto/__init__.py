"""
Data Transfer Objects (DTOs) for the application layer.

DTOs define the structure of data passed into and out of use cases.
They provide a clear contract between layers and enable validation.
"""

from .base import Request, Response
from .common import PlayerInfo, RoomInfo, GameStateInfo

__all__ = [
    # Base classes
    "Request",
    "Response",
    # Common DTOs
    "PlayerInfo",
    "RoomInfo",
    "GameStateInfo",
]
