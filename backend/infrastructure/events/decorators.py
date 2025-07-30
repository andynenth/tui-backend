"""
Decorators for event handling.

These decorators make it easy to register event handlers.
"""

import functools
from typing import Type, Callable, Optional
from domain.events.base import DomainEvent
from .in_memory_event_bus import get_event_bus


def event_handler(
    event_type: Type[DomainEvent],
    priority: int = 0,
    event_bus: Optional["InMemoryEventBus"] = None,
):
    """
    Decorator to register a function as an event handler.

    Usage:
        @event_handler(PlayerJoinedRoom, priority=10)
        async def handle_player_joined(event: PlayerJoinedRoom):
            # Handle the event
            pass

    Args:
        event_type: The type of event to handle
        priority: Handler priority (higher = called first)
        event_bus: Optional event bus instance (uses global if not provided)
    """

    def decorator(func: Callable):
        # Register the handler immediately
        bus = event_bus or get_event_bus()
        bus.subscribe(event_type, func, priority)

        # Mark the function as an event handler
        func._is_event_handler = True
        func._event_type = event_type
        func._priority = priority

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def handles(*event_types: Type[DomainEvent], priority: int = 0):
    """
    Decorator to register a handler for multiple event types.

    Usage:
        @handles(PlayerJoinedRoom, PlayerLeftRoom, priority=5)
        async def handle_room_changes(event: Union[PlayerJoinedRoom, PlayerLeftRoom]):
            # Handle either event type
            pass

    Args:
        *event_types: The types of events to handle
        priority: Handler priority for all event types
    """

    def decorator(func: Callable):
        bus = get_event_bus()

        # Register for each event type
        for event_type in event_types:
            bus.subscribe(event_type, func, priority)

        # Mark the function
        func._is_event_handler = True
        func._event_types = event_types
        func._priority = priority

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator


class EventHandlerRegistry:
    """
    Registry for discovering and auto-registering event handlers.

    This can scan modules and automatically register decorated handlers.
    """

    @staticmethod
    def scan_module(module):
        """
        Scan a module for event handlers and register them.

        Args:
            module: The module to scan
        """
        bus = get_event_bus()
        registered = 0

        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            # Check if it's a decorated event handler
            if hasattr(attr, "_is_event_handler") and callable(attr):
                # Single event type handler
                if hasattr(attr, "_event_type"):
                    bus.subscribe(attr._event_type, attr, attr._priority)
                    registered += 1

                # Multiple event types handler
                elif hasattr(attr, "_event_types"):
                    for event_type in attr._event_types:
                        bus.subscribe(event_type, attr, attr._priority)
                    registered += 1

        return registered
