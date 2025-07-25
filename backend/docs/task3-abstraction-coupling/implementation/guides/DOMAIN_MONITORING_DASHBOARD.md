# Domain Layer Monitoring Dashboard Specification

**Purpose**: Define metrics and visualizations for monitoring the domain layer in production.

**Target Tools**: Grafana, Prometheus, CloudWatch, or similar

## Dashboard Overview

The domain monitoring dashboard provides real-time visibility into:
- Domain adapter usage and performance
- Event processing metrics
- Error rates and types
- System health indicators

## Key Metrics

### 1. Domain Adapter Metrics

#### Usage Metrics
```python
# Metric: domain_adapter_requests_total
# Type: Counter
# Labels: event_type, status (success/error/fallback)
# Description: Total requests handled by domain adapters

domain_adapter_requests_total{event_type="start_game", status="success"} 1234
domain_adapter_requests_total{event_type="declare", status="error"} 5
domain_adapter_requests_total{event_type="play", status="fallback"} 10
```

#### Performance Metrics
```python
# Metric: domain_adapter_duration_seconds
# Type: Histogram
# Labels: event_type
# Description: Time taken to process requests

domain_adapter_duration_seconds_bucket{event_type="play", le="0.01"} 950
domain_adapter_duration_seconds_bucket{event_type="play", le="0.05"} 990
domain_adapter_duration_seconds_bucket{event_type="play", le="0.1"} 999
```

#### Enable/Disable Status
```python
# Metric: domain_adapter_enabled
# Type: Gauge
# Values: 0 (disabled), 1 (enabled)
# Description: Current enable/disable status

domain_adapter_enabled 1
```

### 2. Event Bus Metrics

#### Event Publishing
```python
# Metric: domain_events_published_total
# Type: Counter
# Labels: event_type
# Description: Total events published to event bus

domain_events_published_total{event_type="GameStarted"} 456
domain_events_published_total{event_type="PlayerDeclaredPiles"} 1823
domain_events_published_total{event_type="TurnCompleted"} 8934
```

#### Event Processing
```python
# Metric: domain_events_processed_total
# Type: Counter
# Labels: event_type, handler
# Description: Events processed by handlers

domain_events_processed_total{event_type="GameStarted", handler="WebSocketBroadcast"} 456
domain_events_processed_total{event_type="GameStarted", handler="Analytics"} 456
```

#### Event Latency
```python
# Metric: domain_event_processing_duration_seconds
# Type: Histogram
# Labels: event_type, handler
# Description: Time from event creation to handler completion

domain_event_processing_duration_seconds{event_type="TurnCompleted", handler="WebSocketBroadcast", quantile="0.95"} 0.002
```

### 3. Repository Metrics

#### Operation Counts
```python
# Metric: domain_repository_operations_total
# Type: Counter
# Labels: repository, operation, status
# Description: Repository operation counts

domain_repository_operations_total{repository="room", operation="save", status="success"} 789
domain_repository_operations_total{repository="room", operation="find_by_id", status="success"} 3456
domain_repository_operations_total{repository="room", operation="find_by_id", status="not_found"} 23
```

#### Operation Duration
```python
# Metric: domain_repository_duration_seconds
# Type: Histogram
# Labels: repository, operation
# Description: Repository operation duration

domain_repository_duration_seconds{repository="room", operation="save", quantile="0.99"} 0.001
```

### 4. Domain Service Metrics

#### Service Calls
```python
# Metric: domain_service_calls_total
# Type: Counter
# Labels: service, method
# Description: Domain service method calls

domain_service_calls_total{service="GameRules", method="identify_play_type"} 8934
domain_service_calls_total{service="ScoringService", method="calculate_round_scores"} 456
domain_service_calls_total{service="TurnResolution", method="resolve_turn"} 8934
```

#### Validation Failures
```python
# Metric: domain_validation_failures_total
# Type: Counter
# Labels: service, validation_type
# Description: Domain validation failures

domain_validation_failures_total{service="GameRules", validation_type="invalid_play"} 67
domain_validation_failures_total{service="Declaration", validation_type="sum_equals_eight"} 12
```

## Dashboard Panels

### 1. Overview Panel
```yaml
title: "Domain Layer Overview"
panels:
  - type: stat
    title: "Domain Adapter Status"
    query: domain_adapter_enabled
    thresholds:
      - value: 0
        color: red
        text: "DISABLED"
      - value: 1
        color: green
        text: "ENABLED"
  
  - type: stat
    title: "Traffic %"
    query: |
      sum(rate(domain_adapter_requests_total[5m])) / 
      sum(rate(websocket_requests_total[5m])) * 100
    unit: percent
  
  - type: gauge
    title: "Success Rate"
    query: |
      sum(rate(domain_adapter_requests_total{status="success"}[5m])) /
      sum(rate(domain_adapter_requests_total[5m])) * 100
    thresholds:
      - value: 95
        color: red
      - value: 99
        color: yellow
      - value: 99.9
        color: green
```

### 2. Performance Panel
```yaml
title: "Domain Performance"
panels:
  - type: graph
    title: "Request Latency (p95)"
    queries:
      - label: "Start Game"
        query: histogram_quantile(0.95, domain_adapter_duration_seconds{event_type="start_game"})
      - label: "Declare"
        query: histogram_quantile(0.95, domain_adapter_duration_seconds{event_type="declare"})
      - label: "Play"
        query: histogram_quantile(0.95, domain_adapter_duration_seconds{event_type="play"})
    
  - type: heatmap
    title: "Latency Distribution"
    query: domain_adapter_duration_seconds
```

### 3. Event Processing Panel
```yaml
title: "Event Processing"
panels:
  - type: graph
    title: "Events Published/sec"
    query: sum(rate(domain_events_published_total[1m])) by (event_type)
    
  - type: graph
    title: "Event Processing Lag"
    query: |
      histogram_quantile(0.99, 
        domain_event_processing_duration_seconds
      )
    
  - type: table
    title: "Top Event Types"
    query: |
      topk(10, 
        sum(increase(domain_events_published_total[1h])) by (event_type)
      )
```

### 4. Error Analysis Panel
```yaml
title: "Error Analysis"
panels:
  - type: graph
    title: "Error Rate"
    queries:
      - label: "Domain Errors"
        query: sum(rate(domain_adapter_requests_total{status="error"}[5m]))
      - label: "Fallbacks"
        query: sum(rate(domain_adapter_requests_total{status="fallback"}[5m]))
    
  - type: table
    title: "Recent Errors"
    query: domain_error_logs{level="error"}
    columns:
      - timestamp
      - event_type
      - error_message
      - stack_trace
```

### 5. Repository Operations Panel
```yaml
title: "Repository Operations"
panels:
  - type: graph
    title: "Repository Operations/sec"
    query: sum(rate(domain_repository_operations_total[1m])) by (operation)
    
  - type: stat
    title: "Cache Hit Rate"
    query: |
      sum(rate(domain_repository_cache_hits[5m])) /
      sum(rate(domain_repository_operations_total{operation="find_by_id"}[5m])) * 100
    unit: percent
```

### 6. Comparison Panel
```yaml
title: "Domain vs Legacy Comparison"
panels:
  - type: graph
    title: "Response Time Comparison"
    queries:
      - label: "Domain p95"
        query: histogram_quantile(0.95, domain_adapter_duration_seconds)
      - label: "Legacy p95"
        query: histogram_quantile(0.95, legacy_handler_duration_seconds)
    
  - type: graph
    title: "Error Rate Comparison"
    queries:
      - label: "Domain Errors"
        query: sum(rate(domain_adapter_requests_total{status="error"}[5m]))
      - label: "Legacy Errors"
        query: sum(rate(legacy_handler_errors_total[5m]))
```

## Alert Rules

```yaml
groups:
  - name: domain_layer_alerts
    rules:
      - alert: DomainAdapterHighErrorRate
        expr: |
          sum(rate(domain_adapter_requests_total{status="error"}[5m])) /
          sum(rate(domain_adapter_requests_total[5m])) > 0.01
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Domain adapter error rate above 1%"
          
      - alert: DomainAdapterHighLatency
        expr: |
          histogram_quantile(0.95, domain_adapter_duration_seconds) > 0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Domain adapter p95 latency above 200ms"
          
      - alert: EventProcessingLag
        expr: |
          histogram_quantile(0.99, domain_event_processing_duration_seconds) > 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Event processing lag above 1 second"
```

## Implementation Example (Prometheus)

```python
# In domain_adapter_wrapper.py
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
domain_requests = Counter(
    'domain_adapter_requests_total',
    'Total domain adapter requests',
    ['event_type', 'status']
)

domain_duration = Histogram(
    'domain_adapter_duration_seconds',
    'Domain adapter request duration',
    ['event_type']
)

domain_enabled = Gauge(
    'domain_adapter_enabled',
    'Domain adapter enable status'
)

# Use in code
async def try_handle_with_domain(self, websocket, message, room_id):
    event_type = message.get('event')
    
    with domain_duration.labels(event_type=event_type).time():
        try:
            response = await self.integration.handle_message(...)
            domain_requests.labels(
                event_type=event_type,
                status='success' if response else 'fallback'
            ).inc()
            return response
        except Exception as e:
            domain_requests.labels(
                event_type=event_type,
                status='error'
            ).inc()
            raise
```

## Dashboard Access Control

```yaml
# Grafana folder permissions
folders:
  - name: "Domain Layer Monitoring"
    permissions:
      - team: "Backend Engineers"
        permission: "Edit"
      - team: "SRE"
        permission: "Admin"
      - team: "Support"
        permission: "View"
```

## Mobile/Responsive View

Create a simplified mobile dashboard with:
- Domain adapter status (enabled/disabled)
- Current error rate
- p95 latency
- Events per second
- Quick links to detailed views

## Export and Sharing

- **PDF Reports**: Weekly performance summaries
- **Slack Integration**: Alert notifications
- **API Access**: Metrics endpoint for custom integrations
- **Public Dashboard**: Read-only view for stakeholders

This monitoring dashboard provides comprehensive visibility into the domain layer's health and performance, enabling quick problem detection and resolution.