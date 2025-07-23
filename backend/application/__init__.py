# application/__init__.py
"""
Application layer of the Liap Tui game.

This layer contains:
- Use Cases: Business operations orchestration
- Application Services: Complex operations coordination
- Commands: User intention encapsulation
- Interfaces: Abstractions for infrastructure

The application layer orchestrates domain operations and
coordinates with infrastructure services.
"""

# Commands
from .commands.base import (
    Command,
    CommandResult,
    CommandHandler,
    CommandBus,
    CommandValidator,
    ValidatingCommandBus
)
from .commands.room_commands import (
    CreateRoomCommand,
    JoinRoomCommand,
    LeaveRoomCommand,
    UpdateRoomSettingsCommand,
    KickPlayerCommand,
    TransferHostCommand,
    CloseRoomCommand
)
from .commands.game_commands import (
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

# Use Cases
from .use_cases.create_room import CreateRoomUseCase, RoomCreationResult
from .use_cases.join_room import JoinRoomUseCase, JoinRoomResult
from .use_cases.start_game import StartGameUseCase, StartGameResult
from .use_cases.play_turn import PlayTurnUseCase, PlayTurnResult
from .use_cases.declare_piles import DeclarePilesUseCase, DeclareResult

# Services
from .services.game_service import GameService
from .services.room_service import RoomService, RoomInfo
from .services.bot_service import BotService, BotInfo

# Interfaces
from .interfaces.notification_service import (
    NotificationService,
    NotificationType,
    Notification
)
from .interfaces.authentication_service import (
    AuthenticationService,
    PlayerIdentity,
    AuthToken
)

__all__ = [
    # Commands
    'Command',
    'CommandResult',
    'CommandHandler',
    'CommandBus',
    'CommandValidator',
    'ValidatingCommandBus',
    'CreateRoomCommand',
    'JoinRoomCommand',
    'LeaveRoomCommand',
    'UpdateRoomSettingsCommand',
    'KickPlayerCommand',
    'TransferHostCommand',
    'CloseRoomCommand',
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
    
    # Use Cases
    'CreateRoomUseCase',
    'RoomCreationResult',
    'JoinRoomUseCase',
    'JoinRoomResult',
    'StartGameUseCase',
    'StartGameResult',
    'PlayTurnUseCase',
    'PlayTurnResult',
    'DeclarePilesUseCase',
    'DeclareResult',
    
    # Services
    'GameService',
    'RoomService',
    'RoomInfo',
    'BotService',
    'BotInfo',
    
    # Interfaces
    'NotificationService',
    'NotificationType',
    'Notification',
    'AuthenticationService',
    'PlayerIdentity',
    'AuthToken',
]