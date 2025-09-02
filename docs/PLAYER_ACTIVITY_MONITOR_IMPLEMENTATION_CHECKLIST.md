# Player Activity Monitor - Implementation Checklist

## Pre-Implementation Setup
- [ ] Create feature flag configuration file
- [ ] Set up branch: `feature/player-activity-monitor`
- [ ] Review existing heartbeat implementation in NetworkService.ts
- [ ] Review existing WebSocket handlers in ws.py
- [ ] Backup current logs for comparison

---

## Phase 1: Enhanced Client Heartbeat (Priority: CRITICAL)
**Goal**: Add diagnostic data to existing heartbeat  
**Timeline**: 2-3 hours  
**Risk**: Very Low

### Implementation Tasks
- [ ] **Frontend: Enhance NetworkService.ts**
  - [ ] Add diagnostic data collection method
  - [ ] Include current game phase in heartbeat
  - [ ] Include UI state (current view, waiting for action)
  - [ ] Include captured_piles value
  - [ ] Include declared value
  - [ ] Include last user action timestamp
  - [ ] Include message queue size

- [ ] **Backend: Update ws.py heartbeat handler**
  - [ ] Parse enhanced heartbeat data
  - [ ] Log received diagnostic data
  - [ ] Maintain last heartbeat timestamp per player
  - [ ] Send pong response with server timestamp

### Testing & Verification
- [ ] Verify heartbeat payload in browser DevTools Network tab
- [ ] Check server logs show enhanced heartbeat data
- [ ] Confirm no performance impact (response time <10ms)
- [ ] Test with browser refresh - see captured_piles/declared values
- [ ] Verify heartbeat continues during all game phases

### Rollback Plan
- [ ] Feature flag: `ENHANCED_HEARTBEAT = False`
- [ ] Document flag location and usage

---

## Phase 2: Basic Activity Logging (Priority: HIGH)
**Goal**: Log every player action with context  
**Timeline**: 2-3 hours  
**Risk**: Very Low

### Implementation Tasks
- [ ] **Create Activity Logger Module**
  - [ ] Create `backend/api/services/activity_logger.py`
  - [ ] Define activity log format
  - [ ] Include room_id, player_name, action, timestamp
  - [ ] Add context data (game phase, turn number)

- [ ] **Integrate with WebSocket Handlers**
  - [ ] Log 'join_room' events
  - [ ] Log 'start_game' events
  - [ ] Log 'declare' events with declared value
  - [ ] Log 'play' events with pieces played
  - [ ] Log 'redeal' accept/decline events
  - [ ] Log disconnection events

- [ ] **Add Specialized Logging**
  - [ ] Log when captured_piles changes
  - [ ] Log when bot should act (with timeout tracking)
  - [ ] Log state transitions

### Testing & Verification
- [ ] Tail logs during gameplay
- [ ] Verify all actions are logged
- [ ] Test log format is parseable
- [ ] Confirm no performance impact
- [ ] Test log rotation doesn't lose data

### Rollback Plan
- [ ] Feature flag: `ACTIVITY_LOGGING = False`
- [ ] Ensure logging can be disabled without affecting gameplay

---

## Phase 3: Current State Debug Endpoint (Priority: HIGH)
**Goal**: Instant visibility into room state  
**Timeline**: 1-2 hours  
**Risk**: Very Low

### Implementation Tasks
- [ ] **Create Debug Router**
  - [ ] Add `backend/api/routes/debug.py` if not exists
  - [ ] Implement `/api/debug/room-state/{room_id}` endpoint
  - [ ] Return current game phase
  - [ ] Return all players with connection status
  - [ ] Return last heartbeat time for each player
  - [ ] Return pending actions for each player
  - [ ] Return current scores and captured piles

- [ ] **Add Security**
  - [ ] Add basic authentication or IP restriction
  - [ ] Log access to debug endpoints
  - [ ] Rate limit to prevent abuse

### Testing & Verification
- [ ] Test endpoint with active game room
- [ ] Test endpoint with non-existent room
- [ ] Verify response format is clear and useful
- [ ] Test during different game phases
- [ ] Document example responses

### Rollback Plan
- [ ] Feature flag: `DEBUG_ENDPOINTS = False`
- [ ] Ensure endpoints return 404 when disabled

---

## Phase 4: Simple Hang Detection (Priority: HIGH)
**Goal**: Automatically detect stuck players/bots  
**Timeline**: 3-4 hours  
**Risk**: Low

### Implementation Tasks
- [ ] **Create Hang Detector Module**
  - [ ] Create `backend/api/services/hang_detector.py`
  - [ ] Define hang detection thresholds
  - [ ] Implement no-heartbeat detection (>90s)
  - [ ] Implement waiting-for-action detection (>60s)
  - [ ] Implement bot-not-responding detection

- [ ] **Create Background Task**
  - [ ] Check all active rooms every 30 seconds
  - [ ] Log warnings for detected hangs
  - [ ] Track hang occurrences per player
  - [ ] Special handling for bot hang detection

- [ ] **Integration Points**
  - [ ] Hook into room manager for active rooms list
  - [ ] Access player heartbeat timestamps
  - [ ] Access pending actions queue

### Testing & Verification
- [ ] Test by stopping browser JavaScript
- [ ] Test by delaying bot response
- [ ] Verify warnings appear in logs
- [ ] Test detection thresholds are appropriate
- [ ] Ensure no false positives during normal play

### Rollback Plan
- [ ] Feature flag: `HANG_DETECTION = False`
- [ ] Ensure background task can be disabled

---

## Phase 5: Activity History Buffer (Priority: MEDIUM)
**Goal**: Store recent actions for debugging  
**Timeline**: 2-3 hours  
**Risk**: Low

### Implementation Tasks
- [ ] **Create Activity Buffer**
  - [ ] Implement circular buffer (deque) per player
  - [ ] Store last 50 actions per player
  - [ ] Include timestamp, action type, context
  - [ ] Implement memory limit safeguards

- [ ] **Add History Endpoint**
  - [ ] Create `/api/debug/player-history/{room_id}/{player_name}`
  - [ ] Return recent actions in chronological order
  - [ ] Include helpful context for each action
  - [ ] Add filtering options (action type, time range)

- [ ] **Buffer Management**
  - [ ] Clear buffers for completed games
  - [ ] Implement max memory usage limits
  - [ ] Add buffer statistics endpoint

### Testing & Verification
- [ ] Verify buffer stores correct number of actions
- [ ] Test memory usage with many active players
- [ ] Verify old actions are properly evicted
- [ ] Test endpoint returns useful data
- [ ] Confirm buffer survives player reconnection

### Rollback Plan
- [ ] Feature flag: `ACTIVITY_HISTORY = False`
- [ ] Ensure game functions without history buffer

---

## Phase 6: Diagnostic Snapshots (Priority: MEDIUM)
**Goal**: Capture full context when hangs detected  
**Timeline**: 3-4 hours  
**Risk**: Low

### Implementation Tasks
- [ ] **Define Snapshot Structure**
  - [ ] Create HangDiagnostic dataclass
  - [ ] Include player state
  - [ ] Include game state
  - [ ] Include recent actions from buffer
  - [ ] Include client state from last heartbeat
  - [ ] Include network metrics

- [ ] **Implement Snapshot Collection**
  - [ ] Trigger on hang detection
  - [ ] Store in circular buffer (last 100)
  - [ ] Add timestamp and unique ID
  - [ ] Implement JSON serialization

- [ ] **Create Diagnostics Endpoint**
  - [ ] Create `/api/debug/hang-diagnostics`
  - [ ] Add filtering by player, room, hang type
  - [ ] Add time range filtering
  - [ ] Return detailed snapshots

### Testing & Verification
- [ ] Trigger hang and verify snapshot created
- [ ] Verify snapshot contains all needed data
- [ ] Test circular buffer limits
- [ ] Verify snapshots are useful for debugging
- [ ] Test endpoint filtering options

### Rollback Plan
- [ ] Feature flag: `DIAGNOSTIC_SNAPSHOTS = False`
- [ ] Ensure hang detection works without snapshots

---

## Phase 7: Real-time Monitoring WebSocket (Priority: LOW)
**Goal**: Live dashboard of system activity  
**Timeline**: 2-3 hours  
**Risk**: Low

### Implementation Tasks
- [ ] **Create Monitor WebSocket**
  - [ ] Add `/api/debug/ws/monitor` endpoint
  - [ ] Send updates every 5 seconds
  - [ ] Include active/inactive player counts
  - [ ] Include recent hang detections
  - [ ] Include activity rates

- [ ] **Create Simple Web Dashboard**
  - [ ] Basic HTML page for monitoring
  - [ ] Connect to WebSocket
  - [ ] Display real-time statistics
  - [ ] Show recent hangs
  - [ ] Color code by severity

### Testing & Verification
- [ ] Test WebSocket connection stability
- [ ] Verify updates are timely and accurate
- [ ] Test with multiple monitoring clients
- [ ] Ensure low performance impact
- [ ] Test dashboard is intuitive

### Rollback Plan
- [ ] Feature flag: `REALTIME_MONITORING = False`
- [ ] WebSocket returns 404 when disabled

---

## Phase 8: Alerts and Metrics (Priority: LOW)
**Goal**: Proactive issue notification  
**Timeline**: 4-5 hours  
**Risk**: Medium

### Implementation Tasks
- [ ] **Define Alert Rules**
  - [ ] Mass hang detection (>3 players)
  - [ ] Repeated hangs same player
  - [ ] Bot consistently hanging
  - [ ] High reconnection rate

- [ ] **Implement Alert System**
  - [ ] Create alert configuration
  - [ ] Log critical alerts
  - [ ] Optional: Email notifications
  - [ ] Optional: Slack integration

- [ ] **Add Metrics Collection**
  - [ ] Track hang rates over time
  - [ ] Track recovery success rates
  - [ ] Player reliability scores
  - [ ] Common hang patterns

- [ ] **Create Metrics Endpoint**
  - [ ] `/api/debug/metrics`
  - [ ] Return aggregated statistics
  - [ ] Include time-series data
  - [ ] Export Prometheus format (optional)

### Testing & Verification
- [ ] Trigger each alert condition
- [ ] Verify alerts are actionable
- [ ] Test alert fatigue prevention
- [ ] Verify metrics are accurate
- [ ] Test metrics don't impact performance

### Rollback Plan
- [ ] Feature flag: `ALERTS_ENABLED = False`
- [ ] Ensure system works without alerting

---

## Post-Implementation

### Documentation
- [ ] Update CLAUDE.md with new debugging capabilities
- [ ] Create troubleshooting guide using new tools
- [ ] Document all debug endpoints
- [ ] Create example debugging scenarios
- [ ] Update team runbook

### Performance Validation
- [ ] Run load test with 100 concurrent players
- [ ] Verify <1% CPU increase
- [ ] Verify <5MB memory increase
- [ ] Check no impact on game latency
- [ ] Validate log volume is manageable

### Team Enablement
- [ ] Demo new debugging tools to team
- [ ] Create quick reference card
- [ ] Set up monitoring dashboard
- [ ] Train on common debugging patterns
- [ ] Gather feedback for improvements

### Success Metrics
- [ ] Reduce "unable to reproduce" bugs by 50%
- [ ] Decrease average debug time by 60%
- [ ] Catch 90% of hangs automatically
- [ ] Achieve <5 minute issue identification time

---

## Quick Reference

### Feature Flags
```python
FEATURE_FLAGS = {
    'enhanced_heartbeat': False,      # Phase 1
    'activity_logging': False,        # Phase 2
    'debug_endpoints': False,         # Phase 3
    'hang_detection': False,          # Phase 4
    'activity_history': False,        # Phase 5
    'diagnostic_snapshots': False,    # Phase 6
    'realtime_monitoring': False,     # Phase 7
    'alerts_enabled': False,          # Phase 8
}
```

### Key Endpoints
```bash
# Current room state
GET /api/debug/room-state/{room_id}

# Player action history
GET /api/debug/player-history/{room_id}/{player_name}

# Hang diagnostics
GET /api/debug/hang-diagnostics

# Real-time monitoring
WS /api/debug/ws/monitor

# System metrics
GET /api/debug/metrics
```

### Critical Thresholds
- No Heartbeat: 90 seconds
- Action Timeout: 60 seconds
- Bot Response: 30 seconds
- Message Queue: 50 messages
- Reconnect Limit: 3 in 5 minutes