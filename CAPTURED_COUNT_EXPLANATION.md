# Understanding captured_count Field

## The captured_count IS Working Correctly

The `captured_count` field in each play shows **how many piles the player has captured BEFORE making that play**, not after.

## Example from Room C5E645:

### Turn 1:
```
Bot 3 plays: captured_count = 0 ✅ (no one has won anything yet)
Bot 4 plays: captured_count = 0 ✅
Andy plays: captured_count = 0 ✅
Bot 2 plays: captured_count = 0 ✅
→ Bot 3 wins 3 piles
```

### Turn 2:
```
Bot 3 plays: captured_count = 3 ✅ (won 3 in turn 1)
Bot 4 plays: captured_count = 0 ✅ (hasn't won anything)
Andy plays: captured_count = 0 ✅
Bot 2 plays: captured_count = 0 ✅
→ Bot 3 wins 1 more pile (total: 4)
```

### Turn 3:
```
Bot 3 plays: captured_count = 4 ✅ (3+1 from turns 1&2)
Bot 4 plays: captured_count = 0 ✅
Andy plays: captured_count = 0 ✅
Bot 2 plays: captured_count = 0 ✅
→ Andy wins 1 pile
```

### Turn 4:
```
Andy plays: captured_count = 1 ✅ (won 1 in turn 3)
Bot 2 plays: captured_count = 0 ✅
Bot 3 plays: captured_count = 4 ✅ (unchanged)
Bot 4 plays: captured_count = 0 ✅
→ Andy wins 2 more piles (total: 3)
```

## Why Turn 1 Shows All Zeros

In Turn 1, everyone shows `captured_count = 0` because:
1. It's the first turn of the round
2. No one has captured any piles yet
3. The field shows captures BEFORE the play, not after

## Final Verification

Round 1 final captures match our tracking:
- Andy: 3 piles ✅
- Bot 2: 0 piles ✅
- Bot 3: 5 piles ✅
- Bot 4: 0 piles ✅

The `captured_count` field is working exactly as designed!