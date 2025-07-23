# backend/api/routes/routes.py

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import backend.socket_manager
from shared_instances import shared_bot_manager, shared_room_manager
from backend.socket_manager import broadcast
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

# Import Pydantic models for OpenAPI documentation
from api.models.game_models import (
    HealthCheck,
    DetailedHealthCheck,
    ErrorResponse,
    HealthStatus,
)

from api.validation import RestApiValidator
from engine.state_machine.core import ActionType, GameAction

# Import debug routes
from . import debug

# Import EventStore for recovery endpoints
try:
    from api.services.event_store import event_store

    EVENT_STORE_AVAILABLE = True
except ImportError:
    EVENT_STORE_AVAILABLE = False
    event_store = None

print(f"socket_manager id in {__name__}: {id(backend.socket_manager)}")

# Global instances - REMOVED: RedealController (using state machine instead)
router = APIRouter()
room_manager = shared_room_manager
bot_manager = shared_bot_manager

# Mount debug router
router.include_router(debug.router)

# REMOVED: All redeal controller endpoints - state machine handles redeal logic

# ---------- WEBSOCKET MIGRATION COMPLETE ----------
# NOTE: ALL game operations have been migrated to WebSocket-only implementation.
# This includes both room management AND game actions (declare, play, redeal, etc.)
# The frontend exclusively uses WebSocket events for all game mechanics.
# Migration completed: January 2025
# See REST_TO_WEBSOCKET_MIGRATION.md for details.

# ---------- DEBUG / STATUS ----------


@router.get("/debug/room-stats")
async def get_room_stats(room_id: Optional[str] = Query(None)):
    """Get room statistics for debugging"""
    from backend.socket_manager import _socket_manager

    stats = _socket_manager.get_room_stats(room_id)

    if room_id:
        # Include room validation if specific room requested
        room = await room_manager.get_room(room_id)
        if room:
            validation = room.validate_state()
            stats["room_validation"] = validation
            stats["room_summary"] = await room.summary()

    return {"timestamp": time.time(), "stats": stats}


# ---------- LOBBY NOTIFICATION FUNCTIONS ----------
# NOTE: These functions are used by WebSocket room management.
# They remain active even though REST endpoints are removed.


async def notify_lobby_room_created(room_data):
    """Notify lobby clients about new room creation"""
    try:
        from backend.socket_manager import ensure_lobby_ready

        ensure_lobby_ready()

        await broadcast(
            "lobby",
            "room_created",
            {
                "room_id": room_data["room_id"],
                "host_name": room_data["host_name"],
                "timestamp": asyncio.get_event_loop().time(),
            },
        )

        # Also send updated room list
        available_rooms = await room_manager.list_rooms()
        await broadcast(
            "lobby",
            "room_list_update",
            {
                "rooms": available_rooms,
                "timestamp": asyncio.get_event_loop().time(),
                "reason": "new_room_created",
            },
        )
        print(f"✅ Notified lobby about new room: {room_data['room_id']}")
    except Exception as e:
        print(f"❌ Failed to notify lobby about new room: {e}")


async def notify_lobby_room_updated(room_data):
    """Notify lobby clients about room updates (occupancy changes)"""
    try:
        from backend.socket_manager import ensure_lobby_ready

        ensure_lobby_ready()

        await broadcast(
            "lobby",
            "room_updated",
            {
                "room_id": room_data["room_id"],
                "occupied_slots": room_data["occupied_slots"],
                "total_slots": room_data["total_slots"],
                "timestamp": asyncio.get_event_loop().time(),
            },
        )

        # Send fresh room list
        available_rooms = await room_manager.list_rooms()
        await broadcast(
            "lobby",
            "room_list_update",
            {
                "rooms": available_rooms,
                "timestamp": asyncio.get_event_loop().time(),
                "reason": "room_updated",
            },
        )
        print(f"✅ Notified lobby about room update: {room_data['room_id']}")
    except Exception as e:
        print(f"❌ Failed to notify lobby about room update: {e}")


async def notify_lobby_room_closed(room_id, reason="Room closed"):
    """Notify lobby clients about room closure"""
    try:
        await broadcast(
            "lobby",
            "room_closed",
            {
                "room_id": room_id,
                "reason": reason,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )

        # Send updated room list (without the closed room)
        available_rooms = await room_manager.list_rooms()
        await broadcast(
            "lobby",
            "room_list_update",
            {
                "rooms": available_rooms,
                "timestamp": asyncio.get_event_loop().time(),
                "reason": "room_closed",
            },
        )
        print(f"✅ Notified lobby about room closure: {room_id}")
    except Exception as e:
        print(f"❌ Failed to notify lobby about room closure: {e}")


# ---------- EVENT SOURCING & RECOVERY ENDPOINTS ----------


@router.get("/rooms/{room_id}/events/{since_sequence}")
async def get_room_events_since(room_id: str, since_sequence: int):
    """
    Client recovery: Get events that occurred after a specific sequence number

    Args:
        room_id: The room identifier
        since_sequence: Get events after this sequence number

    Returns:
        Dict: Events for client recovery
    """
    # Validate inputs
    room_id = RestApiValidator.validate_room_id(room_id)
    since_sequence = RestApiValidator.validate_sequence_number(since_sequence)

    if not EVENT_STORE_AVAILABLE or not event_store:
        raise HTTPException(status_code=501, detail="Event store not available")

    try:
        events = await event_store.get_events_since(room_id, since_sequence)

        return {
            "success": True,
            "room_id": room_id,
            "since_sequence": since_sequence,
            "event_count": len(events),
            "events": [event.to_dict() for event in events],
            "recovery_info": {
                "latest_sequence": events[-1].sequence if events else since_sequence,
                "has_more_events": len(events) > 0,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve events: {str(e)}"
        )


@router.get("/rooms/{room_id}/state")
async def get_room_reconstructed_state(room_id: str):
    """
    Client recovery: Get current room state reconstructed from events

    Args:
        room_id: The room identifier

    Returns:
        Dict: Complete room state for recovery
    """
    if not EVENT_STORE_AVAILABLE or not event_store:
        raise HTTPException(status_code=501, detail="Event store not available")

    try:
        # First try to get live room state
        room = await room_manager.get_room(room_id)
        if room and room.game:
            # Return live state if available
            return {
                "success": True,
                "room_id": room_id,
                "state_source": "live",
                "state": {
                    "phase": room.game.current_phase,
                    "players": [
                        {"name": p.name, "hand": [str(piece) for piece in p.hand]}
                        for p in room.game.players
                    ],
                    "round_number": room.game.round_number,
                    "game_active": True,
                },
                "recovery_info": {
                    "live_state_available": True,
                    "reconstructed_from_events": False,
                },
            }

        # Fallback to reconstructed state from events
        reconstructed_state = await event_store.replay_room_state(room_id)

        return {
            "success": True,
            "room_id": room_id,
            "state_source": "reconstructed",
            "state": reconstructed_state,
            "recovery_info": {
                "live_state_available": False,
                "reconstructed_from_events": True,
                "events_processed": reconstructed_state.get("events_processed", 0),
                "last_sequence": reconstructed_state.get("last_sequence", 0),
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get room state: {str(e)}"
        )


@router.get("/rooms/{room_id}/events")
async def get_all_room_events(
    room_id: str,
    limit: Optional[int] = Query(None, description="Limit number of events returned"),
):
    """
    Get all events for a room (for debugging and analysis)

    Args:
        room_id: The room identifier
        limit: Optional limit on number of events

    Returns:
        Dict: All events for the room
    """
    if not EVENT_STORE_AVAILABLE or not event_store:
        raise HTTPException(status_code=501, detail="Event store not available")

    try:
        events = await event_store.get_room_events(room_id, limit)

        return {
            "success": True,
            "room_id": room_id,
            "event_count": len(events),
            "events": [event.to_dict() for event in events],
            "analysis": {
                "first_event": events[0].created_at if events else None,
                "last_event": events[-1].created_at if events else None,
                "event_types": list(set(event.event_type for event in events)),
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve all events: {str(e)}"
        )


@router.get("/event-store/stats")
async def get_event_store_stats():
    """
    Get event store statistics for monitoring

    Returns:
        Dict: Event store statistics
    """
    if not EVENT_STORE_AVAILABLE or not event_store:
        raise HTTPException(status_code=501, detail="Event store not available")

    try:
        stats = await event_store.get_event_stats()
        health = await event_store.health_check()

        return {
            "success": True,
            "statistics": stats,
            "health": health,
            "features": {
                "event_persistence": True,
                "state_reconstruction": True,
                "client_recovery": True,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get event store stats: {str(e)}"
        )


@router.post("/event-store/cleanup")
async def cleanup_old_events(
    older_than_hours: int = Query(
        24, description="Remove events older than this many hours"
    )
):
    """
    Clean up old events from the event store

    Args:
        older_than_hours: Remove events older than this many hours

    Returns:
        Dict: Cleanup results
    """
    # Validate input
    older_than_hours = RestApiValidator.validate_older_than_hours(older_than_hours)

    if not EVENT_STORE_AVAILABLE or not event_store:
        raise HTTPException(status_code=501, detail="Event store not available")

    try:
        deleted_count = await event_store.cleanup_old_events(older_than_hours)

        return {
            "success": True,
            "deleted_events": deleted_count,
            "older_than_hours": older_than_hours,
            "cleanup_completed": True,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to cleanup events: {str(e)}"
        )


# ---------- HEALTH MONITORING & RECOVERY ENDPOINTS ----------


@router.get(
    "/health",
    response_model=HealthCheck,
    responses={
        200: {"description": "Service is healthy"},
        503: {"model": ErrorResponse, "description": "Service is unhealthy"},
    },
    tags=["health"],
    summary="Basic Health Check",
    description="Provides a basic health status for load balancers and monitoring systems",
)
async def health_check():
    """
    Basic health check for load balancers and monitoring systems.

    This endpoint is designed for:
    - Load balancer health checks
    - Simple uptime monitoring
    - Basic service availability verification

    Returns basic health status with minimal overhead.
    """
    try:
        # Import health monitor
        from api.services.health_monitor import health_monitor

        health_status = await health_monitor.get_health_status()

        # Determine HTTP status code
        if health_status.status.value == "healthy":
            status_code = 200
        elif health_status.status.value == "warning":
            status_code = 200  # Still operational
        else:  # critical or unknown
            status_code = 503  # Service unavailable

        response_data = {
            "status": health_status.status.value,
            "timestamp": health_status.last_check,
            "uptime_seconds": health_status.uptime_seconds,
            "uptime_formatted": health_status._format_uptime(),
            "version": "1.0.0",
            "service": "liap-tui-backend",
        }

        return JSONResponse(content=response_data, status_code=status_code)

    except Exception as e:
        return JSONResponse(
            content={
                "status": "critical",
                "error": str(e),
                "timestamp": time.time(),
                "service": "liap-tui-backend",
            },
            status_code=503,
        )


@router.get(
    "/health/detailed",
    response_model=DetailedHealthCheck,
    responses={
        200: {"description": "Detailed health information"},
        503: {"model": ErrorResponse, "description": "Service is unhealthy"},
    },
    tags=["health"],
    summary="Detailed Health Check",
    description="Provides comprehensive health information including system metrics and component status",
)
async def detailed_health_check():
    """
    Detailed health information for monitoring and debugging.

    This endpoint provides:
    - System resource usage (memory, CPU)
    - Component health status (database, WebSocket, game engine)
    - Active connections and room counts
    - Server uptime statistics
    - Performance metrics

    Useful for debugging performance issues and monitoring system health.
    """
    try:
        # Import health monitor and get system stats
        from api.services.health_monitor import health_monitor
        import psutil

        health_status = await health_monitor.get_health_status()

        # Convert component status to HealthStatus enum
        components = {
            "event_store": (
                HealthStatus.HEALTHY
                if EVENT_STORE_AVAILABLE
                else HealthStatus.UNHEALTHY
            ),
            "health_monitor": HealthStatus.HEALTHY,
            "recovery_manager": HealthStatus.HEALTHY,
            "websocket_manager": HealthStatus.HEALTHY,
            "room_manager": HealthStatus.HEALTHY,
            "rate_limiter": HealthStatus.HEALTHY,  # Will be updated based on actual status
        }

        # Check rate limiting status
        try:
            from api.middleware.rate_limit import get_rate_limiter

            rate_limiter = get_rate_limiter()
            rate_stats = rate_limiter.get_stats()

            # Calculate overall block rate
            total_requests = sum(
                stats.get("total_requests", 0)
                for stats in rate_stats.values()
                if isinstance(stats, dict)
            )
            total_blocked = sum(
                stats.get("blocked_requests", 0)
                for stats in rate_stats.values()
                if isinstance(stats, dict)
            )

            if total_requests > 0:
                block_rate = (total_blocked / total_requests) * 100
                if block_rate > 50:  # More than 50% blocked is unhealthy
                    components["rate_limiter"] = HealthStatus.UNHEALTHY
                elif block_rate > 20:  # More than 20% blocked is degraded
                    components["rate_limiter"] = HealthStatus.DEGRADED
        except Exception:
            components["rate_limiter"] = HealthStatus.UNKNOWN

        # Get memory usage
        process = psutil.Process()
        memory_usage_mb = process.memory_info().rss / 1024 / 1024

        # Get active rooms and connections
        active_rooms = len(room_manager.rooms)
        active_connections = sum(
            len(conns)
            for conns in backend.socket_manager._socket_manager.room_connections.values()
        )

        # Return in the expected DetailedHealthCheck format
        return {
            "status": (
                HealthStatus.HEALTHY
                if health_status.status.value == "healthy"
                else (
                    HealthStatus.DEGRADED
                    if health_status.status.value == "warning"
                    else HealthStatus.UNHEALTHY
                )
            ),
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "uptime_seconds": health_status.uptime_seconds,
            "components": components,
            "memory_usage_mb": memory_usage_mb,
            "active_rooms": active_rooms,
            "active_connections": active_connections,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get detailed health: {str(e)}"
        )


@router.get("/health/metrics")
async def health_metrics():
    """
    Prometheus-compatible metrics endpoint

    Returns:
        str: Metrics in Prometheus format
    """
    try:
        # Import health monitor and socket manager
        import sys

        from api.services.health_monitor import health_monitor

        sys.path.append("/Users/nrw/python/tui-project/liap-tui/backend")
        from socket_manager import _socket_manager as socket_manager

        health_status = await health_monitor.get_health_status()

        # Generate Prometheus-style metrics
        metrics = []

        # System metrics
        if "memory" in health_status.metrics:
            metrics.append(
                f"liap_memory_usage_percent {health_status.metrics['memory'].value}"
            )

        if "cpu" in health_status.metrics:
            metrics.append(
                f"liap_cpu_usage_percent {health_status.metrics['cpu'].value}"
            )

        if "disk" in health_status.metrics:
            metrics.append(
                f"liap_disk_usage_percent {health_status.metrics['disk'].value}"
            )

        # WebSocket metrics
        total_connections = sum(
            len(conns) for conns in socket_manager.room_connections.values()
        )
        total_pending = sum(
            len(pending) for pending in socket_manager.pending_messages.values()
        )

        metrics.append(f"liap_websocket_connections_total {total_connections}")
        metrics.append(f"liap_websocket_pending_messages_total {total_pending}")

        # Room metrics
        room_count = len(room_manager.rooms)
        active_games = sum(1 for room in room_manager.rooms.values() if room.started)

        metrics.append(f"liap_rooms_total {room_count}")
        metrics.append(f"liap_active_games_total {active_games}")

        # Health status (0=healthy, 1=warning, 2=critical, 3=unknown)
        status_map = {"healthy": 0, "warning": 1, "critical": 2, "unknown": 3}
        health_value = status_map.get(health_status.status.value, 3)
        metrics.append(f"liap_health_status {health_value}")

        # Uptime
        metrics.append(f"liap_uptime_seconds {health_status.uptime_seconds}")

        # Message delivery stats
        if socket_manager.message_stats:
            total_sent = sum(
                stats.sent for stats in socket_manager.message_stats.values()
            )
            total_acked = sum(
                stats.acknowledged for stats in socket_manager.message_stats.values()
            )
            total_failed = sum(
                stats.failed for stats in socket_manager.message_stats.values()
            )

            metrics.append(f"liap_messages_sent_total {total_sent}")
            metrics.append(f"liap_messages_acknowledged_total {total_acked}")
            metrics.append(f"liap_messages_failed_total {total_failed}")

            if total_sent > 0:
                success_rate = (total_acked / total_sent) * 100
                metrics.append(f"liap_message_success_rate_percent {success_rate}")

        # Add timestamp
        metrics.append(f"liap_metrics_generated_timestamp {time.time()}")

        from fastapi.responses import PlainTextResponse

        return PlainTextResponse(content="\n".join(metrics), media_type="text/plain")

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate metrics: {str(e)}"
        )


@router.get("/recovery/status")
async def recovery_status():
    """
    Get recovery system status and recent attempts

    Returns:
        Dict: Recovery system status
    """
    try:
        # Import recovery manager
        from api.services.recovery_manager import recovery_manager

        status = recovery_manager.get_recovery_status()

        return {"success": True, "recovery_system": status}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get recovery status: {str(e)}"
        )


@router.post("/recovery/trigger/{procedure_name}")
async def trigger_recovery(procedure_name: str, context: dict = None):
    """
    Manually trigger a recovery procedure

    Args:
        procedure_name: Name of the recovery procedure to trigger
        context: Optional context data for the recovery procedure

    Returns:
        Dict: Recovery execution result
    """
    try:
        # Import recovery manager
        from api.services.recovery_manager import recovery_manager

        success = await recovery_manager.trigger_recovery(procedure_name, context or {})

        return {
            "success": success,
            "procedure": procedure_name,
            "context": context,
            "triggered": True,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger recovery: {str(e)}"
        )


@router.get("/rate-limit/stats")
async def rate_limit_stats():
    """
    Get rate limiting statistics

    Returns:
        Dict: Rate limiting statistics including blocked requests and unique clients
    """
    try:
        from api.middleware.rate_limit import get_rate_limiter
        from api.middleware.websocket_rate_limit import get_websocket_rate_limiter

        # Get HTTP rate limiter stats
        http_limiter = get_rate_limiter()
        http_stats = http_limiter.get_stats()

        # Get WebSocket rate limiter stats
        ws_limiter = get_websocket_rate_limiter()
        ws_stats = ws_limiter.get_connection_stats()

        return {
            "success": True,
            "timestamp": time.time(),
            "http_rate_limits": http_stats,
            "websocket_rate_limits": ws_stats,
            "rate_limiting_enabled": True,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get rate limit stats: {str(e)}"
        )


@router.get("/system/stats")
async def system_stats():
    """
    Get comprehensive system statistics

    Returns:
        Dict: System statistics including health, recovery, and performance data
    """
    try:
        # Import all services
        import sys

        from api.services.health_monitor import health_monitor
        from api.services.recovery_manager import recovery_manager

        sys.path.append("/Users/nrw/python/tui-project/liap-tui/backend")
        from socket_manager import _socket_manager as socket_manager

        # Get health status
        health_status = await health_monitor.get_health_status()

        # Get recovery status
        recovery_status = recovery_manager.get_recovery_status()

        # Get socket manager stats
        socket_stats = socket_manager.get_message_stats()

        # Get room stats
        room_stats = {
            "total_rooms": len(room_manager.rooms),
            "active_games": sum(
                1 for room in room_manager.rooms.values() if room.started
            ),
            "total_players": sum(
                len([slot for slot in room.slots if slot is not None])
                for room in room_manager.rooms.values()
            ),
        }

        # Get event store stats if available
        event_stats = {}
        if EVENT_STORE_AVAILABLE and event_store:
            event_stats = await event_store.get_event_stats()

        return {
            "success": True,
            "timestamp": time.time(),
            "health": health_status.to_dict(),
            "recovery": recovery_status,
            "websocket": socket_stats,
            "rooms": room_stats,
            "events": event_stats,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get system stats: {str(e)}"
        )


@router.get(
    "/metrics/rate_limits",
    tags=["monitoring"],
    summary="Get rate limit metrics",
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "Rate limit metrics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "timestamp": 1234567890.123,
                        "rate_limiting": {
                            "enabled": True,
                            "configuration": {
                                "global_rpm": 100,
                                "burst_multiplier": 1.5,
                            },
                            "rest_api": {
                                "total_requests": 12345,
                                "blocked_requests": 123,
                                "unique_clients": 45,
                                "endpoints": {
                                    "/api/health": {
                                        "total": 5000,
                                        "blocked": 50,
                                        "block_rate": 1.0,
                                    }
                                },
                            },
                            "websocket": {
                                "total_connections": 234,
                                "total_messages": 45678,
                                "rate_limited_events": 567,
                                "by_event": {
                                    "declare": {"total": 1000, "blocked": 100}
                                },
                            },
                        },
                    }
                }
            },
        },
        500: {"model": ErrorResponse},
    },
)
async def get_rate_limit_metrics():
    """
    Get comprehensive rate limit metrics.

    Returns detailed statistics about rate limiting including:
    - Current configuration
    - REST API rate limit statistics
    - WebSocket rate limit statistics
    - Per-endpoint/event breakdown
    - Client tracking information
    """
    try:
        # Import rate limiting components
        from api.middleware.rate_limit import get_rate_limiter
        from api.middleware.websocket_rate_limit import get_websocket_rate_limiter

        # Import configuration if available
        try:
            from config.rate_limits import get_rate_limit_config

            config = get_rate_limit_config()
            config_data = config.to_dict()
        except ImportError:
            config_data = {"error": "Configuration module not available"}

        # Get rate limiter instances
        rate_limiter = get_rate_limiter()
        ws_rate_limiter = get_websocket_rate_limiter()

        # Get REST API stats
        rest_stats = rate_limiter.get_stats()

        # Get WebSocket stats
        ws_stats = ws_rate_limiter.get_connection_stats()

        # Get current limit configuration
        current_limits = {"rest_api": {}, "websocket": {}}

        # Add REST API limits from config
        if "error" not in config_data:
            current_limits["rest_api"] = config_data.get("rest_api_limits", {})
            current_limits["websocket"] = config_data.get("websocket_limits", {})

        return {
            "success": True,
            "timestamp": time.time(),
            "rate_limiting": {
                "enabled": (
                    config_data.get("enabled", True)
                    if "error" not in config_data
                    else "unknown"
                ),
                "configuration": config_data,
                "current_limits": current_limits,
                "rest_api": rest_stats,
                "websocket": ws_stats,
                "summary": {
                    "total_blocked": sum(
                        stats.get("blocked_requests", 0)
                        for stats in rest_stats.values()
                        if isinstance(stats, dict)
                    ),
                    "active_blocks": (
                        len(rate_limiter.blocked_until)
                        if hasattr(rate_limiter, "blocked_until")
                        else 0
                    ),
                },
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get rate limit metrics: {str(e)}"
        )
