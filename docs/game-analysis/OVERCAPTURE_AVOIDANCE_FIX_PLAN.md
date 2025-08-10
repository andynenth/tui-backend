# Overcapture Avoidance System Fix Plan

## Current Issues

### 1. Activation Logic Problem
- **Current**: Only activates when `captured == declared` (line 84)
- **Issue**: This is too late! Bot should avoid overcapture BEFORE reaching target
- **Example**: Bot at 2/3 should avoid plays that would win 2+ piles

### 2. Design Philosophy Problem  
- **Current**: System tells bot what TO play (weakest pieces)
- **Should be**: System tells bot what NOT to play (avoid winning combinations)
- **Example**: Bot at 2/3 should avoid strong PAIRs, THREE_OF_A_KIND, etc.

### 3. Implementation Issues
- Doesn't consider how many piles each play type would capture
- Weak pieces might still form winning combinations (e.g., SOLDIER PAIRs)
- No consideration of opponent strength or likelihood of winning

## Game Rules Context

From RULES.md:
- Winner captures N piles where N = number of pieces played
- Scoring: Declared X, captured X = X + 5 points (perfect hit)
- Scoring: Declared X, captured ≠ X = 0 points (miss)

## Proposed Solution

### 1. New Activation Logic
```python
# Calculate risk of overcapture
piles_needed = context.my_declared - context.my_captured
current_hand_size = len(context.my_hand)

# Activate when at risk of overcapture
if piles_needed >= 0 and piles_needed < current_hand_size:
    # Bot needs to be careful about winning too many piles
```

### 2. Constraint-Based Approach
Instead of telling bot what to play, create constraints:

```python
def get_overcapture_constraints(context: TurnPlayContext) -> Dict:
    """
    Returns constraints to avoid overcapture.
    
    Example: If at 2/3 (need 1 pile), return:
    {
        'max_safe_pieces': 1,  # Can only safely win 1-piece turns
        'avoid_piece_counts': [2, 3, 4, 5, 6],  # Would cause overcapture
        'risky_plays': ['PAIR', 'THREE_OF_A_KIND', ...],  # Strong plays to avoid
    }
    """
```

### 3. Integration Points

#### A. Starter Strategy (`execute_starter_strategy`)
- Check constraints before choosing piece count
- If starter and constrained, prefer lower piece counts
- Avoid strong combinations that are likely to win

#### B. Responder Strategy (`execute_responder_strategy`) 
- When constrained, prefer weaker pieces
- But don't force specific plays - let normal strategy work within constraints

#### C. Strategic Plan Generation
- Mark certain combos as "risky" when near target
- Adjust urgency calculation to consider overcapture risk

### 4. Implementation Details

#### Phase 1: Add Constraint System
1. Create `get_overcapture_constraints()` function
2. Calculate safe piece counts based on piles needed
3. Identify risky play types based on field strength

#### Phase 2: Modify Decision Flow
1. In `choose_strategic_play()`:
   - Calculate constraints early
   - Pass constraints to strategy functions
   
2. In `execute_starter_strategy()`:
   - Check constraints when starter
   - Prefer safe piece counts
   - Avoid risky combinations
   
3. In `execute_responder_strategy()`:
   - Use constraints to filter disposal candidates
   - Prefer pieces that won't form strong combos

#### Phase 3: Remove Old System
1. Remove the current `avoid_overcapture_strategy()` function
2. Remove the `captured == declared` check
3. Integrate constraint checking throughout

### 5. Example Scenarios

#### Scenario 1: Bot at 2/3 as Starter
- Constraints: max_safe_pieces = 1
- Bot should play SINGLE pieces
- Avoid PAIR, THREE_OF_A_KIND, etc.

#### Scenario 2: Bot at 1/3 as Starter  
- Constraints: max_safe_pieces = 2
- Can safely play up to 2 pieces
- Should avoid 3+ piece combinations

#### Scenario 3: Bot at 0/1 as Responder
- Constraints: max_safe_pieces = 1
- When required to play 2+ pieces, choose weak non-matching pieces
- Minimize chance of winning

### 6. Benefits
1. **Proactive**: Prevents overcapture before it happens
2. **Flexible**: Works with existing strategies, just adds constraints
3. **Realistic**: Bots make intelligent decisions within constraints
4. **Game-compliant**: Still plays valid combinations when required

### 7. Testing Strategy
1. Test bot at various captured/declared ratios
2. Verify constraint calculation accuracy
3. Ensure bots avoid overcapture when possible
4. Check edge cases (e.g., must play to avoid forfeit)
5. Verify integration with urgency levels

### 8. Code Changes Summary
1. **New functions**:
   - `get_overcapture_constraints()`
   - `is_play_risky_for_overcapture()`
   - `filter_plays_by_constraints()`

2. **Modified functions**:
   - `choose_strategic_play()` - Add constraint calculation
   - `execute_starter_strategy()` - Apply constraints
   - `execute_responder_strategy()` - Consider constraints
   - `calculate_urgency()` - Factor in overcapture risk

3. **Removed**:
   - `avoid_overcapture_strategy()` function
   - Direct `captured == declared` check

This approach makes the overcapture avoidance system more intelligent and integrated with the overall AI strategy.