# Never-Win Combo Root Cause Analysis

## Summary

After detailed analysis with hand states, we found that **8 out of 26 never-win combos (31%)** were poor AI choices where better alternatives existed. All 8 cases were SOLDIER_BLACK pairs.

## Root Cause Identified

The bug is in the **responder strategy** in `ai_turn_strategy.py` at line 1033:

```python
# Take required number from disposal candidates
if len(disposal_candidates) >= required:
    pieces_to_play = disposal_candidates[:required]
```

### The Problem

When `required=2`, the responder strategy:
1. Builds a priority list of pieces to dispose (burden → reserve → openers)
2. **Simply takes the first 2 pieces** from this list
3. **Does NOT check if they form a valid pair**
4. **Does NOT check if it's a never-win combo**

### Why This Happens

In all 8 poor choice cases:
- Players needed to win more turns (piles_needed > 0)
- Responder strategy was activated (not starter)
- Required pieces = 2
- SOLDIER_BLACK pieces were in the "burden" category (low-value pieces to dispose)
- The code took the first 2 SOLDIER_BLACK pieces without checking alternatives

### Example Case

```
Game AI_96414, Round 6, Turn 3
Player: Bot 2
Declared: 5, Captured: 3, Piles needed: 2
Remaining hand: ELEPHANT_BLACK, HORSE_RED, ELEPHANT_BLACK, ADVISOR_BLACK, 
                SOLDIER_BLACK, SOLDIER_BLACK, CANNON_RED, CHARIOT_RED

What happened:
1. Responder strategy activated
2. SOLDIER_BLACK pieces classified as "burden" (low value)
3. Code took first 2 pieces: SOLDIER_BLACK + SOLDIER_BLACK
4. Ignored available ELEPHANT_BLACK pair (18 pts)
```

## Fix Required

The responder strategy needs to:
1. When `required > 1`, check for valid combinations
2. Filter out never-win combos if alternatives exist
3. Select the best valid combination from disposal candidates
4. Only fall back to arbitrary pieces if no valid combos exist

## Code Location

File: `backend/engine/ai_turn_strategy.py`
Function: `execute_responder_strategy`
Lines: 1032-1056 (disposal selection logic)