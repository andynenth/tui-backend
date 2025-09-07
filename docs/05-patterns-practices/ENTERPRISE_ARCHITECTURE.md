# 🚀 Enterprise Architecture Guide for Liap Tui

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Core Enterprise Patterns](#core-enterprise-patterns)
3. [Automatic Broadcasting System](#automatic-broadcasting-system)
4. [Event-Driven vs Polling Patterns](#event-driven-vs-polling-patterns)
5. [What Violates the Architecture](#what-violates-the-architecture)
6. [What is Correct](#what-is-correct)
7. [Implementation Examples](#implementation-examples)
8. [Validation and Testing](#validation-and-testing)
9. [Migration Guide](#migration-guide)

---

## Architecture Overview

The **Liap Tui Enterprise Architecture** is a production-ready, event-driven system that eliminates sync bugs and ensures consistent state management across the entire application. It implements enterprise-grade patterns for automatic broadcasting, centralized state management, and event sourcing.

### 🎯 **Key Principles**
1. **Single Source of Truth**: All state changes go through one centralized method
2. **Automatic Broadcasting**: No manual broadcast calls - everything is automatic
3. **Event-Driven**: No polling patterns - everything uses event listeners
4. **JSON-Safe Serialization**: All data automatically converted for transmission
5. **Complete Audit Trail**: Every change tracked with sequence numbers and timestamps

### 🏗️ **Architecture Layers**

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                            │
├─────────────────────────────────────────────────────────────┤
│ • React Components (Event-driven UI updates)                │
│ • Connection Status Hooks (Event listeners, no polling)     │
│ • GameService (Reactive state management)                   │
│ • NetworkService (Event-driven WebSocket management)        │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   WebSocket Layer  │
                    │ (Automatic Events) │
                    └─────────┬─────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     BACKEND LAYER                           │
├─────────────────────────────────────────────────────────────┤
│ • State Machine (Enterprise Architecture)                   │
│   - update_phase_data() - ONLY way to change state         │
│   - broadcast_custom_event() - ONLY way to send events     │
│   - Automatic broadcasting on ALL state changes            │
│ • Health Monitor (Adaptive intervals, no fixed polling)     │
│ • Bot Manager (Uses state machine, no manual broadcasts)    │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Enterprise Patterns

### 🔐 **1. Centralized State Management**

**THE RULE**: All state changes MUST go through `update_phase_data()`

```python
# ✅ CORRECT - Enterprise Pattern
await self.update_phase_data({
    'current_player': next_player,
    'turn_number': game.turn_number,
    'piece_count': len(pieces)
}, "Player moved - automatic broadcasting")

# ❌ WRONG - Manual Pattern (FORBIDDEN)
self.phase_data['current_player'] = next_player  # Bypasses enterprise system
self.phase_data['turn_number'] = game.turn_number  # No automatic broadcasting
```

### 🤖 **2. Automatic Broadcasting System**

**THE RULE**: NEVER call `broadcast()` manually - it's automatic

```python
# ✅ CORRECT - Automatic Broadcasting
await self.update_phase_data({
    'game_state': 'updated'
}, "State changed")
# ↑ Automatically triggers phase_change broadcast to all clients
# ↑ Includes sequence numbers, timestamps, and reason
# ↑ JSON-safe serialization happens automatically

# ❌ WRONG - Manual Broadcasting (FORBIDDEN)
await broadcast(room_id, "state_change", data)  # Bypasses enterprise system
# ↑ No sequence numbers, no audit trail, potential sync bugs
```

### 📡 **3. Event Sourcing**

Every state change is automatically tracked:

```python
# Automatic metadata added to every broadcast:
{
    "sequence": 123,
    "timestamp": "2025-06-27T09:30:00Z",
    "reason": "Player moved piece",
    "phase": "turn",
    "game_data": {...}  # JSON-safe serialized
}
```

### 🔄 **4. Event-Driven Communication**

**THE RULE**: Use event listeners, NEVER polling

```javascript
// ✅ CORRECT - Event-Driven
networkService.addEventListener('connected', handleConnection);
serviceIntegration.addEventListener('healthStatusChanged', updateStatus);

// ❌ WRONG - Polling Pattern (FORBIDDEN)
setInterval(checkConnectionStatus, 5000);  // Wasteful, inefficient
setInterval(updateHealthStatus, 3000);     // Creates unnecessary load
```

---

## Automatic Broadcasting System

### 🎯 **How It Works**

1. **Developer calls** `update_phase_data()` with new state
2. **System automatically** validates and applies changes
3. **System automatically** generates sequence number and timestamp
4. **System automatically** serializes data to JSON-safe format
5. **System automatically** broadcasts `phase_change` event to all clients
6. **System automatically** stores change in audit trail

### 🔧 **Internal Flow**

```python
async def update_phase_data(self, updates: Dict, reason: str):
    # 1. Validate updates
    validated_data = self._validate_updates(updates)

    # 2. Apply to phase_data
    self.phase_data.update(validated_data)

    # 3. Generate metadata
    sequence = self._get_next_sequence()
    timestamp = datetime.now().isoformat()

    # 4. JSON-safe serialization
    broadcast_data = self._serialize_for_broadcast({
        'phase': self.current_phase.value,
        'phase_data': self.phase_data,
        'players': self._get_player_data(),
        'sequence': sequence,
        'timestamp': timestamp,
        'reason': reason
    })

    # 5. Automatic broadcast (NEVER manual)
    await self._broadcast_phase_change(broadcast_data)

    # 6. Store in audit trail
    self._store_change_event(sequence, reason, updates)
```

### 🎯 **Benefits**

- **🔒 Sync Bug Prevention**: Impossible to forget broadcasting
- **🔍 Complete Debugging**: Every change logged with reason and sequence
- **⚡ Performance**: Optimized JSON serialization
- **🏗️ Maintainability**: Single source of truth
- **🧪 Testability**: Predictable state changes

---

## Event-Driven vs Polling Patterns

### ✅ **Event-Driven (CORRECT)**

```javascript
// Frontend Connection Management
class ConnectionManager {
    constructor() {
        // Event listeners - react to actual changes
        networkService.addEventListener('connected', this.onConnect);
        networkService.addEventListener('disconnected', this.onDisconnect);
        networkService.addEventListener('error', this.onError);
    }

    onConnect(event) {
        // React immediately to connection change
        this.updateConnectionState(true);
    }
}
```

```python
# Backend Health Monitoring
class HealthMonitor {
    async def monitor_resources(self):
        check_interval = 30  # Start with 30 seconds

        while self.monitoring_active:
            await asyncio.sleep(check_interval)

            # Check health
            health_issues = await self.check_system_health()

            # Adaptive monitoring - react to conditions
            if health_issues:
                check_interval = max(10, check_interval / 2)  # Check more frequently
            else:
                check_interval = min(120, check_interval * 1.2)  # Less frequent when healthy
```

### ❌ **Polling Patterns (FORBIDDEN)**

```javascript
// BAD: Fixed interval polling
setInterval(() => {
    checkConnectionStatus();      // Wasteful - checks even when nothing changed
    updateHealthMetrics();        // CPU intensive
    refreshGameState();          // Can cause race conditions
}, 5000);

// BAD: Continuous status checking
while (true) {
    if (isConnected()) {
        updateUI();              // Inefficient busy-waiting
    }
    await sleep(1000);
}
```

---

## What Violates the Architecture

### 🚨 **Critical Violations**

#### 1. **Manual Broadcast Calls**
```python
# ❌ VIOLATION: Manual broadcasting
await broadcast(room_id, "game_update", data)
await broadcast(room_id, "player_moved", player_data)

# WHY IT'S BAD:
# - Bypasses automatic sequence numbering
# - No audit trail
# - Potential sync bugs
# - No JSON-safe serialization
# - Manual process prone to human error
```

#### 2. **Direct Phase Data Manipulation**
```python
# ❌ VIOLATION: Direct state changes
self.phase_data['current_player'] = new_player
self.phase_data['score'] = updated_score

# WHY IT'S BAD:
# - No automatic broadcasting
# - Clients don't get updates
# - State becomes inconsistent
# - No change tracking
```

#### 3. **Fixed Interval Polling**
```javascript
// ❌ VIOLATION: Polling patterns
setInterval(checkGameStatus, 3000);
setInterval(updatePlayerList, 5000);

// WHY IT'S BAD:
# - Wastes CPU and network resources
# - Updates even when nothing changed
# - Not responsive to actual changes
# - Poor user experience
```

#### 4. **Manual JSON Serialization**
```python
# ❌ VIOLATION: Manual serialization
data = {
    'player': player_object,  # Object won't serialize
    'pieces': piece_objects   # Objects won't serialize
}
await broadcast(room_id, "update", data)  # Will fail or corrupt

# WHY IT'S BAD:
# - Objects can't be JSON serialized
# - Data corruption
# - WebSocket transmission failures
```

### ⚠️ **Minor Violations**

#### 1. **Inconsistent Event Handling**
```javascript
// ❌ Some events use listeners, others use polling
networkService.addEventListener('connected', handler);
setInterval(checkDisconnectionStatus, 5000);  // Should be event-driven too
```

#### 2. **Missing Enterprise Metadata**
```python
# ❌ Custom events without proper metadata
await self.broadcast_custom_event("turn_complete", {"winner": player})
# Should include sequence, timestamp, reason
```

---

## What is Correct

### ✅ **Perfect Enterprise Patterns**

#### 1. **State Management**
```python
# ✅ PERFECT: Enterprise state changes
await self.update_phase_data({
    'current_player': next_player,
    'turn_number': self.game.turn_number,
    'scores': updated_scores
}, f"Player {player_name} completed turn")

# BENEFITS:
# ✅ Automatic broadcasting to all clients
# ✅ Sequence numbers and timestamps added
# ✅ JSON-safe serialization
# ✅ Complete audit trail
# ✅ Guaranteed sync across all clients
```

#### 2. **Custom Events**
```python
# ✅ PERFECT: Enterprise custom events
await self.broadcast_custom_event("turn_resolved", {
    'winner': winner_name,
    'pile_count': final_pile_count,
    'next_phase': 'scoring'
}, f"Turn won by {winner_name}")

# BENEFITS:
# ✅ Includes enterprise metadata
# ✅ Proper event naming
# ✅ JSON-safe data
# ✅ Descriptive reason
```

#### 3. **Event-Driven Frontend**
```javascript
// ✅ PERFECT: Event-driven updates
class GameService {
    constructor() {
        // React to actual network events
        networkService.addEventListener('connected', this.onNetworkConnected);
        networkService.addEventListener('disconnected', this.onNetworkDisconnected);
        networkService.addEventListener('messageReceived', this.onGameMessage);

        // React to service events
        serviceIntegration.addEventListener('healthStatusChanged', this.onHealthChange);
        serviceIntegration.addEventListener('metricsUpdated', this.onMetricsUpdate);
    }

    onGameMessage(event) {
        // Process immediately when data arrives
        this.processGameEvent(event.data);
    }
}
```

#### 4. **Adaptive Monitoring**
```python
# ✅ PERFECT: Adaptive, event-driven monitoring
class HealthMonitor:
    async def monitor_websocket_health(self):
        check_interval = 60  # Start with 1 minute
        consecutive_healthy = 0

        while self.monitoring_active:
            await asyncio.sleep(check_interval)

            # Check actual health
            health_metrics = await self.check_websocket_metrics()

            # Adapt based on conditions
            if health_metrics.has_issues:
                check_interval = max(15, check_interval / 2)  # More frequent
                consecutive_healthy = 0
            else:
                consecutive_healthy += 1
                if consecutive_healthy > 3:
                    check_interval = min(300, check_interval * 1.5)  # Less frequent
```

---

## Implementation Examples

### 🎮 **Game State Transitions**

#### ✅ **Correct Implementation**
```python
class TurnState(GameState):
    async def handle_player_move(self, action: GameAction):
        player_name = action.player_name
        pieces = action.payload['pieces']

        # Process the move
        result = self.game.play_turn(player_name, pieces)

        if result.get('valid'):
            # ✅ ENTERPRISE: Single source of truth
            await self.update_phase_data({
                'current_player': result['next_player'],
                'last_play': {
                    'player': player_name,
                    'pieces': pieces,
                    'timestamp': time.time()
                },
                'turn_count': result['turn_count']
            }, f"Player {player_name} played {len(pieces)} pieces")
            # ↑ Automatically broadcasts to all clients
            # ↑ Includes sequence numbers and timestamps
            # ↑ JSON-safe serialization

            # Check for turn completion
            if result.get('turn_complete'):
                await self.broadcast_custom_event("turn_resolved", {
                    'winner': result['winner'],
                    'pile_count': result['pile_count']
                }, f"Turn won by {result['winner']}")

        return {'status': 'success', 'valid': result.get('valid')}
```

#### ❌ **Incorrect Implementation**
```python
class TurnState(GameState):
    async def handle_player_move(self, action: GameAction):
        player_name = action.player_name
        pieces = action.payload['pieces']

        # Process the move
        result = self.game.play_turn(player_name, pieces)

        if result.get('valid'):
            # ❌ VIOLATION: Direct state manipulation
            self.phase_data['current_player'] = result['next_player']
            self.phase_data['last_play'] = {
                'player': player_name,
                'pieces': pieces
            }

            # ❌ VIOLATION: Manual broadcasting
            await broadcast(self.room_id, "player_moved", {
                'player': player_name,
                'next_player': result['next_player'],
                'pieces': pieces  # ❌ May not be JSON-safe
            })

            # ❌ VIOLATION: Separate manual broadcast
            if result.get('turn_complete'):
                await broadcast(self.room_id, "turn_complete", {
                    'winner': result['winner']
                })
```

### 🔄 **Frontend State Updates**

#### ✅ **Correct Implementation**
```javascript
class GameService {
    constructor() {
        this.state = this.getInitialState();

        // ✅ Event-driven updates
        networkService.addEventListener('messageReceived', this.handleGameMessage);
        networkService.addEventListener('connected', this.handleConnection);
        networkService.addEventListener('disconnected', this.handleDisconnection);
    }

    handleGameMessage = (event) => {
        const { type, data } = event.detail;

        switch (type) {
            case 'phase_change':
                // ✅ React immediately to enterprise broadcasts
                this.processPhaseChange(data);
                break;
            case 'turn_resolved':
                // ✅ React to custom enterprise events
                this.processTurnResolved(data);
                break;
        }
    }

    processPhaseChange(data) {
        // ✅ Immutable state updates
        const newState = {
            ...this.state,
            phase: data.phase,
            currentPlayer: data.phase_data.current_player,
            lastEventSequence: data.sequence,  // ✅ Track enterprise metadata
            lastUpdateTime: data.timestamp
        };

        this.setState(newState);
        this.notifyObservers('PHASE_CHANGE', newState);
    }
}
```

#### ❌ **Incorrect Implementation**
```javascript
class GameService {
    constructor() {
        this.state = this.getInitialState();

        // ❌ VIOLATION: Polling pattern
        setInterval(() => {
            this.checkForUpdates();
        }, 2000);
    }

    async checkForUpdates() {
        // ❌ VIOLATION: Manual status checking
        try {
            const response = await fetch('/api/game-status');
            const data = await response.json();

            // ❌ VIOLATION: Direct state mutation
            this.state.phase = data.phase;
            this.state.currentPlayer = data.currentPlayer;

            // ❌ VIOLATION: Manual notification
            this.notifyObservers('UPDATE', this.state);
        } catch (error) {
            console.error('Polling failed:', error);
        }
    }
}
```

---

## Validation and Testing

### 🧪 **Enterprise Architecture Testing**

The codebase includes comprehensive testing to validate enterprise architecture compliance:

```python
# test_all_phases_enterprise.py
async def test_all_phases_enterprise():
    """Validates all enterprise architecture patterns"""

    # 1. Test automatic broadcasting
    broadcast_calls = []

    # 2. Test phase transitions
    await state_machine.start(GamePhase.PREPARATION)
    await simulate_declarations()
    await simulate_turns()

    # 3. Validate enterprise features
    enterprise_compliant = 0
    for call in broadcast_calls:
        if (call['has_sequence'] and call['has_reason'] and
            call['has_timestamp'] and call['event_type'] == 'phase_change'):
            enterprise_compliant += 1

    # 4. Check compliance
    assert enterprise_compliant == len(phase_change_calls)
    assert all_broadcasts_automatic()
    assert sequence_numbers_ordered()
    assert json_serialization_safe()
```

### 📊 **Compliance Metrics**

The system tracks enterprise architecture compliance:

```
📋 ENTERPRISE COMPLIANCE SUMMARY
   Automatic Broadcasting: ✅ 100%
   Enterprise Metadata: ✅ 100%
   Phase Change Events: ✅ 100%
   Sequence Ordering: ✅ 100%
   JSON Serialization: ✅ 100%
   Overall Status: 🚀 ENTERPRISE COMPLIANT
```

### 🔍 **Common Violations Detected**

The testing framework automatically detects:
- Manual `broadcast()` calls
- Direct `phase_data` manipulation
- Missing sequence numbers or timestamps
- Non-JSON-safe objects in broadcasts
- Out-of-order sequence numbers
- Polling patterns in frontend code

---

## Migration Guide

### 🔄 **From Manual to Enterprise Architecture**

#### Step 1: Replace Manual Broadcasts
```python
# BEFORE (Manual)
await broadcast(room_id, "state_update", {
    'player': current_player,
    'score': new_score
})

# AFTER (Enterprise)
await self.update_phase_data({
    'current_player': current_player,
    'player_score': new_score
}, f"Player {current_player} score updated")
```

#### Step 2: Remove Direct State Access
```python
# BEFORE (Direct)
self.phase_data['current_turn'] = turn_number
self.phase_data['players'][player_id]['ready'] = True

# AFTER (Enterprise)
await self.update_phase_data({
    'current_turn': turn_number,
    'player_ready': {player_id: True}
}, f"Turn {turn_number} started")
```

#### Step 3: Convert Polling to Events
```javascript
// BEFORE (Polling)
setInterval(checkGameStatus, 5000);

// AFTER (Event-Driven)
networkService.addEventListener('messageReceived', handleGameStatusUpdate);
```

#### Step 4: Add Enterprise Metadata
```python
# BEFORE (Basic)
await self.broadcast_custom_event("game_event", data)

# AFTER (Enterprise)
await self.broadcast_custom_event("game_event", data, "Descriptive reason for event")
```

### 🎯 **Validation Checklist**

- [ ] No manual `broadcast()` calls anywhere in codebase
- [ ] All state changes go through `update_phase_data()`
- [ ] No direct `phase_data` manipulation
- [ ] All frontend updates are event-driven (no `setInterval`)
- [ ] All broadcasts include sequence numbers and timestamps
- [ ] All data is JSON-safe serialized
- [ ] Enterprise compliance tests pass 100%

---

## 🎉 **Benefits of Enterprise Architecture**

### 🔒 **Reliability**
- **Zero Sync Bugs**: Automatic broadcasting prevents state inconsistencies
- **Complete Audit Trail**: Every change tracked and traceable
- **Predictable Behavior**: Single source of truth eliminates race conditions

### ⚡ **Performance**
- **Event-Driven**: Only updates when changes occur
- **Optimized Serialization**: JSON-safe conversion built-in
- **Adaptive Monitoring**: System scales monitoring based on load

### 🏗️ **Maintainability**
- **Single Pattern**: One way to do state changes
- **Self-Documenting**: Reasons included with every change
- **Testable**: Enterprise patterns are predictable and verifiable

### 🧪 **Quality Assurance**
- **Automatic Validation**: System prevents violations
- **Comprehensive Testing**: Enterprise compliance continuously verified
- **Real-time Monitoring**: Architecture health tracked in production

---

## 📚 **Additional Resources**

- **Implementation Examples**: See `backend/engine/state_machine/states/` for correct patterns
- **Testing Framework**: `test_all_phases_enterprise.py` for validation
- **Architecture Validation**: Run enterprise compliance tests before deployment
- **Performance Monitoring**: Health monitor tracks enterprise architecture metrics

---

*This enterprise architecture ensures production-ready, scalable, and maintainable code that eliminates sync bugs and provides complete observability into system behavior.*
