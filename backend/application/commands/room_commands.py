# application/commands/room_commands.py
"""
Room-related commands for the application layer.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from .base import Command


@dataclass
class CreateRoomCommand(Command):
    """Command to create a new game room."""
    host_name: str
    room_settings: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        super().__init__()
        if self.room_settings is None:
            self.room_settings = {}


@dataclass
class JoinRoomCommand(Command):
    """Command to join an existing room."""
    room_id: str
    player_name: str
    player_token: Optional[str] = None


@dataclass
class LeaveRoomCommand(Command):
    """Command to leave a room."""
    room_id: str
    player_name: str


@dataclass
class UpdateRoomSettingsCommand(Command):
    """Command to update room settings."""
    room_id: str
    player_name: str  # Must be the host
    settings: Dict[str, Any]


@dataclass
class KickPlayerCommand(Command):
    """Command to kick a player from a room."""
    room_id: str
    requesting_player: str  # Must be the host
    player_to_kick: str


@dataclass
class TransferHostCommand(Command):
    """Command to transfer host privileges to another player."""
    room_id: str
    current_host: str
    new_host: str


@dataclass
class CloseRoomCommand(Command):
    """Command to close a room."""
    room_id: str
    requesting_player: str  # Must be the host