# Production Operations Guide

This guide provides comprehensive documentation for all API endpoints, monitoring procedures, and operational tasks for the Liap Tui application.

## Quick Reference

- **Base URL**: `http://localhost:5050`
- **REST API Prefix**: `/api`
- **WebSocket Prefix**: `/ws`
- **Total Endpoints**: 66 (63 REST + 3 WebSocket)

## Table of Contents

1. [Health Monitoring](#1-health-monitoring) - 4 endpoints
2. [System Statistics](#2-system-statistics) - 5 endpoints
3. [Player Activity Monitor](#3-player-activity-monitor) - 3 endpoints
4. [Debug Operations](#4-debug-operations) - 13 endpoints
5. [Event Store & Recovery](#5-event-store--recovery) - 6 endpoints
6. [Play History](#6-play-history) - 4 endpoints
7. [Performance Monitoring](#7-performance-monitoring) - 8 endpoints
8. [Telemetry & Analytics](#8-telemetry--analytics) - 5 endpoints
9. [Maintenance](#9-maintenance) - 3 endpoints
10. [Privacy & Compliance](#10-privacy--compliance) - 5 endpoints
11. [Rate Limiting](#11-rate-limiting) - 2 endpoints
12. [WebSocket Endpoints](#12-websocket-endpoints) - 3 endpoints
13. [Quick Troubleshooting](#13-quick-troubleshooting)

---

## 1. Health Monitoring

### 1.1 GET /api/health
- **Purpose**: Basic health check for load balancers
- **Parameters**: None
- **Response**: `{"status": "healthy", "timestamp": "2024-01-15T10:30:00Z"}`
- **Status**: 200 OK

### 1.2 GET /api/health/detailed
- **Purpose**: Comprehensive system health metrics
- **Parameters**: None
- **Response Fields**: 
  - `uptime`: Service uptime in seconds
  - `cpu_usage`: Current CPU percentage
  - `memory_usage`: Memory usage in MB
  - `active_connections`: Number of active WebSocket connections
  - `error_rate`: Recent error rate percentage
- **Status**: 200 OK

### 1.3 GET /api/health/metrics
- **Purpose**: Prometheus-compatible metrics
- **Parameters**: None
- **Response Format**: Prometheus text format
- **Example**:
  ```
  # HELP active_connections Number of active WebSocket connections
  # TYPE active_connections gauge
  active_connections 42
  ```
- **Status**: 200 OK

### 1.4 GET /api/health/performance
- **Purpose**: API performance health status
- **Parameters**: None
- **Response Fields**:
  - `status`: "GREEN" | "YELLOW" | "RED"
  - `issues`: Array of performance issues
  - `metrics_summary`: Object with total_requests, error_rate, slow_requests
- **Status**: 200 OK

---

## 2. System Statistics

### 2.1 GET /api/system/stats
- **Purpose**: Complete system overview
- **Parameters**: None
- **Response Fields**:
  - `server`: CPU, memory, uptime
  - `connections`: Active, total, by_type
  - `rooms`: Active, completed, average_duration
  - `performance`: Request_rate, error_rate, avg_latency
- **Status**: 200 OK

### 2.2 GET /api/recovery/status
- **Purpose**: Recovery system status
- **Parameters**: None
- **Response Fields**:
  - `auto_recovery_enabled`: Boolean
  - `recent_recoveries`: Array of recovery events
  - `failed_attempts`: Count of failures
  - `stability_score`: 0.0 to 1.0
- **Status**: 200 OK

### 2.3 POST /api/recovery/trigger/{procedure_name}
- **Purpose**: Manually trigger recovery procedure
- **Path Parameters**: 
  - `procedure_name`: "room_recovery" | "connection_reset" | "cache_clear"
- **Request Body**: Optional configuration object
- **Response**: `{"success": true, "procedure": "room_recovery", "timestamp": 1234567890}`
- **Status**: 200 OK | 400 Bad Request

### 2.4 GET /api/event-store/stats
- **Purpose**: Event store statistics
- **Parameters**: None
- **Response Fields**:
  - `total_events`: Total event count
  - `events_by_type`: Object mapping event types to counts
  - `storage_size_mb`: Current storage usage
  - `compression_ratio`: Compression efficiency
- **Status**: 200 OK

### 2.5 GET /api/rate-limit/stats
- **Purpose**: Rate limiting statistics
- **Parameters**: None
- **Response Fields**:
  - `http_rate_limits`: Object with total_requests, blocked_requests, unique_clients, block_rate
  - `websocket_rate_limits`: Object with total_connections, blocked_connections, active_connections
  - `rate_limiting_enabled`: Boolean
- **Status**: 200 OK

---

## 3. Player Activity Monitor

### 3.1 GET /api/debug/player-activity/{room_id}
- **Purpose**: Current player activity status
- **Path Parameters**: 
  - `room_id`: Room identifier
- **Query Parameters**: None
- **Response Fields**:
  - `players`: Array of player objects with:
    - `name`: Player identifier
    - `status`: "active" | "inactive" | "hanging"
    - `last_heartbeat`: Unix timestamp
    - `last_action`: Unix timestamp
    - `heartbeat_lag`: Seconds since last heartbeat
    - `connection_health`: "good" | "warning" | "critical"
- **Status**: 200 OK | 404 Not Found

### 3.2 GET /api/debug/hang-diagnostics
- **Purpose**: Recent hang diagnostic snapshots
- **Query Parameters**:
  - `limit`: Max results (default: 50)
  - `hang_type`: "no_heartbeat" | "waiting_for_action"
  - `player_id`: Filter by player name
- **Response**: Array of diagnostic snapshots
- **Status**: 200 OK

### 3.3 WebSocket /api/debug/ws/activity-monitor
- **Purpose**: Real-time activity monitoring
- **Connection**: `ws://localhost:5050/api/debug/ws/activity-monitor`
- **Incoming Events**: None required
- **Outgoing Events**:
  - `activity_update`: Periodic updates with active_players, inactive_players, hang counts

---

## 4. Debug Operations

### 4.1 GET /api/debug/room-stats
- **Purpose**: Detailed room statistics
- **Parameters**: None
- **Response Fields**:
  - `active_rooms`: Count and list
  - `player_distribution`: Players per room
  - `phase_distribution`: Games by phase
  - `bot_vs_human`: Ratio statistics
- **Status**: 200 OK

### 4.2 GET /api/debug/events/{room_id}
- **Purpose**: List room events
- **Path Parameters**: 
  - `room_id`: Room identifier
- **Query Parameters**:
  - `limit`: Max events
  - `event_type`: Filter by type
- **Response**: Array of events with sequence, type, timestamp, payload
- **Status**: 200 OK | 404 Not Found

### 4.3 GET /api/debug/replay/{room_id}
- **Purpose**: Replay and reconstruct game state
- **Path Parameters**: 
  - `room_id`: Room identifier
- **Response**: Reconstructed game state object
- **Status**: 200 OK | 404 Not Found

### 4.4 GET /api/debug/events/{room_id}/sequence/{seq}
- **Purpose**: Events since sequence number
- **Path Parameters**: 
  - `room_id`: Room identifier
  - `seq`: Sequence number (exclusive)
- **Query Parameters**:
  - `limit`: Max events
- **Response**: Array of events after sequence
- **Status**: 200 OK

### 4.5 GET /api/debug/export/{room_id}
- **Purpose**: Export complete room history
- **Path Parameters**: 
  - `room_id`: Room identifier
- **Response**: Complete history with timeline and analysis
- **Status**: 200 OK

### 4.6 GET /api/debug/stats
- **Purpose**: Overall debug statistics
- **Parameters**: None
- **Response**: Event store health and statistics
- **Status**: 200 OK

### 4.7 GET /api/debug/turns/{room_id}
- **Purpose**: Turn play history
- **Path Parameters**: 
  - `room_id`: Room identifier
- **Query Parameters**:
  - `turn_number`: Specific turn
  - `player_name`: Filter by player
- **Response**: Structured turn data with plays and winners
- **Status**: 200 OK

### 4.8 POST /api/debug/cleanup
- **Purpose**: Clean up old events
- **Query Parameters**:
  - `older_than_hours`: Age threshold (default: 24)
- **Response**: `{"deleted_events": 1234, "space_freed_mb": 56.7}`
- **Status**: 200 OK

### 4.9 GET /api/debug/validate/{room_id}
- **Purpose**: Validate event sequence integrity
- **Path Parameters**: 
  - `room_id`: Room identifier
- **Response**: Validation results with any gaps or issues
- **Status**: 200 OK

### 4.10 GET /api/debug/logs
- **Purpose**: Retrieve log entries
- **Query Parameters**:
  - `limit`: Max entries (default: 100)
  - `level`: "DEBUG" | "INFO" | "WARNING" | "ERROR"
  - `logger_filter`: Logger name pattern
  - `since_minutes`: Time window
  - `search`: Text search
- **Response**: Array of log entries
- **Status**: 200 OK

### 4.11 GET /api/debug/logs/stats
- **Purpose**: Log buffer statistics
- **Response**: Buffer size, entry counts by level
- **Status**: 200 OK

### 4.12 DELETE /api/debug/logs
- **Purpose**: Clear log buffer
- **Response**: `{"cleared": true, "entries_deleted": 1234}`
- **Status**: 200 OK

### 4.13 GET /api/debug/connection-timeline/{room_id}
- **Purpose**: Connection event timeline
- **Path Parameters**: 
  - `room_id`: Room identifier
- **Query Parameters**:
  - `player_name`: Filter by player
- **Response**: Chronological array of connection events
- **Status**: 200 OK

### 4.14 GET /api/debug/bot-control-analysis/{room_id}
- **Purpose**: Analyze bot control patterns
- **Path Parameters**: 
  - `room_id`: Room identifier
- **Response**: Bot takeover analysis with timings and patterns
- **Status**: 200 OK

---

## 5. Event Store & Recovery

### 5.1 GET /api/rooms/{room_id}/events
- **Purpose**: Get all room events
- **Path Parameters**: 
  - `room_id`: Room identifier
- **Response**: Same as /api/debug/events/{room_id}
- **Status**: 200 OK

### 5.2 GET /api/rooms/{room_id}/events/{since_sequence}
- **Purpose**: Get events since sequence
- **Path Parameters**: 
  - `room_id`: Room identifier
  - `since_sequence`: Sequence number (exclusive)
- **Response**: Array of events after sequence
- **Status**: 200 OK

### 5.3 GET /api/rooms/{room_id}/state
- **Purpose**: Reconstructed game state
- **Path Parameters**: 
  - `room_id`: Room identifier
- **Response**: Current game state from events
- **Status**: 200 OK

### 5.4 POST /api/event-store/cleanup
- **Purpose**: Clean up old events
- **Request Body**: `{"older_than_hours": 168}`
- **Response**: `{"success": true, "deleted_count": 1234}`
- **Status**: 200 OK

### 5.5 POST /api/recovery/recreate
- **Purpose**: Recreate room from events
- **Request Body**: `{"room_id": "ROOM_ABC"}`
- **Response**: `{"success": true, "room_id": "ROOM_ABC", "state": "restored"}`
- **Status**: 200 OK | 404 Not Found

---

## 6. Play History

### 6.1 GET /api/rooms/{room_id}/play-history
- **Purpose**: Complete play history from SQLite
- **Path Parameters**: 
  - `room_id`: Room identifier
- **Query Parameters**:
  - `format`: "full" | "compact" (default: "full")
  - `include_hands`: Boolean (default: true)
  - `include_ai_analysis`: Boolean (default: true)
  - `rounds`: Comma-separated round numbers
- **Response**: Complete game history with rounds, plays, scores
- **Cache**: 5-minute TTL
- **Status**: 200 OK | 404 Not Found

### 6.2 GET /api/rooms/{room_id}/play-history/rounds
- **Purpose**: Get specific round range
- **Path Parameters**: 
  - `room_id`: Room identifier
- **Query Parameters**:
  - `from`: Starting round (inclusive)
  - `to`: Ending round (inclusive)
- **Response**: Array of round data
- **Status**: 200 OK

### 6.3 GET /api/rooms/{room_id}/play-history/round/{round_number}
- **Purpose**: Get specific round details
- **Path Parameters**: 
  - `room_id`: Room identifier
  - `round_number`: Round to retrieve
- **Response**: Single round data
- **Status**: 200 OK | 404 Not Found

### 6.4 GET /api/rooms/{room_id}/play-history/current
- **Purpose**: Get current round (NOT IMPLEMENTED)
- **Status**: 501 Not Implemented

---

## 7. Performance Monitoring

### 7.1 GET /api/metrics
- **Purpose**: Overall performance metrics
- **Response Fields**:
  - `overall`: Total requests, errors, slow requests, average response time
  - `endpoints`: Per-endpoint metrics with percentiles
  - `cache`: Cache hit rates by cache type
- **Status**: 200 OK

### 7.2 GET /api/metrics/time-series
- **Purpose**: Time series performance data
- **Query Parameters**:
  - `endpoint`: Specific endpoint path
  - `minutes`: Time window (default: 10)
- **Response**: Arrays of timestamps and values
- **Status**: 200 OK

### 7.3 GET /api/metrics/{endpoint_path}
- **Purpose**: Metrics for specific endpoint
- **Path Parameters**: 
  - `endpoint_path`: URL-encoded endpoint path
- **Response**: Endpoint-specific metrics
- **Status**: 200 OK

### 7.4 GET /api/metrics/play-history
- **Purpose**: Play History API metrics
- **Response**: Specialized metrics for play history performance
- **Status**: 200 OK

### 7.5 GET /api/metrics/rate_limits
- **Purpose**: Detailed rate limit metrics
- **Response**: Per-endpoint rate limiting statistics
- **Status**: 200 OK

### 7.6 POST /api/metrics/reset
- **Purpose**: Reset performance metrics
- **Request Body**: Optional `{"endpoints": ["/api/specific"]}`
- **Response**: `{"success": true, "reset_count": 45}`
- **Status**: 200 OK

### 7.7 GET /api/alerts
- **Purpose**: Recent performance alerts
- **Query Parameters**:
  - `minutes`: Time window (default: 10)
  - `severity`: "info" | "warning" | "critical"
- **Response**: Array of alert objects
- **Status**: 200 OK

### 7.8 GET /api/alerts/summary
- **Purpose**: Alert statistics
- **Response**: Counts by severity and type
- **Status**: 200 OK

### 7.9 POST /api/alerts/test
- **Purpose**: Test alert system
- **Request Body**: `{"type": "slow_query", "severity": "warning"}`
- **Response**: `{"success": true, "alert_id": "test_123"}`
- **Status**: 200 OK

---

## 8. Telemetry & Analytics

### 8.1 POST /api/telemetry
- **Purpose**: Submit client telemetry
- **Request Body**:
  ```json
  {
    "sessionId": "abc123",
    "events": [{
      "event": "bundle_load_success",
      "timestamp": 1234567890,
      "elapsed": 1250,
      "userAgent": "Mozilla/5.0..."
    }]
  }
  ```
- **Response**: `{"success": true, "events_processed": 1}`
- **Status**: 200 OK

### 8.2 GET /api/analytics/bundle-load-stats
- **Purpose**: Bundle loading performance
- **Query Parameters**:
  - `hours`: 1-168 (default: 24)
  - `group_by`: "device" | "connection"
- **Response**: Statistics with success rates and load times
- **Status**: 200 OK

### 8.3 GET /api/analytics/client-errors
- **Purpose**: Client-side error analysis
- **Query Parameters**:
  - `hours`: Time window (default: 24)
  - `min_occurrences`: Minimum count (default: 1)
- **Response**: Grouped errors with frequencies
- **Status**: 200 OK

### 8.4 GET /api/analytics/device-breakdown
- **Purpose**: Device and browser statistics
- **Query Parameters**:
  - `hours`: Time window (default: 24)
- **Response**: Device, browser, and connection type counts
- **Status**: 200 OK

### 8.5 GET /api/analytics/performance-trends
- **Purpose**: Performance over time
- **Query Parameters**:
  - `hours`: Time window (default: 24)
  - `interval`: "5m" | "15m" | "1h" | "1d"
- **Response**: Time series data points
- **Status**: 200 OK

---

## 9. Maintenance

### 9.1 GET /api/maintenance/status
- **Purpose**: Maintenance system status
- **Response Fields**:
  - `database`: Size and retention info
  - `archives`: Archive count and size
  - `last_cleanup`: Timestamp
  - `next_cleanup`: Scheduled time
  - `scheduler_running`: Boolean
- **Status**: 200 OK

### 9.2 GET /api/maintenance/config
- **Purpose**: Maintenance configuration
- **Response**: Current configuration values
- **Status**: 200 OK

### 9.3 POST /api/maintenance/trigger-cleanup
- **Purpose**: Manual cleanup trigger
- **Response**: `{"success": true, "cleaned_items": 1234}`
- **Status**: 200 OK

---

## 10. Privacy & Compliance

### 10.1 GET /api/privacy/report
- **Purpose**: Privacy compliance report
- **Response**: Data retention policies and compliance status
- **Status**: 200 OK

### 10.2 GET /api/privacy/export/{session_id}
- **Purpose**: Export user data (GDPR)
- **Path Parameters**: 
  - `session_id`: Session identifier
- **Response**: All data for session
- **Status**: 200 OK | 404 Not Found

### 10.3 DELETE /api/privacy/delete/{session_id}
- **Purpose**: Delete user data
- **Path Parameters**: 
  - `session_id`: Session identifier
- **Response**: `{"success": true, "deleted_events": 123}`
- **Status**: 200 OK | 404 Not Found

### 10.4 POST /api/privacy/cleanup
- **Purpose**: Bulk privacy cleanup
- **Request Body**: `{"older_than_days": 90}`
- **Response**: `{"success": true, "sessions_cleaned": 45}`
- **Status**: 200 OK

### 10.5 GET /api/privacy/data-summary
- **Purpose**: Data retention summary
- **Response**: Statistics about stored data
- **Status**: 200 OK

---

## 11. Rate Limiting

### 11.1 Configuration
- **HTTP API**: 100 requests/minute per IP
- **WebSocket New Connections**: 10/minute per IP
- **Game Actions**: 30/minute per player
- **Headers**:
  - `X-RateLimit-Limit`: Request limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset timestamp

### 11.2 GET /api/rate-limit/stats
- **Purpose**: Rate limit statistics
- **Response**: See section 2.5
- **Status**: 200 OK

### 11.3 GET /api/metrics/rate_limits
- **Purpose**: Detailed metrics
- **Response**: See section 7.5
- **Status**: 200 OK

---

## 12. WebSocket Endpoints

### 12.1 WebSocket /ws/{room_id}
- **Purpose**: Main game connection
- **Path Parameters**: 
  - `room_id`: Room identifier or "lobby"
- **Connection**: `ws://localhost:5050/ws/{room_id}`
- **Events (Client → Server)**:
  - `client_ready`: `{"room_id": "ABC", "player_name": "John", "is_reconnection": false}`
  - `create_room`: `{"player_name": "John", "max_players": 4}`
  - `join_room`: `{"room_id": "ABC", "player_name": "John", "is_bot": false}`
  - `start_game`: `{}`
  - `declare`: `{"count": 3}`
  - `play`: `{"pieces": [0, 1, 2]}`
  - `accept_redeal`: `{}`
  - `decline_redeal`: `{}`
  - `leave_room`: `{}`
- **Events (Server → Client)**:
  - `room_created`: Room creation confirmation
  - `player_joined`: New player notification
  - `game_started`: Game initialization
  - `phase_change`: Game state updates
  - `error`: Error messages

### 12.2 WebSocket /ws/lobby
- **Purpose**: Lobby operations
- **Note**: Same as /ws/lobby using room_id "lobby"

### 12.3 WebSocket /api/telemetry/ws/telemetry-monitor
- **Purpose**: Real-time telemetry monitoring
- **Connection**: `ws://localhost:5050/api/telemetry/ws/telemetry-monitor`
- **Dashboard**: http://localhost:5050/telemetry-dashboard
- **Outgoing Events**: Real-time telemetry updates

---

## 13. Quick Troubleshooting

### 13.1 Common Status Codes
| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | Success | Normal operation |
| 400 | Bad Request | Invalid parameters, malformed JSON |
| 404 | Not Found | Room/resource doesn't exist |
| 429 | Rate Limited | Too many requests |
| 500 | Server Error | Check logs |
| 501 | Not Implemented | Feature not available |
| 503 | Service Unavailable | Server overloaded |

### 13.2 Performance Thresholds
| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| WebSocket Latency | <50ms | 50-200ms | >200ms |
| API Response | <500ms | 500-2000ms | >2000ms |
| Play History API | <500ms | 1-3s | >3s |
| Error Rate | <0.1% | 0.1-1% | >1% |
| Heartbeat Lag | <35s | 35-90s | >90s |
| Bundle Success | >95% | 90-95% | <90% |
| Cache Hit Rate | >80% | 50-80% | <50% |

### 13.3 Quick Debug Checklist
```bash
# Player hanging?
curl http://localhost:5050/api/debug/player-activity/{room_id}
curl http://localhost:5050/api/debug/hang-diagnostics?player_id={name}

# Performance issue?
curl http://localhost:5050/api/metrics
curl http://localhost:5050/api/health/performance

# Connection problems?
curl http://localhost:5050/api/debug/connection-timeline/{room_id}
curl http://localhost:5050/api/debug/bot-control-analysis/{room_id}

# System health?
curl http://localhost:5050/api/health/detailed
curl http://localhost:5050/api/system/stats
```

### 13.4 Environment Variables
```bash
DATABASE_PATH=/path/to/game_events.db
LOG_RETENTION_ACTIVE_DAYS=3
LOG_RETENTION_ARCHIVE_DAYS=30
LOG_CLEANUP_ENABLED=true
LOG_CLEANUP_HOUR=3
STORE_TURN_DETAILS=false
ENABLE_RATE_LIMITING=true
TELEMETRY_ENABLED=true
TELEMETRY_RETENTION_DAYS=7
```