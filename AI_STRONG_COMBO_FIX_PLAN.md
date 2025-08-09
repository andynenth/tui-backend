# AI Strong Combo Fix Plan

## Problem Analysis

The current implementation uses **average piece value > 6** to determine if a combo is "strong". This is fundamentally flawed because:

1. **THREE_OF_A_KIND beats PAIR** in game hierarchy, but:
   - THREE_OF_A_KIND SOLDIERs: avg = 1-2 points (considered weak)
   - PAIR of HORSEs: avg = 5-6 points (considered at threshold)

2. **Original Intent**: "Strong combo is whatever higher than pair of HORSE_RED"
   - This should mean combos that **beat** a HORSE pair in gameplay
   - OR combos with **total value > 12 points** (HORSE_RED pair)

## Correct Interpretation

Based on the game rules and the original intent, a "strong combo" should be:

### Option 1: Hierarchy-Based (Recommended)
A combo is strong if it's **THREE_OF_A_KIND or higher** in the play type hierarchy:
- THREE_OF_A_KIND ✓
- STRAIGHT ✓
- FOUR_OF_A_KIND ✓
- EXTENDED_STRAIGHT ✓
- EXTENDED_STRAIGHT_5 ✓
- FIVE_OF_A_KIND ✓
- DOUBLE_STRAIGHT ✓
- PAIR ✗ (not strong enough)

### Option 2: Value-Based
A combo is strong if its **total value > 12** (value of HORSE_RED pair):
- GENERAL pair: 28 or 26 points ✓
- ADVISOR pair: 24 or 22 points ✓
- ELEPHANT pair: 20 or 18 points ✓
- CHARIOT pair: 16 or 14 points ✓
- HORSE pair: 12 or 10 points ✗
- Any straight with high pieces ✓
- SOLDIER combos: usually ✗

### Option 3: Hybrid Approach
- For PAIR: total value must be > 12
- For all other combo types: always considered strong

## Implementation Changes

### 1. Update `is_strong_combo()` function

```python
def is_strong_combo(combo_type: str, pieces: List) -> bool:
    """
    Check if a combo qualifies as a strong combo.
    
    A combo is strong if:
    - It's THREE_OF_A_KIND or higher in hierarchy, OR
    - It's a PAIR with total value > 12 (HORSE_RED pair)
    
    Args:
        combo_type: Type of combo
        pieces: List of pieces in the combo
        
    Returns:
        True if combo is strong
    """
    # Option 1: Hierarchy-based (recommended)
    if combo_type in ["THREE_OF_A_KIND", "STRAIGHT", "FOUR_OF_A_KIND", 
                      "EXTENDED_STRAIGHT", "EXTENDED_STRAIGHT_5", 
                      "FIVE_OF_A_KIND", "DOUBLE_STRAIGHT"]:
        return True
    
    # For PAIR, check if stronger than HORSE_RED pair
    if combo_type == "PAIR":
        total_value = sum(p.point for p in pieces)
        return total_value > 12  # HORSE_RED pair = 12 points
    
    return False
```

### 2. Update or Remove `STRONG_COMBO_MIN_AVG`

Since we're not using average anymore, we should:
- Remove `STRONG_COMBO_MIN_AVG = 6`
- Add `HORSE_PAIR_VALUE = 12` as the threshold for pairs

### 3. Update Constants

```python
# Strong combo types (hierarchy-based)
STRONG_COMBO_TYPES = {
    "THREE_OF_A_KIND",
    "STRAIGHT", 
    "FOUR_OF_A_KIND",
    "EXTENDED_STRAIGHT",
    "EXTENDED_STRAIGHT_5",
    "FIVE_OF_A_KIND",
    "DOUBLE_STRAIGHT"
}

# Threshold for PAIR to be considered strong
STRONG_PAIR_THRESHOLD = 12  # Total value must exceed HORSE_RED pair
```

## Test Impact Analysis

This change will affect many test expectations:

1. **CHR-HRS-CNN straight** (avg=5, but STRAIGHT type) → Now STRONG ✓
2. **SOLDIER THREE_OF_A_KIND** (avg=1-2, but THREE_OF_A_KIND) → Now STRONG ✓
3. **Low-value pairs** (e.g., SOLDIER pairs) → Still WEAK ✗
4. **High-value pairs** (e.g., GENERAL, ADVISOR) → Still STRONG ✓

## Implementation Steps

1. **Update `is_strong_combo()` function** with new logic
2. **Remove/update constants** related to average calculation
3. **Update test expectations** in test files
4. **Run all tests** to identify failures
5. **Update expected values** based on new logic
6. **Document the change** in code comments

## Expected Behavior Changes

### For Starters:
- Will now count THREE_OF_A_KIND and STRAIGHT as strong combos
- Will declare higher values when holding these combos
- More aggressive declarations overall

### For Non-starters:
- Still need opener first
- But after finding opener, will count more combos as strong
- Slightly more aggressive declarations

## Questions to Clarify

1. Should we use **Option 1** (hierarchy-based) or **Option 3** (hybrid)?
2. For pairs, is 12 the correct threshold (total value > HORSE_RED pair)?
3. Should SOLDIER combos be considered strong despite low value?