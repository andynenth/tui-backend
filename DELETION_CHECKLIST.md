# 🗑️ Liap Tui Code Deletion Checklist

## Overview

This checklist ensures you delete all old code completely when replacing components. Check off each item as you delete it to ensure nothing is missed.

## Phase 1: State Management Deletion

### Frontend Deletions
- [ ] Delete `frontend/src/services/GameService.ts` (1,534 lines)
- [ ] Delete `frontend/src/hooks/useGameState.ts`
- [ ] Delete `frontend/src/hooks/useGameActions.ts` 
- [ ] Delete `frontend/src/services/ServiceIntegration.ts`

### Code Pattern Deletions
Search and delete all instances of:
- [ ] `gameService.setState()`
- [ ] `gameService.getState()`
- [ ] `useGameState()` hooks
- [ ] `this.notifyListeners()`
- [ ] `console.group()` for state logging
- [ ] `this.stateDiff()` calls

### Backend Deletions
- [ ] Remove `phase_data` dict manipulation in state classes
- [ ] Remove manual `broadcast()` calls for state updates
- [ ] Delete redundant state tracking variables

## Phase 2: God Class Deletion

### Backend God Classes
- [ ] Delete `backend/engine/state_machine/game_state_machine.py` (855 lines)
- [ ] Delete `backend/socket_manager.py` (865 lines)
- [ ] Delete `backend/engine/state_machine/base_state.py` (if not needed)

### Frontend God Classes
- [ ] Delete `frontend/src/services/NetworkService.ts` (647 lines)
- [ ] Delete `frontend/src/services/types.ts` (if merged into new structure)

### Component Deletions
Remove these scattered responsibilities:
- [ ] Bot management code from state machine
- [ ] Broadcasting logic from state classes
- [ ] Event storage from state machine
- [ ] Statistics tracking from game logic
- [ ] Timer management from state machine

## Phase 3: Circular Dependency Deletion

### Import Hack Deletions
Search for and delete all:
- [ ] `try/except ImportError` blocks
- [ ] `sys.path.append()` calls
- [ ] `__file__` path manipulations
- [ ] Conditional imports based on environment

### Example Patterns to Delete:
```python
# DELETE all instances like this:
try:
    from backend.socket_manager import broadcast
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from socket_manager import broadcast
```

### File Reorganization
- [ ] Delete entire `backend/engine/state_machine/` directory
- [ ] Delete `backend/api/routes/` directory
- [ ] Delete any `__init__.py` with import hacks

## Phase 4: Event System Deletion

### Direct Broadcast Deletions
Search and delete all:
- [ ] `await broadcast(room_id, event, data)`
- [ ] `self.broadcast_phase_change()`
- [ ] `self.broadcast_custom_event()`
- [ ] Manual WebSocket `send_json()` calls

### Event Pattern Deletions
- [ ] Delete `broadcast_manager.py` if exists
- [ ] Delete custom event emitters
- [ ] Delete event type constants scattered in files
- [ ] Delete duplicate event handling logic

### WebSocket Handler Deletions
In `ws.py`, delete:
- [ ] Individual event handlers (replace with unified handler)
- [ ] Manual JSON construction for events
- [ ] Duplicate event validation logic

## Global Search & Destroy Patterns

### Anti-Patterns to Remove

```bash
# Run these searches to find code to delete:

# 1. Async setState patterns
grep -r "setTimeout.*setState" frontend/
grep -r "async.*setState" frontend/

# 2. Manual broadcast calls  
grep -r "await broadcast(" backend/
grep -r "broadcast_phase_change" backend/

# 3. Circular import hacks
grep -r "except ImportError:" backend/
grep -r "sys.path.append" backend/

# 4. God class methods (>50 lines)
# Look for methods with too many responsibilities

# 5. Duplicate state management
grep -r "phase_data\[" backend/
grep -r "self.state =" frontend/
```

### Old Patterns to Remove

1. **State Updates**
   ```python
   # DELETE
   self.phase_data['current_player'] = player
   await broadcast(room_id, "phase_change", data)
   
   # Will be replaced with:
   # await self.state_manager.update(changes)
   ```

2. **Event Broadcasting**
   ```python
   # DELETE
   await self.broadcast_custom_event("play", {...})
   await broadcast(room_id, "turn_complete", {...})
   
   # Will be replaced with:
   # await event_bus.publish(event)
   ```

3. **Component Coupling**
   ```python
   # DELETE
   from ..socket_manager import broadcast
   from ..room_manager import get_room
   from ..game import Game
   
   # Will be replaced with:
   # Dependency injection
   ```

## Validation After Deletion

### Phase 1 Validation
```bash
# These searches should return NOTHING:
grep -r "GameService" frontend/src/
grep -r "useGameState" frontend/src/
grep -r "setState.*reason" frontend/src/
```

### Phase 2 Validation
```bash
# These files should NOT exist:
ls backend/engine/state_machine/game_state_machine.py  # Should fail
ls frontend/src/services/GameService.ts                # Should fail
ls backend/socket_manager.py                           # Should fail
```

### Phase 3 Validation
```bash
# No circular imports:
python -m pytest backend/tests/ -v  # Should have no import errors
grep -r "ImportError" backend/      # Should return nothing
```

### Phase 4 Validation
```bash
# Single event system:
grep -r "broadcast(" backend/         # Should only find UnifiedEventBus
grep -r "send_json" backend/          # Should only find in WebSocket client
```

## Celebration Milestones

### After Phase 1
- [ ] Deleted 2,000+ lines of state management code
- [ ] No more async state delays
- [ ] Run `cloc` to see reduction

### After Phase 2  
- [ ] Deleted 3,500+ lines of god classes
- [ ] No file larger than 200 lines
- [ ] Run complexity analysis - all methods simple

### After Phase 3
- [ ] Deleted all import hacks
- [ ] Clean dependency graph
- [ ] Tests run without warnings

### After Phase 4
- [ ] Deleted all duplicate event systems
- [ ] Single, clean event flow
- [ ] 50% less code overall!

## The Final Celebration

When all checkboxes are checked:
1. Run `git diff --stat` to see total deletions
2. Run the game - it should work perfectly
3. Share the deletion stats with the team
4. Order pizza! 🍕

Remember: **Every line deleted is a bug prevented!**