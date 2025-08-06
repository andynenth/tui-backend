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
# Point values from the game:
GENERAL = 14 points (highest)
KING = 13 points
QUEEN = 12 points
JACK = 11 points
10 = 10 points
9 = 9 points
8 = 8 points
7 = 7 points
# ... down to SOLDIER = 1 point

# AI categories:
high_pieces = [p for p in hand if p.point >= 9]      # Strong individual pieces
mid_pieces = [p for p in hand if 7 <= p.point < 9]   # Moderate pieces
# Low pieces (< 7) are implicitly weak
```

### Step 2: Combination Analysis

The AI searches for valid play types as defined in the rules:

```python
# Valid combinations the AI looks for:
- SINGLE: Any 1 piece
- PAIR: 2 of same name and color
- THREE_OF_A_KIND: 3 SOLDIERs of same color
- STRAIGHT: 3 pieces (GENERAL-ELEPHANT or CHARIOT-CANNON groups)
- FOUR_OF_A_KIND: 4 SOLDIERs of same color
- EXTENDED_STRAIGHT: 4 pieces with 1 duplicate
- FIVE_OF_A_KIND: 5 SOLDIERs of same color
- DOUBLE_STRAIGHT: 2 each of CHARIOT, HORSE, CANNON
```

The AI identifies "strong" combinations (everything except SINGLE and PAIR) because these are more likely to win turns.

### Step 3: Opening Strength Detection

```python
has_strong_opening = any(
    p.name.startswith("GENERAL") or p.point >= 13 for p in hand
)
```

This checks for:
- **GENERAL piece**: Worth 14 points, likely to win first turn
- **Kings (13 points)**: Also very strong openers
- **High-value straights**: Total 20+ points

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
Hand: [GENERAL_RED, KING_BLACK, HORSE_RED, HORSE_RED, CHARIOT_RED, CANNON_RED, SOLDIER_BLACK, SOLDIER_BLACK]

Analysis:
- High pieces: 2 (GENERAL=14, KING=13)
- Strong combos: 2
  1. STRAIGHT (CHARIOT-HORSE-CANNON) = 21 points
  2. PAIR (HORSE-HORSE) = 16 points
- Has strong opening: Yes (GENERAL)
- First player bonus: +1 (if applicable)

Score calculation: 2 (combos) + 1 (strong opening) + 1 (if first) = 4
Declaration: 4 piles
```

#### Medium Hand Example
```
Hand: [10_RED, 9_BLACK, 8_RED, 7_RED, 6_BLACK, 5_BLACK, 4_RED, 3_RED]

Analysis:
- High pieces: 2 (10, 9)
- Strong combos: 1
  1. STRAIGHT (8-7-6) = 21 points
- Has strong opening: No
- First player bonus: +1 (if applicable)

Score calculation: 1 (combo) + 0 + 1 (if first) = 2
Declaration: 2 piles
```

#### Weak Hand Example
```
Hand: [6_RED, 5_BLACK, 4_RED, 3_BLACK, 3_RED, 2_BLACK, 2_RED, SOLDIER_RED]

Analysis:
- High pieces: 0 (all pieces < 9)
- Strong combos: 0
- Has strong opening: No
- Would trigger redeal request!

Score calculation: 0 → adjusted to 1 (minimum)
Declaration: 1 pile (forced minimum)
```

## Why This Evaluation Works

1. **Strong combinations win turns**: The AI correctly identifies that THREE_OF_A_KIND, STRAIGHT, etc. are more likely to capture piles than singles or pairs.

2. **High pieces matter**: A GENERAL (14 points) or KING (13 points) can often win turns even as singles.

3. **Position advantage**: Being first player means you can declare without knowing others' intentions.

4. **Conservative estimation**: The AI tends to slightly underestimate (declaring 3-4 piles is common) which is safer than overcommitting.

## Limitations of Current Evaluation

1. **No opponent consideration**: Doesn't account for what others might have
2. **Static evaluation**: Doesn't adapt based on game state
3. **No strategic saving**: Always plays best combination available
4. **Simple redeal logic**: Only considers max piece value, not combination potential

These limitations are what the enhancement plan aims to address!