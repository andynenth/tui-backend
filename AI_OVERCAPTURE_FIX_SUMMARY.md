# AI Overcapture Avoidance Fix Summary

## Issue Found
Bot 3 in round 3 of room A9B136 played a strong CHARIOT pair (16 points) when they had declared 0 and already had 0 piles captured. This was the opposite of what should happen - they should have played weak pieces to avoid winning.

## Root Cause
The `async_bot_strategy.py` module was being used instead of the strategic AI. The async bot strategy was only calling the basic `ai.choose_best_play()` function, which always tries to play the strongest hand, not the new `choose_strategic_play()` that includes overcapture avoidance.

## Fix Applied

### 1. Updated `async_bot_strategy.py`
- Modified `choose_best_play()` method to accept a `context` parameter
- Added logic to use strategic AI when context is provided
- Falls back to basic AI when no context

### 2. Updated `bot_manager.py`
- Modified async bot strategy call to pass the TurnPlayContext
- Fixed import issues for `get_play_type`
- Added comprehensive logging

### 3. Added Logging
- Strategic AI logs when overcapture avoidance activates
- Bot manager logs what pieces are played and why
- Clear indication when bot is "at target" and playing weakly

## Verification
Created test script that confirms:
- ✅ Strategic AI is called for bots
- ✅ Overcapture avoidance activates when bot is at target
- ✅ Bot plays weakest pieces when at declared target

## What Actually Happened (Before Fix)

From room A9B136, round 3, Bot 3's turn:
- Bot 3 declared: 0 piles
- Bot 3 captured: 0 piles (already at target!)
- Bot 3's complete hand was:
  - CHARIOT_BLACK(7) - 1 piece
  - SOLDIER_BLACK(1) - 3 pieces
  - CHARIOT_RED(8) - 2 pieces  
  - HORSE_BLACK(5) - 1 piece
  - Total: 7 pieces
- Required to play: 2 pieces
- Bot 3 played: CHARIOT_RED(8) + CHARIOT_RED(8) = 16 points ❌
- Should have played: SOLDIER_BLACK(1) + SOLDIER_BLACK(1) = 2 points ✓
- Result: Bot 3 won the turn and captured 2 extra piles!

## Example Output (After Fix)
When we tested the same scenario after the fix:
```
📊 Building context for Bot 3: pile_counts={'Bot 1': 0, 'Bot 2': 0, 'Bot 3': 0, 'Bot 4': 0}, bot_captured=0, bot_declared=0
🤖 Strategic AI wrapper called for Bot 3
🎯 Strategic AI for Bot 3: captured=0, declared=0, required=2
🛡️ Bot 3 is at target (0/0) - activating overcapture avoidance
🎲 Bot 3 plays weak pieces (value=2) to avoid overcapture: ['SOLDIER', 'SOLDIER']
🤖 BOT Bot 3 (at target 0/0) plays weakly: PAIR (2 pts): SOLDIER, SOLDIER
```

Now Bot 3 correctly plays SOLDIER_BLACK(1) + SOLDIER_BLACK(1) = 2 points instead of the strong CHARIOT pair!

## Impact
All bots will now correctly avoid winning extra piles when they've already reached their declared target, preventing overcapture and the associated scoring penalties.