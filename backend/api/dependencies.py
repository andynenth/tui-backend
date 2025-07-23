# api/dependencies.py
"""
Dependency injection container for the API layer.
"""

from typing import Optional
import logging

# Domain
from backend.domain.interfaces.event_publisher import EventPublisher
from backend.domain.interfaces.bot_strategy import BotStrategyFactory

# Application
from backend.application.commands.base import CommandBus, ValidatingCommandBus
from backend.application.use_cases import (
    CreateRoomUseCase,
    JoinRoomUseCase,
    StartGameUseCase,
    PlayTurnUseCase,
    DeclarePilesUseCase
)
from backend.application.use_cases.room_management import (
    UpdateRoomSettingsUseCase,
    KickPlayerUseCase,
    TransferHostUseCase,
    CloseRoomUseCase,
    LeaveRoomUseCase
)
from backend.application.use_cases.bot_management import (
    AddBotUseCase,
    RemoveBotUseCase,
    ConfigureBotUseCase
)
from backend.application.services import (
    GameService,
    RoomService,
    BotService
)
from backend.application.interfaces.notification_service import NotificationService
from backend.application.interfaces.authentication_service import AuthenticationService

# Infrastructure
from backend.infrastructure import (
    ConnectionManager,
    BroadcastService,
    WebSocketNotificationAdapter,
    InMemoryGameRepository,
    RoomRepository,
    InMemoryEventPublisher,
    InMemoryEventStore,
    StateMachineRepository,
    SimpleBotStrategyFactory,
    SimpleAuthAdapter
)

# Application Events
from backend.application.events import InMemoryEventBus
from backend.application.events.game_event_handlers import (
    GameNotificationHandler,
    GameStateUpdateHandler,
    BotActionHandler,
    AuditLogHandler
)

# Infrastructure Events
from backend.infrastructure.events import (
    EventBusAdapter,
    EventStoreAdapter,
    DomainEventPublisher
)

logger = logging.getLogger(__name__)


class DependencyContainer:
    """
    Dependency injection container.
    
    This container manages all dependencies and their lifecycle.
    It provides a centralized place to configure the application.
    """
    
    def __init__(self):
        """Initialize the container with all dependencies."""
        # Infrastructure - Core Services
        self._connection_manager = ConnectionManager()
        self._broadcast_service = BroadcastService()
        self._event_store_impl = InMemoryEventStore()
        
        # Application - Event Bus
        self._event_bus = InMemoryEventBus()
        
        # Infrastructure - Event System
        self._event_publisher = DomainEventPublisher(
            event_bus=self._event_bus,
            enable_sync=True,
            enable_async=True
        )
        
        # Event Store with bus integration
        self._event_store = EventStoreAdapter(
            event_store=self._event_store_impl,
            event_bus=self._event_bus
        )
        
        # Infrastructure - Authentication
        self._auth_service = SimpleAuthAdapter()
        
        # Infrastructure - Notification
        self._notification_service = WebSocketNotificationAdapter(
            connection_manager=self._connection_manager,
            broadcast_service=self._broadcast_service
        )
        
        # Infrastructure - Repositories
        self._game_repository = InMemoryGameRepository()
        self._room_repository = RoomRepository()
        self._state_machine_repository = StateMachineRepository(
            event_publisher=self._event_publisher,
            notification_service=self._notification_service
        )
        
        # Infrastructure - Bot
        self._bot_strategy_factory = SimpleBotStrategyFactory()
        
        # Application - Services
        self._game_service = GameService(
            game_repository=self._game_repository,
            event_publisher=self._event_publisher,
            notification_service=self._notification_service
        )
        
        self._room_service = RoomService(
            room_repository=self._room_repository,
            game_repository=self._game_repository,
            event_publisher=self._event_publisher,
            notification_service=self._notification_service
        )
        
        self._bot_service = BotService(
            bot_strategy_factory=self._bot_strategy_factory,
            event_publisher=self._event_publisher,
            notification_service=self._notification_service
        )
        
        # Application - Use Cases
        self._create_room_use_case = CreateRoomUseCase(
            room_repository=self._room_repository,
            auth_service=self._auth_service,
            event_publisher=self._event_publisher,
            notification_service=self._notification_service
        )
        
        self._join_room_use_case = JoinRoomUseCase(
            room_repository=self._room_repository,
            game_repository=self._game_repository,
            auth_service=self._auth_service,
            event_publisher=self._event_publisher,
            notification_service=self._notification_service
        )
        
        self._start_game_use_case = StartGameUseCase(
            room_repository=self._room_repository,
            game_repository=self._game_repository,
            auth_service=self._auth_service,
            event_publisher=self._event_publisher,
            notification_service=self._notification_service,
            state_machine_factory=self._state_machine_repository
        )
        
        self._play_turn_use_case = PlayTurnUseCase(
            room_repository=self._room_repository,
            game_repository=self._game_repository,
            state_machine_repository=self._state_machine_repository,
            event_publisher=self._event_publisher,
            notification_service=self._notification_service
        )
        
        self._declare_piles_use_case = DeclarePilesUseCase(
            room_repository=self._room_repository,
            game_repository=self._game_repository,
            state_machine_repository=self._state_machine_repository,
            event_publisher=self._event_publisher,
            notification_service=self._notification_service
        )
        
        # Room management use cases
        self._update_room_settings_use_case = UpdateRoomSettingsUseCase(
            room_service=self._room_service,
            notification_service=self._notification_service
        )
        
        self._kick_player_use_case = KickPlayerUseCase(
            room_service=self._room_service,
            notification_service=self._notification_service
        )
        
        self._transfer_host_use_case = TransferHostUseCase(
            room_repository=self._room_repository,
            event_publisher=self._event_publisher,
            notification_service=self._notification_service
        )
        
        self._close_room_use_case = CloseRoomUseCase(
            room_repository=self._room_repository,
            event_publisher=self._event_publisher,
            notification_service=self._notification_service
        )
        
        self._leave_room_use_case = LeaveRoomUseCase(
            room_service=self._room_service
        )
        
        # Bot management use cases
        self._add_bot_use_case = AddBotUseCase(
            room_service=self._room_service,
            bot_service=self._bot_service,
            room_repository=self._room_repository
        )
        
        self._remove_bot_use_case = RemoveBotUseCase(
            room_service=self._room_service,
            bot_service=self._bot_service
        )
        
        self._configure_bot_use_case = ConfigureBotUseCase(
            room_service=self._room_service,
            bot_service=self._bot_service
        )
        
        # Application - Command Bus
        self._command_bus = ValidatingCommandBus()
        self._register_command_handlers()
        
        # Event Handlers
        self._register_event_handlers()
        
        logger.info("Dependency container initialized")
    
    def _register_command_handlers(self):
        """Register all command handlers with the command bus."""
        from backend.application.commands import (
            CreateRoomCommand,
            JoinRoomCommand,
            LeaveRoomCommand,
            UpdateRoomSettingsCommand,
            KickPlayerCommand,
            TransferHostCommand,
            CloseRoomCommand,
            StartGameCommand,
            PlayTurnCommand,
            DeclareCommand,
            AddBotCommand,
            RemoveBotCommand,
            ConfigureBotCommand
        )
        
        # Room commands
        self._command_bus.register_handler(
            CreateRoomCommand,
            self._create_room_use_case
        )
        self._command_bus.register_handler(
            JoinRoomCommand,
            self._join_room_use_case
        )
        self._command_bus.register_handler(
            LeaveRoomCommand,
            self._leave_room_use_case
        )
        self._command_bus.register_handler(
            UpdateRoomSettingsCommand,
            self._update_room_settings_use_case
        )
        self._command_bus.register_handler(
            KickPlayerCommand,
            self._kick_player_use_case
        )
        self._command_bus.register_handler(
            TransferHostCommand,
            self._transfer_host_use_case
        )
        self._command_bus.register_handler(
            CloseRoomCommand,
            self._close_room_use_case
        )
        
        # Game commands
        self._command_bus.register_handler(
            StartGameCommand,
            self._start_game_use_case
        )
        self._command_bus.register_handler(
            PlayTurnCommand,
            self._play_turn_use_case
        )
        self._command_bus.register_handler(
            DeclareCommand,
            self._declare_piles_use_case
        )
        
        # Bot commands
        self._command_bus.register_handler(
            AddBotCommand,
            self._add_bot_use_case
        )
        self._command_bus.register_handler(
            RemoveBotCommand,
            self._remove_bot_use_case
        )
        self._command_bus.register_handler(
            ConfigureBotCommand,
            self._configure_bot_use_case
        )
    
    def _register_event_handlers(self):
        """Register event handlers with the event bus."""
        from backend.domain.events.game_events import (
            GameStartedEvent,
            RoundStartedEvent,
            TurnPlayedEvent,
            PhaseChangedEvent,
            PlayerDeclaredEvent,
            RoundEndedEvent,
            GameEndedEvent
        )
        from backend.domain.events.player_events import (
            PlayerJoinedEvent,
            PlayerLeftEvent
        )
        
        # Create handlers
        self._game_notification_handler = GameNotificationHandler(
            notification_service=self._notification_service,
            room_service=self._room_service
        )
        
        self._game_state_handler = GameStateUpdateHandler(
            room_service=self._room_service
        )
        
        self._bot_action_handler = BotActionHandler(
            bot_service=self._bot_service
        )
        
        self._audit_log_handler = AuditLogHandler()
        
        # Register notification handler for all game events
        game_events = [
            GameStartedEvent,
            RoundStartedEvent,
            TurnPlayedEvent,
            PhaseChangedEvent,
            PlayerDeclaredEvent,
            RoundEndedEvent,
            GameEndedEvent,
            PlayerJoinedEvent,
            PlayerLeftEvent
        ]
        
        for event_type in game_events:
            self._event_bus.subscribe(
                event_type,
                self._game_notification_handler.handle,
                priority=100  # High priority for notifications
            )
            
            # Also register state handler
            self._event_bus.subscribe(
                event_type,
                self._game_state_handler.handle,
                priority=90
            )
            
            # Register audit handler
            self._event_bus.subscribe(
                event_type,
                self._audit_log_handler.handle,
                priority=10  # Low priority for auditing
            )
        
        # Register bot handler for specific events
        bot_trigger_events = [PhaseChangedEvent, TurnPlayedEvent]
        for event_type in bot_trigger_events:
            self._event_bus.subscribe(
                event_type,
                self._bot_action_handler.handle,
                priority=80
            )
        
        logger.info("Event handlers registered")
    
    # Getters for dependencies
    
    @property
    def connection_manager(self) -> ConnectionManager:
        return self._connection_manager
    
    @property
    def broadcast_service(self) -> BroadcastService:
        return self._broadcast_service
    
    @property
    def notification_service(self) -> NotificationService:
        return self._notification_service
    
    @property
    def auth_service(self) -> AuthenticationService:
        return self._auth_service
    
    @property
    def event_publisher(self) -> EventPublisher:
        return self._event_publisher
    
    @property
    def game_repository(self):
        return self._game_repository
    
    @property
    def room_repository(self):
        return self._room_repository
    
    @property
    def state_machine_repository(self):
        return self._state_machine_repository
    
    @property
    def game_service(self) -> GameService:
        return self._game_service
    
    @property
    def room_service(self) -> RoomService:
        return self._room_service
    
    @property
    def bot_service(self) -> BotService:
        return self._bot_service
    
    @property
    def command_bus(self) -> CommandBus:
        return self._command_bus
    
    @property
    def event_bus(self) -> InMemoryEventBus:
        return self._event_bus
    
    @property
    def event_store(self) -> EventStoreAdapter:
        return self._event_store
    
    # Use case getters
    
    @property
    def create_room_use_case(self) -> CreateRoomUseCase:
        return self._create_room_use_case
    
    @property
    def join_room_use_case(self) -> JoinRoomUseCase:
        return self._join_room_use_case
    
    @property
    def start_game_use_case(self) -> StartGameUseCase:
        return self._start_game_use_case
    
    @property
    def play_turn_use_case(self) -> PlayTurnUseCase:
        return self._play_turn_use_case
    
    @property
    def declare_piles_use_case(self) -> DeclarePilesUseCase:
        return self._declare_piles_use_case
    
    async def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up dependency container")
        # Add cleanup logic if needed


# Global container instance
_container: Optional[DependencyContainer] = None


def get_container() -> DependencyContainer:
    """Get the global dependency container."""
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container


def reset_container():
    """Reset the global container (mainly for testing)."""
    global _container
    if _container:
        # Clean up if needed
        pass
    _container = None