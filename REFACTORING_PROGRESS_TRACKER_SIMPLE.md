# 📊 Liap Tui Refactoring Progress (Simplified)

**Approach:** Complete replacement, no parallel systems  
**Downtime:** Planned maintenance windows each phase

## Quick Status Dashboard

```
Phase 1: State Sync     [⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜] 0% - Not Started
Phase 2: God Classes    [⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜] 0% - Not Started  
Phase 3: Dependencies   [⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜] 0% - Not Started
Phase 4: Events         [⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜] 0% - Not Started

Lines Deleted: 0 / 4,100 target
Lines Added: 0 / 2,000 target
Net Reduction: 0 / 2,100 target (51%)
```

## Phase 1: State Management Replacement

### Build Week (Week 1)
- [ ] Mon-Tue: Build `UnifiedGameStore.ts`
- [ ] Wed-Thu: Build `StateManager.py`
- [ ] Friday: Prepare replacement scripts

### Replacement Weekend (Week 1-2)
- [ ] Friday 6pm: Stop game, backup everything
- [ ] Saturday: Delete old state management (2,000+ lines)
- [ ] Sunday: Wire up new system, test everything
- [ ] Sunday 6pm: Restart game

### Deletion Targets
```
❌ GameService.ts (1,534 lines)
❌ useGameState.ts (~100 lines)
❌ ServiceIntegration.ts (~200 lines)
❌ Manual setState calls everywhere (~200 lines)
Total: ~2,034 lines to delete

✅ UnifiedGameStore.ts (100 lines)
✅ StateManager.py (150 lines)
Total: ~250 lines to add

Net: -1,784 lines 🎉
```

### Success Metrics
| Metric | Before | After | Status |
|--------|--------|-------|--------|
| State sync bugs/week | ~20 | 0 | ⬜ |
| UI update latency | 500-2000ms | <50ms | ⬜ |
| Player confusion reports | High | None | ⬜ |

---

## Phase 2: God Class Destruction

### Week 3: Backend God Classes

#### Build (Mon-Thu)
- [ ] GameOrchestrator.py (100 lines)
- [ ] StateTransitions.py (80 lines)
- [ ] EventBroadcaster.py (60 lines)
- [ ] BotCoordinator.py (90 lines)
- [ ] ActionValidator.py (70 lines)

#### Replace (Weekend)
- [ ] Friday 6pm: Stop game
- [ ] Saturday: Delete GameStateMachine.py (855 lines)
- [ ] Sunday: Add new components, test
- [ ] Sunday 6pm: Restart game

### Week 4: Frontend God Classes

#### Build (Mon-Thu)
- [ ] WebSocketClient.ts (150 lines)
- [ ] GameActions.ts (80 lines)
- [ ] StateSubscriber.ts (60 lines)
- [ ] ActionValidator.ts (50 lines)

#### Replace (Weekend)
- [ ] Friday 6pm: Stop game
- [ ] Saturday: Delete NetworkService.ts (647 lines)
- [ ] Sunday: Add new components, test
- [ ] Sunday 6pm: Restart game

### Deletion Summary
```
❌ GameStateMachine.py (855 lines)
❌ NetworkService.ts (647 lines)
❌ socket_manager.py (865 lines)
Total: 2,367 lines to delete

✅ New focused components (~740 lines)
Net: -1,627 lines 🎉
```

---

## Phase 3: Clean Dependencies

### Week 5: Architecture Cleanup

#### Design (Mon-Wed)
- [ ] Map current dependencies
- [ ] Design clean layers
- [ ] Create interfaces

#### Replace (Thu-Fri)
- [ ] Thursday: Stop game
- [ ] Delete old structure with circular deps
- [ ] Add clean architecture
- [ ] Friday: Test and restart

### What Changes
```
Before:
- Circular imports everywhere
- try/except ImportError hacks
- sys.path manipulations

After:
- Clean layers (Domain → Application → Infrastructure)
- Dependency injection
- No circular dependencies
```

---

## Phase 4: Event Unification

### Week 6: Single Event System

#### Build (Mon-Tue)
- [ ] UnifiedEventBus.py (150 lines)
- [ ] EventTypes.py (50 lines)

#### Replace (Wed-Fri)
- [ ] Wednesday: Stop game
- [ ] Delete all broadcast() calls
- [ ] Delete custom event systems
- [ ] Wire up UnifiedEventBus
- [ ] Friday: Test and restart

### Event System Changes
```
Before:
- broadcast() calls scattered
- Manual WebSocket sends
- Custom event emitters
- Enterprise auto-broadcasting

After:
- event_bus.publish(event)  # That's it!
```

---

## Scoreboard

### Lines of Code
| Phase | To Delete | To Add | Net Change | Status |
|-------|-----------|--------|------------|--------|
| 1: State | 2,034 | 250 | -1,784 | ⬜ |
| 2: God Classes | 2,367 | 740 | -1,627 | ⬜ |
| 3: Dependencies | ~200 | ~100 | -100 | ⬜ |
| 4: Events | ~500 | ~200 | -300 | ⬜ |
| **Total** | **5,101** | **1,290** | **-3,811** | ⬜ |

### Maintenance Windows
| Phase | Date | Downtime | Status |
|-------|------|----------|--------|
| 1 | ___ | Sat 6pm - Sun 6pm | ⬜ |
| 2 | ___ | Sat 6pm - Sun 6pm | ⬜ |
| 3 | ___ | Thu 6pm - Fri 6pm | ⬜ |
| 4 | ___ | Wed 6pm - Fri 6pm | ⬜ |

---

## Weekly Logs

### Week 1 Log
```
Date: _______
Focus: Building new state system
Completed:
- 
Issues:
- 
Next: Replacement weekend
```

### Week 2 Log
```
Date: _______
Focus: State system replacement
Completed:
- 
Deleted: ___ lines
Added: ___ lines
Next: God class decomposition
```

### Week 3 Log
```
Date: _______
Focus: Backend god classes
Completed:
- 
Deleted: ___ lines
Added: ___ lines
Next: Frontend god classes
```

### Week 4 Log
```
Date: _______
Focus: Frontend god classes
Completed:
- 
Deleted: ___ lines
Added: ___ lines
Next: Dependencies
```

### Week 5 Log
```
Date: _______
Focus: Clean dependencies
Completed:
- 
Import errors fixed: ___
Next: Event system
```

### Week 6 Log
```
Date: _______
Focus: Event unification
Completed:
- 
Total deleted: ___ lines
Total added: ___ lines
NET REDUCTION: ___ lines!
```

---

## Celebration Checklist

### After Each Phase
- [ ] Game working perfectly
- [ ] Metrics improved
- [ ] Old code completely gone
- [ ] Team briefed on changes

### Final Celebration
- [ ] 3,800+ lines deleted
- [ ] No more recurring bugs
- [ ] Clean architecture achieved
- [ ] Pizza ordered! 🍕

---

## Emergency Rollback

If anything goes wrong:
```bash
# Instant rollback
git checkout pre-phase-X-backup
./start.sh
# Game back online in 5 minutes
```

Remember: **Bold deletions lead to clean architecture!**