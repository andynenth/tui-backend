# Phase 3: Domain Layer Implementation Plan

**Status**: ✅ COMPLETE AND TESTED (2025-07-25)  
**Prerequisites**: Phase 1 (Adapters) ✅ COMPLETE | Phase 2 (Events) ✅ COMPLETE  
**Objective**: Extract pure domain logic from infrastructure dependencies  
**Test Results**: 162/162 tests passing (100%)  

## 1. Overview & Objective

### Purpose
Phase 3 focuses on extracting the core game logic into a pure domain layer that has zero dependencies on infrastructure (WebSocket, database, etc.). This phase builds upon the adapter and event foundations from Phases 1-2 to create truly isolated business logic.

### Key Objectives
1. **Pure Domain Logic**: Extract game rules into infrastructure-free classes
2. **Domain Services**: Create services for complex domain operations
3. **Value Objects**: Implement immutable value objects for domain concepts
4. **Domain Interfaces**: Define ports for infrastructure dependencies
5. **Maintain Compatibility**: All changes behind adapters - zero frontend impact

### How It Fits the Overall Strategy
- **Phase 0**: Established testing infrastructure ✅
- **Phase 1**: Created adapter layer for API compatibility ✅
- **Phase 2**: Implemented event system for decoupling ✅
- **Phase 3**: Extract pure domain logic (THIS PHASE)
- **Phase 4**: Build application layer (use cases)
- **Phase 5**: Complete infrastructure separation

## 2. Scope Definition

### What WILL Be Done
1. **Domain Entity Extraction**
   - Extract `Game` class with pure game logic
   - Extract `Player` entity with player state
   - Extract `Piece` value object
   - Extract `Room` aggregate root
   - Remove all infrastructure dependencies

2. **Domain Services Creation**
   - `GameRules` service for rule validation
   - `ScoringService` for score calculations
   - `TurnResolution` service for turn logic
   - `WinConditions` service for game ending

3. **Value Objects Implementation**
   - `PlayResult` for turn outcomes
   - `GamePhase` enumeration
   - `Declaration` for pile declarations
   - `Score` for immutable scoring

4. **Domain Events Enhancement**
   - Ensure all state changes emit events
   - Events carry complete state change info
   - No infrastructure data in events

5. **Repository Interfaces**
   - Define `GameRepository` interface
   - Define `RoomRepository` interface
   - Keep interfaces in domain layer

### What Will NOT Be Done
1. **Repository Implementations**: Deferred to Phase 5
2. **Database Changes**: No persistence layer modifications
3. **State Machine Refactor**: Keep current state machine as infrastructure
4. **Bot Logic Extraction**: Keep bots in infrastructure for now
5. **WebSocket Changes**: Zero modifications to API layer
6. **Breaking Changes**: Everything behind existing adapters

## 3. Alignment Check

### Connection to Phase 0
- ✅ Use contract tests to verify game logic unchanged
- ✅ Behavioral tests ensure game rules preserved
- ✅ Golden masters validate outputs remain identical

### Connection to Phase 1
- ✅ Adapters call domain logic instead of direct implementation
- ✅ Feature flags control domain usage
- ✅ Shadow mode can compare old vs new logic
- ✅ Performance monitoring for domain operations

### Connection to Phase 2
- ✅ Domain emits events for all state changes
- ✅ Events trigger infrastructure actions
- ✅ Event handlers update external systems
- ✅ Clean separation via event boundaries

### Preparation for Phase 4
- Sets up clean domain for use cases to orchestrate
- Defines clear interfaces for application layer
- Provides testable domain logic
- Enables transaction script pattern

## 4. Conflicts & Redundancy Review

### Identified Issues
1. **State Machine Coupling**
   - Current: State machine directly modifies game state
   - Conflict: Domain should be self-contained
   - Resolution: State machine becomes infrastructure orchestrator

2. **Game-Room Circular Dependency**
   - Current: Game knows about Room, Room contains Game
   - Conflict: Tight coupling between aggregates
   - Resolution: Room as aggregate root, Game as entity within

3. **Direct State Mutation**
   - Current: `game.turn_number += 1` scattered everywhere
   - Conflict: No encapsulation of state changes
   - Resolution: Explicit methods with event emission

4. **Bot Manager Integration**
   - Current: Bot logic mixed with game logic
   - Conflict: AI strategy is infrastructure concern
   - Resolution: Extract bot decisions to infrastructure

### Documentation Updates Needed
1. Create DOMAIN_MODEL.md showing entity relationships
2. Update CLAUDE.md with domain patterns
3. Document aggregate boundaries
4. Create domain glossary of terms

## 5. Detailed Implementation Checklist

### Phase 3.1: Domain Entity Extraction
- [x] Create `backend/domain/entities/` directory structure
- [x] Extract Game entity (24 tests passing)
  - [x] Create pure `Game` class without infrastructure imports
  - [x] Move game state (pieces, scores, turn number)
  - [x] Implement state change methods (play_turn, declare, etc.)
  - [x] Emit domain events for all changes
  - [x] Remove direct broadcast calls
- [x] Extract Player entity (16 tests passing)
  - [x] Create `Player` class with player state
  - [x] Include hand, declarations, connection status
  - [x] Implement player actions as methods
  - [x] Remove WebSocket references
- [x] Extract Piece value object (12 tests passing)
  - [x] Create immutable `Piece` class
  - [x] Implement piece comparison logic
  - [x] Add piece validation rules
- [x] Extract Room aggregate (20 tests passing)
  - [x] Create `Room` as aggregate root
  - [x] Include Game as entity within Room
  - [x] Manage player lifecycle
  - [x] Coordinate game phases

### Phase 3.2: Domain Services Implementation
- [x] Create `backend/domain/services/` directory
- [x] Implement GameRules service (17 tests passing)
  - [x] Extract validation logic from scattered locations
  - [x] Create pure functions for rule checking
  - [x] Include weak hand detection
  - [x] Validate plays and declarations
- [x] Implement ScoringService (11 tests passing)
  - [x] Extract scoring logic from `scoring.py`
  - [x] Create pure scoring calculations
  - [x] Handle multipliers and special cases
  - [x] Return immutable score results
- [x] Implement TurnResolution service (12 tests passing)
  - [x] Extract turn comparison logic
  - [x] Determine turn winners
  - [x] Handle special piece rules
  - [x] Return resolution results
- [x] Implement WinConditions service (integrated into Game entity)
  - [x] Extract game ending logic
  - [x] Check score limits
  - [x] Check round limits
  - [x] Return game end results

### Phase 3.3: Value Objects Creation
- [x] Create `backend/domain/value_objects/` directory
- [x] Implement core value objects
  - [x] Create `TurnResult` for turn outcomes (in TurnResolution service)
  - [x] Create `Declaration` for pile counts (21 tests passing)
  - [x] Create `RoundScore` for immutable scores (in ScoringService)
  - [x] Create `GamePhase` enumeration (in entities)
- [x] Implement game-specific values
  - [x] Create `TurnPlay` for played pieces (in TurnResolution)
  - [x] Create `HandStrength` for weak hand detection (18 tests passing)
  - [x] Create `RoundResult` for round outcomes (in ScoringService)
- [x] Add value object factories
  - [x] Factory methods for complex creation
  - [x] Validation in factory methods
  - [x] Immutability enforcement (all use frozen dataclasses)

### Phase 3.4: Domain Interfaces Definition
- [x] Create `backend/domain/interfaces/` directory
- [x] Define repository interfaces
  - [x] Create `GameRepository` interface
  - [x] Create `RoomRepository` interface
  - [x] Define query methods needed
  - [x] Keep interfaces minimal
- [x] Define infrastructure interfaces
  - [x] Create `EventPublisher` interface
  - [x] Create `NotificationService` interface
  - [x] Create `BotStrategy` interface
- [x] Define domain service interfaces
  - [x] Interfaces for services that might vary
  - [x] Keep implementations in domain
  - [x] Allow infrastructure overrides

### Phase 3.5: Adapter Integration
- [x] Update existing adapters to use domain
  - [x] CreateRoomAdapter uses Room aggregate
  - [x] StartGameAdapter uses Game entity
  - [x] PlayAdapter uses domain validation
  - [x] DeclareAdapter uses domain rules
- [x] Create domain-to-API mappers
  - [x] Map domain entities to API responses
  - [x] Preserve exact message formats
  - [x] Handle legacy field names
- [x] Implement feature flags for domain
  - [x] Flag to use domain vs legacy (DOMAIN_ADAPTERS_ENABLED)
  - [x] Gradual rollout per adapter
  - [x] Shadow mode comparison
- [x] Ensure event emission
  - [x] All domain changes emit events
  - [x] Events flow to infrastructure
  - [x] Broadcasts triggered by events

### Phase 3.6: Testing & Validation
- [x] Create domain unit tests (151 tests)
  - [x] Test entities in isolation (60 tests)
  - [x] Test services with mocks (40 tests)
  - [x] Test value object behavior (51 tests)
  - [x] No infrastructure in tests
- [x] Create integration tests (11 tests)
  - [x] Test domain with adapters
  - [x] Verify event emission
  - [x] Check state consistency
- [x] Run contract tests
  - [x] All WebSocket contracts pass
  - [x] Golden masters match
  - [x] No behavior changes
- [x] Performance testing
  - [x] Measure domain operation speed
  - [x] Compare with legacy code
  - [x] All tests run in < 0.34 seconds
- [x] Shadow mode validation
  - [x] Run domain in shadow mode
  - [x] Compare all outputs
  - [x] Log any discrepancies

## 6. Documentation Update Plan

### During Implementation
1. **Create DOMAIN_MODEL.md**
   - Entity relationship diagrams
   - Aggregate boundaries
   - Invariant documentation
   - Domain event catalog

2. **Update Existing Docs**
   - CLAUDE.md: Add domain patterns
   - Architecture docs: Show domain layer
   - Add domain glossary

3. **Create Developer Guides**
   - How to add domain logic
   - Testing domain entities
   - Domain event guidelines

### After Phase Completion
1. **Update Status Documents**
   - Create PHASE_3_COMPLETION.md
   - Document implementation decisions
   - Record performance metrics

2. **Create Migration Guide**
   - How to migrate logic to domain
   - Common patterns and pitfalls
   - Rollback procedures

## Success Criteria
1. ✅ All game logic extracted to pure domain classes
2. ✅ Zero infrastructure imports in domain layer
3. ✅ 100% WebSocket contract compatibility maintained
4. ✅ All domain changes emit appropriate events
5. ✅ Domain fully testable without infrastructure
6. ✅ Performance overhead under 20%
7. ✅ Shadow mode shows identical behavior
8. ✅ Feature flags enable gradual rollout

## Risk Mitigation
1. **Complex Extraction**: Start with simple entities, build up
2. **State Consistency**: Extensive testing at each step
3. **Performance Impact**: Profile and optimize critical paths
4. **Missing Behavior**: Contract tests catch any differences
5. **Integration Issues**: Adapter pattern maintains compatibility

## Implementation Order
1. **Start with Piece** (simplest value object)
2. **Then Player** (simple entity)
3. **Then Game Rules** (pure service)
4. **Then Game** (complex entity)
5. **Finally Room** (aggregate root)

This order minimizes risk and builds complexity gradually.

---

**Note**: Phase 3 establishes the heart of the clean architecture - pure business logic with no infrastructure dependencies. This is the most critical phase for long-term maintainability.