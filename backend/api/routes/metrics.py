"""
Metrics API Routes

Provides REST endpoints for accessing WebSocket metrics and monitoring data.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any
from datetime import datetime

from infrastructure.monitoring.websocket_metrics import metrics_collector

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])


@router.get("/summary")
async def get_metrics_summary() -> Dict[str, Any]:
    """
    Get a comprehensive summary of all WebSocket metrics.

    Returns metrics for:
    - Connections (total, active, by room)
    - Messages (sent, received, broadcasts)
    - Events (count, duration, success rate)
    - Performance (slow events)
    """
    return metrics_collector.get_metrics_summary()


@router.get("/events/{event_name}")
async def get_event_metrics(event_name: str) -> Dict[str, Any]:
    """
    Get detailed metrics for a specific event type.

    Args:
        event_name: The name of the event (e.g., 'create_room', 'ping')

    Returns:
        Detailed metrics including count, duration, success rate, and errors
    """
    metrics = metrics_collector.get_event_metrics(event_name)

    if metrics is None:
        raise HTTPException(
            status_code=404, detail=f"No metrics found for event '{event_name}'"
        )

    return metrics


@router.get("/events")
async def list_event_metrics() -> Dict[str, Any]:
    """
    List metrics for all tracked events.

    Returns:
        Summary of all events with basic metrics
    """
    summary = metrics_collector.get_metrics_summary()
    return {"events": summary["events"], "total_event_types": len(summary["events"])}


@router.get("/connections")
async def get_connection_metrics() -> Dict[str, Any]:
    """
    Get current connection metrics.

    Returns:
        Connection statistics including active connections and room distribution
    """
    summary = metrics_collector.get_metrics_summary()
    return summary["connections"]


@router.get("/messages")
async def get_message_metrics() -> Dict[str, Any]:
    """
    Get message traffic metrics.

    Returns:
        Message statistics including sent/received counts and broadcast info
    """
    summary = metrics_collector.get_metrics_summary()
    return summary["messages"]


@router.get("/time-series")
async def get_time_series_data(
    minutes: int = Query(
        default=5, ge=1, le=60, description="Number of minutes of data to retrieve"
    )
) -> Dict[str, Any]:
    """
    Get time-series data for events and connections.

    Args:
        minutes: Number of minutes of historical data (1-60)

    Returns:
        Time-series data for monitoring and graphing
    """
    return metrics_collector.get_time_series_data(minutes)


@router.get("/performance")
async def get_performance_metrics() -> Dict[str, Any]:
    """
    Get performance-related metrics.

    Returns:
        Performance data including slow events and thresholds
    """
    summary = metrics_collector.get_metrics_summary()

    # Calculate additional performance metrics
    event_metrics = summary["events"]

    # Find slowest events
    slowest_events = sorted(
        [
            {
                "event": name,
                "avg_duration_ms": data["avg_duration_ms"],
                "max_duration_ms": data["max_duration_ms"],
            }
            for name, data in event_metrics.items()
        ],
        key=lambda x: x["max_duration_ms"],
        reverse=True,
    )[
        :10
    ]  # Top 10 slowest

    # Find events with highest error rates
    error_prone_events = sorted(
        [
            {
                "event": name,
                "error_rate": 1.0 - data["success_rate"],
                "error_count": data["errors"],
            }
            for name, data in event_metrics.items()
            if data["errors"] > 0
        ],
        key=lambda x: x["error_rate"],
        reverse=True,
    )[
        :10
    ]  # Top 10 error-prone

    return {
        "performance": summary["performance"],
        "slowest_events": slowest_events,
        "error_prone_events": error_prone_events,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health")
async def get_metrics_health() -> Dict[str, Any]:
    """
    Get health status based on metrics.

    Returns:
        Health indicators based on current metrics
    """
    summary = metrics_collector.get_metrics_summary()

    # Define health thresholds
    health_status = "healthy"
    issues = []

    # Check connection health
    connections = summary["connections"]
    if connections["active"] > 1000:
        issues.append("High number of active connections")
        health_status = "warning"

    if connections["errors"] > connections["total"] * 0.1:  # >10% error rate
        issues.append("High connection error rate")
        health_status = "unhealthy"

    # Check event health
    for event_name, metrics in summary["events"].items():
        if metrics["success_rate"] < 0.9:  # <90% success rate
            issues.append(f"Low success rate for event '{event_name}'")
            health_status = "warning" if health_status == "healthy" else health_status

        if metrics["avg_duration_ms"] > 500:  # >500ms average
            issues.append(f"Slow performance for event '{event_name}'")
            health_status = "warning" if health_status == "healthy" else health_status

    return {
        "status": health_status,
        "issues": issues,
        "metrics": {
            "active_connections": connections["active"],
            "total_events": sum(m["count"] for m in summary["events"].values()),
            "avg_success_rate": sum(
                m["success_rate"] * m["count"] for m in summary["events"].values()
            )
            / max(1, sum(m["count"] for m in summary["events"].values())),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/reset")
async def reset_metrics() -> Dict[str, str]:
    """
    Reset all metrics (admin endpoint).

    Warning: This will clear all collected metrics data.
    """
    # In a production system, this would require authentication

    # Reset metrics
    metrics_collector.event_metrics.clear()
    metrics_collector.connection_metrics = type(metrics_collector.connection_metrics)()
    metrics_collector.message_metrics = type(metrics_collector.message_metrics)()
    metrics_collector.time_series_events.clear()
    metrics_collector.time_series_connections.clear()
    metrics_collector.slow_events.clear()

    return {
        "status": "success",
        "message": "All metrics have been reset",
        "timestamp": datetime.utcnow().isoformat(),
    }
