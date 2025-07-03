# Backend Migration Guide: Integrating StateManager

This guide provides step-by-step instructions to integrate the new StateManager into the existing backend state machine.

## Overview

The StateManager provides:
- Centralized state versioning and checksum validation
- Automatic state synchronization with frontend
- State history tracking for debugging
- Guaranteed consistency between backend and frontend

## Files to Update

### Core Files:
1. `backend/socket_manager.py` - Add StateManager initialization
2. `backend/engine/state_machine/base.py` - Integrate state tracking
3. `backend/engine/state_machine/game_state_machine.py` - Update state transitions
4. `backend/api/routes/websocket.py` - Handle version/checksum validation

## Migration Steps

### Step 1: Update socket_manager.py

Add StateManager initialization when creating game rooms:

**Add imports:**
```python
from backend.engine.state_manager import StateManager
```

**Update process_action method:**
```python
async def process_action(self, room_id: str, player_id: str, action: GameAction) -> bool:
    """Process a game action for a room."""
    room = self.rooms.get(room_id)
    if not room:
        return False
    
    # Initialize StateManager if not exists
    if not hasattr(room, 'state_manager'):
        room.state_manager = StateManager(room_id)
    
    # Validate action version if provided
    if hasattr(action, 'version'):
        is_valid, expected_version = room.state_manager.validate_version(
            action.version, 
            player_id
        )
        if not is_valid:
            await self.send_error(player_id, 
                f"Version mismatch. Expected: {expected_version}, Got: {action.version}"
            )
            return False
    
    # Process action through state machine
    result = await room.state_machine.process_action(action)
    
    # Update state manager after successful action
    if result:
        room.state_manager.update_state(
            room.state_machine.get_full_state(),
            action
        )
    
    return result
```

### Step 2: Update base.py (GameState base class)

Integrate StateManager with the enterprise architecture:

**Add to GameState.__init__:**
```python
def __init__(self, game: 'Game', context: Optional[Dict[str, Any]] = None):
    self.game = game
    self.context = context or {}
    self.phase_data: Dict[str, Any] = {}
    self._transition_to: Optional['GameState'] = None
    self._broadcast_queue: List[Dict[str, Any]] = []
    self._change_history: List[Dict[str, Any]] = []
    self._sequence_number = 0
    
    # Add StateManager reference
    self.state_manager: Optional[StateManager] = None
    if context and 'state_manager' in context:
        self.state_manager = context['state_manager']
```

**Update update_phase_data method:**
```python
async def update_phase_data(self, updates: Dict[str, Any], reason: str = "State update") -> None:
    """
    Enterprise method for updating phase data with automatic broadcasting.
    This is the ONLY method that should be used for state updates.
    """
    if not updates:
        return
        
    # Create change record
    self._sequence_number += 1
    change_record = {
        "sequence": self._sequence_number,
        "timestamp": time.time(),
        "reason": reason,
        "updates": updates,
        "previous_values": {k: self.phase_data.get(k) for k in updates.keys()}
    }
    
    # Apply updates
    self.phase_data.update(updates)
    
    # Record change
    self._change_history.append(change_record)
    
    # Get full state for broadcast
    full_state = self._get_json_safe_state()
    
    # Update StateManager if available
    if self.state_manager:
        self.state_manager.update_state(full_state, {
            "type": "phase_data_update",
            "reason": reason,
            "updates": updates
        })
    
    # Queue broadcast
    broadcast_data = {
        "event": "phase_change",
        "data": full_state,
        "metadata": {
            "sequence": self._sequence_number,
            "reason": reason,
            "timestamp": change_record["timestamp"]
        }
    }
    
    # Include version info if StateManager available
    if self.state_manager:
        broadcast_data["version"] = self.state_manager.current_version
        broadcast_data["checksum"] = self.state_manager.calculate_checksum(full_state)
    
    self._broadcast_queue.append(broadcast_data)
    
    # Process broadcast queue
    await self._process_broadcast_queue()
```

### Step 3: Update game_state_machine.py

Pass StateManager through context:

**Update __init__:**
```python
class GameStateMachine:
    def __init__(self, game: Game, room_id: str):
        self.game = game
        self.room_id = room_id
        self.context = {
            "room_id": room_id,
            "game": game
        }
        
        # StateManager will be injected by socket_manager
        self.state_manager: Optional[StateManager] = None
        
        # Initialize with preparation state
        self.current_state = PreparationState(game, self.context)
        self._state_history: List[Tuple[str, float]] = [
            (self.current_state.__class__.__name__, time.time())
        ]
```

**Update transition_to method:**
```python
def transition_to(self, state_class: Type[GameState]) -> None:
    """Transition to a new state."""
    # Pass state manager in context
    if self.state_manager:
        self.context['state_manager'] = self.state_manager
    
    self.current_state = state_class(self.game, self.context)
    self._state_history.append(
        (self.current_state.__class__.__name__, time.time())
    )
    
    # Log transition with state manager
    if self.state_manager:
        self.state_manager.update_state(
            self.get_full_state(),
            {"type": "state_transition", "to_state": state_class.__name__}
        )
```

**Add method to inject StateManager:**
```python
def set_state_manager(self, state_manager: StateManager) -> None:
    """Inject StateManager into the state machine."""
    self.state_manager = state_manager
    self.context['state_manager'] = state_manager
    
    # Update current state's reference
    if self.current_state:
        self.current_state.state_manager = state_manager
```

### Step 4: Update WebSocket route

Add version validation to websocket endpoint:

**In backend/api/routes/websocket.py:**

```python
@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    player_id = str(uuid.uuid4())
    await socket_manager.connect(websocket, room_id, player_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Add version info if available
            if 'version' in data:
                action = GameAction(
                    player_id=player_id,
                    action_type=data.get("action"),
                    payload=data.get("payload", {}),
                    version=data['version']  # Pass version for validation
                )
            else:
                action = GameAction(
                    player_id=player_id,
                    action_type=data.get("action"),
                    payload=data.get("payload", {})
                )
            
            success = await socket_manager.process_action(room_id, player_id, action)
            
            if not success:
                await websocket.send_json({
                    "error": "Action processing failed",
                    "action": data.get("action")
                })
                
    except WebSocketDisconnect:
        socket_manager.disconnect(room_id, player_id)
```

### Step 5: Update Room initialization

Modify how rooms are created to include StateManager:

**In socket_manager.py, update/add create_room method:**
```python
def create_room(self, room_id: str) -> GameRoom:
    """Create a new game room with all necessary components."""
    game = Game()
    state_machine = GameStateMachine(game, room_id)
    
    # Create and inject StateManager
    state_manager = StateManager(room_id)
    state_machine.set_state_manager(state_manager)
    
    room = GameRoom(
        room_id=room_id,
        game=game,
        state_machine=state_machine,
        state_manager=state_manager,
        players={}
    )
    
    self.rooms[room_id] = room
    return room
```

## Integration Points

### 1. State Updates
All state updates through `update_phase_data()` will automatically:
- Increment version
- Calculate checksum
- Include version/checksum in broadcasts
- Track state history

### 2. Client Validation
Frontend UnifiedGameStore will:
- Track version numbers
- Validate checksums
- Request full state on mismatch
- Include version in actions

### 3. Debugging
StateManager provides:
- State history: `state_manager.get_history()`
- Version info: `state_manager.get_version_info(player_id)`
- State replay: `state_manager.get_state_at_version(version)`

## Testing the Integration

After integration, test these scenarios:

### 1. Version Increment Test
```python
# In Python shell or test
room = socket_manager.rooms['test-room']
initial_version = room.state_manager.current_version

# Trigger state change
await room.state_machine.current_state.update_phase_data(
    {'test': 'data'}, 
    'Test update'
)

# Check version incremented
assert room.state_manager.current_version == initial_version + 1
```

### 2. Checksum Validation Test
```python
# Get current state and checksum
state = room.state_machine.get_full_state()
checksum = room.state_manager.calculate_checksum(state)

# Verify checksum matches
assert checksum == room.state_manager.last_checksum
```

### 3. Broadcast Integration Test
Monitor WebSocket messages to ensure they include:
```json
{
  "event": "phase_change",
  "data": { /* game state */ },
  "version": 5,
  "checksum": "abc123...",
  "metadata": {
    "sequence": 5,
    "reason": "Player played pieces",
    "timestamp": 1234567890.123
  }
}
```

## Rollback Plan

If integration causes issues:

1. Remove StateManager references from:
   - socket_manager.py
   - base.py
   - game_state_machine.py

2. Restore original files from backups

3. The system will continue working with existing enterprise architecture

## Common Issues and Solutions

### Issue: "AttributeError: 'GameState' object has no attribute 'state_manager'"
**Solution:** Ensure StateManager is passed in context during state creation

### Issue: Version mismatch errors from frontend
**Solution:** Check that broadcasts include version/checksum fields

### Issue: State history not being tracked
**Solution:** Verify StateManager.update_state() is called in update_phase_data()

### Issue: Performance degradation
**Solution:** 
- Limit history size in StateManager
- Use lazy checksum calculation
- Consider caching checksums

## Next Steps

1. Run validation tests: `python migration/phase1/validation_tests.py`
2. Test full game flow with multiple players
3. Monitor logs for version mismatches
4. Verify state sync in development tools