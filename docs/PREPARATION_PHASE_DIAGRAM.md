# Preparation Phase Diagrams

## Overview
The Preparation Phase handles initial game setup, piece dealing, weak hand detection, redeal mechanics, and starter determination. This phase ensures fair gameplay by allowing players with weak hands to request redeals.

## Main Flow Diagram

```mermaid
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
    
    %% Styling
    style Start fill:#e1f5fe
    style Complete fill:#e8f5e8
    style Redeal fill:#fff3e0
    style Multiplier fill:#f3e5f5
    style RedGeneral fill:#ffcdd2
    style RedealRequester fill:#ffcdd2
    style LastWinner fill:#ffcdd2
```

## State Machine Diagram

```mermaid
stateDiagram-v2
    [*] --> Dealing
    Dealing --> CheckingWeakHands : All hands dealt
    
    CheckingWeakHands --> RedealDecision : Weak hands found
    CheckingWeakHands --> DeterminingStarter : No weak hands
    
    RedealDecision --> ExecutingRedeal : Player accepts redeal
    RedealDecision --> CheckingNextWeak : Player declines
    RedealDecision --> DeterminingStarter : All players declined
    
    CheckingNextWeak --> RedealDecision : More weak players
    CheckingNextWeak --> DeterminingStarter : No more weak players
    
    ExecutingRedeal --> IncreasingMultiplier : Redeal approved
    IncreasingMultiplier --> Reshuffling : Multiplier updated
    Reshuffling --> Dealing : Cards reshuffled
    
    DeterminingStarter --> Complete : Starter determined
    Complete --> [*]
```

## Sequence Diagram - Normal Flow (No Weak Hands)

```mermaid
sequenceDiagram
    participant GM as Game Manager
    participant Deck as Deck System
    participant P1 as Player 1
    participant P2 as Player 2
    participant P3 as Player 3
    participant P4 as Player 4
    participant UI as User Interface
    
    GM->>Deck: Shuffle deck
    GM->>Deck: Deal 8 pieces to each player
    
    Deck->>P1: Your hand (8 pieces)
    Deck->>P2: Your hand (8 pieces)
    Deck->>P3: Your hand (8 pieces)
    Deck->>P4: Your hand (8 pieces)
    
    GM->>GM: Check for weak hands
    Note over GM: No players have all pieces ≤ 9 points
    
    GM->>GM: Determine starter (Round 1)
    GM->>P2: You have GENERAL_RED, you start
    
    GM->>UI: Display preparation complete
    GM->>UI: Highlight P2 as round starter
    GM->>GM: Transition to Declaration Phase
```

## Sequence Diagram - Redeal Flow

```mermaid
sequenceDiagram
    participant GM as Game Manager
    participant Deck as Deck System
    participant P1 as Player 1 (Weak)
    participant P3 as Player 3 (Weak)
    participant P2 as Player 2
    participant P4 as Player 4
    participant UI as User Interface
    
    GM->>Deck: Deal initial hands
    GM->>GM: Check for weak hands
    GM->>GM: Found weak hands: P1, P3
    
    GM->>P1: You have a weak hand. Request redeal?
    P1->>GM: Yes, I request redeal
    GM->>GM: P1 accepted redeal
    
    GM->>P3: P1 requested redeal. Do you also want redeal?
    P3->>GM: No, I'll keep my hand
    GM->>GM: P3 declined redeal
    
    GM->>GM: Execute redeal (multiplier: 1x → 2x)
    GM->>Deck: Reshuffle all cards
    GM->>Deck: Deal new hands to all players
    
    Deck->>P1: New hand (8 pieces)
    Deck->>P2: New hand (8 pieces) 
    Deck->>P3: New hand (8 pieces)
    Deck->>P4: New hand (8 pieces)
    
    GM->>GM: Check for weak hands again
    Note over GM: No weak hands in new deal
    
    GM->>GM: Determine starter (after redeal)
    GM->>P1: You requested redeal, you start
    
    GM->>UI: Display redeal complete (2x multiplier)
    GM->>UI: Highlight P1 as round starter
    GM->>GM: Transition to Declaration Phase
```

## Redeal Mechanics

### Weak Hand Definition
A weak hand contains **no pieces with value > 9 points**:
- Contains only: 1-9 point pieces
- Missing: 10, 11, 12, 13, General pieces

### Redeal Process
1. **Detection**: Identify all players with weak hands
2. **Decision**: Each weak player decides independently
3. **Execution**: If any player accepts, redeal for everyone
4. **Multiplier**: Increase score multiplier (2x, 3x, 4x...)
5. **Restart**: Return to dealing phase with new multiplier

### Starter Determination Rules

| Condition | Starter |
|-----------|---------|
| Round 1, no redeal | Player with GENERAL_RED piece |
| After redeal | Player who requested the redeal |
| Subsequent rounds | Winner of previous round's final turn |

## Multiplier System

```mermaid
graph LR
    Initial[1x multiplier] -->|First redeal| Double[2x multiplier]
    Double -->|Second redeal| Triple[3x multiplier]
    Triple -->|Third redeal| Quad[4x multiplier]
    Quad -->|Additional redeals| Increment[+1x each redeal]
    
    style Initial fill:#e8f5e8
    style Double fill:#fff3e0
    style Triple fill:#ffebee
    style Quad fill:#f3e5f5
```

## Error Conditions

- **Invalid Hand Size**: Player receives ≠ 8 pieces
- **Deck Exhaustion**: Not enough cards for redeal (should never happen)
- **Missing GENERAL_RED**: No player has GENERAL_RED in Round 1
- **Invalid Starter**: Cannot determine starter based on rules