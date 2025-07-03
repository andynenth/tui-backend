# 🔧 Liap Tui Architecture Refactoring Plan (Simplified)

## Executive Summary

This is a simplified 6-week plan to refactor Liap Tui by **replacing components entirely** rather than running old and new code in parallel. This approach is cleaner, less confusing, and reduces the risk of mixing old and new patterns.

## Core Principle: Replace, Don't Parallel

Instead of maintaining both old and new code, we will:
1. **Stop the game** briefly for each phase
2. **Replace entire components** at once
3. **Test thoroughly** before moving on
4. **Delete old code immediately** to prevent confusion

## Refactoring Phases

### Phase 1: State Synchronization Replacement (Weeks 1-2)

#### Step 1: Build New State System (Week 1)
```bash
# Create new files - don't modify existing ones yet
frontend/src/stores/UnifiedGameStore.ts      # New single source of truth
backend/engine/state/StateManager.py         # New state coordinator
backend/engine/state/StateSnapshot.py        # Versioned state
```

#### Step 2: Replace Everything at Once (Weekend 1)
```bash
# Friday evening - Stop the game
# Saturday - Delete old state management:
rm frontend/src/services/GameService.ts      # Delete 1534 lines!
rm frontend/src/hooks/useGameState.ts        # Delete old hook

# Sunday - Wire up new system:
# - Update all imports to use UnifiedGameStore
# - Update backend to use StateManager
# - Test everything
# - Restart game Sunday evening
```

#### What Gets Deleted:
- `GameService.ts` - entire file (1534 lines)
- All `setState()` calls with logging
- All manual state synchronization code
- Duplicate state management in components

#### What Gets Added:
- `UnifiedGameStore` - single source of truth (100 lines)
- `StateManager` - backend coordinator (150 lines)
- Clean state flow with automatic versioning

### Phase 2: God Class Destruction (Weeks 3-4)

#### Week 3: Backend God Classes

**Friday Evening: Stop the game**

**Saturday: Delete and Replace GameStateMachine**
```bash
# Delete the monster
rm backend/engine/state_machine/game_state_machine.py  # 855 lines gone!

# Add focused components
backend/engine/orchestration/
├── GameOrchestrator.py       # 100 lines - coordinates everything
├── StateTransitions.py       # 80 lines - phase changes only
├── EventBroadcaster.py       # 60 lines - broadcasting only
├── BotCoordinator.py         # 90 lines - bot management only
└── ActionValidator.py        # 70 lines - validation only
```

**Sunday: Test and Restart**

#### Week 4: Frontend God Classes

**Friday Evening: Stop the game**

**Saturday: Delete and Replace Frontend Services**
```bash
# Delete the giants
rm frontend/src/services/GameService.ts        # Already gone!
rm frontend/src/services/NetworkService.ts     # 647 lines
rm frontend/src/services/ServiceIntegration.ts # 200+ lines

# Add clean services
frontend/src/core/
├── network/
│   └── WebSocketClient.ts    # 150 lines - just WebSocket
├── actions/
│   └── GameActions.ts        # 80 lines - action dispatch
├── state/
│   └── StateSubscriber.ts    # 60 lines - state updates
└── validation/
    └── ActionValidator.ts    # 50 lines - client validation
```

### Phase 3: Dependency Cleanup (Week 5)

#### Monday: Map Dependencies
Create a clean dependency graph

#### Tuesday-Wednesday: Create New Structure
```bash
backend/
├── domain/          # No imports from other layers
├── application/     # Imports only from domain
└── infrastructure/  # Imports from domain and application
```

#### Thursday: Delete Old Structure
```bash
# Delete all the old circular mess
rm -rf backend/engine/state_machine/  # All of it
rm -rf backend/api/routes/           # Rebuild clean

# Friday: Add new clean structure
backend/
├── core/            # Pure business logic
├── services/        # Application services  
├── adapters/        # External interfaces
└── main.py          # Wire everything up
```

### Phase 4: Event System Replacement (Week 6)

#### Monday-Tuesday: Build UnifiedEventBus
```python
# One event system to rule them all
class UnifiedEventBus:
    async def publish(self, event: GameEvent):
        # Single pipeline for everything
```

#### Wednesday: Delete All Old Event Systems
```bash
# Search and destroy all:
- broadcast() calls
- manual WebSocket sends  
- custom event emitters
- duplicate broadcasting

# Replace with:
event_bus.publish(event)  # That's it!
```

## Benefits of This Approach

### 1. **No Confusion**
- Old code is deleted immediately
- No mixing of patterns
- Clear boundaries

### 2. **Forced Completion**
- Can't leave refactoring half-done
- Must finish each phase completely
- No technical debt accumulation

### 3. **Easier Testing**
- Test new system in isolation
- No interference from old code
- Clear before/after comparison

### 4. **Psychological Benefits**
- Satisfaction of deleting bad code
- Clear progress (lines deleted!)
- No temptation to use old patterns

## Implementation Schedule

### Week 1: Build New State System
- Mon-Thu: Build UnifiedGameStore and StateManager
- Fri: Prepare for replacement
- Weekend: **REPLACE EVERYTHING**

### Week 2: State System Testing
- Mon-Wed: Fix any issues
- Thu-Fri: Performance optimization
- Metrics: State sync should be perfect

### Week 3: Backend God Classes
- Mon-Thu: Build new components
- Fri: Stop game
- Weekend: **DELETE GameStateMachine, ADD new components**

### Week 4: Frontend God Classes  
- Mon-Thu: Build new frontend services
- Fri: Stop game
- Weekend: **DELETE old services, ADD new ones**

### Week 5: Dependencies
- Mon-Wed: Design new structure
- Thu: Stop game
- Fri: **DELETE old structure, ADD clean architecture**

### Week 6: Events
- Mon-Tue: Build UnifiedEventBus
- Wed: Stop game
- Thu-Fri: **DELETE all old event systems, USE only new**

## Metrics to Track

### What to Measure Before/After Each Phase

1. **Phase 1 (State Sync)**
   - Before: Count state inconsistency bugs
   - After: Should be ZERO

2. **Phase 2 (God Classes)**
   - Before: Time to find a bug (hours)
   - After: Should be < 30 minutes

3. **Phase 3 (Dependencies)**
   - Before: Circular import errors
   - After: Should be ZERO

4. **Phase 4 (Events)**
   - Before: Different event patterns
   - After: Should be ONE

## Risk Mitigation

### Backup Strategy
```bash
# Before each phase
git tag pre-phase-1-backup
pg_dump liap_tui > backup-phase-1.sql

# If something goes wrong
git checkout pre-phase-1-backup
psql liap_tui < backup-phase-1.sql
# Game back online in 5 minutes
```

### Testing Strategy
- Build new system completely before touching old
- Test new system with comprehensive test suite
- Only delete old after new is proven

### Communication
- Announce maintenance windows in advance
- "Game will be offline Saturday 6pm - Sunday 6pm for major improvements"
- Players understand and appreciate the honesty

## What You'll Delete (The Satisfaction List)

### Lines of Code to Delete
- `GameStateMachine.py`: 855 lines ❌
- `GameService.ts`: 1,534 lines ❌
- `NetworkService.ts`: 647 lines ❌
- `socket_manager.py`: 865 lines ❌
- Various circular import hacks: ~200 lines ❌
- **Total: ~4,100 lines of problematic code GONE**

### Lines of Code to Add
- New focused components: ~2,000 lines ✅
- **Net reduction: 2,100 lines (50% less code!)**

## Success Criteria

### After Each Phase
1. **Game still works** (obviously)
2. **Specific metric improved** (see above)
3. **Old code completely gone** (no remnants)
4. **Team understands new structure**

### After Complete Refactoring
1. **No more recurring bugs**
2. **New features take 50% less time**
3. **Any developer can understand any component in 5 minutes**
4. **Monitoring shows all green metrics**

## The Nuclear Option

If at any phase things aren't working:
1. `git checkout main`
2. `./start.sh`
3. Game is back online
4. Regroup and try again next weekend

This approach is **bold but clean**. No half-measures, no confusion, just better architecture.

## Final Note

By deleting old code immediately, you:
- Force yourself to complete each phase
- Eliminate confusion between old and new
- Get the satisfaction of removing technical debt
- Make the codebase 50% smaller and 200% cleaner

The game will be offline for a few weekends, but players will thank you when it comes back faster, more reliable, and bug-free.