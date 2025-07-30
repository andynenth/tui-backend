"""
Base classes for domain events.

Events are immutable records of things that have happened in the domain.
They carry all the data needed to understand what occurred.
"""

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


@dataclass(frozen=True)
class EventMetadata:
    """Metadata that all events carry."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    user_id: Optional[str] = None
    sequence_number: Optional[int] = None
    version: int = 1


@dataclass(frozen=True)
class DomainEvent(ABC):
    """
    Base class for all domain events.

    Events are immutable and represent facts about things that have happened.
    They should be named in past tense (e.g., OrderPlaced, GameStarted).
    """

    metadata: EventMetadata

    @property
    def event_type(self) -> str:
        """Return the type of this event."""
        return self.__class__.__name__

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.event_type,
            "event_id": self.metadata.event_id,
            "timestamp": self.metadata.timestamp.isoformat(),
            "correlation_id": self.metadata.correlation_id,
            "causation_id": self.metadata.causation_id,
            "user_id": self.metadata.user_id,
            "sequence_number": self.metadata.sequence_number,
            "version": self.metadata.version,
            "data": self._get_event_data(),
        }

    def _get_event_data(self) -> Dict[str, Any]:
        """Get event-specific data. Override in subclasses."""
        # Default implementation - exclude metadata
        data = {}
        for key, value in self.__dict__.items():
            if key != "metadata":
                data[key] = value
        return data


@dataclass(frozen=True)
class GameEvent(DomainEvent):
    """
    Base class for game-specific domain events.

    All game events must have a room_id to identify which game they belong to.
    """

    room_id: str

    def _get_event_data(self) -> Dict[str, Any]:
        """Include room_id in event data."""
        data = super()._get_event_data()
        data["room_id"] = self.room_id
        return data
