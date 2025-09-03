# Performance Monitoring Guide

## Overview

This guide documents the comprehensive performance monitoring system for Liap Tui, including metrics collection, alerting, logging middleware, and performance analysis tools.

## Architecture Overview

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│  Request Middleware │     │  Metrics Collector  │     │   Alert Service     │
├─────────────────────┤     ├─────────────────────┤     ├─────────────────────┤
│ • Request timing    │ ──> │ • Aggregation       │ ──> │ • Threshold checks  │
│ • Response logging  │     │ • Time windows      │     │ • Notifications     │
│ • Performance flags │     │ • Statistics        │     │ • Escalation        │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
                                      ↓
                            ┌─────────────────────┐
                            │  Historical Writer  │
                            ├─────────────────────┤
                            │ • Time series data  │
                            │ • Long-term storage │
                            │ • Trend analysis    │
                            └─────────────────────┘
```

## Core Components

### 1. Logging Middleware

The `StructuredLoggingMiddleware` captures detailed metrics for every API request:

```python
# backend/api/middleware/logging_middleware.py

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Start timing
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log with performance warnings
        if duration_ms > 1000:  # Slow request (>1s)
            log_data["performance_warning"] = "slow_request"
        elif duration_ms > 500:  # Medium slow (>500ms)
            log_data["performance_warning"] = "medium_slow_request"
```

### 2. Monitoring Service

The `MonitoringService` provides real-time metrics collection and analysis:

```python
# backend/services/monitoring_service.py

class MonitoringService:
    def __init__(self):
        self.metrics_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.alert_thresholds = self._load_thresholds()
        
    def record_metric(self, metric_name: str, value: float, tags: Dict = None):
        """Record a metric with timestamp and optional tags"""
        
    def get_statistics(self, metric_name: str, window_minutes: int = 5) -> Dict:
        """Get statistics for a metric over a time window"""
        
    def check_alerts(self) -> List[Alert]:
        """Check all metrics against thresholds and return alerts"""
```

### 3. Performance Metrics

#### Request Metrics
- **Duration**: Total request processing time
- **Status Code**: HTTP response codes
- **Endpoint**: API path performance
- **Method**: GET/POST/WebSocket metrics

#### System Metrics
- **Memory Usage**: Process memory consumption
- **CPU Usage**: Process CPU percentage
- **Active Connections**: WebSocket connection count
- **Thread Count**: Active thread monitoring

#### Game Metrics
- **Room Count**: Active game rooms
- **Player Count**: Connected players
- **Message Rate**: WebSocket messages/second
- **Event Rate**: Game events/second

### 4. Alert Service

Automated alerting based on configurable thresholds:

```python
# backend/services/alert_service.py

class AlertService:
    ALERT_THRESHOLDS = {
        'response_time_ms': {
            'warning': 1000,    # 1 second
            'critical': 3000,   # 3 seconds
        },
        'error_rate': {
            'warning': 0.05,    # 5%
            'critical': 0.10,   # 10%
        },
        'memory_usage_mb': {
            'warning': 500,
            'critical': 800,
        }
    }
```

## Implementation Guide

### 1. Basic Setup

Enable monitoring in your FastAPI application:

```python
# backend/api/main.py

from backend.api.middleware.logging_middleware import StructuredLoggingMiddleware
from backend.services.monitoring_service import MonitoringService

app = FastAPI()

# Add logging middleware
app.add_middleware(StructuredLoggingMiddleware)

# Initialize monitoring
monitoring = MonitoringService()
app.state.monitoring = monitoring
```

### 2. Custom Metrics

Add custom metrics to your code:

```python
from backend.services.monitoring_service import metrics_collector

# Record custom metric
metrics_collector.record_metric(
    'game.turn_duration',
    duration_ms,
    tags={'room_id': room_id, 'turn_number': turn_number}
)

# Record counter
metrics_collector.increment_counter('game.turns_completed')

# Record gauge
metrics_collector.set_gauge('rooms.active', active_room_count)
```

### 3. Performance Annotations

Use decorators for automatic timing:

```python
from backend.services.monitoring_service import monitor_performance

@monitor_performance('play_history.build')
async def build_play_history(room_id: str) -> Dict:
    """Build complete play history with monitoring"""
    # Function automatically timed
    pass
```

## Monitoring Dashboards

### 1. Real-Time Dashboard

Access real-time metrics at `/api/monitoring/dashboard`:

```json
{
    "current_metrics": {
        "requests_per_minute": 120,
        "average_response_time_ms": 45.3,
        "error_rate": 0.002,
        "active_connections": 25,
        "memory_usage_mb": 125.6
    },
    "alerts": [
        {
            "severity": "warning",
            "metric": "response_time_p95",
            "value": 1250,
            "threshold": 1000,
            "message": "95th percentile response time exceeds 1 second"
        }
    ]
}
```

### 2. Historical Metrics

Query historical data via API:

```bash
# Get metrics for last hour
curl http://localhost:5050/api/monitoring/metrics?metric=response_time&window=1h

# Get specific endpoint performance
curl http://localhost:5050/api/monitoring/endpoints?path=/api/rooms/*/play-history

# Get error rates
curl http://localhost:5050/api/monitoring/errors?window=24h
```

### 3. WebSocket Monitoring

Real-time monitoring via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:5050/api/monitoring/ws');

ws.onmessage = (event) => {
  const metrics = JSON.parse(event.data);
  console.log('Current metrics:', metrics);
};
```

## Performance Thresholds

### API Endpoints

| Endpoint | Good | Warning | Critical |
|----------|------|---------|----------|
| Health Check | <10ms | 10-50ms | >50ms |
| Game State | <50ms | 50-200ms | >200ms |
| Play History | <500ms | 500-1000ms | >1000ms |
| WebSocket Message | <20ms | 20-100ms | >100ms |

### System Resources

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| CPU Usage | <50% | 50-80% | >80% |
| Memory Usage | <60% | 60-85% | >85% |
| Thread Count | <50 | 50-100 | >100 |
| File Descriptors | <500 | 500-900 | >900 |

### Game Performance

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Turn Processing | <100ms | 100-500ms | >500ms |
| State Broadcast | <50ms | 50-200ms | >200ms |
| AI Decision Time | <50ms | 50-200ms | >200ms |
| Event Store Write | <20ms | 20-100ms | >100ms |

## Alert Configuration

### Alert Channels

Configure alert destinations in `monitoring_config.yaml`:

```yaml
alerts:
  channels:
    - type: log
      level: WARNING
      
    - type: webhook
      url: ${ALERT_WEBHOOK_URL}
      severity: [critical]
      
    - type: email
      to: ops-team@example.com
      severity: [critical]
      rate_limit: 1_per_hour
```

### Alert Rules

Define custom alert rules:

```yaml
rules:
  high_error_rate:
    metric: error_rate
    condition: "value > 0.05"
    window: 5m
    severity: warning
    message: "Error rate exceeds 5% over 5 minutes"
    
  memory_leak:
    metric: memory_usage_mb
    condition: "rate_of_change > 10"
    window: 30m
    severity: critical
    message: "Potential memory leak detected"
    
  slow_endpoint:
    metric: endpoint_response_time_p95
    condition: "value > 1000"
    window: 5m
    severity: warning
    message: "Endpoint {endpoint} p95 exceeds 1 second"
```

## Performance Analysis Tools

### 1. Request Analysis

Analyze slow requests:

```python
# backend/scripts/analyze_performance.py

from backend.services.monitoring_service import monitoring_service

# Get slowest endpoints
slow_endpoints = monitoring_service.get_slow_endpoints(
    threshold_ms=500,
    window_minutes=60
)

for endpoint in slow_endpoints:
    print(f"{endpoint['path']}: {endpoint['p95_ms']}ms (p95)")
```

### 2. Performance Reports

Generate performance reports:

```bash
# Daily performance report
python scripts/performance_report.py --date 2024-01-09

# Endpoint comparison
python scripts/compare_endpoints.py --window 7d

# Trend analysis
python scripts/analyze_trends.py --metric response_time --days 30
```

### 3. Load Testing Integration

Monitor during load tests:

```python
# Monitor load test performance
async def monitor_load_test():
    baseline = await monitoring_service.get_baseline_metrics()
    
    # Run load test
    await run_load_test()
    
    # Compare metrics
    comparison = await monitoring_service.compare_with_baseline(baseline)
    
    if comparison['degradation'] > 0.2:  # 20% degradation
        alert("Performance degradation during load test")
```

## Debugging Performance Issues

### 1. Slow Request Investigation

When a request is slow:

```python
# Check request logs
curl http://localhost:5050/api/debug/logs?search=request_id:abc123

# View request trace
curl http://localhost:5050/api/monitoring/trace/abc123

# Check concurrent requests
curl http://localhost:5050/api/monitoring/concurrent?time=2024-01-09T10:30:00
```

### 2. Memory Leak Detection

Monitor memory patterns:

```python
# Get memory usage over time
memory_data = monitoring_service.get_metric_history(
    'memory_usage_mb',
    window_hours=24
)

# Detect leak pattern
if is_increasing_trend(memory_data):
    # Analyze object counts
    object_counts = get_object_counts()
    # Find growing collections
    find_memory_leaks(object_counts)
```

### 3. Database Query Analysis

Monitor database performance:

```python
# Log slow queries
@monitor_slow_queries(threshold_ms=100)
async def get_room_events(room_id: str):
    return await db.query("SELECT * FROM events WHERE room_id = ?", room_id)
```

## Best Practices

### 1. Metric Naming

Use consistent naming conventions:

```
<category>.<subcategory>.<metric>

Examples:
- api.request.duration_ms
- game.turn.processing_time_ms
- websocket.message.queue_size
- system.memory.usage_mb
```

### 2. Tag Usage

Add meaningful tags for filtering:

```python
metrics_collector.record_metric(
    'api.request.duration_ms',
    duration,
    tags={
        'endpoint': '/api/rooms/{room_id}/play-history',
        'method': 'GET',
        'status_code': 200,
        'room_id': room_id
    }
)
```

### 3. Sampling Strategies

For high-volume metrics:

```python
# Sample 10% of requests
if random.random() < 0.1:
    metrics_collector.record_detailed_trace(request)
else:
    metrics_collector.record_basic_metric(request)
```

### 4. Performance Budget

Set performance budgets:

```python
PERFORMANCE_BUDGETS = {
    'api.response_time_p95': 200,  # ms
    'websocket.latency_p95': 50,   # ms
    'memory.usage': 512,            # MB
    'cpu.usage': 70,                # percent
}

# Check budgets in CI/CD
def check_performance_budgets():
    for metric, budget in PERFORMANCE_BUDGETS.items():
        current = monitoring_service.get_metric_value(metric)
        if current > budget:
            raise PerformanceBudgetExceeded(f"{metric}: {current} > {budget}")
```

## Integration Examples

### 1. FastAPI Integration

```python
from fastapi import FastAPI, Request
from backend.services.monitoring_service import monitor_endpoint

app = FastAPI()

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    # Skip health checks
    if request.url.path == "/health":
        return await call_next(request)
        
    return await monitor_endpoint(request, call_next)
```

### 2. WebSocket Monitoring

```python
class MonitoredWebSocket:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.message_count = 0
        self.connect_time = time.time()
        
    async def send_json(self, data: dict):
        start = time.time()
        await self.websocket.send_json(data)
        
        metrics_collector.record_metric(
            'websocket.send.duration_ms',
            (time.time() - start) * 1000,
            tags={'message_type': data.get('event')}
        )
        
        self.message_count += 1
```

### 3. Background Task Monitoring

```python
from backend.services.monitoring_service import monitor_task

@monitor_task('cleanup.old_events')
async def cleanup_old_events():
    """Cleanup task with automatic monitoring"""
    deleted = await event_store.cleanup_old_events(hours=24)
    
    metrics_collector.set_gauge('events.deleted', deleted)
    return deleted
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Check for memory leaks in long-running connections
   - Review circular reference in event handlers
   - Monitor object allocation patterns

2. **Slow Response Times**
   - Check database query performance
   - Review synchronous operations in async handlers
   - Look for N+1 query problems

3. **WebSocket Latency**
   - Monitor message queue sizes
   - Check for broadcast storms
   - Review heartbeat frequency

### Debug Commands

```bash
# View current metrics
curl http://localhost:5050/api/monitoring/current

# Check specific metric history
curl http://localhost:5050/api/monitoring/metrics/api.request.duration_ms?window=1h

# Export metrics for analysis
curl http://localhost:5050/api/monitoring/export?format=csv > metrics.csv

# Real-time metric stream
wscat -c ws://localhost:5050/api/monitoring/stream
```

## Performance Optimization Guide

### 1. Code-Level Optimizations

```python
# Use async operations
async def get_room_state(room_id: str):
    # Parallel queries
    state, events, players = await asyncio.gather(
        get_state(room_id),
        get_events(room_id),
        get_players(room_id)
    )
    
# Cache expensive operations
@cache(ttl=60)
async def get_player_stats(player_id: str):
    return await calculate_stats(player_id)
```

### 2. Database Optimizations

```python
# Use connection pooling
database_pool = await asyncpg.create_pool(
    min_size=10,
    max_size=20,
    command_timeout=60
)

# Batch operations
async def store_events(events: List[Event]):
    async with database_pool.acquire() as conn:
        await conn.executemany(
            "INSERT INTO events VALUES ($1, $2, $3)",
            [(e.id, e.type, e.data) for e in events]
        )
```

### 3. WebSocket Optimizations

```python
# Message batching
class MessageBatcher:
    def __init__(self, flush_interval=0.1):
        self.pending = []
        self.flush_interval = flush_interval
        
    async def add_message(self, message):
        self.pending.append(message)
        if len(self.pending) == 1:
            asyncio.create_task(self._flush_after_interval())
            
    async def _flush_after_interval(self):
        await asyncio.sleep(self.flush_interval)
        await self.flush()
        
    async def flush(self):
        if self.pending:
            await websocket.send_json({
                'type': 'batch',
                'messages': self.pending
            })
            self.pending = []
```

## Capacity Planning

### Metrics for Scaling

Monitor these metrics for capacity planning:

1. **Request Rate**: Requests per second
2. **Concurrent Users**: Active WebSocket connections
3. **Response Time**: 95th percentile latency
4. **Resource Usage**: CPU, Memory, Network
5. **Queue Depths**: Message queues, task queues

### Scaling Triggers

```yaml
scaling_rules:
  scale_up:
    - metric: cpu_usage
      threshold: 70
      duration: 5m
      
    - metric: response_time_p95
      threshold: 500
      duration: 3m
      
    - metric: concurrent_connections
      threshold: 1000
      duration: 1m
      
  scale_down:
    - metric: cpu_usage
      threshold: 30
      duration: 10m
```

## Conclusion

Effective performance monitoring requires:
1. Comprehensive metric collection
2. Meaningful alerting thresholds
3. Regular analysis and optimization
4. Proactive capacity planning
5. Continuous improvement

Use the tools and patterns in this guide to maintain optimal performance for your Liap Tui game platform.