# domain/events/base.py
"""
Base domain event classes.
Domain events represent things that have happened in the domain.
"""

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict
import uuid


@dataclass(frozen=True)
class DomainEvent(ABC):
    """
    Base class for all domain events.
    
    Domain events are immutable records of things that have happened
    in the domain. They are used for:
    - Decoupling domain logic from infrastructure
    - Event sourcing
    - Audit trails
    - Integration between bounded contexts
    """
    
    @property
    def event_type(self) -> str:
        """Get the event type name."""
        return self.__class__.__name__
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary for serialization.
        Can be overridden by subclasses for custom serialization.
        """
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'data': self._get_event_data()
        }
    
    def _get_event_data(self) -> Dict[str, Any]:
        """
        Get event-specific data.
        Should be overridden by subclasses.
        """
        # Default implementation excludes metadata fields
        data = {}
        for key, value in self.__dict__.items():
            if key not in ['event_id', 'occurred_at']:
                data[key] = value
        return data


@dataclass(frozen=True, kw_only=True)
class SimpleDomainEvent(DomainEvent):
    """
    Base class for simple domain events that don't belong to an aggregate.
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True, kw_only=True)
class AggregateEvent(DomainEvent):
    """
    Base class for events that belong to an aggregate.
    
    Aggregate events always have an aggregate_id that identifies
    which aggregate instance the event belongs to.
    """
    aggregate_id: str
    aggregate_type: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    
    def _get_event_data(self) -> Dict[str, Any]:
        """Include aggregate information in event data."""
        data = super()._get_event_data()
        data.update({
            'aggregate_id': self.aggregate_id,
            'aggregate_type': self.aggregate_type
        })
        return data