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
    
    AllPlayed -->|Yes| DetermineWinner[Determine winner]
    
    DetermineWinner --> WinnerTakesPiles[Winner gets piles equal to number of pieces played]
    
    WinnerTakesPiles --> UpdateScore[Update winner's pile count]
    
    UpdateScore --> CheckNextTurn{Players have more pieces?}
    
    CheckNextTurn -->|Yes| NextTurnStarter[Winner starts next turn]
    CheckNextTurn -->|No| RoundComplete[All hands empty<br/>→ Scoring Phase]
    
    NextTurnStarter --> NewTurn
    
    RoundComplete --> End([Turn Phase Complete<br/>→ Scoring Phase])
    
    style StarterMustRetry fill:#FFB6C1
    style RoundComplete fill:#90EE90