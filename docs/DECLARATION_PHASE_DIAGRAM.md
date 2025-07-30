# Declaration Phase Diagrams

## Overview
The Declaration Phase is where players predict how many piles they will win in the upcoming Turn Phase. This phase includes validation rules to prevent total declarations from equaling exactly 8 piles.

## Main Flow Diagram

```mermaid
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
    
    %% Styling
    style Start fill:#e1f5fe
    style Complete fill:#e8f5e8
    style Error fill:#ffebee
    style ForceNonZero fill:#fff3e0
    style ForbidValue fill:#fff3e0
    style ShowError fill:#ffebee
```

## State Machine Diagram

```mermaid
stateDiagram-v2
    [*] --> WaitingToStart
    WaitingToStart --> PlayerTurn : Start declaration phase
    
    PlayerTurn --> ValidatingRestrictions : Player selected
    ValidatingRestrictions --> PlayerTurn : Zero streak restriction
    ValidatingRestrictions --> PlayerTurn : Last player + total=8 restriction
    ValidatingRestrictions --> MakingDeclaration : No restrictions
    
    MakingDeclaration --> ValidatingChoice : Declaration made
    ValidatingChoice --> MakingDeclaration : Invalid choice
    ValidatingChoice --> RecordingDeclaration : Valid choice
    
    RecordingDeclaration --> CheckingComplete : Declaration recorded
    CheckingComplete --> PlayerTurn : More players remain
    CheckingComplete --> ShowingSummary : All players complete
    
    ShowingSummary --> ValidatingTotal : Summary displayed
    ValidatingTotal --> Complete : Total ≠ 8
    ValidatingTotal --> Error : Total = 8 (should not happen)
    
    Error --> Complete
    Complete --> [*]
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant GM as Game Manager
    participant P1 as Player 1 (Starter)
    participant P2 as Player 2
    participant P3 as Player 3
    participant P4 as Player 4
    participant UI as User Interface
    
    GM->>GM: Initialize declaration phase
    GM->>UI: Set declaration order (P1 first)
    
    loop For each player in order
        GM->>P1: Your turn to declare
        P1->>GM: Check my restrictions
        GM->>P1: Zero streak: No, Last player: No
        P1->>GM: I declare 2 piles
        GM->>GM: Validate declaration (2 is valid)
        GM->>UI: Update display (P1: 2)
        
        GM->>P2: Your turn to declare
        P2->>GM: Check my restrictions
        GM->>P2: Zero streak: No, Last player: No
        P2->>GM: I declare 3 piles
        GM->>GM: Validate declaration (3 is valid)
        GM->>UI: Update display (P1: 2, P2: 3)
        
        GM->>P3: Your turn to declare
        P3->>GM: Check my restrictions
        GM->>P3: Zero streak: No, Last player: No
        P3->>GM: I declare 1 pile
        GM->>GM: Validate declaration (1 is valid)
        GM->>UI: Update display (P1: 2, P2: 3, P3: 1)
        
        GM->>P4: Your turn to declare (LAST PLAYER)
        P4->>GM: Check my restrictions
        GM->>P4: Current total: 6, Cannot declare 2 (would make 8)
        P4->>GM: I declare 1 pile
        GM->>GM: Validate declaration (total = 7, valid)
        GM->>UI: Update display (P1: 2, P2: 3, P3: 1, P4: 1)
    end
    
    GM->>UI: Show declaration summary
    GM->>GM: Validate total ≠ 8 (7 ≠ 8 ✓)
    GM->>GM: Declaration phase complete
    GM->>UI: Transition to Turn Phase
```

## Key Rules

1. **Zero Streak Rule**: Players cannot declare 0 twice in a row
2. **Total ≠ 8 Rule**: The sum of all declarations cannot equal 8
3. **Last Player Restriction**: The final player cannot make a declaration that would cause the total to equal 8
4. **Declaration Range**: Players can declare 0-8 piles
5. **Turn Order**: Declarations follow the same order as the upcoming Turn Phase

## Error Conditions

- **Invalid Range**: Declaration outside 0-8 range
- **Zero Streak Violation**: Attempting to declare 0 twice consecutively
- **Total = 8**: Last player attempting to make total equal 8
- **System Error**: If total somehow equals 8 after validation (should never happen)