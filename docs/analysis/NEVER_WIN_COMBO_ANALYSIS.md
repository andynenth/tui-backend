# Never-Win Combo Analysis

## Problem: Never-Win Combo Detection Not Implemented

### What are Never-Win Combos?

Based on the test file, never-win combos are combinations that can never win a turn:

1. **All-BLACK Straights**
   - Example: CANNON_BLACK(3) + HORSE_BLACK(5) + CHARIOT_BLACK(7) = 15 points
   - These have the minimum possible points for a straight
   - Any other straight will beat them

2. **Minimum Pairs**
   - Example: SOLDIER_BLACK + SOLDIER_BLACK = 2 points total
   - Lowest possible pair value
   - Any other pair will beat them

3. **Minimum Three/Four/Five of a Kind**
   - Three SOLDIER_BLACK = 3 points total
   - Four SOLDIER_BLACK = 4 points total
   - Five SOLDIER_BLACK = 5 points total

### Current Status

**Test exists**: `tests/ai_regression/test_never_win_combo.py`
- Tests import `is_never_win_combo` from `backend.engine.ai_turn_strategy`
- Tests check detection of all-BLACK straights and minimum soldier combos
- Tests verify responders avoid these combos when possible

**Implementation missing**: 
- `is_never_win_combo()` function not found in codebase
- The import in the test would fail if run
- No logic to avoid these combos in actual gameplay

### Impact on Game Performance

Without never-win detection:
1. Bots may play unwinnable combinations
2. This wastes pieces that could be used strategically
3. May contribute to poor declaration accuracy
4. Bots declaring high might count these as "winning combos"

### Why This Matters

If a bot plays a never-win combo:
- It's guaranteed to lose that turn
- Wastes 2-6 pieces depending on combo type
- Reduces ability to win future turns
- May lead to missing declaration targets

### Recommendation

Implement `is_never_win_combo()` in `ai_turn_strategy.py` to:
1. Detect these minimum-value combinations
2. Avoid playing them unless no other option
3. Don't count them as "winning plays" when declaring