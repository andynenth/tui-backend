"""
In-memory implementation of the message queue repository.

This implementation stores message queues in memory and is suitable
for development and testing. In production, this would be replaced with
a persistent message queue system like Redis or RabbitMQ.
"""

from typing import Optional, List, Dict
from datetime import datetime

from domain.entities.message_queue import PlayerQueue, QueuedMessage
from domain.value_objects import PlayerId, RoomId
from application.interfaces.repositories import MessageQueueRepository


class InMemoryMessageQueueRepository(MessageQueueRepository):
    """
    In-memory implementation of MessageQueueRepository.
    
    Stores message queues in nested dictionaries for fast lookup by
    room and player.
    """
    
    def __init__(self):
        # Structure: {room_id: {player_name: PlayerQueue}}
        self._queues: Dict[str, Dict[str, PlayerQueue]] = {}
    
    async def create_queue(self, room_id: str, player_name: str) -> None:
        """Create a message queue for a player."""
        if room_id not in self._queues:
            self._queues[room_id] = {}
        
        # Only create if doesn't exist
        if player_name not in self._queues[room_id]:
            self._queues[room_id][player_name] = PlayerQueue(
                player_id=PlayerId(player_name),
                room_id=RoomId(room_id)
            )
    
    async def get_queue(self, room_id: str, player_name: str) -> Optional[PlayerQueue]:
        """Get message queue for a player."""
        room_queues = self._queues.get(room_id, {})
        return room_queues.get(player_name)
    
    async def save_queue(self, queue: PlayerQueue) -> None:
        """Save a message queue."""
        room_id = queue.room_id.value
        player_name = queue.player_id.value
        
        if room_id not in self._queues:
            self._queues[room_id] = {}
        
        self._queues[room_id][player_name] = queue
    
    async def clear_queue(self, room_id: str, player_name: str) -> None:
        """Clear and delete a message queue."""
        if room_id in self._queues and player_name in self._queues[room_id]:
            del self._queues[room_id][player_name]
            
            # Clean up empty room dict
            if not self._queues[room_id]:
                del self._queues[room_id]
    
    async def clear_room_queues(self, room_id: str) -> None:
        """Clear all queues for a room."""
        if room_id in self._queues:
            del self._queues[room_id]
    
    async def add_message(
        self, 
        room_id: str, 
        player_name: str,
        event_type: str,
        data: Dict,
        is_critical: bool = False
    ) -> bool:
        """
        Add a message to a player's queue.
        
        Args:
            room_id: The room ID
            player_name: The player name
            event_type: Type of event
            data: Event data
            is_critical: Whether this is a critical message
            
        Returns:
            True if message was added, False if queue is full
        """
        queue = await self.get_queue(room_id, player_name)
        if not queue:
            await self.create_queue(room_id, player_name)
            queue = await self.get_queue(room_id, player_name)
        
        message = QueuedMessage(
            event_type=event_type,
            data=data,
            timestamp=datetime.utcnow(),
            is_critical=is_critical
        )
        
        success = queue.add_message(message)
        if success:
            await self.save_queue(queue)
        
        return success
    
    async def get_all_queues(self) -> Dict[str, Dict[str, PlayerQueue]]:
        """Get all queues. Useful for debugging."""
        return self._queues.copy()
    
    async def count_messages(self) -> Dict[str, int]:
        """Count total messages across all queues."""
        stats = {
            "total_queues": 0,
            "total_messages": 0,
            "critical_messages": 0
        }
        
        for room_queues in self._queues.values():
            for queue in room_queues.values():
                stats["total_queues"] += 1
                stats["total_messages"] += len(queue.messages)
                stats["critical_messages"] += sum(
                    1 for msg in queue.messages if msg.is_critical
                )
        
        return stats
    
    def snapshot(self) -> Dict:
        """Create a snapshot of the current state for rollback."""
        import copy
        return copy.deepcopy(self._queues)
    
    def restore(self, snapshot: Dict) -> None:
        """Restore from a snapshot."""
        import copy
        self._queues = copy.deepcopy(snapshot)