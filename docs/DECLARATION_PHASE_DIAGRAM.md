flowchart TD
    Start([Declaration Phase Start]) --> SetOrder[Set declaration order<br/>Starting from round starter]
    
    SetOrder --> NextPlayer[Next player's turn]
    
    NextPlayer --> CheckRestrictions{Check player restrictions}
    
    CheckRestrictions --> ZeroStreak{Declared 0<br/>twice in a row?}
    ZeroStreak -->|Yes| ForceNonZero[Must declare ≥1]
    ZeroStreak -->|No| CheckLastPlayer{Is last player?}
    
    ForceNonZero --> MakeDeclaration
    
    CheckLastPlayer -->|Yes| CheckTotal{Current total<br/>+ declaration = 8?}
    CheckLastPlayer -->|No| MakeDeclaration[Player makes declaration<br/>Choose 0-8 piles]
    
    CheckTotal -->|Yes| ForbidValue[Forbidden: Cannot make<br/>total exactly 8]
    CheckTotal -->|No| MakeDeclaration
    
    ForbidValue --> MakeDeclaration
    
    MakeDeclaration --> ValidateDeclaration{Valid choice?}
    
    ValidateDeclaration -->|Invalid| ShowError[Show error message]
    ShowError --> MakeDeclaration
    
    ValidateDeclaration -->|Valid| RecordDeclaration[Record player's declaration]
    
    RecordDeclaration --> UpdateUI[Update UI with declaration]
    
    UpdateUI --> AllDeclared{All players<br/>declared?}
    
    AllDeclared -->|No| NextPlayer
    AllDeclared -->|Yes| ShowSummary[Show declaration summary]
    
    ShowSummary --> ValidateTotal{Total ≠ 8?}
    
    ValidateTotal -->|Total = 8| Error[ERROR: Invalid total<br/>Should not happen!]
    ValidateTotal -->|Total ≠ 8| Complete([Declaration Complete<br/>→ Turn Phase])
    
    Error --> Complete