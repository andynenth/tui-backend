# Phase 3: Domain Layer Implementation Plan

**Status**: PLANNING  
**Prerequisites**: Phase 1 (Adapters) ✅ COMPLETE | Phase 2 (Events) ✅ COMPLETE  
**Objective**: Extract pure domain logic from infrastructure dependencies  

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
- [ ] Create `backend/domain/entities/` directory structure
- [ ] Extract Game entity
  - [ ] Create pure `Game` class without infrastructure imports
  - [ ] Move game state (pieces, scores, turn number)
  - [ ] Implement state change methods (play_turn, declare, etc.)
  - [ ] Emit domain events for all changes
  - [ ] Remove direct broadcast calls
- [ ] Extract Player entity
  - [ ] Create `Player` class with player state
  - [ ] Include hand, declarations, connection status
  - [ ] Implement player actions as methods
  - [ ] Remove WebSocket references
- [ ] Extract Piece value object
  - [ ] Create immutable `Piece` class
  - [ ] Implement piece comparison logic
  - [ ] Add piece validation rules
- [ ] Extract Room aggregate
  - [ ] Create `Room` as aggregate root
  - [ ] Include Game as entity within Room
  - [ ] Manage player lifecycle
  - [ ] Coordinate game phases

### Phase 3.2: Domain Services Implementation
- [ ] Create `backend/domain/services/` directory
- [ ] Implement GameRules service
  - [ ] Extract validation logic from scattered locations
  - [ ] Create pure functions for rule checking
  - [ ] Include weak hand detection
  - [ ] Validate plays and declarations
- [ ] Implement ScoringService
  - [ ] Extract scoring logic from `scoring.py`
  - [ ] Create pure scoring calculations
  - [ ] Handle multipliers and special cases
  - [ ] Return immutable score results
- [ ] Implement TurnResolution service
  - [ ] Extract turn comparison logic
  - [ ] Determine turn winners
  - [ ] Handle special piece rules
  - [ ] Return resolution results
- [ ] Implement WinConditions service
  - [ ] Extract game ending logic
  - [ ] Check score limits
  - [ ] Check round limits
  - [ ] Return game end results

### Phase 3.3: Value Objects Creation
- [ ] Create `backend/domain/value_objects/` directory
- [ ] Implement core value objects
  - [ ] Create `PlayResult` for turn outcomes
  - [ ] Create `Declaration` for pile counts
  - [ ] Create `Score` for immutable scores
  - [ ] Create `GamePhase` enumeration
- [ ] Implement game-specific values
  - [ ] Create `PiecePlay` for played pieces
  - [ ] Create `HandStrength` for weak hand detection
  - [ ] Create `RoundResult` for round outcomes
- [ ] Add value object factories
  - [ ] Factory methods for complex creation
  - [ ] Validation in factory methods
  - [ ] Immutability enforcement

### Phase 3.4: Domain Interfaces Definition
- [ ] Create `backend/domain/interfaces/` directory
- [ ] Define repository interfaces
  - [ ] Create `GameRepository` interface
  - [ ] Create `RoomRepository` interface
  - [ ] Define query methods needed
  - [ ] Keep interfaces minimal
- [ ] Define infrastructure interfaces
  - [ ] Create `EventPublisher` interface (already exists)
  - [ ] Create `NotificationService` interface
  - [ ] Create `BotStrategy` interface
- [ ] Define domain service interfaces
  - [ ] Interfaces for services that might vary
  - [ ] Keep implementations in domain
  - [ ] Allow infrastructure overrides

### Phase 3.5: Adapter Integration
- [ ] Update existing adapters to use domain
  - [ ] CreateRoomAdapter uses Room aggregate
  - [ ] StartGameAdapter uses Game entity
  - [ ] PlayAdapter uses domain validation
  - [ ] DeclareAdapter uses domain rules
- [ ] Create domain-to-API mappers
  - [ ] Map domain entities to API responses
  - [ ] Preserve exact message formats
  - [ ] Handle legacy field names
- [ ] Implement feature flags for domain
  - [ ] Flag to use domain vs legacy
  - [ ] Gradual rollout per adapter
  - [ ] Shadow mode comparison
- [ ] Ensure event emission
  - [ ] All domain changes emit events
  - [ ] Events flow to infrastructure
  - [ ] Broadcasts triggered by events

### Phase 3.6: Testing & Validation
- [ ] Create domain unit tests
  - [ ] Test entities in isolation
  - [ ] Test services with mocks
  - [ ] Test value object behavior
  - [ ] No infrastructure in tests
- [ ] Create integration tests
  - [ ] Test domain with adapters
  - [ ] Verify event emission
  - [ ] Check state consistency
- [ ] Run contract tests
  - [ ] All WebSocket contracts pass
  - [ ] Golden masters match
  - [ ] No behavior changes
- [ ] Performance testing
  - [ ] Measure domain operation speed
  - [ ] Compare with legacy code
  - [ ] Target < 20% overhead
- [ ] Shadow mode validation
  - [ ] Run domain in shadow mode
  - [ ] Compare all outputs
  - [ ] Log any discrepancies

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