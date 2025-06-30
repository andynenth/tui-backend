# backend/engine/state_machine/events/__init__.py

"""
Event-driven state machine components

This module contains the event-driven architecture components that replace
the polling-based state machine with immediate event processing.
"""

from .event_types import GameEvent, EventResult, UserEvent, SystemEvent, TimerEvent, StateEvent
from .event_processor import EventProcessor

__all__ = [
    'GameEvent',
    'EventResult', 
    'UserEvent',
    'SystemEvent',
    'TimerEvent',
    'StateEvent',
    'EventProcessor'
]