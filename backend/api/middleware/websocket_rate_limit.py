# backend/api/middleware/websocket_rate_limit.py

"""
WebSocket-specific rate limiting middleware.

This module provides rate limiting functionality tailored for WebSocket connections,
which have different patterns than REST endpoints.
"""

import time
import logging
import hashlib
from typing import Dict, Any
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import WebSocket

from .event_priority import get_priority_manager, EventPriority

# Set up logging
logger = logging.getLogger(__name__)

# Error codes - simplified version
ERROR_CODES_AVAILABLE = False

# Simple rate limit tracking
class SimpleRateLimitRule:
    """Simple rate limit rule for WebSocket events."""
    def __init__(self, requests: int, window_seconds: int, block_duration_seconds: int = 0, burst_multiplier: float = 1.0):
        self.requests = requests
        self.window_seconds = window_seconds
        self.block_duration_seconds = block_duration_seconds
        self.burst_multiplier = burst_multiplier

# WebSocket rate limit rules
WEBSOCKET_RATE_LIMITS = {
    # System events
    "ping": SimpleRateLimitRule(requests=120, window_seconds=60),  # 2 per second
    "ack": SimpleRateLimitRule(requests=200, window_seconds=60),  # High limit for acknowledgments
    "sync_request": SimpleRateLimitRule(requests=10, window_seconds=60),  # Prevent sync spam
    
    # Lobby events
    "request_room_list": SimpleRateLimitRule(requests=30, window_seconds=60),
    "get_rooms": SimpleRateLimitRule(requests=30, window_seconds=60),
    "create_room": SimpleRateLimitRule(requests=5, window_seconds=60, block_duration_seconds=300),  # 5 min block
    "join_room": SimpleRateLimitRule(requests=10, window_seconds=60),
    
    # Room management
    "get_room_state": SimpleRateLimitRule(requests=60, window_seconds=60),
    "remove_player": SimpleRateLimitRule(requests=10, window_seconds=60),
    "add_bot": SimpleRateLimitRule(requests=10, window_seconds=60),
    "leave_room": SimpleRateLimitRule(requests=5, window_seconds=60),
    "start_game": SimpleRateLimitRule(requests=3, window_seconds=60, block_duration_seconds=600),  # 10 min block
    
    # Game events - more restrictive
    "declare": SimpleRateLimitRule(requests=5, window_seconds=60, burst_multiplier=1.2),  # Max 5 declarations/min
    "play": SimpleRateLimitRule(requests=20, window_seconds=60),  # 20 plays/min
    "play_pieces": SimpleRateLimitRule(requests=20, window_seconds=60),
    "request_redeal": SimpleRateLimitRule(requests=3, window_seconds=60),
    "accept_redeal": SimpleRateLimitRule(requests=5, window_seconds=60),
    "decline_redeal": SimpleRateLimitRule(requests=5, window_seconds=60),
    
    # Default for unknown events
    "_default": SimpleRateLimitRule(requests=60, window_seconds=60),  # 1 per second default
}


class WebSocketRateLimiter:
    """
    Rate limiter specifically designed for WebSocket connections.
    
    Features:
    - Per-connection + per-event rate limiting
    - Automatic cleanup of old tracking data
    - Priority-based event handling
    - Burst allowance for certain events
    """

    def __init__(self, rules: Dict[str, SimpleRateLimitRule] = None):
        """
        Initialize the WebSocket rate limiter.

        Args:
            rules: Dictionary of event_type -> RateLimitRule mappings
        """
        self.rules = rules or WEBSOCKET_RATE_LIMITS
        self.connections: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "requests": defaultdict(list),
            "blocked_until": {},
            "warnings": 0,
            "last_cleanup": time.time()
        })
        self.priority_manager = get_priority_manager()
        self._last_global_cleanup = time.time()

    def _get_connection_key(self, websocket: WebSocket) -> str:
        """Generate a unique key for the connection."""
        # Use client host and port for identification
        client_host = websocket.client.host if websocket.client else "unknown"
        client_port = websocket.client.port if websocket.client else 0
        return f"{client_host}:{client_port}"

    def _cleanup_old_requests(self, connection_data: Dict[str, Any], current_time: float):
        """Remove old request timestamps outside the tracking window."""
        for event_type, timestamps in list(connection_data["requests"].items()):
            # Keep only requests within the largest window (60 seconds)
            connection_data["requests"][event_type] = [
                ts for ts in timestamps if current_time - ts < 60
            ]
            if not connection_data["requests"][event_type]:
                del connection_data["requests"][event_type]

    def _is_blocked(self, connection_data: Dict[str, Any], event_type: str, current_time: float) -> bool:
        """Check if the connection is blocked for this event type."""
        if event_type in connection_data["blocked_until"]:
            if current_time < connection_data["blocked_until"][event_type]:
                return True
            else:
                # Block has expired
                del connection_data["blocked_until"][event_type]
        return False

    async def check_rate_limit(self, websocket: WebSocket, event_type: str) -> tuple[bool, str]:
        """
        Check if a WebSocket event is allowed under rate limiting rules.

        Args:
            websocket: The WebSocket connection
            event_type: Type of event being sent

        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        current_time = time.time()
        connection_key = self._get_connection_key(websocket)
        connection_data = self.connections[connection_key]

        # Periodic cleanup (every 60 seconds per connection)
        if current_time - connection_data["last_cleanup"] > 60:
            self._cleanup_old_requests(connection_data, current_time)
            connection_data["last_cleanup"] = current_time

        # Check if blocked
        if self._is_blocked(connection_data, event_type, current_time):
            remaining_block = connection_data["blocked_until"][event_type] - current_time
            return False, f"Rate limit exceeded. Blocked for {int(remaining_block)} more seconds."

        # Get the rule for this event type
        rule = self.rules.get(event_type, self.rules.get("_default"))
        if not rule:
            # No rate limiting if no rule defined
            return True, "No rate limit applied"

        # Get request history for this event type
        request_history = connection_data["requests"][event_type]
        
        # Count requests in the time window
        window_start = current_time - rule.window_seconds
        recent_requests = [ts for ts in request_history if ts >= window_start]
        
        # Apply burst multiplier for calculation
        effective_limit = int(rule.requests * rule.burst_multiplier)
        
        if len(recent_requests) >= effective_limit:
            # Rate limit exceeded
            connection_data["warnings"] += 1
            
            # Block if specified
            if rule.block_duration_seconds > 0:
                connection_data["blocked_until"][event_type] = current_time + rule.block_duration_seconds
                logger.warning(
                    f"WebSocket {connection_key} blocked for {event_type} "
                    f"for {rule.block_duration_seconds} seconds"
                )
            
            return False, f"Rate limit exceeded: {len(recent_requests)}/{rule.requests} requests in {rule.window_seconds}s"
        
        # Request allowed - track it
        request_history.append(current_time)
        return True, "Request allowed"

    async def should_process_event(self, websocket: WebSocket, event_type: str, 
                                  priority: EventPriority = None) -> bool:
        """
        Determine if an event should be processed based on rate limits and priority.

        Args:
            websocket: The WebSocket connection
            event_type: Type of event
            priority: Event priority (optional)

        Returns:
            True if event should be processed
        """
        # High priority events bypass rate limiting
        if priority and priority == EventPriority.CRITICAL:
            return True

        allowed, reason = await self.check_rate_limit(websocket, event_type)
        
        if not allowed:
            logger.debug(f"Rate limit hit for {event_type}: {reason}")
            
        return allowed

    def get_connection_stats(self, websocket: WebSocket) -> Dict[str, Any]:
        """Get rate limiting statistics for a connection."""
        connection_key = self._get_connection_key(websocket)
        connection_data = self.connections.get(connection_key)
        
        if not connection_data:
            return {"status": "no_data"}
        
        current_time = time.time()
        stats = {
            "warnings": connection_data["warnings"],
            "active_blocks": {},
            "recent_requests": {}
        }
        
        # Check active blocks
        for event_type, blocked_until in connection_data["blocked_until"].items():
            if current_time < blocked_until:
                stats["active_blocks"][event_type] = int(blocked_until - current_time)
        
        # Count recent requests per event type
        for event_type, timestamps in connection_data["requests"].items():
            recent = [ts for ts in timestamps if current_time - ts < 60]
            if recent:
                stats["recent_requests"][event_type] = len(recent)
        
        return stats

    def cleanup_connection(self, websocket: WebSocket):
        """Clean up tracking data for a disconnected connection."""
        connection_key = self._get_connection_key(websocket)
        if connection_key in self.connections:
            del self.connections[connection_key]
            logger.debug(f"Cleaned up rate limit data for {connection_key}")

    def global_cleanup(self):
        """Perform global cleanup of old connection data."""
        current_time = time.time()
        
        # Only run every 5 minutes
        if current_time - self._last_global_cleanup < 300:
            return
        
        self._last_global_cleanup = current_time
        
        # Remove connections with no recent activity
        inactive_connections = []
        for conn_key, conn_data in self.connections.items():
            # If no requests in the last 10 minutes, consider inactive
            has_recent_activity = any(
                any(current_time - ts < 600 for ts in timestamps)
                for timestamps in conn_data["requests"].values()
            )
            
            if not has_recent_activity:
                inactive_connections.append(conn_key)
        
        for conn_key in inactive_connections:
            del self.connections[conn_key]
        
        if inactive_connections:
            logger.info(f"Cleaned up {len(inactive_connections)} inactive connections")


# Global instance
_websocket_rate_limiter = None


def get_websocket_rate_limiter() -> WebSocketRateLimiter:
    """Get the global WebSocket rate limiter instance."""
    global _websocket_rate_limiter
    if _websocket_rate_limiter is None:
        _websocket_rate_limiter = WebSocketRateLimiter()
    return _websocket_rate_limiter


# Convenience function for rate limit checking
async def check_websocket_rate_limit(websocket: WebSocket, event_type: str) -> tuple[bool, str]:
    """
    Check if a WebSocket event is allowed under rate limits.
    
    Args:
        websocket: The WebSocket connection
        event_type: Type of event being sent
        
    Returns:
        Tuple of (allowed: bool, reason: str)
    """
    limiter = get_websocket_rate_limiter()
    return await limiter.check_rate_limit(websocket, event_type)


# Legacy compatibility function
async def send_rate_limit_error(websocket: WebSocket, event_type: str, message: str = None):
    """
    Send a rate limit error message to the WebSocket client.
    
    Args:
        websocket: The WebSocket connection
        event_type: The event type that was rate limited
        message: Optional custom error message
    """
    error_message = message or f"Rate limit exceeded for event: {event_type}"
    
    try:
        await websocket.send_json({
            "event": "error",
            "data": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": error_message,
                "event_type": event_type
            }
        })
    except Exception as e:
        logger.error(f"Failed to send rate limit error: {e}")