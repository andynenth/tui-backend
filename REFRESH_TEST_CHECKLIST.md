# Comprehensive Refresh Test Checklist

## Test Execution Plan
Test every possible game state and action point by refreshing the browser and verifying state restoration.

## 1. PREPARATION PHASE
- [ ] Initial preparation phase (before any cards dealt)
- [ ] During card dealing animation
- [ ] After cards dealt, before weak hand check
- [ ] During weak hand dialog (if applicable)
- [ ] After weak hand resolution

## 2. DECLARATION PHASE  
- [ ] Initial declaration phase (before any declarations)
- [ ] After 1 player declared
- [ ] After 2 players declared
- [ ] After 3 players declared (before last player)
- [ ] During own declaration input
- [ ] After all players declared

## 3. TURN PHASE
- [ ] Before first turn (starter's turn)
- [ ] During piece selection (own turn)
- [ ] After selecting pieces but before playing
- [ ] After playing pieces (waiting for others)
- [ ] During bot player's turn
- [ ] After bot plays (between turns)
- [ ] Middle of round (various turn states)
- [ ] Last turn of round

## 4. SCORING PHASE
- [ ] Initial score display
- [ ] During score animation
- [ ] After viewing scores (before next round)
- [ ] During round transition

## 5. SPECIAL CASES
- [ ] During weak hand redeal vote
- [ ] After accepting/declining redeal
- [ ] During game end (winner announcement)
- [ ] With different player positions (1st, 2nd, 3rd, 4th)
- [ ] With different game states (winning, losing, tied)

## Test Verification Points
For each refresh test, verify:
1. Correct phase is displayed
2. Player hand is visible and correct
3. Game state matches pre-refresh state
4. Turn order is preserved
5. Scores are accurate
6. No "Waiting for Game" error
7. All UI elements functional
8. Can continue playing normally

## Results Format
```
Test Case: [Description]
Pre-Refresh State: [Details]
Post-Refresh State: [Details]  
Result: PASS/FAIL
Issues: [Any problems found]
```