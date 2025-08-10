# Liap Tui AI System - Detailed Technical Explanation

## Table of Contents
1. [Overview](#overview)
2. [Piece Hierarchy](#piece-hierarchy)
3. [AI Architecture](#ai-architecture)
4. [Declaration Phase AI (V2)](#declaration-phase-ai-v2)
5. [Turn Play AI](#turn-play-ai)
6. [Key Constants and Thresholds](#key-constants-and-thresholds)
7. [Helper Functions](#helper-functions)
8. [Decision Flow Diagrams](#decision-flow-diagrams)
9. [Strategic Considerations](#strategic-considerations)

## Overview

The Liap Tui AI system consists of two main components:
1. **Declaration AI**: Decides how many piles (0-8) to declare at the start of each round
2. **Turn Play AI**: Decides which pieces to play during each turn

The system uses a sophisticated V2 declaration strategy that differentiates between starters (first players) and non-starters, with special rules for piece combinations and pile room calculations.

## Piece Hierarchy

Pieces are ranked by point values, with RED pieces stronger than BLACK:

```
GENERAL_RED    = 14 points  ← Strongest
GENERAL_BLACK  = 13 points
ADVISOR_RED    = 12 points
ADVISOR_BLACK  = 11 points  ← Opener threshold (11+)
ELEPHANT_RED   = 10 points
ELEPHANT_BLACK = 9 points
CHARIOT_RED    = 8 points
CHARIOT_BLACK  = 7 points
HORSE_RED      = 6 points
HORSE_BLACK    = 5 points
CANNON_RED     = 4 points
CANNON_BLACK   = 3 points
SOLDIER_RED    = 2 points
SOLDIER_BLACK  = 1 point   ← Weakest
```

**Key Concept: "Openers"** - Pieces with 11+ points (ADVISOR_BLACK and above) that can reliably win turns and provide control.

## AI Architecture

### Entry Points

```python
# Main declaration function (public API)
choose_declare() → choose_declare_strategic_v2()

# Turn play function (with fallback)
choose_strategic_play_safe() → ai_turn_strategy.choose_strategic_play()
                             → choose_best_play() [fallback]
```

### Core Components

1. **Declaration System (V2)**
   - Separate logic for starters vs non-starters
   - Pile room calculation with special GENERAL_RED rule
   - Combo detection and evaluation
   - Forbidden value handling

2. **Turn Play System**
   - Strategic play via `ai_turn_strategy` module
   - Basic fallback that maximizes point value
   - Respects required piece count constraints

## Declaration Phase AI (V2)

### Starter Strategy (Position 0)

Starters have control and can play combos without needing openers:

```python
1. Find all strong combos iteratively (largest first)
   - DOUBLE_STRAIGHT (6 pieces)
   - FIVE_OF_A_KIND (5 pieces)
   - FOUR_OF_A_KIND (4 pieces)
   - EXTENDED_STRAIGHT (4-5 pieces)
   - STRAIGHT/THREE_OF_A_KIND (3 pieces)
   - Strong PAIR (2 pieces, >12 points total)

2. Calculate remaining pile room (8 - combo pieces)

3. Add individual strong pieces based on pile room
   - Use get_piece_threshold() to determine minimum value
   - Take highest value pieces first

4. Declaration = total pieces in play list
```

### Non-Starter Strategy (Positions 1-3)

Non-starters MUST have at least one opener for control:

```python
1. Calculate pile room using calculate_pile_room()
   - Normal: 8 - sum(previous_declarations)
   - With GENERAL_RED: 8 - starter_declaration_only
   - Handle overflow (sum > 8) by ignoring last declaration

2. Find ONE opener based on pile room threshold
   - Pile room 1: Need GENERAL_RED (>13 points)
   - Pile room 2: Need GENERAL (≥13 points)
   - Pile room 3-4: Need ADVISOR_RED+ (≥12 points)
   - Pile room 5+: Need ADVISOR_BLACK+ (≥11 points)

3. If no opener found → declare 0

4. Find strong combos from remaining pieces

5. Add additional individual strong pieces

6. Fit to pile room constraints (remove weakest combos if needed)

7. Declaration = total pieces in play list
```

### Pile Room Calculation

```python
def calculate_pile_room(previous_declarations, has_general_red):
    # Special GENERAL_RED rule
    if has_general_red and len(previous_declarations) >= 1:
        # Only count starter's declaration
        total = previous_declarations[0]
    else:
        total = sum(previous_declarations)
    
    # Handle overflow
    if total > 8:
        if has_general_red:
            total = 0  # Reset if starter declared >8
        else:
            # Ignore last declaration that caused overflow
            total = sum(previous_declarations[:-1])
    
    return max(0, 8 - total)
```

This creates strategic tension:
- Early players can't block others by declaring 8
- Later players must compete for remaining piles
- GENERAL_RED provides special advantage

### Forbidden Values

Last player (position 3) cannot make total declarations = 8:

```python
if position_in_order == 3:
    total_so_far = sum(previous_declarations)
    forbidden = 8 - total_so_far
    if 0 <= forbidden <= 8:
        forbidden_declares.add(forbidden)
```

The AI rebuilds its play list to avoid forbidden values using `rebuild_play_list_avoiding_forbidden()`.

## Turn Play AI

### Strategic Play (via ai_turn_strategy module)

The strategic turn play considers:
- Current turn context
- Required piece count
- What other players have played
- Remaining cards in hand
- Game state

### Basic Fallback Play

```python
def choose_best_play(hand, required_count):
    best_play = None
    best_score = -1
    
    # Check all valid combinations of required size
    for combo in combinations(hand, required_count):
        if is_valid_play(combo):
            total = sum(p.point for p in combo)
            if total > best_score:
                best_score = total
                best_play = combo
    
    # Fallback: discard lowest pieces if no valid play
    if not best_play:
        best_play = sorted(hand, key=lambda p: p.point)[:required_count]
    
    return best_play
```

This maximizes point value while respecting game rules.

## Key Constants and Thresholds

### Combo Types

```python
STRONG_COMBO_TYPES = {
    "THREE_OF_A_KIND",
    "STRAIGHT", 
    "FOUR_OF_A_KIND",
    "EXTENDED_STRAIGHT",
    "EXTENDED_STRAIGHT_5",
    "FIVE_OF_A_KIND",
    "DOUBLE_STRAIGHT"
}

STRONG_PAIR_THRESHOLD = 12  # Must exceed HORSE_RED pair value
```

### Opener Thresholds by Pile Room

| Pile Room | Threshold | Qualifying Pieces |
|-----------|-----------|-------------------|
| 1 | >13 | GENERAL_RED only |
| 2 | ≥13 | GENERAL_BLACK/RED |
| 3-4 | ≥12 | ADVISOR_RED+ |
| 5+ | ≥11 | ADVISOR_BLACK+ |

### Combo Hierarchy (for removal priority)

```python
combo_hierarchy = {
    "FIVE_OF_A_KIND": 6,      # Highest priority (keep)
    "FOUR_OF_A_KIND": 5,
    "EXTENDED_STRAIGHT": 4,
    "DOUBLE_STRAIGHT": 4,
    "STRAIGHT": 3,
    "THREE_OF_A_KIND": 2,
    "PAIR": 1                 # Lowest priority (remove first)
}
```

## Helper Functions

### find_all_valid_combos(hand)
Finds all valid piece combinations (1-6 pieces) in a hand using the game rules.

### is_strong_combo(combo_type, pieces)
Determines if a combo is "strong" (beats PAIR in hierarchy or is a high-value PAIR).

### find_and_select_strong_combos_iteratively(hand, play_list)
Iteratively finds strong combos, preferring larger combinations:
1. Find all valid combos
2. Filter for strong combos only
3. Sort by size (descending)
4. Select largest combo
5. Remove pieces from hand
6. Repeat until no more strong combos

### remove_pieces_from_hand(hand, pieces)
Safely removes specific pieces from a hand copy.

### fit_plays_to_pile_room(play_list, pile_room)
Adjusts play list to fit constraints by removing weakest/smallest combos first.

## Decision Flow Diagrams

### Declaration Flow - Starter

```
START
  ↓
Find all strong combos (iteratively, largest first)
  ↓
Calculate remaining pile room (8 - combo pieces)
  ↓
Add individual strong pieces (11+ points)
  ↓
Total pieces = declaration
  ↓
Handle forbidden values if needed
  ↓
END
```

### Declaration Flow - Non-Starter

```
START
  ↓
Calculate pile room (consider GENERAL_RED rule)
  ↓
Pile room > 0? → No → Declare 0 → END
  ↓ Yes
Find ONE opener (threshold based on pile room)
  ↓
Found opener? → No → Declare 0 → END
  ↓ Yes
Find strong combos from remaining pieces
  ↓
Add additional strong pieces
  ↓
Fit to pile room (remove excess combos)
  ↓
Total pieces = declaration
  ↓
Handle forbidden values if needed
  ↓
END
```

## Strategic Considerations

### For Starters
- Can play combos without openers
- Should maximize strong combos first
- Balance between combos and individual openers
- Can't declare more than 8 total

### For Non-Starters
- MUST have at least one opener (11+ points)
- Pile room limits options
- GENERAL_RED provides significant advantage
- Must compete for remaining piles

### Field Strength Assessment
The AI categorizes opponents based on average declarations:
- **Weak** (≤2.0 avg): Opponents have poor hands
- **Normal** (2.0-3.5 avg): Mixed hands
- **Strong** (≥3.5 avg): Opponents have excellent hands

### Key Strategic Elements

1. **Control**: Having openers (11+ point pieces) is crucial for non-starters
2. **Efficiency**: Larger combos provide more piles per "control" spent
3. **Competition**: Later players must fight for limited pile room
4. **Special Rules**: GENERAL_RED ignores non-starter declarations
5. **Forbidden Values**: Last player can't make total equal 8

The AI balances these factors to make optimal declarations that maximize expected pile captures while respecting game constraints.

## Example: AI Decision Making in Practice

### Example 1: Starter with Strong Combos

**Hand**: [GENERAL_RED(14), GENERAL_BLACK(13), ADVISOR_RED(12), HORSE_RED(6), HORSE_BLACK(5), CANNON_RED(4), SOLDIER_RED(2), SOLDIER_BLACK(1)]

**AI Process**:
1. Find strong combos iteratively:
   - STRAIGHT found: [SOLDIER_RED(2), CANNON_RED(4), HORSE_RED(6)] = 3 pieces
   - PAIR found: [GENERAL_RED(14), GENERAL_BLACK(13)] = 2 pieces (27 points > 12 threshold)
   
2. Choose largest combo first: STRAIGHT (3 pieces)
   - Add to play_list, remove from hand
   
3. Find more combos in remaining hand:
   - PAIR still available: [GENERAL_RED(14), GENERAL_BLACK(13)]
   - Add to play_list
   
4. Total so far: 3 + 2 = 5 pieces, room left = 3

5. Add individual strong pieces:
   - ADVISOR_RED(12) ≥ 11 → add to play_list
   - Room left = 2
   
6. **Final declaration: 6 piles**

### Example 2: Non-Starter with Limited Pile Room

**Position**: 2 (third player)
**Previous declarations**: [4, 3]
**Hand**: [ADVISOR_BLACK(11), ELEPHANT_RED(10), CHARIOT_RED(8), CHARIOT_BLACK(7), HORSE_RED(6), HORSE_BLACK(5), CANNON_RED(4), SOLDIER_RED(2)]

**AI Process**:
1. Calculate pile room: 8 - (4 + 3) = 1

2. Find opener for pile room 1:
   - Need > 13 points (only GENERAL_RED qualifies)
   - ADVISOR_BLACK(11) doesn't qualify
   - No valid opener found

3. **Final declaration: 0 piles** (forced conservative play)

### Example 3: Non-Starter with GENERAL_RED

**Position**: 3 (last player)
**Previous declarations**: [5, 2, 1]
**Hand**: [GENERAL_RED(14), CHARIOT_RED(8), CHARIOT_BLACK(7), HORSE_RED(6), HORSE_BLACK(5), CANNON_RED(4), SOLDIER_RED(2), SOLDIER_BLACK(1)]

**AI Process**:
1. Has GENERAL_RED → special rule applies
   - Only count starter's declaration: 5
   - Pile room = 8 - 5 = 3

2. Find opener:
   - GENERAL_RED(14) ≥ 12 (threshold for pile room 3) ✓
   - Add to play_list

3. Find combos from remaining pieces:
   - STRAIGHT found: [SOLDIER_BLACK(1), SOLDIER_RED(2), CANNON_RED(4)] = 3 pieces
   - But total would be 1 + 3 = 4 pieces > 3 pile room
   - Skip combo

4. Find additional strong pieces:
   - None qualify (need ≥12 for original pile room 3)

5. Check forbidden values:
   - As last player, cannot declare 8 - (5 + 2 + 1) = 0
   - Current declaration: 1 (not forbidden)

6. **Final declaration: 1 pile** (GENERAL_RED only)

### Example 4: Handling Forbidden Values

**Position**: 3 (last player)
**Previous declarations**: [3, 3, 1]
**Hand**: [ADVISOR_RED(12), ELEPHANT_RED(10), ELEPHANT_BLACK(9), HORSE_RED(6), HORSE_BLACK(5), SOLDIER_RED(2), SOLDIER_BLACK(1)]

**AI Process**:
1. Calculate pile room: 8 - (3 + 3 + 1) = 1

2. Find opener for pile room 1:
   - Need > 13 points
   - ADVISOR_RED(12) doesn't qualify
   - Would declare 0

3. Check forbidden values:
   - As last player, cannot declare 8 - (3 + 3 + 1) = 1
   - 0 is not forbidden

4. **Final declaration: 0 piles** (acceptable since 0 ≠ 1)


## Summary

The Liap Tui AI system uses a sophisticated two-phase approach:

### Declaration Phase (V2)
- **Starters**: Maximize strong combos first, then add individual openers
- **Non-starters**: Must secure at least one opener, then optimize within pile room constraints
- **Special rules**: GENERAL_RED advantage, forbidden sum of 8, pile room overflow handling

### Turn Play Phase
- Primary: Strategic module considering game context
- Fallback: Point maximization within valid plays
- Respects required piece counts

### Key Innovations

1. **Differentiated Strategies**: Starters vs non-starters have fundamentally different approaches
2. **Dynamic Thresholds**: Opener requirements adapt based on available pile room
3. **Iterative Combo Finding**: Prioritizes larger combinations for efficiency
4. **Overflow Handling**: Prevents early players from blocking later ones
5. **Forbidden Value Adaptation**: Rebuilds play strategy to avoid illegal declarations

### AI Strengths
- Strong mathematical optimization
- Adapts to game state and position
- Balances risk vs reward
- Handles edge cases gracefully

### AI Limitations
- Cannot bluff or use psychological tactics
- Doesn't track opponent patterns across rounds
- Limited look-ahead (single round focus)
- No learning from past games

The AI provides a challenging opponent that plays optimally within the game rules while maintaining fairness and preventing degenerate strategies.
