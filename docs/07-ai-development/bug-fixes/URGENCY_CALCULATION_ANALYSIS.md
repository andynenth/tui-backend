# Urgency Calculation Analysis

## Current Urgency Logic

The urgency calculation uses a "room" concept:
```
room = remaining_turns - max_opponent_target_remaining
urgency = "critical" if room < my_target_remaining else "low"
```

### Example Calculation

Scenario:
- Bot has 8 pieces (8 remaining turns)
- Bot declared 2, captured 1 (needs 1 more)
- Opponent A: declared 3, captured 1 (needs 2)
- Opponent B: declared 2, captured 0 (needs 2)
- Opponent C: declared 1, captured 0 (needs 1)

Calculation:
- remaining_turns = 8
- max_opponent_remaining = 2 (Opponents A and B)
- room = 8 - 2 = 6
- my_target_remaining = 1
- Since room (6) >= my_target_remaining (1) → urgency = "low"

### Issues with Current Logic

1. **Only Two Levels**: "low" or "critical" (no medium/high)
2. **Ignores Turn Number**: Early game vs late game treated the same
3. **Oversimplified**: Doesn't consider:
   - Current turn winner dynamics
   - Piece quality in hand
   - Competition intensity

### Impact on Behavior

When urgency = "critical":
- Lines 857-858: Forces bot to play strongest valid combo
- No strategic holding back
- May waste good pieces early

When urgency = "low":
- Allows random opener play
- More flexible strategy

### Why This Contributes to Over-Declaration

The urgency calculation affects play style, not declaration. However:
1. If urgency is often "critical", bots burn good pieces
2. This makes it harder to achieve declared targets
3. The declaration logic doesn't account for this burn rate

### Example of Problem

Turn 1: Bot has room, plays randomly
Turn 2: Suddenly critical, must play best combo
Turn 3: Still critical, burns another good combo
Turn 4+: Out of good pieces, can't win needed piles

### Recommendations

1. **Add Medium/High Levels**: More nuanced urgency
2. **Consider Turn Number**: Early turns less urgent
3. **Adjust for Piece Quality**: Factor in hand strength
4. **Link to Declaration**: Make declaration consider expected urgency