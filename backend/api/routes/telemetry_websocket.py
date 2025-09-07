# backend/api/routes/telemetry_websocket.py
"""
Real-time telemetry monitoring via WebSocket.
Provides live feed of telemetry events, alerts, and performance metrics.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set, Dict, List, Any
import json
import logging
import asyncio
import os
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path

router = APIRouter()
logger = logging.getLogger(__name__)

# Connected monitoring clients
connected_monitors: Set[WebSocket] = set()


# Database path (use same pattern as telemetry.py)
def get_telemetry_db_path() -> str:
    """Get telemetry database path with same pattern as telemetry.py."""
    # Check environment variable first (for production/Docker)
    env_db_path = os.getenv("TELEMETRY_DB_PATH")
    if env_db_path:
        return env_db_path
    else:
        # Fall back to data directory (for local development)
        current_dir = Path(__file__).resolve()
        project_root = current_dir.parent.parent.parent.parent
        return str(project_root / "data" / "telemetry_data.db")


DB_PATH = get_telemetry_db_path()


@router.websocket("/ws/telemetry-monitor")
async def telemetry_monitoring_websocket(websocket: WebSocket):
    """
    Live telemetry monitoring WebSocket endpoint.

    Provides real-time stream of:
    - Critical telemetry events (errors, failures)
    - Performance metrics and alerts
    - Session statistics
    - Live analytics data
    """
    await websocket.accept()
    connected_monitors.add(websocket)

    try:
        # Send initial dashboard data on connection
        initial_data = await get_dashboard_overview()
        await websocket.send_json(
            {
                "type": "initial_data",
                "timestamp": datetime.utcnow().isoformat(),
                "data": initial_data,
            }
        )

        logger.info(
            f"Telemetry monitor connected. Total monitors: {len(connected_monitors)}"
        )

        # Keep connection alive with periodic updates
        while True:
            try:
                # Wait for messages (ping/pong or commands)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                data = json.loads(message)

                # Handle different command types
                if data.get("command") == "get_recent_events":
                    recent_events = await get_recent_events(limit=data.get("limit", 20))
                    await websocket.send_json(
                        {
                            "type": "recent_events",
                            "timestamp": datetime.utcnow().isoformat(),
                            "data": recent_events,
                        }
                    )

                elif data.get("command") == "get_stats":
                    stats = await get_live_statistics()
                    await websocket.send_json(
                        {
                            "type": "live_stats",
                            "timestamp": datetime.utcnow().isoformat(),
                            "data": stats,
                        }
                    )

                elif data.get("command") == "ping":
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                    )

            except asyncio.TimeoutError:
                # Send periodic updates every 30 seconds
                stats = await get_live_statistics()
                await websocket.send_json(
                    {
                        "type": "periodic_update",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": stats,
                    }
                )

    except WebSocketDisconnect:
        logger.info("Telemetry monitor disconnected")
    except Exception as e:
        logger.error(f"Telemetry monitor error: {str(e)}")
    finally:
        connected_monitors.discard(websocket)
        logger.info(f"Monitor removed. Remaining monitors: {len(connected_monitors)}")


async def broadcast_telemetry_event(event_data: Dict[str, Any]):
    """
    Broadcast important telemetry events to all connected monitors.
    Called from the main telemetry processing pipeline.
    """
    if not connected_monitors:
        return

    # Filter and sanitize data for monitoring dashboard
    safe_event = {
        "type": "live_event",
        "timestamp": datetime.utcnow().isoformat(),
        "event": {
            "session_id": event_data.get("sessionId", "unknown"),
            "event_type": event_data.get("event", "unknown"),
            "user_agent": sanitize_user_agent(event_data.get("userAgent", "")),
            "connection": event_data.get("connection", {}),
            "error": event_data.get("error")
            if event_data.get("event")
            in ["bundle_error", "load_timeout", "load_failed", "javascript_error"]
            else None,
            "load_time": event_data.get("loadTime"),
            "attempt": event_data.get("attempt"),
            "severity": get_event_severity(event_data.get("event", "")),
        },
    }

    # Broadcast to all connected monitors
    disconnected = []
    for websocket in connected_monitors:
        try:
            await websocket.send_json(safe_event)
        except:
            disconnected.append(websocket)

    # Clean up disconnected clients
    for ws in disconnected:
        connected_monitors.discard(ws)


def sanitize_user_agent(user_agent: str) -> str:
    """Extract safe browser info from user agent"""
    if not user_agent:
        return "Unknown"

    # Extract browser and platform info only
    if "Chrome" in user_agent:
        browser = "Chrome"
    elif "Safari" in user_agent and "Chrome" not in user_agent:
        browser = "Safari"
    elif "Firefox" in user_agent:
        browser = "Firefox"
    elif "Edge" in user_agent:
        browser = "Edge"
    else:
        browser = "Other"

    # Detect platform
    if "Mobile" in user_agent or "Android" in user_agent or "iPhone" in user_agent:
        platform = "Mobile"
    elif "iPad" in user_agent:
        platform = "Tablet"
    else:
        platform = "Desktop"

    return f"{browser} ({platform})"


def get_event_severity(event_type: str) -> str:
    """Determine event severity for dashboard display"""
    critical_events = ["bundle_error", "load_failed", "javascript_error"]
    warning_events = ["load_timeout", "unhandled_rejection", "component_error"]

    if event_type in critical_events:
        return "critical"
    elif event_type in warning_events:
        return "warning"
    else:
        return "info"


async def get_dashboard_overview() -> Dict[str, Any]:
    """Get initial dashboard overview data"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get stats for last 24 hours
        since = datetime.utcnow() - timedelta(hours=24)

        cursor.execute(
            """
            SELECT
                COUNT(DISTINCT session_id) as total_sessions,
                COUNT(DISTINCT CASE WHEN bundle_load_success THEN session_id END) as successful_sessions,
                SUM(errors_count) as total_errors,
                AVG(bundle_load_time_ms) as avg_load_time,
                COUNT(DISTINCT CASE WHEN device_type = 'mobile' THEN session_id END) as mobile_sessions
            FROM telemetry_sessions
            WHERE created_at >= ?
        """,
            (since,),
        )

        stats = cursor.fetchone()

        if stats:
            total, successful, errors, avg_time, mobile = stats
            success_rate = successful / total if total > 0 else 0.0

            overview = {
                "total_sessions": total or 0,
                "success_rate": round(success_rate, 3),
                "total_errors": errors or 0,
                "avg_load_time": round(avg_time, 1) if avg_time else 0.0,
                "mobile_percentage": round(mobile / total * 100, 1)
                if total > 0
                else 0.0,
                "active_monitors": len(connected_monitors),
            }
        else:
            overview = {
                "total_sessions": 0,
                "success_rate": 0.0,
                "total_errors": 0,
                "avg_load_time": 0.0,
                "mobile_percentage": 0.0,
                "active_monitors": len(connected_monitors),
            }

        conn.close()
        return overview

    except Exception as e:
        logger.error(f"Failed to get dashboard overview: {str(e)}")
        return {
            "total_sessions": 0,
            "success_rate": 0.0,
            "total_errors": 0,
            "avg_load_time": 0.0,
            "mobile_percentage": 0.0,
            "active_monitors": len(connected_monitors),
            "error": str(e),
        }


async def get_recent_events(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent telemetry events for live feed"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                session_id,
                timestamp,
                event,
                data,
                user_agent,
                connection_type,
                received_at
            FROM telemetry_events
            WHERE event IN ('bundle_error', 'load_timeout', 'load_failed',
                           'javascript_error', 'unhandled_rejection', 'bundle_load_success',
                           'component_error')
            ORDER BY received_at DESC
            LIMIT ?
        """,
            (limit,),
        )

        events = []
        for row in cursor.fetchall():
            (
                session_id,
                timestamp,
                event_type,
                data_json,
                user_agent,
                conn_type,
                received_at,
            ) = row

            try:
                event_data = json.loads(data_json)
            except:
                event_data = {}

            events.append(
                {
                    "session_id": session_id[:8] + "...",  # Truncate for privacy
                    "timestamp": received_at,
                    "event_type": event_type,
                    "browser": sanitize_user_agent(user_agent),
                    "connection": conn_type or "unknown",
                    "error": event_data.get("error") or event_data.get("message"),
                    "load_time": event_data.get("loadTime"),
                    "attempt": event_data.get("attempt"),
                    "severity": get_event_severity(event_type),
                }
            )

        conn.close()
        return events

    except Exception as e:
        logger.error(f"Failed to get recent events: {str(e)}")
        return []


async def get_live_statistics() -> Dict[str, Any]:
    """Get live statistics for dashboard"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Stats for last hour
        since = datetime.utcnow() - timedelta(hours=1)

        cursor.execute(
            """
            SELECT
                COUNT(DISTINCT session_id) as sessions,
                COUNT(DISTINCT CASE WHEN bundle_load_success THEN session_id END) as successful,
                SUM(errors_count) as errors,
                AVG(bundle_load_time_ms) as avg_time,
                COUNT(DISTINCT CASE WHEN connection_type IN ('slow-2g', '2g') THEN session_id END) as slow_conn
            FROM telemetry_sessions
            WHERE created_at >= ?
        """,
            (since,),
        )

        stats = cursor.fetchone()

        # Recent error count (last 5 minutes)
        recent = datetime.utcnow() - timedelta(minutes=5)
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM telemetry_events
            WHERE received_at >= ?
              AND event IN ('bundle_error', 'load_timeout', 'load_failed', 'javascript_error')
        """,
            (recent,),
        )

        recent_errors = cursor.fetchone()[0]

        conn.close()

        if stats:
            sessions, successful, errors, avg_time, slow_conn = stats

            return {
                "last_hour": {
                    "sessions": sessions or 0,
                    "success_rate": round(successful / sessions, 3)
                    if sessions > 0
                    else 0.0,
                    "errors": errors or 0,
                    "avg_load_time": round(avg_time, 1) if avg_time else 0.0,
                    "slow_connections": slow_conn or 0,
                },
                "last_5_minutes": {"recent_errors": recent_errors},
                "monitors": {"connected": len(connected_monitors)},
            }
        else:
            return {
                "last_hour": {
                    "sessions": 0,
                    "success_rate": 0.0,
                    "errors": 0,
                    "avg_load_time": 0.0,
                    "slow_connections": 0,
                },
                "last_5_minutes": {"recent_errors": recent_errors},
                "monitors": {"connected": len(connected_monitors)},
            }

    except Exception as e:
        logger.error(f"Failed to get live statistics: {str(e)}")
        return {"error": str(e)}


# Export function for use in telemetry.py
async def notify_monitoring_dashboard(event_data: Dict[str, Any]):
    """
    Called from telemetry.py to notify the monitoring dashboard of critical events.
    This function can be imported and used in the main telemetry processing.
    """
    if connected_monitors:
        await broadcast_telemetry_event(event_data)
