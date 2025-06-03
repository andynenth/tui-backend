# backend/socket_manager.py

from fastapi.websockets import WebSocket
from typing import Dict, List, Optional, Set
import asyncio
import json

# Use a class to ensure state is properly shared
class SocketManager:
    def __init__(self):
        # Dictionary to store WebSocket connections for each room
        self.room_connections: Dict[str, Set[WebSocket]] = {}
        # Queue for Broadcast Messages
        self.broadcast_queues: Dict[str, asyncio.Queue] = {}
        # Task for managing the Broadcast Queue for each room
        self.broadcast_tasks: Dict[str, asyncio.Task] = {}
        # Lock for thread-safe operations
        self.lock = asyncio.Lock()

    async def _process_broadcast_queue(self, room_id: str):
        """
        Background task to process messages from the broadcast queue for a specific room.
        """
        queue = self.broadcast_queues.get(room_id)
        if not queue:
            return
            
        print(f"DEBUG_WS: Starting broadcast queue processor for room {room_id}.")
        
        while True:
            try:
                # Wait for messages with a timeout
                message = await asyncio.wait_for(queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                # Check if we should continue processing
                async with self.lock:
                    if room_id not in self.room_connections or not self.room_connections[room_id]:
                        print(f"DEBUG_WS: No connections for room {room_id}, stopping queue processor.")
                        break
                continue
                
            event = message["event"]
            data = message["data"]

            # Get active WebSocket connections
            async with self.lock:
                active_websockets = list(self.room_connections.get(room_id, set()))

            if not active_websockets:
                print(f"DEBUG_WS: No active connections found for room {room_id} during queue processing.")
                continue

            print(f"DEBUG_WS: Broadcasting event '{event}' to {len(active_websockets)} clients in room {room_id}.")

            # Send to all active websockets
            failed_websockets = []
            for ws in active_websockets:
                try:
                    await ws.send_json({"event": event, "data": data})
                    print(f"DEBUG_WS: Successfully sent '{event}' to a client in room {room_id}.")
                except Exception as e:
                    print(f"DEBUG_WS: Error sending to client in room {room_id}: {e}")
                    failed_websockets.append(ws)

            # Clean up failed connections
            if failed_websockets:
                async with self.lock:
                    for ws in failed_websockets:
                        if room_id in self.room_connections:
                            self.room_connections[room_id].discard(ws)

        # Cleanup when the processor stops
        async with self.lock:
            if room_id in self.broadcast_queues:
                del self.broadcast_queues[room_id]
            if room_id in self.broadcast_tasks:
                del self.broadcast_tasks[room_id]
        print(f"DEBUG_WS: Stopped broadcast queue processor for room {room_id}.")

    async def register(self, room_id: str, websocket: WebSocket) -> WebSocket:
        """
        Registers a new WebSocket connection for a given room.
        """
        await websocket.accept()
        
        async with self.lock:
            # Initialize room connections set if it doesn't exist
            if room_id not in self.room_connections:
                self.room_connections[room_id] = set()
            
            # Add the connection
            self.room_connections[room_id].add(websocket)
            
            # Create broadcast queue and task if they don't exist
            if room_id not in self.broadcast_queues:
                self.broadcast_queues[room_id] = asyncio.Queue()
                self.broadcast_tasks[room_id] = asyncio.create_task(self._process_broadcast_queue(room_id))
                print(f"DEBUG_WS: Created new broadcast queue and task for room {room_id}.")
            
            print(f"DEBUG_WS: Registered new connection for room {room_id}. Total connections: {len(self.room_connections[room_id])}")
        
        return websocket

    def unregister(self, room_id: str, websocket: WebSocket):
        """
        Unregisters a WebSocket connection from a room.
        """
        asyncio.create_task(self._unregister_async(room_id, websocket))

    async def _unregister_async(self, room_id: str, websocket: WebSocket):
        """
        Async version of unregister to properly handle cleanup.
        """
        async with self.lock:
            if room_id not in self.room_connections:
                print(f"DEBUG_WS: Attempted to unregister from non-existent room {room_id}")
                return
                
            # Remove the connection
            self.room_connections[room_id].discard(websocket)
            
            print(f"DEBUG_WS: Unregistered connection for room {room_id}. Remaining connections: {len(self.room_connections[room_id])}")
            
            # Clean up empty rooms
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]
                # Cancel the broadcast task
                if room_id in self.broadcast_tasks:
                    self.broadcast_tasks[room_id].cancel()

    async def broadcast(self, room_id: str, event: str, data: dict):
        """
        Adds a message to the broadcast queue for a specific room.
        """
        async with self.lock:
            # Check if we have connections for this room
            if room_id not in self.room_connections or not self.room_connections[room_id]:
                print(f"DEBUG_WS: No connections for room {room_id}. Cannot broadcast event '{event}'.")
                return
            
            # Check if broadcast queue exists
            if room_id not in self.broadcast_queues:
                print(f"DEBUG_WS: No broadcast queue for room {room_id}. This should not happen!")
                return
        
        # Add message to queue
        await self.broadcast_queues[room_id].put({"event": event, "data": data})
        print(f"DEBUG_WS: Message for event '{event}' added to queue for room {room_id}.")
        
        # Give the queue processor a chance to run
        await asyncio.sleep(0)

# Create a singleton instance
_socket_manager = SocketManager()

# Export the methods as module-level functions for backward compatibility
async def register(room_id: str, websocket: WebSocket) -> WebSocket:
    return await _socket_manager.register(room_id, websocket)

def unregister(room_id: str, websocket: WebSocket):
    _socket_manager.unregister(room_id, websocket)

async def broadcast(room_id: str, event: str, data: dict):
    await _socket_manager.broadcast(room_id, event, data)