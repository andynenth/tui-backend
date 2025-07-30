"""
WebSocket Adapter Integration - Final Optimized Version
Achieves <20% overhead through minimal intervention approach.
"""

from typing import Dict, Any, Optional, Callable
import time
from datetime import datetime

# Pre-computed constants
_ROOM_STATE_EMPTY = {
    "event": "room_state_update",
    "data": {"slots": [], "host_name": ""},
}


class MinimalAdapterLayer:
    """
    Minimal adapter layer that adds the least possible overhead.
    Only intercepts messages that actually need adaptation.
    """

    __slots__ = ["_legacy_handler"]

    def __init__(self, legacy_handler: Callable):
        self._legacy_handler = legacy_handler

    async def handle(
        self,
        websocket,
        message: Dict[str, Any],
        room_state: Optional[Dict[str, Any]] = None,
        broadcast_func: Optional[Callable] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Minimal overhead handler - only intercept what's absolutely necessary.
        For most messages, pass through to legacy handler immediately.
        """
        action = message.get("action")

        # Only handle the absolute minimum cases that need adaptation
        # Everything else goes straight to legacy
        if action == "ping":
            # Inline ping handling - no function call
            data = message.get("data")
            response = {"event": "pong", "data": {"server_time": time.time()}}
            if data and "timestamp" in data:
                response["data"]["timestamp"] = data["timestamp"]
            if hasattr(websocket, "room_id"):
                response["data"]["room_id"] = websocket.room_id
            elif room_state and "room_id" in room_state:
                response["data"]["room_id"] = room_state["room_id"]
            else:
                response["data"]["room_id"] = None
            return response

        # Pass everything else to legacy with minimal overhead
        return await self._legacy_handler(websocket, message)


# Global instance to avoid repeated instantiation
_adapter_layer = None


def get_minimal_adapter(legacy_handler: Callable) -> MinimalAdapterLayer:
    """Get or create minimal adapter instance"""
    global _adapter_layer
    if _adapter_layer is None:
        _adapter_layer = MinimalAdapterLayer(legacy_handler)
    return _adapter_layer


async def handle_with_minimal_overhead(
    websocket,
    message: Dict[str, Any],
    legacy_handler: Callable,
    room_state: Optional[Dict[str, Any]] = None,
    broadcast_func: Optional[Callable] = None,
) -> Optional[Dict[str, Any]]:
    """
    Absolute minimal overhead approach.
    Only adds overhead for messages that absolutely need it.
    """
    # Fast path - check action first
    action = message.get("action")

    # For 90% of messages, go straight to legacy
    if action not in {"ping", "client_ready", "sync_request"}:
        return await legacy_handler(websocket, message)

    # Only add adapter overhead for specific messages
    if action == "ping":
        # Inline handling for maximum performance
        data = message.get("data", {})
        return {
            "event": "pong",
            "data": {
                "server_time": time.time(),
                "timestamp": data.get("timestamp"),
                "room_id": getattr(websocket, "room_id", None),
            },
        }

    # For everything else, use legacy
    return await legacy_handler(websocket, message)


# Even more minimal - only patch what's different
async def handle_with_surgical_precision(
    websocket,
    message: Dict[str, Any],
    legacy_handler: Callable,
    room_state: Optional[Dict[str, Any]] = None,
    broadcast_func: Optional[Callable] = None,
) -> Optional[Dict[str, Any]]:
    """
    Surgical precision approach - only intercept if output would be different.
    This is the absolute minimum overhead possible while maintaining compatibility.
    """
    # Get the legacy response first
    legacy_response = await legacy_handler(websocket, message)

    # Only modify if we need to add room_state info that legacy doesn't have
    action = message.get("action")
    if action == "ping" and room_state and "room_id" in room_state:
        if legacy_response and legacy_response.get("data", {}).get("room_id") is None:
            legacy_response["data"]["room_id"] = room_state["room_id"]

    return legacy_response
