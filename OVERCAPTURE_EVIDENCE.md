# Overcapture Avoidance - Detailed Evidence

## Overview
The overcapture avoidance feature is supposed to make bots play weak pieces when they've reached their declared target. This is CRITICAL for competitive play but is completely broken.

## Expected Behavior
When `bot.captured_piles == bot.declared_piles`:
- Bot should activate `avoid_overcapture_strategy()`
- Play weakest possible pieces
- Avoid winning turns
- Log: "🛡️ {bot_name} is at target - activating overcapture avoidance"

## Actual Behavior Analysis

### Round-by-Round Evidence

#### Round 1
| Player | Declared | Turn 1 | Turn 2 | Turn 3 | Turn 4 | Turn 5 | Turn 6 | Final Captured | Result |
|--------|----------|--------|--------|--------|--------|--------|--------|----------------|--------|
| Bot 3 | 1 | Lost | Won (1) | Won (2) ⚠️ | Lost | Won (3) ⚠️ | Won (4) ⚠️ | 4 | -3 points |

**🚨 CRITICAL**: Bot 3 should have stopped trying after Turn 2!

#### Round 2
| Player | Declared | Captures by Turn | Final | Overcapture? |
|--------|----------|------------------|-------|--------------|
| Alexanderium | 3 | 0→0→1→2→2→3→4 | 4 | YES (+1) |
| Bot 2 | 0 | 0→0→0→0→0→0→0 | 0 | NO ✅ |
| Bot 3 | 1 | 0→1→1→1→1→2 | 2 | YES (+1) |
| Bot 4 | 2 | 0→0→1→1→2→2 | 2 | NO ✅ |

#### Round 3
| Player | Declared | Captures by Turn | Final | Overcapture? |
|--------|----------|------------------|-------|--------------|
| Alexanderium | 4 | 0→0→0→1→2→3→4→5 | 5 | YES (+1) |
| Bot 2 | 1 | 0→0→0→0→0→0→0 | 0 | Under (-1) |
| Bot 3 | 4 | 1→1→2→2→2→2 | 2 | Under (-2) |
| Bot 4 | 1 | 0→1→1→1→1→1 | 1 | NO ✅ |

### Detailed Turn Analysis - Round 1, Bot 3

**Initial State**: Declared = 1, Captured = 0

**Turn 2** (Captured = 1, At Target! 🎯)
- Current hand: [GENERAL_BLACK(13), remaining pieces...]
- **EXPECTED**: Play weakest piece (SOLDIER_BLACK)
- **ACTUAL**: Plays GENERAL_BLACK(13) and WINS
- Result: Now at Captured = 1 ✅

**Turn 3** (Captured = 1, SHOULD AVOID WINNING)
- Bot 3 plays: HORSE_RED(6)
- Others play: Bot 4: ELEPHANT_BLACK(9), Alex: CANNON_BLACK(3), Bot 2: ADVISOR_BLACK(11)
- **EXPECTED**: Should play weakest (SOLDIER_BLACK(1))
- **ACTUAL**: Plays HORSE_RED(6), but still wins!
- Result: Captured = 2 (OVERCAPTURE!) ⚠️

**Turn 5** (Captured = 2, STILL TRYING TO WIN)
- Bot 3 plays: ELEPHANT_BLACK(9)
- **EXPECTED**: Should forfeit with weak pieces
- **ACTUAL**: Plays strong piece and WINS AGAIN
- Result: Captured = 3 ⚠️⚠️

**Turn 6** (Captured = 3, CONTINUES WINNING)
- Bot 3 plays: ELEPHANT_RED(10)
- **ACTUAL**: Wins AGAIN!
- Final: Captured = 4 (300% overcapture!) ⚠️⚠️⚠️

## Code Investigation Points

1. **Check Trigger Condition**:
   ```python
   # In choose_strategic_play()
   if context.my_captured == context.my_declared:
       print(f"🛡️ {context.my_name} is at target...")
   ```
   - Is this condition evaluated with correct values?
   - Is captured count updated before this check?

2. **Check Strategy Activation**:
   ```python
   result = avoid_overcapture_strategy(hand, context)
   ```
   - Is this function being called?
   - What pieces is it returning?

3. **Check Turn Order**:
   - Is Bot 3 checking its captured count AFTER winning previous turn?
   - Timing issue: captured count might not be updated yet

## Hypothesis

Most likely issue: **Timing Problem**
- The captured pile count might be updated AFTER the bot makes its decision
- Bot checks "am I at target?" with stale data
- By the time it realizes it's at target, it's already overcaptured

## Test Case

```python
# Simulate Bot 3 scenario
bot_hand = [GENERAL_BLACK, HORSE_RED, ELEPHANT_BLACK, ELEPHANT_RED, SOLDIER_BLACK]
context = TurnPlayContext(
    my_name="Bot 3",
    my_captured=1,  # Already at target!
    my_declared=1,
    required_piece_count=1,
    am_i_starter=False
)

# This should return SOLDIER_BLACK(1)
result = choose_strategic_play(bot_hand, context)
assert result[0].name == "SOLDIER"
```

## Fix Priority: CRITICAL 🚨

This is the #1 issue to fix because:
1. It's a core strategic feature
2. It affects game balance significantly  
3. Players expect this to work
4. The fix should be straightforward once we identify the timing issue