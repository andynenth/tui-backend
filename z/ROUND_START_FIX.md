# Round Start Phase Fix

## Problem
After implementing the ROUND_START phase, the game was encountering errors:
```
❌ Invalid transition: GamePhase.PREPARATION -> GamePhase.DECLARATION
❌ STATE_MACHINE_DEBUG: Invalid transition blocked!
```

## Root Cause
Multiple places in the code were trying to transition directly from PREPARATION to DECLARATION, but the new flow requires:
- PREPARATION → ROUND_START → DECLARATION

## Fixes Applied

### 1. Bot Manager Notification (game_state_machine.py)
Updated `_notify_bot_manager` method to handle ROUND_START phase:
- When transitioning to ROUND_START: Send simple "phase_change" event
- When transitioning to DECLARATION: Send "round_started" event to trigger bot declarations

### 2. Preparation State Transitions (preparation_state.py)
Fixed two locations that were transitioning to DECLARATION:
- Line 671: `check_transition_conditions` now returns `GamePhase.ROUND_START` instead of `GamePhase.DECLARATION`
- Line 325: `_handle_redeal_decision` now transitions to `GamePhase.ROUND_START` after redeal decisions

## Testing
To test the fix:
1. Restart the server: `./start.sh`
2. Create a new game with bots
3. Verify the phase flow:
   - PREPARATION (cards dealt)
   - ROUND_START (5 seconds, shows starter)
   - DECLARATION (bots declare normally)
4. Check that no "Invalid transition" errors appear in the console

## Code Change
```python
# Before: Bot manager notified on DECLARATION phase
if new_phase == GamePhase.DECLARATION:
    await bot_manager.handle_game_event(room_id, "round_started", ...)

# After: Separate handling for ROUND_START and DECLARATION
if new_phase == GamePhase.ROUND_START:
    # Just notify, no bot actions
    await bot_manager.handle_game_event(room_id, "phase_change", ...)
elif new_phase == GamePhase.DECLARATION:
    # Now trigger bot declarations
    await bot_manager.handle_game_event(room_id, "round_started", ...)
```