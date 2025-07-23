# application/commands/game_commands.py
"""
Game-related commands for the application layer.
"""

from dataclasses import dataclass
from typing import List, Optional

from .base import Command


@dataclass
class StartGameCommand(Command):
    """Command to start a game in a room."""
    room_id: str
    requesting_player: str  # Must be the host
    
    def __post_init__(self):
        super().__init__()


@dataclass
class DeclareCommand(Command):
    """Command to declare pile count in declaration phase."""
    room_id: str
    player_name: str
    declaration: int  # 0-8
    
    def __post_init__(self):
        super().__init__()


@dataclass
class PlayTurnCommand(Command):
    """Command to play pieces in a turn."""
    room_id: str
    player_name: str
    piece_indices: List[int]  # Indices of pieces to play
    
    def __post_init__(self):
        super().__init__()


@dataclass
class AcceptRedealCommand(Command):
    """Command to accept a redeal request."""
    room_id: str
    player_name: str
    
    def __post_init__(self):
        super().__init__()


@dataclass
class DeclineRedealCommand(Command):
    """Command to decline a redeal request."""
    room_id: str
    player_name: str
    
    def __post_init__(self):
        super().__init__()


@dataclass
class RequestRedealCommand(Command):
    """Command to request a redeal (weak hand)."""
    room_id: str
    player_name: str
    reason: Optional[str] = "weak_hand"
    
    def __post_init__(self):
        super().__init__()


@dataclass
class EndGameCommand(Command):
    """Command to end a game early."""
    room_id: str
    requesting_player: str  # Must be the host
    reason: Optional[str] = None
    
    def __post_init__(self):
        super().__init__()


@dataclass
class PauseGameCommand(Command):
    """Command to pause the game."""
    room_id: str
    requesting_player: str
    
    def __post_init__(self):
        super().__init__()


@dataclass
class ResumeGameCommand(Command):
    """Command to resume a paused game."""
    room_id: str
    requesting_player: str
    
    def __post_init__(self):
        super().__init__()


@dataclass
class AddBotCommand(Command):
    """Command to add a bot player to the game."""
    room_id: str
    requesting_player: str  # Must be the host
    bot_name: str
    difficulty: str = "medium"  # easy, medium, hard, expert
    
    def __post_init__(self):
        super().__init__()


@dataclass
class RemoveBotCommand(Command):
    """Command to remove a bot player from the game."""
    room_id: str
    requesting_player: str  # Must be the host
    bot_name: str
    
    def __post_init__(self):
        super().__init__()


@dataclass
class ConfigureBotCommand(Command):
    """Command to configure bot behavior."""
    room_id: str
    requesting_player: str  # Must be the host
    bot_name: str
    difficulty: Optional[str] = None
    
    def __post_init__(self):
        super().__init__()
    play_speed: Optional[int] = None  # milliseconds