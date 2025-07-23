# application/commands/__init__.py
"""
Commands represent user intentions in the application.

Commands:
- Encapsulate all data needed for an operation
- Are immutable once created
- Can be validated before execution
- Support command/query separation
"""

from .base import (
    Command,
    CommandResult,
    CommandHandler,
    CommandBus,
    CommandValidator,
    ValidatingCommandBus
)
from .room_commands import (
    CreateRoomCommand,
    JoinRoomCommand,
    LeaveRoomCommand,
    UpdateRoomSettingsCommand,
    KickPlayerCommand,
    TransferHostCommand,
    CloseRoomCommand
)
from .game_commands import (
    StartGameCommand,
    DeclareCommand,
    PlayTurnCommand,
    AcceptRedealCommand,
    DeclineRedealCommand,
    RequestRedealCommand,
    EndGameCommand,
    PauseGameCommand,
    ResumeGameCommand,
    AddBotCommand,
    RemoveBotCommand,
    ConfigureBotCommand
)

__all__ = [
    # Base
    'Command',
    'CommandResult',
    'CommandHandler',
    'CommandBus',
    'CommandValidator',
    'ValidatingCommandBus',
    
    # Room Commands
    'CreateRoomCommand',
    'JoinRoomCommand',
    'LeaveRoomCommand',
    'UpdateRoomSettingsCommand',
    'KickPlayerCommand',
    'TransferHostCommand',
    'CloseRoomCommand',
    
    # Game Commands
    'StartGameCommand',
    'DeclareCommand',
    'PlayTurnCommand',
    'AcceptRedealCommand',
    'DeclineRedealCommand',
    'RequestRedealCommand',
    'EndGameCommand',
    'PauseGameCommand',
    'ResumeGameCommand',
    'AddBotCommand',
    'RemoveBotCommand',
    'ConfigureBotCommand',
]