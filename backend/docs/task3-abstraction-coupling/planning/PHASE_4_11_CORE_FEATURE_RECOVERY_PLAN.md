# Phase 4.11: Core Feature Recovery Plan

## Critical Issue Summary

During the Domain-Driven Design refactoring (Phases 2-4), we missed implementing the **Reconnection System** - a core game feature that handles:
- Player disconnection → bot conversion
- Message queuing for disconnected players  
- State restoration on reconnect
- Bot deactivation when player returns

This was missed because Phase 0 (Feature Inventory) was incomplete. The reconnection system is **core game behavior**, not optional infrastructure.

## Phase 4.11 Overview

**Name**: Core Feature Recovery  
**Position**: After Phase 4.10, Before Phase 5  
**Duration**: 3-4 days  
**Risk Level**: High (retrofitting into completed phases)  
**Critical**: MUST complete before Phase 5 to avoid architectural inconsistency

### Goals
1. Retrofit reconnection system into clean architecture without breaking existing work
2. Ensure 100% feature parity with original system
3. Maintain clean architecture principles and boundaries
4. Document the recovery process for future reference

### Scope
- Add reconnection support to completed phases (2, 3, 4)
- Update domain models, events, and use cases
- Ensure compatibility with existing adapters
- Create comprehensive tests

## Feature Categorization

### Group 1: Core Game Behavior (Must Recover in Phase 4.11)

1. **Reconnection System**
   - Player disconnect detection
   - Bot activation on disconnect  
   - Message queuing for offline players
   - State restoration on reconnect
   - Bot deactivation on player return

2. **Bot Scheduling/Timing**
   - Bot decision delays (simulate thinking)
   - Turn timers for bots
   - Automatic bot actions on timeout

3. **Message Queue Management**
   - Critical event preservation
   - Queue size limits with priority
   - Delivery on reconnection
   - Queue cleanup

### Group 2: Infrastructure Features (Belongs in Phase 5)

1. **Rate Limiting** - Middleware concern
2. **Event Store & Recovery** - Persistence infrastructure  
3. **Health Monitoring** - System observability
4. **Logging Service** - Cross-cutting infrastructure
5. **Metrics Collection** - Performance monitoring
6. **Middleware Pipeline** - Request processing

## Architecture Layer Updates Required

### Phase 2: Event Layer Updates
```python
# domain/events/__init__.py - Add new events
PlayerDisconnectedEvent
PlayerReconnectedEvent  
BotActivatedEvent
BotDeactivatedEvent
MessageQueuedEvent
QueuedMessagesDeliveredEvent
```

### Phase 3: Domain Layer Updates
```python
# domain/entities/player.py - Add connection state
class Player:
    is_connected: bool
    is_bot: bool  
    disconnect_time: Optional[datetime]
    original_is_bot: bool  # Track if originally human
    
# domain/entities/connection.py - New entity
class PlayerConnection:
    player_id: str
    websocket_id: str
    connection_status: ConnectionStatus
    last_activity: datetime
    queued_messages: List[QueuedMessage]
    
# domain/value_objects/connection_status.py
class ConnectionStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
```

### Phase 4: Application Layer Updates
```python
# application/use_cases/connection/
handle_player_disconnect_use_case.py
handle_player_reconnect_use_case.py
queue_message_for_player_use_case.py
deliver_queued_messages_use_case.py

# application/use_cases/bot/
activate_bot_for_player_use_case.py
deactivate_bot_for_player_use_case.py
schedule_bot_action_use_case.py

# application/services/
reconnection_service.py  # Orchestrates the reconnection flow
message_queue_service.py # Manages message queues
```

## Implementation Checklist

### Step 1: Update Domain Events (Phase 2 retrofit)
- [ ] Create `domain/events/connection_events.py`
  - [ ] Define PlayerDisconnectedEvent
  - [ ] Define PlayerReconnectedEvent
  - [ ] Define BotActivatedEvent
  - [ ] Define BotDeactivatedEvent
- [ ] Create `domain/events/message_queue_events.py`
  - [ ] Define MessageQueuedEvent
  - [ ] Define QueuedMessagesDeliveredEvent
- [ ] Update `domain/events/__init__.py` to export new events
- [ ] Run domain event tests to ensure no regression

### Step 2: Update Domain Models (Phase 3 retrofit)
- [ ] Update `domain/entities/player.py`
  - [ ] Add connection tracking fields
  - [ ] Add methods: disconnect(), reconnect(), activate_bot(), deactivate_bot()
  - [ ] Ensure backward compatibility
- [ ] Create `domain/entities/connection.py`
  - [ ] Define PlayerConnection entity
  - [ ] Add connection lifecycle methods
- [ ] Create `domain/value_objects/connection_status.py`
  - [ ] Define ConnectionStatus enum
  - [ ] Add validation logic
- [ ] Create `domain/entities/message_queue.py`
  - [ ] Define QueuedMessage entity
  - [ ] Define PlayerQueue aggregate
  - [ ] Add queue management logic
- [ ] Update domain model tests

### Step 3: Create Application Use Cases (Phase 4 retrofit)
- [ ] Create connection use cases:
  - [ ] `handle_player_disconnect_use_case.py`
    - Convert player to bot
    - Create message queue
    - Emit disconnect event
  - [ ] `handle_player_reconnect_use_case.py`
    - Restore human control
    - Deliver queued messages
    - Clear queue
    - Emit reconnect event
- [ ] Create message queue use cases:
  - [ ] `queue_message_for_player_use_case.py`
  - [ ] `deliver_queued_messages_use_case.py`
  - [ ] `clear_message_queue_use_case.py`
- [ ] Create bot timing use cases:
  - [ ] `schedule_bot_action_use_case.py`
  - [ ] `execute_bot_action_use_case.py`
- [ ] Update existing game use cases to check connection status

### Step 4: Create Application Services
- [ ] Create `application/services/reconnection_service.py`
  - [ ] Orchestrate disconnect flow
  - [ ] Orchestrate reconnect flow
  - [ ] Coordinate with game state
- [ ] Create `application/services/message_queue_service.py`
  - [ ] Manage all player queues
  - [ ] Handle queue overflow
  - [ ] Prioritize critical messages
- [ ] Update existing services to use reconnection service

### Step 5: Update Repository Interfaces
- [ ] Add to `application/interfaces/repositories.py`:
  - [ ] get_player_connection()
  - [ ] save_player_connection()
  - [ ] get_message_queue()
  - [ ] save_message_queue()
- [ ] Update IPlayerRepository with connection methods

### Step 6: Update Infrastructure (minimal changes)
- [ ] Update `infrastructure/repositories/in_memory_game_repository.py`
  - [ ] Add connection tracking
  - [ ] Add message queue storage
- [ ] Update `infrastructure/adapters/websocket_adapter.py`
  - [ ] Hook into disconnect/reconnect use cases
  - [ ] Integrate message queue delivery

### Step 7: Create Comprehensive Tests
- [ ] Unit tests for all new domain entities
- [ ] Unit tests for all new use cases
- [ ] Integration tests for reconnection flow
- [ ] E2E test simulating full disconnect/reconnect cycle
- [ ] Performance test for message queue under load

### Step 8: Update Documentation
- [ ] Update Phase 0 feature inventory
- [ ] Update architecture diagrams
- [ ] Create reconnection flow diagram
- [ ] Update API documentation
- [ ] Add to migration guide

## Documents Requiring Updates

1. **Phase Tracking Documents**
   - `TASK_3_ABSTRACTION_COUPLING_PLAN.md` - Add Phase 4.11
   - `PHASE_4_STATUS.md` - Mark Phase 4 incomplete until 4.11 done
   - `docs/task3-abstraction-coupling/README.md` - Update current status

2. **Feature Inventories**
   - `PHASE_0_FEATURE_INVENTORY.md` - Add missed features
   - `websocket_contracts.py` - Already has contracts, needs validation
   - `FEATURE_MATRIX.md` - Add reconnection system

3. **Architecture Documents**
   - `docs/clean-architecture/README.md` - Add reconnection section
   - `docs/clean-architecture/MIGRATION_GUIDE.md` - Add recovery steps
   - `ARCHITECTURE_DECISIONS.md` - Document why these are core features

4. **Test Documents**
   - `test_reconnection_flow.py` - Validate against new architecture
   - `CONTRACT_TESTING_README.md` - Ensure contracts still valid
   - Add new test files to test inventory

5. **Implementation Guides**
   - `WS_INTEGRATION_GUIDE.md` - Update with reconnection handling
   - `ADAPTER_DEPLOYMENT_RUNBOOK.md` - Add reconnection adapter config
   - Create `RECONNECTION_RECOVERY_GUIDE.md`

## Risk Mitigation

### Risk 1: Breaking Existing Work
- **Mitigation**: All changes are additive, no modifications to existing interfaces
- **Validation**: Run full test suite after each step

### Risk 2: Architectural Inconsistency  
- **Mitigation**: Follow established patterns from Phases 2-4
- **Validation**: Architecture review after implementation

### Risk 3: Missing Edge Cases
- **Mitigation**: Port ALL tests from original system
- **Validation**: Shadow mode comparison testing

### Risk 4: Performance Impact
- **Mitigation**: Use same patterns as existing features
- **Validation**: Performance benchmarks before/after

## Success Criteria

1. **Feature Parity**: Reconnection works identically to original system
2. **Clean Architecture**: Features properly separated into layers
3. **Test Coverage**: 100% coverage of reconnection flows
4. **Performance**: No degradation vs original system
5. **Documentation**: Complete documentation of recovery process

## Why Before Phase 5?

1. **Core vs Infrastructure**: Reconnection is core game behavior, not infrastructure
2. **Dependencies**: Phase 5 infrastructure may depend on these features
3. **Testing**: Need complete feature set before infrastructure testing
4. **Risk**: Harder to retrofit after infrastructure is built
5. **Consistency**: Maintains phase progression integrity

## Timeline

- Day 1: Domain events and models (Steps 1-2)
- Day 2: Use cases and services (Steps 3-4)  
- Day 3: Infrastructure updates and testing (Steps 5-7)
- Day 4: Documentation and validation (Step 8)

## Next Steps

1. Get approval for Phase 4.11 addition
2. Update all tracking documents
3. Begin implementation following checklist
4. Daily progress updates
5. Final validation before Phase 5

---

**Critical Note**: This recovery phase is essential to prevent loss of core functionality. The reconnection system is not optional - it's a fundamental part of the game experience that ensures players can recover from network issues without losing their game state.