# AI Turn Play Decision Process - Detailed Analysis

## Overview

The AI turn play system in Liap Tui is a sophisticated multi-layered decision engine that strategically manages piece playing during the Turn Phase. The system incorporates target achievement strategies, overcapture avoidance, role-based planning, and adaptive play selection.

## Architecture Overview

### Key Components

1. **`ai_turn_strategy.py`** - Main strategic decision engine
2. **`TurnPlayContext`** - Data structure containing all game state information
3. **`StrategicPlan`** - Planning system for achieving target piles
4. **`OvercaptureConstraints`** - Risk management system
5. **`bot_manager.py`** - Bot action orchestration
6. **State Machine Integration** - Enterprise architecture for automatic broadcasting

## Decision Flow Step-by-Step

### Phase 1: Bot Triggering

When it's a bot's turn to play, the process begins in `bot_manager.py`:

1. **Phase Change Detection** (`_handle_enterprise_phase_change`)
   - State machine broadcasts phase_change event with turn data
   - Bot manager detects current player from phase_data
   - Checks if current player is a bot

2. **Sequential Processing** (`_handle_turn_play_phase`)
   - Processes bot plays sequentially (like declarations)
   - Adds 0.5-1.5 second delay for realism
   - Calls `_bot_play()` for the bot

### Phase 2: Context Building

The `_bot_play()` method creates a comprehensive context:

```python
context = TurnPlayContext(
    my_name=bot.name,
    my_hand=bot.hand,
    my_captured=bot_captured,      # Piles already won
    my_declared=bot.declared,      # Target pile count
    required_piece_count=required_piece_count,  # Set by starter
    turn_number=turn_number,
    pieces_per_player=len(bot.hand),
    am_i_starter=(current_turn_starter == bot.name),
    current_plays=[],              # ⚠️ NOT IMPLEMENTED - Always empty
    revealed_pieces=[],            # ⚠️ NOT IMPLEMENTED - Always empty
    player_states=player_states    # All players' captured/declared
)
```

### Phase 3: Strategic Decision (`choose_strategic_play`)

The main decision function performs these steps:

#### 3.1 Overcapture Risk Assessment

```python
constraints = get_overcapture_constraints(context)
```

This calculates:
- **`max_safe_pieces`**: Maximum pieces that can be played without overcapture risk
- **`avoid_piece_counts`**: Specific counts that would likely cause overcapture
- **`risky_play_types`**: Combinations likely to win and cause overcapture
- **`risk_level`**: "none", "low", "medium", "high", or "at_target"

Example scenarios:
- If bot has captured 1/3 piles → avoid playing 3+ piece combos
- If bot has captured 4/5 piles → avoid playing 2+ piece combos  
- If bot is at target (2/2) → play only singles with weak pieces

#### 3.2 Strategic Plan Generation

```python
plan = generate_strategic_plan(hand, context)
```

This creates a plan with:
- **`target_remaining`**: Piles still needed (declared - captured)
- **`valid_combos`**: All valid plays from current hand
- **`opener_pieces`**: High-value pieces (≥11 points)
- **`urgency_level`**: Based on turns remaining vs piles needed

Urgency calculation:
- **"critical"**: Need to win every remaining turn
- **"high"**: Need to win 75%+ of remaining turns
- **"medium"**: Need to win 50%+ of remaining turns
- **"low"**: Have cushion for strategic play
- **"none"**: Already at/above target

#### 3.3 Hand Evaluation and Role Assignment

```python
hand_eval = evaluate_hand(hand, context, plan)
```

This calls `form_execution_plan()` which categorizes pieces into roles:

1. **Assigned Openers**: High-value pieces (≥11 points) reserved for winning
   - **Selection**: `[p for p in hand if p.point >= 11]`
   - **Sorting**: By point value descending (strongest first)
   - **Assignment based on target_remaining**:
     - 0 piles needed: 0 openers (already at target)
     - 1 pile needed: 1 opener (for control)
     - 2 piles needed: up to 2 openers
     - 3 piles needed: 1-2 openers (leave room for combos)
     - 4+ piles needed: up to 2 openers
   - **Starter exception**: May remove openers if they overlap with preferred combos

2. **Assigned Combos**: Valid combinations that can win turns
   - **First filter**: All valid combos from `find_all_valid_combos()`
   - **Viability check**: `is_combo_viable(combo_type, pieces, field_strength)`
     - THREE_OF_A_KIND and above: Always viable
     - PAIR viability by field strength:
       - Weak field: ≥10 points (HORSE pair)
       - Normal field: ≥14 points (CHARIOT pair)
       - Strong field: ≥18 points (ELEPHANT pair)
   - **Overlap handling**: Skip combos that use already assigned opener pieces
   - **Starter preference**: May replace openers with strong combos

3. **Reserve Pieces**: 1-2 weakest pieces (≤4 points) for overcapture avoidance
   - **Selection**: `[p for p in hand if p.point <= 4 and p not in pieces_in_plan]`
   - **Sorting**: By point value ascending (weakest first)
   - **Limit**: Maximum 2 pieces

4. **Burden Pieces**: Everything not assigned to other roles
   - **Selection**: `[p for p in hand if p not in pieces_in_plan]`
   - **Sorting**: By point value descending (dispose high value first)
   - **Purpose**: Disposed of when not leading to minimize win chances

Example plan formation:
```
Target: 3 piles needed
Hand: [GENERAL_RED(14), ADVISOR_BLACK(12), HORSE_RED(5), HORSE_BLACK(5), 
       CANNON_RED(3), CANNON_BLACK(3), SOLDIER_RED(1), SOLDIER_BLACK(1)]

Plan:
- Openers: [GENERAL_RED, ADVISOR_BLACK] (2 pieces for 2 potential wins)
- Combos: [PAIR of HORSEs] (1 combo for 1 potential win)  
- Reserve: [SOLDIER_RED, SOLDIER_BLACK] (weak pieces)
- Burden: [CANNON_RED, CANNON_BLACK] (not in winning plan)
```

### Phase 4: Strategy Execution

Based on role (starter vs responder) and constraints:

#### 4.1 Starter Strategy (`execute_starter_strategy`)

When leading the turn, bot must choose piece count:

1. **Random Opener Timing** (35-50% chance based on hand size)
   - If bot has opener-only plan, may randomly play singles
   - Simulates human unpredictability

2. **Constraint-Based Selection**
   - If at/above target → play 1 piece (minimize wins)
   - If overcapture risk → play max_safe_pieces
   - Otherwise → prefer playing assigned combos

3. **Combo Selection Priority**
   - Exact match for required pieces
   - Best ranked combo that fits (by hierarchy then value)
   - Dispose burden pieces if low urgency

4. **Fallback Logic**
   - Try any available combo before random selection
   - Select from disposable pieces (burden → reserve → other)
   - Validate plays for starter requirements

#### 4.2 Responder Strategy (`execute_responder_strategy`)

When following, must match starter's piece count:

1. **Random Opener Timing** (only when required = 1)
   - Checks if bot has opener-only plan (no viable combos)
   - Uses same probability as starters (35-50% based on hand size)
   - If triggered, plays strongest opener immediately
   - This happens BEFORE all other strategies

2. **Critical Urgency Override**
   - If must win remaining turns → play strongest valid combo
   - Searches all possible combinations of required size
   - Ignores disposal priority in critical situations

3. **Disposal Priority System**
   ```
   Priority 1: Burden pieces (highest value first)
   Priority 2: Reserve pieces (if needed)
   Priority 3: Openers (last resort only!)
   Priority 4: Combo pieces (emergency only)
   ```

4. **Overcapture Risk Handling**
   - High risk + required count risky → select non-matching pieces
   - Avoids accidental strong combinations
   - Minimizes total play value

### Phase 5: Aggressive Capture (Plan Broken)

When the strategic plan becomes impossible:

```python
if plan.plan_impossible and plan.urgency_level != "none":
    result = execute_aggressive_capture(hand, required_count, constraints)
```

This mode:
- Finds strongest possible combination of required size
- Respects overcapture constraints if risk is high
- Falls back to weakest combo if no safe options
- Maximizes win probability when plan fails

### Phase 6: Validation and Execution

The chosen pieces undergo validation:

1. **Result Validation** (`validate_play_result`)
   - Checks all pieces exist in hand
   - Verifies piece count matches requirement
   - Validates starter plays are legal combinations

2. **Bot Manager Validation** (`_bot_play`)
   - Double-checks AI output validity
   - Adjusts piece count if needed
   - Removes invalid pieces and replaces

3. **State Machine Execution**
   - Creates GameAction with selected pieces
   - State machine validates and processes
   - Automatic broadcasting via enterprise architecture

## Special Features

### 1. Overcapture Avoidance System

The AI actively avoids winning too many piles:

```python
# Example: Bot has captured 4/5 piles
constraints = OvercaptureConstraints(
    max_safe_pieces=1,        # Only singles safe
    avoid_piece_counts=[2,3,4,5,6],  # All multis risky
    risky_play_types=["PAIR", "THREE_OF_A_KIND", ...],
    risk_level="high"
)
```

### 2. Field Strength Assessment

Evaluates opponent declarations to gauge competition:
- **Weak field** (avg ≤ 1.5): Low declarations, easier to win
- **Normal field** (avg 1.5-2.5): Moderate competition
- **Strong field** (avg > 2.5): High declarations, harder to win

Affects combo viability:
- Weak field: HORSE pairs (10+ points) viable
- Normal field: CHARIOT pairs (14+ points) viable  
- Strong field: ELEPHANT pairs (18+ points) viable

### 3. Random Timing System

Adds human-like unpredictability:
```python
def should_randomly_play_opener(hand_size: int) -> bool:
    if hand_size >= 6:
        threshold = 0.35  # 35% early game
    elif hand_size >= 4:
        threshold = 0.40  # 40% mid game
    else:
        threshold = 0.50  # 50% late game
    return random.random() < threshold
```

### 4. Starter Preference System

Starters may prefer strong combos over individual openers:
```python
STARTER_PREFERRED_COMBOS = [
    "THREE_OF_A_KIND",
    "STRAIGHT", 
    "FOUR_OF_A_KIND",
    "EXTENDED_STRAIGHT",
    "FIVE_OF_A_KIND",
    "DOUBLE_STRAIGHT"
]
```

Plus high-value pairs (ELEPHANT pairs = 18+ points).

## Debug Output Examples

### Example 1: Bot at Target
```
🎯 Strategic AI Decision Process for Bot_2
  📊 Status: captured=2, declared=2
  🎮 Turn 4, required pieces=2
  🃏 Hand size: 4 pieces
  👥 Starter: NO

⚠️ OVERCAPTURE RISK DETECTED - Level: at_target
  Piles needed: 0
  Max safe pieces: 1
  Avoid piece counts: [2, 3, 4, 5, 6]

🎯 Bot_2 at/above target - minimizing wins
🗑️ DISPOSING 1 burden + 1 reserve: [ELEPHANT_BLACK(9), SOLDIER_RED(1)]
```

### Example 2: Critical Urgency
```
🎯 Strategic AI Decision Process for Bot_3
  📊 Status: captured=1, declared=4
  🎮 Turn 7, required pieces=3
  🃏 Hand size: 3 pieces
  👥 Starter: YES

📈 Bot_3 needs 3 more pile(s) - using strategic play
📊 Bot_3 - Urgency: critical, Target remaining: 3

💥 CRITICAL URGENCY - must win turns!
⚡ Playing strongest combo (value=21): [ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED]
```

### Example 3: Strategic Disposal
```
🎯 RESPONDER STRATEGY for Bot_1 (Turn 3)
  Current hand: [GENERAL_BLACK(14), HORSE_RED(5), CANNON_RED(3), SOLDIER_BLACK(1)]
  Required pieces: 2
  Urgency: medium, Target remaining: 2

🗑️ DISPOSAL PRIORITY:
  1. Burden pieces: [CANNON_RED(3)]
  2. Reserve pieces: [SOLDIER_BLACK(1)]
  3. Openers (last resort): [GENERAL_BLACK(14)]

🗑️ DISPOSING 1 burden + 1 reserve: [CANNON_RED(3), SOLDIER_BLACK(1)]
Total value: 4 pts
```

### Example 4: Responder Random Opener Timing
```
🎯 RESPONDER STRATEGY for Bot_3 (Turn 5)
  Current hand: [GENERAL_RED(14), ADVISOR_RED(12), CANNON_BLACK(3), SOLDIER_RED(1)]
  Required pieces: 1
  Urgency: low, Target remaining: 1
  Overcapture risk: none

  🎲 Bot_3 (RESPONDER) randomly playing opener due to timing
     - Hand size: 4, Probability was 40%
     - Opener-only plan with 2 openers
  🎯 Playing opener: GENERAL_RED(14)
```

## Summary

The AI turn play system is a sophisticated decision engine that:

1. **Strategically plans** piece usage to achieve declared targets
2. **Actively avoids** overcapture through constraint analysis
3. **Categorizes pieces** into roles (openers, combos, reserve, burden)
4. **Adapts strategy** based on position (starter vs responder)
5. **Handles urgency** with aggressive capture when needed
6. **Adds unpredictability** through random timing
7. **Validates thoroughly** to ensure legal plays

The system balances optimal play with risk management, creating challenging and realistic bot opponents that play strategically rather than simply maximizing each turn's value.