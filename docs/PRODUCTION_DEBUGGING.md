# Production Debugging Guide

## Overview

This guide provides comprehensive procedures for debugging issues in production Liap Tui deployments. It covers debug endpoints, log analysis, real-time monitoring, and emergency procedures.

## Debug Architecture

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│    Debug Routes     │     │    Event Store      │     │    Log Buffer       │
├─────────────────────┤     ├─────────────────────┤     ├─────────────────────┤
│ • /debug/events     │ ──> │ • Event history     │ ←── │ • Circular buffer   │
│ • /debug/logs       │     │ • State replay      │     │ • Structured logs   │
│ • /debug/stats      │     │ • Validation        │     │ • Search/filter     │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
                  ↓                                                 ↓
        ┌─────────────────────┐                       ┌─────────────────────┐
        │  Activity Monitor   │                       │   Health Monitor    │
        ├─────────────────────┤                       ├─────────────────────┤
        │ • Player tracking   │                       │ • System metrics    │
        │ • Hang detection    │                       │ • Resource usage    │
        │ • Diagnostics       │                       │ • Performance       │
        └─────────────────────┘                       └─────────────────────┘
```

## Debug Endpoints Reference

### Event Store Endpoints

#### 1. Get Room Events
```bash
GET /api/debug/events/{room_id}?limit=100&event_type=turn_play
```

View all events for a room with optional filtering:

```bash
# Get last 50 events
curl http://localhost:5050/api/debug/events/ROOM123?limit=50

# Get only turn_play events
curl http://localhost:5050/api/debug/events/ROOM123?event_type=turn_play

# Get declaration events
curl http://localhost:5050/api/debug/events/ROOM123?event_type=declaration
```

#### 2. Replay Room State
```bash
GET /api/debug/replay/{room_id}
```

Reconstruct game state from events:

```bash
curl http://localhost:5050/api/debug/replay/ROOM123
```

Response includes:
- Reconstructed state
- Validation results
- Event statistics
- Timeline

#### 3. Get Events Since Sequence
```bash
GET /api/debug/events/{room_id}/sequence/{seq}
```

Get events after a specific sequence number:

```bash
# Get events after sequence 100
curl http://localhost:5050/api/debug/events/ROOM123/sequence/100
```

#### 4. Export Room History
```bash
GET /api/debug/export/{room_id}
```

Complete room history for analysis:

```bash
curl http://localhost:5050/api/debug/export/ROOM123 > room_history.json
```

#### 5. Validate Event Sequence
```bash
GET /api/debug/validate/{room_id}
```

Check event integrity:

```bash
curl http://localhost:5050/api/debug/validate/ROOM123
```

### Log Buffer Endpoints

#### 1. Get Debug Logs
```bash
GET /api/debug/logs?limit=100&level=ERROR&search=timeout
```

Query parameters:
- `limit`: Max entries (default: 100, max: 1000)
- `level`: Filter by level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logger_filter`: Filter by logger name
- `since_minutes`: Only recent logs
- `search`: Search in messages

Examples:
```bash
# Get all errors from last 5 minutes
curl "http://localhost:5050/api/debug/logs?level=ERROR&since_minutes=5"

# Search for WebSocket errors
curl "http://localhost:5050/api/debug/logs?search=websocket&level=ERROR"

# Get logs from specific logger
curl "http://localhost:5050/api/debug/logs?logger_filter=backend.api.routes.ws"
```

#### 2. Log Statistics
```bash
GET /api/debug/logs/stats
```

Get buffer statistics:

```bash
curl http://localhost:5050/api/debug/logs/stats
```

#### 3. Clear Logs
```bash
DELETE /api/debug/logs
```

Clear log buffer (use with caution):

```bash
curl -X DELETE http://localhost:5050/api/debug/logs
```

### Turn History Endpoints

#### 1. Get Turn Plays
```bash
GET /api/debug/turns/{room_id}?turn_number=5&player_name=Player1
```

User-friendly turn history:

```bash
# Get all turns
curl http://localhost:5050/api/debug/turns/ROOM123

# Get specific turn
curl http://localhost:5050/api/debug/turns/ROOM123?turn_number=5

# Get player's turns
curl "http://localhost:5050/api/debug/turns/ROOM123?player_name=Player1"
```

### System Statistics

#### 1. Event Store Stats
```bash
GET /api/debug/stats
```

Overall event store health:

```bash
curl http://localhost:5050/api/debug/stats
```

#### 2. Cleanup Old Events
```bash
POST /api/debug/cleanup?older_than_hours=24
```

Remove old events:

```bash
curl -X POST "http://localhost:5050/api/debug/cleanup?older_than_hours=48"
```

## Common Debugging Scenarios

### Scenario 1: Player Reports Game Frozen

**Step 1**: Check player activity
```bash
curl http://localhost:5050/api/debug/player-activity/ROOM123
```

**Step 2**: Review recent events
```bash
curl "http://localhost:5050/api/debug/events/ROOM123?limit=20"
```

**Step 3**: Check for errors
```bash
curl "http://localhost:5050/api/debug/logs?search=ROOM123&level=ERROR&since_minutes=10"
```

**Step 4**: Validate state
```bash
curl http://localhost:5050/api/debug/replay/ROOM123
```

### Scenario 2: Game State Inconsistency

**Step 1**: Export full history
```bash
curl http://localhost:5050/api/debug/export/ROOM123 > history.json
```

**Step 2**: Validate event sequence
```bash
curl http://localhost:5050/api/debug/validate/ROOM123
```

**Step 3**: Compare states
```python
# Analyze exported history
import json

with open('history.json') as f:
    data = json.load(f)
    
# Check for gaps
events = data['events']
for i in range(1, len(events)):
    if events[i]['sequence'] != events[i-1]['sequence'] + 1:
        print(f"Gap detected at sequence {events[i-1]['sequence']}")
```

### Scenario 3: Performance Issues

**Step 1**: Check system health
```bash
curl http://localhost:5050/api/health/detailed
```

**Step 2**: Review slow requests
```bash
curl "http://localhost:5050/api/debug/logs?search=slow_request&since_minutes=30"
```

**Step 3**: Check room statistics
```bash
curl http://localhost:5050/api/debug/room-stats
```

**Step 4**: Monitor WebSocket connections
```bash
curl http://localhost:5050/api/system/stats
```

### Scenario 4: WebSocket Connection Issues

**Step 1**: Check connection logs
```bash
curl "http://localhost:5050/api/debug/logs?logger_filter=ws&since_minutes=5"
```

**Step 2**: Review player reconnections
```bash
curl http://localhost:5050/api/debug/player-activity/ROOM123 | jq '.players[].reconnect_count'
```

**Step 3**: Check message queues
```bash
curl http://localhost:5050/api/debug/player-activity/ROOM123 | jq '.players[].message_queue_size'
```

## Log Analysis Patterns

### 1. Structured Log Format

Logs use JSON format for easy parsing:

```json
{
  "timestamp": "2024-01-09T10:30:45.123Z",
  "level": "ERROR",
  "logger": "backend.api.routes.ws",
  "message": "WebSocket error",
  "extra": {
    "event": "websocket_error",
    "room_id": "ROOM123",
    "player_id": "Player1",
    "error": "Connection timeout"
  }
}
```

### 2. Common Log Queries

```bash
# Find all errors for a specific room
curl "http://localhost:5050/api/debug/logs?search=ROOM123&level=ERROR"

# Find authentication failures
curl "http://localhost:5050/api/debug/logs?search=auth_failed"

# Find slow database queries
curl "http://localhost:5050/api/debug/logs?search=slow_query"

# Find WebSocket disconnections
curl "http://localhost:5050/api/debug/logs?search=websocket_disconnect"
```

### 3. Log Correlation

Correlate logs with events:

```python
# Get logs and events for same time period
import requests
from datetime import datetime, timedelta

room_id = "ROOM123"
time_window = datetime.now() - timedelta(minutes=10)

# Get logs
logs = requests.get(
    f"http://localhost:5050/api/debug/logs?search={room_id}&since_minutes=10"
).json()

# Get events
events = requests.get(
    f"http://localhost:5050/api/debug/events/{room_id}?limit=100"
).json()

# Correlate by timestamp
for log in logs['data']:
    log_time = datetime.fromisoformat(log['timestamp'])
    related_events = [
        e for e in events['events']
        if abs((datetime.fromisoformat(e['timestamp']) - log_time).total_seconds()) < 1
    ]
    if related_events:
        print(f"Log: {log['message']}")
        print(f"Related events: {[e['event_type'] for e in related_events]}")
```

## Production Monitoring Setup

### 1. Health Check Monitoring

```bash
# Basic health check
curl http://localhost:5050/api/health

# Detailed health check
curl http://localhost:5050/api/health/detailed

# Performance metrics
curl http://localhost:5050/api/health/performance
```

### 2. Automated Monitoring Script

```python
#!/usr/bin/env python3
import requests
import time
import logging

def monitor_production():
    while True:
        try:
            # Check health
            health = requests.get("http://localhost:5050/api/health/detailed").json()
            
            if not health['healthy']:
                logging.error(f"Unhealthy: {health['checks']}")
                
            # Check for hangs
            hangs = requests.get("http://localhost:5050/api/debug/hang-diagnostics").json()
            
            if hangs['total'] > 0:
                logging.warning(f"Active hangs: {hangs['total']}")
                
            # Check error rate
            logs = requests.get(
                "http://localhost:5050/api/debug/logs/stats"
            ).json()
            
            error_rate = logs['data']['level_counts'].get('ERROR', 0) / logs['data']['total_entries']
            if error_rate > 0.05:  # 5% error rate
                logging.error(f"High error rate: {error_rate:.1%}")
                
        except Exception as e:
            logging.error(f"Monitor error: {e}")
            
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    monitor_production()
```

### 3. Alert Configuration

Set up alerts for critical issues:

```yaml
# alerts.yaml
alerts:
  - name: high_error_rate
    condition: error_rate > 0.05
    window: 5m
    action: page_oncall
    
  - name: player_hangs
    condition: hang_count > 5
    window: 1m
    action: notify_team
    
  - name: event_store_failure
    condition: event_store_healthy == false
    window: 30s
    action: page_oncall
```

## Emergency Procedures

### 1. Mass Player Disconnect

```bash
# Check all rooms
curl http://localhost:5050/api/debug/room-stats

# Force refresh all connections
python scripts/emergency_refresh.py --all-rooms

# Clear stuck connections
curl -X POST http://localhost:5050/api/recovery/clear-stuck-connections
```

### 2. Database Issues

```bash
# Check event store health
curl http://localhost:5050/api/debug/stats

# Validate all rooms
for room in $(curl http://localhost:5050/api/rooms | jq -r '.[].room_id'); do
    curl http://localhost:5050/api/debug/validate/$room
done

# Emergency cleanup
curl -X POST "http://localhost:5050/api/debug/cleanup?older_than_hours=1"
```

### 3. Memory Leak

```bash
# Check memory usage
curl http://localhost:5050/api/health/metrics | jq '.memory'

# Dump heap profile
curl -X POST http://localhost:5050/api/debug/heap-dump

# Force garbage collection
curl -X POST http://localhost:5050/api/debug/gc

# Restart with memory limit
docker restart liap-tui --memory="1g"
```

### 4. Performance Degradation

```bash
# Enable profiling
curl -X POST http://localhost:5050/api/debug/profile/start

# Wait 30 seconds
sleep 30

# Stop and get results
curl -X POST http://localhost:5050/api/debug/profile/stop > profile.json

# Analyze profile
python scripts/analyze_profile.py profile.json
```

## Production Access Controls

### Authentication

All debug endpoints require authentication in production:

```bash
# Set auth token
export DEBUG_TOKEN="your-secure-token"

# Use with curl
curl -H "Authorization: Bearer $DEBUG_TOKEN" \
     http://localhost:5050/api/debug/events/ROOM123
```

### Rate Limiting

Debug endpoints have rate limits:
- 100 requests per minute per IP
- 1000 requests per hour per IP
- Bypass with admin token

### Audit Logging

All debug access is logged:

```bash
# View debug access logs
curl "http://localhost:5050/api/debug/logs?logger_filter=debug.access"
```

## Best Practices

### 1. Non-Invasive Debugging

Always use read-only operations first:
- Check logs and events
- Review metrics
- Analyze state
- Only modify if necessary

### 2. Document Actions

When debugging production:
1. Record initial symptoms
2. Document each action taken
3. Note findings
4. Create incident report

### 3. Gradual Escalation

Follow escalation path:
1. Read-only investigation
2. Targeted diagnostics
3. Isolated fixes
4. System-wide changes (last resort)

### 4. Testing Fixes

Before applying production fixes:
1. Reproduce in staging
2. Test fix in staging
3. Verify no side effects
4. Apply to production
5. Monitor results

## Troubleshooting Checklist

### Initial Investigation
- [ ] Check system health
- [ ] Review error logs
- [ ] Check player activity
- [ ] Validate event sequences
- [ ] Review recent deployments

### Deep Dive
- [ ] Export room history
- [ ] Analyze event patterns
- [ ] Check resource usage
- [ ] Review network logs
- [ ] Profile performance

### Resolution
- [ ] Identify root cause
- [ ] Document findings
- [ ] Test fix in staging
- [ ] Apply fix
- [ ] Monitor results
- [ ] Create incident report

## Tools and Scripts

### Log Analysis Tool

```python
#!/usr/bin/env python3
# scripts/analyze_logs.py

import requests
import json
from collections import Counter

def analyze_logs(since_minutes=60):
    response = requests.get(
        f"http://localhost:5050/api/debug/logs?since_minutes={since_minutes}&limit=1000"
    )
    logs = response.json()['data']
    
    # Analyze patterns
    error_types = Counter()
    error_rooms = Counter()
    
    for log in logs:
        if log['level'] == 'ERROR':
            error_types[log['message']] += 1
            if 'room_id' in log.get('extra', {}):
                error_rooms[log['extra']['room_id']] += 1
    
    print(f"Top errors: {error_types.most_common(5)}")
    print(f"Rooms with errors: {error_rooms.most_common(5)}")

if __name__ == "__main__":
    analyze_logs()
```

### Event Validator

```python
#!/usr/bin/env python3
# scripts/validate_events.py

import requests

def validate_room(room_id):
    # Get validation
    validation = requests.get(
        f"http://localhost:5050/api/debug/validate/{room_id}"
    ).json()
    
    if not validation['valid']:
        print(f"Room {room_id} has issues:")
        print(f"  Missing sequences: {validation.get('gaps', [])}")
        print(f"  Duplicates: {validation.get('diagnostics', {}).get('duplicate_sequences', {})}")
        
        # Get problematic events
        events = requests.get(
            f"http://localhost:5050/api/debug/events/{room_id}"
        ).json()
        
        # Analyze
        print("\nEvent analysis:")
        # Add analysis logic
        
    return validation['valid']

if __name__ == "__main__":
    import sys
    room_id = sys.argv[1] if len(sys.argv) > 1 else "ROOM123"
    validate_room(room_id)
```

## Conclusion

Effective production debugging requires:
1. Comprehensive monitoring
2. Structured logging
3. Non-invasive tools
4. Clear procedures
5. Proper documentation

Use these tools and procedures to quickly identify and resolve production issues while minimizing impact on players.