# Zero Declaration Streak Fix Documentation

## Problem Summary
Players were able to declare 0 three times in a row, violating game rules. The UI restriction that should disable the "0" option after two consecutive zero declarations was not working.

## Root Cause Analysis

### Issue 1: Backend Not Updating Zero Streak Counter
The backend was tracking `zero_declares_in_a_row` in the Player class but wasn't updating it when declarations were made.

**Problem Code:**
```python
# declaration_state.py - Only setting declared value, not updating streak
player.declared = declared_value
```

**Fix:**
```python
# Now calls record_declaration which updates zero_declares_in_a_row
player.record_declaration(declared_value)
```

### Issue 2: Frontend Data Overwriting
The critical issue was in the frontend's `GameService.ts`. The backend sends player data in two places:
1. `data.players` - Contains full player info including `zero_declares_in_a_row`
2. `data.phase_data.players` - Contains phase-specific player info WITHOUT `zero_declares_in_a_row`

**Problem Code:**
```typescript
// This completely replaced player data, losing zero_declares_in_a_row
if (phaseData.players) {
  newState.players = phaseData.players;
}
```

**Fix:**
```typescript
// Now merges data, preserving zero_declares_in_a_row
if (phaseData.players) {
  const existingPlayersMap = new Map(newState.players.map(p => [p.name, p]));
  newState.players = phaseData.players.map((player: any) => {
    const existing = existingPlayersMap.get(player.name);
    return {
      ...player,
      zero_declares_in_a_row: existing?.zero_declares_in_a_row || 0
    };
  });
}
```

### Issue 3: Frontend Not Passing consecutiveZeros
The `GameContainer.jsx` was hardcoding `consecutiveZeros: 0` instead of getting it from player data.

**Problem Code:**
```javascript
consecutiveZeros: 0, // TODO: Get from backend if needed
```

**Fix:**
```javascript
const currentPlayerData = gameState.players?.find(p => p.name === gameState.playerName);
const consecutiveZeros = currentPlayerData?.zero_declares_in_a_row || 0;
```

## What Blocked the Investigation

### 1. Data Flow Complexity
The backend sends player data through multiple channels:
- Automatic broadcasting system (`data.players`)
- Phase-specific data (`phase_data.players`)
- Different data structures with different fields

This made it difficult to track where the `zero_declares_in_a_row` value was being lost.

### 2. Timing Issues
The bug manifested as a race condition where:
- `consecutiveZeros` would show 2 (correct)
- Then reset to 0 (incorrect)
- Then the player could declare 0 again
- Only after declaration would it show 3

This intermittent behavior made it hard to identify the exact cause.

### 3. Missing Backend Logging
The backend wasn't logging the zero streak updates, so we couldn't see if the backend was tracking correctly. We had to add debug logs to trace the issue.

### 4. Frontend State Management
The frontend's state updates happen through multiple paths, and the overwriting behavior wasn't immediately obvious. The issue only became clear when examining the exact sequence of state changes in the browser console logs.

## Lessons Learned

1. **Data Consistency**: When merging data from multiple sources, always preserve critical fields that might not be present in all sources.

2. **Debug Logging**: Add comprehensive debug logging for state tracking, especially for game rules that depend on historical data.

3. **Backend-Frontend Contract**: Document which fields are sent in which events to avoid assumptions about data availability.

4. **State Management**: Be careful when replacing entire objects/arrays in state - consider merging instead of overwriting to preserve data.

## Verification
After the fix:
- Players can declare 0 once
- Players can declare 0 twice
- On the third round, the "0" option is disabled with message "No third consecutive 0"
- The restriction properly enforces the game rule