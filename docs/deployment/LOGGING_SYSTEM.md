# Logging System Documentation

## Overview

Liap Tui implements a dual logging system:
1. **Event Store**: Structured game events stored in SQLite database for replay and debugging
2. **Application Logs**: Traditional logs for monitoring, debugging, and operational insights

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
├─────────────────┬───────────────────────────────────────────┤
│   Event Store   │           Application Logs                │
├─────────────────┼───────────────────────────────────────────┤
│  SQLite DB      │  stdout  │  File Logs  │  Memory Buffer  │
│ (game_events.db)│ (console)│ (rate_limit)│   (API access)  │
└─────────────────┴──────────┴─────────────┴─────────────────┘
```

## 1. Event Store System

### Purpose
- Store complete game history for debugging and analysis
- Enable game replay and state reconstruction
- Provide audit trail for game fairness
- Support player recovery after disconnections

### Storage Details
- **Type**: SQLite Database
- **File**: `game_events.db`
- **Location**: Project root directory
- **Schema**:
  ```sql
  CREATE TABLE game_events (
      sequence INTEGER PRIMARY KEY AUTOINCREMENT,
      room_id TEXT NOT NULL,
      event_type TEXT NOT NULL,
      payload JSON NOT NULL,
      player_id TEXT,
      timestamp REAL NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
  ```

### Event Types Stored
- `room_created`: New game room initialization
- `player_joined`: Player enters room
- `game_started`: Game begins
- `phase_change`: Game phase transitions
- `phase_data_update`: State updates within a phase
- `action_processed`: Player actions (declare, play, etc.)
- `game_ended`: Game completion
- `player_left`: Player disconnection

### API Endpoints
```bash
# Get all events for a room
GET /api/rooms/{room_id}/events

# Get reconstructed game state
GET /api/rooms/{room_id}/state

# Event store statistics
GET /api/event-store/stats

# Cleanup old events
POST /api/event-store/cleanup
```

### Maintenance
- **Growth Rate**: ~10-50MB per day with active games
- **No automatic cleanup**: Manual intervention required
- **Cleanup Command**:
  ```bash
  curl -X POST http://localhost:5050/api/event-store/cleanup \
    -H "Content-Type: application/json" \
    -d '{"hours": 168}'  # Keep last 7 days
  ```

## 2. Application Logging System

### Purpose
- Monitor application health and performance
- Debug issues and track errors
- Security monitoring and alerting
- Performance analysis and optimization

### Log Destinations

#### 2.1 Console/stdout (Primary)
- **Configuration**: `backend/config/logging_config.py`
- **Format**: JSON or text (via `LOG_FORMAT` env variable)
- **Level**: Controlled by `LOG_LEVEL` env variable (default: INFO)
- **Usage**: Main application logs, errors, warnings

#### 2.2 File-Based Logs
1. **Rate Limit Log**
   - **Path**: `logs/rate_limit.log`
   - **Purpose**: Track API rate limiting events
   - **Rotation**: 10MB max size, 5 backup files
   - **Format**: Standard Python logging format

2. **Claude Debug Log**
   - **Path**: `log.txt` (project root)
   - **Purpose**: Special debugging for AI development
   - **Note**: Referenced in CLAUDE.md for AI assistant access

#### 2.3 In-Memory Buffer
- **Service**: `backend/api/services/log_buffer.py`
- **Capacity**: Recent logs kept in memory
- **Access**: Via API for real-time debugging
- **Use Case**: Development and troubleshooting

### Log Categories

#### Game Events
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "category": "game_event",
  "event": "phase_change",
  "room_id": "ABC123",
  "details": {
    "from_phase": "DECLARATION",
    "to_phase": "TURN",
    "player_count": 4
  }
}
```

#### WebSocket Activity
```json
{
  "timestamp": "2024-01-15T10:30:46.456Z",
  "level": "DEBUG",
  "category": "websocket",
  "event": "connection_established",
  "client_id": "client_xyz",
  "room_id": "ABC123"
}
```

#### Performance Metrics
```json
{
  "timestamp": "2024-01-15T10:30:47.789Z",
  "level": "INFO",
  "category": "performance",
  "operation": "broadcast_game_state",
  "duration_ms": 45,
  "player_count": 4
}
```

#### Security Events
```json
{
  "timestamp": "2024-01-15T10:30:48.012Z",
  "level": "WARNING",
  "category": "security",
  "event": "rate_limit_exceeded",
  "ip_address": "192.168.1.100",
  "endpoint": "/api/rooms"
}
```

#### Error Tracking
```json
{
  "timestamp": "2024-01-15T10:30:49.345Z",
  "level": "ERROR",
  "category": "error",
  "error_type": "ValidationError",
  "message": "Invalid piece play",
  "stack_trace": "...",
  "context": {
    "room_id": "ABC123",
    "player_id": "player_1"
  }
}
```

## Configuration

### Environment Variables
```bash
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Log format: json or text
LOG_FORMAT=json

# Enable/disable specific loggers
ENABLE_WEBSOCKET_LOGGING=true
ENABLE_PERFORMANCE_LOGGING=true
```

### Python Logging Configuration
```python
# backend/config/logging_config.py
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '%(message)s',
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
        },
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json' if os.getenv('LOG_FORMAT') == 'json' else 'standard'
        }
    }
}
```

## Production Deployment

### Log Aggregation Options
1. **ELK Stack** (Elasticsearch, Logstash, Kibana)
   - Parse JSON logs automatically
   - Create dashboards for game metrics
   - Set up alerts for errors

2. **CloudWatch Logs** (AWS)
   - Stream logs from containers
   - Create metric filters
   - Set up CloudWatch alarms

3. **Datadog**
   - APM integration for performance
   - Log correlation with metrics
   - Custom dashboards

### Best Practices
1. **Use structured logging** (JSON) in production
2. **Include correlation IDs** for request tracing
3. **Log at appropriate levels** (avoid DEBUG in production)
4. **Implement log sampling** for high-volume events
5. **Set up alerts** for ERROR and CRITICAL levels
6. **Rotate logs** to prevent disk space issues
7. **Secure sensitive data** - never log passwords, tokens, or PII

## Monitoring and Alerts

### Key Metrics to Monitor
- Error rate per minute
- WebSocket connection failures
- Game phase transition times
- API response times
- Rate limit violations

### Alert Thresholds
| Metric | Warning | Critical |
|--------|---------|----------|
| Error Rate | >10/min | >50/min |
| Response Time | >500ms | >2000ms |
| Connection Failures | >5% | >20% |
| Disk Usage (DB) | >1GB | >5GB |

## Troubleshooting

### Common Issues

#### 1. Database Growing Too Large
```bash
# Check size
ls -lh game_events.db

# Run cleanup
curl -X POST http://localhost:5050/api/event-store/cleanup
```

#### 2. Missing Logs in Production
- Check `LOG_LEVEL` environment variable
- Verify log aggregator is receiving data
- Check container logs: `docker logs <container>`

#### 3. Performance Impact
- Event store writes are async (minimal impact)
- Consider disabling DEBUG logging in production
- Monitor SQLite database performance with large datasets

## Future Improvements

### Planned Enhancements
1. **Automatic event cleanup** based on retention policy
2. **Log compression** for archived events
3. **Separate read/write databases** for event store
4. **Metrics dashboard** for real-time monitoring
5. **Log sampling** for high-frequency events

### Considerations
- Implement event store partitioning by date
- Add support for external databases (PostgreSQL)
- Create log analysis tools for game balance
- Add player behavior analytics

## Related Documentation
- [Production Operations Guide](./OPERATIONS.md)
- [Event Store Maintenance](./EVENT_STORE_MAINTENANCE.md)
- [Debugging Guide](../06-tutorials/DEBUGGING_GUIDE.md)