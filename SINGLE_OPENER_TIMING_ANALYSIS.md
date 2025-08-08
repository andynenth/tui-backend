# Single Opener Random Timing Feature Analysis

## Summary
The single opener random timing feature is **NOT WORKING** due to a logic error in the implementation.

## Root Cause
The feature checks `if context.required_piece_count == 1` to decide whether to randomly play openers. However, when a bot is the starter (which is when this feature should activate), `required_piece_count` is `None` because the starter hasn't chosen the count yet.

## Evidence from Debug Output

### Opener Timing Check Output
```
🎲 OPENER TIMING CHECK for Bot 3:
  - Required piece count: None     <-- This is the problem!
  - Has assigned openers: 1
  - Assigned openers: ['ADVISOR(12)']
  - Opener-only plan: True
  - Hand size: 8
```

The feature never activates because the condition `context.required_piece_count == 1` is never true when the bot is a starter.

## Code Issue Location
In `ai_turn_strategy.py` around line 922:
```python
if context.required_piece_count == 1 and plan.assigned_openers:
    # This condition is never true for starters!
```

## Additional Bug Found
There's also an `UnboundLocalError` at line 1079 where `random.sample()` is called but `random` is being shadowed by the local variable `random_value` used earlier.

## Why It Looked Like It Was Working
- Openers are still being played, but through the normal disposal logic, not the random timing feature
- Bots dispose of burden pieces (including openers when they're not part of the main plan)
- This creates the illusion that openers are being played, but without any random timing

## Impact
- The intended gameplay variety from random opener timing is missing
- Bots play more predictably than designed
- The 35%/40%/50% random chances are never applied

## Test Results
Running 20 iterations across multiple rounds showed:
- 0% of opener plays triggered by the random timing feature
- All opener plays were through burden disposal or other strategies
- The random values were never even generated because the condition check failed

## Recommendation
The fix requires checking for starter status and choosing piece count BEFORE the opener timing logic, or moving the opener timing logic to after the starter has chosen their piece count.