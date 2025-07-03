# 📋 Phase 1 Weekend Migration Checklist

**Migration Window:** Saturday 6pm - Sunday 6pm  
**Objective:** Replace old state management with UnifiedGameStore + StateManager

## Pre-Migration (Friday Evening)

### 1. Preparation Checklist
- [ ] Announce maintenance window to players
- [ ] Pull latest code from git
- [ ] Run `python backend/migration/phase1/prepare_migration.py`
- [ ] Verify all backups created successfully
- [ ] Check no active games: `curl http://localhost:5050/health/detailed`
- [ ] Tag current version: `git tag pre-phase-1-migration`

### 2. Build & Test New Components
- [ ] Frontend: Verify `frontend/src/stores/UnifiedGameStore.ts` exists
- [ ] Frontend: Verify `frontend/src/stores/NetworkIntegration.ts` exists
- [ ] Backend: Verify `backend/engine/state/` directory exists
- [ ] Run new component tests in isolation

## Saturday - Frontend Migration

### 6:00 PM - Stop Services
```bash
# Stop the game
docker-compose down
# or
pkill -f "python main.py"
```

### 6:30 PM - Frontend File Deletions
```bash
cd frontend/src

# Delete the god classes
rm services/GameService.ts              # 1,534 lines gone!
rm services/ServiceIntegration.ts       # ~200 lines gone!
rm hooks/useGameState.ts               # ~100 lines gone!
rm hooks/useGameActions.ts             # ~80 lines gone!

# Verify deletions
ls services/GameService.ts  # Should fail
git status                  # Should show deletions
```

### 7:00 PM - Update Imports

#### In `frontend/src/App.jsx`:
```javascript
// DELETE these lines:
import { GameService } from './services/GameService';
import { ServiceIntegration } from './services/ServiceIntegration';

// ADD these lines:
import { NetworkIntegration } from './stores/NetworkIntegration';

// In App component, ADD:
useEffect(() => {
  const integration = new NetworkIntegration();
  integration.initialize();
  
  return () => {
    integration.cleanup();
  };
}, []);
```

#### Update all game components:
```bash
# Find all files using GameService
grep -r "GameService" frontend/src/

# For each file found, replace:
# OLD: import { GameService } from '../services/GameService';
# NEW: import { useGameStore } from '../stores/useGameStore';

# OLD: const gameService = GameService.getInstance();
# NEW: const { gameState, dispatch } = useGameStore();

# OLD: gameService.getState()
# NEW: gameState

# OLD: gameService.playCards(indices)
# NEW: dispatch({ type: 'PLAY_CARDS', indices })
```

### 8:00 PM - Update React Components

Common patterns to update:

#### GamePage.jsx:
```javascript
// OLD
const gameService = GameService.getInstance();
const [gameState, setGameState] = useState(gameService.getState());

useEffect(() => {
  const unsubscribe = gameService.subscribe(() => {
    setGameState(gameService.getState());
  });
  return unsubscribe;
}, []);

// NEW
const { gameState } = useGameStore();
// That's it! No useState, no subscribe needed
```

#### Action Handlers:
```javascript
// OLD
const handlePlayCards = (indices) => {
  gameService.playCards(indices);
};

// NEW  
const { dispatch } = useGameStore();
const handlePlayCards = (indices) => {
  networkService.send(gameState.roomId, 'play', {
    player_name: gameState.playerName,
    piece_indices: indices
  });
};
```

### 9:00 PM - Test Frontend
```bash
cd frontend
npm run build  # Should succeed with no GameService errors
npm run dev    # Start dev server

# Manual tests:
# 1. Open browser to http://localhost:3000
# 2. Should see lobby (no errors in console)
# 3. Create a room
# 4. UI should update immediately
```

## Sunday - Backend Integration

### 10:00 AM - Backend Integration

#### 1. Update `backend/room.py`:
```python
# At the top, ADD:
from backend.migration.phase1.state_manager_hook import setup_state_manager_integration

# In Room class start_game method, ADD after game_state_machine creation:
# Add StateManager integration
self.state_manager = setup_state_manager_integration(
    self.game_state_machine,
    self.room_id
)
```

#### 2. Update `backend/socket_manager.py`:
```python
# At the top, ADD:
room_state_managers = {}  # Track state managers by room

# Find the broadcast function and WRAP it:
_original_broadcast = broadcast

async def broadcast(room_id: str, event: str, data: dict):
    # Add version/checksum to phase_change events
    if event == "phase_change" and room_id in room_state_managers:
        state_manager = room_state_managers[room_id]
        if state_manager and state_manager.current_snapshot:
            data['version'] = state_manager.current_snapshot.version
            data['checksum'] = state_manager.current_snapshot.checksum
            data['server_timestamp'] = state_manager.current_snapshot.timestamp
    
    return await _original_broadcast(room_id, event, data)
```

#### 3. Update room creation to track state managers:
```python
# In room.py start_game(), after creating state_manager:
from backend.socket_manager import room_state_managers
room_state_managers[self.room_id] = self.state_manager
```

### 12:00 PM - Integration Testing

Run validation tests:
```bash
cd backend
python migration/phase1/validation_tests.py
```

Manual testing checklist:
- [ ] Start backend: `python main.py`
- [ ] Start frontend: `cd frontend && npm run dev`
- [ ] Create a game room
- [ ] Check browser console for version numbers in state
- [ ] Start game with 4 players
- [ ] Verify state updates show incrementing versions
- [ ] Play through a complete round
- [ ] Check no state sync errors

### 2:00 PM - Full System Test

Multi-player test:
- [ ] Open 4 browser windows
- [ ] Create room and join with all 4
- [ ] Start game
- [ ] Each player should see same state version
- [ ] Play cards - all players see updates immediately
- [ ] No "cards still in hand" bugs
- [ ] Complete a full game

### 4:00 PM - Performance Validation

Check metrics:
```bash
# Check state sync latency
curl http://localhost:5050/health/detailed

# Monitor logs for version mismatches
tail -f logs/game.log | grep -i "version"

# Check memory usage (should be lower)
```

### 5:00 PM - Final Checklist

- [ ] All tests passing
- [ ] No errors in browser console
- [ ] State updates are instant (< 50ms)
- [ ] Version numbers incrementing correctly
- [ ] Checksums validating
- [ ] Memory usage reduced
- [ ] No GameService references remaining

### 6:00 PM - Go Live!

```bash
# Commit the changes
git add -A
git commit -m "Phase 1: Unified state management with versioning

- Deleted GameService.ts (1,534 lines)
- Deleted ServiceIntegration.ts (~200 lines)  
- Added UnifiedGameStore (~180 lines)
- Added StateManager with versioning
- All state updates now < 50ms
- Fixed state synchronization bugs"

# Tag the successful migration
git tag phase-1-complete

# Announce completion
echo "🎉 Migration complete! Game is back online!"
```

## Rollback Plan (If Needed)

If anything goes wrong:
```bash
# Quick rollback
git checkout pre-phase-1-migration
cd frontend && npm run build
cd ../backend && python main.py

# Game back online in 5 minutes!
```

## Post-Migration

### Monday Morning:
- [ ] Monitor for any player reports
- [ ] Check metrics dashboard
- [ ] Document any issues found
- [ ] Plan Phase 2 (God Class destruction)

### Success Metrics:
- ✅ Zero state sync bugs reported
- ✅ UI updates < 50ms
- ✅ Version numbers working correctly
- ✅ 2,000+ lines of code deleted
- ✅ Players happy with instant updates!

## Notes Section

```
(Document any issues or learnings here during migration)




```

Remember: **Be bold! Delete the old code completely. The new system is better!**