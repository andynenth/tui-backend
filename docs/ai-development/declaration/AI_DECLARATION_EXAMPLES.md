# AI Declaration Examples & Patterns

This document contains 18 detailed examples showing how declaration strategy works in practice, demonstrating how the same hand can declare differently based on context.

## Example 1: Strong Hand with Opener (As Starter)
```
Hand: [ADVISOR_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]
Position: STARTER (first player)

Hand Analysis:
- ADVISOR_RED = opener (12 points) → 1 pile
- STRAIGHT (CHARIOT-HORSE-CANNON BLACK) → 3 piles

Final Declaration: 4 piles (no position bonuses)
```

## Example 2: Same Hand, Weak Field
```
Hand: [ADVISOR_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]
Position: Player 3 (not starter)
Previous declarations: [0, 1]

Hand Analysis:
- ADVISOR_RED = opener (12 points) → 1 pile
- STRAIGHT (CHARIOT-HORSE-CANNON BLACK) → 3 piles

Final Declaration: 4 piles (AI ignores weak field, only evaluates hand)
```

## Example 3: Same Hand, Strong Field
```
Hand: [ADVISOR_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]
Position: Player 3 (not starter)
Previous declarations: [5, 4]

Hand Analysis:
- ADVISOR_RED = opener (12 points) → 1 pile
- STRAIGHT (CHARIOT-HORSE-CANNON BLACK) → 3 piles

Final Declaration: 4 piles (AI ignores field strength, only evaluates hand)
```

## Example 4: Good Combos, No Opener (Starter)
```
Hand: [CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]
Position: STARTER (first player)
Previous declarations: None (goes first)

Hand Analysis:
- No opener (ELEPHANT only 9 points)
- STRAIGHT (CHARIOT-HORSE-CANNON RED) → 3 piles
- As starter: Guaranteed to play STRAIGHT first

Final Declaration: 3 piles (exactly what STRAIGHT gives)
```

## Example 5: Good Combos, No Opener (Not Starter, Weak Field)
```
Hand: [CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]
Position: Player 3 (not starter)
Previous declarations: [0, 1]

Hand Analysis:
- No opener (ELEPHANT only 9 points)
- STRAIGHT available but weak (18 total points)
- Previous [0, 1] = opponents have NO combos
- 0% chance for STRAIGHT opportunity (opponents play singles only)

Final Declaration: 1 pile (maybe win with ELEPHANT or CHARIOT)
```

## Example 6: Good Combos, No Opener (Not Starter, Strong Field)
```
Hand: [CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]
Position: Player 3 (not starter)
Previous declarations: [4, 5]

Hand Analysis:
- No opener (ELEPHANT only 9 points)
- STRAIGHT available but weak (18 points)
- Previous total: 4 + 5 = 9 (already exceeds 8!)
- Pile room: 8 - 9 = -1 → effectively 0
- IMPOSSIBLE to win any piles (no room)

Final Declaration: 0 piles (pile room constraint)
```

## Example 7: Multiple High Cards (Starter)
```
Hand: [GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]
Position: STARTER (first player)
Previous declarations: None (goes first)

Hand Analysis:
- GENERAL_RED (14 points) → Guaranteed 1 pile
- ADVISOR_BLACK (11 points) → Very likely 1 pile
- ELEPHANT_RED (10 points) → Possible 1 pile
- No combinations, only singles
- Lower pieces unlikely to win

Final Declaration: 2-3 piles (2 from openers, maybe 1 from ELEPHANT)
```

## Example 8: Multiple High Cards (Not Starter, Mixed Field)
```
Hand: [GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]
Position: Player 4 (last, not starter)
Previous declarations: [2, 1, 3]

Hand Analysis:
- GENERAL_RED (14 points) → 1 pile
- ADVISOR_BLACK (11 points) → 1 pile
- Realistically can win 2 piles
- Pile room: 8 - 6 = 2 (matches capability)
- BUT cannot declare 2 (would make total = 8)
- Valid options: 0, 1, or 3+

Final Declaration: 1 pile (conservative, since can't declare true expectation of 2)
```

## Example 9: Weak Hand (Starter)
```
Hand: [ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]
Position: STARTER (first player)
Previous declarations: None (goes first)

Hand Analysis:
- No openers (ELEPHANT 10/9 points not reliable)
- No combos
- As starter, might win 1 turn with ELEPHANT_RED (10)
- Other pieces too weak

Final Declaration: 1 pile (starter advantage doesn't help weak singles)
```

## Example 10: Weak Hand (Not Starter, Weak Field)
```
Hand: [ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]
Position: Player 4 (last, not starter)
Previous declarations: [0, 0, 1]

Hand Analysis:
- No openers (normally)
- No combos
- Declarations [0, 0, 1] = extremely weak field
- In weak field, ELEPHANTs (10/9) become viable
- Even CHARIOTs might win

Final Declaration: 2 piles (medium pieces can win vs very weak opponents)
```

## Example 11: Strong Combos, No Opener (Starter)
```
Hand: [SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]
Position: STARTER (first player)
Previous declarations: None (goes first)

Hand Analysis:
- No opener (highest is CHARIOT 7 points)
- FIVE_OF_A_KIND RED SOLDIERs → 5 piles
- STRAIGHT BLACK → 3 piles
- As starter, can play both!
- Total: 8 piles

Final Declaration: 8 piles (can achieve maximum with both combos)
```

## Example 12: Strong Combos, No Opener (Not Starter, Strong Field)
```
Hand: [SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]
Position: Player 2 (not starter)
Previous declarations: [5] (very strong starter)

Hand Analysis:
- No opener (highest is CHARIOT 7 points)
- Amazing combos but no control
- Without starter/opener: base 0 piles

Position Adjustment:
- Not starter: No bonus
- Strong starter (5): -1 adjustment (but floor at 0)
- Unlikely to play any combos

Final Declaration: 0 piles (great hand, wrong position)
```

## Example 13: Strategic Last Player
```
Hand: [ADVISOR_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_RED]
Position: Player 4 (last, not starter)
Previous declarations: [3, 2, 1]

Hand Analysis:
- ADVISOR_RED (12 points) → 1 pile
- THREE_OF_A_KIND BLACK SOLDIERs → 3 piles
- Pile room: 8 - 6 = 2 (constraint!)
- Can't play both (need 4, only 2 available)
- Must choose opener OR combo
- Cannot declare 2 (would make total = 8)

Final Declaration: 1 pile (ADVISOR only, pile room limits combo)
```

## Example 14: Mid-Strength Opener with Combo (Not Starter, Mid-Field)
```
Hand: [ADVISOR_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_RED, HORSE_BLACK, CANNON_BLACK, ELEPHANT_BLACK]
Position: Player 2 (not starter)
Previous declarations: [3]

Hand Analysis:
- ADVISOR_BLACK (11 points) = opener → 1 pile
- THREE_OF_A_KIND RED SOLDIERs → 3 piles IF opportunity
- Previous [3] = opponent likely has combos
- Problem: Opponent will play their combo, then control with singles
- Very unlikely to get THREE_OF_A_KIND opportunity

Final Declaration: 1 pile (just ADVISOR, THREE_OF_A_KIND unlikely without starter)
```

## Example 15: Double THREE_OF_A_KIND (Starter)
```
Hand: [SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_BLACK]
Position: STARTER (first player)
Previous declarations: None (goes first)

Hand Analysis:
- No opener (highest is CHARIOT 8 points)
- THREE_OF_A_KIND RED → 3 piles
- THREE_OF_A_KIND BLACK → 3 piles
- As starter, can play both!
- Total: 6 piles

Final Declaration: 6 piles (guaranteed both THREE_OF_A_KINDs)
```

## Example 16: Strong Singles, No Combos (Limited by Pile Room)
```
Hand: [GENERAL_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED]
Position: Player 3 (not starter)
Previous declarations: [4, 3]

Hand Analysis:
- GENERAL_BLACK (13 points) = strong opener → 1 pile
- No combos, just singles
- Previous [4, 3] = strong field, total 7
- Pile room: 8 - 7 = 1 only!
- Even with GENERAL, limited by pile room

Final Declaration: 1 pile (pile room constraint overrides hand strength)
```

## Example 17: FOUR_OF_A_KIND with Strongest Opener
```
Hand: [GENERAL_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED]
Position: Player 3 (not starter)
Previous declarations: [1, 0]

Hand Analysis:
- GENERAL_RED (14 points) = STRONGEST piece, guarantees control → 1 pile
- FOUR_OF_A_KIND BLACK SOLDIERs → 4 piles
- Previous [1, 0] = very weak field, no one can beat GENERAL_RED
- Strategy: Win with GENERAL_RED, gain control, then play FOUR_OF_A_KIND
- Total: 1 + 4 = 5 piles

Final Declaration: 5 piles (GENERAL_RED enables combo play like starter)
```

## Example 18: Last Player, Perfect Pile Room Match
```
Hand: [ADVISOR_RED, ADVISOR_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_BLACK]
Position: Player 4 (last, not starter)
Previous declarations: [2, 2, 1]

Hand Analysis:
- Two openers: ADVISOR_RED (12), ADVISOR_BLACK (11) → 2 piles
- STRAIGHT RED available → 3 piles
- Total previous: 5, pile room = 3
- Cannot declare 3 (would make total = 8)
- Must choose openers (2) or hope for STRAIGHT opportunity

Final Declaration: 2 piles (play both ADVISORs, fits constraints)
```

## Pattern Recognition Guide

### Key Patterns from Examples

1. **Pile Room Dominates** (Examples 6, 13, 16)
   - Even great hands must respect pile room limits
   - Pile room = 8 - sum(previous_declarations)

2. **Low Declarations = No Combos** (Examples 2, 5, 10)
   - [0,1] opponents have terrible hands
   - They won't create combo opportunities
   - Your combos become unplayable without control

3. **GENERAL_RED Transforms Hands** (Example 17)
   - Weak field + GENERAL_RED = play like starter
   - Can enable 5+ pile declarations

4. **Position Gap is Massive** (Examples 11 vs 12, 15)
   - Starter with combos: 6-8 piles
   - Non-starter with same combos: 0-1 piles

5. **Last Player Constraints** (Examples 8, 13, 18)
   - Cannot make total = 8
   - Forces sub-optimal declarations

### Quick Reference Scenarios

**Scenario A: Great Hand, No Room**
- Previous: [5, 3] → Room = 0
- Declaration: 0 (regardless of hand)

**Scenario B: Combos, No Control**
- Not starter, no opener
- Previous: [0, 1] (no combo opportunity)
- Declaration: 0-1

**Scenario C: GENERAL_RED Magic**
- GENERAL_RED + combos
- Weak field [1, 0]
- Declaration: 5+ piles

**Scenario D: Last Player Dilemma**
- Want to declare 2
- Previous total = 6
- Forced to declare 1 or 3+