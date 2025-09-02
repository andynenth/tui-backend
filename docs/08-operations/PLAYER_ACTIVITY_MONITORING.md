# Player Activity Monitoring Guide

## Overview

The Player Activity Monitoring system tracks player connectivity, activity patterns, and automatically detects hang situations. It provides real-time visibility into player states and comprehensive diagnostic data for troubleshooting connection issues.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Frontend Client │     │ Activity Tracker │     │ Diagnostic Data │
├─────────────────┤     ├──────────────────┤     ├─────────────────┤
│ • Heartbeats    │────►│ • Track Activity │────►│ • Hang Reports  │
│ • UI State      │     │ • Detect Hangs   │     │ • Debug Buffer  │
│ • Actions       │     │ • Bot Takeover   │     │ • Metrics       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │ Debug Endpoints  │
                        │ /debug/activity  │
                        └──────────────────┘
```

## Core Components

### 1. Player Activity Tracker (`backend/api/services/player_activity_tracker.py`)

Tracks player activity and detects hang situations.

#### Data Structures

```python
@dataclass
class PlayerActivity:
    """Represents a player's activity state"""
    player_id: str
    room_id: str
    last_heartbeat: float
    last_action: float
    last_action_type: str
    heartbeat_data: dict
    action_history: deque  # Last 50 actions
    
    def is_active(self) -> bool:
        """Check if player is considered active"""
        return (time.time() - self.last_heartbeat) < 90  # 90 seconds
```

```python
@dataclass
class HangDiagnostic:
    """Diagnostic information about a detected hang"""
    player_id: str
    room_id: str
    hang_type: str
    duration_seconds: float
    
    # Context data
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

### 2. Heartbeat System

Enhanced heartbeats carry diagnostic data from client to server.

#### Client-Side Heartbeat

```typescript
// frontend/src/services/NetworkService.ts
private async sendHeartbeat(roomId: string): Promise<void> {
    const gameState = this.getGameStateSnapshot();
    const activityData = {
        timestamp: Date.now(),
        last_user_action: this.lastUserAction,
        current_phase: gameState.phase,
        ui_state: gameState.uiState,
        pending_actions: gameState.pendingActions,
        message_queue_size: this.getQueueSize(roomId),
        memory_usage: performance.memory?.usedJSHeapSize,
    };
    
    this.send(roomId, 'heartbeat', activityData);
}
```

#### Server-Side Handler

```python
async def handle_heartbeat(websocket, room_id, player_name, data):
    """Enhanced heartbeat handler with activity tracking"""
    activity_tracker.record_heartbeat(room_id, player_name, {
        'timestamp': data.get('timestamp'),
        'last_action': data.get('last_user_action'),
        'phase': data.get('current_phase'),
        'ui_state': data.get('ui_state'),
        'client_memory': data.get('memory_usage'),
        'queue_size': data.get('message_queue_size')
    })
```

### 3. Activity Detection

#### Active Player Criteria

- Heartbeat received within 90 seconds
- WebSocket connection alive
- No pending timeout warnings

#### Hang Detection Types

1. **Heartbeat Timeout**
   - No heartbeat for >90 seconds
   - Connection still open
   - Indicates client freeze

2. **Action Timeout**
   - Expected action not received
   - Player's turn stuck
   - Other players waiting

3. **State Mismatch**
   - Client/server phase mismatch
   - Indicates sync issues

## Bot Takeover System

### Idle Detection

```python
IDLE_TIMEOUT = 60  # seconds
TAKEOVER_GRACE_PERIOD = 30  # additional seconds

def check_idle_players(self):
    """Check for idle players and initiate bot takeover"""
    current_time = time.time()
    
    for room_id, players in self.activities.items():
        for player_name, activity in players.items():
            idle_duration = current_time - activity.last_action
            
            if idle_duration > IDLE_TIMEOUT:
                if not activity.takeover_initiated:
                    self.initiate_takeover(room_id, player_name)
```

### Takeover Process

1. **Detection**: Player idle for 60 seconds
2. **Warning**: Send takeover warning to player
3. **Grace Period**: 30 seconds to respond
4. **Takeover**: Bot assumes control
5. **Restoration**: Player can reclaim control

#### Implementation

```python
async def initiate_takeover(self, room_id: str, player_name: str):
    """Initiate bot takeover for idle player"""
    # Send warning to player
    await broadcast(room_id, "takeover_warning", {
        "player": player_name,
        "grace_period": TAKEOVER_GRACE_PERIOD,
        "reason": "idle_timeout"
    })
    
    # Schedule takeover
    asyncio.create_task(
        self._execute_takeover_after_grace(room_id, player_name)
    )

async def _execute_takeover_after_grace(self, room_id, player_name):
    """Execute takeover after grace period"""
    await asyncio.sleep(TAKEOVER_GRACE_PERIOD)
    
    # Check if player became active
    if self.is_player_active(room_id, player_name):
        return
    
    # Execute takeover
    await self.bot_manager.takeover_player(room_id, player_name)
```

## Diagnostic Endpoints

### GET `/debug/activity/{room_id}`

Get current activity status for a room.

```json
{
    "room_id": "abc123",
    "players": {
        "Player1": {
            "status": "active",
            "last_heartbeat": "2025-09-02T10:30:00Z",
            "last_action": "2025-09-02T10:29:45Z",
            "heartbeat_lag_ms": 234,
            "is_bot": false
        },
        "Player2": {
            "status": "idle",
            "idle_duration_seconds": 75,
            "takeover_warning_sent": true,
            "grace_period_remaining": 15
        }
    }
}
```

### GET `/debug/hangs`

Get recent hang diagnostics.

```json
{
    "hangs": [
        {
            "player_id": "Player3",
            "room_id": "xyz789",
            "hang_type": "heartbeat_timeout",
            "duration_seconds": 120,
            "game_phase": "TURN",
            "last_actions": ["play", "draw"],
            "client_ui_state": {
                "view": "game_board",
                "modal": null
            }
        }
    ]
}
```

### POST `/debug/activity/simulate-hang`

Simulate a hang for testing.

```json
{
    "room_id": "test123",
    "player_name": "TestPlayer",
    "hang_type": "heartbeat_timeout"
}
```

## Monitoring Integration

### Metrics Collected

1. **Activity Metrics**
   - Active players per room
   - Average heartbeat lag
   - Idle player count
   - Bot takeover rate

2. **Hang Metrics**
   - Hang frequency by type
   - Average hang duration
   - Recovery success rate
   - Affected player percentage

### Alert Triggers

```python
# High idle rate alert
if idle_player_percentage > 0.2:  # 20%
    alert("High idle player rate", severity="warning")

# Frequent hangs alert
if hangs_per_hour > 5:
    alert("Frequent player hangs detected", severity="critical")
```

## Troubleshooting Guide

### Common Issues

#### 1. False Idle Detection

**Symptoms**: Active player marked as idle  
**Causes**: 
- Network latency
- Client-side performance issues
- Clock synchronization

**Solution**:
```python
# Increase tolerance
IDLE_TIMEOUT = 90  # Increase from 60
HEARTBEAT_INTERVAL = 20  # Decrease from 30
```

#### 2. Takeover During Active Play

**Symptoms**: Bot takes over during player's turn  
**Causes**:
- Heartbeat not sent
- Action not recorded
- Race condition

**Solution**:
```python
# Add action validation
if player.is_currently_playing():
    extend_idle_timeout(player, additional=30)
```

#### 3. Reconnection Issues

**Symptoms**: Player can't resume after reconnect  
**Causes**:
- Session state mismatch
- Bot already took over
- Authentication failure

**Solution**:
```python
# Graceful reconnection
if reconnecting_player.was_taken_over:
    await restore_player_control(player)
```

## Configuration

### Activity Tracker Settings

```python
# backend/config/activity.py
ACTIVITY_CONFIG = {
    # Timeouts (seconds)
    "heartbeat_interval": 30,
    "heartbeat_timeout": 90,
    "idle_timeout": 60,
    "takeover_grace_period": 30,
    
    # Detection
    "hang_detection_enabled": True,
    "auto_takeover_enabled": True,
    "takeover_min_players": 2,  # Don't takeover if <2 human players
    
    # Diagnostics
    "diagnostic_buffer_size": 100,
    "action_history_size": 50,
    
    # Performance
    "cleanup_interval": 300,  # Clean old data every 5 min
}
```

### Client Configuration

```typescript
// frontend/src/config/network.ts
export const NETWORK_CONFIG = {
    heartbeatInterval: 30000,  // 30 seconds
    heartbeatTimeout: 90000,   // 90 seconds
    reconnectDelay: 1000,      // 1 second
    maxReconnectAttempts: 5,
    includeMemoryStats: true,
    includePendingActions: true,
};
```

## Best Practices

### 1. Heartbeat Optimization

```typescript
// Batch heartbeats with other messages
if (this.pendingHeartbeat && this.hasQueuedMessages()) {
    this.flushMessageQueue();
    this.pendingHeartbeat = false;
}
```

### 2. Activity Recording

```python
# Record all significant actions
TRACKED_ACTIONS = [
    "play", "draw", "declare", "pass",
    "chat", "emoji", "settings_change"
]

# But ignore noise
IGNORED_ACTIONS = [
    "mouse_move", "hover", "scroll"
]
```

### 3. Diagnostic Data

```python
# Include context in diagnostics
diagnostic = HangDiagnostic(
    player_id=player_id,
    room_id=room_id,
    hang_type=hang_type,
    # Include game context
    game_phase=game.current_phase,
    expected_action=game.waiting_for,
    other_players_waiting=game.blocked_players
)
```

## Testing

### Manual Testing

1. **Simulate Idle Player**
   ```bash
   # Open game, don't interact for 60+ seconds
   # Verify takeover warning appears
   # Verify bot takes over after grace period
   ```

2. **Test Reconnection**
   ```bash
   # Disconnect network
   # Wait for timeout
   # Reconnect and verify state restoration
   ```

### Automated Testing

```python
# test_player_activity_monitor.py
async def test_idle_detection():
    tracker = PlayerActivityTracker()
    
    # Simulate player activity
    tracker.record_action("room1", "player1", "play")
    
    # Fast-forward time
    with mock.patch('time.time', return_value=time.time() + 70):
        idle_players = tracker.get_idle_players()
        assert "player1" in idle_players
```

## Future Enhancements

1. **Machine Learning**: Predict hangs before they occur
2. **Client Diagnostics**: Browser performance metrics
3. **Network Analysis**: Packet loss detection
4. **Smart Takeover**: AI difficulty adjustment
5. **Recovery Strategies**: Automatic state repair