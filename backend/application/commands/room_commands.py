# application/commands/room_commands.py
"""
Room-related commands for the application layer.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from .base import Command


@dataclass
class CreateRoomCommand(Command):
    """Command to create a new game room."""
    host_name: str
    room_settings: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__init__()


@dataclass
class JoinRoomCommand(Command):
    """Command to join an existing room."""
    room_id: str
    player_name: str
    player_token: Optional[str] = None
    
    def __post_init__(self):
        super().__init__()


@dataclass
class LeaveRoomCommand(Command):
    """Command to leave a room."""
    room_id: str
    player_name: str
    
    def __post_init__(self):
        super().__init__()


@dataclass
class UpdateRoomSettingsCommand(Command):
    """Command to update room settings."""
    room_id: str
    player_name: str  # Must be the host
    settings: Dict[str, Any]
    
    def __post_init__(self):
        super().__init__()


@dataclass
class KickPlayerCommand(Command):
    """Command to kick a player from a room."""
    room_id: str
    requesting_player: str  # Must be the host
    player_to_kick: str
    
    def __post_init__(self):
        super().__init__()


@dataclass
class TransferHostCommand(Command):
    """Command to transfer host privileges to another player."""
    room_id: str
    current_host: str
    new_host: str
    
    def __post_init__(self):
        super().__init__()


@dataclass
class CloseRoomCommand(Command):
    """Command to close a room."""
    room_id: str
    requesting_player: str  # Must be the host
    
    def __post_init__(self):
        super().__init__()