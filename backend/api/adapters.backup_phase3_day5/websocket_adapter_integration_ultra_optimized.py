"""
WebSocket Adapter Integration - Ultra Optimized Version
Minimal overhead implementation with aggressive optimizations.
"""

from typing import Dict, Any, Optional, Callable
import logging

# Import adapters directly to avoid function calls
from api.adapters.connection_adapters_optimized import (
    PingAdapter,
    ClientReadyAdapter,
    AckAdapter,
    SyncRequestAdapter,
)

logger = logging.getLogger(__name__)

# Pre-instantiate all adapters at module level
_ping_adapter = PingAdapter()
_client_ready_adapter = ClientReadyAdapter()
_ack_adapter = AckAdapter()
_sync_request_adapter = SyncRequestAdapter()

# Direct mapping for O(1) lookup - no registry needed
_ADAPTER_MAP = {
    "ping": _ping_adapter,
    "client_ready": _client_ready_adapter,
    "ack": _ack_adapter,
    "sync_request": _sync_request_adapter,
}

# Pre-compute enabled set
_ENABLED_ACTIONS = {"ping", "client_ready", "ack", "sync_request"}


async def handle_websocket_message_ultra_optimized(
    websocket,
    message: Dict[str, Any],
    legacy_handler: Callable,
    room_state: Optional[Dict[str, Any]] = None,
    broadcast_func: Optional[Callable] = None,
) -> Optional[Dict[str, Any]]:
    """
    Ultra-optimized WebSocket message handler.
    Minimizes all overhead with direct lookups and minimal branching.
    """
    action = message.get("action")

    # Fast path - direct adapter lookup
    if action in _ENABLED_ACTIONS:
        adapter = _ADAPTER_MAP[action]
        # Direct call without try/except in hot path
        response = await adapter.handle(websocket, message, room_state, broadcast_func)

        # Handle special cases inline without branching
        if response is not None or action == "ack":
            return response

    # Fallback to legacy
    return await legacy_handler(websocket, message)


# Even more optimized version using function dispatch
async def _handle_ping(websocket, message, room_state, broadcast_func):
    """Direct ping handler"""
    import time

    data = message.get("data")

    response = {"event": "pong", "data": {"server_time": time.time()}}

    if data and "timestamp" in data:
        response["data"]["timestamp"] = data["timestamp"]

    if room_state and "room_id" in room_state:
        response["data"]["room_id"] = room_state["room_id"]
    elif hasattr(websocket, "room_id"):
        response["data"]["room_id"] = websocket.room_id
    else:
        response["data"]["room_id"] = None

    return response


async def _handle_client_ready(websocket, message, room_state, broadcast_func):
    """Direct client ready handler"""
    if room_state:
        return {
            "event": "room_state_update",
            "data": {
                "slots": room_state.get("players", []),
                "host_name": room_state.get("host_name", ""),
            },
        }

    return {"event": "room_state_update", "data": {"slots": [], "host_name": ""}}


async def _handle_ack(websocket, message, room_state, broadcast_func):
    """Direct ack handler"""
    return None


async def _handle_sync_request(websocket, message, room_state, broadcast_func):
    """Direct sync request handler"""
    from datetime import datetime

    data = message.get("data", {})
    client_id = data.get("client_id")
    timestamp = datetime.now().isoformat()

    if room_state:
        return {
            "event": "sync_response",
            "data": {
                "room_state": room_state,
                "client_id": client_id,
                "timestamp": timestamp,
            },
        }

    return {
        "event": "sync_response",
        "data": {"room_state": None, "client_id": client_id, "timestamp": timestamp},
    }


# Direct function dispatch table - fastest possible lookup
_DIRECT_HANDLERS = {
    "ping": _handle_ping,
    "client_ready": _handle_client_ready,
    "ack": _handle_ack,
    "sync_request": _handle_sync_request,
}


async def handle_websocket_message_direct_dispatch(
    websocket,
    message: Dict[str, Any],
    legacy_handler: Callable,
    room_state: Optional[Dict[str, Any]] = None,
    broadcast_func: Optional[Callable] = None,
) -> Optional[Dict[str, Any]]:
    """
    Direct dispatch version - minimal overhead possible.
    Uses function pointers for direct dispatch without any adapter overhead.
    """
    action = message.get("action")

    # Direct function lookup and call
    handler = _DIRECT_HANDLERS.get(action)
    if handler:
        return await handler(websocket, message, room_state, broadcast_func)

    # Fallback to legacy
    return await legacy_handler(websocket, message)
