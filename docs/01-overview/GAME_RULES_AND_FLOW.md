# Liap Tui - Game Rules & Flow Guide

## Overview

Liap Tui is a strategic multiplayer card game inspired by traditional Chinese-Thai gameplay. Players compete to accurately predict and achieve their declared pile counts while playing pieces strategically to win turns.

## Table of Contents

1. [Game Setup](#game-setup)
2. [Game Components](#game-components)
3. [Game Flow Overview](#game-flow-overview)
4. [Phase Details](#phase-details)
5. [Scoring System](#scoring-system)
6. [Winning Conditions](#winning-conditions)
7. [Strategy Tips](#strategy-tips)
8. [Common Scenarios](#common-scenarios)

---

## Game Setup

### Players
- **4 players** exactly (human players and/or bots)
- One player acts as the **host** who can start the game
- Players sit in fixed positions around a virtual table

### Game Length
- Multiple rounds until someone reaches **50 points**
- Each round consists of multiple turns
- Average game time: **15-30 minutes**

---

## Game Components

### Pieces (Cards)
The game uses 32 traditional Chinese chess pieces:

#### Red Pieces (16 total)
- **1 General** (帥) - 10 points
- **2 Advisors** (仕) - 2 points each  
- **2 Elephants** (相) - 2 points each
- **2 Horses** (馬) - 4 points each
- **2 Chariots** (車) - 9 points each
- **2 Cannons** (炮) - 4.5 points each
- **5 Soldiers** (兵) - 1 point each

#### Black Pieces (16 total)
- **1 General** (將) - 10 points
- **2 Advisors** (士) - 2 points each
- **2 Elephants** (象) - 2 points each  
- **2 Horses** (馬) - 4 points each
- **2 Chariots** (車) - 9 points each
- **2 Cannons** (炮) - 4.5 points each
- **5 Soldiers** (卒) - 1 point each

### Hand Size
- Each player receives **8 pieces** per round
- Players keep their hands hidden from others

---

## Game Flow Overview

```
🏠 WAITING (Room Setup)
    ↓ All 4 players ready
    
🎯 PREPARATION (Deal Cards)
    ↓ Cards dealt, weak hands checked
    
📋 DECLARATION (Declare Targets)  
    ↓ All players declare pile counts
    
🎮 TURN (Play Pieces)
    ↓ Players play pieces in turns
    
📊 TURN_RESULTS (Show Results)
    ↓ 7-second display, auto-continue
    
⚖️ SCORING (Calculate Points)
    ↓ Compare declared vs actual piles
    
🏆 GAME_OVER (Final Results)
```

---

## Phase Details

### 1. WAITING Phase 
**Room Setup and Player Management**

**What Happens:**
- Host creates a room with a unique Room ID
- Players join using the Room ID
- Host can add bots to fill empty slots
- Game starts when all 4 slots are filled

**Player Actions:**
- Join room using Room ID
- Add/remove bots (host only)
- Start game (host only, when room full)
- Leave room

### 2. PREPARATION Phase
**Card Dealing and Weak Hand Management**

**What Happens:**
- 8 pieces are dealt randomly to each player
- System checks for "weak hands"
- Players with weak hands can request a redeal

**Weak Hand Rule:**
- A hand is "weak" if it contains **no pieces worth more than 9 points**
- Only the **General** (10 points) and **Chariots** (9 points) prevent weak hands
- If multiple players have weak hands, they all decide simultaneously

**Redeal Process:**
- Weak hand players have 30 seconds to accept or decline redeal
- If anyone accepts, cards are reshuffled and dealt again
- Score multiplier increases by 1 for each redeal (affects final scoring)
- First player to accept becomes the round starter

### 3. DECLARATION Phase
**Target Setting**

**What Happens:**
- Players declare how many "piles" they intend to capture
- Declarations happen in turn order (starting with round starter)
- Each player declares a number from **0 to 8**

**Declaration Rules:**
- Must declare between 0-8 piles
- **Last player cannot make the total equal 8** (prevents guaranteed outcomes)
- Once declared, cannot be changed

**Turn Order:**
- Round starter declares first
- Continues clockwise around table
- Order is maintained throughout the round

### 4. TURN Phase
**Strategic Piece Playing**

**What Happens:**
- Players play pieces in turns to compete for "tricks"
- Turn starter plays 1-6 pieces, others must match the count
- Highest value combination wins all played pieces
- Winner gets "piles" equal to the number of pieces played

**Turn Rules:**

#### Piece Count Rules
- **Turn starter**: Can play 1-6 pieces
- **Other players**: Must play exactly the same number of pieces
- If you can't match the count, you're out of the turn

#### Play Types (in order of strength)
1. **SINGLE** (1 piece) - Any single piece
2. **PAIR** (2 pieces) - Two pieces of same name and color
3. **THREE_OF_A_KIND** (3 pieces) - Three soldiers of same color
4. **STRAIGHT** (3 pieces) - Three pieces from same color group
5. **FOUR_OF_A_KIND** (4 pieces) - Four soldiers of same color  
6. **EXTENDED_STRAIGHT** (4 pieces) - Four pieces with one duplicate
7. **EXTENDED_STRAIGHT_5** (5 pieces) - Five pieces with two duplicates
8. **FIVE_OF_A_KIND** (5 pieces) - Five soldiers of same color
9. **DOUBLE_STRAIGHT** (6 pieces) - 2 Chariots + 2 Horses + 2 Cannons (same color)

#### Winning a Turn
- Highest play type wins
- If same play type, highest point value wins
- Winner collects all played pieces as "piles"
- Winner becomes starter of next turn

### 5. TURN_RESULTS Phase
**Results Display**

**What Happens:**
- Shows who won the turn and with what play
- Displays updated pile counts for all players
- Automatically continues after 7 seconds
- No player input required

**Information Shown:**
- Winner's name and winning play
- Pieces won and pile count gained
- Current pile standings
- Next turn starter

### 6. SCORING Phase
**Point Calculation**

**What Happens:**
- Compare each player's declared vs actual pile count
- Calculate round scores using scoring formula
- Apply redeal multiplier if applicable
- Check for game winner (50+ points)

**Scoring Formula:**
- **Perfect Zero**: Declared 0, got 0 → **+3 points**
- **Failed Zero**: Declared 0, got more → **-[actual piles] points**
- **Perfect Match**: Declared X, got X → **X + 5 points**
- **Missed Target**: Otherwise → **-|declared - actual| points**
- **Multiplier**: Final score × redeal_multiplier

**Examples:**
```
Player declares 3, captures 3 piles:
Base score = 3 + 5 = 8 points

Player declares 0, captures 0 piles:
Base score = 3 points (perfect zero bonus)

Player declares 2, captures 4 piles:
Base score = -|2 - 4| = -2 points

Player declares 0, captures 2 piles:
Base score = -2 points (failed zero penalty)
```

### 7. GAME_OVER Phase
**Final Results**

**What Happens:**
- Display final rankings and scores
- Show game statistics (rounds played, duration)
- Celebrate winners
- Option to return to lobby

**End Conditions:**
- Game ends when any player reaches **50+ points**
- If multiple players reach 50+, highest score wins
- Maximum 20 rounds (rare)

---

## Scoring System

### Round Scoring
Each round, players earn points based on accuracy of their declarations:

| Scenario | Formula | Example |
|----------|---------|---------|
| Perfect Zero | +3 | Declared 0, got 0 → +3 pts |
| Failed Zero | -actual | Declared 0, got 2 → -2 pts |
| Perfect Match | declared + 5 | Declared 3, got 3 → +8 pts |
| Missed Target | -difference | Declared 2, got 4 → -2 pts |

### Redeal Multiplier
- Starts at 1 (no effect)
- Increases by 1 for each redeal in the round
- Multiplies the final round score
- Example: Base score +8, multiplier 2 → Final score +16

### Cumulative Scoring
- Points accumulate across rounds
- First to 50+ points wins
- Negative scores are possible and can delay victory

---

## Winning Conditions

### Primary Win Condition
- **First player to reach 50+ total points** wins the game
- If multiple players reach 50+ in the same round, **highest score wins**

### Secondary Conditions
- **Tie-breaker**: If scores are exactly tied at 50+, play continues
- **Maximum rounds**: Game ends after 20 rounds (winner = highest score)
- **Early victory**: Possible to win in as few as 2-3 rounds with perfect play

---

## Strategy Tips

### Declaration Strategy
- **Conservative approach**: Declare lower numbers for safer, positive scores
- **Aggressive approach**: Declare higher numbers for big point gains
- **Zero strategy**: Declaring 0 can be safe (+3) or risky (-actual)
- **Watch opponents**: Consider what others have declared

### Piece Playing Strategy
- **High-value pieces**: Save Generals and Chariots for important turns
- **Combination building**: Look for pairs, straights, and special combinations
- **Count management**: Remember you must match the starter's piece count
- **End-game timing**: Plan when to use your best pieces

### Turn Management
- **Starting turns**: Control the piece count when you start
- **Following turns**: Adapt to required piece count
- **Pile distribution**: Win turns when you need piles most
- **Defensive play**: Sometimes losing a turn strategically helps

### Advanced Tactics
- **Pile counting**: Track who needs what pile counts
- **Hand deduction**: Guess opponents' hands from their plays  
- **Timing decisions**: When to use strong vs weak pieces
- **Risk assessment**: Balance safety vs potential gain

---

## Common Scenarios

### Weak Hand Decisions
**Scenario**: You have 8 low-value pieces (all 1-4 points)
- **Accept redeal**: Higher chance of better pieces, but score multiplier increases
- **Decline redeal**: Play with current hand, avoid multiplier penalty
- **Consider opponents**: If others also have weak hands, coordinate decisions

### Declaration Dilemmas
**Scenario**: You're last to declare, current total is 6
- **Cannot declare 2** (would make total = 8, which is illegal)
- **Must choose 0, 1, 3, 4, 5, 6, 7, or 8**
- **Consider your hand strength** to estimate realistic pile count

### Turn Playing Choices
**Scenario**: Starter plays 3 pieces with low value
- **Match with strong pieces**: Likely to win but uses good cards
- **Match with weak pieces**: Save strong cards but likely lose
- **Consider pile needs**: Do you need piles to meet your declaration?

### End Game Situations
**Scenario**: You're at 45 points, need 5+ to win
- **Aggressive declaration**: Go for higher pile count
- **Safe declaration**: Ensure positive score to stay in contention
- **Watch leader**: Block opponents who are close to winning

### Redeal Multiplier Impact
**Scenario**: Redeal multiplier is 3, you scored +6 base points
- **Final score**: +6 × 3 = +18 points (significant boost)
- **Risk assessment**: Multiplier amplifies both gains and losses
- **Strategic consideration**: High multipliers make precision more important

---

## Game Variants & House Rules

While the official rules are implemented in the digital version, players sometimes use variants:

### Declaration Variants
- **Total must equal 8**: Alternative rule where all declarations must sum to exactly 8
- **Open declarations**: All declarations visible immediately
- **Blind declarations**: Declare before seeing your hand

### Scoring Variants  
- **No zero bonus**: Remove the +3 bonus for perfect zero
- **Progressive bonus**: Bonus increases with declaration size
- **Penalty cap**: Limit negative scores per round

### Special Rules
- **Mercy rule**: End game at 75 points instead of 50
- **Comeback rule**: Reset scores if someone gets too far behind
- **Speed rounds**: Time limits on declarations and plays

*Note: The digital implementation uses the standard rules described above.*

---

## Conclusion

Liap Tui combines strategic thinking, risk assessment, and tactical play in a fast-paced multiplayer environment. Success requires:

- **Accurate self-assessment** of your hand strength
- **Strategic declaration** based on risk tolerance  
- **Tactical piece play** to achieve your declared goals
- **Adaptability** to changing game situations

Master these elements, and you'll be well on your way to Liap Tui victory! 🏆

---

*For technical implementation details, see the [Game Lifecycle Documentation](GAME_LIFECYCLE_DOCUMENTATION.md) and [Developer Onboarding Guide](DEVELOPER_ONBOARDING_GUIDE.md).*