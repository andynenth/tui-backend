# Monitoring System Guide

## Overview

The Liap Tui monitoring system provides comprehensive performance tracking, alerting, and observability features. It consists of three core components: **Metrics Collection**, **Alert Management**, and **Health Monitoring**, all designed to ensure optimal system performance and rapid issue detection.

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌────────────────┐
│   API Request   │────►│   Metrics    │────►│   Metrics API  │
│   Middleware    │     │  Collector   │     │   /api/metrics │
└─────────────────┘     └──────┬───────┘     └────────────────┘
                               │
                               ▼
                        ┌──────────────┐     ┌────────────────┐
                        │    Alert     │────►│   Alerts API   │
                        │   Service    │     │   /api/alerts  │
                        └──────────────┘     └────────────────┘
                               │
                               ▼
                        ┌──────────────┐     ┌────────────────┐
                        │   Health     │────►│  Health Check  │
                        │   Monitor    │     │ /api/health/*  │
                        └──────────────┘     └────────────────┘
```

## Core Components

### 1. Metrics Collector (`backend/services/monitoring_service.py`)

Thread-safe metrics collection for API performance monitoring.

#### Key Features

- **Request Tracking**: Count, duration, status codes
- **Response Time Analysis**: P50, P95, P99 percentiles
- **Error Rate Monitoring**: 4xx, 5xx response tracking
- **Cache Performance**: Hit/miss ratios
- **Time Series Data**: Second-by-second metrics

#### Metrics Structure

```python
class MetricsCollector:
    def __init__(self, window_size_minutes: int = 60):
        # Sliding window for metrics
        self.window_size = timedelta(minutes=window_size_minutes)
        
        # Metric storage
        self.request_counts = defaultdict(int)
        self.response_times = defaultdict(lambda: deque(maxlen=1000))
        self.error_counts = defaultdict(int)
        self.cache_hits = defaultdict(int)
        self.cache_misses = defaultdict(int)
        self.slow_requests = defaultdict(int)  # > 1 second
```

#### Recording Metrics

```python
# Record API request
metrics_collector.record_request(
    endpoint="/api/rooms/123/play-history",
    method="GET",
    status_code=200,
    duration_ms=145.3
)

# Record cache performance
metrics_collector.record_cache_hit("play_history")
metrics_collector.record_cache_miss("play_history")
```

### 2. Alert Service (`backend/services/alert_service.py`)

Intelligent alerting system with threshold management and cooldowns.

#### Alert Thresholds

```python
@dataclass
class AlertThreshold:
    name: str
    threshold_ms: float
    severity: str  # "warning" or "critical"
    cooldown_seconds: int = 300  # 5 min default
```

#### Default Thresholds

| Alert Type | Threshold | Severity | Cooldown |
|------------|-----------|----------|----------|
| play_history_slow | 1000ms | warning | 5 min |
| play_history_critical | 3000ms | critical | 10 min |
| api_slow | 500ms | warning | 3 min |
| api_critical | 2000ms | critical | 10 min |

#### Alert Structure

```python
@dataclass
class Alert:
    alert_type: str
    severity: str
    message: str
    context: Dict
    timestamp: float
    alert_id: str
```

### 3. Health Monitor (`backend/api/services/health_monitor.py`)

Comprehensive health checking system for all components.

#### Health Check Levels

1. **Basic Health** (`/api/health`)
   - Simple alive check
   - Minimal overhead

2. **Detailed Health** (`/api/health/detailed`)
   - Component status
   - Database connectivity
   - WebSocket status

3. **Performance Health** (`/api/health/performance`)
   - Response time analysis
   - Resource utilization
   - Queue depths

## API Endpoints

### 1. Metrics Endpoints

#### GET `/api/metrics`
Overall API metrics summary.

**Response Example**:
```json
{
    "timestamp": "2025-09-02T10:30:00Z",
    "window_size_minutes": 60,
    "endpoints": {
        "GET:/api/rooms/{room_id}/play-history": {
            "request_count": 1234,
            "avg_response_time_ms": 145.3,
            "p50_response_time_ms": 120.5,
            "p95_response_time_ms": 289.7,
            "error_rate": 0.02,
            "slow_request_rate": 0.05
        }
    },
    "cache": {
        "play_history": {
            "hit_rate": 0.78,
            "total_hits": 962,
            "total_misses": 272
        }
    },
    "overall": {
        "total_requests": 5678,
        "total_errors": 23,
        "total_slow_requests": 45
    }
}
```

#### GET `/api/metrics/play-history`
Play history specific metrics.

**Response Example**:
```json
{
    "general_metrics": {
        "GET:/api/rooms/{room_id}/play-history": {
            "request_count": 1234,
            "avg_response_time_ms": 145.3
        }
    },
    "specialized_metrics": {
        "total_rounds_processed": 45678,
        "avg_rounds_per_request": 3.4,
        "response_size_stats": {
            "avg_kb": 12.5,
            "max_kb": 156.3
        },
        "format_breakdown": {
            "full": 0.65,
            "compact": 0.35
        }
    }
}
```

### 2. Alert Endpoints

#### GET `/api/alerts`
Get recent alerts.

**Query Parameters**:
- `severity`: Filter by severity (warning, critical)
- `limit`: Maximum alerts to return (default: 100)
- `since`: Timestamp to get alerts after

**Response Example**:
```json
{
    "alerts": [
        {
            "alert_id": "alert-1693654200123",
            "alert_type": "play_history_slow",
            "severity": "warning",
            "message": "Play history endpoint slow: 1523ms",
            "context": {
                "endpoint": "/api/rooms/abc123/play-history",
                "duration_ms": 1523,
                "rounds_requested": 5
            },
            "timestamp": 1693654200.123,
            "timestamp_iso": "2025-09-02T10:30:00.123Z"
        }
    ],
    "total_count": 15,
    "severity_breakdown": {
        "warning": 12,
        "critical": 3
    }
}
```

#### POST `/api/alerts/acknowledge/{alert_id}`
Acknowledge an alert.

### 3. Health Endpoints

#### GET `/api/health`
Basic health check.

**Response**:
```json
{
    "status": "healthy",
    "timestamp": "2025-09-02T10:30:00Z",
    "version": "1.4.9"
}
```

#### GET `/api/health/detailed`
Detailed component health.

**Response**:
```json
{
    "status": "healthy",
    "timestamp": "2025-09-02T10:30:00Z",
    "services": {
        "api": "healthy",
        "websocket": "healthy",
        "database": "healthy",
        "room_manager": {
            "status": "healthy",
            "active_rooms": 5,
            "total_connections": 20
        }
    },
    "metrics": {
        "uptime_seconds": 3600,
        "total_requests": 5678,
        "error_rate": 0.02
    }
}
```

#### GET `/api/health/performance`
Performance analysis.

**Response**:
```json
{
    "status": "healthy",
    "performance": {
        "current": {
            "avg_response_time_ms": 145.3,
            "p95_response_time_ms": 289.7,
            "requests_per_second": 12.5
        },
        "thresholds": {
            "warning_ms": 500,
            "critical_ms": 2000
        },
        "alerts": []
    }
}
```

## Integration

### 1. Automatic Metrics Collection

Metrics are collected automatically via middleware:

```python
# In FastAPI app
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration_ms = (time.time() - start_time) * 1000
    
    metrics_collector.record_request(
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
        duration_ms=duration_ms
    )
    
    return response
```

### 2. Alert Integration

Alerts can trigger webhooks or notifications:

```python
# Configure alert handlers
alert_service.add_handler(webhook_handler)
alert_service.add_handler(log_handler)
alert_service.add_handler(email_handler)

# Handlers receive Alert objects
def webhook_handler(alert: Alert):
    if alert.severity == "critical":
        send_webhook(ALERT_WEBHOOK_URL, alert.to_dict())
```

### 3. Health Check Integration

Health checks can be used by:
- Load balancers
- Container orchestrators
- Monitoring systems

```yaml
# Docker Compose example
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Monitoring Best Practices

### 1. Metric Collection

- **Sample Rate**: Collect all requests for accuracy
- **Window Size**: 60-minute sliding window balances memory/detail
- **Percentiles**: Track P50, P95, P99 for better insights
- **Cache Metrics**: Monitor hit rates to optimize performance

### 2. Alert Configuration

- **Thresholds**: Set based on baseline performance
- **Cooldowns**: Prevent alert fatigue
- **Severity**: Use warning for investigation, critical for action
- **Context**: Include relevant details for debugging

### 3. Health Monitoring

- **Levels**: Use basic for LB, detailed for debugging
- **Frequency**: Check every 30s for containers
- **Dependencies**: Include all critical services
- **Performance**: Track trends, not just current state

## Common Patterns

### 1. Performance Degradation Detection

```python
# Monitor response time trends
metrics = metrics_collector.get_metrics_summary()
endpoint_metrics = metrics["endpoints"]["GET:/api/rooms/{room_id}/play-history"]

if endpoint_metrics["p95_response_time_ms"] > 1000:
    # Investigate cache performance
    cache_metrics = metrics["cache"]["play_history"]
    if cache_metrics["hit_rate"] < 0.7:
        # Cache issues detected
        optimize_cache_strategy()
```

### 2. Alert Response Workflow

```python
# Handle critical alerts
recent_alerts = alert_service.get_recent_alerts(severity="critical")

for alert in recent_alerts:
    if alert.alert_type == "play_history_critical":
        # Check specific issues
        context = alert.context
        if context["rounds_requested"] > 10:
            # Large request optimization needed
            implement_pagination()
```

### 3. Health-Based Scaling

```python
# Auto-scale based on performance
health = await get_health_performance()

if health["performance"]["current"]["avg_response_time_ms"] > 300:
    if health["performance"]["current"]["requests_per_second"] > 20:
        # Scale up
        increase_container_count()
```

## Troubleshooting

### High Response Times

1. Check cache hit rates
2. Analyze slow request patterns
3. Review database query performance
4. Check concurrent connection count

### Alert Storms

1. Review threshold settings
2. Increase cooldown periods
3. Implement alert aggregation
4. Check for cascading failures

### Health Check Failures

1. Verify service dependencies
2. Check resource limits
3. Review error logs
4. Test component connectivity

## Future Enhancements

1. **Distributed Tracing**: Request flow visualization
2. **Custom Metrics**: Business-specific KPIs
3. **Predictive Alerts**: ML-based anomaly detection
4. **Dashboard Integration**: Grafana/Prometheus export
5. **SLA Monitoring**: Automated compliance tracking