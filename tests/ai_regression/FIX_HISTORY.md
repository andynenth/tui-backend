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

## Fix #6: Object Comparison in Disposal Strategy

**Date**: 2025-08-29
**Bug**: Responder disposal strategy failed to identify burden pieces
**Root Cause**: 
1. Disposal strategy used `if p in context.my_hand` for object comparison
2. Plan pieces and context.my_hand contained different Piece objects
3. Python's `in` operator checks object identity, not equality
4. Result: burden_in_hand was always empty, causing incorrect disposal

**Fix**: 
Changed object comparison to compare by piece.kind:
```python
# OLD (broken):
burden_in_hand = [p for p in plan.burden_pieces if p in context.my_hand]

# NEW (fixed):
plan_burden_kinds = {p.kind for p in plan.burden_pieces}
burden_in_hand = [p for p in context.my_hand if p.kind in plan_burden_kinds]
```

Applied same fix to all disposal priorities:
- burden_in_hand (line 881)
- reserve_in_hand (line 887)
- openers_in_hand (line 894)
- combo_pieces_in_hand (line 903)

**Test**: `test_object_comparison_fix.py`

**Impact**: 
- Disposal strategy now correctly identifies pieces by type
- Burden pieces are properly disposed when they exist
- Preserves important pieces like openers and combos
- Note: Bot 2's specific scenario still has issues due to excessive combo assignment

## Fix #7: Zero Streak Declaration Bug

**Date**: 2025-08-29
**Bug**: Bot with zero streak declared 0 despite must_declare_nonzero=True
**Root Cause**: 
1. Early returns in non-starter logic bypassed forbidden value checking
2. Variable `has_general_red` was undefined in starter branch
3. `rebuild_play_list_avoiding_forbidden` returned empty list when no valid combos

**Fix**: 
1. Moved `has_general_red` check to beginning of function
2. Replaced early `return 0` statements with `declaration = 0` to allow forbidden value checking
3. Updated `rebuild_play_list_avoiding_forbidden` to force non-zero declaration when required
4. Handle edge case where pile_room=0 but must_declare_nonzero=True

**Test**: `test_zero_streak_fix.py`

**Impact**: 
- Bots now correctly respect zero streak rule and declare at least 1
- Prevents game getting stuck when bot repeatedly tries to declare 0
- Handles edge cases like no pile room or no opener scenarios

## Fix #8: Declaration Calculation Bug and Opener Threshold Issue

**Date**: 2025-08-29
**Bug**: AI declaring 0 with strong hands (2-3 openers available)
**Root Cause**: 
1. Declaration calculation was incorrectly indented inside final room adjustment block
2. `get_piece_threshold` was using variable thresholds based on pile room instead of standard 11+ definition
**Fix**: 
1. Fixed indentation so declaration is always calculated from play_list
2. Changed to use standard opener threshold of 11 points regardless of pile room
3. Removed dynamic threshold logic that was too restrictive

**Code Changes**:
- Line ~1339: Moved declaration calculation outside of the if block
- Lines ~1261, ~1287, ~1330, ~934: Use fixed `opener_threshold = 11` instead of `get_piece_threshold(pile_room)`

**Test**: Manual testing shows zero_declaration_strong_hand bugs eliminated

**Impact**: 
- AI now correctly declares based on actual openers (11+ point pieces)
- Eliminated false "zero declaration with strong hand" bugs
- Better declaration accuracy while maintaining zero streak rule functionality

## Running Regression Tests

```bash
cd tests/ai_regression
source ../../venv/bin/activate
python run_all_regression_tests.py
```

All tests should pass before committing any AI changes.