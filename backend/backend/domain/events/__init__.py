"""
Domain Events Module

This module contains all domain events that represent things that have happened
in the game. Events are immutable records of state changes and are used to
decouple the domain logic from infrastructure concerns like broadcasting.
"""

from .base import DomainEvent, GameEvent, EventMetadata
from .event_types import EventType

__all__ = ['DomainEvent', 'GameEvent', 'EventMetadata', 'EventType']