# Bot Slot Management Issues - Test Analysis Report

## Test Execution Summary

Tests were executed following the exact sequences provided. No fixes were implemented, only analysis.

## Issue 1: Lobby Update on Bot Removal

### Test Sequence Executed:
1. Player 1 >> join lobby ✓
2. Player 1 >> create room ✓
3. Player 2 >> join lobby ✓
4. Player 1 >> remove bot 3
5. Player 2 should see room update from 4/4 to 3/4

### Observed Behavior:
- **Initial state**: Room created with 4/4 players (Player1Host + Bot 2 + Bot 3 + Bot 4)
- **Player 2 lobby view**: Shows `null` - room is not visible at all
- **After bot removal**: Player 2 still sees `null` - no update received
- **WebSocket messages**: No `room_list_update` received by Player 2 after bot removal

### Analysis:
1. **Primary Issue**: Player 2 never sees the room in the lobby at all
2. **Secondary Issue**: No WebSocket updates are being sent to lobby subscribers when bots are removed
3. **Root Cause Hypothesis**: 
   - Lobby WebSocket subscription might not be working properly
   - Room might be created as private or with visibility issues
   - `PlayerRemoved` event might not be triggering lobby broadcasts

## Issue 2 & 3: Bot Slot Targeting

### Test Evidence:
```
Initial room state (should be 4/4)
  Slot 1: Player1…
  Slot 2: Bot 2
  Slot 3: Bot 3
  Slot 4: Bot 4

Player 1 >> remove bot 3
After removing bot 3:
  Slot 1: Player1…
  Slot 2: Bot 2
  Slot 3: Bot 3    ← Still shows Bot 3!
  Slot 4: [empty]   ← Slot 4 became empty instead!
```

### Observed Behavior:
1. **Wrong Slot Removal**: Clicking "Remove" on slot 3 actually removes the bot from slot 4
2. **Off-by-One Error**: There's a clear indexing mismatch
3. **Bot Names Persist**: "Bot 3" text remains in slot 3 even though a bot was removed

### Analysis:
1. **Slot Indexing Issue**: 
   - Frontend might be sending slot position (1-4)
   - Backend might be using array index (0-3)
   - The removal is happening at index `position - 1`
   
2. **Bot Naming Issue**:
   - Bot names appear to be static ("Bot 2", "Bot 3", "Bot 4")
   - They don't update based on actual slot position
   - This causes confusion when bots are removed/added

3. **Player ID Generation**:
   - Based on code analysis: `player_id = room_id + "_p" + slot_index`
   - If slot 3 is clicked, it might be generating wrong player_id

## WebSocket Message Analysis

### Messages Captured:
1. **Player 1 WebSocket**:
   - Received: `room_list_update` (on lobby join)
   - Received: `room_update` (on room creation)
   - Received: `room_update` (on bot removal)

2. **Player 2 WebSocket**:
   - Received: `room_list_update` (on lobby join)
   - No further updates received

### Missing Messages:
- Player 2 never receives `room_list_update` after Player 1 removes a bot
- No `remove_player` WebSocket message was logged (might not be captured)

## Key Findings

1. **Issue 1 (Lobby Update)**: 
   - CONFIRMED: Lobby does not update when bots are removed
   - MORE SEVERE: Player 2 can't even see the room in the lobby initially

2. **Issue 2 (Add Bot Targeting)**: 
   - Could not complete test due to wrong slot removal blocking the sequence

3. **Issue 3 (Remove Bot Targeting)**:
   - CONFIRMED: Removing bot from slot 3 actually removes from slot 4
   - Clear off-by-one error in slot targeting

## Probable Root Causes

1. **Lobby Visibility**:
   - Room might not be properly registered in lobby
   - WebSocket subscription for lobby might be broken
   - `room_list_update` events might not include all rooms

2. **Slot Indexing Mismatch**:
   - Frontend uses 1-based positioning (slots 1, 2, 3, 4)
   - Backend uses 0-based array indexing (indices 0, 1, 2, 3)
   - Conversion is happening incorrectly: clicking slot 3 affects index 3 (which is slot 4)

3. **Bot Naming**:
   - Bot names are hardcoded as "Bot 2", "Bot 3", "Bot 4"
   - They don't dynamically update based on actual position
   - This creates confusion about which bot is actually in which slot

## Next Steps (Analysis Only)

To properly fix these issues, the following areas need investigation:
1. WebSocket subscription mechanism for lobby updates
2. Slot index conversion between frontend and backend
3. Bot naming and player_id generation logic
4. Event publishing for `PlayerRemoved` events

No fixes have been implemented as per instructions.