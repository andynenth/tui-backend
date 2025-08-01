# Characterization Tests for State Management Integration

## Purpose

These characterization tests document the EXACT current behavior of the system before any state management integration. They serve as a safety net to ensure we don't break existing functionality during the integration process.

## Test Organization

### 1. `test_start_game_current_behavior.py`
- Documents how `StartGameUseCase` works today
- Shows direct domain calls without state persistence
- Captures exact event emission order
- Verifies no state management is currently used

### 2. `test_state_persistence_isolation.py`
- Tests `StatePersistenceManager` infrastructure in isolation
- Verifies it can handle game state transitions
- Confirms automatic phase persistence works
- Tests recovery and snapshot capabilities

### 3. `test_golden_master_game_flow.py`
- Captures complete game flow as golden master
- Documents all state transitions
- Maps integration points for each use case
- Identifies GamePhase enum duplication

## Key Findings

### Current Architecture
1. **Direct Domain Calls**: `StartGameUseCase` calls `game.start_round()` directly (line 149)
2. **No State Persistence**: Zero integration with `StatePersistenceManager`
3. **Duplicate Enums**: Two different `GamePhase` enums exist
4. **Event Order**: Specific sequence must be maintained

### Infrastructure Capabilities (Unused)
1. **Automatic Persistence**: `persist_on_phase_change: True` ready to use
2. **State Recovery**: Full snapshot and recovery mechanisms available
3. **Event Sourcing**: Complete audit trail capabilities
4. **Performance Optimizations**: Caching and batching built-in

## Running the Tests

```bash
# Run all characterization tests
pytest tests/characterization/ -v

# Run specific test file
pytest tests/characterization/test_start_game_current_behavior.py -v

# Run with coverage
pytest tests/characterization/ --cov=application.use_cases.game --cov=infrastructure.state_persistence
```

## Using Tests During Integration

1. **Before Changes**: Run all tests to ensure they pass
2. **During Integration**: Tests should continue to pass (with feature flags OFF)
3. **After Integration**: Same external behavior, but with state tracking
4. **Feature Flag Testing**: New tests verify state management when enabled

## Test Maintenance

These tests are intentionally rigid - they should ONLY change if we intentionally want to change existing behavior. Any unintentional changes indicate a breaking change that needs investigation.