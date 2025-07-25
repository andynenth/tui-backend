# Phase 4: Application Layer Implementation Plan

**Status**: 📋 PLANNING  
**Prerequisites**: Phase 1 (Adapters) ✅ COMPLETE | Phase 2 (Events) ✅ COMPLETE | Phase 3 (Domain) ✅ COMPLETE  
**Objective**: Create application layer with use cases to orchestrate domain logic  
**Estimated Duration**: 3-4 days  

## 1. Overview & Objective

### Purpose
Phase 4 introduces the application layer following clean architecture principles. This layer contains use cases (application services) that orchestrate domain entities and services to implement business workflows. The application layer acts as the coordinator between the API layer (adapters) and the domain layer, handling transaction boundaries, cross-cutting concerns, and complex workflows.

### Key Objectives
1. **Use Case Implementation**: Create use cases for all 22 adapter operations
2. **Domain Orchestration**: Coordinate domain entities and services to fulfill business requirements
3. **Transaction Management**: Define clear transaction boundaries for atomic operations
4. **Cross-Cutting Concerns**: Handle authorization, validation, and error handling at application level
5. **Maintain Compatibility**: All changes behind adapters with zero frontend impact

### How It Fits the Overall Strategy
- **Phase 0**: Established testing infrastructure to verify behavior preservation ✅
- **Phase 1**: Created adapter layer providing clean API boundaries ✅
- **Phase 2**: Implemented event system for decoupled communication ✅
- **Phase 3**: Extracted pure domain logic into entities and services ✅
- **Phase 4**: Build application layer to orchestrate domain (THIS PHASE)
- **Phase 5**: Implement infrastructure layer with repositories
- **Phase 6**: Gradual cutover using feature flags
- **Phase 7**: Complete migration and cleanup

## 2. Scope Definition

### What WILL Be Done

1. **Use Case Creation (22 use cases)**
   ```
   backend/application/use_cases/
   ├── connection/
   │   ├── handle_ping.py
   │   ├── mark_client_ready.py
   │   ├── acknowledge_message.py
   │   └── sync_client_state.py
   ├── room_management/
   │   ├── create_room.py
   │   ├── join_room.py
   │   ├── leave_room.py
   │   ├── get_room_state.py
   │   ├── add_bot_player.py
   │   └── remove_player.py
   ├── lobby/
   │   ├── get_room_list.py
   │   └── get_room_details.py
   └── game/
       ├── start_game.py
       ├── declare_piles.py
       ├── play_pieces.py
       ├── request_redeal.py
       ├── accept_redeal.py
       ├── decline_redeal.py
       ├── handle_redeal_decision.py
       ├── mark_player_ready.py
       └── leave_game.py
   ```

2. **Application Services**
   - `GameApplicationService`: High-level game operations
   - `RoomApplicationService`: Room lifecycle management
   - `LobbyApplicationService`: Room discovery and matchmaking
   - `ConnectionApplicationService`: Client connection management

3. **Application Interfaces**
   - Define interfaces for infrastructure services needed by use cases
   - Create DTOs for data transfer between layers
   - Implement request/response models for use cases

4. **Adapter Integration**
   - Update all 22 adapters to call use cases instead of legacy handlers
   - Implement feature flags for each use case
   - Add shadow mode comparison for validation

5. **Error Handling**
   - Application-specific exceptions
   - Error mapping to WebSocket error codes
   - Consistent error response format

6. **Testing**
   - Unit tests for each use case
   - Integration tests for adapter-to-use-case flow
   - Contract tests to ensure WebSocket compatibility

### What Will NOT Be Done

1. **Repository Implementations**: Deferred to Phase 5
   - Use cases will use repository interfaces only
   - Actual persistence remains in legacy code

2. **Infrastructure Services**: Deferred to Phase 5
   - No new notification systems
   - No new metric collectors
   - Continue using existing infrastructure

3. **State Machine Refactoring**: Out of scope
   - Keep current state machine as infrastructure
   - Use cases coordinate with existing state machine

4. **Bot Strategy Extraction**: Deferred to later phase
   - Bot logic remains in current location
   - Focus on core game operations first

5. **WebSocket Protocol Changes**: Strictly forbidden
   - No changes to message formats
   - No new event types
   - 100% backward compatibility required

6. **Direct Database Access**: Not allowed
   - All persistence through repository interfaces
   - No SQL or direct storage operations

## 3. Alignment Check

### Connection to Phase 0
- ✅ Use comprehensive test suite to verify behavior preservation
- ✅ Run WebSocket contract tests after each use case
- ✅ Use golden master tests to validate outputs
- ✅ Performance benchmarks to track overhead

### Connection to Phase 1
- ✅ Each adapter maps to one or more use cases
- ✅ Adapters become thin delegation layers
- ✅ Feature flags control adapter behavior
- ✅ Shadow mode compares old vs new paths
- ✅ Maintains 44% performance overhead baseline

### Connection to Phase 2
- ✅ Use cases publish domain events
- ✅ Event handlers trigger infrastructure actions
- ✅ Events provide audit trail for use case execution
- ✅ Async event processing for notifications

### Connection to Phase 3
- ✅ Use cases orchestrate domain entities (Room, Game, Player)
- ✅ Call domain services (GameRules, ScoringService, TurnResolution)
- ✅ Work with value objects (Declaration, HandStrength, etc.)
- ✅ Respect aggregate boundaries defined in domain

### Preparation for Phase 5
- Define clear repository interfaces for infrastructure
- Identify all infrastructure service needs
- Document persistence requirements
- Prepare for repository implementations

## 4. Conflicts & Redundancy Review

### Identified Challenges

1. **Transaction Boundaries**
   - Current: Implicit transactions in state machine
   - Challenge: Defining explicit boundaries in use cases
   - Resolution: Each use case represents one transaction

2. **Event vs Direct Updates**
   - Current: Mix of direct updates and events
   - Challenge: Ensuring consistency
   - Resolution: Use cases always emit events, infrastructure reacts

3. **Authorization Placement**
   - Current: Scattered across handlers
   - Challenge: Centralizing without duplication
   - Resolution: Application layer handles all authorization

4. **Error Code Mapping**
   - Current: Hardcoded error responses
   - Challenge: Maintaining compatibility
   - Resolution: Error mapper service in application layer

### Documentation Updates Needed
1. Update `CLAUDE.md` with application layer patterns
2. Create `APPLICATION_LAYER_GUIDE.md` for developers
3. Update architecture diagrams
4. Document use case specifications

## 5. Detailed Implementation Checklist

### Phase 4.1: Application Structure Setup
- [ ] Create `backend/application/` directory structure
- [ ] Set up Python packages with `__init__.py` files
- [ ] Create base classes:
  - [ ] `UseCase` base class with execute method
  - [ ] `ApplicationService` base class
  - [ ] `ApplicationException` hierarchy
- [ ] Define common interfaces:
  - [ ] `UnitOfWork` for transaction management
  - [ ] `EventPublisher` for domain events
  - [ ] `Logger` for structured logging
- [ ] Create DTO (Data Transfer Object) models:
  - [ ] Request DTOs for each use case
  - [ ] Response DTOs with proper serialization
  - [ ] Validation decorators/utilities

### Phase 4.2: Connection Use Cases
- [ ] Implement `HandlePingUseCase`
  - [ ] Accept ping request
  - [ ] Update last activity timestamp
  - [ ] Return pong response
  - [ ] Unit tests (3 minimum)
- [ ] Implement `MarkClientReadyUseCase`
  - [ ] Validate client state
  - [ ] Update player ready status
  - [ ] Emit ClientReady event
  - [ ] Unit tests (3 minimum)
- [ ] Implement `AcknowledgeMessageUseCase`
  - [ ] Track message acknowledgments
  - [ ] Handle retransmission logic
  - [ ] Unit tests (3 minimum)
- [ ] Implement `SyncClientStateUseCase`
  - [ ] Gather current game state
  - [ ] Format for client consumption
  - [ ] Handle partial sync requests
  - [ ] Unit tests (5 minimum)
- [ ] Update connection adapters to use use cases
- [ ] Integration tests for connection flow

### Phase 4.3: Room Management Use Cases
- [ ] Implement `CreateRoomUseCase`
  - [ ] Validate room parameters
  - [ ] Create Room aggregate
  - [ ] Assign room code
  - [ ] Emit RoomCreated event
  - [ ] Unit tests (5 minimum)
- [ ] Implement `JoinRoomUseCase`
  - [ ] Validate room exists and has space
  - [ ] Add player to room
  - [ ] Handle host migration if needed
  - [ ] Emit PlayerJoined event
  - [ ] Unit tests (7 minimum)
- [ ] Implement `LeaveRoomUseCase`
  - [ ] Remove player from room
  - [ ] Handle host migration
  - [ ] Clean up empty rooms
  - [ ] Emit PlayerLeft event
  - [ ] Unit tests (6 minimum)
- [ ] Implement `GetRoomStateUseCase`
  - [ ] Retrieve room aggregate
  - [ ] Format state for client
  - [ ] Include game state if active
  - [ ] Unit tests (4 minimum)
- [ ] Implement `AddBotPlayerUseCase`
  - [ ] Validate room has space
  - [ ] Create bot player
  - [ ] Assign to room
  - [ ] Emit BotAdded event
  - [ ] Unit tests (4 minimum)
- [ ] Implement `RemovePlayerUseCase`
  - [ ] Validate permissions
  - [ ] Remove specified player
  - [ ] Handle game state updates
  - [ ] Emit PlayerRemoved event
  - [ ] Unit tests (5 minimum)
- [ ] Update room adapters to use use cases
- [ ] Integration tests for room management

### Phase 4.4: Lobby Use Cases
- [ ] Implement `GetRoomListUseCase`
  - [ ] Query available rooms
  - [ ] Filter by criteria
  - [ ] Format room summaries
  - [ ] Unit tests (4 minimum)
- [ ] Implement `GetRoomDetailsUseCase`
  - [ ] Retrieve specific room
  - [ ] Include player details
  - [ ] Check visibility permissions
  - [ ] Unit tests (3 minimum)
- [ ] Update lobby adapters to use use cases
- [ ] Integration tests for lobby operations

### Phase 4.5: Game Flow Use Cases (Part 1)
- [ ] Implement `StartGameUseCase`
  - [ ] Validate room ready to start
  - [ ] Create Game entity
  - [ ] Deal initial pieces
  - [ ] Emit GameStarted event
  - [ ] Unit tests (6 minimum)
- [ ] Implement `DeclarePilesUseCase`
  - [ ] Validate declaration timing
  - [ ] Apply declaration rules
  - [ ] Update game state
  - [ ] Emit DeclarationMade event
  - [ ] Unit tests (8 minimum)
- [ ] Implement `PlayPiecesUseCase`
  - [ ] Validate play legality
  - [ ] Apply game rules
  - [ ] Determine turn winner
  - [ ] Update scores
  - [ ] Emit PiecesPlayed event
  - [ ] Unit tests (12 minimum)
- [ ] Update game adapters (part 1)
- [ ] Integration tests for basic game flow

### Phase 4.6: Game Flow Use Cases (Part 2)
- [ ] Implement `RequestRedealUseCase`
  - [ ] Check weak hand conditions
  - [ ] Initiate redeal voting
  - [ ] Set timeout for responses
  - [ ] Emit RedealRequested event
  - [ ] Unit tests (5 minimum)
- [ ] Implement `AcceptRedealUseCase`
  - [ ] Record acceptance vote
  - [ ] Check if all voted
  - [ ] Trigger redeal if unanimous
  - [ ] Emit RedealAccepted event
  - [ ] Unit tests (4 minimum)
- [ ] Implement `DeclineRedealUseCase`
  - [ ] Record decline vote
  - [ ] Cancel redeal process
  - [ ] Continue with current hands
  - [ ] Emit RedealDeclined event
  - [ ] Unit tests (4 minimum)
- [ ] Implement `HandleRedealDecisionUseCase`
  - [ ] Process timeout scenarios
  - [ ] Finalize redeal decision
  - [ ] Update game state
  - [ ] Unit tests (5 minimum)
- [ ] Implement `MarkPlayerReadyUseCase`
  - [ ] Update player ready state
  - [ ] Check if all ready
  - [ ] Trigger next phase
  - [ ] Unit tests (4 minimum)
- [ ] Implement `LeaveGameUseCase`
  - [ ] Handle mid-game departure
  - [ ] Convert to bot if needed
  - [ ] Update game state
  - [ ] Emit PlayerLeftGame event
  - [ ] Unit tests (5 minimum)
- [ ] Update remaining game adapters
- [ ] Integration tests for complex game flows

### Phase 4.7: Application Services
- [ ] Implement `GameApplicationService`
  - [ ] High-level game operations
  - [ ] Coordinate multiple use cases
  - [ ] Transaction management
  - [ ] Unit tests (8 minimum)
- [ ] Implement `RoomApplicationService`
  - [ ] Room lifecycle management
  - [ ] Player management
  - [ ] State coordination
  - [ ] Unit tests (6 minimum)
- [ ] Implement `LobbyApplicationService`
  - [ ] Room discovery
  - [ ] Matchmaking logic
  - [ ] Statistics gathering
  - [ ] Unit tests (4 minimum)
- [ ] Implement `ConnectionApplicationService`
  - [ ] Connection health monitoring
  - [ ] Reconnection handling
  - [ ] State synchronization
  - [ ] Unit tests (4 minimum)

### Phase 4.8: Infrastructure Integration
- [ ] Create adapter-to-use-case mapping
  - [ ] Wire up all 22 adapters
  - [ ] Implement delegation logic
  - [ ] Add error handling
- [ ] Implement feature flags
  - [ ] Flag per use case
  - [ ] Runtime toggle capability
  - [ ] Fallback to legacy handlers
- [ ] Add shadow mode
  - [ ] Run both paths in parallel
  - [ ] Compare results
  - [ ] Log discrepancies
  - [ ] Performance metrics
- [ ] Create application context
  - [ ] Dependency injection setup
  - [ ] Service registration
  - [ ] Lifecycle management

### Phase 4.9: Testing & Validation
- [ ] Run all unit tests (target: 150+ tests)
  - [ ] Use case tests
  - [ ] Service tests
  - [ ] DTO validation tests
- [ ] Run integration tests
  - [ ] Adapter to use case flow
  - [ ] End-to-end scenarios
  - [ ] Error handling paths
- [ ] Run contract tests
  - [ ] All WebSocket contracts pass
  - [ ] Message formats unchanged
  - [ ] Error codes preserved
- [ ] Performance testing
  - [ ] Measure use case overhead
  - [ ] Compare with 44% baseline
  - [ ] Identify bottlenecks
- [ ] Shadow mode validation
  - [ ] Run for all operations
  - [ ] Verify identical outputs
  - [ ] Document any discrepancies

### Phase 4.10: Documentation & Rollout Preparation
- [ ] Create developer documentation
  - [ ] `APPLICATION_LAYER_GUIDE.md`
  - [ ] Use case specifications
  - [ ] Service interaction diagrams
  - [ ] Error handling guide
- [ ] Update architecture documentation
  - [ ] Update `CLAUDE.md`
  - [ ] Create sequence diagrams
  - [ ] Document patterns used
- [ ] Create operations runbook
  - [ ] Feature flag configuration
  - [ ] Monitoring guidelines
  - [ ] Rollback procedures
  - [ ] Performance baselines
- [ ] Prepare rollout plan
  - [ ] Gradual activation schedule
  - [ ] Success metrics
  - [ ] Risk mitigation steps

## 6. Documentation Update Plan

### During Implementation
1. **Create APPLICATION_LAYER_GUIDE.md**
   - Use case patterns and conventions
   - Service organization principles
   - Transaction management approach
   - Error handling strategies

2. **Update Existing Documentation**
   - CLAUDE.md: Add application layer section
   - Architecture diagrams: Show new layer
   - API documentation: Note internal changes

3. **Create Use Case Specifications**
   - One file per use case
   - Input/output documentation
   - Business rules enforced
   - Error conditions

### After Phase Completion
1. **Update Status Documents**
   - Create PHASE_4_COMPLETE.md
   - Document implementation decisions
   - Record performance metrics
   - List all use cases created

2. **Create Integration Guide**
   - How to add new use cases
   - Testing requirements
   - Feature flag setup
   - Rollout procedures

## Success Criteria
1. ✅ All 22 adapters integrated with use cases
2. ✅ 100% WebSocket contract compatibility maintained
3. ✅ All tests passing (unit, integration, contract)
4. ✅ Performance overhead within acceptable range (<60%)
5. ✅ Shadow mode shows identical behavior
6. ✅ Feature flags enable instant rollback
7. ✅ Zero frontend changes required
8. ✅ Documentation complete and accurate

## Risk Mitigation
1. **Complex Use Cases**: Start with simple ones, build complexity
2. **Performance Regression**: Profile each use case, optimize hot paths
3. **Integration Issues**: Extensive integration testing at each step
4. **State Inconsistency**: Clear transaction boundaries, event sourcing
5. **Rollback Complexity**: Feature flags at use case level

## Implementation Order
1. **Week 1, Day 1**: Structure setup and connection use cases
2. **Week 1, Day 2**: Room management use cases
3. **Week 1, Day 3**: Lobby and basic game use cases
4. **Week 1, Day 4**: Complex game use cases and services
5. **Week 1, Day 5**: Integration, testing, and documentation

---

**Note**: Phase 4 establishes the application layer that orchestrates the domain. This layer provides clear business workflows while maintaining complete backward compatibility through the adapter pattern established in Phase 1.