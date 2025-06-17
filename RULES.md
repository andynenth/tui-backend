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

- Shuffle the 32 pieces and deal **8 pieces to each player**.
- **Redeal Request:** If a player has a **weak hand** (meaning no single piece has a value greater than **9 points**), they may request a **redeal**.
    - **When a Redeal Occurs:**
        - All hands are immediately **reshuffled and redealt**.
        - The player who requested the redeal becomes the **starter of the round**.
        - Scores for this round are **doubled** (a 2x multiplier applies).
        - If a player still has a **weak hand** after this redeal, they may request another redeal. For each subsequent redeal request, the score multiplier increases by **1** (e.g., a 3x multiplier for the second redeal, 4x for the third, and so on).

### 2. Starter Selection
- **First Round:** The player holding the **GENERAL_RED** piece starts the round.
- **Redeal Override:** If a **redeal** occurs this turn, the player who requested the redeal starts the round.
- **Subsequent Rounds:** Otherwise, the **winner of the last turn of the previous round** starts the current round.

### 3. Declaration Phase

- Each player declares how many **piles** they aim to capture (0–8)
- Rules:
    - **The cumulative total of all declarations must not equal 8. To ensure this, the last player of the declaration phase may not declare a number that would cause the total sum to reach exactly 8.**
    - If a player declares `0` for **2 rounds in a row**, they must declare **≥1** this round

### 4. Turn Phase

- Players take turns playing **sets of 1–6 pieces**
- Each turn:
    1. **Starter** plays a valid set (must pass validation)
    2. Others must play **same number of pieces** (can be invalid, but auto lose the turn)
    3. Winner is determined using `compare_plays()`
        - Winner takes all pieces as a **pile**
        - Winner starts next turn

### 5. Scoring Phase

- After all hands are empty:
    - Compare each player's **actual captured piles** to their **declared target**
    - Calculate score (see table below)
    - Apply **redeal multiplier** if applicable

### 6. End Game Check

- Game ends if:
    - A player reaches **50 points**
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
# RULE
# 🕹️ Liap Tui – Complete Game Rules
# 🎯 Objective
Players aim to **accumulate points** by capturing piles across multiple rounds. **Win condition:** First player to reach **50 points** wins the game.

# 🃏 Piece Point Values
| **Piece** | **Points** | **Piece** | **Points** |
|:-:|:-:|:-:|:-:|
| GENERAL_RED | 14 | GENERAL_BLACK | 13 |
| ADVISOR_RED | 12 | ADVISOR_BLACK | 11 |
| ELEPHANT_RED | 10 | ELEPHANT_BLACK | 9 |
| CHARIOT_RED | 8 | CHARIOT_BLACK | 7 |
| HORSE_RED | 6 | HORSE_BLACK | 5 |
| CANNON_RED | 4 | CANNON_BLACK | 3 |
| SOLDIER_RED | 2 | SOLDIER_BLACK | 1 |
**Note:** RED pieces are generally stronger than BLACK pieces of the same type.

# 👥 Setup
* **4 players** per game
* **32 pieces total** (8 pieces per player each round)
* Each piece has: name, color (RED/BLACK), and point value

⠀
# 🔄 Complete Round Flow
### Phase 1: Preparation Phase
**1** **Deal 8 pieces** to each player
**2** **Check for weak hands** (no piece > 9 points)
**3** **Redeal process** (if weak hands exist):
	* Each weak player decides: accept redeal or decline
	* If accepted: reshuffle all hands, increase multiplier (2x → 3x → 4x...)
	* Redeal requester becomes round starter
**4** **Determine starter** (priority order):
	* **If redeal occurred:** Redeal requester starts (overrides all other rules, even Round 1)
	* **If Round 1 & no redeal:** Player with GENERAL_RED starts
	* **If other rounds & no redeal:** Last turn winner starts

⠀Phase 2: Declaration Phase
Each player declares target piles (0-8) starting from round starter.
**Declaration Rules:**
* **Total declarations cannot equal exactly 8**
* **Two-zero rule:** If declared 0 twice in a row → must declare ≥1
* **Last player restriction:** Cannot choose number that makes total = 8

⠀**Important:** Only the **last player** is restricted. Other players can make the total equal 8.
**Example Declaration Sequence:**
* Player 1: declares 5 (total = 5)
* Player 2: declares 3 (total = 8) ✅ **Allowed - not last player**
* Player 3: declares 0 (total = 8) ✅ **Allowed - not last player**
* Player 4: ❌ **Cannot declare 0** (would keep total = 8), must choose different number

⠀Phase 3: Turn Phase
**How each turn works:**
**1** **Starter plays 1-6 pieces** (must be valid combination)
	* Invalid plays → must retry until valid
	* **Starter must announce the play type** to all players
	* **Starter's play sets TWO requirements for everyone else:**
		* **Piece count:** Everyone must play same number of pieces
		* **Play type:** Everyone must play same type to compete
**2** **Other players play same number of pieces**
	* **Must match starter's play type** to get points for comparison
	* **Different type = 0 points** (same as auto-lose)
	* **Invalid combination = 0 points**
**3** **Winner determination:**
	* Compare only plays of same type as starter
	* Higher play type priority wins, if tied → higher points wins
	* If same type and same points → **earlier play order wins**
**4** **Winner gets piles = number of pieces played in turn**
	* Example: 4 pieces played → winner gets 4 piles toward declaration
**5** **Winner starts next turn, continue until all hands empty**

⠀Phase 4: Scoring Phase
**Calculate base score for each player:**
| **Declared** | **Actual** | **Score Formula** | **Example** |
|:-:|:-:|:-:|:-:|
| 0 | 0 | +3 bonus | +3 points |
| 0 | >0 | -actual | Declared 0, got 2 → -2 points |
| X | X | X + 5 bonus | Declared 3, got 3 → 8 points |
| X | ≠X | -|difference| | Declared 5, got 3 → -2 points |
**Apply redeal multiplier if applicable:**
* First redeal: ×2, Second redeal: ×3, Third redeal: ×4, etc.

⠀**Check win condition:**
* If anyone ≥ 50 points → Game Over
* **Multiple players ≥ 50:** Highest score wins
* **Tied at same score:** Both players win (tie allowed)
* Otherwise → Start next round

⠀
# 💪 Play Types (Strength Priority)
**1** **SINGLE** - 1 piece
**2** **PAIR** - 2 same name + color
**3** **THREE_OF_A_KIND** - 3 SOLDIERs same color
**4** **STRAIGHT** - 3 of group (GENERAL-ELEPHANT or CHARIOT-CANNON) same color
**5** **FOUR_OF_A_KIND** - 4 SOLDIERs same color
**6** **EXTENDED_STRAIGHT** - STRAIGHT + 1 duplicate (4 of group, same color, 1 duplicate)
**7** **EXTENDED_STRAIGHT_5** - STRAIGHT + 2 duplicates (5 of group, same color, 2 duplicates)
**8** **FIVE_OF_A_KIND** - 5 SOLDIERs same color
**9** **DOUBLE_STRAIGHT** - 2 each CHARIOT+HORSE+CANNON same color

⠀**Special Scoring Rule:**
* **EXTENDED_STRAIGHT & EXTENDED_STRAIGHT_5**: Only count the **top 3 highest-value unique piece types** for comparison
* **All other types**: Count total points of all pieces

⠀
# 📊 Example Turn Sequences
### Example 1: Play Type Matching
**Starter sets requirements for everyone:**
**1** **Starter plays 4 pieces** (SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED) - FOUR_OF_A_KIND
	* **Requirements set:** Everyone must play 4 pieces of FOUR_OF_A_KIND type
**2** **Player B plays 4 pieces** (CHARIOT_RED, HORSE_RED, CANNON_RED, ADVISOR_RED) - tries STRAIGHT → **0 points** (wrong type)
**3** **Player C plays 4 pieces** (GENERAL_RED, CHARIOT_BLACK, HORSE_BLACK, ELEPHANT_RED) - invalid → **0 points** (invalid)
**4** **Player D plays 4 pieces** (SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK) - FOUR_OF_A_KIND → **Valid competitor**
	* **Scoring:** SOLDIER_BLACK(1) × 4 = 4 points
**5** **Result:** Starter wins (SOLDIER_RED: 2×4 = 8 points vs Player D: 4 points)
**6** **Starter gets 4 piles** and starts next turn

⠀Example 2: Same Type Competition (EXTENDED_STRAIGHT)
**1** **Starter plays 4 pieces** (CHARIOT_BLACK, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK) - EXTENDED_STRAIGHT
	* **Scoring:** Top 3 unique types = CHARIOT_BLACK(7) + HORSE_BLACK(5) + CANNON_BLACK(3) = 15 points
**2** **Player B plays 4 pieces** (CHARIOT_RED, HORSE_RED, CANNON_RED, CANNON_RED) - valid EXTENDED_STRAIGHT
	* **Scoring:** Top 3 unique types = CHARIOT_RED(8) + HORSE_RED(6) + CANNON_RED(4) = 18 points
**3** **Player C plays 4 pieces** (GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, SOLDIER_BLACK) - invalid combination → **0 points**
**4** **Player D plays 4 pieces** (SOLDIER_RED, SOLDIER_RED, ELEPHANT_BLACK, HORSE_RED) - invalid combination → **0 points**
**5** **Result:** Player B wins (18 points vs Starter's 15 points)

⠀Example 3: Tie Breaker (SINGLE Type)
**1** **Player 1 plays 1 piece** (CANNON_BLACK, 3 points) - sets SINGLE type
**2** **Player 2 plays 1 piece** (CHARIOT_BLACK, 7 points) - valid SINGLE
**3** **Player 3 plays 1 piece** (CHARIOT_BLACK, 7 points) - valid SINGLE, same as Player 2
**4** **Player 4 plays 1 piece** (HORSE_BLACK, 5 points) - valid SINGLE
**5** **Result:** Player 2 wins (7 points, played before Player 3 who also had 7 points)

⠀
# 🎮 Strategic Implications
**Declaration Strategy:**
* Higher declarations = bigger rewards but harder to achieve
* Zero declarations = safe +3 points but no growth potential
* Last player can see all others' declarations before choosing

⠀**Turn Strategy (as Starter):**
* **Piece count choice:** More pieces = more piles if you win, but harder for everyone
* **Play type choice:** Pick types you can beat or others can't match
* **Double advantage:** You set both requirements AND play first

⠀**Turn Strategy (as Follower):**
* Must have the right type to compete at all
* Sometimes better to play invalid (0 points) than waste good pieces
* Pay attention to what types others likely have

⠀**Scoring Strategy:**
* Perfect predictions give massive bonuses (declared + 5)
* Redeal multipliers can dramatically change scores
* Game can end suddenly when someone hits 50

⠀This system rewards both tactical turn play and strategic long-term planning!
