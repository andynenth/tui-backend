# backend/socket_manager.py

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set

from fastapi.websockets import WebSocket


@dataclass
class PendingMessage:
    """Represents a message awaiting acknowledgment"""

    message: Dict[str, Any]
    websocket: WebSocket
    timestamp: float
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: float = 30.0
    room_id: str = ""

    def is_expired(self) -> bool:
        """Check if message has exceeded timeout"""
        return time.time() - self.timestamp > self.timeout_seconds

    def should_retry(self) -> bool:
        """Check if message should be retried"""
        return self.retry_count < self.max_retries and not self.is_expired()


@dataclass
class MessageStats:
    """Statistics for message delivery tracking"""

    sent: int = 0
    acknowledged: int = 0
    failed: int = 0
    retried: int = 0
    duplicates_detected: int = 0
    average_latency: float = 0.0
    last_activity: float = field(default_factory=time.time)


class SocketManager:
    def __init__(self):
        self.room_connections: Dict[str, Set[WebSocket]] = {}
        self.broadcast_queues: Dict[str, asyncio.Queue] = {}
        self.broadcast_tasks: Dict[str, asyncio.Task] = {}
        self.lock = asyncio.Lock()

        self.queue_stats = {}
        self.connection_stats = {}
        self.rate_limiters = {}  # Rate limiting per room

        # Reliable message delivery features
        self.pending_messages: Dict[str, Dict[int, PendingMessage]] = (
            {}
        )  # room_id -> {seq -> message}
        self.message_sequences: Dict[str, int] = {}  # room_id -> current sequence
        self.message_stats: Dict[str, MessageStats] = {}  # room_id -> stats
        self.client_last_seen_sequence: Dict[str, Dict[str, int]] = (
            {}
        )  # room_id -> {client_id -> sequence}

        # Start background retry task
        self._retry_task = asyncio.create_task(self._message_retry_worker())

    def __del__(self):
        """Cleanup background tasks"""
        if hasattr(self, "_retry_task") and self._retry_task:
            self._retry_task.cancel()

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
            "start_time": time.time(),
        }

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
                    # Wait for connections to return instead of re-queueing
                    await asyncio.sleep(0.5)  # Wait for potential reconnection

                    # Check again for connections
                    async with self.lock:
                        active_websockets = list(
                            self.room_connections.get(room_id, set())
                        )

                    if not active_websockets:
                        await self.broadcast_queues[room_id].put(message)
                        continue

                # Send to all active websockets with error tracking
                failed_websockets = []
                success_count = 0

                for ws in active_websockets:
                    try:
                        # Check if WebSocket is still active before sending
                        if hasattr(ws, "client_state") and ws.client_state.name in [
                            "DISCONNECTED",
                            "CLOSED",
                        ]:
                            failed_websockets.append(ws)
                            continue

                        await ws.send_json({"event": event, "data": data})
                        success_count += 1
                    except Exception as e:
                        if "not JSON serializable" in str(e):
                            # Try to identify which field has the issue
                            if isinstance(data, dict):
                                for key, value in data.items():
                                    try:
                                        import json

                                        json.dumps(value)
                                    except:
                                        pass
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
                stats["average_latency"] = (
                    stats["average_latency"] + processing_time
                ) / 2
                stats["last_success"] = time.time()
                stats["last_success_count"] = success_count
                stats["last_failure_count"] = len(failed_websockets)

            except asyncio.TimeoutError:
                # Only log timeouts for debugging specific issues, not normal operation
                # For lobby, be more aggressive about keeping the processor alive
                if room_id == "lobby":
                    continue  # Keep processing for lobby even if no messages

                # Check if we should continue processing
                async with self.lock:
                    connections_exist = room_id in self.room_connections and bool(
                        self.room_connections[room_id]
                    )
                    queue_has_messages = queue.qsize() > 0

                    if not connections_exist and not queue_has_messages:
                        break
                    elif not connections_exist:
                        pass
                continue
            except Exception as e:
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
                del self.queue_stats[room_id]

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
                    "first_connection": time.time(),
                }

            # Add the connection
            self.room_connections[room_id].add(websocket)

            # Update stats
            stats = self.connection_stats[room_id]
            stats["total_connections"] += 1
            stats["current_connections"] = len(self.room_connections[room_id])
            stats["peak_connections"] = max(
                stats["peak_connections"], stats["current_connections"]
            )
            stats["last_connection"] = time.time()

            # Create broadcast queue and task if they don't exist
            if room_id not in self.broadcast_queues:
                self.broadcast_queues[room_id] = asyncio.Queue()
                self.broadcast_tasks[room_id] = asyncio.create_task(
                    self._process_broadcast_queue(room_id)
                )

            # IMPORTANT: Ensure lobby broadcast processor is always running
            elif room_id == "lobby" and room_id in self.broadcast_tasks:
                task = self.broadcast_tasks[room_id]
                if task.done() or task.cancelled():
                    self.broadcast_tasks[room_id] = asyncio.create_task(
                        self._process_broadcast_queue(room_id)
                    )

        return websocket

    def unregister(self, room_id: str, websocket: WebSocket):
        """
        Unregisters a WebSocket connection from a room.
        """
        asyncio.create_task(self._unregister_async(room_id, websocket))

    async def _unregister_async(self, room_id: str, websocket: WebSocket):
        async with self.lock:
            if room_id not in self.room_connections:
                return

            self.room_connections[room_id].discard(websocket)

            # Update connection stats
            if room_id in self.connection_stats:
                self.connection_stats[room_id]["current_connections"] = len(
                    self.room_connections[room_id]
                )
                self.connection_stats[room_id]["last_disconnection"] = time.time()

            # Clean up empty rooms - BUT PROTECT ACTIVE GAMES
            if not self.room_connections[room_id]:
                # Check if room has an active game before cleanup
                from shared_instances import shared_room_manager

                room = await shared_room_manager.get_room(room_id)

                if room and room.game and not room.game._is_game_over():
                    # Keep the room in connections dict but empty, so queue stays alive
                    # Don't delete the broadcast task
                    return

                # Safe to clean up - no active game
                del self.room_connections[room_id]
                if room_id in self.broadcast_tasks:
                    self.broadcast_tasks[room_id].cancel()

    async def broadcast(self, room_id: str, event: str, data: dict):
        """
        Enhanced broadcast with debugging specifically for lobby
        """
        # Add extra debugging for lobby
        if room_id == "lobby":
            pass

        async with self.lock:
            # Check if we have connections for this room
            if (
                room_id not in self.room_connections
                or not self.room_connections[room_id]
            ):
                if room_id == "lobby":
                    pass
                return

            # Check if broadcast queue exists
            if room_id not in self.broadcast_queues:
                if room_id == "lobby":
                    pass
                return

            # Validate message
            if not isinstance(data, dict):
                return

            # Show lobby connection count
            if room_id == "lobby":
                connection_count = len(self.room_connections[room_id])

        # Add timestamp and room info to message
        enhanced_data = {**data, "timestamp": time.time(), "room_id": room_id}

        # Add message to queue
        try:
            await self.broadcast_queues[room_id].put(
                {"event": event, "data": enhanced_data}
            )

            if room_id == "lobby":
                pass

        except Exception as e:
            if room_id == "lobby":
                pass

        # Give the queue processor a chance to run
        await asyncio.sleep(0)

    def _next_sequence(self, room_id: str) -> int:
        """Generate next sequence number for room (thread-safe)"""
        current = self.message_sequences.get(room_id, 0)
        self.message_sequences[room_id] = current + 1
        return current + 1

    async def send_with_ack(
        self,
        room_id: str,
        event: str,
        data: dict,
        websocket: WebSocket,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> bool:
        """
        Send message with acknowledgment requirement and automatic retry

        Args:
            room_id: The room identifier
            event: Event type
            data: Message data
            websocket: Target WebSocket connection
            timeout: Timeout in seconds for acknowledgment
            max_retries: Maximum retry attempts

        Returns:
            bool: True if message was sent (not necessarily acknowledged)
        """
        # Generate sequence number
        sequence = self._next_sequence(room_id)

        # Ensure stats exist
        if room_id not in self.message_stats:
            self.message_stats[room_id] = MessageStats()

        # Prepare message with sequence and ack requirement
        message = {
            "event": event,
            "data": {
                **data,
                "_seq": sequence,
                "_ack_required": True,
                "_timestamp": time.time(),
                "room_id": room_id,
            },
        }

        try:
            # Send message
            await websocket.send_json(message)

            # Store for retry if needed
            if room_id not in self.pending_messages:
                self.pending_messages[room_id] = {}

            self.pending_messages[room_id][sequence] = PendingMessage(
                message=message,
                websocket=websocket,
                timestamp=time.time(),
                retry_count=0,
                max_retries=max_retries,
                timeout_seconds=timeout,
                room_id=room_id,
            )

            # Update stats
            self.message_stats[room_id].sent += 1
            self.message_stats[room_id].last_activity = time.time()

            print(
                f"🔄 RELIABLE_MSG: Sent message seq {sequence} to room {room_id} (awaiting ack)"
            )
            return True

        except Exception as e:
            print(
                f"❌ RELIABLE_MSG: Failed to send message seq {sequence} to room {room_id}: {e}"
            )
            self.message_stats[room_id].failed += 1
            return False

    async def handle_ack(
        self, room_id: str, sequence: int, client_id: Optional[str] = None
    ) -> bool:
        """
        Handle acknowledgment from client

        Args:
            room_id: The room identifier
            sequence: Sequence number being acknowledged
            client_id: Optional client identifier for tracking

        Returns:
            bool: True if acknowledgment was processed
        """
        try:
            # Remove from pending messages
            if (
                room_id in self.pending_messages
                and sequence in self.pending_messages[room_id]
            ):

                pending_msg = self.pending_messages[room_id][sequence]
                response_time = time.time() - pending_msg.timestamp

                # Update stats
                if room_id in self.message_stats:
                    stats = self.message_stats[room_id]
                    stats.acknowledged += 1
                    stats.average_latency = (stats.average_latency + response_time) / 2
                    stats.last_activity = time.time()

                # Track client sequence
                if client_id:
                    if room_id not in self.client_last_seen_sequence:
                        self.client_last_seen_sequence[room_id] = {}
                    self.client_last_seen_sequence[room_id][client_id] = sequence

                # Remove from pending
                del self.pending_messages[room_id][sequence]

                print(
                    f"✅ RELIABLE_MSG: Acknowledged seq {sequence} for room {room_id} "
                    f"(latency: {response_time:.3f}s)"
                )
                return True
            else:
                # Check for duplicate acknowledgment
                if room_id in self.message_stats:
                    self.message_stats[room_id].duplicates_detected += 1

                print(
                    f"⚠️  RELIABLE_MSG: Duplicate or unknown ack seq {sequence} for room {room_id}"
                )
                return False

        except Exception as e:
            print(
                f"❌ RELIABLE_MSG: Error handling ack seq {sequence} for room {room_id}: {e}"
            )
            return False

    async def _message_retry_worker(self):
        """Background worker to retry unacknowledged messages"""
        print("🔄 RELIABLE_MSG: Message retry worker started")

        while True:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds

                current_time = time.time()
                retry_tasks = []

                # Check all pending messages across all rooms
                for room_id, room_messages in list(self.pending_messages.items()):
                    for sequence, pending_msg in list(room_messages.items()):

                        # Check if message should be retried
                        if pending_msg.should_retry():
                            # Check if it's time to retry (exponential backoff)
                            retry_delay = min(5 * (2**pending_msg.retry_count), 30)
                            if current_time - pending_msg.timestamp >= retry_delay:
                                retry_tasks.append(
                                    self._retry_message(room_id, sequence, pending_msg)
                                )

                        # Check if message has expired
                        elif pending_msg.is_expired():
                            retry_tasks.append(
                                self._handle_expired_message(
                                    room_id, sequence, pending_msg
                                )
                            )

                # Execute retry tasks
                if retry_tasks:
                    await asyncio.gather(*retry_tasks, return_exceptions=True)

            except Exception as e:
                print(f"❌ RELIABLE_MSG: Error in retry worker: {e}")

    async def _retry_message(
        self, room_id: str, sequence: int, pending_msg: PendingMessage
    ):
        """Retry a pending message"""
        try:
            pending_msg.retry_count += 1
            pending_msg.timestamp = (
                time.time()
            )  # Reset timestamp for new retry interval

            # Update message with retry indicator
            retry_message = pending_msg.message.copy()
            retry_message["data"]["_retry_count"] = pending_msg.retry_count

            # Attempt to send
            await pending_msg.websocket.send_json(retry_message)

            # Update stats
            if room_id in self.message_stats:
                self.message_stats[room_id].retried += 1

            print(
                f"🔄 RELIABLE_MSG: Retried seq {sequence} for room {room_id} "
                f"(attempt {pending_msg.retry_count}/{pending_msg.max_retries})"
            )

        except Exception as e:
            print(
                f"❌ RELIABLE_MSG: Failed to retry seq {sequence} for room {room_id}: {e}"
            )
            # Move to expired handling
            await self._handle_expired_message(room_id, sequence, pending_msg)

    async def _handle_expired_message(
        self, room_id: str, sequence: int, pending_msg: PendingMessage
    ):
        """Handle a message that has expired or failed all retries"""
        try:
            # Remove from pending messages
            if (
                room_id in self.pending_messages
                and sequence in self.pending_messages[room_id]
            ):
                del self.pending_messages[room_id][sequence]

            # Update stats
            if room_id in self.message_stats:
                self.message_stats[room_id].failed += 1

            print(
                f"❌ RELIABLE_MSG: Expired seq {sequence} for room {room_id} "
                f"after {pending_msg.retry_count} retries"
            )

            # Could trigger client disconnect/recovery here if needed

        except Exception as e:
            print(
                f"❌ RELIABLE_MSG: Error handling expired message seq {sequence}: {e}"
            )

    async def request_client_sync(
        self, room_id: str, websocket: WebSocket, client_id: str
    ):
        """
        Request client to synchronize state (get missing events)

        Args:
            room_id: The room identifier
            websocket: Client WebSocket connection
            client_id: Client identifier
        """
        try:
            # Get client's last seen sequence
            last_seen = 0
            if (
                room_id in self.client_last_seen_sequence
                and client_id in self.client_last_seen_sequence[room_id]
            ):
                last_seen = self.client_last_seen_sequence[room_id][client_id]

            # Send sync request
            sync_message = {
                "event": "sync_request",
                "data": {
                    "room_id": room_id,
                    "last_seen_sequence": last_seen,
                    "current_sequence": self.message_sequences.get(room_id, 0),
                    "_timestamp": time.time(),
                },
            }

            await websocket.send_json(sync_message)
            print(
                f"🔄 RELIABLE_MSG: Sent sync request to client {client_id} in room {room_id}"
            )

        except Exception as e:
            print(f"❌ RELIABLE_MSG: Failed to send sync request to {client_id}: {e}")

    def get_message_stats(self, room_id: str = None) -> dict:
        """
        Get message delivery statistics

        Args:
            room_id: Optional room to get stats for, None for all rooms

        Returns:
            Dict: Message delivery statistics
        """
        if room_id:
            stats = self.message_stats.get(room_id, MessageStats())
            pending_count = len(self.pending_messages.get(room_id, {}))

            return {
                "room_id": room_id,
                "messages_sent": stats.sent,
                "messages_acknowledged": stats.acknowledged,
                "messages_failed": stats.failed,
                "messages_retried": stats.retried,
                "duplicates_detected": stats.duplicates_detected,
                "pending_messages": pending_count,
                "average_latency_ms": stats.average_latency * 1000,
                "success_rate": (stats.acknowledged / max(stats.sent, 1)) * 100,
                "last_activity": stats.last_activity,
            }
        else:
            # Return stats for all rooms
            all_stats = {}
            total_pending = 0

            for room_id in self.message_stats:
                all_stats[room_id] = self.get_message_stats(room_id)
                total_pending += len(self.pending_messages.get(room_id, {}))

            return {
                "rooms": all_stats,
                "total_pending_messages": total_pending,
                "total_rooms": len(self.message_stats),
            }

    def get_room_stats(self, room_id: str = None) -> dict:
        """
        Get statistics for monitoring
        """
        if room_id:
            return {
                "connection_stats": self.connection_stats.get(room_id, {}),
                "queue_stats": self.queue_stats.get(room_id, {}),
                "active_connections": len(self.room_connections.get(room_id, set())),
            }
        else:
            return {
                "total_rooms": len(self.room_connections),
                "total_active_connections": sum(
                    len(conns) for conns in self.room_connections.values()
                ),
                "rooms": list(self.room_connections.keys()),
                "connection_stats": self.connection_stats,
                "queue_stats": self.queue_stats,
            }

    def ensure_lobby_broadcast_task(self):
        """
        Ensure lobby broadcast task is always running
        """
        if "lobby" not in self.broadcast_queues:
            self.broadcast_queues["lobby"] = asyncio.Queue()

        if "lobby" not in self.broadcast_tasks or self.broadcast_tasks["lobby"].done():
            self.broadcast_tasks["lobby"] = asyncio.create_task(
                self._process_broadcast_queue("lobby")
            )


# CREATE SINGLETON INSTANCE
_socket_manager = SocketManager()


# EXPORT MODULE-LEVEL FUNCTIONS (THIS WAS MISSING!)
async def register(room_id: str, websocket: WebSocket) -> WebSocket:
    """
    Register a WebSocket connection to a room.

    Args:
        room_id: The ID of the room to register to
        websocket: The WebSocket connection to register

    Returns:
        WebSocket: The registered WebSocket connection
    """
    return await _socket_manager.register(room_id, websocket)


def unregister(room_id: str, websocket: WebSocket):
    """
    Unregister a WebSocket connection from a room.

    Args:
        room_id: The ID of the room to unregister from
        websocket: The WebSocket connection to unregister
    """
    _socket_manager.unregister(room_id, websocket)


async def broadcast(room_id: str, event: str, data: dict):
    """
    Broadcast a message to all connections in a room.

    Args:
        room_id: The ID of the room to broadcast to
        event: The event type to send
        data: The event data payload
    """
    await _socket_manager.broadcast(room_id, event, data)


def get_room_stats(room_id: str = None) -> dict:
    """
    Get statistics for WebSocket connections.

    Args:
        room_id: Optional room ID to get stats for. If None, returns stats for all rooms.

    Returns:
        dict: Connection statistics including active connections, queue sizes, etc.
    """
    return _socket_manager.get_room_stats(room_id)


def ensure_lobby_ready():
    """
    Ensure the lobby broadcast task is running.

    Creates the lobby broadcast task if it doesn't exist or has completed.
    This maintains real-time room list updates for all lobby connections.
    """
    _socket_manager.ensure_lobby_broadcast_task()
