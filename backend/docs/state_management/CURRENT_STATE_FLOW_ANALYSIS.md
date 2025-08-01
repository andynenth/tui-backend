# Current State Flow Analysis

## Executive Summary

The Clean Architecture implementation completely bypasses the sophisticated state management infrastructure (`StatePersistenceManager`), creating a disconnected dual-architecture system where enterprise-grade state management capabilities sit unused.

## Complete WebSocket → Domain Flow

### 1. WebSocket Entry Point
```
api/routes/ws.py:156-189 (message routing)
    ↓
WebSocket handler receives message
    ↓
```

### 2. Clean Architecture Adapter
```
infrastructure/adapters/clean_architecture_adapter.py:96-145
    ↓
CleanArchitectureAdapter.handle_event()
    ↓ (checks feature flags)
Routes to use case handlers (e.g., _handle_start_game)
    ↓
```

### 3. Use Case Layer
```
application/use_cases/game/start_game.py:69-366
    ↓
StartGameUseCase.execute()
    ↓
Line 142: game.start_game()     # Direct domain call
Line 149: game.start_round()    # Direct domain call - KEY BYPASS
    ↓
```

### 4. Domain Entity
```
domain/entities/game.py:126-243
    ↓
Game entity methods execute business logic
Emits domain events
Updates internal state directly
    ↓
```

### 5. Event Publishing
```
infrastructure/events/websocket_event_publisher.py
    ↓
Publishes events to WebSocket clients
```

## Critical Findings

### 1. Direct Domain Calls (The Core Problem)

**Location**: `application/use_cases/game/start_game.py:149`
```python
# Current implementation
game.start_round()  # Direct call bypasses ALL state management
```

**What Should Happen**:
```python
# Desired implementation
await state_manager.handle_transition(
    state_machine_id=game.room_id,
    transition=StateTransition(
        from_state="NOT_STARTED",
        to_state="PREPARATION",
        action="start_game",
        payload={"players": game.players}
    )
)
```

### 2. No StatePersistenceManager Integration

**Current Constructor** (start_game.py:51-56):
```python
def __init__(
    self,
    unit_of_work: UnitOfWork,
    event_publisher: EventPublisher,
    metrics: Optional[MetricsCollector] = None,
):
```

**Missing**: No `StatePersistenceManager` parameter or usage.

### 3. Duplicate GamePhase Enums

**Domain Enum** (`domain/entities/game.py:33-42`):
```python
class GamePhase(Enum):
    NOT_STARTED = "NOT_STARTED"
    PREPARATION = "PREPARATION"
    DECLARATION = "DECLARATION"
    TURN = "TURN"
    SCORING = "SCORING"
    GAME_OVER = "GAME_OVER"
```

**State Machine Enum** (`engine/state_machine/core.py:15-26`):
```python
class GamePhase(Enum):
    NOT_STARTED = "NOT_STARTED"
    WAITING = "WAITING"
    PREPARATION = "PREPARATION"
    ROUND_START = "ROUND_START"
    DECLARATION = "DECLARATION"
    TURN = "TURN"
    TURN_END = "TURN_END"
    SCORING = "SCORING"
    ROUND_END = "ROUND_END"
    GAME_OVER = "GAME_OVER"
    ERROR = "ERROR"
```

**Differences**: State machine has 5 additional phases for granular control.

### 4. Event Flow Without State Tracking

Current event emission (start_game.py:152-188):
1. Domain events from `game.events` (if any)
2. Manually created `GameStarted` event
3. Manually created `RoundStarted` event
4. Manually created `PiecesDealt` event
5. `PhaseChanged` event is **commented out** (line 277)

**Missing**: No state transition events or persistence triggers.

## State Management Gaps

### 1. No State Persistence
- Zero calls to `StatePersistenceManager`
- No state snapshots created
- No transition logging
- No recovery mechanisms

### 2. No Phase Change Tracking
- Phase changes happen silently in domain
- No audit trail of state transitions
- No ability to replay or recover state

### 3. No Integration with State Machine
- `PreparationState` with weak hand algorithm unused
- Sophisticated state logic in `engine/state_machine/` bypassed
- Enterprise patterns not utilized

### 4. Feature Flags Not Used for State
- Feature flags exist but don't control state management
- No gradual rollout path configured
- Clean architecture adapter doesn't check state flags

## Dependency Injection Opportunities

### Current Dependencies (infrastructure/dependencies.py)
- `get_unit_of_work()` - ✅ Exists
- `get_event_publisher()` - ✅ Exists
- `get_metrics_collector()` - ✅ Exists
- `get_state_persistence_manager()` - ❌ Missing

### Integration Points
1. Add `StatePersistenceManager` to dependency injection
2. Modify use case constructors to accept state manager
3. Create adapter/bridge for gradual integration
4. Use feature flags to control activation

## Use Case Analysis

### StartGameUseCase
- **Line 149**: Direct `game.start_round()` call
- **Events**: Manually creates 4 event types
- **State Changes**: NOT_STARTED → PREPARATION
- **Integration Needed**: Replace direct call with state transition

### DeclareUseCase
- **Domain Calls**: `player.declare()`, `game.change_phase()`
- **State Changes**: DECLARATION → TURN (when all declared)
- **Integration Needed**: Track declaration state transitions

### PlayUseCase
- **Domain Calls**: `game.play_turn()`, `game.complete_round()`
- **State Changes**: Multiple phase transitions possible
- **Integration Needed**: Complex state flow tracking

### Redeal Use Cases
- **Current**: Handle weak hands at domain level
- **Missing**: State machine's sophisticated weak hand logic
- **Integration Needed**: Connect to PreparationState logic

## Architecture Disconnection Root Cause

### Historical Context
1. Clean Architecture was implemented first
2. State machine was added later for sophistication
3. Integration was never completed
4. Two parallel systems now exist

### Technical Debt
- Duplicate phase enums
- Parallel state management approaches
- Unused enterprise infrastructure
- Complex weak hand logic bypassed

## Next Steps for Integration

1. **Create State Management Adapter** - Bridge pattern for gradual integration
2. **Unify GamePhase Enums** - Single source of truth
3. **Add Dependency Injection** - Wire StatePersistenceManager
4. **Implement Feature Flags** - Control rollout per use case
5. **Update Use Cases** - Replace direct domain calls
6. **Enable State Features** - Activate persistence, snapshots, recovery