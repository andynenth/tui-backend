# AI Pile Counting Fix - Implementation Summary

## What We Fixed

### 1. Critical Bug: Pile Counting
**Problem**: AI was counting NUMBER of combinations instead of PILES they yield
- Old: `score = len(strong_combos)` → STRAIGHT counted as 1
- New: STRAIGHT correctly counted as 3 piles

**Impact**: This explains why bots seemed conservative in declarations - they were under-counting by 2-5 piles per hand!

### 2. Opener Detection  
**Problem**: Only GENERAL pieces (13+ points) were considered openers
- Old: Missed ADVISOR pieces (11-12 points)
- New: All pieces with 11+ points are openers

**Impact**: More hands now correctly identified as having control potential

## Test Results

Our test script confirmed the fixes are working:

1. **ADVISOR + STRAIGHT**: Correctly declares 4 (was 2)
2. **GENERAL + Multiple Combos**: Correctly declares 7 (was 3-4)
3. **Weak Hands**: Still conservative as expected

## Remaining Issue

**Overlapping Combinations**: The AI finds all possible combinations even if they share pieces
- Example: 4 SOLDIERs → counts as THREE_OF_A_KIND × 4 + FOUR_OF_A_KIND
- This causes over-declaration in some cases
- Fix needed: Choose best non-overlapping combinations

## Code Changes

```python
# backend/engine/ai.py - choose_declare()

# OLD: Just counted combinations
score = len(strong_combos)

# NEW: Count actual piles
score = 0
for combo_type, pieces in strong_combos:
    if combo_type in ["THREE_OF_A_KIND", "STRAIGHT"]:
        score += 3  # 3-piece play = 3 piles
    elif combo_type in ["FOUR_OF_A_KIND", "EXTENDED_STRAIGHT"]:
        score += 4  # 4-piece play = 4 piles
    # ... etc

# OLD: Only GENERAL or 13+ points
has_strong_opening = any(
    p.name.startswith("GENERAL") or p.point >= 13 for p in hand
)

# NEW: Include ADVISOR pieces (11+ points)  
has_strong_opening = any(
    p.point >= 11 for p in hand
)
```

## Expected Impact

- Bots will declare more aggressively (3-5 instead of 1-2)
- Better reflection of actual hand strength
- More realistic gameplay similar to human players
- Some over-declaration due to overlap issue (to be fixed)

## Next Steps

1. Test in actual games to verify improved behavior
2. Fix combination overlap issue
3. Consider simple adjustments based on game state (later)