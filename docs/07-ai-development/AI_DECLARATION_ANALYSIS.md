# AI Declaration Analysis

## Problem: Bots Over-Declare by ~0.5 Piles

### Evidence
- Bot 1-3: Declare 2.1, capture 1.5-1.6 (gap: 0.5-0.6)
- Bot 4: Declares 1.9, captures 1.5 (gap: 0.4)
- Declaration accuracy only 33-36%

### Root Cause Analysis

#### 1. High Piece Thresholds
The `get_piece_threshold()` function uses very restrictive thresholds:
- Pile room 1: >13 (only GENERAL_RED qualifies)
- Pile room 2: ≥13 (only GENERAL pieces)
- Pile room 3-4: ≥12 (ADVISOR_RED and up)
- Pile room 5+: ≥11 (standard opener)

#### 2. Optimistic Strong Piece Counting
When declaring, the AI:
1. Finds all strong combos first
2. Fills remaining pile room with "strong pieces"
3. But these thresholds are too restrictive

Example scenario:
- Bot has pile room 3
- Needs pieces ≥12 points (only ADVISOR_RED, GENERAL)
- If bot doesn't have these specific high pieces, it may:
  - Count lower pieces as "strong"
  - Or find combos that aren't actually winnable

#### 3. Competition Not Considered
The declaration logic doesn't account for:
- Other players competing for the same piles
- The fact that only the highest play wins
- Risk of being outplayed

### Why Bot 4 Performs Worse

Bot 4 has the lowest win rate (18%) despite declaring slightly less (1.9 vs 2.1):
- Position 4 declares last, seeing others' declarations
- May be forced into suboptimal declarations
- Still over-declares relative to ability

### Recommendations

1. **Lower thresholds for pile room 3-4** to standard opener (11 points)
2. **Add competition factor** - reduce declaration by 0.5 to account for competition
3. **Track historical accuracy** and adjust declarations based on past performance
4. **Implement never-win combo detection** to avoid counting unwinnable combinations
