# Player Activity Monitor - Phased Implementation Plan

## Overview

This plan breaks down the Player Activity Monitor into 8 independent phases, each delivering immediate value while minimizing implementation risk. Each phase is self-contained and can be rolled back without affecting other phases.

## Phase 1: Enhanced Client Heartbeat (Priority: CRITICAL)
**Timeline**: 2-3 hours  
**Risk**: Very Low  
**Rollback**: Simple flag to disable

### What You Get:
- **Immediate visibility** into client state every 30 seconds
- See exactly what the player's UI shows vs what server thinks
- Detect client-side issues (frozen UI, JavaScript errors)
- **Directly helps debug your refresh bug** - you'll see client state before/after refresh

### Implementation:
```typescript
// NetworkService.ts - Add to existing heartbeat
heartbeatData = {
  timestamp: Date.now(),
  current_phase: gameState?.phase,
  ui_state: {
    view: currentView,
    waiting_for: waitingForAction,
    captured_piles: player?.capturedPiles,  // Key for refresh bug!
    declared: player?.declared              // Key for refresh bug!
  }
}
```

### Verification:
- Browser DevTools Network tab shows enhanced heartbeat payload
- Server logs show received heartbeat data
- No performance impact (only ~200 bytes added)

---

## Phase 2: Basic Activity Logging (Priority: HIGH)
**Timeline**: 2-3 hours  
**Risk**: Very Low  
**Rollback**: Comment out logging calls

### What You Get:
- **Track every player action** with timestamp
- See patterns of actions before hangs occur
- Identify duplicate or missing actions
- Simple server-side logging, no database needed

### Implementation:
```python
# ws.py - Add to existing event handlers
logger.info(f"ACTIVITY: {room_id}|{player_name}|{event_name}|{timestamp}")

# Specific for your issues:
# - Log when captured_piles changes
# - Log when player declares
# - Log when bot should act but doesn't
```

### Verification:
- Tail logs to see real-time activity
- grep logs for specific player/room
- Correlate with reported issues

---

## Phase 3: Current State Debug Endpoint (Priority: HIGH)
**Timeline**: 1-2 hours  
**Risk**: Very Low  
**Rollback**: Remove endpoint

### What You Get:
- **Instant snapshot** of any room's current state
- See all players' last heartbeat times
- Check if players are "alive" or "stale"
- No storage needed - just current in-memory state

### Implementation:
```python
@router.get("/api/debug/room-state/{room_id}")
async def get_room_state(room_id: str):
    return {
        "players": get_connected_players(room_id),
        "last_heartbeats": get_heartbeat_times(room_id),
        "game_phase": get_game_phase(room_id),
        "waiting_for": get_pending_actions(room_id)
    }
```

### Usage:
```bash
# When player reports issue:
curl http://localhost:5050/api/debug/room-state/room123
```

---

## Phase 4: Simple Hang Detection (Priority: HIGH)
**Timeline**: 3-4 hours  
**Risk**: Low  
**Rollback**: Disable detection flag

### What You Get:
- **Automatic detection** of stuck players
- Log warnings when:
  - No heartbeat for >90 seconds
  - Player hasn't acted for >60 seconds when action required
  - Bot hasn't responded to its turn
- Early warning system for issues

### Implementation:
```python
# Simple background task checking every 30 seconds
async def check_player_health():
    for room in active_rooms:
        for player in room.players:
            if time.now() - player.last_heartbeat > 90:
                logger.warning(f"HANG: No heartbeat from {player.name}")
            if player.pending_action and time.now() - player.last_action > 60:
                logger.warning(f"HANG: {player.name} not responding to {action}")
```

### Verification:
- See warnings in logs when issues occur
- Test by pausing browser debugger
- Catches bot hanging immediately

---

## Phase 5: Activity History Buffer (Priority: MEDIUM)
**Timeline**: 2-3 hours  
**Risk**: Low  
**Rollback**: Disable buffer

### What You Get:
- **Last 50 actions per player** stored in memory
- See sequence of events leading to issues
- Identify patterns in player behavior
- Critical for debugging intermittent issues

### Implementation:
```python
from collections import deque

player_activities = {}  # player_id -> deque(maxlen=50)

def record_activity(player_id, action, context):
    if player_id not in player_activities:
        player_activities[player_id] = deque(maxlen=50)
    
    player_activities[player_id].append({
        'timestamp': time.now(),
        'action': action,
        'context': context
    })
```

### New Endpoint:
```python
@router.get("/api/debug/player-history/{room_id}/{player_name}")
# Returns last 50 actions for debugging
```

---

## Phase 6: Diagnostic Snapshots (Priority: MEDIUM)
**Timeline**: 3-4 hours  
**Risk**: Low  
**Rollback**: Disable snapshot collection

### What You Get:
- **Full context capture** when hang detected
- Includes:
  - Player's recent actions
  - Current game state
  - Client UI state (from heartbeat)
  - Server state
  - Network metrics
- Store last 100 snapshots in circular buffer

### Implementation:
```python
@dataclass
class HangSnapshot:
    player_id: str
    hang_type: str
    game_state: dict
    client_state: dict  # From last heartbeat
    recent_actions: list  # From activity buffer
    timestamp: float
    
diagnostic_buffer = deque(maxlen=100)
```

### Usage:
- Automatic capture when hang detected
- Query endpoint to retrieve snapshots
- Contains everything needed to debug

---

## Phase 7: Real-time Monitoring WebSocket (Priority: LOW)
**Timeline**: 2-3 hours  
**Risk**: Low  
**Rollback**: Close WebSocket endpoint

### What You Get:
- **Live dashboard** of all player activity
- Watch issues happen in real-time
- See patterns across multiple rooms
- Useful for catching intermittent issues

### Implementation:
```python
@router.websocket("/api/debug/ws/monitor")
async def monitor_websocket(websocket: WebSocket):
    # Send updates every 5 seconds
    # Show active/inactive players
    # Show recent hangs
    # Show activity rates
```

### Usage:
- Open in browser for live monitoring
- Watch during testing
- Leave open to catch issues

---

## Phase 8: Alerts and Metrics (Priority: LOW)
**Timeline**: 4-5 hours  
**Risk**: Medium  
**Rollback**: Disable alerting

### What You Get:
- **Proactive notifications** of issues
- Metrics tracking:
  - Hang rates over time
  - Common hang types
  - Player reliability scores
- Integration with monitoring systems

### Implementation:
- Prometheus metrics for hang rates
- Alert thresholds configuration
- Slack/email notifications (optional)

---

## Implementation Strategy

### Start with Phase 1-3 (Week 1)
- Get immediate visibility
- Very low risk
- Helps debug current issues
- 5-8 hours total

### Add Phase 4-5 (Week 2)
- Automatic problem detection
- Historical context
- 5-7 hours total

### Complete Phase 6-8 (Week 3+)
- Full diagnostic capabilities
- Real-time monitoring
- Production-ready monitoring
- 9-12 hours total

## Risk Mitigation

1. **Each phase is independent** - No dependencies between phases
2. **Feature flags** - Enable/disable each phase independently
3. **No database changes** - Everything in memory initially
4. **Minimal client changes** - Only heartbeat enhancement
5. **Progressive rollout** - Test with single room first

## Success Metrics

### Phase 1 Success:
- Can see client state in heartbeats
- Identify refresh bug state loss

### Phase 2 Success:
- Complete activity trail in logs
- Can trace player actions

### Phase 3 Success:
- Instant room state visibility
- Quick debugging of reported issues

### Phase 4 Success:
- Automatic hang detection in logs
- Catch bot hanging immediately

### Phase 5-8 Success:
- Full diagnostic capabilities
- Proactive issue detection
- Historical pattern analysis

## Rollback Plan

Each phase can be rolled back independently:

```python
# config.py
FEATURE_FLAGS = {
    'enhanced_heartbeat': True,      # Phase 1
    'activity_logging': True,        # Phase 2
    'debug_endpoints': True,         # Phase 3
    'hang_detection': True,          # Phase 4
    'activity_history': True,        # Phase 5
    'diagnostic_snapshots': True,    # Phase 6
    'realtime_monitoring': False,    # Phase 7
    'alerts_enabled': False,         # Phase 8
}
```

Simply set any flag to `False` to disable that phase's functionality.