# Complete WebSocket Reconnection Fix

## Issues Fixed

### 1. JSON Serialization Error
**Error**: `Object of type Piece is not JSON serializable`

**Cause**: During TURN phase, `phase_data` contains `table_center` field with actual Piece objects that can't be serialized to JSON.

**Fix**: Use the game state machine's `get_phase_data()` method which already returns JSON-safe data instead of accessing raw phase_data.

### 2. AttributeError on GamePhase
**Error**: `'GamePhase' object has no attribute '_make_json_safe'`

**Cause**: Initial fix incorrectly tried to call `_make_json_safe()` on `current_phase` (a GamePhase enum) instead of `current_state` (the actual GameState object).

**Fix**: Use the proper game state machine methods:
- `get_current_phase()` - returns the GamePhase enum
- `get_phase_data()` - returns JSON-safe phase data
- `get_allowed_actions()` - returns allowed actions set

## Code Changes Summary

### File: `backend/api/routes/ws.py`

1. **client_ready handler** (lines ~795-800):
   - Changed from direct phase_data access to `room.game_state_machine.get_phase_data()`
   - Removed manual JSON-safe conversion since the method already handles it

2. **client_ready full state** (lines ~743-766):
   - Simplified to use `state_machine.get_current_phase()` and `state_machine.get_phase_data()`
   - Fixed `allowed_actions` to use `state_machine.get_allowed_actions()`
   - Changed `current_phase.phase_name.value` to `current_phase.value`

3. **get_full_state handler** (lines ~883-906):
   - Same simplifications as above
   - Consistent use of game state machine methods

## Key Improvements

1. **Cleaner Code**: Using the proper API methods instead of direct attribute access
2. **No Manual Conversion**: The `get_phase_data()` method already handles JSON serialization
3. **Type Safety**: Using the correct methods prevents attribute errors on enums
4. **Consistency**: All handlers now use the same approach

## Testing

After these changes:
1. Players can successfully reconnect to games in progress
2. No JSON serialization errors occur
3. Game state is properly synchronized on reconnection
4. No AttributeError on GamePhase enum

## Remaining Issue

While reconnection now works technically, there's still a UX issue where brief disconnections during game start cause the bot to take over immediately. This should be addressed with a grace period before bot activation.