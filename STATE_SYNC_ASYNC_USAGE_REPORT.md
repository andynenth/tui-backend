# State Sync / Async Usage Report
## Codebase Status at Commit 2bfdd3a

### Executive Summary

After inspecting the codebase at commit 2bfdd3a (post-rollback), I found:

1. **EventStore/State Sync**: Implementation exists but is **completely disconnected** from the game execution path
2. **Async Readiness**: Async implementations exist but the application still uses **synchronous versions** throughout

---

## 1. State Sync / Replay Capability

### What EXISTS in the codebase:

#### EventStore Implementation (`backend/api/services/event_store.py`)
- ✅ Full SQLite-based event storage system
- ✅ Methods: `store_state_event()`, `store_action_event()`, `get_room_events()`, `replay_room_state()`
- ✅ Event replay and state reconstruction capabilities
- ✅ Client recovery support with sequence tracking

#### Debug Endpoints (`backend/api/routes/debug.py`)
- ✅ `/api/debug/events/{room_id}` - List events for a room
- ✅ `/api/debug/replay/{room_id}` - Replay and reconstruct state
- ✅ `/api/debug/stats` - Event statistics
- ✅ `/api/debug/room-stats` - Room-specific stats

### What is NOT ACTIVE:

#### No Event Storage Calls in Game Flow
- ❌ **NO calls** to `event_store.store_state_event()` in any state machine files
- ❌ **NO calls** to `event_store.store_action_event()` in action processing
- ❌ The GameStateMachine and state classes have no event store integration

#### Debug Routes Not Mounted
- ❌ The debug router is **NOT imported** in `backend/api/routes/routes.py`
- ❌ The debug endpoints are **NOT accessible** via HTTP

#### Missing Integration Points
The following files process game events but don't store them:
- `backend/engine/state_machine/base_state.py` - broadcasts phase changes but no storage
- `backend/engine/state_machine/game_state_machine.py` - processes actions but no storage
- `backend/api/routes/ws.py` - handles WebSocket events but no storage

---

## 2. Async Readiness

### What EXISTS in the codebase:

#### Async Implementations
- ✅ `backend/engine/async_game.py` - AsyncGame class with async methods
- ✅ `backend/engine/async_room.py` - AsyncRoom with async locks and methods
- ✅ `backend/engine/async_room_manager.py` - AsyncRoomManager implementation
- ✅ `backend/engine/state_machine/async_game_adapter.py` - Adapter for async/sync bridge
- ✅ `backend/api/websocket/async_migration_helper.py` - Migration utilities

#### Async Infrastructure
- ✅ Async locks in AsyncRoom and AsyncGame
- ✅ Proper async/await chains in async implementations
- ✅ AsyncGameAdapter to wrap sync/async games

### What is NOT ACTIVE:

#### Synchronous Versions Still in Use
- ❌ `shared_room_manager` uses **sync** `RoomManager` (not AsyncRoomManager)
- ❌ WebSocket handlers use **sync** methods:
  - `room_manager.create_room()` - sync version at `backend/api/routes/ws.py:443`
  - `room_manager.get_room()` - sync version at `backend/api/routes/ws.py:497`
  - `room.join_room()` - sync version throughout ws.py
  - `room.start_game()` - sync version throughout ws.py

#### No Async Lock Usage in Active Code
- ❌ The sync `Room` class has no locks for thread safety
- ❌ The sync `Game` class has no locks for concurrent access
- ❌ State machine uses sync game methods without protection

---

## 3. Files and Functions Needing Re-wiring

### To Enable EventStore:

1. **Import event_store in state machine**:
   - File: `backend/engine/state_machine/game_state_machine.py`
   - Add: `from api.services.event_store import event_store`

2. **Add storage calls in base_state.py**:
   - File: `backend/engine/state_machine/base_state.py`
   - In `update_phase_data()` method (around line 226):
     ```python
     # After broadcasting phase_change
     await event_store.store_state_event(
         room_id=self.state_machine.room_id,
         phase=self.phase_name.value,
         phase_data=json_safe_phase_data,
         players=players_data
     )
     ```

3. **Add action storage in action processing**:
   - File: `backend/engine/state_machine/action_queue.py`
   - In `process_action()` method:
     ```python
     # Before processing action
     await event_store.store_action_event(
         room_id=self._room_id,
         action_type=action.action_type.value,
         player_id=action.player_name,
         payload=action.payload
     )
     ```

4. **Mount debug routes**:
   - File: `backend/api/routes/routes.py`
   - Add: `from . import debug`
   - Add: `router.include_router(debug.router)`

### To Enable Async:

1. **Replace shared_room_manager**:
   - File: `backend/shared_instances.py`
   - Change:
     ```python
     from engine.async_room_manager import AsyncRoomManager
     shared_room_manager = AsyncRoomManager()
     ```

2. **Update WebSocket handlers to use async**:
   - File: `backend/api/routes/ws.py`
   - Replace all sync calls with async equivalents:
     - `room_manager.create_room()` → `await room_manager.create_room()`
     - `room_manager.get_room()` → `await room_manager.get_room()`
     - `room.join_room()` → `await room.join_room()`
     - `room.start_game()` → `await room.start_game()`

3. **Ensure game creation uses AsyncGame**:
   - File: `backend/engine/async_room.py`
   - Already uses AsyncGame in `start_game()` method

---

## Summary of Required Work

### EventStore Integration:
1. Add event_store imports to state machine files
2. Add storage calls at key points (phase changes, actions)
3. Mount debug routes in the API
4. Test event persistence and replay functionality

### Async Migration:
1. Switch to AsyncRoomManager in shared_instances.py
2. Update all WebSocket handler calls to use async methods
3. Ensure proper await chains throughout
4. Test concurrent access patterns

### Estimated Effort:
- EventStore integration: 2-4 hours
- Async migration: 4-6 hours
- Testing both: 2-3 hours

Both features are well-implemented but need to be "plugged in" to the active execution path.