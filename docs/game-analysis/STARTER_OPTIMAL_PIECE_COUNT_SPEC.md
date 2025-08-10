# Starter Optimal Piece Count Function Specification

## Function Signature
```python
def get_optimal_piece_count_for_starter(
    plan: StrategicPlan,
    constraints: OvercaptureConstraints,
    context: TurnPlayContext,
    hand: List[Piece]
) -> Tuple[int, Optional[List[Piece]]]:
    """
    Returns: (piece_count, combo_to_play)
    - piece_count: Optimal number of pieces to play
    - combo_to_play: Specific combo if one is selected, None otherwise
    """
```

## Decision Logic Flow

### 1. Already At/Above Target
```python
if context.my_declared - context.my_captured <= 0:
    return (1, None)  # Minimize to avoid overcapture
```

### 2. Critical Urgency Override
```python
if plan.urgency_level == "critical" and plan.target_remaining > 0:
    # Must win every turn - find strongest combo
    best_combo = find_strongest_viable_combo(plan.valid_combos, constraints)
    if best_combo:
        return (len(best_combo), best_combo)
```

### 3. Check Assigned Combos (Primary Strategy)
```python
if plan.assigned_combos:
    # Sort by strategic value (not just points)
    for combo_type, pieces in plan.assigned_combos:
        if all(p in hand for p in pieces):
            if not is_play_risky_for_overcapture(pieces, constraints):
                return (len(pieces), pieces)
```

### 4. No Viable Combos - Strategic Count Selection
```python
# Based on urgency and target
if plan.urgency_level == "high":
    # Try to maximize winning chances
    if has_openers >= 2:
        return (2, None)  # Play 2 for better odds
    else:
        return (1, None)  # Play strongest single
        
elif plan.urgency_level == "medium":
    # Balanced approach
    if plan.target_remaining >= 3 and len(hand) >= 4:
        return (2, None)  # Can afford 2-piece plays
    else:
        return (1, None)
        
else:  # "low" urgency
    # Conservative, save resources
    return (1, None)
```

### 5. Overcapture Constraint Override
```python
# Always respect max_safe_pieces
if constraints.risk_level != "none":
    piece_count = min(piece_count, constraints.max_safe_pieces)
```

## Examples

### Example 1: Critical Urgency with Combos
```
Input:
- urgency: "critical"
- target_remaining: 2
- assigned_combos: [("PAIR", [HORSE_RED, HORSE_BLACK])]
- constraints: risk_level="none"

Output: (2, [HORSE_RED, HORSE_BLACK])
Reason: Must win turns, have viable combo
```

### Example 2: Medium Urgency, No Combos
```
Input:
- urgency: "medium"
- target_remaining: 3
- assigned_combos: []
- hand_size: 5
- has 2 openers

Output: (2, None)
Reason: Need wins, have resources, play 2 for better odds
```

### Example 3: At Target
```
Input:
- my_captured: 3
- my_declared: 3
- Any other values

Output: (1, None)
Reason: Already at target, minimize
```

### Example 4: High Overcapture Risk
```
Input:
- urgency: "high"
- constraints: max_safe_pieces=1, risk_level="high"
- assigned_combos: [("THREE_OF_A_KIND", [...])]

Output: (1, None)
Reason: Constraints override combo strategy
```

## Integration with Existing Code

### Replace This Section (Lines 953-984):
```python
if context.required_piece_count is None:  # We're setting the count
    # OLD: Random timing and default logic
    # NEW: Call our function
    required, combo_to_play = get_optimal_piece_count_for_starter(
        plan, constraints, context, context.my_hand
    )
    
    if combo_to_play:
        return combo_to_play  # Direct return if combo selected
```

### Benefits Over Current Implementation

1. **Removes random timing** that ignores combos
2. **Prioritizes assigned combos** from planning phase
3. **Dynamic piece count** based on game state
4. **Cleaner logic flow** - one decision point
5. **Better urgency handling** - affects piece count choice

## Testing Scenarios

1. **Combo Available Tests**
   - With THREE_OF_A_KIND assigned
   - With PAIR assigned
   - With overlapping combos

2. **Urgency Tests**
   - Critical with/without combos
   - High/Medium/Low variations

3. **Constraint Tests**
   - Various overcapture risk levels
   - Max safe pieces limitations

4. **Edge Cases**
   - Empty hand
   - No assigned combos
   - All pieces in combos