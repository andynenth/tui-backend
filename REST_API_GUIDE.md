# REST API Guide for Liap Tui

This guide explains the remaining REST endpoints in the Liap Tui backend after the WebSocket migration. These endpoints are used for monitoring, debugging, and administrative purposes only. All game operations use WebSocket.

## Important Note: API Prefix

⚠️ **All REST endpoints require the `/api` prefix** because they're mounted under `/api/` in the FastAPI application.

## Table of Contents
1. [Health Monitoring](#health-monitoring)
2. [Debug and Admin Tools](#debug-and-admin-tools)
3. [Event Store Management](#event-store-management)
4. [Recovery System](#recovery-system)
5. [System Statistics](#system-statistics)

---

## Health Monitoring

### 1. Basic Health Check - `/api/health`

**Purpose**: Quick health check for load balancers and uptime monitoring.

**Command**:
```bash
curl "http://localhost:5050/api/health"
```

**Expected Response**:
```json
{
    "status": "healthy",
    "timestamp": 1736963245.789,
    "uptime_seconds": 3847,
    "uptime_formatted": "1h 4m 7s",
    "version": "1.0.0",
    "service": "liap-tui-backend"
}
```

**What it means**:
- `status`: "healthy" = good, "warning" = degraded, "critical" = failing
- `uptime_seconds`: How long the server has been running
- `uptime_formatted`: Human-readable uptime

**Use cases**:
- Load balancer health checks
- Monitoring dashboards
- Quick server status check

### 2. Detailed Health Check - `/api/health/detailed`

**Purpose**: Comprehensive health information including system resources and component status.

**Note**: This endpoint may return 500 error if health monitoring components are not fully initialized. This is a known issue.

**Command**:
```bash
curl "http://localhost:5050/api/health/detailed"
```

**Expected Response**:
```json
{
    "success": true,
    "health": {
        "status": "healthy",
        "timestamp": 1736963245.789,
        "uptime_seconds": 3847,
        "components": {
            "websocket": {
                "status": "healthy",
                "connections": 12,
                "message_queue_size": 0
            },
            "room_manager": {
                "status": "healthy",
                "active_rooms": 3,
                "total_players": 11
            },
            "event_store": {
                "status": "healthy",
                "event_count": 1523,
                "latest_event": "2025-01-15T10:32:15Z"
            }
        },
        "metrics": {
            "memory": {
                "name": "memory",
                "value": 42.3,
                "threshold": 90,
                "unit": "%"
            },
            "cpu": {
                "name": "cpu",
                "value": 18.5,
                "threshold": 80,
                "unit": "%"
            },
            "disk": {
                "name": "disk",
                "value": 67.2,
                "threshold": 90,
                "unit": "%"
            }
        },
        "active_connections": 12,
        "active_rooms": 3,
        "total_games_played": 47
    },
    "components": {
        "event_store": true,
        "health_monitor": true,
        "recovery_manager": true,
        "websocket_manager": true,
        "room_manager": true
    }
}
```

**What it means**:
- `components`: Status of each major system component
- `metrics`: System resource usage (memory, CPU, disk)
- `active_connections`: Current WebSocket connections
- `active_rooms`: Rooms with active games

**Use cases**:
- Debugging performance issues
- Monitoring system resources
- Checking component health

### 3. Prometheus Metrics - `/api/health/metrics`

**Purpose**: Metrics in Prometheus format for monitoring systems.

**Command**:
```bash
curl "http://localhost:5050/api/health/metrics"
```

**Expected Response** (Plain text):
```
liap_memory_usage_percent 42.3
liap_cpu_usage_percent 18.5
liap_disk_usage_percent 67.2
liap_websocket_connections_total 12
liap_websocket_pending_messages_total 0
liap_rooms_total 3
liap_active_games_total 3
liap_health_status 0
liap_uptime_seconds 3847
liap_messages_sent_total 4523
liap_messages_acknowledged_total 4520
liap_messages_failed_total 3
liap_message_success_rate_percent 99.93
liap_metrics_generated_timestamp 1736963245.789
```

**What it means**:
- Each line is a metric in format: `metric_name value`
- `health_status`: 0=healthy, 1=warning, 2=critical, 3=unknown
- `message_success_rate_percent`: Reliability of WebSocket messages

**Use cases**:
- Prometheus/Grafana integration
- Automated monitoring alerts
- Performance tracking

---

## Debug and Admin Tools

### 4. Room Statistics - `/api/debug/room-stats`

**Purpose**: Debug information about rooms and WebSocket connections.

**Command** (All rooms):
```bash
curl "http://localhost:5050/api/debug/room-stats"
```

**Command** (Specific room):
```bash
curl "http://localhost:5050/api/debug/room-stats?room_id=1BDD98"
```

**Expected Response**:
```json
{
    "timestamp": 1736963245.789,
    "stats": {
        "total_connections": 12,
        "room_connections": {
            "lobby": 3,
            "1BDD98": 4,
            "2XYZ45": 3,
            "3ABC67": 2
        },
        "pending_messages": {
            "1BDD98": 0,
            "2XYZ45": 2
        },
        "room_validation": {
            "valid": true,
            "errors": [],
            "warnings": []
        },
        "room_summary": {
            "room_id": "1BDD98",
            "host_name": "Alice",
            "players": ["Alice", "Bob", "Bot 3", "Bot 4"],
            "game_started": true,
            "current_phase": "TURN",
            "round_number": 3,
            "turn_number": 15,
            "current_player": "Bob",
            "scores": {
                "Alice": 23,
                "Bob": 18,
                "Bot 3": 31,
                "Bot 4": 12
            }
        }
    }
}
```

**What it means**:
- `room_connections`: Number of WebSocket connections per room
- `pending_messages`: Undelivered messages (should be 0 or low)
- `room_validation`: Checks if room state is valid
- `room_summary`: Current game state details

**Use cases**:
- Debugging connection issues
- Checking game state
- Monitoring message delivery

---

## Event Store Management

### 5. Event Store Statistics - `/api/event-store/stats`

**Purpose**: Monitor the event sourcing system.

**Command**:
```bash
curl "http://localhost:5050/api/event-store/stats"
```

**Expected Response**:
```json
{
    "success": true,
    "statistics": {
        "total_events": 15234,
        "rooms_with_events": 47,
        "average_events_per_room": 324,
        "oldest_event": "2025-01-14T08:15:23Z",
        "newest_event": "2025-01-15T11:45:02Z",
        "event_types": {
            "game_started": 47,
            "phase_change": 523,
            "player_action": 8234,
            "bot_action": 6430
        }
    },
    "health": {
        "status": "healthy",
        "storage_size_mb": 12.5,
        "write_performance_ms": 2.3,
        "read_performance_ms": 0.8
    },
    "features": {
        "event_persistence": true,
        "state_reconstruction": true,
        "client_recovery": true
    }
}
```

**What it means**:
- `total_events`: Total events stored
- `event_types`: Breakdown by type
- `storage_size_mb`: Disk usage
- Performance metrics for writes/reads

**Use cases**:
- Monitor event store growth
- Check performance
- Plan cleanup schedules

### 6. Room Events - `/api/rooms/{room_id}/events`

**Purpose**: View all events for a specific room (debugging).

**Command**:
```bash
curl "http://localhost:5050/api/rooms/1BDD98/events?limit=10"
```

**Expected Response**:
```json
{
    "success": true,
    "room_id": "1BDD98",
    "event_count": 10,
    "events": [
        {
            "sequence": 234,
            "event_type": "phase_change",
            "timestamp": "2025-01-15T11:23:45Z",
            "data": {
                "from_phase": "DECLARATION",
                "to_phase": "TURN",
                "reason": "All players declared"
            }
        },
        {
            "sequence": 235,
            "event_type": "player_action",
            "timestamp": "2025-01-15T11:24:01Z",
            "data": {
                "player": "Alice",
                "action": "play_pieces",
                "pieces": ["8♥", "8♠"],
                "result": "won_turn"
            }
        }
    ],
    "analysis": {
        "first_event": "2025-01-15T10:15:23Z",
        "last_event": "2025-01-15T11:24:01Z",
        "event_types": ["game_started", "phase_change", "player_action"]
    }
}
```

**What it means**:
- Each event shows what happened in the game
- `sequence`: Order of events
- Events can be replayed to reconstruct game state

**Use cases**:
- Debug game issues
- Analyze player behavior
- Verify game logic

### 7. Event Cleanup - `/api/event-store/cleanup`

**Purpose**: Remove old events to save space.

**Command** (Default: 24 hours):
```bash
curl -X POST "http://localhost:5050/api/event-store/cleanup"
```

**Command** (Custom: 48 hours):
```bash
curl -X POST "http://localhost:5050/api/event-store/cleanup?older_than_hours=48"
```

**Expected Response**:
```json
{
    "success": true,
    "deleted_events": 3847,
    "older_than_hours": 24,
    "cleanup_completed": true
}
```

**What it means**:
- `deleted_events`: Number of events removed
- Only completed game events are deleted

**Use cases**:
- Regular maintenance
- Free up disk space
- Remove old game data

---

## Recovery System

### 8. Recovery Status - `/api/recovery/status`

**Purpose**: Check the automatic recovery system.

**Command**:
```bash
curl "http://localhost:5050/api/recovery/status"
```

**Expected Response**:
```json
{
    "success": true,
    "recovery_system": {
        "enabled": true,
        "last_check": "2025-01-15T11:40:00Z",
        "recent_recoveries": [
            {
                "timestamp": "2025-01-15T09:15:23Z",
                "procedure": "restart_stuck_game",
                "room_id": "XYZ123",
                "success": true,
                "details": "Game stuck in TURN phase for 30 minutes"
            }
        ],
        "registered_procedures": [
            "restart_stuck_game",
            "cleanup_abandoned_rooms",
            "reconnect_dropped_players",
            "clear_message_queues"
        ],
        "health": {
            "status": "healthy",
            "checks_performed": 847,
            "recoveries_triggered": 3,
            "success_rate": 100.0
        }
    }
}
```

**What it means**:
- `recent_recoveries`: What recovery actions were taken
- `registered_procedures`: Available recovery procedures
- `success_rate`: How reliable the recovery system is

**Use cases**:
- Monitor automatic recovery
- Check recovery history
- Verify system self-healing

### 9. Trigger Recovery - `/api/recovery/trigger/{procedure}`

**Purpose**: Manually trigger a recovery procedure.

**Command**:
```bash
curl -X POST "http://localhost:5050/api/recovery/trigger/cleanup_abandoned_rooms" \
  -H "Content-Type: application/json" \
  -d '{"context": {"older_than_minutes": 60}}'
```

**Expected Response**:
```json
{
    "success": true,
    "procedure": "cleanup_abandoned_rooms",
    "context": {
        "older_than_minutes": 60
    },
    "triggered": true
}
```

**Available Procedures**:
- `restart_stuck_game`: Restart games stuck in a phase
- `cleanup_abandoned_rooms`: Remove empty/abandoned rooms
- `reconnect_dropped_players`: Attempt to reconnect players
- `clear_message_queues`: Clear stuck message queues

**Use cases**:
- Manual intervention for stuck games
- Scheduled maintenance
- Emergency recovery

---

## System Statistics

### 10. Comprehensive System Stats - `/api/system/stats`

**Purpose**: All system statistics in one call.

**Command**:
```bash
curl "http://localhost:5050/api/system/stats"
```

**Expected Response**:
```json
{
    "success": true,
    "timestamp": 1736963245.789,
    "health": {
        "status": "healthy",
        "uptime_seconds": 3847,
        "components": {
            "websocket": "healthy",
            "room_manager": "healthy",
            "event_store": "healthy"
        }
    },
    "recovery": {
        "enabled": true,
        "last_check": "2025-01-15T11:40:00Z",
        "recent_recoveries": 3
    },
    "websocket": {
        "total_connections": 12,
        "messages_sent": 4523,
        "messages_acknowledged": 4520,
        "messages_failed": 3,
        "success_rate": 99.93
    },
    "rooms": {
        "total_rooms": 3,
        "active_games": 3,
        "total_players": 11
    },
    "events": {
        "total_events": 15234,
        "rooms_with_events": 47,
        "storage_size_mb": 12.5
    }
}
```

**What it means**:
- Combines data from all other endpoints
- One-stop view of entire system
- Good for dashboards

**Use cases**:
- System overview dashboard
- Regular health checks
- Performance monitoring

---

## Common Issues and Solutions

### 404 Not Found
- **Cause**: Missing `/api` prefix
- **Solution**: Add `/api` before the endpoint path

### Connection Refused
- **Cause**: Server not running or wrong port
- **Solution**: Check server is running on port 5050

### Empty or Null Responses
- **Cause**: No data available (e.g., no rooms)
- **Solution**: Create some game activity first

### Slow Responses
- **Cause**: Large data sets or performance issues
- **Solution**: Use limit parameters, check system resources

---

## Testing the Endpoints

To verify all endpoints are working, run:
```bash
python test_rest_endpoints.py
```

This will test each endpoint and report any issues.