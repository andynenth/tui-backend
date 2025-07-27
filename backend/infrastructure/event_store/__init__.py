"""
Event store infrastructure for event sourcing and CQRS.

This module provides:
- Hybrid event store with memory-first access
- Event sourcing abstractions for aggregates
- Projection support for read models
- Real-time event subscriptions
"""

from .hybrid_event_store import (
    Event,
    EventType,
    EventStream,
    IEventStore,
    HybridEventStore
)

from .event_sourcing import (
    DomainEvent,
    EventSourcedAggregate,
    EventSourcedRepository,
    Projection,
    ProjectionManager,
    # Example events
    GameCreatedEvent,
    GameStartedEvent,
    PlayerActionEvent,
    PhaseChangedEvent
)

__all__ = [
    # Event store
    'Event',
    'EventType',
    'EventStream',
    'IEventStore',
    'HybridEventStore',
    
    # Event sourcing
    'DomainEvent',
    'EventSourcedAggregate',
    'EventSourcedRepository',
    'Projection',
    'ProjectionManager',
    
    # Domain events
    'GameCreatedEvent',
    'GameStartedEvent', 
    'PlayerActionEvent',
    'PhaseChangedEvent'
]