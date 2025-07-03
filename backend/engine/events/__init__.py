# backend/engine/events/__init__.py

"""
📡 **Event System Module** - Phase 4 Event System Unification

This module provides a centralized event bus for optimal cross-component communication,
replacing direct method calls with event-driven architecture.

Components:
- EventBus: Central event distribution hub
- EventTypes: Strongly-typed event definitions
- EventHandlers: Event processing abstractions
- EventMiddleware: Cross-cutting concerns (logging, metrics, etc.)
"""

from .event_bus import EventBus, get_global_event_bus, reset_global_event_bus
from .event_types import (
    GameEvent,
    EventType,
    EventPriority,
    PhaseChangeEvent,
    ActionEvent,
    BroadcastEvent,
    BotNotificationEvent,
    StateUpdateEvent,
    ErrorEvent
)
from .event_handlers import (
    IEventHandler,
    EventHandler,
    AsyncEventHandler,
    EventHandlerRegistry,
    create_simple_handler,
    create_async_handler
)
from .event_middleware import (
    IEventMiddleware,
    LoggingMiddleware,
    MetricsMiddleware,
    ErrorHandlingMiddleware,
    ValidationMiddleware
)
from .event_routing import (
    EventRouter,
    RoutingRule,
    RoutingStrategy,
    create_event_type_rule,
    create_room_rule,
    create_player_rule,
    create_pattern_rule,
    create_priority_rule,
    create_conditional_rule,
    create_rate_limited_rule
)
from .game_event_handlers import (
    PhaseChangeHandler,
    ActionHandler,
    BroadcastHandler,
    BotNotificationHandler,
    StateUpdateHandler,
    ErrorHandler,
    create_game_handlers
)
from .integration import (
    EventBusIntegration,
    integrate_event_bus
)

__all__ = [
    # Core event bus
    'EventBus',
    'get_global_event_bus',
    'reset_global_event_bus',
    
    # Event types
    'GameEvent',
    'EventType',
    'EventPriority',
    'PhaseChangeEvent',
    'ActionEvent',
    'BroadcastEvent',
    'BotNotificationEvent',
    'StateUpdateEvent',
    'ErrorEvent',
    
    # Event handlers
    'IEventHandler',
    'EventHandler',
    'AsyncEventHandler',
    'EventHandlerRegistry',
    'create_simple_handler',
    'create_async_handler',
    
    # Middleware
    'IEventMiddleware',
    'LoggingMiddleware',
    'MetricsMiddleware',
    'ErrorHandlingMiddleware',
    'ValidationMiddleware',
    
    # Event routing
    'EventRouter',
    'RoutingRule',
    'RoutingStrategy',
    'create_event_type_rule',
    'create_room_rule',
    'create_player_rule',
    'create_pattern_rule',
    'create_priority_rule',
    'create_conditional_rule',
    'create_rate_limited_rule',
    
    # Game event handlers
    'PhaseChangeHandler',
    'ActionHandler',
    'BroadcastHandler',
    'BotNotificationHandler',
    'StateUpdateHandler',
    'ErrorHandler',
    'create_game_handlers',
    
    # Integration
    'EventBusIntegration',
    'integrate_event_bus'
]