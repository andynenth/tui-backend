# WebSocket Reconnection JSON Serialization Fix

## Issue
Player could not reconnect to the game. Two errors occurred:
1. First: `WebSocket error in room 22E410: Object of type Piece is not JSON serializable`
2. Then: `WebSocket error in room F8694A: 'GamePhase' object has no attribute '_make_json_safe'`

## Root Cause
1. When a player reconnects, the backend sends the current game state including `phase_data`. During the TURN phase, this `phase_data` contains a `table_center` field with actual `Piece` objects, which cannot be directly serialized to JSON.
2. The initial fix incorrectly tried to call `_make_json_safe()` on the `current_phase` (which is a GamePhase enum) instead of the `current_state` (which is the actual GameState object with the method).

## Solution
1. Use the existing `_make_json_safe()` method from the GameState base class to convert all non-JSON-serializable objects (like Piece objects) to strings before sending them over WebSocket.
2. Access the method through `current_state` (the GameState object) instead of `current_phase` (the GamePhase enum).
3. Get `phase_data` from `current_state.phase_data` instead of `current_phase.phase_data`.

## Code Changes

### File: `backend/api/routes/ws.py`

1. **In `client_ready` handler (line ~802):**
   - Added JSON-safe conversion for phase_data when sending current game phase
   
2. **In `client_ready` handler for full state (line ~748):**
   - Added JSON-safe conversion for phase_data when sending full state on reconnection
   
3. **In `get_full_state` handler (line ~893):**
   - Added JSON-safe conversion for phase_data when handling explicit full state requests

## Implementation Details

The fix uses the existing `_make_json_safe()` method which:
- Recursively converts dictionaries and lists
- Converts Piece objects to their string representation (e.g., "GENERAL_RED(14)")
- Handles datetime objects by converting to timestamps
- Preserves already JSON-safe types (str, int, float, bool, None)

## Testing
1. Start a game and progress to TURN phase
2. Disconnect the player (close browser/tab)
3. Reconnect by navigating back to the game URL
4. Player should successfully reconnect without JSON serialization errors
5. Game state should be properly restored with all pieces visible

## Prevention
This fix ensures that any future phase_data containing non-JSON-serializable objects will be automatically converted to a safe format before WebSocket transmission.