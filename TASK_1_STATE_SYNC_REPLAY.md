# Task Document: State Sync/Replay Capability Implementation

## 1. Current Code Behavior

After inspecting the codebase, I found that the system already has **partial event persistence infrastructure** in place:

### Existing Components:
- **EventStore** (`backend/api/services/event_store.py`): Fully implemented SQLite-based event storage system
- **ActionQueue** (`backend/engine/state_machine/action_queue.py`): Already has hooks for storing events but conditionally imports EventStore
- **GameState** base class: Has enterprise architecture with automatic broadcasting and change history tracking
- **State Machine**: Tracks phase transitions and maintains sequence numbers

### Current Limitations:
1. **EventStore is not properly integrated** - The import in ActionQueue is wrapped in try/except and marked as optional
2. **Only action events are stored** - Phase changes and other state transitions are not persisted
3. **No replay functionality** - EventStore has `replay_room_state()` but it's not connected to the game engine
4. **Limited event types** - Only basic event application logic exists in `_apply_event_to_state()`
5. **No debugging interface** - Events are stored but not accessible for debugging

## 2. Specific Code Files and Functions Involved

### Files to Modify:
1. `backend/engine/state_machine/action_queue.py` - Enable event storage
2. `backend/engine/state_machine/base_state.py` - Add state transition event logging
3. `backend/engine/state_machine/game_state_machine.py` - Add phase transition events
4. `backend/api/services/event_store.py` - Enhance event application logic
5. `backend/api/routes/debug.py` (new) - Create debugging endpoints

### Key Functions to Modify:
- `ActionQueue._store_action_event()` - Currently conditional, needs to be always enabled
- `GameState.update_phase_data()` - Add event storage for phase data changes
- `GameStateMachine._transition_to()` - Store phase transition events
- `EventStore._apply_event_to_state()` - Expand to handle all game event types

## 3. Exact Changes Needed

### 3.1 Enable EventStore Integration
```python
# backend/engine/state_machine/action_queue.py
# Remove conditional import and make EventStore required
from backend.api.services.event_store import event_store
```

### 3.2 Add State Transition Event Storage
```python
# backend/engine/state_machine/base_state.py
# In update_phase_data() method, after line 131:
await self._store_state_transition_event(updates, reason)

# New method to add:
async def _store_state_transition_event(self, updates: Dict[str, Any], reason: str) -> None:
    """Store state transition in event store"""
    if hasattr(self.state_machine, 'action_queue'):
        await self.state_machine.action_queue.store_state_event(
            event_type='phase_data_update',
            payload={
                'phase': self.phase_name.value,
                'updates': self._make_json_safe(updates),
                'reason': reason,
                'sequence': self._sequence_number
            }
        )
```

### 3.3 Add Phase Transition Events
```python
# backend/engine/state_machine/game_state_machine.py
# In _transition_to() method, add:
await self.action_queue.store_state_event(
    event_type='phase_transition',
    payload={
        'from_phase': self.current_phase.value if self.current_phase else None,
        'to_phase': new_phase.value,
        'game_round': self.game.round_number if self.game else 0
    }
)
```

### 3.4 Enhance Event Application Logic
```python
# backend/api/services/event_store.py
# Expand _apply_event_to_state() to handle new event types:
- phase_data_update
- phase_transition
- turn_complete
- round_scoring
- game_complete
```

### 3.5 Create Debug Interface
```python
# backend/api/routes/debug.py (new file)
# Endpoints:
- GET /api/debug/events/{room_id} - List all events for a room
- GET /api/debug/replay/{room_id} - Replay and show reconstructed state
- GET /api/debug/events/{room_id}/sequence/{seq} - Get events since sequence
```

## 4. Database Schema Required

The existing SQLite schema is sufficient:
```sql
CREATE TABLE game_events (
    sequence INTEGER PRIMARY KEY,
    room_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    player_id TEXT,
    timestamp REAL NOT NULL,
    created_at TEXT NOT NULL
)
```

Indexes already exist for performance.

## 5. Interfaces to Modify/Extend

### 5.1 ActionQueue Interface
- Make `room_id` required in constructor
- Remove conditional event storage
- Add method for bulk event retrieval

### 5.2 GameState Interface
- Add `_store_state_transition_event()` method
- Ensure all state changes go through `update_phase_data()`

### 5.3 EventStore Interface (extend)
- Add `get_events_by_type()` method
- Add `export_room_history()` for debugging
- Add `validate_event_sequence()` for integrity checks

## 6. Async Behavior Requirements

All event storage operations are already async and non-blocking:
- Event storage uses `async with self._lock` for thread safety
- Storage failures don't break game flow (logged but not raised)
- All database operations are async-compatible

## 7. Testing Correctness

### 7.1 Unit Tests
```python
# backend/tests/test_event_store.py
- Test event storage and retrieval
- Test replay state reconstruction
- Test event sequence integrity
- Test cleanup of old events
```

### 7.2 Integration Tests
```python
# backend/tests/test_state_replay.py
- Play a complete game while storing events
- Replay the game from events
- Compare final states (should be identical)
- Test recovery from partial event sequences
```

### 7.3 Debugging Validation
1. Start a game and play several turns
2. Use debug endpoint to view all events
3. Use replay endpoint to reconstruct state
4. Compare reconstructed state with live game state
5. Verify event sequence has no gaps

### 7.4 Performance Tests
- Measure event storage overhead (should be < 5ms per event)
- Test with high-frequency events (rapid bot plays)
- Verify no impact on game responsiveness

## Summary

The codebase is **surprisingly well-prepared** for state sync/replay capability. The EventStore is already implemented but not fully integrated. The main work is:
1. Enabling the existing EventStore integration
2. Adding event storage calls to state transitions
3. Expanding event replay logic for all event types
4. Creating debugging interfaces

This is a relatively straightforward implementation since most infrastructure already exists.