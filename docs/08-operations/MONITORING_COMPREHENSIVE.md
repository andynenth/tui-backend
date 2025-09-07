# Comprehensive Monitoring & Observability Guide

## Overview

This guide consolidates all monitoring documentation for the Liap Tui system, providing a complete reference for performance monitoring, health checks, alerting, and observability.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Metrics Collection](#metrics-collection)
4. [Health Monitoring](#health-monitoring)
5. [Performance Monitoring](#performance-monitoring)
6. [Alert System](#alert-system)
7. [Player Activity Monitoring](#player-activity-monitoring)
8. [Event Store & Logging](#event-store--logging)
9. [API Endpoints](#api-endpoints)
10. [EC2 Deployment Monitoring](#ec2-deployment-monitoring)
11. [Dashboards & Visualization](#dashboards--visualization)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)

## Architecture Overview

The monitoring system consists of integrated components providing comprehensive observability:

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   FastAPI   │  │  WebSocket   │  │   Game Engine   │   │
│  │   Routes    │  │   Handlers   │  │   State Machine │   │
│  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘   │
│         │                 │                    │             │
├─────────┼─────────────────┼────────────────────┼────────────┤
│         ▼                 ▼                    ▼             │
│                    Monitoring Layer                          │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   Metrics   │  │    Health    │  │     Alert       │   │
│  │  Collector  │  │   Monitor    │  │    Service      │   │
│  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘   │
│         │                 │                    │             │
├─────────┼─────────────────┼────────────────────┼────────────┤
│         ▼                 ▼                    ▼             │
│                     Storage Layer                            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ Time Series │  │  Event Store │  │   Structured    │   │
│  │   Metrics   │  │   (SQLite)   │  │     Logs        │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                     External Access                          │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Health API │  │  Metrics API │  │ Prometheus/     │   │
│  │  Endpoints  │  │   Endpoints  │  │  Grafana        │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Metrics Collector (`backend/services/monitoring_service.py`)

Thread-safe metrics collection with sliding window analysis.

```python
class MetricsCollector:
    def __init__(self, window_size_minutes: int = 60):
        self.window_size = timedelta(minutes=window_size_minutes)
        
        # Metric storage
        self.response_times = defaultdict(lambda: deque())
        self.error_counts = defaultdict(int)
        self.request_counts = defaultdict(int)
        self.cache_metrics = defaultdict(lambda: {"hits": 0, "misses": 0})
        
    def record_request(self, endpoint: str, method: str, status_code: int, duration_ms: float):
        """Record API request metrics"""
        timestamp = datetime.utcnow()
        
        # Store response time
        self.response_times[endpoint].append({
            "timestamp": timestamp,
            "duration_ms": duration_ms,
            "status_code": status_code
        })
        
        # Update counters
        self.request_counts[endpoint] += 1
        if status_code >= 400:
            self.error_counts[endpoint] += 1
```

### 2. Health Monitor (`backend/services/health_monitor.py`)

Real-time system health assessment with multi-level checks.

```python
class HealthMonitor:
    def __init__(self):
        self.checks = {
            "database": self.check_database,
            "websocket": self.check_websocket,
            "memory": self.check_memory,
            "disk": self.check_disk_space,
            "game_engine": self.check_game_engine
        }
        
    async def get_health_status(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        results = {}
        for name, check_func in self.checks.items():
            try:
                results[name] = await check_func()
            except Exception as e:
                results[name] = {"status": "unhealthy", "error": str(e)}
                
        overall_status = self._calculate_overall_status(results)
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results
        }
```

### 3. Alert Service (`backend/services/alert_service.py`)

Intelligent alerting with severity levels and escalation.

```python
class AlertService:
    def __init__(self):
        self.alerts = []
        self.alert_rules = {
            "high_error_rate": {
                "condition": lambda m: m.error_rate > 0.05,
                "severity": "critical",
                "message": "Error rate exceeds 5%"
            },
            "slow_response": {
                "condition": lambda m: m.p95_response_time > 2000,
                "severity": "warning",
                "message": "P95 response time > 2s"
            }
        }
```

## Metrics Collection

### Request Metrics

Track every API request with detailed timing and status:

```python
# Automatic middleware collection
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration_ms = (time.time() - start_time) * 1000
    metrics_collector.record_request(
        endpoint=str(request.url.path),
        method=request.method,
        status_code=response.status_code,
        duration_ms=duration_ms
    )
    
    return response
```

### Game Metrics

Monitor game-specific metrics:

```python
def record_game_event(event_type: str, room_id: str, data: Dict):
    """Record game-specific metrics"""
    metrics = {
        "game_started": lambda: increment_counter("games_started"),
        "player_joined": lambda: increment_gauge("active_players"),
        "round_completed": lambda: record_histogram("round_duration", data.get("duration")),
        "game_ended": lambda: increment_counter("games_completed")
    }
    
    if event_type in metrics:
        metrics[event_type]()
```

### WebSocket Metrics

Track real-time connection health:

```python
class WebSocketMetrics:
    def __init__(self):
        self.active_connections = 0
        self.message_counts = defaultdict(int)
        self.connection_durations = []
        
    def on_connect(self, client_id: str):
        self.active_connections += 1
        self.connection_start[client_id] = time.time()
        
    def on_message(self, event_type: str):
        self.message_counts[event_type] += 1
        
    def on_disconnect(self, client_id: str):
        self.active_connections -= 1
        duration = time.time() - self.connection_start.pop(client_id, 0)
        self.connection_durations.append(duration)
```

## Health Monitoring

### Multi-Level Health Checks

#### Basic Health (`/api/health`)
Quick endpoint for load balancers:
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Detailed Health (`/api/health/detailed`)
Comprehensive system status:
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "checks": {
        "database": {
            "status": "healthy",
            "response_time_ms": 1.2,
            "connections": 5
        },
        "websocket": {
            "status": "healthy",
            "active_connections": 42,
            "message_rate": 15.3
        },
        "memory": {
            "status": "healthy",
            "usage_percent": 45.2,
            "available_mb": 1024
        },
        "disk": {
            "status": "healthy",
            "usage_percent": 30.5,
            "free_gb": 25.3
        },
        "game_engine": {
            "status": "healthy",
            "active_games": 8,
            "processing_time_ms": 0.8
        }
    },
    "version": "2.0.0",
    "uptime_seconds": 86400
}
```

#### Performance Health (`/api/health/performance`)
Real-time performance assessment:
```json
{
    "status": "healthy",
    "issues": [],
    "metrics_summary": {
        "total_requests": 12345,
        "error_rate": "0.5%",
        "slow_requests": 12,
        "p95_response_time_ms": 234
    }
}
```

### Health Status Logic

```python
def calculate_health_status(metrics: Dict) -> str:
    """Determine overall health based on metrics"""
    
    # Critical checks
    if metrics["error_rate"] > 0.05:  # >5% errors
        return "unhealthy"
    if metrics["p95_response_time"] > 3000:  # >3s response
        return "unhealthy"
    if metrics["memory_usage"] > 0.90:  # >90% memory
        return "unhealthy"
        
    # Warning checks
    if metrics["error_rate"] > 0.02:  # >2% errors
        return "degraded"
    if metrics["p95_response_time"] > 1000:  # >1s response
        return "degraded"
    if metrics["memory_usage"] > 0.75:  # >75% memory
        return "degraded"
        
    return "healthy"
```

## Performance Monitoring

### Response Time Tracking

Monitor API response times with percentile analysis:

```python
def calculate_percentiles(times: List[float]) -> Dict[str, float]:
    """Calculate response time percentiles"""
    if not times:
        return {"p50": 0, "p95": 0, "p99": 0}
        
    sorted_times = sorted(times)
    return {
        "p50": sorted_times[len(times) // 2],
        "p95": sorted_times[int(len(times) * 0.95)],
        "p99": sorted_times[int(len(times) * 0.99)]
    }
```

### Performance Thresholds

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| P95 Response Time | < 500ms | < 1s | > 2s |
| Error Rate | < 1% | < 2% | > 5% |
| Cache Hit Rate | > 80% | > 60% | < 50% |
| Memory Usage | < 60% | < 75% | > 90% |
| CPU Usage | < 50% | < 70% | > 85% |

### Play History Performance

Special monitoring for expensive operations:

```python
class PlayHistoryMetrics:
    def record_play_history_request(
        self,
        room_id: str,
        total_rounds: int,
        response_size: int,
        build_time_ms: float,
        format: str = "full"
    ):
        # Alert on large responses
        if response_size > 1_000_000:  # 1MB
            logger.warning(
                f"Large play history response: {response_size} bytes",
                extra={"room_id": room_id, "rounds": total_rounds}
            )
            
        # Alert on slow builds
        if build_time_ms > 1000:  # 1 second
            create_alert(
                type="slow_play_history",
                severity="warning",
                details={
                    "room_id": room_id,
                    "build_time_ms": build_time_ms,
                    "rounds": total_rounds
                }
            )
```

## Alert System

### Alert Configuration

```python
ALERT_RULES = {
    # Performance alerts
    "slow_response": {
        "metric": "p95_response_time",
        "threshold": 2000,  # 2 seconds
        "severity": "warning",
        "cooldown": 300  # 5 minutes
    },
    "very_slow_response": {
        "metric": "p95_response_time", 
        "threshold": 5000,  # 5 seconds
        "severity": "critical",
        "cooldown": 600  # 10 minutes
    },
    
    # Error rate alerts
    "elevated_errors": {
        "metric": "error_rate",
        "threshold": 0.02,  # 2%
        "severity": "warning",
        "cooldown": 300
    },
    "high_errors": {
        "metric": "error_rate",
        "threshold": 0.05,  # 5%
        "severity": "critical",
        "cooldown": 600
    },
    
    # Resource alerts
    "high_memory": {
        "metric": "memory_usage_percent",
        "threshold": 85,
        "severity": "warning",
        "cooldown": 300
    },
    "critical_memory": {
        "metric": "memory_usage_percent",
        "threshold": 95,
        "severity": "critical",
        "cooldown": 60
    }
}
```

### Alert Delivery

```python
class AlertDelivery:
    async def send_alert(self, alert: Alert):
        """Send alert through configured channels"""
        
        # Log all alerts
        logger.warning(f"Alert: {alert.message}", extra=alert.to_dict())
        
        # Critical alerts
        if alert.severity == "critical":
            await self.send_pagerduty(alert)
            await self.send_slack(alert, channel="#alerts-critical")
            
        # Warning alerts
        elif alert.severity == "warning":
            await self.send_slack(alert, channel="#alerts-warning")
            
        # Store in alert history
        self.alert_history.append(alert)
```

## Player Activity Monitoring

Track player behavior and engagement:

### Activity Metrics

```python
class PlayerActivityMonitor:
    def __init__(self):
        self.player_sessions = {}
        self.game_participation = defaultdict(list)
        
    def track_player_action(self, player_id: str, action: str, metadata: Dict):
        """Track individual player actions"""
        
        self.player_sessions[player_id].append({
            "timestamp": datetime.utcnow(),
            "action": action,
            "metadata": metadata
        })
        
        # Track key metrics
        if action == "game_joined":
            self.increment_daily_active_users()
        elif action == "game_completed":
            self.record_game_duration(player_id, metadata["duration"])
        elif action == "disconnected":
            self.record_session_length(player_id)
```

### Engagement Metrics

- **Daily Active Users (DAU)**: Unique players per day
- **Session Length**: Average time connected
- **Games per Session**: Average games played
- **Win Rate**: Player success metrics
- **Retention**: Players returning next day

## Event Store & Logging

### Event Sourcing

All game events stored for replay and analysis:

```python
class EventStore:
    def __init__(self, db_path: str = "game_events.db"):
        self.db_path = db_path
        
    def store_event(self, event: GameEvent):
        """Store game event with metadata"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (
                    event_id, room_id, event_type, 
                    player_id, data, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event.id, event.room_id, event.type,
                event.player_id, json.dumps(event.data),
                event.timestamp
            ))
```

### Structured Logging

```python
import structlog

# Configure structured logging
logger = structlog.get_logger()

# Rich context logging
logger.info("game_action",
    room_id=room_id,
    player=player_name,
    action="play",
    pieces=piece_count,
    phase=game.phase,
    round=game.round_number,
    duration_ms=duration
)
```

## API Endpoints

### Metrics Endpoints

#### GET `/api/metrics`
Overall system metrics:
```json
{
    "endpoints": {
        "/api/health": {
            "request_count": 1234,
            "error_count": 5,
            "error_rate": 0.004,
            "p50_response_time_ms": 12,
            "p95_response_time_ms": 45,
            "p99_response_time_ms": 89
        }
    },
    "system": {
        "uptime_seconds": 86400,
        "total_requests": 45678,
        "total_errors": 123,
        "active_connections": 42
    },
    "cache": {
        "play_history": {
            "hits": 234,
            "misses": 56,
            "hit_rate": 0.807
        }
    }
}
```

#### GET `/api/metrics/time-series`
Historical metrics data:
```json
{
    "endpoint": "/api/rooms/{room_id}/play-history",
    "period": "5m",
    "data": [
        {
            "timestamp": "2024-01-15T10:25:00Z",
            "requests": 15,
            "errors": 0,
            "p95_ms": 234
        },
        {
            "timestamp": "2024-01-15T10:26:00Z",
            "requests": 18,
            "errors": 1,
            "p95_ms": 256
        }
    ]
}
```

#### GET `/api/alerts`
Recent alerts:
```json
{
    "alerts": [
        {
            "id": "alert_123",
            "timestamp": "2024-01-15T10:30:00Z",
            "severity": "warning",
            "type": "slow_response",
            "message": "P95 response time exceeded threshold",
            "details": {
                "endpoint": "/api/rooms/{room_id}/play-history",
                "p95_ms": 2150,
                "threshold_ms": 2000
            },
            "resolved": true,
            "resolved_at": "2024-01-15T10:32:00Z"
        }
    ]
}
```

## EC2 Deployment Monitoring

### CloudWatch Integration

```yaml
# cloudwatch-config.yml
metrics:
  namespace: "LiapTui/Production"
  metrics_collected:
    cpu:
      measurement:
        - name: cpu_usage_idle
        - name: cpu_usage_iowait
      totalcpu: true
    disk:
      measurement:
        - name: used_percent
      path: "/"
    mem:
      measurement:
        - name: mem_used_percent
```

### EC2-Specific Health Checks

```python
class EC2HealthMonitor:
    async def check_ec2_health(self):
        """EC2-specific health checks"""
        
        return {
            "instance_health": await self.check_instance_status(),
            "load_balancer": await self.check_alb_health(),
            "auto_scaling": await self.check_asg_status(),
            "disk_usage": await self.check_ebs_usage(),
            "network": await self.check_network_performance()
        }
```

### Monitoring Setup Script

```bash
#!/bin/bash
# setup_ec2_monitoring.sh

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
sudo rpm -U ./amazon-cloudwatch-agent.rpm

# Configure agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard

# Start agent
sudo systemctl start amazon-cloudwatch-agent
sudo systemctl enable amazon-cloudwatch-agent

# Setup custom metrics
cat > /opt/liap-tui/monitoring/custom_metrics.sh << 'EOF'
#!/bin/bash
# Send custom metrics to CloudWatch

# Active games metric
ACTIVE_GAMES=$(curl -s localhost:8000/api/metrics | jq '.game.active_games')
aws cloudwatch put-metric-data \
    --namespace "LiapTui/Production" \
    --metric-name ActiveGames \
    --value $ACTIVE_GAMES

# WebSocket connections
WS_CONNECTIONS=$(curl -s localhost:8000/api/metrics | jq '.websocket.active_connections')
aws cloudwatch put-metric-data \
    --namespace "LiapTui/Production" \
    --metric-name WebSocketConnections \
    --value $WS_CONNECTIONS
EOF

# Add to crontab
echo "* * * * * /opt/liap-tui/monitoring/custom_metrics.sh" | crontab -
```

## Dashboards & Visualization

### Grafana Dashboard Configuration

```json
{
    "dashboard": {
        "title": "Liap Tui Production Monitoring",
        "panels": [
            {
                "title": "API Response Times",
                "type": "graph",
                "targets": [
                    {
                        "expr": "http_request_duration_seconds{quantile=\"0.95\"}",
                        "legendFormat": "P95 Response Time"
                    }
                ]
            },
            {
                "title": "Active Games",
                "type": "stat",
                "targets": [
                    {
                        "expr": "liap_tui_active_games"
                    }
                ]
            },
            {
                "title": "Error Rate",
                "type": "gauge",
                "targets": [
                    {
                        "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
                    }
                ]
            },
            {
                "title": "WebSocket Connections",
                "type": "graph",
                "targets": [
                    {
                        "expr": "liap_tui_websocket_connections"
                    }
                ]
            }
        ]
    }
}
```

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'liap-tui'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/metrics/prometheus'
    
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

rule_files:
  - 'alerts.yml'
```

### Alert Rules

```yaml
# alerts.yml
groups:
  - name: liap_tui_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} (threshold: 0.05)"
          
      - alert: SlowAPIResponse
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow API responses detected"
          description: "P95 response time is {{ $value }}s (threshold: 2s)"
          
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"
```

## Best Practices

### 1. Metric Collection

```python
# DO: Use consistent metric names
metrics.record("api.request.duration", duration_ms, tags={"endpoint": "/api/health"})

# DON'T: Use inconsistent naming
metrics.record("apiRequestTime", duration_ms)
metrics.record("request_duration_api", duration_ms)

# DO: Include relevant tags
metrics.record("game.event", 1, tags={
    "event_type": "game_started",
    "room_id": room_id,
    "player_count": 4
})

# DON'T: Log sensitive information
metrics.record("user.login", 1, tags={
    "username": username,  # OK
    "password": password   # NEVER DO THIS
})
```

### 2. Alert Configuration

```python
# DO: Set reasonable thresholds based on baselines
alert_rules = {
    "response_time": {
        "threshold": baseline_p95 * 2,  # 2x normal
        "duration": 300  # 5 minutes
    }
}

# DON'T: Set arbitrary thresholds
alert_rules = {
    "response_time": {
        "threshold": 1000,  # Random number
        "duration": 1  # Too short
    }
}

# DO: Include context in alerts
create_alert(
    message=f"High error rate on {endpoint}",
    details={
        "error_rate": current_rate,
        "threshold": threshold,
        "recent_errors": get_recent_errors(5)
    }
)
```

### 3. Performance Optimization

```python
# DO: Use sampling for high-volume metrics
if random.random() < 0.1:  # 10% sampling
    metrics.record("detailed.trace", trace_data)

# DON'T: Log everything at full detail
for request in all_requests:  # Could be millions
    metrics.record("detailed.trace", full_request_data)

# DO: Aggregate before storing
aggregated = {
    "count": len(requests),
    "avg_duration": sum(r.duration for r in requests) / len(requests),
    "max_duration": max(r.duration for r in requests)
}
metrics.record("request.summary", aggregated)
```

### 4. Dashboard Design

- **Overview First**: High-level health at the top
- **Drill Down**: Detailed metrics below
- **Time Windows**: Include multiple time ranges
- **Annotations**: Mark deployments and incidents
- **Mobile Friendly**: Ensure readability on small screens

## Troubleshooting

### Common Issues

#### 1. Missing Metrics

**Problem**: Metrics not appearing in dashboard

**Solutions**:
```python
# Check metric collection
logger.debug(f"Recording metric: {metric_name} = {value}")

# Verify endpoint is registered
print(metrics_collector.get_registered_endpoints())

# Check time windows
# Metrics may be outside the query window
```

#### 2. Alert Storms

**Problem**: Too many alerts firing

**Solutions**:
```python
# Implement alert grouping
def group_alerts(alerts: List[Alert]) -> List[Alert]:
    grouped = defaultdict(list)
    for alert in alerts:
        key = f"{alert.type}:{alert.endpoint}"
        grouped[key].append(alert)
    
    # Return only one alert per group
    return [merge_alerts(group) for group in grouped.values()]

# Add cooldown periods
if time.time() - last_alert_time < COOLDOWN_SECONDS:
    logger.info(f"Suppressing alert due to cooldown")
    return
```

#### 3. Performance Impact

**Problem**: Monitoring causing performance issues

**Solutions**:
```python
# Use async collection
async def record_metric_async(name: str, value: float):
    asyncio.create_task(_record_metric(name, value))

# Batch metric writes
metric_buffer = []
if len(metric_buffer) >= BATCH_SIZE:
    await flush_metrics(metric_buffer)
    metric_buffer.clear()

# Reduce collection frequency
@throttle(seconds=10)  # Only collect every 10 seconds
def collect_expensive_metric():
    return calculate_expensive_value()
```

## Integration Examples

### Application Integration

```python
# FastAPI integration
from backend.services.monitoring import metrics_collector, health_monitor

app = FastAPI()

# Add monitoring middleware
app.add_middleware(MonitoringMiddleware, collector=metrics_collector)

# Health check routes
@app.get("/health")
async def health_check():
    return await health_monitor.get_basic_health()

@app.get("/health/detailed")
async def health_check_detailed():
    return await health_monitor.get_detailed_health()

# Metrics routes
@app.get("/metrics")
async def get_metrics():
    return metrics_collector.get_current_metrics()
```

### Docker Compose Integration

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONITORING_ENABLED=true
      - METRICS_PORT=9090
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - ./grafana/dashboards:/var/lib/grafana/dashboards
```

## Future Enhancements

1. **Machine Learning Alerts**: Anomaly detection for metrics
2. **Distributed Tracing**: Track requests across services
3. **Custom Dashboards**: Player-specific monitoring
4. **Mobile Alerts**: Push notifications for critical issues
5. **SLA Tracking**: Automated uptime and performance reporting

---

*This comprehensive guide consolidates all monitoring documentation. For specific implementation details, refer to the code files mentioned in each section.*