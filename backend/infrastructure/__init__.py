# infrastructure/__init__.py
"""
Infrastructure layer of the Liap Tui game.

This layer contains:
- WebSocket: Connection management and broadcasting
- Persistence: Repository implementations
- State Machine: Game state management adapters
- Bot: AI strategy implementations
- Auth: Authentication implementations

The infrastructure layer implements the interfaces defined
in the domain and application layers.
"""

# WebSocket
from .websocket.connection_manager import ConnectionManager, ConnectionInfo
from .websocket.broadcast_service import BroadcastService, WebSocketMessage
from .websocket.notification_adapter import WebSocketNotificationAdapter

# Persistence
from .persistence.game_repository_impl import (
    InMemoryGameRepository,
    FileBasedGameRepository
)
from .persistence.room_repository_impl import RoomRepository, Room
from .persistence.event_publisher_impl import (
    InMemoryEventPublisher,
    InMemoryEventStore
)

# State Machine
from .state_machine.state_adapter import (
    StateMachineAdapter,
    StateMachineRepository,
    StateTransitionResult
)

# Bot
from .bot.ai_strategy import (
    EasyBotStrategy,
    MediumBotStrategy,
    SimpleBotStrategyFactory
)

# Auth
from .auth.simple_auth_adapter import SimpleAuthAdapter

__all__ = [
    # WebSocket
    'ConnectionManager',
    'ConnectionInfo',
    'BroadcastService',
    'WebSocketMessage',
    'WebSocketNotificationAdapter',
    
    # Persistence
    'InMemoryGameRepository',
    'FileBasedGameRepository',
    'RoomRepository',
    'Room',
    'InMemoryEventPublisher',
    'InMemoryEventStore',
    
    # State Machine
    'StateMachineAdapter',
    'StateMachineRepository',
    'StateTransitionResult',
    
    # Bot
    'EasyBotStrategy',
    'MediumBotStrategy',
    'SimpleBotStrategyFactory',
    
    # Auth
    'SimpleAuthAdapter',
]