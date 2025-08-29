# Production Operations Guide

This guide covers production monitoring, maintenance, and operational procedures for Liap Tui.

## Table of Contents
1. [Health Monitoring](#health-monitoring)
2. [System Statistics](#system-statistics)
3. [Event Store & Recovery](#event-store--recovery)
   - [Automated Log Maintenance System](#automated-log-maintenance-system)
4. [Logging](#logging)
5. [Performance Monitoring](#performance-monitoring)
6. [Troubleshooting Production Issues](#troubleshooting-production-issues)

## Health Monitoring

The application includes enterprise-grade monitoring and observability features.

### Health Check Endpoints

#### Basic Health Check
Used by load balancers to verify service availability:
```bash
curl http://localhost:5050/api/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Detailed Health Information
Provides comprehensive system health metrics:
```bash
curl http://localhost:5050/api/health/detailed
```

Response includes:
- Service uptime
- Resource usage (CPU, memory)
- Active connections
- Recent error rates
- Component health status

#### Prometheus-Compatible Metrics
For integration with monitoring systems:
```bash
curl http://localhost:5050/api/health/metrics
```

Returns metrics in Prometheus format:
```
# HELP active_connections Number of active WebSocket connections
# TYPE active_connections gauge
active_connections 42

# HELP game_rooms_active Number of active game rooms
# TYPE game_rooms_active gauge
game_rooms_active 12
```

## System Statistics

### Complete System Overview
```bash
curl http://localhost:5050/api/system/stats
```

Provides:
- Server resource usage
- Connection statistics
- Game room metrics
- Performance indicators
- Error summaries

### Recovery System Status
```bash
curl http://localhost:5050/api/recovery/status
```

Shows:
- Auto-recovery configuration
- Recent recovery actions
- Failed recovery attempts
- System stability score

### Room and Game Statistics
```bash
curl http://localhost:5050/api/debug/room-stats
```

Detailed room information:
- Active rooms and their states
- Player counts and bot status
- Game phase distribution
- Average game duration

## Event Store & Recovery

### View Game Events
Analyze game history for debugging or auditing:
```bash
curl http://localhost:5050/api/rooms/{room_id}/events
```

Returns chronological event list:
- Player actions
- State transitions
- System events
- Error occurrences

### Reconstructed Game State
Get current game state from event history:
```bash
curl http://localhost:5050/api/rooms/{room_id}/state
```

Useful for:
- Debugging state inconsistencies
- Recovering from crashes
- Analyzing game progression

### Event Store Statistics
```bash
curl http://localhost:5050/api/event-store/stats
```

Metrics include:
- Total events stored
- Events per game type
- Storage usage
- Compression ratios

### Play History API
The Play History API provides comprehensive game history for analysis and debugging:

#### Get Complete Play History
```bash
curl http://localhost:5050/api/rooms/{room_id}/play-history
```

Features:
- **Persistent Storage**: Retrieves data from SQLite event store
- **Works Without Memory**: Returns history even when room not in memory
- **Survives Restarts**: Historical data always available
- **5-Minute Cache**: Improves performance for repeated requests

#### Get Specific Rounds
```bash
# Get rounds 1-5
curl "http://localhost:5050/api/rooms/{room_id}/play-history/rounds?from=1&to=5"

# Get compact format (30-50% smaller)
curl "http://localhost:5050/api/rooms/{room_id}/play-history?format=compact"

# Exclude AI analysis
curl "http://localhost:5050/api/rooms/{room_id}/play-history?include_ai_analysis=false"
```

#### Performance Monitoring
- **Warning Alert**: Response time > 1 second
- **Critical Alert**: Response time > 3 seconds
- Monitor via `/api/metrics/play-history`

#### Data Sources
1. **Primary**: SQLite event store (`game_events.db`)
2. **Fallback**: In-memory game state (for active games)

### Automated Log Maintenance System

The application includes an automated log maintenance system that prevents database growth and manages storage efficiently.

#### Maintenance Status
Check the current status of the log maintenance system:
```bash
curl http://localhost:5050/api/maintenance/status
```

Response:
```json
{
  "database": {
    "size_mb": 4.68,
    "days_retained": 3
  },
  "archives": {
    "count": 15,
    "size_mb": 234.5,
    "oldest": "game_events_2024_12_15.db.gz",
    "days_retained": 30
  },
  "total_size_mb": 239.18,
  "last_cleanup": "2024-01-15T03:00:15Z",
  "next_cleanup": "2024-01-16T03:00:00Z",
  "scheduler_running": true
}
```

#### How It Works
1. **Automatic Daily Cleanup**: Runs at 3 AM (configurable)
2. **3-Day Active Retention**: Recent events stay in main database for fast queries
3. **30-Day Archive**: Older events compressed to `.gz` files
4. **Self-Limiting Storage**: Total usage capped at ~1.1GB

#### Configuration
Set these environment variables to customize behavior:
```bash
LOG_RETENTION_ACTIVE_DAYS=3     # Days in main database
LOG_RETENTION_ARCHIVE_DAYS=30   # Days to keep archives
LOG_CLEANUP_ENABLED=true        # Enable/disable automation
LOG_CLEANUP_HOUR=3              # Hour to run (0-23)
```

#### Manual Operations

Trigger cleanup manually (for testing or emergency):
```bash
curl -X POST http://localhost:5050/api/maintenance/trigger-cleanup
```

View current configuration:
```bash
curl http://localhost:5050/api/maintenance/config
```

#### Emergency Cleanup
When disk space is critical:
```bash
./emergency_cleanup.sh
```
This script:
- Keeps only 24 hours in database
- Deletes archives older than 7 days
- Vacuums database immediately

## Logging

### Log Structure
All system events are logged in structured JSON format with correlation IDs.

#### Log Categories

**Game Events**
- Phase transitions
- Player actions (declare, play, redeal decisions)
- Scoring calculations
- Win conditions

**WebSocket Activity**
- Connection establishment/termination
- Message delivery confirmations
- Reconnection attempts
- Protocol errors

**Performance Metrics**
- Operation timing
- Resource usage spikes
- Queue depths
- Latency measurements

**Security Events**
- Authentication attempts
- Rate limit violations
- Suspicious patterns
- Access denials

**Error Tracking**
- Full stack traces
- Request context
- User session info
- Recovery attempts

### Log Format Example
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "correlation_id": "abc123-def456",
  "category": "game_event",
  "event": "phase_change",
  "room_id": "ROOM_XYZ",
  "details": {
    "from_phase": "DECLARATION",
    "to_phase": "TURN",
    "player_count": 4,
    "duration_ms": 150
  }
}
```

### Log Aggregation
Logs can be aggregated using standard tools:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- CloudWatch Logs (AWS)
- Splunk
- Datadog

## Performance Monitoring

### Key Metrics to Monitor

**Response Times**
- WebSocket message round-trip time
- API endpoint latency
- Database query duration
- Play History API response time (target < 1s)

**Throughput**
- Messages per second
- Concurrent games
- Active connections
- Play History API requests per minute

**Resource Usage**
- CPU utilization
- Memory consumption
- Network bandwidth
- Disk I/O
- SQLite database size (auto-managed)

**Game Metrics**
- Average game duration
- Actions per minute
- Bot vs human player ratio
- Popular game times
- Historical games retrieved via Play History API

### Performance Thresholds

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| WebSocket Latency | <50ms | 50-200ms | >200ms |
| Play History API | <500ms | 1-3s | >3s |
| CPU Usage | <60% | 60-80% | >80% |
| Memory Usage | <70% | 70-85% | >85% |
| Error Rate | <0.1% | 0.1-1% | >1% |
| SQLite Cache Hit | >80% | 50-80% | <50% |

## Telemetry Monitoring

The application includes comprehensive client-side telemetry collection and monitoring capabilities for tracking bundle loading performance, user interactions, and error conditions.

### Telemetry Dashboard

Access the real-time telemetry monitoring dashboard:
```
http://localhost:5050/telemetry-dashboard
```

Features:
- **Real-time Event Feed**: Live stream of client telemetry events
- **Critical Alerts**: Automatic alerts for bundle failures and errors  
- **Performance Metrics**: Success rates, load times, and session statistics
- **Analytics Overview**: Error analysis, device breakdown, and connection quality
- **WebSocket Integration**: Live updates without page refresh

### Telemetry Data Collection API

#### Submit Telemetry Events
Client-side telemetry automatically submits events via:
```
POST /api/telemetry
```

**Request Format**:
```json
{
  "sessionId": "c0ul3k",
  "events": [
    {
      "event": "bundle_load_success",
      "timestamp": 1756452685169,
      "elapsed": 1250,
      "loadTime": 1250,
      "attempt": 1,
      "userAgent": "Mozilla/5.0...",
      "connection": {"effectiveType": "4g"},
      "screen": {"width": 1920, "height": 1080},
      "viewport": {"width": 1600, "height": 900},
      "memory": {"usedJSHeapSize": 45000000}
    }
  ]
}
```

**Event Types**:
- `page_load_start`: Initial page load
- `bundle_load_attempt`: Bundle loading initiated
- `bundle_load_success`: Bundle loaded successfully
- `bundle_error`: Bundle loading failed
- `load_timeout`: Loading exceeded timeout
- `javascript_error`: Client-side JavaScript error
- `unhandled_rejection`: Promise rejection
- `component_error`: React component error
- `performance_metrics`: Browser performance data
- `long_task`: Performance bottleneck detected
- `route_change`: Navigation event
- `react_app_unload`: Application cleanup

### Analytics APIs

#### Bundle Loading Performance
```bash
curl "http://localhost:5050/api/analytics/bundle-load-stats?hours=24&group_by=device"
```

**Response**:
```json
{
  "period": "last_24_hours",
  "summary": {
    "total_sessions": 152,
    "successful_loads": 147,
    "failed_loads": 5,
    "success_rate": 0.967,
    "avg_load_time": 1420.5,
    "mobile_percentage": 23.7,
    "slow_connections": 8,
    "total_errors": 12
  },
  "groups": {
    "desktop": {"sessions": 116, "success_rate": 0.974, "avg_load_time": 1245.2},
    "mobile": {"sessions": 36, "success_rate": 0.944, "avg_load_time": 1890.1}
  }
}
```

**Parameters**:
- `hours`: Time window (1-168 hours, default: 24)
- `group_by`: Group results by "device", "connection", or omit for summary only

#### Client-Side Errors
```bash
curl "http://localhost:5050/api/analytics/client-errors?hours=1&min_occurrences=1"
```

**Response**:
```json
{
  "period": "last_1_hours",
  "total_error_types": 3,
  "total_occurrences": 7,
  "unique_sessions_affected": 4,
  "errors": [
    {
      "type": "bundle_error",
      "message": "Failed to fetch bundle.js",
      "filename": "Unknown file",
      "occurrences": 3,
      "unique_sessions": 2,
      "last_seen": "2025-08-29 00:45:12",
      "severity": "critical"
    },
    {
      "type": "javascript_error", 
      "message": "Cannot read properties of null",
      "filename": "main.js",
      "occurrences": 2,
      "unique_sessions": 2,
      "last_seen": "2025-08-29 00:30:25",
      "severity": "warning"
    }
  ]
}
```

#### Device and Browser Breakdown
```bash
curl "http://localhost:5050/api/analytics/device-breakdown?hours=24"
```

**Response**:
```json
{
  "period": "last_24_hours",
  "devices": {
    "desktop": 116,
    "mobile": 34,
    "tablet": 2
  },
  "browsers": {
    "Chrome": 98,
    "Safari": 32,
    "Firefox": 18,
    "Edge": 4
  },
  "connections": {
    "4g": 89,
    "3g": 34,
    "wifi": 25,
    "2g": 4
  }
}
```

#### Performance Trends
```bash
curl "http://localhost:5050/api/analytics/performance-trends?hours=24&interval=1h"
```

**Response**:
```json
{
  "period": "last_24_hours",
  "interval": "1h",
  "data_points": 24,
  "trends": [
    {
      "timestamp": "2025-08-29 01:00:00",
      "sessions": 12,
      "success_rate": 0.917,
      "avg_load_time": 1580.3,
      "error_rate": 0.08
    }
  ]
}
```

### Privacy and Data Management

#### Privacy Compliance Report
```bash
curl http://localhost:5050/api/privacy/report
```

Shows data retention policies, anonymization practices, and compliance status.

#### Export User Data (GDPR)
```bash
curl http://localhost:5050/api/privacy/export/{session_id}
```

Export all telemetry data for a specific session ID.

#### Delete User Data (Right to be Forgotten)
```bash
curl -X DELETE http://localhost:5050/api/privacy/delete/{session_id}
```

Permanently delete all telemetry data for a session.

#### Data Summary
```bash
curl http://localhost:5050/api/privacy/data-summary
```

**Response**:
```json
{
  "summary": {
    "total_events": 1247,
    "total_sessions": 89,
    "oldest_data": "2025-08-27 10:15:32",
    "newest_data": "2025-08-29 00:31:25"
  },
  "events_by_type": {
    "bundle_load_success": 523,
    "performance_metrics": 312,
    "page_load_start": 89,
    "javascript_error": 12
  },
  "sessions_by_device": {
    "desktop": 67,
    "mobile": 20,
    "tablet": 2
  },
  "data_retention": "7-90 days depending on event type",
  "privacy_note": "All data is anonymized and automatically cleaned up"
}
```

### Telemetry Monitoring Thresholds

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Bundle Success Rate | >95% | 90-95% | <90% |
| Average Load Time | <2s | 2-5s | >5s |
| Error Rate | <1% | 1-5% | >5% |
| Mobile Success Rate | >90% | 80-90% | <80% |
| Slow Connection Success | >85% | 70-85% | <70% |

### Automatic Alerting

The telemetry system includes intelligent alerting:

**Critical Alerts** (immediate attention):
- Bundle load failures ≥3 consecutive attempts
- Mobile Safari compatibility issues
- Error rate spike >5% in 5 minutes
- Complete bundle loading failures

**Warning Alerts** (investigate when convenient):
- Success rate drops below 95%
- Average load time exceeds 3 seconds
- Slow connection (2G/slow-2G) issues
- High error frequency on specific browsers

**Alert Actions**:
1. **Dashboard Notification**: Real-time alert bar with dismiss option
2. **Server Logging**: Structured logs with alert context
3. **WebSocket Broadcast**: Live updates to monitoring dashboard
4. **Auto-Dismissal**: Warning alerts auto-dismiss after 10 seconds

### Telemetry Data Storage

**Database**: SQLite (`telemetry_data.db`) with automatic cleanup
**Tables**:
- `telemetry_events`: Individual telemetry events with full context
- `telemetry_sessions`: Session-level aggregated metrics
- `telemetry_stats`: Daily statistics for historical analysis

**Data Retention**:
- Raw events: 7 days (configurable)
- Session summaries: 30 days
- Daily statistics: 90 days
- Automatic cleanup prevents unbounded growth

**Privacy Compliance**:
- All IP addresses are anonymized after 24 hours
- No personally identifiable information is stored
- Session IDs are randomly generated, not user-linked
- Full GDPR compliance with export/deletion endpoints

## Troubleshooting Production Issues

### Common Issues and Solutions

#### High Memory Usage
**Symptoms**: Increasing memory consumption over time

**Diagnosis**:
1. Check for memory leaks in game state
2. Review connection cleanup
3. Analyze event store size

**Solutions**:
- Implement connection limits
- Add memory-based auto-scaling
- Event store pruning is automated (see [Automated Log Maintenance System](#automated-log-maintenance-system))

#### WebSocket Connection Drops
**Symptoms**: Frequent disconnections, reconnection storms

**Diagnosis**:
1. Check network infrastructure
2. Review proxy/load balancer timeouts
3. Analyze client-side errors

**Solutions**:
- Adjust keepalive intervals
- Implement connection pooling
- Add retry backoff logic

#### Slow Game Performance
**Symptoms**: High latency, delayed responses

**Diagnosis**:
1. Profile hot code paths
2. Check database query performance
3. Review broadcast efficiency

**Solutions**:
- Optimize state machine transitions
- Implement caching layer
- Batch message broadcasts

#### Play History API Performance Issues
**Symptoms**: Slow response times, timeouts on history requests

**Diagnosis**:
1. Check SQLite database size
2. Review cache hit rates
3. Analyze query complexity

**Solutions**:
- Ensure automated log maintenance is running
- Increase cache TTL if appropriate
- Use compact format for large histories
- Query specific rounds instead of full history

### Emergency Procedures

#### Service Degradation
1. Enable rate limiting
2. Disable non-essential features
3. Scale horizontally
4. Monitor recovery

#### Data Corruption
1. Stop write operations
2. Backup current state
3. Restore from event store
4. Validate data integrity

#### Complete Outage
1. Check infrastructure health
2. Review recent deployments
3. Rollback if necessary
4. Communicate with users

### Monitoring Dashboards

Recommended dashboard panels:
1. **System Overview**: Health, uptime, active games
2. **Performance**: Latency, throughput, errors
3. **Resources**: CPU, memory, network, disk
4. **Game Analytics**: Popular times, game duration, win rates
5. **Alerts**: Critical issues, anomalies, trends

### Alerting Rules

Configure alerts for:
- Health check failures (>3 consecutive)
- Error rate spike (>1% for 5 minutes)
- Resource exhaustion (>90% for 10 minutes)
- Connection limit reached
- Recovery system activation

## Maintenance Tasks

### Regular Maintenance

**Daily**
- Review error logs
- Check resource trends
- Verify backup completion

**Weekly**
- Analyze performance metrics
- Review security events
- Update monitoring thresholds

**Monthly**
- Review log maintenance metrics
- Optimize database indices
- Review capacity planning
- Update documentation

### Deployment Procedures

**Pre-deployment**
1. Run full test suite
2. Check resource availability
3. Notify users of maintenance
4. Prepare rollback plan

**Deployment**
1. Deploy to staging
2. Run smoke tests
3. Deploy to production (rolling)
4. Monitor error rates

**Post-deployment**
1. Verify all services healthy
2. Check performance metrics
3. Monitor user feedback
4. Document any issues

## Security Monitoring

### Security Metrics
- Failed authentication attempts
- Rate limit violations
- Unusual traffic patterns
- Geographic anomalies

### Security Response
1. **Detection**: Automated alerts on suspicious activity
2. **Investigation**: Review logs and patterns
3. **Mitigation**: Block IPs, adjust rate limits
4. **Prevention**: Update rules and monitoring

## Capacity Planning

### Scaling Triggers
- CPU sustained >70%
- Memory usage >80%
- Queue depth >1000
- Response time >200ms

### Scaling Strategy
1. **Horizontal**: Add more containers
2. **Vertical**: Increase container resources
3. **Geographic**: Deploy to multiple regions
4. **Caching**: Add Redis/CDN layers

## Compliance and Auditing

### Audit Requirements
- Game fairness verification
- User action logging
- System access tracking
- Data retention policies

### Compliance Checks
- Regular security scans
- Dependency updates
- License compliance
- Privacy regulations

---

For development and testing procedures, see the main [README](README.md).
For debugging specific issues, consult the [Debugging Guide](docs/06-tutorials/DEBUGGING_GUIDE.md).