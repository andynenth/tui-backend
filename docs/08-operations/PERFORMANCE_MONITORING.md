# Performance Monitoring Guide

This document has been consolidated into a comprehensive reference.

## New Location

Please see: [Comprehensive Monitoring & Observability Guide](./MONITORING_COMPREHENSIVE.md)

Specifically, performance monitoring is covered in:
- **Section**: "Performance Monitoring"
- **Section**: "Performance Thresholds"
- **Section**: "Play History Performance"

## Legacy Reference

This file originally contained performance-specific monitoring guidance. All content has been preserved and enhanced in the comprehensive guide.

## Architecture

```
┌───────────────┐     ┌─────────────────┐     ┌──────────────┐
│ API Requests  │────►│ Metrics Layer   │────►│ Time Series  │
│               │     │ (Middleware)    │     │ Storage      │
└───────────────┘     └────────┬────────┘     └──────────────┘
                              │
                    ┌─────────▼──────────┐
                    │ Metrics Collector  │
                    ├────────────────────┤
                    │ • Response times   │
                    │ • Error rates      │
                    │ • Cache metrics    │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐     ┌──────────────┐
                    │ Performance Health │────►│ Health API   │
                    │ Analysis           │     │ /health/*    │
                    └────────────────────┘     └──────────────┘
```

## Key Metrics

### 1. Response Time Metrics

#### Percentile Tracking
- **P50 (Median)**: Typical response time
- **P95**: 95% of requests faster than this
- **P99**: 99% of requests faster than this

#### Implementation
```python
response_times = defaultdict(lambda: deque(maxlen=1000))

# Calculate percentiles
def get_percentiles(times):
    sorted_times = sorted(times)
    return {
        "p50": sorted_times[len(times) // 2],
        "p95": sorted_times[int(len(times) * 0.95)],
        "p99": sorted_times[int(len(times) * 0.99)]
    }
```

### 2. Error Rate Monitoring

#### Error Categories
- **4xx**: Client errors (bad requests)
- **5xx**: Server errors (internal issues)

#### Thresholds
```python
if error_rate > 0.05:  # > 5% errors
    health_status = "RED"
elif error_rate > 0.02:  # > 2% errors
    health_status = "YELLOW"
```

### 3. Cache Performance

#### Metrics Tracked
- **Hit Rate**: Percentage of cache hits
- **Miss Rate**: Percentage of cache misses
- **Total Operations**: Hits + misses

#### Optimal Thresholds
- Hit rate > 70%: Good
- Hit rate 50-70%: Acceptable
- Hit rate < 50%: Needs optimization

## Performance Health Endpoint

### GET `/api/health/performance`

Provides real-time performance health assessment.

#### Response Structure
```json
{
    "status": "GREEN",  // GREEN, YELLOW, or RED
    "issues": [],       // List of performance issues
    "metrics_summary": {
        "total_requests": 12345,
        "error_rate": "1.23%",
        "slow_requests": 45
    }
}
```

#### Health Status Logic

```python
# GREEN: All metrics within acceptable ranges
# YELLOW: Some metrics approaching thresholds
# RED: Critical performance issues detected

# Error rate check
if error_rate > 0.05:  # > 5%
    status = "RED"
elif error_rate > 0.02:  # > 2%
    status = "YELLOW"

# Response time check
if p95_response_time > 2000:  # > 2 seconds
    status = "RED"
elif p95_response_time > 1000:  # > 1 second
    status = "YELLOW"

# Cache performance check
if cache_hit_rate < 0.5:  # < 50%
    status = "YELLOW"
```

## Play History Specific Monitoring

### Specialized Metrics

```python
class PlayHistoryMetrics:
    def record_play_history_request(
        room_id: str,
        total_rounds: int,
        response_size: int,
        build_time_ms: float,
        format: str = "full"
    ):
        # Track rounds processed
        # Monitor response sizes
        # Track format usage
```

### Large Response Detection

```python
if response_size > 1_000_000:  # 1MB
    logger.warning(
        "Large play history response",
        extra={
            "room_id": room_id,
            "response_size_bytes": response_size,
            "total_rounds": total_rounds
        }
    )
```

### Metrics Available

- **Total rounds processed**: Cumulative game rounds
- **Average rounds per request**: Typical request size
- **Response size**: Track payload sizes
- **Format usage**: full vs compact format distribution

## Time Series Data

### Data Collection

```python
# Store second-by-second metrics
time_series_data = defaultdict(lambda: deque(maxlen=3600))  # 1 hour

# Record data point
time_series_data[endpoint].append({
    "timestamp": time.time(),
    "duration_ms": duration_ms,
    "status_code": status_code
})
```

### Querying Time Series

```python
# Get last 5 minutes of data
def get_time_series_data(endpoint: str, minutes: int = 5):
    cutoff_time = time.time() - (minutes * 60)
    return [d for d in data if d["timestamp"] > cutoff_time]
```

## Performance Optimization Strategies

### 1. Response Time Optimization

#### Identify Slow Endpoints
```python
# Find endpoints with p95 > 1 second
slow_endpoints = [
    endpoint for endpoint, stats in metrics["endpoints"].items()
    if stats["p95_response_time_ms"] > 1000
]
```

#### Common Causes
- Database query optimization needed
- Missing indexes
- N+1 query problems
- Large payload sizes

### 2. Cache Optimization

#### Improve Hit Rates
```python
# Monitor cache effectiveness
for cache_type, stats in metrics["cache"].items():
    if stats["hit_rate"] < 0.7:
        # Optimize cache strategy
        # - Increase TTL
        # - Better cache keys
        # - Preload common data
```

#### Cache Strategies
- **TTL Tuning**: Balance freshness vs performance
- **Key Design**: Include version in cache keys
- **Warming**: Preload frequently accessed data

### 3. Error Rate Reduction

#### Error Analysis
```python
# Group errors by type
error_patterns = defaultdict(int)
for endpoint, count in error_counts.items():
    error_type = categorize_error(endpoint)
    error_patterns[error_type] += count
```

#### Common Fixes
- Input validation
- Better error messages
- Retry logic for transient failures
- Circuit breakers for failing services

## Monitoring Dashboard

### Key Visualizations

1. **Response Time Graph**
   - Line chart showing P50, P95, P99 over time
   - Highlight threshold violations

2. **Error Rate Trend**
   - Percentage of failed requests
   - Breakdown by error type

3. **Cache Performance**
   - Hit rate percentage
   - Cache size and eviction rate

4. **Endpoint Heatmap**
   - Color-coded by response time
   - Size by request volume

### Example Dashboard Query

```python
# Get comprehensive metrics for dashboard
dashboard_data = {
    "response_times": {
        endpoint: {
            "p50": stats["p50_response_time_ms"],
            "p95": stats["p95_response_time_ms"],
            "volume": stats["request_count"]
        }
        for endpoint, stats in metrics["endpoints"].items()
    },
    "error_trend": get_time_series_data("errors", minutes=60),
    "cache_performance": metrics["cache"],
    "health_status": get_performance_health()
}
```

## Alert Configuration

### Performance Alerts

```python
# Slow response alert
if p95_response_time > 3000:  # 3 seconds
    alert = Alert(
        alert_type="slow_response",
        severity="critical",
        message=f"P95 response time {p95_response_time}ms exceeds threshold",
        context={"endpoint": endpoint, "threshold_ms": 3000}
    )
```

### Alert Escalation

1. **Warning**: Performance degradation detected
2. **Critical**: User-impacting performance issues
3. **Emergency**: System-wide performance failure

## Best Practices

### 1. Baseline Establishment

```python
# Track weekly performance baselines
baseline = {
    "monday": {"p95": 250, "error_rate": 0.01},
    "tuesday": {"p95": 280, "error_rate": 0.012},
    # ... other days
}

# Compare current to baseline
deviation = (current_p95 - baseline[day]["p95"]) / baseline[day]["p95"]
if deviation > 0.5:  # 50% slower than baseline
    trigger_investigation()
```

### 2. Capacity Planning

```python
# Track growth trends
def calculate_growth_rate(metrics_history):
    weekly_averages = calculate_weekly_averages(metrics_history)
    return linear_regression(weekly_averages)

# Predict when thresholds will be exceeded
growth_rate = calculate_growth_rate(last_90_days)
days_until_threshold = (threshold - current) / growth_rate
```

### 3. Performance Budgets

```yaml
performance_budgets:
  api_endpoints:
    p95_target: 500ms
    p99_target: 1000ms
  cache:
    min_hit_rate: 0.7
  errors:
    max_rate: 0.02
```

## Troubleshooting Performance Issues

### 1. Sudden Slowdown

```bash
# Check recent deployments
git log --oneline --since="2 hours ago"

# Check resource utilization
docker stats

# Review slow query logs
tail -f logs/slow_queries.log
```

### 2. Gradual Degradation

```python
# Analyze trend over time
trend = analyze_performance_trend(days=30)
if trend.slope > 0:
    # Performance getting worse
    investigate_causes()
```

### 3. Intermittent Issues

```python
# Look for patterns
spikes = detect_performance_spikes(time_series_data)
correlate_with_events(spikes, [
    "deployments",
    "traffic_surges",
    "database_maintenance",
    "cache_clears"
])
```

## Integration Examples

### 1. Grafana Integration

```yaml
datasource:
  - name: liap-tui-metrics
    type: prometheus
    url: http://localhost:8001/api/metrics

dashboard:
  - title: API Performance
    panels:
      - graph: Response Time Percentiles
      - stat: Current Error Rate
      - table: Slow Endpoints
```

### 2. Alertmanager Integration

```yaml
alerts:
  - name: HighErrorRate
    expr: error_rate > 0.05
    for: 5m
    annotations:
      summary: "High error rate detected"

  - name: SlowResponse
    expr: p95_response_time > 2000
    for: 10m
    annotations:
      summary: "API response time degraded"
```

## Future Enhancements

1. **Distributed Tracing**: Track requests across services
2. **Anomaly Detection**: ML-based performance anomaly detection
3. **Predictive Scaling**: Auto-scale before hitting limits
4. **SLO Tracking**: Service level objective monitoring
5. **Cost Attribution**: Performance cost analysis
