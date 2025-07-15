# backend/api/middleware/websocket_rate_limit.py

import asyncio
import time
import logging
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
import hashlib

from fastapi import WebSocket

from .rate_limit import RateLimiter, RateLimitRule, get_rate_limiter
from .event_priority import get_priority_manager, EventPriority

# Set up logging
logger = logging.getLogger(__name__)

# Import error codes if available
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../shared'))
    from error_codes import ErrorCode, create_standard_error
    ERROR_CODES_AVAILABLE = True
except ImportError:
    ERROR_CODES_AVAILABLE = False


# Import configuration
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
    from config.rate_limits import get_rate_limit_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# Get WebSocket rate limit rules from configuration
if CONFIG_AVAILABLE:
    WEBSOCKET_RATE_LIMITS = get_rate_limit_config().get_websocket_rules()
else:
    # Fallback to hardcoded values if config not available
    WEBSOCKET_RATE_LIMITS = {
        # System events
        "ping": RateLimitRule(requests=120, window_seconds=60),  # 2 per second
        "ack": RateLimitRule(requests=200, window_seconds=60),  # High limit for acknowledgments
        "sync_request": RateLimitRule(requests=10, window_seconds=60),  # Prevent sync spam
        
        # Lobby events  
        "request_room_list": RateLimitRule(requests=30, window_seconds=60),
        "get_rooms": RateLimitRule(requests=30, window_seconds=60),
        "create_room": RateLimitRule(requests=5, window_seconds=60, block_duration_seconds=300),  # 5 min block
        "join_room": RateLimitRule(requests=10, window_seconds=60),
        
        # Room management
        "get_room_state": RateLimitRule(requests=60, window_seconds=60),
        "remove_player": RateLimitRule(requests=10, window_seconds=60),
        "add_bot": RateLimitRule(requests=10, window_seconds=60),
        "leave_room": RateLimitRule(requests=5, window_seconds=60),
        "start_game": RateLimitRule(requests=3, window_seconds=60, block_duration_seconds=600),  # 10 min block
        
        # Game events - more restrictive
        "declare": RateLimitRule(requests=5, window_seconds=60, burst_multiplier=1.2),  # Max 5 declarations/min
        "play": RateLimitRule(requests=20, window_seconds=60),  # 20 plays/min
        "play_pieces": RateLimitRule(requests=20, window_seconds=60),
        "request_redeal": RateLimitRule(requests=3, window_seconds=60, block_duration_seconds=300),
        "accept_redeal": RateLimitRule(requests=5, window_seconds=60),
        "decline_redeal": RateLimitRule(requests=5, window_seconds=60),
        "redeal_decision": RateLimitRule(requests=5, window_seconds=60),
        "player_ready": RateLimitRule(requests=10, window_seconds=60),
        "leave_game": RateLimitRule(requests=3, window_seconds=60),
        
        # Default for unknown events
        "default": RateLimitRule(requests=60, window_seconds=60, burst_multiplier=1.5)
    }


class WebSocketRateLimiter:
    """
    Rate limiter specifically designed for WebSocket connections.
    
    Features:
    - Per-connection rate limiting
    - Per-event-type rate limiting
    - Room-based rate limiting to prevent flooding
    - Client identification and tracking
    """
    
    def __init__(self):
        self.rate_limiter = get_rate_limiter()
        self.connection_stats: Dict[str, Dict[str, int]] = {}  # Track per-connection stats
        self.room_message_counts: Dict[str, Dict[str, int]] = {}  # Track messages per room
        
    def _get_client_id(self, websocket: WebSocket, room_id: str) -> str:
        """Generate a unique client identifier for a WebSocket connection"""
        # Try to get client IP
        client_host = "unknown"
        if hasattr(websocket, 'client') and websocket.client:
            client_host = websocket.client.host
            
        # Create a hash of connection details for privacy
        connection_string = f"{client_host}:{room_id}:{id(websocket)}"
        client_hash = hashlib.md5(connection_string.encode()).hexdigest()[:16]
        
        return client_hash
        
    async def check_websocket_message_rate_limit(self, 
                                               websocket: WebSocket,
                                               room_id: str,
                                               event_name: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if a WebSocket message should be rate limited.
        
        Args:
            websocket: The WebSocket connection
            room_id: The room ID (can be "lobby")
            event_name: The event type being sent
            
        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        # Get priority manager
        priority_manager = get_priority_manager()
        
        # Check if this event should bypass rate limiting
        if priority_manager.should_bypass_rate_limit(event_name):
            return True, {"bypassed": True, "reason": "critical_event"}
        
        # Get the appropriate rule
        rule = WEBSOCKET_RATE_LIMITS.get(event_name, WEBSOCKET_RATE_LIMITS["default"])
        
        # Get client identifier
        client_id = self._get_client_id(websocket, room_id)
        
        # Track connection statistics
        if client_id not in self.connection_stats:
            self.connection_stats[client_id] = {}
        if event_name not in self.connection_stats[client_id]:
            self.connection_stats[client_id][event_name] = 0
        current_count = self.connection_stats[client_id][event_name]
        
        # Adjust rate limit based on priority
        adjusted_limit, should_warn = priority_manager.adjust_rate_limit_for_priority(
            event_name, rule.requests, current_count
        )
        
        # Apply grace period if applicable
        final_limit = priority_manager.apply_grace_period_multiplier(
            client_id, event_name, adjusted_limit
        )
        
        # Create adjusted rule
        adjusted_rule = RateLimitRule(
            requests=final_limit,
            window_seconds=rule.window_seconds,
            burst_multiplier=rule.burst_multiplier,
            block_duration_seconds=rule.block_duration_seconds
        )
        
        # Check rate limit
        allowed, rate_info = await self.rate_limiter.check_websocket_rate_limit(
            room_id, client_id, event_name, adjusted_rule
        )
        
        # Update statistics
        self.connection_stats[client_id][event_name] += 1
        
        # Track room message counts
        if room_id not in self.room_message_counts:
            self.room_message_counts[room_id] = {}
        if event_name not in self.room_message_counts[room_id]:
            self.room_message_counts[room_id][event_name] = 0
        self.room_message_counts[room_id][event_name] += 1
        
        # Handle warnings and grace periods
        if allowed and should_warn:
            if priority_manager.should_send_warning(client_id, event_name):
                priority_manager.grant_grace_period(client_id, event_name)
                in_grace = priority_manager.check_grace_period(client_id, event_name)
                
                rate_info["warning"] = priority_manager.get_rate_limit_response(
                    event_name, True, 
                    final_limit - current_count, 
                    final_limit, 
                    in_grace
                )
        
        # Add priority info to response
        if not allowed:
            rate_info["priority"] = priority_manager.get_event_priority(event_name).name
            rate_info["grace_eligible"] = event_name in priority_manager.GRACE_ELIGIBLE_EVENTS
            
            # Log WebSocket rate limit violation
            logger.info(
                f"WebSocket rate limit exceeded for {event_name}",
                extra={
                    "rate_limit_data": {
                        "client_id": client_id,
                        "room_id": room_id,
                        "event_type": event_name,
                        "priority": rate_info["priority"],
                        "current_count": current_count,
                        "limit": final_limit,
                        "event": "ws_rate_limit_exceeded"
                    }
                }
            )
        elif allowed and "warning" in rate_info:
            # Log warning
            logger.debug(
                f"WebSocket rate limit warning for {event_name}",
                extra={
                    "rate_limit_data": {
                        "client_id": client_id,
                        "room_id": room_id,
                        "event_type": event_name,
                        "remaining": final_limit - current_count,
                        "limit": final_limit,
                        "in_grace": in_grace if 'in_grace' in locals() else False,
                        "event": "ws_rate_limit_warning"
                    }
                }
            )
        
        return allowed, rate_info
        
    async def check_room_flood(self, room_id: str, threshold: int = 1000) -> bool:
        """
        Check if a room is being flooded with messages.
        
        Args:
            room_id: The room to check
            threshold: Max messages per minute for the entire room
            
        Returns:
            True if room appears to be flooded
        """
        if room_id not in self.room_message_counts:
            return False
            
        # Count total messages in the last minute
        total_messages = sum(self.room_message_counts[room_id].values())
        
        return total_messages > threshold
        
    def get_connection_stats(self, client_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for WebSocket connections"""
        if client_id:
            return self.connection_stats.get(client_id, {})
        else:
            return {
                "total_connections": len(self.connection_stats),
                "total_messages": sum(
                    sum(events.values()) for events in self.connection_stats.values()
                ),
                "room_stats": {
                    room_id: sum(events.values()) 
                    for room_id, events in self.room_message_counts.items()
                }
            }
            
    async def cleanup_connection(self, websocket: WebSocket, room_id: str):
        """Clean up rate limiting data when a connection closes"""
        client_id = self._get_client_id(websocket, room_id)
        
        # Remove connection stats after a delay
        await asyncio.sleep(300)  # Keep stats for 5 minutes after disconnect
        
        if client_id in self.connection_stats:
            del self.connection_stats[client_id]


# Global WebSocket rate limiter instance
_websocket_rate_limiter = None


def get_websocket_rate_limiter() -> WebSocketRateLimiter:
    """Get the global WebSocket rate limiter instance"""
    global _websocket_rate_limiter
    if _websocket_rate_limiter is None:
        _websocket_rate_limiter = WebSocketRateLimiter()
    return _websocket_rate_limiter


async def check_websocket_rate_limit(websocket: WebSocket, 
                                   room_id: str, 
                                   event_name: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Convenience function to check WebSocket rate limits.
    
    Args:
        websocket: The WebSocket connection
        room_id: The room ID
        event_name: The event being sent
        
    Returns:
        Tuple of (allowed, rate_limit_info)
    """
    rate_limiter = get_websocket_rate_limiter()
    return await rate_limiter.check_websocket_message_rate_limit(websocket, room_id, event_name)


async def send_rate_limit_error(websocket: WebSocket, rate_info: Dict[str, Any]):
    """Send a rate limit error message to the client"""
    if ERROR_CODES_AVAILABLE:
        error = create_standard_error(
            ErrorCode.NETWORK_RATE_LIMITED,
            "Rate limit exceeded for this event type",
            context={
                "retry_after": rate_info.get("retry_after", 60),
                "limit": rate_info.get("limit"),
                "window": rate_info.get("window"),
                "blocked": rate_info.get("blocked", False)
            }
        )
        error_data = error.to_dict()
    else:
        error_data = {
            "message": rate_info.get("reason", "Rate limit exceeded. Please slow down."),
            "type": "rate_limit_error",
            "retry_after": rate_info.get("retry_after", 60),
            "limit": rate_info.get("limit"),
            "window": rate_info.get("window")
        }
        
    await websocket.send_json({
        "event": "error",
        "data": error_data
    })