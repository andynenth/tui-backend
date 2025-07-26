"""
Message queue entities for disconnected players.

These entities manage queued messages that accumulate while
a player is disconnected, ensuring they don't miss critical
game events.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

from domain.value_objects.identifiers import PlayerId, RoomId
from domain.events.base import DomainEvent, EventMetadata
from domain.events.message_queue_events import MessageQueued, MessageQueueOverflow


@dataclass
class QueuedMessage:
    """
    A message queued for a disconnected player.
    
    Value object representing a single queued message.
    """
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    sequence: int
    is_critical: bool = False
    
    def age_seconds(self) -> float:
        """Get age of message in seconds."""
        return (datetime.utcnow() - self.timestamp).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "sequence": self.sequence,
            "is_critical": self.is_critical
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueuedMessage":
        """Create from dictionary."""
        return cls(
            event_type=data["event_type"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            sequence=data["sequence"],
            is_critical=data.get("is_critical", False)
        )


@dataclass
class PlayerQueue:
    """
    Message queue for a specific player.
    
    This aggregate manages the queue of messages for a disconnected
    player, including size limits and critical message prioritization.
    """
    player_id: PlayerId
    room_id: RoomId
    messages: List[QueuedMessage] = field(default_factory=list)
    max_size: int = 100
    last_sequence: int = 0
    
    # Domain events
    _events: List[DomainEvent] = field(default_factory=list, init=False)
    
    @property
    def events(self) -> List[DomainEvent]:
        """Get domain events."""
        return self._events.copy()
    
    def clear_events(self) -> None:
        """Clear domain events."""
        self._events.clear()
    
    def _emit_event(self, event: DomainEvent) -> None:
        """Emit a domain event."""
        self._events.append(event)
    
    def add_message(
        self, 
        event_type: str, 
        data: Dict[str, Any], 
        is_critical: bool = False
    ) -> None:
        """
        Add a message to the queue.
        
        Args:
            event_type: Type of event being queued
            data: Event data
            is_critical: Whether this is a critical message
        """
        self.last_sequence += 1
        message = QueuedMessage(
            event_type=event_type,
            data=data,
            timestamp=datetime.utcnow(),
            sequence=self.last_sequence,
            is_critical=is_critical
        )
        
        self.messages.append(message)
        
        # Emit event for message queued
        self._emit_event(MessageQueued(
            room_id=str(self.room_id),
            player_name=str(self.player_id),
            event_type_queued=event_type,
            is_critical=is_critical,
            queue_size=len(self.messages),
            metadata=EventMetadata()
        ))
        
        # Trim if needed
        self._trim_if_needed()
    
    def _trim_if_needed(self) -> None:
        """
        Trim queue if it exceeds max size.
        
        Prioritizes critical messages when trimming.
        """
        if len(self.messages) <= self.max_size:
            return
        
        # Separate critical and non-critical
        critical = [m for m in self.messages if m.is_critical]
        non_critical = [m for m in self.messages if not m.is_critical]
        
        # Calculate how many to drop
        total_to_drop = len(self.messages) - self.max_size
        dropped_count = 0
        
        # Try to drop non-critical first
        if non_critical and total_to_drop > 0:
            drop_from_non_critical = min(len(non_critical), total_to_drop)
            non_critical = non_critical[drop_from_non_critical:]
            dropped_count += drop_from_non_critical
            total_to_drop -= drop_from_non_critical
        
        # If still need to drop, take from critical (oldest first)
        if total_to_drop > 0:
            critical = critical[total_to_drop:]
            dropped_count += total_to_drop
        
        # Rebuild messages list
        self.messages = critical + non_critical
        
        # Sort by sequence to maintain order
        self.messages.sort(key=lambda m: m.sequence)
        
        # Emit overflow event if messages were dropped
        if dropped_count > 0:
            self._emit_event(MessageQueueOverflow(
                room_id=str(self.room_id),
                player_name=str(self.player_id),
                dropped_count=dropped_count,
                retained_critical_count=len([m for m in self.messages if m.is_critical]),
                queue_capacity=self.max_size,
                metadata=EventMetadata()
            ))
    
    def get_messages_since(self, sequence: int) -> List[QueuedMessage]:
        """
        Get all messages after a sequence number.
        
        Args:
            sequence: Sequence number to get messages after
            
        Returns:
            List of messages with sequence > provided sequence
        """
        return [m for m in self.messages if m.sequence > sequence]
    
    def get_all_messages(self) -> List[QueuedMessage]:
        """Get all queued messages."""
        return self.messages.copy()
    
    def clear(self) -> None:
        """Clear all messages from the queue."""
        self.messages.clear()
        self.last_sequence = 0
    
    def size(self) -> int:
        """Get current queue size."""
        return len(self.messages)
    
    def critical_count(self) -> int:
        """Get count of critical messages."""
        return sum(1 for m in self.messages if m.is_critical)
    
    def oldest_message_age(self) -> Optional[float]:
        """Get age of oldest message in seconds."""
        if not self.messages:
            return None
        return self.messages[0].age_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "player_id": str(self.player_id),
            "room_id": str(self.room_id),
            "messages": [m.to_dict() for m in self.messages],
            "max_size": self.max_size,
            "last_sequence": self.last_sequence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlayerQueue":
        """Create from dictionary."""
        queue = cls(
            player_id=PlayerId(data["player_id"]),
            room_id=RoomId(data["room_id"]),
            max_size=data.get("max_size", 100),
            last_sequence=data.get("last_sequence", 0)
        )
        
        # Restore messages
        queue.messages = [
            QueuedMessage.from_dict(m) for m in data.get("messages", [])
        ]
        
        return queue