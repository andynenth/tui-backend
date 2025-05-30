# 🧠 Liap Tui – Game Rules

## 🎯 Objective

Players aim to **accumulate points** by capturing piece sets ("piles") across multiple rounds.

A player wins by reaching **50 points**, or having the **highest score after 20 rounds**.

---

## 👥 Players

- 4 players per game
- Each player holds **8 pieces** at the start of each round

---

## 🃏 Pieces

- **Total:** 32 pieces
- Each piece has a `name` (e.g., GENERAL, SOLDIER) and a `color` (RED or BLACK)
- Each piece has a `point` value defined in `PIECE_POINTS`
- Example:
    - `GENERAL_RED` = 14 points
    - `SOLDIER_BLACK` = 1 point

---

## 🔄 Round Flow

### 1. Deal Phase

- Shuffle and deal 32 pieces (8 per player)
- If a player has **no piece > 9 points**, they may request a **redeal**
    - If redeal is accepted:
        - All hands are reshuffled and redealt
        - The redealing player becomes **starter next round**
        - Scores are multiplied (×2, ×3, etc.)

### 2. Starter Selection

- If a previous round winner exists → they start
- Otherwise → player with `GENERAL_RED` starts

### 3. Declaration Phase

- Each player declares how many **piles** they aim to capture (0–8)
- Rules:
    - **Sum of declarations must NOT equal 8**
    - If a player declares `0` for **2 rounds in a row**, they must declare **≥1** this round

### 4. Turn Phase

- Players take turns playing **sets of 1–6 pieces**
- Each turn:
    1. **Starter** plays a valid set (must pass validation)
    2. Others must play **same number of pieces** (can be invalid)
    3. Winner is determined using `compare_plays()`
        - Winner takes all pieces as a **pile**
        - Winner starts next turn
    4. Remove all played pieces from hands

### 5. Scoring Phase

- After all hands are empty:
    - Compare each player's **actual captured piles** to their **declared target**
    - Calculate score (see table below)
    - Apply **redeal multiplier** if applicable

### 6. End Game Check

- Game ends if:
    - A player reaches **50 points**, or
    - **20 rounds** have passed
- Highest score wins (ties allowed)

---

## 🧮 Scoring Table

| Case | Result |
| --- | --- |
| Declared 0, captured 0 | +3 points (bonus) |
| Declared 0, captured > 0 | −captured (penalty) |
| Declared X, captured X | X + 5 points (perfect hit) |
| Declared X, captured ≠ X | − |
- If redeal occurred → **multiply score** by ×2, ×3, etc.

---

## 🧠 Play Types (Valid Sets)

| Type | Description |
| --- | --- |
| `SINGLE` | 1 piece |
| `PAIR` | 2 of the same `name` and `color` |
| `THREE_OF_A_KIND` | 3 `SOLDIER`s of the same color |
| `STRAIGHT` | 3 of a valid group (GENERAL–ELEPHANT or CHARIOT–CANNON), same color |
| `FOUR_OF_A_KIND` | 4 `SOLDIER`s of the same color |
| `EXTENDED_STRAIGHT` | 4 of valid group, same color, 1 piece duplicated (e.g., HORSE x2) |
| `EXTENDED_STRAIGHT_5` | 5 of valid group, same color, 2 duplicates, only 3 unique types |
| `FIVE_OF_A_KIND` | 5 `SOLDIER`s of the same color |
| `DOUBLE_STRAIGHT` | 2 each of `CHARIOT`, `HORSE`, `CANNON` (6 pieces), same color |

> Play strength is ranked using `PLAY_TYPE_PRIORITY`  
> If tied by type → higher total points wins  
> For `EXTENDED_STRAIGHT(_5)` → only **top 3 unique piece types** are summed

---

## 🧠 Key Data Structures

- **`Player`**: Holds name, hand, score, declaration, and zero-declare streak
- **`Piece`**: Has kind, point, and derived `name`/`color`
- **`TurnPlay`**: One player's action in a single turn
- **`TurnResult`**: Summary of all plays and the winner for one turn

---
