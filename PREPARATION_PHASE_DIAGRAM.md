flowchart TD
    Start([Game Start]) --> Deal[Deal 8 pieces to each player]
    
    Deal --> CheckWeak{Check for weak hands<br/>No piece > 9 points}
    
    CheckWeak -->|No weak hands| DetermineStarter[Determine Starter]
    CheckWeak -->|Weak hands found| RedealPhase[Redeal Phase]
    
    RedealPhase --> WeakPlayer{Weak player decides}
    WeakPlayer -->|Accept redeal| Redeal[Execute Redeal]
    WeakPlayer -->|Decline| NextWeak{More weak players?}
    
    NextWeak -->|Yes| WeakPlayer
    NextWeak -->|All declined| DetermineStarter
    
    Redeal --> Multiplier[Increase multiplier<br/>2x → 3x → 4x...]
    Multiplier --> Reshuffle[Reshuffle & redeal all hands]
    Reshuffle --> Deal
    
    DetermineStarter --> StarterRule{Starter rules}
    StarterRule -->|Round 1| RedGeneral[Player with GENERAL_RED]
    StarterRule -->|After redeal| RedealRequester[Redeal requester starts]
    StarterRule -->|Other rounds| LastWinner[Previous round's final turn winner]
    
    RedGeneral --> Complete
    RedealRequester --> Complete
    LastWinner --> Complete
    
    Complete([Preparation Complete<br/>→ Declaration Phase])