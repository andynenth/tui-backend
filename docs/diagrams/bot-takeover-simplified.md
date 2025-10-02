# Bot Takeover Flow - Simplified Alternatives

## Option 1: High-Level State Transition (Recommended)

Simple and clear, focuses on the player's perspective.

```mermaid
graph LR
    subgraph "Normal Play"
        HP[Human Playing]
    end

    subgraph "Disconnect"
        HP -->|Connection Lost| D[Disconnected State]
        D --> SS[State Saved]
        SS --> BA[Bot Activated]
        BA --> BP[Bot Playing]
    end

    subgraph "Reconnect"
        BP -->|Player Returns| RC[Reconnection Check]
        RC --> RS[Restore State]
        RS --> HP2[Human Playing Again]
    end

    style HP fill:#90EE90
    style D fill:#FFB6C1
    style BA fill:#87CEEB
    style BP fill:#87CEEB
    style HP2 fill:#90EE90
```

## Option 2: Timeline View

Shows the seamless transition over time.

```mermaid
gantt
    title Player Connection Timeline
    dateFormat X
    axisFormat %s

    section Human Player
    Active Play           :done, human1, 0, 30
    Reconnected          :done, human2, 70, 30

    section Connection
    Connected            :done, conn1, 0, 30
    Disconnected         :crit, disc, 30, 40
    Connected Again      :done, conn2, 70, 30

    section Bot Control
    Inactive             :done, bot1, 0, 30
    Bot Takes Over       :active, bot2, 30, 40
    Inactive Again       :done, bot3, 70, 30

    section Game State
    Playing              :done, game1, 0, 100
```

## Option 3: Simple Flow Chart

Focus on the key decision point and actions.

```mermaid
flowchart TB
    Start([Player Connected]) --> Playing[Playing Game]
    Playing --> Disconnect{Connection Lost?}

    Disconnect -->|Yes| CheckGame{Game Started?}
    Disconnect -->|No| Playing

    CheckGame -->|Yes| InGame[In-Game Disconnect]
    CheckGame -->|No| PreGame[Pre-Game Disconnect]

    InGame --> SaveState[Save Player State]
    SaveState --> ActivateBot[Bot Takes Control]
    ActivateBot --> BotPlays[Bot Continues Playing]
    BotPlays --> WaitReconnect[Wait for Reconnection]

    PreGame --> RemovePlayer[Remove from Room]
    RemovePlayer --> End([Player Gone])

    WaitReconnect --> Reconnect{Player Returns?}
    Reconnect -->|Yes| RestoreState[Restore Original State]
    Reconnect -->|No| BotPlays
    RestoreState --> Playing

    style InGame fill:#FFE4B5
    style ActivateBot fill:#87CEEB
    style RestoreState fill:#90EE90
```

## Option 4: State Machine Diagram

Clean state representation.

```mermaid
stateDiagram-v2
    [*] --> HumanControl: Join Game

    HumanControl --> BotControl: Disconnect (In-Game)
    HumanControl --> [*]: Disconnect (Pre-Game)

    BotControl --> HumanControl: Reconnect
    BotControl --> RoomCleanup: All Disconnected

    RoomCleanup --> [*]: Timeout

    state HumanControl {
        Human: Human Playing
        Connected: Connected = True
        Bot: is_bot = False
    }

    state BotControl {
        BotActive: Bot Playing
        Disconnected: Connected = False
        BotFlag: is_bot = True
        Preserved: Original State Saved
    }
```

## Option 5: Visual Metaphor

Using icons and minimal text for clarity.

```mermaid
graph TB
    subgraph "1. Normal Play"
        P1[👤 Human Player<br/>Connected]
    end

    subgraph "2. Connection Lost"
        P1 --> D[📵 Disconnected]
        D --> S[💾 State Saved]
        S --> B[🤖 Bot Activated]
    end

    subgraph "3. Game Continues"
        B --> G[🎮 Bot Plays<br/>No Interruption]
    end

    subgraph "4. Player Returns"
        G --> R[🔄 Reconnect]
        R --> P2[👤 Human Restored<br/>Game Continues]
    end

    style P1 fill:#90EE90
    style B fill:#87CEEB
    style P2 fill:#90EE90
    style G fill:#FFE4E1
```

## Recommendation

I recommend **Option 3 (Simple Flow Chart)** because it:
- Shows both disconnect scenarios clearly
- Easy to follow the logic flow
- Highlights the key decision points
- Not overwhelming with technical details
- Still includes all important states

For technical documentation, you could use **Option 1** as a companion diagram showing the high-level state transitions without the implementation details.
