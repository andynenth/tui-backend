# AI Declaration Strategy Guide

## Core Understanding

### What is Declaration?
**Declaration = Number of piles you expect to capture with your hand**
- Piles = number of pieces each player played in turns you win
- Win 1-piece turn = 1 pile
- Win 3-piece turn (STRAIGHT) = 3 piles
- Win 4-piece turn = 4 piles
- Maximum 8 piles per round (you have 8 pieces total)
- Declaration range: 0-7 (sum of all 4 players cannot equal 8)

### Pile Counting Rule
This is the fundamental rule that was initially misunderstood:
- **Piles ≠ number of winning turns**
- **Piles = total pieces captured from all wins**
- Example: Win 2 turns (1-piece + 3-piece) = 4 piles total

## Strategic Framework

### Core Strategic Principles

#### 1. Pile Room as Absolute Constraint
- Maximum piles in any round = 8
- Available room = 8 - sum(previous_declarations)
- This creates a HARD CEILING regardless of hand strength
- Example: Great combos but pile room = 0 → MUST declare 0
- Example: GENERAL_BLACK but pile room = 1 → can only win 1

#### 2. Competition Assessment
- **Weak field (declarations 0-1)**: Opponents have poor hands, no combos
- **Strong field (declarations 4-5)**: Opponents have excellent hands with combos
- This dramatically affects your winning chances

#### 3. Reading Declaration Patterns (CRITICAL)
- **Declarations 0-1 = No combos**: These players have terrible hands with NO combinations
- **Declarations 2-3 = Mixed**: May have some combos or decent singles  
- **Declarations 4+ = Strong combos**: Likely have multiple combinations
- **Key Insight**: Low declarers (0-1) will NOT create combo opportunities - they play singles only!

#### 4. Opener Reliability in Context
**Definition**: Strong single pieces that can reliably win turns and give control

**The Opener Group** (11-14 points):
- GENERAL_RED (14 points) - Always reliable
- GENERAL_BLACK (13 points) - Always reliable
- ADVISOR_RED (12 points) - Context-dependent
- ADVISOR_BLACK (11 points) - Context-dependent

**Context Matters**:
- Weak field → ADVISOR likely wins
- Strong field → ADVISOR might lose to GENERALs

#### 5. GENERAL_RED as Game Changer
- **GENERAL_RED (14 points) = Strongest piece in game**
- **Guarantees control like being starter**
- In weak fields especially, enables dramatic declarations:
  1. Win with GENERAL_RED → gain control
  2. Play your combinations freely
- Example: With [1,0] opponents:
  - Without GENERAL_RED: 2 piles (opener + maybe 1 more)
  - With GENERAL_RED: 5 piles! (GENERAL + FOUR_OF_A_KIND)
- **Key**: GENERAL_RED transforms unplayable combos into guaranteed piles

#### 6. Combo Opportunity Analysis
- **Without starter/opener, need opponents to play 3+ pieces**
- Check opponent declarations:
  - Low (0-2) → They have no combos → 0% chance for your combo
  - High (3+) → They have combos → Possible opportunity (but they control)
- **Combo strength matters**: 
  - CHARIOT-HORSE-CANNON (18pts) is too weak to rely on
  - Even with opportunity, weak combos often lose
- **Critical Exception**: GENERAL_RED/BLACK can CREATE opportunities

#### 7. Turn Economy & Last Player Constraints
- 8 pieces = 8 turns total
- Must allocate turns wisely
- Can't play all combinations if limited room
- **Last Player Rule**: Cannot declare value that makes total = 8
  - Creates strategic distortions and forced sub-optimal declarations

#### 8. Realistic Evaluation & Position Gap
- Don't count piles you can't actually win
- Consider competition when valuing openers
- **Starter vs Non-Starter is MASSIVE**:
  - Same hand as starter can declare 8 piles
  - Same hand non-starter might declare 0 piles!
- Combos without opportunity = dead weight
- GENERAL_RED changes everything by guaranteeing control

## How Combinations Affect Pile Count

**Key Insight**: Larger combinations = more piles per win
- SINGLE (1 piece) → 1 pile
- PAIR (2 pieces) → 2 piles
- STRAIGHT/THREE_OF_A_KIND (3 pieces) → 3 piles
- FOUR_OF_A_KIND (4 pieces) → 4 piles
- FIVE_OF_A_KIND (5 pieces) → 5 piles
- DOUBLE_STRAIGHT (6 pieces) → 6 piles

## Implementation Approaches

### Option 1: Full Strategic Implementation (Complex)
- Add pile room calculation
- Add competition assessment
- Add opener reliability adjustment
- Add combo viability check
- Complex but realistic

### Option 2: Simplified Version (Recommended)
- Just add pile room check
- If room < combo_size, don't count combo
- Simpler but still improves realism

### Option 3: Keep Current Simple System (Current Choice)
- Just count piles from hand
- No strategic adjustments
- Easiest but less realistic

**User Decision**: Keep Option 3 - simple hand evaluation only

## Key Strategic Insights

1. **Pile room is absolute** - trumps all other considerations
2. **Declaration patterns reveal combo availability** - [0,1] = no combo opportunities
3. **GENERAL_RED is transformative** - turns unplayable hands into powerhouses
4. **Position matters enormously** - starter vs non-starter can be 8 vs 0 piles
5. **Last player distortions** - sum ≠ 8 rule creates strategic anomalies

## Order of Hand Value

From the examples, we can see a clear hierarchy:
1. **Starter + Opener + Combos = Best** (5-8 piles)
2. **Starter + Combos = Good** (3-4 piles)
3. **Opener + Combos = Good** (3-4 piles)
4. **Just Opener = Okay** (1-2 piles)
5. **Just Combos = Poor** (0-1 piles) - can't play without control
6. **Nothing = Worst** (0 piles)

## Critical Takeaways

1. **Control is Everything**: Without starter position OR opener, combinations are often unplayable
2. **Context Changes Value**: Same hand can be worth 0-8 piles depending on situation
3. **GENERAL_RED is Special**: Only piece that guarantees control regardless of field
4. **Low Declarations Matter**: [0,1] tells you opponents can't help you play combos
5. **Pile Room Overrides All**: Even perfect hands can't exceed available room