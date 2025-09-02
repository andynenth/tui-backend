# Production Debugging Guide

## Overview

The production debugging system provides comprehensive tools for diagnosing issues in live environments. It includes event sourcing replay, log analysis, activity monitoring, and real-time debugging endpoints without impacting game performance.

## Architecture

```
┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ Debug Endpoints  │     │ Event Store     │     │ Log Buffer       │
├──────────────────┤     ├─────────────────┤     ├──────────────────┤
│ • /debug/events  │────►│ • Game Events   │     │ • Circular Log   │
│ • /debug/replay  │     │ • State Replay  │     │ • Level Filter   │
│ • /debug/logs    │     │ • Validation    │     │ • Search         │
└──────────────────┘     └─────────────────┘     └──────────────────┘
         │                        │                        │
         └────────────────────────┴────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │ Activity Tracker   │
                    │ • Player Activity  │
                    │ • Hang Detection   │
                    └────────────────────┘
```

## Debug Endpoints

### 1. Event Analysis

#### GET `/api/debug/events/{room_id}`

Retrieve all events for a room with optional filtering.

**Query Parameters**:
- `limit`: Maximum events to return
- `event_type`: Filter by specific event type

**Response**:
```json
{
    "room_id": "abc123",
    "total_events": 245,
    "events": [
        {
            "sequence": 1,
            "event_type": "game_started",
            "player_id": "system",
            "timestamp": 1693654200.123,
            "payload": {
                "players": ["Player1", "Player2", "Player3", "Player4"],
                "round": 1
            }
        }
    ]
}
```

#### GET `/api/debug/replay/{room_id}`

Replay and reconstruct game state from events.

**Response**:
```json
{
    "room_id": "abc123",
    "reconstructed_state": {
        "phase": "TURN",
        "current_player": "Player2",
        "scores": {"Player1": 25, "Player2": 18, ...}
    },
    "validation": {
        "valid": true,
        "gaps": [],
        "duplicate_sequences": []
    },
    "statistics": {
        "total_events": 245,
        "event_types": {
            "turn_play": 89,
            "declaration": 16,
            "phase_change": 20
        }
    }
}
```

### 2. Turn Analysis

#### GET `/api/debug/turns/{room_id}`

Get detailed turn-by-turn play history.

**Query Parameters**:
- `turn_number`: Specific turn to retrieve
- `player_name`: Filter by player

**Response**:
```json
{
    "room_id": "abc123",
    "total_turns": 15,
    "turns": [
        {
            "turn_number": 1,
            "plays": [
                {
                    "player": "Player1",
                    "pieces_count": 3,
                    "play_type": "STRAIGHT",
                    "play_value": 456,
                    "pieces": ["CANNON_RED", "HORSE_BLACK", "CHARIOT_RED"],
                    "valid": true
                }
            ],
            "winner": "Player3",
            "piles_won": 2
        }
    ]
}
```

### 3. Room Statistics

#### GET `/api/debug/room-stats`

Get comprehensive room statistics.

**Query Parameters**:
- `room_id`: Optional specific room ID

**Response**:
```json
{
    "timestamp": 1693654200.123,
    "stats": {
        "total_rooms": 5,
        "active_connections": 18,
        "rooms": {
            "abc123": {
                "player_count": 4,
                "bot_count": 1,
                "phase": "TURN",
                "created_at": "2025-09-02T10:00:00Z",
                "last_activity": "2025-09-02T10:30:00Z"
            }
        }
    }
}
```

### 4. Log Analysis

#### GET `/api/debug/logs`

Retrieve filtered server logs from memory buffer.

**Query Parameters**:
- `limit`: Maximum entries (default: 100)
- `level`: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logger`: Filter by logger name
- `since_minutes`: Logs from last N minutes
- `search`: Search in message content

**Response**:
```json
{
    "total_entries": 523,
    "filtered_count": 45,
    "entries": [
        {
            "timestamp": 1693654200.123,
            "level": "ERROR",
            "logger": "backend.engine.game",
            "message": "Invalid play attempted",
            "context": {
                "room_id": "abc123",
                "player": "Player2",
                "error": "Insufficient pieces"
            }
        }
    ]
}
```

### 5. Activity Monitoring

#### GET `/api/debug/activity/{room_id}`

Get player activity status for debugging hangs.

**Response**:
```json
{
    "room_id": "abc123",
    "players": {
        "Player1": {
            "status": "active",
            "last_heartbeat": "2025-09-02T10:30:00Z",
            "last_action": "play",
            "idle_duration": 0
        },
        "Player2": {
            "status": "idle",
            "idle_duration_seconds": 120,
            "takeover_pending": true
        }
    }
}
```

### 6. System Health

#### GET `/api/health/detailed`

Get detailed system health information.

**Response**:
```json
{
    "status": "healthy",
    "services": {
        "api": "healthy",
        "websocket": "healthy",
        "event_store": {
            "status": "healthy",
            "total_events": 12453,
            "database_size_mb": 45.2
        },
        "room_manager": {
            "status": "healthy",
            "active_rooms": 5,
            "total_players": 18
        }
    }
}
```

## Common Debugging Scenarios

### 1. Player Hang Investigation

```bash
# 1. Check player activity
GET /api/debug/activity/{room_id}

# 2. Review recent logs
GET /api/debug/logs?search=player_name&since_minutes=10

# 3. Check recent events
GET /api/debug/events/{room_id}?limit=50

# 4. Analyze turn history
GET /api/debug/turns/{room_id}?player_name=Player2
```

### 2. Game State Corruption

```bash
# 1. Replay state from events
GET /api/debug/replay/{room_id}

# 2. Validate event sequence
GET /api/debug/validate/{room_id}

# 3. Compare with room stats
GET /api/debug/room-stats?room_id={room_id}

# 4. Check error logs
GET /api/debug/logs?level=ERROR&logger=state_machine
```

### 3. Performance Issues

```bash
# 1. Check performance metrics
GET /api/health/performance

# 2. Review slow query logs
GET /api/debug/logs?search=slow_query&level=WARNING

# 3. Check event processing rate
GET /api/debug/stats

# 4. Monitor active connections
GET /api/debug/room-stats
```

## Log Buffer System

### Configuration

```python
# backend/api/services/log_buffer.py
class InMemoryLogBuffer:
    def __init__(self, max_size: int = 2000):
        # Circular buffer with 2000 entries
        self.buffer = deque(maxlen=max_size)
```

### Log Entry Format

```python
{
    "timestamp": 1693654200.123,
    "level": "ERROR",
    "logger": "backend.engine.game",
    "message": "Error message",
    "context": {
        # Additional context data
    }
}
```

### Custom Logger Integration

```python
# Add to any module for debugging
import logging
from backend.api.services.log_buffer import log_buffer

logger = logging.getLogger(__name__)

# Log with context
logger.error("Game error", extra={
    "room_id": room_id,
    "player": player_name,
    "phase": game_phase
})
```

## Event Store Debugging

### Event Validation

```python
# Validate event sequence integrity
validation = await event_store.validate_event_sequence(room_id)

if not validation["valid"]:
    # Check for gaps
    for gap in validation["gaps"]:
        logger.error(f"Sequence gap: expected {gap['expected']}, got {gap['actual']}")
    
    # Check for duplicates
    for dup in validation["duplicate_sequences"]:
        logger.error(f"Duplicate sequence {dup} found")
```

### State Reconstruction

```python
# Replay events to reconstruct state
state = await event_store.replay_room_state(room_id)

# Useful for:
# - Debugging state inconsistencies
# - Recovering from corruption
# - Analyzing game progression
```

## Production Debugging Best Practices

### 1. Non-Invasive Monitoring

```python
# Use read-only endpoints
# Never modify state through debug endpoints
# Implement rate limiting on debug endpoints

@router.get("/debug/events/{room_id}")
@rate_limit(calls=10, period=60)  # 10 calls per minute
async def get_room_events(room_id: str):
    # Implementation
```

### 2. Structured Logging

```python
# Always include context
logger.info("Player action", extra={
    "room_id": room_id,
    "player": player_name,
    "action": action_type,
    "phase": current_phase,
    "request_id": request_id  # For tracing
})
```

### 3. Event Correlation

```python
# Use request IDs for tracing
request_id = str(uuid.uuid4())

# Pass through all operations
await process_action(action, request_id=request_id)

# Query by request ID
GET /api/debug/logs?search=request_id_value
```

### 4. Performance Impact

```python
# Use sampling for high-frequency operations
if random.random() < 0.1:  # 10% sampling
    detailed_logging_enabled = True

# Async operations for debugging
asyncio.create_task(log_debug_info(data))
```

## Security Considerations

### 1. Access Control

```python
# Protect debug endpoints
@router.get("/debug/events/{room_id}")
@require_admin_auth
async def get_room_events(room_id: str):
    # Implementation
```

### 2. Data Sanitization

```python
# Remove sensitive data from logs
def sanitize_player_data(data):
    if "password" in data:
        data["password"] = "[REDACTED]"
    if "token" in data:
        data["token"] = "[REDACTED]"
    return data
```

### 3. Rate Limiting

```python
# Prevent debug endpoint abuse
from fastapi_limiter import RateLimiter

@router.get("/debug/logs")
@RateLimiter(times=10, seconds=60)
async def get_logs():
    # Implementation
```

## Troubleshooting Tools

### 1. Event Stream Monitor

```bash
# Watch events in real-time
wscat -c ws://localhost:8001/debug/stream/{room_id}
```

### 2. Log Tail

```bash
# Continuous log monitoring
while true; do
    curl -s "http://localhost:8001/api/debug/logs?limit=10&since_minutes=1"
    sleep 2
done
```

### 3. Health Check Loop

```bash
# Monitor system health
watch -n 5 'curl -s http://localhost:8001/api/health/detailed | jq'
```

## Common Issues and Solutions

### Issue: Missing Events

**Diagnosis**:
```bash
GET /api/debug/validate/{room_id}
```

**Solution**:
- Check event store health
- Verify database connectivity
- Review error logs for write failures

### Issue: State Mismatch

**Diagnosis**:
```bash
GET /api/debug/replay/{room_id}
```

**Solution**:
- Compare replayed state with current
- Check for missing phase_change events
- Verify state machine transitions

### Issue: Player Timeout

**Diagnosis**:
```bash
GET /api/debug/activity/{room_id}
```

**Solution**:
- Check heartbeat configuration
- Verify WebSocket stability
- Review network logs

## Future Enhancements

1. **Distributed Tracing**: OpenTelemetry integration
2. **Time-Travel Debugging**: Replay to specific points
3. **Automated Diagnostics**: AI-powered issue detection
4. **Visual Debugging**: Web-based debug dashboard
5. **Performance Profiling**: Detailed execution traces