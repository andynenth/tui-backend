# Scoring System Refactoring Plan

## Current Issues

### 1. Duplicate Implementation Problem

There are currently **three different implementations** of scoring logic:

1. **`calculate_score()` in `scoring.py`**
   - Returns the OLD scoring logic (includes bonuses in base score)
   - Used by `calculate_round_scores()`
   - Does NOT implement the new multiplier rules

2. **`calculate_round_scores()` in `scoring.py`**
   - Uses the OLD scoring logic via `calculate_score()`
   - Applies multiplier to ENTIRE score (including bonuses)
   - Returns a list of dictionaries
   - NOT used by the actual game

3. **`ScoringState._calculate_round_scores()` in `scoring_state.py`**
   - Implements the NEW scoring logic directly
   - Multipliers only apply to base points, not bonuses
   - This is what the actual game uses
   - Does NOT call any functions from `scoring.py`

### 2. Inconsistency Problems

- **Different Rules**: `scoring.py` implements old rules, `scoring_state.py` implements new rules
- **Maintenance Risk**: Changes must be made in multiple places
- **Confusion**: Unclear which implementation is authoritative
- **Dead Code**: `calculate_round_scores()` appears to be unused

### 3. Current Scoring Rules (as implemented in ScoringState)

| Scenario | Formula | Example (2x multiplier) |
|----------|---------|------------------------|
| Declared 0, Got 0 | +3 (no multiplier) | +3 |
| Declared 0, Got X | -X × multiplier | -2 × 2 = -4 |
| Declared X, Got X | (X × multiplier) + 5 | (3 × 2) + 5 = 11 |
| Declared X, Got Y | -\|X-Y\| × multiplier | -2 × 2 = -4 |

## Proposed Solution

### Option 1: Centralize in `scoring.py` (Recommended)

1. **Update `calculate_score()` to return structured data:**
```python
def calculate_score(declared: int, actual: int) -> dict:
    """
    Calculate scoring components based on declared and actual piles.
    
    Returns:
        dict: {
            'base_points': int,  # The X value (declared amount or penalty)
            'bonus': int,        # Fixed bonus (0, 3, or 5)
            'is_penalty': bool   # Whether base_points should be negative
        }
    """
```

2. **Create new `calculate_final_score()` function:**
```python
def calculate_final_score(declared: int, actual: int, multiplier: int = 1) -> int:
    """
    Calculate final score with multiplier applied correctly.
    
    Returns:
        int: Final score with multiplier applied only to base points
    """
```

3. **Update `ScoringState._calculate_round_scores()` to use these functions**

4. **Remove or deprecate `calculate_round_scores()` if truly unused**

### Option 2: Keep Implementation in ScoringState

1. **Delete unused functions from `scoring.py`:**
   - Remove `calculate_score()`
   - Remove `calculate_round_scores()`

2. **Extract scoring logic from `ScoringState` into reusable methods**

3. **Document that scoring logic lives in the state machine**

### Option 3: Create New Scoring Module

1. **Create `backend/engine/scoring_v2.py`:**
   - Implement new scoring rules cleanly
   - Provide clear API for state machine to use

2. **Deprecate old `scoring.py`**

3. **Update all references to use new module**

## Implementation Steps (for Option 1)

### Phase 1: Update scoring.py

1. **Create new functions with correct logic:**
```python
def calculate_score_components(declared: int, actual: int) -> dict:
    """Calculate base points, bonus, and penalty flag."""
    
def calculate_final_score(declared: int, actual: int, multiplier: int = 1) -> int:
    """Calculate final score with new multiplier rules."""
```

2. **Add deprecation warning to old `calculate_score()`**

3. **Fix or remove `calculate_round_scores()`**

### Phase 2: Update ScoringState

1. **Replace inline logic with calls to new functions:**
```python
# Instead of inline if/elif/else blocks:
final_score = calculate_final_score(declared, actual, multiplier)
```

2. **Maintain same output structure for frontend compatibility**

3. **Remove duplicate logic**

### Phase 3: Testing

1. **Create comprehensive test suite for new scoring functions**
2. **Ensure frontend still receives expected data structure**
3. **Test with various multiplier scenarios**
4. **Verify no regression in game behavior**

### Phase 4: Cleanup

1. **Remove old unused functions**
2. **Update documentation**
3. **Remove debug print statements**

## Benefits of Refactoring

1. **Single Source of Truth**: Scoring logic in one place
2. **Easier Maintenance**: Change rules in one location
3. **Better Testing**: Can unit test scoring logic independently
4. **Clearer Code**: Explicit function names and purposes
5. **Reduced Bugs**: No risk of implementations diverging

## Risks and Mitigation

### Risk 1: Breaking Frontend
- **Mitigation**: Maintain exact same data structure in `round_scores`
- **Testing**: Verify all fields still present

### Risk 2: Missing Edge Cases
- **Mitigation**: Comprehensive test suite before refactoring
- **Testing**: Test all declaration/actual combinations

### Risk 3: Performance Impact
- **Mitigation**: Profile before/after if concerned
- **Note**: Function calls are negligible overhead

## Decision Required

Before proceeding, decide:

1. **Which option to implement?** (Recommended: Option 1)
2. **When to implement?** (Consider current sprint/priorities)
3. **Who will test?** (Need thorough testing of scoring scenarios)

## Alternative: Document Current State

If refactoring is not immediate priority:

1. **Add clear comments** explaining which implementation is used
2. **Mark unused code** with deprecation warnings
3. **Document** that `ScoringState` contains authoritative implementation
4. **Create ticket** for future refactoring

## Conclusion

The current duplicate implementation is a technical debt that should be addressed. The recommended approach is to centralize scoring logic in `scoring.py` with new functions that implement the current rules correctly, then update `ScoringState` to use these functions instead of reimplementing the logic inline.