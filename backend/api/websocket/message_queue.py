# backend/api/websocket/message_queue.py

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class QueuedMessage:
    """Represents a queued message for a disconnected player"""
    event: str
    data: Any
    sequence_number: int
    timestamp: float


class MessageQueueManager:
    """
    Manages message queues for disconnected players.
    Stores critical game events to be delivered upon reconnection.
    """

    # Critical events that should be queued
    CRITICAL_EVENTS = {
        'phase_change',
        'turn_resolved',
        'round_complete',
        'game_ended',
        'score_update',
        'host_changed',
        'turn_start',
        'declaration_made',
        'play_made',
        'weak_hands_found',
        'redeal_executed'
    }

    def __init__(self):
        # Nested dict: room_id -> player_name -> deque of messages
        self._queues: Dict[str, Dict[str, Deque[QueuedMessage]]] = defaultdict(lambda: defaultdict(deque))
        # Track sequence numbers per room
        self._sequence_numbers: Dict[str, int] = defaultdict(int)
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        # Maximum messages per player queue
        self._max_queue_size = 100
        logger.info("MessageQueueManager initialized")

    def _should_queue_event(self, event: str) -> bool:
        """
        Check if an event should be queued.
        
        Args:
            event: The event name
            
        Returns:
            True if the event should be queued
        """
        return event in self.CRITICAL_EVENTS

    async def queue_message(self, room_id: str, player_name: str, event: str, data: Any) -> bool:
        """
        Queue a message for a disconnected player.
        
        Args:
            room_id: The room ID
            player_name: The player's name
            event: The event name
            data: The event data
            
        Returns:
            True if message was queued, False if not a critical event
        """
        if not self._should_queue_event(event):
            return False

        async with self._lock:
            # Get or create player queue
            player_queue = self._queues[room_id][player_name]
            
            # Enforce queue size limit (remove oldest if full)
            if len(player_queue) >= self._max_queue_size:
                removed = player_queue.popleft()
                logger.warning(
                    f"Queue full for {player_name} in room {room_id}, "
                    f"dropping oldest message: {removed.event}"
                )
            
            # Get next sequence number
            self._sequence_numbers[room_id] += 1
            sequence = self._sequence_numbers[room_id]
            
            # Create and queue message
            message = QueuedMessage(
                event=event,
                data=data,
                sequence_number=sequence,
                timestamp=time.time()
            )
            player_queue.append(message)
            
            logger.info(
                f"Queued {event} for {player_name} in room {room_id} "
                f"(seq: {sequence}, queue size: {len(player_queue)})"
            )
            return True

    async def get_queued_messages(self, room_id: str, player_name: str) -> List[Dict[str, Any]]:
        """
        Get all queued messages for a player and clear their queue.
        
        Args:
            room_id: The room ID
            player_name: The player's name
            
        Returns:
            List of messages in order, each with event, data, sequence_number, and timestamp
        """
        async with self._lock:
            player_queue = self._queues[room_id].get(player_name, deque())
            if not player_queue:
                return []
            
            # Convert to list of dicts
            messages = []
            while player_queue:
                msg = player_queue.popleft()
                messages.append({
                    'event': msg.event,
                    'data': msg.data,
                    'sequence_number': msg.sequence_number,
                    'timestamp': msg.timestamp
                })
            
            # Clean up empty player entry
            if player_name in self._queues[room_id]:
                del self._queues[room_id][player_name]
            
            logger.info(
                f"Retrieved {len(messages)} queued messages for {player_name} "
                f"in room {room_id}"
            )
            return messages

    async def clear_queue(self, room_id: str, player_name: str) -> None:
        """
        Clear all queued messages for a player.
        
        Args:
            room_id: The room ID
            player_name: The player's name
        """
        async with self._lock:
            if room_id in self._queues and player_name in self._queues[room_id]:
                queue_size = len(self._queues[room_id][player_name])
                del self._queues[room_id][player_name]
                logger.info(
                    f"Cleared {queue_size} messages for {player_name} "
                    f"in room {room_id}"
                )

    async def cleanup_room(self, room_id: str) -> None:
        """
        Clean up all message queues for a room.
        
        Args:
            room_id: The room ID to clean up
        """
        async with self._lock:
            if room_id in self._queues:
                player_count = len(self._queues[room_id])
                total_messages = sum(
                    len(queue) for queue in self._queues[room_id].values()
                )
                del self._queues[room_id]
                
                if room_id in self._sequence_numbers:
                    del self._sequence_numbers[room_id]
                
                logger.info(
                    f"Cleaned up {total_messages} messages for {player_count} "
                    f"players in room {room_id}"
                )

    async def get_queue_stats(self, room_id: str) -> Dict[str, int]:
        """
        Get queue statistics for a room.
        
        Args:
            room_id: The room ID
            
        Returns:
            Dict mapping player names to their queue sizes
        """
        async with self._lock:
            if room_id not in self._queues:
                return {}
            
            return {
                player: len(queue)
                for player, queue in self._queues[room_id].items()
            }

    async def has_queued_messages(self, room_id: str, player_name: str) -> bool:
        """
        Check if a player has queued messages.
        
        Args:
            room_id: The room ID
            player_name: The player's name
            
        Returns:
            True if player has queued messages
        """
        async with self._lock:
            return (
                room_id in self._queues and
                player_name in self._queues[room_id] and
                len(self._queues[room_id][player_name]) > 0
            )


# Singleton instance
message_queue_manager = MessageQueueManager()