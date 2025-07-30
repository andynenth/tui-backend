"""
Lobby use cases.

These use cases handle room discovery, listing available rooms,
and providing room information for the lobby interface.
"""

from .get_room_list import GetRoomListUseCase
from .get_room_details import GetRoomDetailsUseCase

__all__ = ["GetRoomListUseCase", "GetRoomDetailsUseCase"]
