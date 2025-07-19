# backend/api/websocket/message_queue.py

"""
Message queue system for disconnected players
Stores critical game events that happened during disconnect
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class QueuedMessage:
    """Represents a queued message for a disconnected player"""

    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    sequence: int
    is_critical: bool = False  # Critical messages must be delivered

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "sequence": self.sequence,
            "is_critical": self.is_critical,
        }


@dataclass
class PlayerQueue:
    """Message queue for a specific player"""

    player_name: str
    room_id: str
    messages: List[QueuedMessage] = field(default_factory=list)
    max_size: int = 100
    last_sequence: int = 0

    def add_message(
        self, event_type: str, data: Dict[str, Any], is_critical: bool = False
    ) -> None:
        """Add a message to the queue"""
        self.last_sequence += 1
        message = QueuedMessage(
            event_type=event_type,
            data=data,
            timestamp=datetime.now(),
            sequence=self.last_sequence,
            is_critical=is_critical,
        )

        self.messages.append(message)

        # Trim queue if too large (keep critical messages)
        if len(self.messages) > self.max_size:
            # Separate critical and non-critical messages
            critical = [m for m in self.messages if m.is_critical]
            non_critical = [m for m in self.messages if not m.is_critical]

            # Keep all critical messages and as many non-critical as fit
            remaining_space = self.max_size - len(critical)
            if remaining_space > 0:
                self.messages = critical + non_critical[-remaining_space:]
            else:
                # If critical messages exceed max_size, keep newest
                self.messages = critical[-self.max_size :]

    def get_messages_since(self, sequence: int) -> List[QueuedMessage]:
        """Get all messages after a certain sequence number"""
        return [m for m in self.messages if m.sequence > sequence]

    def clear(self) -> None:
        """Clear all messages"""
        self.messages.clear()

    def get_summary(self) -> Dict[str, Any]:
        """Get queue summary for debugging"""
        return {
            "player_name": self.player_name,
            "room_id": self.room_id,
            "message_count": len(self.messages),
            "critical_count": len([m for m in self.messages if m.is_critical]),
            "last_sequence": self.last_sequence,
            "oldest_message": (
                self.messages[0].timestamp.isoformat() if self.messages else None
            ),
            "newest_message": (
                self.messages[-1].timestamp.isoformat() if self.messages else None
            ),
        }


class MessageQueueManager:
    """Manages message queues for all disconnected players"""

    # Critical event types that must be delivered
    CRITICAL_EVENTS = {
        "phase_change",
        "turn_resolved",
        "round_complete",
        "game_ended",
        "score_update",
        "host_changed",
    }

    def __init__(self):
        self.queues: Dict[str, PlayerQueue] = {}
        self._lock = asyncio.Lock()

    async def create_queue(self, room_id: str, player_name: str) -> None:
        """Create a message queue for a disconnected player"""
        async with self._lock:
            key = f"{room_id}:{player_name}"
            if key not in self.queues:
                self.queues[key] = PlayerQueue(player_name=player_name, room_id=room_id)
                logger.info(
                    f"Created message queue for {player_name} in room {room_id}"
                )

    async def queue_message(
        self, room_id: str, player_name: str, event_type: str, data: Dict[str, Any]
    ) -> None:
        """Queue a message for a disconnected player"""
        async with self._lock:
            key = f"{room_id}:{player_name}"
            if key in self.queues:
                is_critical = event_type in self.CRITICAL_EVENTS
                self.queues[key].add_message(event_type, data, is_critical)
                logger.debug(
                    f"Queued {event_type} message for {player_name} (critical: {is_critical})"
                )

    async def get_queued_messages(
        self, room_id: str, player_name: str, last_sequence: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all queued messages for a reconnecting player"""
        async with self._lock:
            key = f"{room_id}:{player_name}"
            if key in self.queues:
                messages = self.queues[key].get_messages_since(last_sequence)
                logger.info(
                    f"Retrieved {len(messages)} queued messages for {player_name}"
                )
                return [m.to_dict() for m in messages]
            return []

    async def clear_queue(self, room_id: str, player_name: str) -> None:
        """Clear the message queue for a player"""
        async with self._lock:
            key = f"{room_id}:{player_name}"
            if key in self.queues:
                del self.queues[key]
                logger.info(
                    f"Cleared message queue for {player_name} in room {room_id}"
                )

    async def cleanup_room_queues(self, room_id: str) -> None:
        """Clean up all queues for a room"""
        async with self._lock:
            keys_to_remove = [
                k for k in self.queues.keys() if k.startswith(f"{room_id}:")
            ]
            for key in keys_to_remove:
                del self.queues[key]
            if keys_to_remove:
                logger.info(
                    f"Cleaned up {len(keys_to_remove)} message queues for room {room_id}"
                )

    def get_status(self) -> Dict[str, Any]:
        """Get status of all message queues"""
        return {
            "total_queues": len(self.queues),
            "queues": {key: queue.get_summary() for key, queue in self.queues.items()},
        }

    async def broadcast_to_room_except(
        self,
        room_id: str,
        excluded_players: List[str],
        event_type: str,
        data: Dict[str, Any],
    ) -> None:
        """Queue messages for disconnected players in a room"""
        async with self._lock:
            for key, queue in self.queues.items():
                if (
                    queue.room_id == room_id
                    and queue.player_name not in excluded_players
                ):
                    is_critical = event_type in self.CRITICAL_EVENTS
                    queue.add_message(event_type, data, is_critical)


# Global instance
message_queue_manager = MessageQueueManager()
