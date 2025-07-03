# 🔧 Liap Tui Architecture Refactoring Plan

## Executive Summary

This document outlines a comprehensive 6-week plan to refactor the Liap Tui codebase to eliminate recurring bugs caused by architectural issues. The refactoring focuses on breaking circular dependencies, decomposing god classes, unifying state management, and leveraging the existing monitoring system.

## Current Problems

### 1. **State Synchronization Issues** (Root cause of 80% of bugs)
- Frontend and backend maintain separate state copies
- Asynchronous React setState causes display delays
- Players see outdated information, report "bugs" that are actually sync delays

### 2. **God Classes** (Making bugs hard to locate)
- `GameStateMachine`: 855 lines with 8+ responsibilities
- `GameService`: 1534 lines managing everything
- `socket_manager.py`: 865 lines with 7+ concerns

### 3. **Circular Dependencies**
- Complex import workarounds throughout codebase
- Makes testing and deployment difficult
- Prevents clean architectural boundaries

### 4. **Multiple Event Systems**
- Direct broadcast() calls
- Enterprise architecture events
- WebSocket events
- Frontend events
- All operating independently, causing confusion

## Refactoring Phases

### Phase 1: State Synchronization Fix (Weeks 1-2)
**Goal:** Single source of truth with instant updates

#### Current State (❌ Problems)
```
Backend State Change → broadcast() → WebSocket → Frontend receives → 
→ GameService.setState() → Heavy logging → React setState (async) → 
→ UI update (delayed) → User sees old state → Reports "bug"
```

#### Target State (✅ Solution)
```
Backend State Change → Versioned Snapshot → WebSocket → 
→ Unified Store (immediate) → React subscribes → Instant UI update
```

#### Deliverables:
1. `UnifiedGameStore` class with versioned state
2. Remove async setState delays
3. Integrate with monitoring for sync detection
4. State checksum validation

#### Success Metrics:
- Client desync recovery drops from ~50/hour to <1/hour
- UI updates within 50ms of backend changes
- Zero "phantom bug" reports

### Phase 2: God Class Decomposition (Weeks 3-4)
**Goal:** Small, focused, testable components

#### GameStateMachine Decomposition
```
Current (855 lines):                Target (50-100 lines each):
GameStateMachine                    StateTransitionManager
  - manage_state_transitions   →      - transition_to()
  - handle_broadcasting        →    EventBroadcaster
  - manage_bots               →      - broadcast_change()
  - store_events              →    BotManager
  - calculate_scores          →      - get_bot_action()
  - validate_actions          →    GameValidator
  - manage_timers             →      - validate_action()
  - track_statistics          →    GameOrchestrator (coordinates all)
```

#### GameService Decomposition
```
Current (1534 lines):              Target (100-200 lines each):
GameService                        GameStateStore
  - manage_state              →      - getState()
  - handle_networking         →      - updateState()
  - calculate_derived         →    GameActionDispatcher
  - validate_actions          →      - dispatch()
  - debug_logging             →    GameDerivedState
                                     - isMyTurn()
                                     - canPlayAnyCount()
```

#### Success Metrics:
- No class larger than 200 lines
- Method execution time < 100ms
- Memory usage drops 30%
- 90% unit test coverage (was impossible before)

### Phase 3: Fix Circular Dependencies (Week 5)
**Goal:** Clean, unidirectional dependency flow

#### Current Dependency Mess
```
game_state.py → socket_manager.py → room_manager.py → game_state.py (circular!)
     ↓                                      ↑
base_state.py ←────────────────────────────┘
```

#### Target Clean Architecture
```
Domain Layer (no dependencies)
    ↓
Application Layer (depends only on Domain)
    ↓
Infrastructure Layer (depends on Application)
```

#### Implementation:
1. Extract interfaces/protocols
2. Dependency injection
3. Remove all import workarounds
4. Enforce layer boundaries with import linting

#### Success Metrics:
- Zero circular import errors
- Clean pytest runs without warnings
- 50% faster test execution

### Phase 4: Event System Unification (Week 6)
**Goal:** Single, predictable event flow

#### Current Chaos
```
- broadcast() calls scattered everywhere
- Enterprise architecture auto-broadcasting
- Manual WebSocket sends
- Custom event emitters
```

#### Target Unified System
```
All Events → UnifiedEventBus → Event Store (for replay)
                            ↘ WebSocket Broadcast
                            ↘ Local Handlers
                            ↘ Monitoring System
```

#### Success Metrics:
- 100% of events flow through unified system
- Complete event replay capability
- Event flow visualization in monitoring

## Timeline & Milestones

### Week 1-2: State Synchronization
- **Day 1-3:** Implement UnifiedGameStore
- **Day 4-5:** Remove async delays
- **Day 6-7:** Integration testing
- **Milestone:** Frontend updates < 50ms latency

### Week 3: Backend God Classes
- **Day 1-2:** Extract StateTransitionManager
- **Day 3-4:** Extract EventBroadcaster & BotManager
- **Day 5:** Create GameOrchestrator
- **Milestone:** GameStateMachine < 100 lines

### Week 4: Frontend God Classes
- **Day 1-2:** Split GameService into stores
- **Day 3-4:** Create focused dispatchers
- **Day 5:** Migration and testing
- **Milestone:** No frontend file > 200 lines

### Week 5: Dependencies
- **Day 1-2:** Define layer boundaries
- **Day 3-4:** Implement dependency injection
- **Day 5:** Validation and cleanup
- **Milestone:** Zero circular dependencies

### Week 6: Events
- **Day 1-3:** Implement UnifiedEventBus
- **Day 4-5:** Migrate all systems
- **Milestone:** Single event flow path

## Risk Mitigation

### During Refactoring
1. **Feature Freeze:** No new features during refactoring
2. **Incremental Changes:** Small, tested commits
3. **Parallel Testing:** Keep old code until new code proven
4. **Monitoring:** Watch metrics continuously

### Rollback Plan
- Git tags at each phase completion
- Feature flags for gradual rollout
- A/B testing with monitoring
- Automated rollback on metric degradation

## Expected Outcomes

### Immediate Benefits (Week 1-2)
- 90% reduction in "phantom bugs"
- Instant UI updates
- Happy players

### Medium-term Benefits (Week 3-5)
- 80% faster bug location and fixing
- New features take 50% less time
- Onboarding new developers in days, not weeks

### Long-term Benefits (Week 6+)
- Self-documenting architecture
- Predictable system behavior
- Confidence in making changes
- Scalable to more game modes

## Success Criteria

### Quantitative
- Client desync events: < 1/hour (from ~50/hour)
- Average method execution: < 100ms (from > 500ms)
- Memory usage: < 60% (from > 85%)
- Bug fix time: < 2 hours (from > 8 hours)
- Test coverage: > 90% (from ~40%)

### Qualitative
- Developers say "This makes sense!"
- New features don't break existing ones
- Debugging is straightforward
- Code is self-documenting

## Monitoring Integration

The existing monitoring system will track progress:

```yaml
refactoring_dashboard:
  panels:
    - title: "State Sync Health"
      metric: "client_desync_recovery_rate"
      target: "< 0.1/hour"
      current: "~50/hour"
      
    - title: "Code Complexity"
      metric: "max_lines_per_class"
      target: "< 200"
      current: "855"
      
    - title: "Performance"
      metric: "p95_method_execution_time"
      target: "< 100ms"
      current: "> 500ms"
      
    - title: "Memory Efficiency"
      metric: "memory_usage_percent"
      target: "< 60%"
      current: "> 85%"
```

## Communication Plan

### Weekly Updates
- Progress against milestones
- Metrics dashboard screenshot
- Blockers and solutions
- Next week's focus

### Phase Completion
- Demo of improvements
- Before/after metrics
- Lessons learned
- Go/no-go for next phase

## Conclusion

This refactoring plan addresses the root causes of recurring bugs by:
1. Fixing state synchronization (eliminates phantom bugs)
2. Breaking up god classes (makes bugs easier to find)
3. Removing circular dependencies (enables clean testing)
4. Unifying events (predictable behavior)

The incremental approach with continuous monitoring ensures we can track progress and roll back if needed. By the end of 6 weeks, the codebase will be maintainable, testable, and a joy to work with.