# Opener Random Timing Feature Analysis

## Understanding the Game Flow

From RULES.md:
- Each turn, a **starter** plays first and decides how many pieces everyone must play (1-6 pieces)
- The starter plays a valid set of that many pieces
- Other players must follow with the same number of pieces
- Winner captures piles equal to the number of pieces played

## What Are "Openers"?

- Pieces with point value >= 11 (ADVISOR: 11-12 points, GENERAL: 13-14 points)
- Strong pieces that can often win single-piece turns
- Valuable for controlling the game when played strategically

## How the Feature SHOULD Work

The single opener random timing feature is designed to add unpredictability to bot play:

1. **When**: Bot is the starter and must decide how many pieces to play
2. **Condition**: Bot has an "opener-only plan" (no viable combos, just strong single pieces)
3. **Decision**: Randomly decide to play 1 piece specifically to use an opener
4. **Probability**: 
   - Early game (6+ pieces): 35% chance
   - Mid game (4-5 pieces): 40% chance
   - Late game (<4 pieces): 50% chance
5. **Result**: Bot plays 1 piece (their strongest opener) instead of other strategies

## How It Currently Works (BROKEN)

Looking at the code flow in `execute_starter_strategy`:

```python
def execute_starter_strategy(...):
    # Step 1: Starter decides how many pieces to play
    if context.required_piece_count is None:  # We're setting the count
        # ... logic to determine 'required' ...
        required = 1  # or 2, 3, etc based on strategy
    else:
        required = context.required_piece_count
    
    # ... other logic ...
    
    # Step 2: Check for opener timing (BROKEN!)
    if context.required_piece_count == 1 and plan.assigned_openers:
        # This is NEVER true for starters because
        # context.required_piece_count is still None!
        if opener_only_plan:
            # Random timing logic that never executes
```

## The Critical Bug

The feature checks `context.required_piece_count == 1` but:
- For starters, `context.required_piece_count` is always `None` 
- The starter just decided to play `required` pieces (local variable)
- The check should be `if required == 1` not `if context.required_piece_count == 1`

## Why This Matters

Without this feature working:
1. **Predictable Play**: Bots always use the same decision logic for choosing piece counts
2. **Lost Variety**: The intended 35-50% random opener plays never happen
3. **Strategic Monotony**: Openers are only played through burden disposal, not strategic timing
4. **Gameplay Impact**: Less dynamic and interesting bot behavior

## Evidence from Debug Logs

```
🎲 OPENER TIMING CHECK for Bot 3:
  - Required piece count: None     <-- Always None for starters!
  - Has assigned openers: 1
  - Assigned openers: ['ADVISOR(12)']
  - Opener-only plan: True
  - Hand size: 8
```

The feature never activates because the condition fails before the random check.

## Test Results

Running 20 iterations showed:
- **0%** of single opener plays triggered by random timing
- **100%** of opener plays were through other mechanisms (burden disposal, etc.)
- No random values were ever generated or checked

## How It Should Be Fixed

The logic should be:
1. Starter determines how many pieces to play (sets `required`)
2. If `required == 1` AND bot has opener-only plan
3. Skip that and go to random timing check
4. If starter doesn't already have a piece count decided:
   - Check random chance (35-50%)
   - If successful, set `required = 1` and play opener
   - Otherwise continue with normal logic

The key is checking the LOCAL `required` variable, not the context's `required_piece_count`.