# infrastructure/websocket/broadcast_service.py
"""
Service for broadcasting messages through WebSocket connections.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import asyncio
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class WebSocketMessage:
    """Standard WebSocket message format."""
    event: str
    data: Dict[str, Any]
    timestamp: str = ""
    sequence: Optional[int] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_json(self) -> str:
        """Convert to JSON string for transmission."""
        return json.dumps(asdict(self))


class BroadcastService:
    """
    Handles broadcasting messages to WebSocket connections.
    
    This service is responsible for:
    - Formatting messages
    - Managing broadcast queues
    - Handling connection failures
    - Tracking message sequences
    """
    
    def __init__(self):
        self._sequence_counter = 0
        self._broadcast_lock = asyncio.Lock()
        self._failed_sends: Dict[str, int] = {}  # Track failed sends per connection
    
    def _get_next_sequence(self) -> int:
        """Get the next sequence number."""
        self._sequence_counter += 1
        return self._sequence_counter
    
    async def send_to_connection(
        self,
        connection,
        event_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Send a message to a specific connection.
        
        Args:
            connection: WebSocket connection object
            event_type: Type of event
            data: Event data
            
        Returns:
            True if message was sent successfully
        """
        try:
            message = WebSocketMessage(
                event=event_type,
                data=data,
                sequence=self._get_next_sequence()
            )
            
            await connection.send_text(message.to_json())
            
            # Reset failed count on success
            connection_id = id(connection)
            if connection_id in self._failed_sends:
                del self._failed_sends[connection_id]
            
            return True
            
        except Exception as e:
            connection_id = id(connection)
            self._failed_sends[connection_id] = self._failed_sends.get(connection_id, 0) + 1
            
            logger.error(
                f"Failed to send to connection {connection_id}: {str(e)}"
            )
            
            # If too many failures, connection might be dead
            if self._failed_sends[connection_id] > 3:
                logger.warning(
                    f"Connection {connection_id} has failed {self._failed_sends[connection_id]} times"
                )
            
            return False
    
    async def broadcast_to_connections(
        self,
        connections: List,
        event_type: str,
        data: Dict[str, Any],
        exclude_connections: Optional[Set] = None
    ) -> int:
        """
        Broadcast to multiple connections.
        
        Args:
            connections: List of WebSocket connections
            event_type: Type of event
            data: Event data
            exclude_connections: Connections to exclude
            
        Returns:
            Number of successful sends
        """
        if not connections:
            return 0
        
        exclude_set = exclude_connections or set()
        
        # Create tasks for concurrent sending
        tasks = []
        for connection in connections:
            if connection not in exclude_set:
                tasks.append(
                    self.send_to_connection(connection, event_type, data)
                )
        
        if not tasks:
            return 0
        
        # Send concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes
        success_count = sum(
            1 for result in results
            if result is True or (isinstance(result, bool) and result)
        )
        
        logger.debug(
            f"Broadcast {event_type} to {success_count}/{len(tasks)} connections"
        )
        
        return success_count
    
    async def broadcast_to_room(
        self,
        room_id: str,
        event_type: str,
        data: Dict[str, Any],
        exclude_players: Optional[List[str]] = None,
        connection_manager=None
    ) -> int:
        """
        Broadcast to all connections in a room.
        
        Args:
            room_id: The room ID
            event_type: Type of event
            data: Event data
            exclude_players: Player IDs to exclude
            connection_manager: Manager to get room connections
            
        Returns:
            Number of successful sends
        """
        if not connection_manager:
            logger.error("No connection manager provided for room broadcast")
            return 0
        
        # Get all connections in the room
        room_connections = connection_manager.get_room_connections_objects(room_id)
        
        if not room_connections:
            logger.warning(f"No connections found for room {room_id}")
            return 0
        
        # Convert exclude players to connections
        exclude_connections = set()
        if exclude_players:
            for player_id in exclude_players:
                connection = connection_manager.get_connection(player_id)
                if connection:
                    exclude_connections.add(connection)
        
        # Add room context to data
        data_with_context = {
            **data,
            "_room_id": room_id,
            "_broadcast_time": datetime.utcnow().isoformat()
        }
        
        return await self.broadcast_to_connections(
            room_connections,
            event_type,
            data_with_context,
            exclude_connections
        )
    
    async def broadcast_global(
        self,
        event_type: str,
        data: Dict[str, Any],
        connection_manager=None
    ) -> int:
        """
        Broadcast to all connected clients.
        
        Args:
            event_type: Type of event
            data: Event data
            connection_manager: Manager to get all connections
            
        Returns:
            Number of successful sends
        """
        if not connection_manager:
            logger.error("No connection manager provided for global broadcast")
            return 0
        
        all_connections = connection_manager.get_all_connections()
        
        # Add global context
        data_with_context = {
            **data,
            "_global": True,
            "_broadcast_time": datetime.utcnow().isoformat()
        }
        
        return await self.broadcast_to_connections(
            all_connections,
            event_type,
            data_with_context
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get broadcast statistics."""
        return {
            "sequence_counter": self._sequence_counter,
            "failed_connections": len(self._failed_sends),
            "failed_details": {
                str(conn_id): count
                for conn_id, count in self._failed_sends.items()
            }
        }