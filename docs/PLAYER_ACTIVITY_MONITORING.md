# Player Activity Monitoring Guide

## Executive Summary

The Player Activity Monitor is a comprehensive system for tracking player behavior, detecting hang situations, and capturing diagnostic data to resolve "frozen game" issues. This guide consolidates information from the existing implementation and documentation.

### Key Features
- Real-time player activity tracking
- Automatic hang detection with diagnostic snapshots
- Enhanced heartbeat system with client state
- Debug endpoints for investigation
- WebSocket monitoring interface

## System Architecture

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   Frontend Client   │     │   Backend Server    │     │  Monitoring Store   │
├─────────────────────┤     ├─────────────────────┤     ├─────────────────────┤
│ • Enhanced Heartbeat│ ──> │ • Activity Tracker  │ ──> │ • Circular Buffer   │
│ • State Snapshots  │     │ • Hang Detector     │     │ • Debug Endpoints   │
│ • Error Context    │     │ • Event Correlation │     │ • Alert System      │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
```

## Core Components

### 1. PlayerActivityTracker

Central service that tracks all player activities:

```python
# backend/api/services/player_activity_tracker.py

@dataclass
class PlayerActivity:
    player_id: str
    room_id: str
    last_heartbeat: float
    last_action: float
    last_action_type: str
    heartbeat_data: dict
    action_history: deque  # Last 50 actions
    
    def is_active(self) -> bool:
        """Check if player is considered active"""
        return time.time() - self.last_heartbeat < 90

class PlayerActivityTracker:
    def __init__(self):
        self.activities: Dict[str, Dict[str, PlayerActivity]] = {}
        self.hang_detections = []
        self.diagnostic_buffer = deque(maxlen=100)
```

### 2. Enhanced Heartbeat System

Client sends diagnostic data with each heartbeat:

```javascript
// frontend/src/services/NetworkService.ts
private collectDiagnosticData(): DiagnosticData {
  return {
    timestamp: Date.now(),
    last_user_action: this.lastUserAction,
    game_context: {
      phase: gameContext?.phase,
      is_my_turn: gameContext?.isMyTurn,
      waiting_for: gameContext?.waitingFor,
    },
    ui_state: {
      current_view: uiState?.currentView,
      blocked_by: uiState?.blockedBy,
    },
    performance: {
      memory_mb: performance.memory?.usedJSHeapSize / 1048576,
    },
  };
}
```

### 3. Hang Detection Engine

Automatically detects various hang scenarios:

```python
# backend/api/services/hang_detector.py

HANG_THRESHOLDS = {
    'no_heartbeat': 90,       # seconds
    'waiting_for_action': 60, # seconds  
    'message_queue_full': 50, # messages
    'repeated_reconnects': 3, # within 5 minutes
}
```

### 4. Diagnostic Snapshots

Comprehensive data captured when hang detected:

```python
@dataclass
class HangDiagnostic:
    # Player info
    player_id: str
    room_id: str
    hang_type: str
    duration_seconds: float
    
    # Game state
    game_phase: str
    last_actions: List[dict]
    pending_actions: List[str]
    
    # Network state
    connection_status: str
    message_queue_size: int
    last_heartbeat_delta: float
    
    # Client state
    client_ui_state: dict
    client_memory_mb: float
```

## API Endpoints

### 1. Player Activity Status

Get current activity for all players in a room:

```bash
GET /api/debug/player-activity/{room_id}
```

Response:
```json
{
  "room_id": "ABC123",
  "timestamp": 1704816000.123,
  "players": [
    {
      "name": "Player1",
      "status": "active",
      "last_heartbeat": 1704815970.0,
      "last_action": 1704815950.0,
      "last_action_type": "play",
      "heartbeat_lag": 30.123,
      "action_lag": 50.123,
      "connection_health": "good",
      "recent_actions": ["declare", "play", "play"],
      "game_state": {
        "phase": "TURN",
        "is_my_turn": true,
        "waiting_for": "play_action"
      }
    }
  ],
  "hang_detections": []
}
```

### 2. Hang Diagnostics

Retrieve diagnostic snapshots:

```bash
GET /api/debug/hang-diagnostics?limit=20&hang_type=no_heartbeat
```

Response includes detailed diagnostic data for troubleshooting.

### 3. Real-Time Monitoring

WebSocket endpoint for live monitoring:

```bash
WS /api/debug/ws/activity-monitor
```

Sends updates every 5 seconds with aggregate statistics.

## Common Hang Scenarios

### 1. No Heartbeat Hang

**Symptoms**: No heartbeat for >90 seconds

**Common Causes**:
- JavaScript error blocking event loop
- Browser tab suspended
- Network connection lost
- Client crash

**Diagnosis**:
```python
# Check in activity data
if player['heartbeat_lag'] > 90:
    # No heartbeat hang confirmed
```

### 2. Waiting for Action Hang

**Symptoms**: Player hasn't acted for >60 seconds when required

**Common Causes**:
- UI not showing action prompt
- WebSocket message not received
- State synchronization issue
- Bot activation failure

**Diagnosis**:
```python
# Check pending actions
if player['game_state']['is_my_turn'] and player['action_lag'] > 60:
    # Waiting for action hang
```

### 3. Message Queue Hang

**Symptoms**: High message queue size

**Common Causes**:
- Client not processing messages
- Network congestion
- Processing bottleneck

**Diagnosis**:
```python
if diagnostic['message_queue_size'] > 10:
    # Message processing issue
```

## Usage Examples

### Investigating a Frozen Game

1. **Check Current Status**:
```bash
curl http://localhost:5050/api/debug/player-activity/ROOM123
```

2. **Look for Inactive Players**:
- Check `status` field
- Review `heartbeat_lag` 
- Check `pending_actions`

3. **Get Diagnostic Details**:
```bash
curl http://localhost:5050/api/debug/hang-diagnostics?player_id=Player1
```

4. **Review Diagnostic Snapshot**:
- Compare client vs server state
- Check message queue
- Review recent actions

### Monitoring Production

Set up automated monitoring:

```python
import requests
import time

def monitor_activity(room_id: str):
    while True:
        response = requests.get(
            f"http://localhost:5050/api/debug/player-activity/{room_id}"
        )
        data = response.json()
        
        for player in data['players']:
            if player['status'] == 'inactive':
                alert(f"Player {player['name']} inactive: "
                     f"{player['heartbeat_lag']}s since heartbeat")
                     
        time.sleep(10)
```

### Real-Time Dashboard

Connect to WebSocket for live updates:

```javascript
const ws = new WebSocket('ws://localhost:5050/api/debug/ws/activity-monitor');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Active: ${data.active_players}, Hangs: ${data.active_hangs}`);
};
```

## Alert Configuration

Configure alerts for hang detection:

```yaml
# monitoring_config.yaml
activity_monitor:
  alerts:
    player_hang:
      threshold: 2        # concurrent hangs
      duration: 60        # seconds
      action: notify_ops
      
    mass_disconnect:
      threshold: 5        # players
      duration: 30        # seconds
      action: escalate
```

## Performance Impact

Minimal overhead:
- Heartbeat size: +300 bytes
- Processing time: +1ms
- Memory per player: +4KB
- Storage: 10MB/day diagnostic buffer

## Troubleshooting Patterns

### Pattern 1: Heartbeat Active but No Actions

**Indicates**: UI state mismatch

**Solution**:
```python
# Force state refresh
await broadcast_phase_change(room_id, force_refresh=True)
```

### Pattern 2: Repeated Reconnections

**Indicates**: Network instability

**Solution**:
- Check WebSocket proxy configuration
- Increase reconnection timeout
- Review network logs

### Pattern 3: High Message Queue

**Indicates**: Client processing issue

**Solution**:
```javascript
// Clear and reprocess queue
networkService.clearMessageQueue(roomId);
networkService.requestStateRefresh();
```

## Integration Points

### With Game State Machine

Activity tracking integrated into state transitions:

```python
# backend/engine/state_machine/base_state.py
async def process_action(self, action: GameAction):
    # Track action
    activity_tracker.record_action(
        self.game.room_id,
        action.player_id,
        action.action_type.value
    )
    
    # Process action
    result = await self._process_action_impl(action)
    return result
```

### With WebSocket Handler

Enhanced heartbeat handling:

```python
# backend/api/routes/ws.py
async def handle_heartbeat(websocket, room_id, player_name, data):
    # Record enhanced heartbeat
    activity_tracker.record_heartbeat(room_id, player_name, data)
    
    # Send pong
    await websocket.send_json({
        'event': 'pong',
        'data': {'timestamp': data.get('timestamp')}
    })
```

## Best Practices

### 1. Proactive Monitoring

- Set up alerts for early detection
- Monitor trends, not just thresholds
- Review diagnostics regularly

### 2. Client Integration

Ensure client sends complete diagnostic data:

```javascript
// Include all relevant state
const diagnosticData = {
  game_context: {...},
  ui_state: {...},
  performance: {...},
  network_state: {...}
};
```

### 3. Debug Workflow

Standard investigation process:

1. Check activity status
2. Review hang diagnostics
3. Compare client vs server state
4. Check network conditions
5. Review recent actions
6. Apply appropriate fix

### 4. Data Retention

- Activity data: 24 hours
- Diagnostic snapshots: 7 days
- Aggregated metrics: 30 days

## Emergency Procedures

### Mass Hang Event

```bash
# 1. Check all rooms
curl http://localhost:5050/api/debug/hang-diagnostics?limit=100

# 2. Force refresh all
python scripts/emergency_refresh.py --all-rooms

# 3. Clear diagnostic buffer if full
curl -X POST http://localhost:5050/api/debug/clear-diagnostics
```

### Disable Monitoring

If monitoring causes issues:

```bash
# Temporarily disable
curl -X POST http://localhost:5050/api/debug/disable-activity-tracking

# Re-enable when fixed
curl -X POST http://localhost:5050/api/debug/enable-activity-tracking
```

## Metrics and KPIs

Key metrics to track:

1. **Active Player Ratio**: >95% target
2. **Average Heartbeat Lag**: <35s target
3. **Hang Detection Rate**: <1% target
4. **Message Queue Health**: 0 players >10 messages

## Future Enhancements

1. **Machine Learning**: Predict hangs before they occur
2. **Auto-Recovery**: Automatic state refresh on detection
3. **Client Diagnostics**: Browser-side error collection
4. **Trend Analysis**: Historical pattern recognition

## Quick Reference

### Essential Commands

```bash
# Check player activity
curl http://localhost:5050/api/debug/player-activity/{room_id}

# Get hang diagnostics
curl http://localhost:5050/api/debug/hang-diagnostics

# Monitor real-time
wscat -c ws://localhost:5050/api/debug/ws/activity-monitor

# Force refresh
curl -X POST http://localhost:5050/api/debug/force-refresh/{room_id}
```

### Key Thresholds

- No Heartbeat: 90 seconds
- Action Timeout: 60 seconds
- Queue Warning: 10 messages
- Reconnect Limit: 3 in 5 minutes

### Support Escalation

- Level 1: Check activity status
- Level 2: Review diagnostics
- Level 3: Engineering team
- Critical: On-call engineer