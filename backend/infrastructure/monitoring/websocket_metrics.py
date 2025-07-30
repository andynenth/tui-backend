"""
WebSocket Metrics and Monitoring

Provides metrics collection and monitoring capabilities for the WebSocket system.
"""

import time
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class EventMetrics:
    """Metrics for a specific event type"""

    event_name: str
    count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float("inf")
    max_duration_ms: float = 0.0
    last_occurrence: Optional[datetime] = None
    error_types: Dict[str, int] = field(default_factory=dict)

    @property
    def avg_duration_ms(self) -> float:
        """Calculate average duration"""
        if self.count == 0:
            return 0.0
        return self.total_duration_ms / self.count

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.count == 0:
            return 0.0
        return self.success_count / self.count

    def record_event(
        self, duration_ms: float, success: bool, error_type: Optional[str] = None
    ):
        """Record an event occurrence"""
        self.count += 1
        self.total_duration_ms += duration_ms
        self.min_duration_ms = min(self.min_duration_ms, duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)
        self.last_occurrence = datetime.utcnow()

        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            if error_type:
                self.error_types[error_type] = self.error_types.get(error_type, 0) + 1


@dataclass
class ConnectionMetrics:
    """Metrics for WebSocket connections"""

    total_connections: int = 0
    active_connections: int = 0
    total_disconnections: int = 0
    connection_errors: int = 0
    avg_connection_duration_sec: float = 0.0
    max_concurrent_connections: int = 0
    connections_by_room: Dict[str, int] = field(default_factory=dict)

    def record_connection(self, room_id: str):
        """Record a new connection"""
        self.total_connections += 1
        self.active_connections += 1
        self.max_concurrent_connections = max(
            self.max_concurrent_connections, self.active_connections
        )
        self.connections_by_room[room_id] = self.connections_by_room.get(room_id, 0) + 1

    def record_disconnection(self, room_id: str, duration_sec: float):
        """Record a disconnection"""
        self.total_disconnections += 1
        self.active_connections = max(0, self.active_connections - 1)

        if room_id in self.connections_by_room:
            self.connections_by_room[room_id] = max(
                0, self.connections_by_room[room_id] - 1
            )
            if self.connections_by_room[room_id] == 0:
                del self.connections_by_room[room_id]

        # Update average duration
        if self.total_disconnections > 0:
            self.avg_connection_duration_sec = (
                self.avg_connection_duration_sec * (self.total_disconnections - 1)
                + duration_sec
            ) / self.total_disconnections


@dataclass
class MessageMetrics:
    """Metrics for WebSocket messages"""

    total_messages: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    broadcast_count: int = 0
    total_broadcast_recipients: int = 0
    message_size_bytes: Dict[str, List[int]] = field(
        default_factory=lambda: defaultdict(list)
    )

    @property
    def avg_broadcast_recipients(self) -> float:
        """Calculate average broadcast recipients"""
        if self.broadcast_count == 0:
            return 0.0
        return self.total_broadcast_recipients / self.broadcast_count

    def record_message_received(self, event_type: str, size_bytes: int):
        """Record a received message"""
        self.total_messages += 1
        self.messages_received += 1
        self.message_size_bytes[event_type].append(size_bytes)

    def record_message_sent(self, event_type: str, size_bytes: int):
        """Record a sent message"""
        self.total_messages += 1
        self.messages_sent += 1
        self.message_size_bytes[event_type].append(size_bytes)

    def record_broadcast(self, recipient_count: int):
        """Record a broadcast"""
        self.broadcast_count += 1
        self.total_broadcast_recipients += recipient_count


class WebSocketMetricsCollector:
    """Main metrics collector for WebSocket system"""

    def __init__(self, window_size_minutes: int = 5):
        self.event_metrics: Dict[str, EventMetrics] = {}
        self.connection_metrics = ConnectionMetrics()
        self.message_metrics = MessageMetrics()

        # Time-series data for monitoring
        self.window_size = timedelta(minutes=window_size_minutes)
        self.time_series_events: deque = deque()
        self.time_series_connections: deque = deque()

        # Performance tracking
        self.slow_event_threshold_ms = 100.0
        self.slow_events: List[Dict[str, Any]] = []

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_old_data())

    async def record_event_start(self, event_name: str) -> float:
        """Record the start of an event (returns start time)"""
        return time.time() * 1000  # Convert to milliseconds

    async def record_event_end(
        self,
        event_name: str,
        start_time: float,
        success: bool,
        error_type: Optional[str] = None,
    ):
        """Record the end of an event"""
        duration_ms = (time.time() * 1000) - start_time

        # Get or create event metrics
        if event_name not in self.event_metrics:
            self.event_metrics[event_name] = EventMetrics(event_name)

        metrics = self.event_metrics[event_name]
        metrics.record_event(duration_ms, success, error_type)

        # Record time series data
        self.time_series_events.append(
            {
                "timestamp": datetime.utcnow(),
                "event": event_name,
                "duration_ms": duration_ms,
                "success": success,
            }
        )

        # Track slow events
        if duration_ms > self.slow_event_threshold_ms:
            self.slow_events.append(
                {
                    "event": event_name,
                    "duration_ms": duration_ms,
                    "timestamp": datetime.utcnow(),
                }
            )
            # Keep only last 100 slow events
            if len(self.slow_events) > 100:
                self.slow_events.pop(0)

        logger.debug(
            f"Event '{event_name}' completed in {duration_ms:.2f}ms "
            f"(success={success})"
        )

    async def record_connection(self, connection_id: str, room_id: str):
        """Record a new WebSocket connection"""
        self.connection_metrics.record_connection(room_id)

        self.time_series_connections.append(
            {"timestamp": datetime.utcnow(), "type": "connect", "room_id": room_id}
        )

        logger.info(
            f"New connection {connection_id} in room {room_id} "
            f"(active: {self.connection_metrics.active_connections})"
        )

    async def record_disconnection(
        self, connection_id: str, room_id: str, connection_start: float
    ):
        """Record a WebSocket disconnection"""
        duration_sec = time.time() - connection_start
        self.connection_metrics.record_disconnection(room_id, duration_sec)

        self.time_series_connections.append(
            {
                "timestamp": datetime.utcnow(),
                "type": "disconnect",
                "room_id": room_id,
                "duration_sec": duration_sec,
            }
        )

        logger.info(
            f"Disconnection {connection_id} from room {room_id} "
            f"after {duration_sec:.1f}s "
            f"(active: {self.connection_metrics.active_connections})"
        )

    async def record_message_received(self, event_type: str, message: Dict[str, Any]):
        """Record a received WebSocket message"""
        size_bytes = len(str(message))
        self.message_metrics.record_message_received(event_type, size_bytes)

    async def record_message_sent(self, event_type: str, message: Dict[str, Any]):
        """Record a sent WebSocket message"""
        size_bytes = len(str(message))
        self.message_metrics.record_message_sent(event_type, size_bytes)

    async def record_broadcast(
        self, room_id: str, event_type: str, recipient_count: int
    ):
        """Record a broadcast message"""
        self.message_metrics.record_broadcast(recipient_count)
        logger.debug(
            f"Broadcast '{event_type}' to {recipient_count} recipients in room {room_id}"
        )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "connections": {
                "total": self.connection_metrics.total_connections,
                "active": self.connection_metrics.active_connections,
                "disconnections": self.connection_metrics.total_disconnections,
                "errors": self.connection_metrics.connection_errors,
                "avg_duration_sec": round(
                    self.connection_metrics.avg_connection_duration_sec, 2
                ),
                "max_concurrent": self.connection_metrics.max_concurrent_connections,
                "by_room": dict(self.connection_metrics.connections_by_room),
            },
            "messages": {
                "total": self.message_metrics.total_messages,
                "sent": self.message_metrics.messages_sent,
                "received": self.message_metrics.messages_received,
                "broadcasts": self.message_metrics.broadcast_count,
                "avg_broadcast_recipients": round(
                    self.message_metrics.avg_broadcast_recipients, 2
                ),
            },
            "events": {
                event_name: {
                    "count": metrics.count,
                    "success_rate": round(metrics.success_rate, 3),
                    "avg_duration_ms": round(metrics.avg_duration_ms, 2),
                    "min_duration_ms": round(metrics.min_duration_ms, 2),
                    "max_duration_ms": round(metrics.max_duration_ms, 2),
                    "errors": metrics.error_count,
                    "error_types": dict(metrics.error_types),
                }
                for event_name, metrics in self.event_metrics.items()
            },
            "performance": {
                "slow_events_count": len(self.slow_events),
                "slow_event_threshold_ms": self.slow_event_threshold_ms,
            },
        }

    def get_event_metrics(self, event_name: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific event"""
        if event_name not in self.event_metrics:
            return None

        metrics = self.event_metrics[event_name]
        return {
            "event": event_name,
            "count": metrics.count,
            "success_count": metrics.success_count,
            "error_count": metrics.error_count,
            "success_rate": round(metrics.success_rate, 3),
            "avg_duration_ms": round(metrics.avg_duration_ms, 2),
            "min_duration_ms": round(metrics.min_duration_ms, 2),
            "max_duration_ms": round(metrics.max_duration_ms, 2),
            "last_occurrence": (
                metrics.last_occurrence.isoformat() if metrics.last_occurrence else None
            ),
            "error_types": dict(metrics.error_types),
        }

    def get_time_series_data(self, minutes: int = 5) -> Dict[str, Any]:
        """Get time series data for the last N minutes"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)

        # Filter events
        recent_events = [e for e in self.time_series_events if e["timestamp"] > cutoff]

        # Filter connections
        recent_connections = [
            c for c in self.time_series_connections if c["timestamp"] > cutoff
        ]

        return {
            "time_range": {
                "start": cutoff.isoformat(),
                "end": datetime.utcnow().isoformat(),
            },
            "events": recent_events,
            "connections": recent_connections,
        }

    async def _cleanup_old_data(self):
        """Background task to cleanup old time-series data"""
        while True:
            try:
                cutoff = datetime.utcnow() - self.window_size

                # Clean up old events
                while (
                    self.time_series_events
                    and self.time_series_events[0]["timestamp"] < cutoff
                ):
                    self.time_series_events.popleft()

                # Clean up old connections
                while (
                    self.time_series_connections
                    and self.time_series_connections[0]["timestamp"] < cutoff
                ):
                    self.time_series_connections.popleft()

                # Wait 60 seconds before next cleanup
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Error in metrics cleanup: {e}")
                await asyncio.sleep(60)


# Global metrics instance
metrics_collector = WebSocketMetricsCollector()
