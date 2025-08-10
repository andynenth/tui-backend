# Round 8 Complete Play History - Room EBA96B

## Initial State
- **Round Starter**: Bot 2 (won last turn from round 7)
- **Scores at Start**: Alexanderium: 13, Bot 2: 2, Bot 3: -1, Bot 4: 13

## Hands Dealt
- **Bot 2**: ELEPHANT_BLACK(9), CANNON_RED(4), ADVISOR_RED(12), HORSE_BLACK(5), ADVISOR_BLACK(11), CANNON_BLACK(3), SOLDIER_BLACK(1), CHARIOT_BLACK(7)
- **Bot 3**: ELEPHANT_RED(10), ADVISOR_BLACK(11), SOLDIER_BLACK(1), CANNON_BLACK(3), CHARIOT_RED(8), SOLDIER_BLACK(1), CHARIOT_BLACK(7), CHARIOT_RED(8)
- **Bot 4**: HORSE_BLACK(5), SOLDIER_RED(2), SOLDIER_RED(2), ELEPHANT_RED(10), SOLDIER_RED(2), SOLDIER_RED(2), GENERAL_BLACK(13), CANNON_RED(4)
- **Alexanderium**: ELEPHANT_BLACK(9), HORSE_RED(6), SOLDIER_BLACK(1), SOLDIER_RED(2), HORSE_RED(6), ADVISOR_RED(12), SOLDIER_BLACK(1), GENERAL_RED(14)

## Declaration Phase
- **Bot 2 declared**: 5
- **Bot 3 declared**: 3
- **Bot 4 declared**: 5
- **Alexanderium declared**: 4
- **Total declared**: 17 (not equal to 8, as required by rules)

## Turn-by-Turn Play History

### Turn 1
- **Bot 2** (starter): HORSE_BLACK(5), CANNON_BLACK(3), CHARIOT_BLACK(7) - Total: 15 points
- **Bot 3**: ELEPHANT_RED(10), CHARIOT_RED(8), CHARIOT_RED(8) - Total: 26 points
- **Bot 4**: ELEPHANT_RED(10), HORSE_BLACK(5), CANNON_RED(4) - Total: 19 points
- **Alexanderium**: ELEPHANT_BLACK(9), HORSE_RED(6), HORSE_RED(6) - Total: 21 points
- **Winner**: Bot 2 (played 3 pieces, others had to match)

### Turn 2
- Details not shown in extract, but **Winner**: Bot 2

### Turn 3
- **Bot 2**: ELEPHANT_BLACK(9) - Single piece
- **Bot 3**: ADVISOR_BLACK(11) - Single piece
- **Bot 4**: SOLDIER_RED(2) - Single piece
- **Alexanderium**: GENERAL_RED(14) - Single piece
- **Winner**: Alexanderium (highest single piece)

### Turn 4
- Details not shown in extract, but **Winner**: Alexanderium

### Turn 5
- **Alexanderium**: ADVISOR_RED(12) - Single piece
- **Bot 2**: CANNON_RED(4) - Single piece
- **Bot 3**: CHARIOT_BLACK(7) - Single piece
- **Bot 4**: GENERAL_BLACK(13) - Single piece
- **Winner**: Bot 4 (GENERAL_BLACK beats ADVISOR_RED)

### Turn 6
- Details not shown in extract, but **Winner**: Bot 4

### Turn 7
- **Bot 4**: SOLDIER_RED(2), SOLDIER_RED(2), SOLDIER_RED(2) - 3 pieces
- **Alexanderium**: SOLDIER_RED(2), SOLDIER_BLACK(1), SOLDIER_BLACK(1) - 3 pieces
- **Bot 2**: SOLDIER_BLACK(1), ADVISOR_BLACK(11), ADVISOR_RED(12) - 3 pieces
- **Bot 3**: CANNON_BLACK(3), SOLDIER_BLACK(1), SOLDIER_BLACK(1) - 3 pieces
- **Winner**: Bot 4 (played first with 3 pieces)

### Turn 8
- Details not shown in extract, but **Winner**: Bot 4

## Final Results
- **Bot 2**: Won 2 turns (Turn 1, Turn 2) = 2 piles → Actually captured 3 piles
- **Alexanderium**: Won 2 turns (Turn 3, Turn 4) = 2 piles
- **Bot 4**: Won 4 turns (Turn 5, Turn 6, Turn 7, Turn 8) = 4 piles
- **Bot 3**: Won 0 turns = 0 piles

## Analysis of Bot 2's Declaration
Bot 2 declared 5 but only captured 3 piles. Looking at the plays:
1. Bot 2 used their strong opening pieces (ADVISOR_BLACK(11) and ADVISOR_RED(12)) in Turn 7 when forced to match 3 pieces
2. This wasted their best pieces in a turn they didn't win
3. Bot 2's strategy of expecting 5 piles failed because:
   - They only won the first 2 turns
   - Their high-value "opener" pieces were used defensively rather than to win turns
   - Bot 4 dominated the later turns with better piece management

The fixed 11+ point threshold for openers doesn't account for tactical play where high-value pieces might be forced out in defensive plays rather than used to win piles.