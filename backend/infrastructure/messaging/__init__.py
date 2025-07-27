"""
Message queue infrastructure for async task processing.

This module provides message queue abstractions and implementations for
handling asynchronous tasks, event processing, and inter-service communication.
"""

from .base import (
    Message,
    MessagePriority,
    MessageStatus,
    MessageHandler,
    IMessageQueue,
    IMessageRouter,
    IMessageSerializer,
    MessageMetadata,
    DeliveryOptions,
    RetryPolicy
)

from .memory_queue import (
    InMemoryQueue,
    PriorityInMemoryQueue,
    BoundedInMemoryQueue
)

from .routing import (
    MessageRouter,
    RoutePattern,
    TopicRouter,
    DirectRouter,
    PatternRouter
)

from .dead_letter import (
    DeadLetterQueue,
    DeadLetterPolicy,
    DeadLetterHandler,
    RetryableDeadLetterQueue
)

from .serialization import (
    JsonMessageSerializer,
    PickleMessageSerializer,
    MessagePackSerializer,
    CompositeSerializer
)

from .handlers import (
    AsyncMessageHandler,
    BatchMessageHandler,
    ChainedMessageHandler,
    ErrorHandlingWrapper,
    RetryingHandler,
    TimeoutHandler
)

from .game_integration import (
    GameEventQueue,
    GameEventHandler,
    GameEventRouter,
    GameTaskProcessor
)

__all__ = [
    # Base types
    'Message',
    'MessagePriority',
    'MessageStatus',
    'MessageHandler',
    'IMessageQueue',
    'IMessageRouter',
    'IMessageSerializer',
    'MessageMetadata',
    'DeliveryOptions',
    'RetryPolicy',
    
    # Memory queues
    'InMemoryQueue',
    'PriorityInMemoryQueue',
    'BoundedInMemoryQueue',
    
    # Routing
    'MessageRouter',
    'RoutePattern',
    'TopicRouter',
    'DirectRouter',
    'PatternRouter',
    
    # Dead letter
    'DeadLetterQueue',
    'DeadLetterPolicy',
    'DeadLetterHandler',
    'RetryableDeadLetterQueue',
    
    # Serialization
    'JsonMessageSerializer',
    'PickleMessageSerializer',
    'MessagePackSerializer',
    'CompositeSerializer',
    
    # Handlers
    'AsyncMessageHandler',
    'BatchMessageHandler',
    'ChainedMessageHandler',
    'ErrorHandlingWrapper',
    'RetryingHandler',
    'TimeoutHandler',
    
    # Game integration
    'GameEventQueue',
    'GameEventHandler',
    'GameEventRouter',
    'GameTaskProcessor'
]