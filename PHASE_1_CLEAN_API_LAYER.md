# Phase 1: Clean API Layer - Implementation Checklist

## Overview
Create API adapters that work alongside existing WebSocket handlers. This phase establishes the foundation for clean architecture without breaking the current system.

**Goal**: Route 10% of WebSocket traffic through clean architecture adapters while maintaining 100% compatibility.

## Pre-Implementation Checklist

### Phase 0 Completion ✓
- [ ] **Feature Inventory Complete** (from [PHASE_0_FEATURE_INVENTORY.md](./PHASE_0_FEATURE_INVENTORY.md))
  - [ ] All WebSocket messages documented
  - [ ] All game features cataloged
  - [ ] All edge cases identified
  - [ ] Feature usage metrics collected
- [ ] **Behavioral Test Suite Ready**
  - [ ] Core feature tests passing
  - [ ] Edge case tests documented
  - [ ] Performance benchmarks established
- [ ] **Shadow Mode Infrastructure**
  - [ ] Comparison framework implemented
  - [ ] Discrepancy logging ready
  - [ ] Monitoring dashboards set up

### Prerequisites ✓
- [ ] Current WebSocket handler (`backend/api/routes/ws.py`) is working correctly
- [ ] Feature flag system is available or can be created
- [ ] Logging infrastructure is set up for monitoring
- [ ] Test environment available for validation

### Understanding Current System ✓
- [ ] Document all WebSocket message types handled by `ws.py` *(Should be complete from Phase 0)*
- [ ] List all direct dependencies in current handler *(Should be complete from Phase 0)*
- [ ] Identify global state access patterns *(Should be complete from Phase 0)*
- [ ] Map current message flow: Frontend → WebSocket → Handler → Response *(Should be complete from Phase 0)*

## Implementation Tasks

### 1. Create Feature Flag System
- [ ] Create `backend/config/feature_flags.py`
  ```python
  class FeatureFlags:
      USE_CLEAN_API_ADAPTER = False
      API_ADAPTER_PERCENTAGE = 10  # Route 10% through adapter
  ```
- [ ] Add environment variable support for flags
- [ ] Create helper function to check if request should use adapter
- [ ] Test flag toggling without code changes

### 2. Create Base Adapter Infrastructure
- [ ] Create `backend/api/adapters/` directory
- [ ] Create `backend/api/adapters/base_adapter.py`
  ```python
  class BaseWebSocketAdapter:
      def __init__(self, legacy_handler):
          self.legacy_handler = legacy_handler
      
      async def handle_message(self, websocket, message):
          # Base routing logic
          pass
  ```
- [ ] Implement message routing logic based on feature flags
- [ ] Add comprehensive logging for adapter usage
- [ ] Create metrics collection for adapter performance

### 3. Create Message Type Adapters
- [ ] Create `backend/api/adapters/room_adapter.py`
  - [ ] Handle `create_room` message
  - [ ] Handle `join_room` message
  - [ ] Handle `leave_room` message
  - [ ] Forward to legacy handler initially
- [ ] Create `backend/api/adapters/game_adapter.py`
  - [ ] Handle `start_game` message
  - [ ] Handle `play` message
  - [ ] Handle `declare` message
  - [ ] Forward to legacy handler initially
- [ ] Test each adapter with real WebSocket messages

### 4. Integrate Adapters with Existing WebSocket Handler
- [ ] Modify `backend/api/routes/ws.py` to check feature flags
- [ ] Add adapter initialization in WebSocket connection
- [ ] Route percentage of traffic through adapters
- [ ] Ensure fallback to legacy handler on any error
- [ ] Add A/B testing metrics collection

### 5. Create Command Pattern Foundation
- [ ] Create `backend/api/commands/` directory
- [ ] Create `backend/api/commands/base_command.py`
  ```python
  @dataclass
  class Command:
      room_id: str
      player_id: str
      timestamp: datetime
  ```
- [ ] Create command classes for each message type:
  - [ ] `CreateRoomCommand`
  - [ ] `JoinRoomCommand`
  - [ ] `StartGameCommand`
  - [ ] `PlayTurnCommand`
  - [ ] `DeclareCommand`
- [ ] Implement command validation
- [ ] Add command serialization/deserialization

### Frontend Compatibility Note
**CRITICAL**: The frontend uses WebSocket exclusively for all game operations. The adapter pattern MUST:
- Preserve exact message structure for all WebSocket events
- Maintain identical response formats
- Keep broadcast event names unchanged
- Preserve event ordering and timing
- Return same error formats

Example compatibility preservation:
```python
# Frontend sends: {"action": "declare", "data": {"player_name": "Alice", "value": 3}}
# Backend MUST respond with exact same format as current system
# No field renaming, no structure changes, no new required fields
```

### 6. Create Command Bus (Simple Version)
- [ ] Create `backend/api/commands/command_bus.py`
- [ ] Implement basic command routing
- [ ] Add command logging and metrics
- [ ] Create command handler registry
- [ ] Test command execution flow

### 7. Integrate with Shadow Mode (From Phase 0)
- [ ] Connect adapters to shadow mode infrastructure
- [ ] Enable comparison between adapter and legacy paths
- [ ] Set up alerts for any behavioral differences
- [ ] Create runbook for handling discrepancies
- [ ] Test shadow mode with real traffic

## Integration Tasks

### 1. Wire Adapters to Use Commands
- [ ] Update room adapter to create commands
- [ ] Update game adapter to create commands
- [ ] Implement command-to-legacy-call translation
- [ ] Test end-to-end flow: WebSocket → Adapter → Command → Legacy Handler

### 2. Add Monitoring and Observability
- [ ] Add request ID tracking through adapter flow
- [ ] Implement performance timing for adapter vs direct calls
- [ ] Create dashboard or logs for monitoring adapter usage
- [ ] Set up alerts for adapter errors

### 3. Implement Gradual Rollout
- [ ] Start with 1% of traffic through adapters
- [ ] Monitor for 24 hours, check metrics
- [ ] Increase to 5% if stable
- [ ] Monitor for 24 hours, check metrics
- [ ] Increase to 10% if stable
- [ ] Document any issues found

## Testing Checklist

### Behavioral Test Validation (From Phase 0)
- [ ] Run full behavioral test suite with adapters enabled
- [ ] Verify all tests still pass with adapter layer
- [ ] Compare test execution time (should be similar)
- [ ] Document any behavioral differences found
- [ ] Update tests if legitimate improvements made

### Unit Tests
- [ ] Test feature flag logic
- [ ] Test adapter routing decisions
- [ ] Test command creation and validation
- [ ] Test command bus routing
- [ ] Test error handling and fallback

### Integration Tests
- [ ] Test WebSocket connection with adapters
- [ ] Test all message types through adapters
- [ ] Test adapter performance vs direct calls
- [ ] Test feature flag changes during active connections
- [ ] Test error scenarios and recovery

### End-to-End Tests
- [ ] Create test script that simulates real game flow
- [ ] Run test with adapters enabled at various percentages
- [ ] Verify no functional differences between adapter and direct paths
- [ ] Load test to ensure no performance degradation

## Rollback Plan

### If Issues Occur:
1. [ ] Set feature flag `USE_CLEAN_API_ADAPTER = False`
2. [ ] All traffic immediately routes through legacy handler
3. [ ] No code deployment needed for rollback
4. [ ] Investigate issues in non-production environment

### Rollback Verification:
- [ ] Confirm all traffic going through legacy path
- [ ] Check that no adapter code is executing
- [ ] Verify game functionality is normal
- [ ] Document lessons learned

## Success Criteria

### Technical Success ✓
- [ ] 10% of traffic successfully routed through adapters
- [ ] No increase in error rate
- [ ] No performance degradation (< 5ms added latency)
- [ ] All message types handled correctly
- [ ] Clean separation between adapter and legacy code

### Architecture Success ✓
- [ ] Command pattern established and working
- [ ] No direct dependencies from adapters to game engine
- [ ] Clear boundary between API and business logic
- [ ] Foundation ready for Phase 2 (Event System)

### Operational Success ✓
- [ ] Monitoring and metrics in place
- [ ] Team comfortable with adapter pattern
- [ ] Documentation updated
- [ ] Rollback tested and verified

## Post-Implementation Review

### Questions to Answer:
1. What issues were discovered during implementation?
2. How did the adapter pattern help or hinder?
3. What would we do differently?
4. Is the system ready for Phase 2?

### Metrics to Collect:
- Total messages processed through adapters
- Error rate comparison (adapter vs legacy)
- Performance metrics (latency, throughput)
- Developer hours spent on implementation
- Number of rollbacks needed

## Next Phase Gate

Before proceeding to Phase 2, ensure:
- [ ] All success criteria met
- [ ] No outstanding issues with adapters
- [ ] Team consensus on approach
- [ ] Phase 2 plan reviewed and approved
- [ ] **All contract tests pass with 100% compatibility**
- [ ] **Golden master comparisons show identical behavior**
- [ ] **No regression in WebSocket message formats or timing**

### Contract Testing Checklist
- [ ] Golden masters captured for all 21 WebSocket message types
- [ ] Contract tests integrated into CI/CD pipeline
- [ ] All adapters pass parallel comparison tests
- [ ] Performance benchmarks within acceptable range (< 20% overhead)
- [ ] Error handling matches exactly (same messages, same formats)

---

**Remember**: The goal is not to replace the existing system yet, but to create a parallel path that we can gradually migrate to. Every step should be reversible, and the system should remain fully functional throughout the process.