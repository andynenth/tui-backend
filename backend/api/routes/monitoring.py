# backend/api/routes/monitoring.py
"""
Monitoring endpoints for API metrics and performance.
"""

from fastapi import APIRouter, Query
from typing import Optional
from backend.services.monitoring_service import metrics_collector, play_history_metrics
from backend.services.alert_service import alert_service

router = APIRouter(tags=["monitoring"])


@router.get("/metrics")
async def get_metrics():
    """
    Get overall API metrics summary.
    
    Returns performance metrics including:
    - Request counts by endpoint
    - Response time percentiles
    - Error rates
    - Cache hit rates
    """
    return metrics_collector.get_metrics_summary()


@router.get("/metrics/play-history")
async def get_play_history_metrics():
    """
    Get play history specific metrics.
    
    Returns:
    - Total rounds processed
    - Average rounds per request
    - Response size statistics
    - Format usage breakdown
    """
    general_metrics = metrics_collector.get_metrics_summary()
    play_history_stats = play_history_metrics.get_play_history_stats()
    
    # Extract play history endpoint metrics
    play_history_endpoints = {
        k: v for k, v in general_metrics["endpoints"].items() 
        if "play-history" in k
    }
    
    return {
        "general_metrics": play_history_endpoints,
        "specialized_metrics": play_history_stats,
        "timestamp": general_metrics["timestamp"]
    }


@router.get("/metrics/time-series")
async def get_time_series_metrics(
    endpoint: str = Query(..., description="Endpoint path to get metrics for"),
    minutes: int = Query(5, description="Number of minutes of data to retrieve", ge=1, le=60)
):
    """
    Get time series data for a specific endpoint.
    
    Returns arrays of timestamp and response time data for graphing.
    """
    data = metrics_collector.get_time_series_data(endpoint, minutes)
    
    if not data:
        return {
            "endpoint": endpoint,
            "minutes": minutes,
            "data_points": 0,
            "timestamps": [],
            "response_times": [],
            "error_count": 0
        }
    
    timestamps = [d["timestamp"] for d in data]
    response_times = [d["duration_ms"] for d in data]
    error_count = sum(1 for d in data if d["status_code"] >= 400)
    
    return {
        "endpoint": endpoint,
        "minutes": minutes,
        "data_points": len(data),
        "timestamps": timestamps,
        "response_times": response_times,
        "error_count": error_count,
        "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
        "max_response_time": max(response_times) if response_times else 0
    }


@router.post("/metrics/reset")
async def reset_metrics():
    """
    Reset all collected metrics.
    
    This should only be used for testing or when metrics become corrupted.
    """
    metrics_collector.reset_metrics()
    return {"status": "Metrics reset successfully"}


@router.get("/health/performance")
async def get_performance_health():
    """
    Get performance health status based on current metrics.
    
    Returns health indicators:
    - GREEN: All metrics within acceptable ranges
    - YELLOW: Some metrics approaching thresholds
    - RED: Critical performance issues detected
    """
    metrics = metrics_collector.get_metrics_summary()
    
    health_status = "GREEN"
    issues = []
    
    # Check overall error rate
    total_requests = metrics["overall"]["total_requests"]
    total_errors = metrics["overall"]["total_errors"]
    if total_requests > 0:
        error_rate = total_errors / total_requests
        if error_rate > 0.05:  # > 5% errors
            health_status = "RED"
            issues.append(f"High error rate: {error_rate:.2%}")
        elif error_rate > 0.02:  # > 2% errors
            health_status = "YELLOW"
            issues.append(f"Elevated error rate: {error_rate:.2%}")
    
    # Check endpoint performance
    for endpoint, stats in metrics["endpoints"].items():
        if stats["p95_response_time_ms"] > 2000:  # > 2s p95
            health_status = "RED" if health_status != "RED" else health_status
            issues.append(f"{endpoint}: Very slow p95 response time ({stats['p95_response_time_ms']}ms)")
        elif stats["p95_response_time_ms"] > 1000:  # > 1s p95
            health_status = "YELLOW" if health_status == "GREEN" else health_status
            issues.append(f"{endpoint}: Slow p95 response time ({stats['p95_response_time_ms']}ms)")
    
    # Check cache performance
    for cache_type, cache_stats in metrics["cache"].items():
        if cache_stats["hit_rate"] < 0.5:  # < 50% hit rate
            health_status = "YELLOW" if health_status == "GREEN" else health_status
            issues.append(f"{cache_type} cache: Low hit rate ({cache_stats['hit_rate']:.2%})")
    
    return {
        "status": health_status,
        "issues": issues,
        "metrics_summary": {
            "total_requests": total_requests,
            "error_rate": f"{(total_errors / total_requests * 100) if total_requests > 0 else 0:.2f}%",
            "slow_requests": metrics["overall"]["total_slow_requests"]
        }
    }


@router.get("/alerts")
async def get_alerts(
    minutes: int = Query(60, description="Number of minutes of alerts to retrieve", ge=1, le=1440),
    severity: Optional[str] = Query(None, description="Filter by severity (warning/critical)"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type")
):
    """
    Get recent performance alerts.
    
    Returns alerts triggered by slow queries and other performance issues.
    """
    alerts = alert_service.get_recent_alerts(
        minutes=minutes,
        severity=severity,
        alert_type=alert_type
    )
    
    return {
        "alerts": alerts,
        "count": len(alerts),
        "filter": {
            "minutes": minutes,
            "severity": severity,
            "alert_type": alert_type
        }
    }


@router.get("/alerts/summary")
async def get_alerts_summary():
    """
    Get summary of alert activity.
    
    Returns counts and breakdowns of alerts by severity and type.
    """
    return alert_service.get_alert_summary()


@router.post("/alerts/test")
async def test_alert(
    severity: str = Query("warning", description="Alert severity", pattern="^(warning|critical)$"),
    message: str = Query("Test alert message", description="Alert message"),
    duration_ms: Optional[float] = Query(None, description="Simulated duration for response time alerts")
):
    """
    Trigger a test alert for monitoring system validation.
    """
    if duration_ms is not None:
        # Test response time alert
        alert = alert_service.check_response_time(
            operation="test_operation",
            duration_ms=duration_ms,
            context={"test": True, "message": message}
        )
        
        return {
            "alert_triggered": alert is not None,
            "alert": alert.to_dict() if alert else None,
            "message": f"Response time alert {'triggered' if alert else 'not triggered'} for {duration_ms}ms"
        }
    else:
        # Test custom alert
        alert = alert_service.create_custom_alert(
            alert_type="test_alert",
            severity=severity,
            message=message,
            context={"test": True}
        )
        
        return {
            "alert_triggered": True,
            "alert": alert.to_dict(),
            "message": "Test alert created successfully"
        }