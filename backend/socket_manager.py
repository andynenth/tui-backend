# backend/socket_manager.py

import asyncio
import json
import time
from typing import Dict, Set
from fastapi.websockets import WebSocket

class SocketManager:
    def __init__(self):
        self.room_connections: Dict[str, Set[WebSocket]] = {}
        self.broadcast_queues: Dict[str, asyncio.Queue] = {}
        self.broadcast_tasks: Dict[str, asyncio.Task] = {}
        self.lock = asyncio.Lock()
        
        self.queue_stats = {}
        self.connection_stats = {}
        self.rate_limiters = {}  # Rate limiting per room

    async def _process_broadcast_queue(self, room_id: str):
        """
        Enhanced broadcast queue processor with monitoring
        """
        queue = self.broadcast_queues.get(room_id)
        if not queue:
            return
            
        # Initialize stats
        self.queue_stats[room_id] = {
            "messages_processed": 0,
            "average_latency": 0,
            "last_error": None,
            "start_time": time.time()
        }
        
        print(f"DEBUG_WS: Starting enhanced broadcast queue processor for room {room_id}.")
        
        while True:
            try:
                start_time = time.time()
                # ✅ FIXED: Reduce timeout for lobby to make it more responsive
                timeout = 0.5 if room_id == "lobby" else 1.0
                message = await asyncio.wait_for(queue.get(), timeout=timeout)
                
                event = message["event"]
                data = message["data"]
                operation_id = data.get("operation_id", "unknown")

                # Get active WebSocket connections with lock
                async with self.lock:
                    active_websockets = list(self.room_connections.get(room_id, set()))

                if not active_websockets:
                    print(f"DEBUG_WS: No active connections found for room {room_id} during queue processing.")
                    continue

                print(f"DEBUG_WS: Broadcasting event '{event}' (op_id: {operation_id}) to {len(active_websockets)} clients in room {room_id}.")

                # Send to all active websockets with error tracking
                failed_websockets = []
                success_count = 0
                
                for ws in active_websockets:
                    try:
                        # Check if WebSocket is still active before sending
                        if hasattr(ws, 'client_state') and ws.client_state.name in ['DISCONNECTED', 'CLOSED']:
                            print(f"DEBUG_WS: Skipping send to closed WebSocket in room {room_id}")
                            failed_websockets.append(ws)
                            continue
                            
                        await ws.send_json({"event": event, "data": data})
                        success_count += 1
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
                
                # Update stats
                processing_time = time.time() - start_time
                stats = self.queue_stats[room_id]
                stats["messages_processed"] += 1
                stats["average_latency"] = (stats["average_latency"] + processing_time) / 2
                stats["last_success"] = time.time()
                stats["last_success_count"] = success_count
                stats["last_failure_count"] = len(failed_websockets)
                
            except asyncio.TimeoutError:
                # For lobby, be more aggressive about keeping the processor alive
                if room_id == "lobby":
                    continue  # Keep processing for lobby even if no messages
                    
                # Check if we should continue processing
                async with self.lock:
                    if room_id not in self.room_connections or not self.room_connections[room_id]:
                        print(f"DEBUG_WS: No connections for room {room_id}, stopping queue processor.")
                        break
                continue
            except Exception as e:
                print(f"DEBUG_WS: Queue processor error in room {room_id}: {e}")
                if room_id in self.queue_stats:
                    self.queue_stats[room_id]["last_error"] = str(e)
                    self.queue_stats[room_id]["last_error_time"] = time.time()

        # Cleanup when the processor stops
        async with self.lock:
            if room_id in self.broadcast_queues:
                del self.broadcast_queues[room_id]
            if room_id in self.broadcast_tasks:
                del self.broadcast_tasks[room_id]
            if room_id in self.queue_stats:
                print(f"DEBUG_WS: Queue stats for room {room_id}: {self.queue_stats[room_id]}")
                del self.queue_stats[room_id]
                
        print(f"DEBUG_WS: Stopped enhanced broadcast queue processor for room {room_id}.")

    async def register(self, room_id: str, websocket: WebSocket) -> WebSocket:
        """
        Enhanced WebSocket registration with connection tracking
        """
        await websocket.accept()
        
        async with self.lock:
            # Initialize room connections set if it doesn't exist
            if room_id not in self.room_connections:
                self.room_connections[room_id] = set()
                self.connection_stats[room_id] = {
                    "total_connections": 0,
                    "current_connections": 0,
                    "peak_connections": 0,
                    "first_connection": time.time()
                }
            
            # Add the connection
            self.room_connections[room_id].add(websocket)
            
            # Update stats
            stats = self.connection_stats[room_id]
            stats["total_connections"] += 1
            stats["current_connections"] = len(self.room_connections[room_id])
            stats["peak_connections"] = max(stats["peak_connections"], stats["current_connections"])
            stats["last_connection"] = time.time()
            
            # Create broadcast queue and task if they don't exist
            if room_id not in self.broadcast_queues:
                self.broadcast_queues[room_id] = asyncio.Queue()
                self.broadcast_tasks[room_id] = asyncio.create_task(self._process_broadcast_queue(room_id))
                print(f"DEBUG_WS: Created new enhanced broadcast queue and task for room {room_id}.")
            
            # IMPORTANT: Ensure lobby broadcast processor is always running
            elif room_id == "lobby" and room_id in self.broadcast_tasks:
                task = self.broadcast_tasks[room_id]
                if task.done() or task.cancelled():
                    print(f"DEBUG_WS: Restarting lobby broadcast task...")
                    self.broadcast_tasks[room_id] = asyncio.create_task(self._process_broadcast_queue(room_id))
            
            print(f"DEBUG_WS: Registered new connection for room {room_id}. Total connections: {stats['current_connections']}")
        
        return websocket

    def unregister(self, room_id: str, websocket: WebSocket):
        """
        Unregisters a WebSocket connection from a room.
        """
        asyncio.create_task(self._unregister_async(room_id, websocket))

    async def _unregister_async(self, room_id: str, websocket: WebSocket):
        async with self.lock:
            if room_id not in self.room_connections:
                print(f"DEBUG_WS: Attempted to unregister from non-existent room {room_id}")
                return
                
            self.room_connections[room_id].discard(websocket)
            
            # Update connection stats
            if room_id in self.connection_stats:
                self.connection_stats[room_id]["current_connections"] = len(self.room_connections[room_id])
                self.connection_stats[room_id]["last_disconnection"] = time.time()
            
            print(f"DEBUG_WS: Unregistered connection for room {room_id}. Remaining connections: {len(self.room_connections[room_id])}")
            
            # Clean up empty rooms
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]
                if room_id in self.broadcast_tasks:
                    self.broadcast_tasks[room_id].cancel()
                print(f"DEBUG_WS: Cleaned up empty room {room_id}")

    async def broadcast(self, room_id: str, event: str, data: dict):
        """
        Enhanced broadcast with debugging specifically for lobby
        """
        # Add extra debugging for lobby
        if room_id == "lobby":
            print(f"🔔 LOBBY_BROADCAST: Attempting to broadcast '{event}' to lobby")
            print(f"🔔 LOBBY_BROADCAST: Data keys: {list(data.keys())}")
        
        async with self.lock:
            # Check if we have connections for this room
            if room_id not in self.room_connections or not self.room_connections[room_id]:
                print(f"DEBUG_WS: No connections for room {room_id}. Cannot broadcast event '{event}'.")
                if room_id == "lobby":
                    print(f"🔔 LOBBY_BROADCAST: No lobby connections found!")
                    print(f"🔔 LOBBY_BROADCAST: Available rooms: {list(self.room_connections.keys())}")
                return
            
            # Check if broadcast queue exists
            if room_id not in self.broadcast_queues:
                print(f"DEBUG_WS: No broadcast queue for room {room_id}. This should not happen!")
                if room_id == "lobby":
                    print(f"🔔 LOBBY_BROADCAST: No lobby broadcast queue!")
                    print(f"🔔 LOBBY_BROADCAST: Available queues: {list(self.broadcast_queues.keys())}")
                return
            
            # Validate message
            if not isinstance(data, dict):
                print(f"DEBUG_WS: Invalid data type for broadcast. Expected dict, got {type(data)}")
                return
            
            # Show lobby connection count
            if room_id == "lobby":
                connection_count = len(self.room_connections[room_id])
                print(f"🔔 LOBBY_BROADCAST: Found {connection_count} lobby connections")
                print(f"🔔 LOBBY_BROADCAST: Queue size: {self.broadcast_queues[room_id].qsize()}")
        
        # Add timestamp and room info to message
        enhanced_data = {
            **data,
            "timestamp": time.time(),
            "room_id": room_id
        }
        
        # Add message to queue
        try:
            await self.broadcast_queues[room_id].put({
                "event": event, 
                "data": enhanced_data
            })
            print(f"DEBUG_WS: Message for event '{event}' added to queue for room {room_id}.")
            
            if room_id == "lobby":
                print(f"🔔 LOBBY_BROADCAST: Message added to lobby queue. New queue size: {self.broadcast_queues[room_id].qsize()}")
                
        except Exception as e:
            print(f"DEBUG_WS: Failed to queue message for room {room_id}: {e}")
            if room_id == "lobby":
                print(f"🔔 LOBBY_BROADCAST: Failed to add message to lobby queue: {e}")
        
        # Give the queue processor a chance to run
        await asyncio.sleep(0)

    def get_room_stats(self, room_id: str = None) -> dict:
        """
        Get statistics for monitoring
        """
        if room_id:
            return {
                "connection_stats": self.connection_stats.get(room_id, {}),
                "queue_stats": self.queue_stats.get(room_id, {}),
                "active_connections": len(self.room_connections.get(room_id, set()))
            }
        else:
            return {
                "total_rooms": len(self.room_connections),
                "total_active_connections": sum(len(conns) for conns in self.room_connections.values()),
                "rooms": list(self.room_connections.keys()),
                "connection_stats": self.connection_stats,
                "queue_stats": self.queue_stats
            }
    
    def ensure_lobby_broadcast_task(self):
        """
        Ensure lobby broadcast task is always running
        """
        if "lobby" not in self.broadcast_queues:
            self.broadcast_queues["lobby"] = asyncio.Queue()
            print(f"🔔 LOBBY_BROADCAST: Created lobby broadcast queue")
        
        if "lobby" not in self.broadcast_tasks or self.broadcast_tasks["lobby"].done():
            self.broadcast_tasks["lobby"] = asyncio.create_task(self._process_broadcast_queue("lobby"))
            print(f"🔔 LOBBY_BROADCAST: Created/restarted lobby broadcast task")


# CREATE SINGLETON INSTANCE
_socket_manager = SocketManager()

# EXPORT MODULE-LEVEL FUNCTIONS (THIS WAS MISSING!)
async def register(room_id: str, websocket: WebSocket) -> WebSocket:
    return await _socket_manager.register(room_id, websocket)

def unregister(room_id: str, websocket: WebSocket):
    _socket_manager.unregister(room_id, websocket)

async def broadcast(room_id: str, event: str, data: dict):
    await _socket_manager.broadcast(room_id, event, data)

def get_room_stats(room_id: str = None) -> dict:
    return _socket_manager.get_room_stats(room_id)

def ensure_lobby_ready():
    _socket_manager.ensure_lobby_broadcast_task()
