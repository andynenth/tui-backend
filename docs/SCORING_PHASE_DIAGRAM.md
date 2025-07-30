# Scoring Phase Diagrams

## Overview
The Scoring Phase calculates points based on declared vs actual pile counts, applies bonuses/penalties, handles redeal multipliers, and determines game completion. This phase implements the core scoring mechanics that drive strategic gameplay.

## Main Flow Diagram

```mermaid
flowchart TD
    Start([Scoring Phase Start<br/>All hands empty]) --> CollectData[Collect round data<br/>Declared vs Actual piles<br/>for each player]
    
    CollectData --> CalculateBase[Calculate base scores<br/>for each player]
    
    CalculateBase --> CheckDeclared{Player declared 0?}
    
    CheckDeclared -->|Yes| CheckActual{Got 0 piles?}
    CheckDeclared -->|No| CheckPerfect{Declared = Actual?}
    
    CheckActual -->|Yes| BonusScore[+3 bonus points<br/>Perfect zero prediction]
    CheckActual -->|No| PenaltyScore[-actual piles<br/>Broke zero declaration]
    
    CheckPerfect -->|Yes| PerfectScore[Declared + 5 bonus points<br/>Perfect prediction]
    CheckPerfect -->|No| MissScore[-abs difference<br/>Missed target penalty]
    
    BonusScore --> ApplyMultiplier
    PenaltyScore --> ApplyMultiplier
    PerfectScore --> ApplyMultiplier
    MissScore --> ApplyMultiplier{Redeal occurred<br/>this round?}
    
    ApplyMultiplier -->|Yes| MultiplyScore[Multiply by redeal multiplier<br/>×2, ×3, ×4, etc.]
    ApplyMultiplier -->|No| UpdateTotals[Update total scores<br/>for each player]
    
    MultiplyScore --> UpdateTotals
    
    UpdateTotals --> ShowSummary[Display round summary<br/>Score breakdown for each player]
    
    ShowSummary --> CheckWin{Anyone ≥ 50 points?}
    
    CheckWin -->|Yes| GameWon[Game Over<br/>Declare winner]
    CheckWin -->|No| NextRound[Start next round<br/>→ Preparation Phase]
    
    GameWon --> End([Game Complete])
    NextRound --> PrepNext([Next Round<br/>→ Preparation Phase])
    
    %% Styling
    style Start fill:#e1f5fe
    style End fill:#e8f5e8
    style PrepNext fill:#e8f5e8
    style BonusScore fill:#c8e6c9
    style PerfectScore fill:#a5d6a7
    style PenaltyScore fill:#ffcdd2
    style MissScore fill:#ffab91
    style MultiplyScore fill:#fff59d
    style GameWon fill:#ffd54f
```

## State Machine Diagram

```mermaid
stateDiagram-v2
    [*] --> CollectingData
    CollectingData --> ProcessingPlayers : Data collected
    
    ProcessingPlayers --> EvaluatingZeroDeclaration : Player declared 0
    ProcessingPlayers --> EvaluatingPerfectMatch : Player declared > 0
    
    EvaluatingZeroDeclaration --> ApplyingBonus : Got 0 piles (perfect)
    EvaluatingZeroDeclaration --> ApplyingPenalty : Got > 0 piles (failed)
    
    EvaluatingPerfectMatch --> ApplyingPerfectBonus : Declared = Actual
    EvaluatingPerfectMatch --> ApplyingMissPenalty : Declared ≠ Actual
    
    ApplyingBonus --> CheckingMultiplier : +3 points applied
    ApplyingPenalty --> CheckingMultiplier : -actual points applied
    ApplyingPerfectBonus --> CheckingMultiplier : +declared+5 points applied
    ApplyingMissPenalty --> CheckingMultiplier : -difference applied
    
    CheckingMultiplier --> ApplyingMultiplier : Redeal occurred
    CheckingMultiplier --> UpdatingTotals : No redeal
    ApplyingMultiplier --> UpdatingTotals : Multiplier applied
    
    UpdatingTotals --> ProcessingPlayers : More players remain
    UpdatingTotals --> ShowingResults : All players processed
    
    ShowingResults --> CheckingWinCondition : Results displayed
    CheckingWinCondition --> GameComplete : Winner found (≥50)
    CheckingWinCondition --> NextRound : No winner yet
    
    GameComplete --> [*]
    NextRound --> [*]
```

## Scoring Algorithm Flowchart

```mermaid
flowchart TD
    PlayerData[Player: Declared=2, Actual=3] --> ZeroCheck{Declared = 0?}
    
    ZeroCheck -->|No| PerfectCheck{Declared = Actual?}
    ZeroCheck -->|Yes| ZeroActual{Actual = 0?}
    
    ZeroActual -->|Yes| ZeroBonus[Score = +3]
    ZeroActual -->|No| ZeroPenalty[Score = -Actual]
    
    PerfectCheck -->|Yes| PerfectBonus[Score = Declared + 5]
    PerfectCheck -->|No| MissPenalty[Score = -|Declared - Actual|]
    
    ZeroBonus --> MultCheck
    ZeroPenalty --> MultCheck
    PerfectBonus --> MultCheck
    MissPenalty --> MultCheck{Redeal Multiplier?}
    
    MultCheck -->|Yes| ApplyMult[Score × Multiplier]
    MultCheck -->|No| FinalScore[Final Score]
    
    ApplyMult --> FinalScore
    
    %% Example calculation
    MissPenalty --> ExampleCalc[Score = -|2 - 3| = -1]
    ExampleCalc --> MultCheck
    
    style ZeroBonus fill:#c8e6c9
    style PerfectBonus fill:#a5d6a7
    style ZeroPenalty fill:#ffcdd2
    style MissPenalty fill:#ffab91
    style ApplyMult fill:#fff59d
```

## Sequence Diagram - Scoring Calculation

```mermaid
sequenceDiagram
    participant GM as Game Manager
    participant P1 as Player 1<br/>(Decl:2, Act:2)
    participant P2 as Player 2<br/>(Decl:0, Act:0)
    participant P3 as Player 3<br/>(Decl:3, Act:1)
    participant P4 as Player 4<br/>(Decl:1, Act:3)
    participant Scorer as Scoring System
    participant UI as User Interface
    
    GM->>Scorer: Begin scoring phase
    GM->>Scorer: Round data (Multiplier: 2x from redeal)
    
    loop For each player
        GM->>Scorer: Process P1 (Declared:2, Actual:2)
        Scorer->>Scorer: Perfect match! Score = 2 + 5 = 7
        Scorer->>Scorer: Apply 2x multiplier: 7 × 2 = 14
        
        GM->>Scorer: Process P2 (Declared:0, Actual:0)
        Scorer->>Scorer: Perfect zero! Score = +3
        Scorer->>Scorer: Apply 2x multiplier: 3 × 2 = 6
        
        GM->>Scorer: Process P3 (Declared:3, Actual:1)
        Scorer->>Scorer: Miss penalty: Score = -|3-1| = -2
        Scorer->>Scorer: Apply 2x multiplier: -2 × 2 = -4
        
        GM->>Scorer: Process P4 (Declared:1, Actual:3)
        Scorer->>Scorer: Miss penalty: Score = -|1-3| = -2
        Scorer->>Scorer: Apply 2x multiplier: -2 × 2 = -4
    end
    
    Scorer->>GM: Round scores calculated
    GM->>UI: Display round summary
    
    Note over UI: P1: +14 pts, P2: +6 pts, P3: -4 pts, P4: -4 pts
    
    GM->>GM: Update total scores
    GM->>GM: Check win condition (≥50 points)
    GM->>GM: No winner yet, continue to next round
    GM->>UI: Start next round preparation
```

## Scoring Rules Reference

### Base Scoring Rules

| Scenario | Calculation | Example |
|----------|-------------|---------|
| **Perfect Zero** | Declared 0, Got 0 | +3 points |
| **Failed Zero** | Declared 0, Got X | -X points |
| **Perfect Match** | Declared = Actual | Declared + 5 points |
| **Miss Penalty** | Declared ≠ Actual | -\|Declared - Actual\| points |

### Multiplier Application

```mermaid
graph TD
    BaseScore[Base Score Calculated] --> MultCheck{Redeal This Round?}
    MultCheck -->|No| FinalScore[Final Score = Base Score]
    MultCheck -->|Yes| GetMult[Get Redeal Multiplier]
    GetMult --> Apply[Final Score = Base Score × Multiplier]
    Apply --> FinalScore
    
    style FinalScore fill:#e8f5e8
    style Apply fill:#fff59d
```

### Win Condition

- **Target**: First player to reach **≥50 total points**
- **Check Timing**: After each round's scoring
- **Tie Resolution**: Multiple players can win simultaneously
- **Game End**: Immediate upon reaching 50+ points

## Example Scoring Scenarios

### Scenario 1: Perfect Round
- **Player**: Declared 3, Actual 3, Multiplier 1x
- **Calculation**: 3 + 5 = 8 points
- **Result**: +8 points

### Scenario 2: Zero Success with Multiplier
- **Player**: Declared 0, Actual 0, Multiplier 3x
- **Calculation**: 3 × 3 = 9 points
- **Result**: +9 points

### Scenario 3: Major Miss with Penalty
- **Player**: Declared 1, Actual 5, Multiplier 2x
- **Calculation**: -|1-5| × 2 = -8 points
- **Result**: -8 points

### Scenario 4: Failed Zero
- **Player**: Declared 0, Actual 2, Multiplier 1x
- **Calculation**: -2 points
- **Result**: -2 points

## Error Conditions

- **Invalid Declaration Data**: Missing or corrupted declaration records
- **Invalid Actual Data**: Pile counts don't match game state
- **Multiplier Error**: Invalid or missing redeal multiplier
- **Score Overflow**: Player score exceeds system limits
- **Win Detection Failure**: Multiple winners not handled properly