# Never-Win Combo Evidence Report

## Executive Summary

Analysis of AI game logs confirms that bots ARE playing never-win combos. These guaranteed-losing plays were found in actual gameplay.

## Evidence Found

### 1. All-BLACK Straights (15 points)

**Pattern**: CANNON_BLACK(3) + HORSE_BLACK(5) + CHARIOT_BLACK(7) = 15 points

**Examples from games**:
- Bot 3 plays: STRAIGHT (15 points) - ['HORSE', 'CHARIOT', 'CANNON']
- Bot 4 plays: STRAIGHT (15 points) - ['CANNON', 'CHARIOT', 'HORSE']
- Bot 3 plays: STRAIGHT (15 points) - ['CHARIOT', 'CANNON', 'HORSE']
- Bot 2 plays: STRAIGHT (15 points) - ['CHARIOT', 'HORSE', 'CANNON']

**Why it's never-win**: This is the minimum possible straight. Any other straight will have at least one RED piece (even points) making it 16+ points.

### 2. SOLDIER_BLACK Pairs (2 points)

**Pattern**: SOLDIER_BLACK(1) + SOLDIER_BLACK(1) = 2 points

**Examples from games**:
- Bot 4 plays: PAIR (2 points) - ['SOLDIER', 'SOLDIER']
- Bot 1 plays: PAIR (2 points) - ['SOLDIER', 'SOLDIER']
- Bot 2 plays: PAIR (2 points) - ['SOLDIER', 'SOLDIER']

**Why it's never-win**: This is the minimum possible pair. Any other pair will be at least 4 points (SOLDIER_RED pairs).

### 3. Three SOLDIER_BLACK (3 points)

**Pattern**: 3 × SOLDIER_BLACK(1) = 3 points

**Examples from games**:
- Bot 3 plays: THREE_OF_A_KIND (3 points) - ['SOLDIER', 'SOLDIER', 'SOLDIER']
- Bot 1 plays: THREE_OF_A_KIND (3 points) - ['SOLDIER', 'SOLDIER', 'SOLDIER']
- Bot 4 plays: THREE_OF_A_KIND (3 points) - ['SOLDIER', 'SOLDIER', 'SOLDIER']

**Why it's never-win**: This is the minimum possible three-of-a-kind. Any other three-of-a-kind will be at least 6 points.

## Frequency Analysis

From just 5 games sampled:
- **All-BLACK straights**: 5 occurrences
- **SOLDIER_BLACK pairs**: 6 occurrences
- **Three SOLDIER_BLACK**: 6 occurrences

This suggests these never-win plays happen regularly.

## Impact Assessment

### Wasted Pieces
- Each all-BLACK straight wastes 3 pieces
- Each SOLDIER pair wastes 2 pieces
- Each three-of-a-kind wastes 3 pieces

### Strategic Impact
When a bot plays a never-win combo:
1. Guaranteed to lose that turn
2. Cannot capture a pile
3. Wastes valuable pieces
4. Makes it harder to achieve declared targets

### Declaration Impact
If bots count these as "winnable plays" when declaring:
- They overestimate their winning potential
- Declare more piles than they can actually win
- Contributes to the 0.5 pile over-declaration gap

## Conclusion

The evidence clearly shows that:
1. **Never-win combos ARE being played** in actual games
2. **All bot positions** are affected (Bot 1-4 all played them)
3. **Multiple types** of never-win combos occur
4. The **is_never_win_combo() function is needed** to prevent these plays
5. This likely contributes to poor declaration accuracy