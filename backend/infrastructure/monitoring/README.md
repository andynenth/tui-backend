# Enterprise Monitoring Infrastructure

## Overview

The Enterprise Monitoring infrastructure provides comprehensive observability for the Liap Tui game system. It includes metrics collection, distributed tracing, event streaming, correlation tracking, and real-time visualization.

## Components

### 1. **Game Metrics Collection** (`game_metrics.py`)
Tracks game-specific metrics including:
- Games started/completed/abandoned per hour
- Average game duration
- Player win rates (human vs bot)
- Phase durations
- WebSocket connection metrics
- Business intelligence metrics

### 2. **System Metrics Collection** (`system_metrics.py`)
Monitors system resources:
- Memory usage (RSS, VMS)
- CPU utilization
- Garbage collection statistics
- Thread and coroutine counts
- File descriptor usage
- Memory growth rate

### 3. **Distributed Tracing** (`tracing.py`)
OpenTelemetry-based tracing for:
- State transitions
- Action processing
- Phase execution
- Cross-service correlation
- Performance measurement

### 4. **Correlation ID Propagation** (`correlation.py`)
Request tracking through:
- Automatic ID generation
- Context propagation
- Metadata tracking
- Cross-layer correlation
- Correlated logging

### 5. **Event Stream** (`event_stream.py`)
Real-time event streaming for:
- State machine events
- Game lifecycle events
- Player actions
- System events
- Debug event stream

### 6. **State Visualization** (`visualization.py`)
Real-time visualization data:
- State diagram with metrics
- Room status overview
- Performance metrics
- Error heatmaps
- Flow diagrams

### 7. **Prometheus Integration** (`prometheus_endpoint.py`)
Metrics export in Prometheus format:
- `/metrics` endpoint
- All metrics aggregated
- Prometheus-compatible format
- Ready for Grafana

### 8. **Grafana Dashboards** (`grafana_dashboards.py`)
Pre-configured dashboards:
- Game Overview Dashboard
- Performance Monitoring Dashboard
- State Machine Monitor Dashboard
- Alert rules

### 9. **Enterprise Monitor** (`enterprise_monitor.py`)
Unified monitoring interface:
- Integrates all components
- Simplified API
- Background tasks
- Lifecycle management

## Usage

### Basic Setup

```python
from backend.infrastructure.monitoring import (
    configure_enterprise_monitoring,
    get_enterprise_monitor
)

# Configure monitoring
monitor = configure_enterprise_monitoring(
    service_name="liap-tui",
    enable_tracing=True,
    enable_console_export=False
)

# Start monitoring
await monitor.start()
```

### Monitoring State Transitions

```python
async with monitor.monitor_state_transition(
    game_id="game123",
    from_state="PREPARATION",
    to_state="DECLARATION"
):
    # Perform state transition
    await transition_logic()
```

### Monitoring Actions

```python
async with monitor.monitor_action_processing(
    game_id="game123",
    action_type="play_piece",
    player_id="player1"
):
    # Process action
    await process_action()
```

### Recording Game Events

```python
# Game start
await monitor.record_game_start(
    game_id="game123",
    room_id="room456",
    player_count=4,
    bot_count=0
)

# Game end
await monitor.record_game_end(
    game_id="game123",
    winner_id="player1",
    final_scores={"player1": 100, "player2": 80}
)

# Phase duration
await monitor.record_phase_duration(
    game_id="game123",
    phase="DECLARATION",
    duration_seconds=45.2
)
```

### WebSocket Monitoring

```python
# Connection events
await monitor.record_websocket_event(
    connection_id="conn123",
    event_type="connect",
    room_id="room456"
)

# Broadcast metrics
await monitor.record_websocket_event(
    connection_id="conn123",
    event_type="broadcast",
    room_id="room456",
    data={
        "recipient_count": 4,
        "broadcast_time_ms": 12.5,
        "success": True
    }
)
```

### Correlation Tracking

```python
from backend.infrastructure.monitoring import (
    set_correlation_id,
    get_correlation_id,
    with_correlation
)

# Set correlation ID
correlation_id = set_correlation_id()

# Use decorator
@with_correlation(generate_new=True)
async def handle_request():
    # Correlation ID available throughout
    corr_id = get_correlation_id()
    logger.info(f"Processing request {corr_id}")
```

### Event Streaming

```python
# Subscribe to events
from backend.infrastructure.monitoring import EventFilter, EventType

filter = EventFilter(
    event_types={EventType.GAME_STARTED, EventType.GAME_ENDED},
    room_ids={"room456"}
)

subscriber = await monitor.subscribe_to_events(
    subscriber_id="dashboard",
    event_filter=filter
)

# Get events
while True:
    event = await subscriber.get_event(timeout=5.0)
    if event:
        print(f"Event: {event.event_type.value}")
```

### Visualization Data

```python
# Get all visualizations
viz_data = monitor.get_visualization_data()

# Get specific visualization
state_diagram = monitor.get_visualization_data("state_diagram")
room_status = monitor.get_visualization_data("room_status")
```

## Prometheus Metrics

### Endpoint Setup

```python
from fastapi import FastAPI
from backend.infrastructure.monitoring import prometheus_router

app = FastAPI()
app.include_router(prometheus_router)

# Metrics available at /metrics
```

### Available Metrics

#### Game Metrics
- `liap_tui_games_active` - Currently active games (gauge)
- `liap_tui_games_completed_total` - Total completed games (counter)
- `liap_tui_games_per_hour` - Average games per hour (gauge)
- `liap_tui_game_duration_minutes` - Average game duration (gauge)
- `liap_tui_player_win_rate{type="bot|human"}` - Win rates (gauge)
- `liap_tui_phase_duration_seconds` - Phase durations (histogram)

#### System Metrics
- `liap_tui_memory_usage_mb{type="rss|vms"}` - Memory usage (gauge)
- `liap_tui_memory_growth_rate` - Memory growth MB/hour (gauge)
- `liap_tui_cpu_usage_percent` - CPU usage (gauge)
- `liap_tui_gc_collections_total{generation="0|1|2"}` - GC collections (counter)
- `liap_tui_threads_active` - Active threads (gauge)

#### State Machine Metrics
- `liap_tui_state_active_games{state="..."}` - Games per state (gauge)
- `liap_tui_state_transitions_total{from="...",to="..."}` - Transitions (counter)
- `liap_tui_state_errors{state="..."}` - Errors by state (counter)

#### WebSocket Metrics
- `liap_tui_websocket_connections_active` - Active connections (gauge)
- `liap_tui_websocket_connections.opened` - Connections opened (counter)
- `liap_tui_websocket_connections.closed` - Connections closed (counter)
- `liap_tui_websocket_broadcast_time` - Broadcast time (histogram)

## Grafana Integration

### Import Dashboards

```python
from backend.infrastructure.monitoring import export_all_dashboards

# Export dashboards
dashboards = export_all_dashboards()

# Save to file for import
save_dashboards_to_file("grafana_dashboards.json")
```

### Dashboard Types

1. **Game Overview Dashboard**
   - Active games and completion rates
   - Games timeline
   - Player win rates
   - Room health status

2. **Performance Dashboard**
   - Memory and CPU usage
   - Garbage collection metrics
   - Action processing times
   - State transition latency

3. **State Machine Dashboard**
   - State transition flow
   - Phase duration distribution
   - Error rates by state
   - Current state distribution

## Configuration

### Environment Variables

```bash
# Monitoring configuration
MONITORING_SERVICE_NAME=liap-tui
MONITORING_ENABLE_TRACING=true
MONITORING_ENABLE_CONSOLE_EXPORT=false

# Event stream configuration
EVENT_STREAM_HISTORY_SIZE=10000
EVENT_STREAM_MAX_SUBSCRIBERS=100

# Metrics retention
METRICS_RETENTION_HOURS=24
METRICS_COLLECTION_INTERVAL=30
```

### Programmatic Configuration

```python
from backend.infrastructure.monitoring import (
    MetricConfig,
    configure_metrics
)

# Custom metric configuration
config = MetricConfig(
    prefix="custom_app",
    default_tags=[MetricTag("env", "production")],
    export_interval=timedelta(seconds=30),
    retention_period=timedelta(hours=48)
)

configure_metrics("custom_app", config)
```

## Performance Considerations

### Memory Usage
- Event history limited to 10,000 events
- Time-series data automatically cleaned up
- Configurable retention periods

### CPU Usage
- Background tasks run at intervals
- Async processing for non-blocking operation
- Efficient data structures

### Network
- Prometheus endpoint caches metrics
- Event stream uses queues for buffering
- WebSocket metrics batched

## Troubleshooting

### High Memory Usage
```python
# Force garbage collection
monitor.system_metrics.force_gc_collection()

# Check memory summary
summary = monitor.system_metrics.get_memory_summary()
print(f"Current RSS: {summary['current_rss_mb']}MB")
print(f"Growth rate: {summary['growth_rate_mb_per_hour']}MB/hour")
```

### Missing Metrics
```python
# Check monitoring status
status = monitor.get_monitoring_status()
print(f"Collectors active: {status['collectors']}")
print(f"Event stream stats: {status['event_stream']}")
```

### Event Stream Issues
```python
# Check subscriber status
stats = monitor.event_stream.get_statistics()
print(f"Total events: {stats['total_events']}")
print(f"Subscribers: {stats['subscriber_count']}")

# Clean up inactive subscribers
await monitor.event_stream.cleanup_inactive_subscribers()
```

## Best Practices

1. **Always use context managers** for state transitions and action processing
2. **Set correlation IDs** at request boundaries
3. **Monitor memory growth** and set up alerts
4. **Use event filters** to reduce subscriber load
5. **Export Grafana dashboards** for consistent monitoring
6. **Configure retention periods** based on needs
7. **Use structured logging** with correlation IDs
8. **Test monitoring** in development environments

## Future Enhancements

1. **Distributed Tracing**
   - Jaeger integration
   - Zipkin support
   - W3C trace context

2. **Advanced Analytics**
   - Machine learning insights
   - Anomaly detection
   - Predictive analytics

3. **External Storage**
   - Time-series databases
   - S3 for long-term storage
   - ClickHouse integration

4. **Enhanced Visualization**
   - Real-time dashboards
   - 3D state diagrams
   - Player behavior flows