# Single Opener Random Timing Feature - Comprehensive Fix Plan

## Overview

Fix the broken single opener random timing feature that currently never activates due to checking the wrong variable at the wrong time.

## Current Issues

1. **Timing Error**: Feature checks `context.required_piece_count == 1` which is always `None` for starters
2. **Logic Location**: Code executes AFTER starter has already chosen piece count
3. **Variable Shadowing**: `random.sample()` fails due to local variable named `random_value`
4. **Incomplete Implementation**: Only attempts to handle one case, missing responder logic

## Feature Requirements

### Starter Behavior
- When bot is starter with opener-only plan
- Random chance (35-50%) to force single-piece play
- Overrides normal strategy to play strongest opener

### Responder Behavior  
- When required = 1 AND bot has opener-only plan
- Random chance (35-50%) to play opener vs other strategies
- Adds variety to single-piece responses

## Implementation Plan

### Phase 1: Code Cleanup and Extraction

#### 1.1 Remove Broken Code Block
**Location**: `ai_turn_strategy.py` lines 922-970
```python
# DELETE THIS ENTIRE BLOCK:
if context.required_piece_count == 1 and plan.assigned_openers:
    # ... all the broken logic ...
```

#### 1.2 Extract Reusable Logic
Create new helper function at module level (after imports):
```python
def should_randomly_play_opener(hand_size: int) -> bool:
    """
    Determine if bot should randomly play opener based on game stage.
    
    Args:
        hand_size: Number of pieces in hand
        
    Returns:
        True if random check succeeds, False otherwise
    """
    import random as rand_module  # Avoid name conflict
    
    # Probability increases as game progresses
    if hand_size >= 6:
        threshold = 0.35  # 35% early game
    elif hand_size >= 4:
        threshold = 0.40  # 40% mid game
    else:
        threshold = 0.50  # 50% late game
    
    return rand_module.random() < threshold


def detect_opener_only_plan(plan: StrategicPlan) -> bool:
    """
    Check if bot has an opener-only plan (no viable combos).
    
    Args:
        plan: Strategic plan with piece assignments
        
    Returns:
        True if only openers available, False otherwise
    """
    return (
        len(plan.assigned_openers) > 0 and
        len(plan.assigned_combos) == 0 and
        plan.main_plan_size == len(plan.assigned_openers)
    )
```

### Phase 2: Implement Starter Logic

#### 2.1 Add Opener Detection Early
At the beginning of `execute_starter_strategy()` (around line 800):
```python
def execute_starter_strategy(...):
    # FIRST THING: Detect opener-only plan
    opener_only_plan = detect_opener_only_plan(plan)
    
    # Debug logging
    if opener_only_plan:
        print(f"\n🎯 {context.my_name} has opener-only plan with {len(plan.assigned_openers)} openers")
```

#### 2.2 Modify Starter Decision Logic
Around line 838, BEFORE setting `required`:
```python
if context.required_piece_count is None:  # We're the starter
    # NEW: Random opener timing check FIRST
    if opener_only_plan:
        hand_size = len(hand)
        if should_randomly_play_opener(hand_size):
            print(f"🎲 {context.my_name} (STARTER) randomly forcing singles to play opener!")
            print(f"   - Hand size: {hand_size}, Probability was {35 if hand_size >= 6 else 40 if hand_size >= 4 else 50}%")
            required = 1
            # Skip all other starter logic
        else:
            print(f"🎲 {context.my_name} (STARTER) random check failed, using normal strategy")
            # Continue with existing logic
            if constraints.risk_level in ["high", "medium"]:
                required = min(required, constraints.max_safe_pieces)
            # ... rest of existing starter logic
    else:
        # No opener-only plan, use existing logic
        if constraints.risk_level in ["high", "medium"]:
            required = min(required, constraints.max_safe_pieces)
        # ... rest of existing starter logic
else:
    required = context.required_piece_count
```

### Phase 3: Implement Responder Logic

#### 3.1 Add Responder Decision Point
After `required` is determined (around line 900):
```python
# Initialize flag for later use
force_opener_play = False

# Check for responder opener timing
if required == 1 and not context.am_i_starter and opener_only_plan:
    hand_size = len(hand)
    if should_randomly_play_opener(hand_size):
        print(f"🎲 {context.my_name} (RESPONDER) randomly choosing to play opener!")
        print(f"   - Hand size: {hand_size}, Probability was {35 if hand_size >= 6 else 40 if hand_size >= 4 else 50}%")
        force_opener_play = True
    else:
        print(f"🎲 {context.my_name} (RESPONDER) random check failed, using normal strategy")
```

#### 3.2 Modify Play Selection Logic
Around line 950, when selecting pieces to play:
```python
# If we're forcing opener play, override other logic
if force_opener_play and plan.assigned_openers:
    strongest_opener = max(plan.assigned_openers, key=lambda p: p.point)
    selected_pieces = [strongest_opener]
    print(f"   → Playing opener: {strongest_opener.name}({strongest_opener.point})")
else:
    # Existing selection logic
    selected_pieces = select_pieces_for_play(...)
```

### Phase 4: Testing Strategy

#### 4.1 Existing Test Reuse
**File**: `test_single_opener_debug.py`
**Verdict**: KEEP and ENHANCE

The existing test is well-structured for testing the fix:
- Uses real game data (good test cases)
- Tracks opener play statistics
- Multiple iterations to verify randomness

**Required Modifications**:
1. Add separate tracking for starter vs responder opener plays
2. Verify randomness is working (should see 35-50% rates)
3. Add assertion checks for expected ranges

#### 4.2 Enhanced Test Structure
```python
def test_round_scenario(round_name: str, players_data: list, iterations: int = 100):
    """Test with more iterations and separate tracking"""
    
    # Enhanced tracking
    starter_opener_plays = {p[0]: 0 for p in players_data}
    starter_opportunities = {p[0]: 0 for p in players_data}
    responder_opener_plays = {p[0]: 0 for p in players_data}
    responder_opportunities = {p[0]: 0 for p in players_data}
    
    # ... test logic ...
    
    # Enhanced reporting
    print("\nSTARTER OPENER TIMING:")
    for name in starter_opener_plays:
        if starter_opportunities[name] > 0:
            rate = (starter_opener_plays[name] / starter_opportunities[name]) * 100
            print(f"  {name}: {rate:.1f}% ({starter_opener_plays[name]}/{starter_opportunities[name]})")
            # Verify randomness (should be 35-50% depending on hand size)
            assert 25 <= rate <= 60, f"Starter rate {rate}% outside expected range"
    
    print("\nRESPONDER OPENER TIMING:")
    # Similar for responders
```

#### 4.3 New Test Scenarios
Add specific test cases:
1. **Starter with opener-only plan** - Should see ~35-50% forcing singles
2. **Responder when singles required** - Should see ~35-50% playing opener
3. **Edge cases**: 
   - Only 1 piece left (no randomness needed)
   - Multiple openers (verify strongest is chosen)
   - Constraint conflicts (random should override)

### Phase 5: Verification Plan

1. **Unit Testing**
   - Run enhanced `test_single_opener_debug.py`
   - Verify rates match expected probabilities
   - Check both starter and responder paths work

2. **Integration Testing**
   - Run `test_round_recreations_with_resolution.py`
   - Verify no regression in existing behavior
   - Check constraint system still works

3. **Manual Testing**
   - Add verbose logging during games
   - Verify feature activates in real gameplay
   - Check for natural-looking bot behavior

### Phase 6: Rollback Plan

If issues arise:
1. **Quick Disable**: Add feature flag `ENABLE_OPENER_TIMING = False`
2. **Revert Changes**: Git revert the commit
3. **Hotfix**: Comment out the random checks, keep refactored structure

## Success Criteria

1. **Functionality**
   - Starters with opener-only plans randomly force singles 35-50% of the time
   - Responders with opener-only plans randomly play openers 35-50% of the time
   - No crashes or errors from the feature

2. **Testing**
   - Automated tests show correct probability distributions
   - No regression in existing bot behavior
   - Edge cases handled gracefully

3. **Code Quality**
   - No variable shadowing issues
   - Clear separation of starter/responder logic
   - Comprehensive debug logging

## Implementation Order

1. **First**: Create helper functions (non-breaking change)
2. **Second**: Remove broken code block (cleanup)
3. **Third**: Add starter logic (main feature)
4. **Fourth**: Add responder logic (complete feature)
5. **Fifth**: Update and run tests (verification)

## Risk Assessment

- **Low Risk**: Changes are localized to one function
- **Testable**: Can verify with existing test infrastructure
- **Reversible**: Easy to disable or revert if needed
- **No Breaking Changes**: Existing behavior preserved when feature doesn't activate