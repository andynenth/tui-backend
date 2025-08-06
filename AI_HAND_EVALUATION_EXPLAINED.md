# AI Hand Evaluation Explained

## Game Context

In Liap Tui, players need to:
1. **Declare** how many piles (0-8) they aim to capture
2. **Play** piece combinations to win turns and capture piles
3. **Score** points based on matching their declaration

## Hand Evaluation Process

### Step 1: Piece Value Assessment

The AI categorizes pieces based on the game's point system:

```python
# Point values from the game (RED/BLACK):
GENERAL = 14/13 points (highest)
ADVISOR = 12/11 points
ELEPHANT = 10/9 points
CHARIOT = 8/7 points
HORSE = 6/5 points
CANNON = 4/3 points
SOLDIER = 2/1 points (lowest)

# AI categories:
high_pieces = [p for p in hand if p.point >= 9]      # GENERAL, ADVISOR, ELEPHANT
mid_pieces = [p for p in hand if 7 <= p.point < 9]   # CHARIOT (and CHARIOT_BLACK at 7)
# Low pieces (< 7) are HORSE, CANNON, SOLDIER
```

### Step 2: Combination Analysis

The AI searches for valid play types as defined in the rules:

```python
# Valid combinations the AI looks for:
- SINGLE: Any 1 piece
- PAIR: 2 of same name and color
- THREE_OF_A_KIND: 3 SOLDIERs of same color
- STRAIGHT: 3 pieces of same color, either:
  - High group: GENERAL-ADVISOR-ELEPHANT
  - Low group: CHARIOT-HORSE-CANNON
- FOUR_OF_A_KIND: 4 SOLDIERs of same color
- EXTENDED_STRAIGHT: 4 pieces with 1 duplicate (e.g., CHARIOT-HORSE-HORSE-CANNON)
- FIVE_OF_A_KIND: 5 SOLDIERs of same color
- DOUBLE_STRAIGHT: 2 each of CHARIOT, HORSE, CANNON (6 pieces total)
```

The AI identifies "strong" combinations (everything except SINGLE and PAIR) because these are more likely to win turns.

### Step 3: Opening Strength Detection

```python
has_strong_opening = any(
    p.name.startswith("GENERAL") or p.point >= 13 for p in hand
)
```

This checks for:
- **GENERAL piece**: Worth 14/13 points, likely to win first turn
- **High-value pieces**: Any piece worth 13+ points (GENERAL_RED or GENERAL_BLACK)
- **High-value straights**: Total 20+ points (e.g., CHARIOT-HORSE-CANNON_RED = 18 points)

### Step 4: Declaration Score Calculation

The AI estimates how many piles it can capture:

```python
Base score = Number of strong combinations found
+ 1 if has strong opening (GENERAL or King)
+ 1 if first player (advantage in declaration order)
```

### Example Hand Evaluations

#### Strong Hand Example
```
Hand: [GENERAL_RED, ADVISOR_BLACK, HORSE_RED, HORSE_RED, CHARIOT_RED, CANNON_RED, SOLDIER_BLACK, SOLDIER_BLACK]

Analysis:
- High pieces: 2 (GENERAL_RED=14, ADVISOR_BLACK=11)
- Strong combos: 2
  1. STRAIGHT (CHARIOT-HORSE-CANNON) = 18 points (8+6+4)
  2. PAIR (SOLDIER-SOLDIER) = 2 points (not counted as strong)
- Has strong opening: Yes (GENERAL_RED)
- First player bonus: +1 (if applicable)

Score calculation: 1 (strong combo) + 1 (strong opening) + 1 (if first) = 3
Declaration: 3 piles
```

#### Medium Hand Example
```
Hand: [ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED]

Analysis:
- High pieces: 2 (ELEPHANT_RED=10, ELEPHANT_BLACK=9)
- Strong combos: 1
  1. STRAIGHT (CHARIOT-HORSE-CANNON_BLACK) = 15 points (7+5+3)
- Has strong opening: No (highest is 10, need 13+)
- First player bonus: +1 (if applicable)

Score calculation: 1 (combo) + 0 + 1 (if first) = 2
Declaration: 2 piles
```

#### Weak Hand Example
```
Hand: [HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK, CANNON_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_RED]

Analysis:
- High pieces: 0 (all pieces < 9, highest is HORSE=6/5)
- Strong combos: 0 (only pairs available, no straights or 3+ of same)
- Has strong opening: No
- Would trigger redeal request! (no piece > 9 points)

Score calculation: 0 → adjusted to 1 (minimum)
Declaration: 1 pile (forced minimum)
```

## Why This Evaluation Works

1. **Strong combinations win turns**: The AI correctly identifies that THREE_OF_A_KIND, STRAIGHT, etc. are more likely to capture piles than singles or pairs.

2. **High pieces matter**: A GENERAL (14/13 points) or ADVISOR (12/11 points) can often win turns even as singles.

3. **Position advantage**: Being first player means you can declare without knowing others' intentions.

4. **Conservative estimation**: The AI tends to slightly underestimate (declaring 3-4 piles is common) which is safer than overcommitting.

## Limitations of Current Evaluation

1. **No opponent consideration**: Doesn't account for what others might have
2. **Static evaluation**: Doesn't adapt based on game state
3. **No strategic saving**: Always plays best combination available
4. **Simple redeal logic**: Only considers max piece value, not combination potential

These limitations are what the enhancement plan aims to address!