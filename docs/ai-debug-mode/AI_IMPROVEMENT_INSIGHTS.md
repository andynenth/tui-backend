# AI Improvement Insights - What to Look For

## Critical Bugs to Detect

### 1. Declaration Phase Bugs
**Bug**: Over-aggressive declarations
```
Pattern: Bot declares 6+ piles with mediocre hand
Example: Hand has 1 opener, no combos → declares 6
Impact: Massive negative scores, immediate loss
Fix: Check hand strength before high declarations
```

**Bug**: Zero declaration with strong hand
```
Pattern: Bot has 2+ openers but declares 0
Example: GENERAL_BLACK, ADVISOR_RED in hand → declares 0
Impact: Wastes winning potential
Fix: Force minimum declaration with strong hands
```

**Bug**: Ignoring pile room constraints
```
Pattern: Position 3 declares high when pile room is low
Example: Previous: [3, 4], Bot declares 4 (total > 8)
Impact: Cannot achieve target, guaranteed negative score
Fix: Respect pile room calculations
```

### 2. Turn Play Bugs
**Bug**: Wasting openers when at target
```
Pattern: Bot at 3/3 piles plays GENERAL on weak turn
Example: Already met target, plays GENERAL vs SOLDIER
Impact: Loses valuable pieces unnecessarily
Fix: Play weakest possible when at target
```

**Bug**: Not playing to win when needed
```
Pattern: Bot needs 1 more pile, plays weak pieces
Example: 2/3 piles, final turn, plays SOLDIER vs HORSE
Impact: Fails to meet declaration target
Fix: Identify must-win situations
```

**Bug**: Combo mismanagement
```
Pattern: Breaking combos unnecessarily
Example: Has THREE_OF_A_KIND, plays one piece only
Impact: Loses combo advantage
Fix: Preserve combos unless necessary
```

## Performance Patterns to Monitor

### 1. Declaration Accuracy Metrics
**Ideal**: 60-80% exact matches (declared = captured)
```
Good: Bot 1 declared 3, captured 3 (100%)
OK: Bot 2 declared 4, captured 3 (75%)
Bad: Bot 3 declared 5, captured 1 (20%)
```

**Red Flags**:
- Accuracy below 40% → AI overestimating
- Accuracy above 90% → AI too conservative
- High variance between games → Inconsistent logic

### 2. Win Rate Distribution
**Ideal**: 20-30% win rate per position
```
Balanced: P1=25%, P2=23%, P3=27%, P4=25%
Imbalanced: P1=45%, P2=20%, P3=20%, P4=15%
```

**Red Flags**:
- First player wins >40% → Starter advantage too high
- Last player wins <15% → Position disadvantage
- Any position <10% → Systematic disadvantage

### 3. Score Distributions
**Healthy Game Patterns**:
```
Winner: 50-80 points (achieved target)
Second: 20-40 points (mostly positive)
Third: -10 to +20 points (mixed results)
Last: -30 to 0 points (struggled)
```

**Unhealthy Patterns**:
```
Blowouts: Winner 100+, others negative
Stalemates: All players 0-20 points
Volatility: -50 to +100 in same game
```

## Strategic Improvements

### 1. Opener Usage Analysis
**What to Log**:
```json
{
  "opener_timing": {
    "played_turn": 3,
    "game_phase": "early",
    "necessity": "high",  // needed to win
    "alternatives": ["PAIR", "weak_pieces"],
    "outcome": "won_pile"
  }
}
```

**Insights to Find**:
- Are openers used too early?
- Do bots save openers when behind?
- Is opener used for control or panic?

### 2. Combo Decision Tree
**What to Log**:
```json
{
  "combo_decision": {
    "available": ["THREE_OF_A_KIND", "PAIR"],
    "hand_size": 6,
    "piles_needed": 2,
    "choice": "save_combo",
    "reasoning": "might_need_later"
  }
}
```

**Insights to Find**:
- When should combos be played vs saved?
- Are weak combos overvalued?
- Do bots recognize combo opportunities?

### 3. Adaptation Patterns
**What to Track**:
- Does AI adjust strategy based on opponent declarations?
- Can AI identify weak opponents?
- Does AI learn from previous rounds?

## Key Metrics Dashboard

### Per-Game Metrics
```
Game #1 Summary:
├── Winner: Bot 3 (52 points)
├── Rounds: 3
├── Declaration Accuracy:
│   ├── Bot 1: 66% (2/3, 3/4, 2/2)
│   ├── Bot 2: 33% (1/3, 2/4, 0/2)
│   ├── Bot 3: 100% (3/3, 3/3, 2/2)
│   └── Bot 4: 50% (2/3, 1/3, 2/3)
├── Turn Wins: B1=8, B2=5, B3=9, B4=6
└── Key Decisions:
    ├── Round 1: Bot 2 over-declared (4 vs 1 actual)
    ├── Round 2: Bot 3 perfect round
    └── Round 3: Bot 1 comeback attempt failed
```

### Aggregate Analysis
```
After 100 games:
├── Position Win Rates: [26%, 24%, 25%, 25%] ✓ Balanced
├── Avg Declaration Accuracy: 68% ✓ Good
├── Avg Game Length: 3.2 rounds ✓ Normal
├── Score Ranges:
│   ├── Winners: 48-73 (avg 58)
│   ├── 2nd place: 15-41 (avg 28)
│   ├── 3rd place: -5-25 (avg 10)
│   └── Last place: -28-5 (avg -12)
└── Common Issues Found:
    ├── 15% games: overcapture by leader
    ├── 8% games: zero streak violations
    └── 5% games: suboptimal opener usage
```

## Bug Report Format

### Example Bug Report
```markdown
BUG-001: Aggressive Declaration with Weak Hand

Severity: High
Frequency: 12/100 games
First Seen: Game #34, Bot 2, Round 2

Description:
Bot declares 4+ piles with no openers and weak combos

Reproduction:
- Hand: [SOLDIER_BLACK, SOLDIER_RED, CAR_BLACK, CAR_RED, HORSE_BLACK, CANNON_BLACK]
- Position: 2nd
- Previous declarations: [3]
- Bot declared: 4
- Actual captured: 1
- Result: -15 points for round

Root Cause:
AI counts all pairs as viable, ignoring field strength

Fix Suggestion:
Adjust viable combo thresholds based on field strength
```

## Continuous Improvement Process

1. **Run Simulations**: 100+ games with current AI
2. **Identify Patterns**: Use analysis tools to find issues
3. **Prioritize Fixes**: Focus on high-frequency, high-impact bugs
4. **Test Changes**: Run before/after comparisons
5. **Validate Improvements**: Ensure fixes don't create new issues
6. **Document Learning**: Add insights to AI knowledge base

## Questions to Answer

### Strategic Questions
1. What is optimal declaration strategy by position?
2. When should bots play aggressively vs conservatively?
3. How to balance short-term vs long-term gains?
4. What indicates a "must-win" situation?

### Technical Questions
1. Why do certain decisions take longer?
2. Are there memory leaks in long simulations?
3. Which calculations could be cached?
4. How to reduce decision tree complexity?

### Game Balance Questions
1. Is first player advantage too strong?
2. Are certain piece combinations overpowered?
3. Should weak hand redeal rules be adjusted?
4. Is the scoring system balanced?

This data-driven approach will lead to continuous AI improvements and a better game experience.
