# AI Fix History

This document tracks all AI bugs fixed and their solutions.

## Fix #1: Combo Preservation When Declaring 0

**Date**: 2025-08-28
**Bug**: Bot 3 preserved ADVISOR_RED pair when declaring 0
**Root Cause**: AI assigned combos to plan regardless of target_remaining
**Fix**: Only preserve combos if target_remaining > 0 (ai_turn_strategy.py line ~637)
**Test**: `test_combo_preservation_fix.py`

**Note**: When declaring 0, the AI correctly disposes high-value pieces first, including combo pieces. This is intentional - no pieces should be "preserved" for future turns.

## Fix #2: Combo Rank Priority in Critical Urgency

**Date**: 2025-08-28  
**Bug**: Bot 2 with critical urgency played GENERAL_RED(14) instead of THREE_OF_A_KIND
**Root Cause**: Critical urgency logic maximized point value instead of combo rank
**Fix**: 
1. Added missing EXTENDED_STRAIGHT_5 to COMBO_TYPE_RANK
2. Updated critical urgency to prioritize combo rank over points (ai_turn_strategy.py line ~1031)
3. Updated combo sorting to use rank-first approach (line ~1215)

**Test**: `test_combo_rank_priority.py`

**Impact**: AI now correctly understands that combo type determines winner, not total points. THREE_OF_A_KIND beats any SINGLE regardless of points.

## Fix #3: Opener Assignment Based on Declaration

**Date**: 2025-08-28
**Bug**: Bot 4 declared 4 but only assigned 2 openers, disposing ADVISOR pieces as "burden"
**Root Cause**: Opener assignment was hard-coded to max 2 for declarations of 4+
**Fix**: Opener assignment now scales with target_remaining (ai_turn_strategy.py line ~598)
```python
openers_needed = min(target_remaining, 4, len(all_openers))
```

**Test**: `test_opener_assignment_fix.py`

**Impact**: Bots now preserve appropriate number of openers based on their declaration. Bot declaring 4 preserves 4 openers, bot declaring 2 preserves 2, etc.

## Fix #4: Smart Opener Assignment with Combo Consideration

**Date**: 2025-08-28
**Bug**: AI assigns openers based on target_remaining without considering secured wins from combos
**Root Cause**: Opener assignment happened before combo counting, treating them as independent
**Fix**: Count secured wins from non-opener combos first, then assign openers (ai_turn_strategy.py lines ~580-615)
```python
# Count secured wins from non-opener combos
secured_wins = 0
opener_set = set(all_openers)

for combo_type, pieces in viable_combos:
    if not any(p in opener_set for p in pieces):
        secured_wins += 1

# Smart calculation
openers_needed = max(0, target_remaining - secured_wins)
```

**Test**: `test_smart_opener_assignment.py`

**Impact**: AI now intelligently assigns openers based on actual needs:
- Target 3 with 1 combo → assigns 2 openers (not hard-coded)
- Target 3 with 0 combos → assigns 3 openers (not capped at 2)
- Target 4 with THREE_OF_A_KIND → assigns 3 openers (not all 4)
- More efficient resource utilization and better late-game performance

**Update**: Code structure simplified from 27 lines with redundant if-elif branches to 14 lines with unified logic. All functionality preserved.

## Fix #5: Urgency-Based Random Opener Play

**Date**: 2025-08-28
**Bug**: Bots always played their strongest opener when playing singles, making them predictable
**Root Cause**: 
1. Urgency calculation didn't consider competitive pressure (room concept)
2. Random opener play was restricted to "opener-only plan" scenarios
3. Always selected max(openers) by point value

**Fix**: 
1. Rewrote urgency calculation to use room = remaining_turns - max_opponent_target_remaining
2. Enable random opener play when urgency == "low" (not urgent)
3. Use random.choice() instead of max() for opener selection
4. Applied to both responder and starter strategies

**Test**: `test_urgency_random_opener.py`

**Impact**: 
- Bots now understand when they have room to play flexibly vs when they must compete
- Opener play is unpredictable - any opener can be selected randomly
- Better simulation of human play patterns
- Strategic play kicks in automatically when room becomes tight

## Running Regression Tests

```bash
cd tests/ai_regression
source ../../venv/bin/activate
python run_all_regression_tests.py
```

All tests should pass before committing any AI changes.