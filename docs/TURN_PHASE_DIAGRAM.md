# Turn Phase Diagrams

## Overview
The Turn Phase is the core gameplay where players compete by playing pieces. The starter determines the number of pieces for each turn, and the winner takes piles while becoming the next starter. This continues until all hands are empty.

## Main Flow Diagram

```mermaid
flowchart TD
    Start([Turn Phase Start]) --> SetStarter[Set first turn starter<br/>Based on round starter]
    
    SetStarter --> NewTurn[Start new turn]
    
    NewTurn --> StarterPlay[Starter plays 1-6 pieces]
    
    StarterPlay --> ValidateStarter{Starter's play valid?}
    
    ValidateStarter -->|Invalid| StarterMustRetry[Starter must play again<br/>Turn cannot start with invalid play]
    ValidateStarter -->|Valid| SetPieceCount[Set required piece count<br/>for this turn]
    
    StarterMustRetry --> StarterPlay
    
    SetPieceCount --> OthersPlay[Other players must play<br/>same number of pieces]
    
    OthersPlay --> CollectPlays[Collect all player plays]
    
    CollectPlays --> AllPlayed{All players have played?}
    
    AllPlayed -->|No| WaitForNext[Wait for next player]
    WaitForNext --> OthersPlay
    
    AllPlayed -->|Yes| DetermineWinner[Determine winner<br/>Highest total piece value]
    
    DetermineWinner --> WinnerTakesPiles[Winner gets piles equal to<br/>number of pieces played]
    
    WinnerTakesPiles --> UpdateScore[Update winner's pile count]
    
    UpdateScore --> CheckNextTurn{Players have more pieces?}
    
    CheckNextTurn -->|Yes| NextTurnStarter[Winner starts next turn]
    CheckNextTurn -->|No| RoundComplete[All hands empty<br/>→ Scoring Phase]
    
    NextTurnStarter --> NewTurn
    
    RoundComplete --> End([Turn Phase Complete<br/>→ Scoring Phase])
    
    %% Styling
    style Start fill:#e1f5fe
    style End fill:#e8f5e8
    style StarterMustRetry fill:#ffcdd2
    style RoundComplete fill:#c8e6c9
    style WinnerTakesPiles fill:#fff59d
```

## State Machine Diagram

```mermaid
stateDiagram-v2
    [*] --> InitializingTurn
    InitializingTurn --> WaitingForStarter : Turn started
    
    WaitingForStarter --> ValidatingStarterPlay : Starter played
    ValidatingStarterPlay --> WaitingForStarter : Invalid play
    ValidatingStarterPlay --> WaitingForOthers : Valid play
    
    WaitingForOthers --> CollectingPlays : Player played
    CollectingPlays --> WaitingForOthers : More players needed
    CollectingPlays --> DeterminingWinner : All played
    
    DeterminingWinner --> DistributingPiles : Winner determined
    DistributingPiles --> CheckingHandsEmpty : Piles distributed
    
    CheckingHandsEmpty --> InitializingTurn : Hands not empty
    CheckingHandsEmpty --> Complete : All hands empty
    
    Complete --> [*]
```

## Sequence Diagram - Single Turn

```mermaid
sequenceDiagram
    participant GM as Game Manager
    participant P1 as Player 1 (Starter)
    participant P2 as Player 2
    participant P3 as Player 3
    participant P4 as Player 4
    participant Judge as Turn Judge
    participant UI as User Interface
    
    GM->>P1: You start this turn
    P1->>GM: I play 2 pieces: [GENERAL_RED, 12]
    GM->>Judge: Validate starter play
    Judge->>Judge: 2 pieces, valid combination
    Judge->>GM: Valid play (2 pieces required)
    
    GM->>UI: Turn requires 2 pieces each
    GM->>P2: Play 2 pieces
    P2->>GM: I play: [11, 9] (total: 20)
    
    GM->>P3: Play 2 pieces
    P3->>GM: I play: [10, 8] (total: 18)
    
    GM->>P4: Play 2 pieces
    P4->>GM: I play: [13, 7] (total: 20)
    
    GM->>Judge: Determine winner
    Judge->>Judge: P1: GENERAL_RED + 12 = 25 (generals beat numbers)
    Judge->>Judge: P2: 11 + 9 = 20
    Judge->>Judge: P3: 10 + 8 = 18  
    Judge->>Judge: P4: 13 + 7 = 20
    Judge->>GM: P1 wins with GENERAL_RED
    
    GM->>P1: You win! Take 2 piles
    GM->>GM: Update P1 pile count (+2)
    GM->>UI: Display turn results
    GM->>P1: You start the next turn
```

## Sequence Diagram - Complete Turn Phase

```mermaid
sequenceDiagram
    participant GM as Game Manager
    participant P1 as Player 1
    participant P2 as Player 2
    participant P3 as Player 3
    participant P4 as Player 4
    participant UI as User Interface
    
    GM->>GM: Turn Phase starts (P2 is round starter)
    
    %% Turn 1
    Note over GM,UI: Turn 1
    GM->>P2: Start turn 1
    P2->>GM: Play 3 pieces
    GM->>P1: Play 3 pieces
    GM->>P3: Play 3 pieces  
    GM->>P4: Play 3 pieces
    GM->>GM: P3 wins, gets 3 piles
    
    %% Turn 2
    Note over GM,UI: Turn 2
    GM->>P3: Start turn 2 (you won last turn)
    P3->>GM: Play 1 piece
    GM->>P4: Play 1 piece
    GM->>P1: Play 1 piece
    GM->>P2: Play 1 piece
    GM->>GM: P1 wins, gets 1 pile
    
    %% Turn 3
    Note over GM,UI: Turn 3
    GM->>P1: Start turn 3
    P1->>GM: Play 4 pieces (last 4 pieces)
    GM->>P2: Play 4 pieces (last 4 pieces)
    GM->>P3: Play 4 pieces (last 4 pieces)
    GM->>P4: Play 4 pieces (last 4 pieces)
    GM->>GM: P4 wins, gets 4 piles
    
    GM->>GM: All hands empty
    GM->>UI: Turn Phase complete
    GM->>GM: Transition to Scoring Phase
```

## Turn Resolution Algorithm

```mermaid
flowchart TD
    AllPlayed[All players have played] --> CompareValues[Compare total piece values]
    
    CompareValues --> CheckGenerals{Any generals played?}
    
    CheckGenerals -->|Yes| GeneralWins[General pieces beat<br/>all number pieces]
    CheckGenerals -->|No| CompareNumbers[Compare number totals]
    
    GeneralWins --> MultipleGenerals{Multiple generals?}
    MultipleGenerals -->|Yes| HighestGeneral[Highest value general wins<br/>RED > BLACK]
    MultipleGenerals -->|No| SingleWinner[Single general winner]
    
    CompareNumbers --> CheckTies{Tied totals?}
    CheckTies -->|Yes| TieBreaker[Tie broken by<br/>highest single piece]
    CheckTies -->|No| HighestTotal[Highest total wins]
    
    HighestGeneral --> Winner
    SingleWinner --> Winner
    TieBreaker --> Winner
    HighestTotal --> Winner[Declare winner]
    
    Winner --> AwardPiles[Winner gets piles =<br/>number of pieces played]
    AwardPiles --> UpdateCounts[Update pile counts]
    
    style Winner fill:#fff59d
    style AwardPiles fill:#c8e6c9
```

## Piece Value Hierarchy

```mermaid
graph TD
    subgraph "Generals (Always Win)"
        GENRED[GENERAL_RED<br/>Highest Priority]
        GENBLK[GENERAL_BLACK<br/>Second Priority]
    end
    
    subgraph "Number Pieces"
        N13[13 - Highest]
        N12[12]
        N11[11]
        N10[10]
        N9[9]
        N8[8]
        N7[7]
        N6[6]
        N5[5]
        N4[4]
        N3[3]
        N2[2]
        N1[1 - Lowest]
    end
    
    GENRED --> GENBLK
    GENBLK --> N13
    N13 --> N12
    N12 --> N11
    N11 --> N10
    N10 --> N9
    N9 --> N8
    N8 --> N7
    N7 --> N6
    N6 --> N5
    N5 --> N4
    N4 --> N3
    N3 --> N2
    N2 --> N1
    
    style GENRED fill:#ffcdd2
    style GENBLK fill:#e0e0e0
```

## Turn Examples

### Example 1: General vs Numbers
- **P1**: GENERAL_RED (value: special)
- **P2**: 13 + 12 = 25
- **P3**: 11 + 10 = 21  
- **P4**: 9 + 8 = 17
- **Winner**: P1 (generals always beat numbers)

### Example 2: Number Competition
- **P1**: 11 + 10 = 21
- **P2**: 13 + 7 = 20
- **P3**: 12 + 9 = 21 (tie!)
- **P4**: 8 + 6 = 14
- **Tie Breaker**: P1 has 11, P3 has 12 → P3 wins (highest single piece)

### Example 3: Multiple Generals
- **P1**: GENERAL_BLACK
- **P2**: 13 + 12 = 25
- **P3**: GENERAL_RED
- **P4**: 11 + 10 = 21
- **Winner**: P3 (GENERAL_RED beats GENERAL_BLACK)

## Game Flow Rules

### Starter Rules
1. **First Turn**: Round starter (from Preparation Phase)
2. **Subsequent Turns**: Previous turn winner
3. **Invalid Play**: Starter must replay until valid

### Piece Count Rules
1. **Starter Choice**: 1-6 pieces (or remaining hand size)
2. **Others Must Match**: Exact same number of pieces
3. **No Choice**: Once starter plays, count is fixed

### Winning Rules
1. **Generals**: Always beat number pieces
2. **General Hierarchy**: RED > BLACK
3. **Number Competition**: Highest total wins
4. **Tie Breaking**: Highest single piece value

### Pile Distribution
- **Winner Gets**: Number of piles = pieces played per person
- **Example**: 3-piece turn → winner gets 3 piles
- **Accumulation**: Piles accumulate for final scoring

## Error Conditions

- **Invalid Starter Play**: Starter plays invalid piece combination
- **Wrong Piece Count**: Player plays ≠ required pieces
- **Invalid Pieces**: Player plays pieces they don't have
- **Turn Resolution Error**: Cannot determine winner
- **Pile Distribution Error**: Incorrect pile count assignment