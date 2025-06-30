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
    
    style BonusScore fill:#90EE90
    style PerfectScore fill:#98FB98
    style PenaltyScore fill:#FFB6C1
    style MissScore fill:#FFA07A
    style MultiplyScore fill:#F0E68C
    style GameWon fill:#FFD700