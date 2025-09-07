# Comprehensive WebSocket Reconnection Bug Report

## Executive Summary
Multiple critical issues occur when refreshing the page during an active game:
1. **Avatar colors are lost** (all players show `null`)
2. **Bot states are incorrect** (all players show as human)
3. **Game state not restored** (shows "Waiting for Game" instead of actual game phase)

## Bugs Identified

### Bug 1: Avatar Colors and Bot States Lost After Reconnection
**Severity**: High
**Impact**: Visual confusion, incorrect player representation

#### Details:
- When refreshing during Declaration phase, all players lose their avatar colors
- Bot players are incorrectly marked as human (`is_bot: false`)
- Root cause: Disconnect handler only saves state for human players, not bots

#### Evidence:
```javascript
// Before refresh:
🎨 Declaration player data: TestPlayer avatar_color: pink is_bot: false
🎨 Declaration player data: Bot 2 avatar_color: null is_bot: true

// After refresh:
🎨 Declaration player data: TestPlayer avatar_color: null is_bot: false
🎨 Declaration player data: Bot 2 avatar_color: null is_bot: false  // WRONG!
```

### Bug 2: Game State Not Restored - Shows "Waiting for Game"
**Severity**: Critical
**Impact**: Players cannot continue playing after refresh

#### Details:
- When refreshing during Turn phase (or any game phase), the UI shows "Waiting for Game"
- The backend sends phase_change events but the frontend doesn't process them correctly
- The game is active but the UI is stuck in waiting state

#### Evidence:
- Before refresh: Turn phase with pieces visible
- After refresh: "Waiting for Game" screen despite active game

### Bug 3: Inconsistent State Restoration
**Severity**: High
**Impact**: Unpredictable behavior across different game phases

#### Details:
- Avatar colors are restored when transitioning between phases normally
- But NOT restored during reconnection
- This suggests the phase transition logic has correct data but reconnection logic doesn't

## Root Cause Analysis

### 1. Backend Disconnect Handler (`ws.py` lines 102-111)
```python
if player and not player.is_bot:  # Only processes human players!
    player.original_is_bot = player.is_bot
    player.original_avatar_color = getattr(player, 'avatar_color', None)
```
- Only human players get their state saved
- Bot players are ignored, losing their avatar state

### 2. Backend Reconnection Handler (`ws.py` lines 699-707)
```python
if player and player.is_bot and not player.original_is_bot:
    # This condition fails for bots because they don't have original_is_bot set
    player.is_bot = False
    player.avatar_color = player.original_avatar_color
```
- Condition fails for actual bots
- Avatar restoration happens inside this block, so it's skipped

### 3. Frontend State Management
- The frontend receives `phase_change` events but doesn't transition from "waiting" state
- Likely missing state transition logic for reconnection scenarios

## Reproduction Steps

### Test 1: Avatar Color Loss
1. Create room and start game
2. Note player avatar colors in Declaration phase
3. Refresh page
4. Observe all avatar colors are null

### Test 2: Game State Not Restored
1. Create room and start game
2. Progress to Turn phase
3. Refresh page
4. Observe "Waiting for Game" instead of Turn phase

## Recommended Fixes

### Fix 1: Backend - Preserve Bot State
```python
# In disconnect handler
if player:
    # Store state for ALL players, not just humans
    player.original_is_bot = player.is_bot
    player.original_avatar_color = getattr(player, 'avatar_color', None)

    if not player.is_bot:  # Only convert humans to bots
        player.is_bot = True
        player.is_connected = False
```

### Fix 2: Backend - Restore All Player States
```python
# In reconnection handler
if player:
    # Restore original bot state
    if hasattr(player, 'original_is_bot'):
        player.is_bot = player.original_is_bot

    # Restore avatar color for ALL players
    if hasattr(player, 'original_avatar_color'):
        player.avatar_color = player.original_avatar_color

    # Handle human reconnection
    if player.name == player_name and not player.original_is_bot:
        player.is_connected = True
        player.disconnect_time = None
```

### Fix 3: Frontend - Handle Reconnection State
- Ensure phase_change events transition the UI from "waiting" to actual game state
- Add explicit handling for reconnection scenarios
- Consider requesting full game state on reconnection

## Test Results Summary

| Phase | Issue | Severity |
|-------|-------|----------|
| Declaration | Avatar colors lost, bots show as human | High |
| Turn | Shows "Waiting for Game", avatar colors lost | Critical |
| All phases | Inconsistent state restoration | High |

## Impact
- **User Experience**: Severely degraded, game appears broken after refresh
- **Game Integrity**: State inconsistencies could affect gameplay
- **Trust**: Players lose confidence when UI doesn't match game state
