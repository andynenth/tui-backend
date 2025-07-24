# Phase 2: Event System Implementation Plan

## 1. Overview & Objective

### Purpose
Phase 2 focuses on implementing a comprehensive event system that will decouple the game logic from infrastructure concerns (broadcasting, persistence, etc.). This phase builds upon the adapter foundation from Phase 1 to create an event-driven architecture that maintains 100% frontend compatibility.

### Key Objectives
1. **Decouple Broadcasting**: Remove direct broadcast calls from game logic
2. **Enable Event Sourcing**: Create foundation for event-based state reconstruction
3. **Improve Testability**: Pure domain logic without infrastructure dependencies
4. **Maintain Compatibility**: All WebSocket messages remain identical
5. **Performance Target**: Keep overhead under 50% (based on Phase 1 learnings)

### How It Fits the Overall Strategy
- **Phase 0**: Established testing infrastructure ✅
- **Phase 1**: Created adapter layer for API compatibility ✅
- **Phase 2**: Implement event system to decouple domain from infrastructure (THIS PHASE)
- **Phase 3**: Extract pure domain logic using events
- **Phase 4**: Build application layer (use cases)
- **Phase 5**: Complete infrastructure separation

## 2. Scope Definition

### What WILL Be Done
1. **Domain Event Definitions**
   - Define all game domain events (TurnPlayed, PhaseChanged, ScoreUpdated, etc.)
   - Create event base classes and interfaces
   - Implement event metadata (timestamps, sequence numbers, correlation IDs)

2. **Event Publisher Infrastructure**
   - Create EventPublisher interface
   - Implement in-memory event bus
   - Add event handler registration system
   - Create event history tracking

3. **Event-to-Broadcast Bridge**
   - Create infrastructure handlers that convert events to WebSocket broadcasts
   - Maintain exact message format compatibility
   - Preserve broadcast ordering and timing

4. **Adapter Integration**
   - Update existing adapters to publish events
   - Remove direct broadcast calls from adapters
   - Maintain backward compatibility through feature flags

5. **Enterprise Architecture Integration**
   - Leverage existing update_phase_data() automatic broadcasting
   - Enhance with event publishing alongside broadcasts
   - Maintain single source of truth pattern

### What Will NOT Be Done
1. **Domain Logic Refactoring**: No changes to game rules or state machine logic
2. **Persistence**: No event store implementation (deferred to Phase 5)
3. **Event Replay**: No event sourcing replay functionality yet
4. **External Message Bus**: No Kafka/RabbitMQ integration
5. **Frontend Changes**: Zero modifications to frontend code
6. **REST API Changes**: Focus only on WebSocket events

## 3. Alignment Check

### Connection to Phase 0
- ✅ Uses contract testing framework to verify compatibility
- ✅ Leverages golden masters for event output validation
- ✅ Behavioral tests ensure game flow unchanged

### Connection to Phase 1
- ✅ Builds on adapter infrastructure
- ✅ Uses same feature flag system
- ✅ Applies performance lessons (minimal intervention pattern)
- ✅ Maintains instant rollback capability

### Preparation for Phase 3
- Sets up event foundation for domain extraction
- Events will carry all data needed for pure domain logic
- Infrastructure handlers ready to support domain layer

## 4. Conflicts & Redundancy Review

### Identified Issues
1. **Enterprise Architecture Overlap**
   - Current: update_phase_data() automatically broadcasts
   - Conflict: Event system also needs to trigger broadcasts
   - Resolution: Event handlers will work alongside enterprise broadcasting

2. **Broadcast Responsibility**
   - Current: Mixed between adapters, state machine, and enterprise methods
   - Conflict: Unclear where broadcasts should originate
   - Resolution: Events become single trigger point for all broadcasts

3. **State Change Tracking**
   - Current: Enterprise architecture tracks changes
   - New: Event system also tracks changes
   - Resolution: Unify through event metadata enhancement

### Documentation Updates Needed
1. Update CLAUDE.md to include event system patterns
2. Enhance enterprise architecture docs with event integration
3. Create EVENT_SYSTEM_GUIDE.md for developers
4. Update adapter documentation with event publishing

## 5. Detailed Implementation Checklist

### Phase 2.1: Event Infrastructure Setup
- [ ] Create `backend/domain/events/` directory structure
- [ ] Implement base event classes
  - [ ] Create `DomainEvent` base class with metadata
  - [ ] Create `GameEvent` base class for game-specific events
  - [ ] Add event type enum for all event types
- [ ] Define all domain events (estimated 30-40 events)
  - [ ] Connection events (PlayerConnected, PlayerDisconnected)
  - [ ] Room events (RoomCreated, PlayerJoined, PlayerLeft)
  - [ ] Game flow events (GameStarted, PhaseChanged, RoundCompleted)
  - [ ] Game action events (PiecesPlayed, DeclarationMade, RedealRequested)
  - [ ] Scoring events (ScoresCalculated, WinnerDetermined)
- [ ] Create event publisher interface
  - [ ] Define `EventPublisher` protocol
  - [ ] Create `InMemoryEventBus` implementation
  - [ ] Add async event handling support
- [ ] Implement event handler registration
  - [ ] Create decorator for event handlers
  - [ ] Support priority-based handler ordering
  - [ ] Add error handling for failed handlers

### Phase 2.2: Event-to-Broadcast Bridge
- [ ] Create `backend/infrastructure/events/` directory
- [ ] Implement broadcast event handlers
  - [ ] Create handler for each event type
  - [ ] Map events to exact WebSocket message format
  - [ ] Preserve all field names and structures
- [ ] Integrate with existing broadcast system
  - [ ] Use socket_manager broadcast functions
  - [ ] Maintain room vs player broadcast logic
  - [ ] Preserve message ordering
- [ ] Add event-to-broadcast mapping tests
  - [ ] Verify each event produces correct broadcast
  - [ ] Test against golden masters
  - [ ] Ensure timing requirements met

### Phase 2.3: Adapter Event Integration
- [ ] Update connection adapters to publish events
  - [ ] PingAdapter → publish PingReceived event
  - [ ] ClientReadyAdapter → publish ClientReady event
  - [ ] Continue for all connection adapters
- [ ] Update room adapters to publish events
  - [ ] CreateRoomAdapter → publish RoomCreated event
  - [ ] JoinRoomAdapter → publish PlayerJoined event
  - [ ] Continue for all room adapters
- [ ] Update game adapters to publish events
  - [ ] StartGameAdapter → publish GameStarted event
  - [ ] PlayAdapter → publish PiecesPlayed event
  - [ ] Continue for all game adapters
- [ ] Remove direct broadcast calls from adapters
  - [ ] Replace with event publishing
  - [ ] Maintain backward compatibility flag
  - [ ] Test with shadow mode

### Phase 2.4: Enterprise Architecture Integration
- [ ] Enhance update_phase_data() to publish events
  - [ ] Create PhaseDataChanged event
  - [ ] Include change metadata in event
  - [ ] Maintain automatic broadcasting
- [ ] Update broadcast_custom_event() to use events
  - [ ] Create CustomGameEvent type
  - [ ] Publish alongside broadcast
  - [ ] Track in event history
- [ ] Integrate with change history
  - [ ] Link events to change entries
  - [ ] Add event sequence numbers
  - [ ] Enhance debugging capabilities

### Phase 2.5: Testing & Validation
- [ ] Create event system unit tests
  - [ ] Test event creation and metadata
  - [ ] Test event bus publish/subscribe
  - [ ] Test handler registration and ordering
- [ ] Create event-broadcast integration tests
  - [ ] Verify events trigger correct broadcasts
  - [ ] Test broadcast format preservation
  - [ ] Validate timing and ordering
- [ ] Run contract tests with events enabled
  - [ ] All WebSocket contracts must pass
  - [ ] Golden master comparison must match
  - [ ] Performance must stay under 50% overhead
- [ ] Shadow mode testing
  - [ ] Enable events for subset of traffic
  - [ ] Compare outputs with legacy path
  - [ ] Monitor for discrepancies

### Phase 2.6: Monitoring & Rollout
- [ ] Add event system metrics
  - [ ] Event publish rate
  - [ ] Handler execution time
  - [ ] Failed event count
- [ ] Create event system dashboard
  - [ ] Real-time event flow visualization
  - [ ] Performance metrics
  - [ ] Error tracking
- [ ] Implement gradual rollout
  - [ ] Start with 1% traffic
  - [ ] Monitor for 24 hours
  - [ ] Increase to 10%, 50%, 100%
- [ ] Document rollback procedure
  - [ ] Feature flag to disable events
  - [ ] Revert to direct broadcasts
  - [ ] No code deployment needed

## 6. Documentation Update Plan

### During Implementation
1. **Create EVENT_SYSTEM_GUIDE.md**
   - Event naming conventions
   - How to add new events
   - Handler implementation patterns
   - Testing guidelines

2. **Update Existing Documentation**
   - CLAUDE.md: Add event system patterns
   - Enterprise architecture: Show event integration
   - Adapter guides: Include event publishing

3. **Create Event Catalog**
   - List all events with descriptions
   - Show which adapters publish which events
   - Document event data structures

### After Phase Completion
1. **Update Phase Status Documents**
   - Mark Phase 2 complete in tracking
   - Document actual vs planned changes
   - Record performance metrics

2. **Create Phase 2 Lessons Learned**
   - What worked well
   - Challenges encountered
   - Recommendations for Phase 3

3. **Update Overall Architecture Docs**
   - Show event flow in system diagrams
   - Update abstraction boundaries
   - Document new interfaces

## Success Criteria
1. ✅ All adapters publish events instead of direct broadcasts
2. ✅ 100% WebSocket contract compatibility maintained
3. ✅ Performance overhead under 50% (similar to Phase 1)
4. ✅ Zero frontend changes required
5. ✅ Complete event catalog documented
6. ✅ Shadow mode shows identical behavior
7. ✅ Instant rollback capability preserved

## Risk Mitigation
1. **Performance Impact**: Use minimal intervention pattern learned from Phase 1
2. **Broadcast Timing**: Maintain exact ordering through priority handlers
3. **Missing Events**: Comprehensive testing against golden masters
4. **Integration Complexity**: Gradual rollout with feature flags
5. **Enterprise Conflicts**: Enhance rather than replace existing patterns

---

**Note**: This plan emphasizes maintaining the existing enterprise architecture while adding events as a complementary system. The goal is evolution, not revolution.