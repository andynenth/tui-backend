# Bot Architecture Diagram Proposals

## 1. **Bot Decision-Making Flow** (Most Comprehensive)
Shows the complete AI decision process from game state analysis to action execution.

```mermaid
graph TB
    subgraph "Game State Input"
        GS[Game State] --> PE[Phase Evaluator]
        PE --> |Declaration Phase| DE[Declaration Engine]
        PE --> |Turn Phase| TE[Turn Engine]
    end

    subgraph "Analysis Layer"
        DE --> HA[Hand Analyzer]
        HA --> |Strength Score| DS[Declaration Strategy]

        TE --> HS[Hand Strength]
        TE --> BS[Board State]
        TE --> PS[Pile Status]
    end

    subgraph "Strategy Layer"
        DS --> |Target Piles| DP[Declaration Processor]

        HS --> SC[Starter Calculator]
        BS --> RC[Responder Calculator]
        PS --> UC[Urgency Calculator]

        SC --> |If Leading| MC[Move Calculator]
        RC --> |If Responding| MC
        UC --> |Pile Pressure| MC
    end

    subgraph "Decision Layer"
        DP --> |Declaration| EX[Executor]
        MC --> |Best Move| VM[Validator]
        VM --> |Valid Moves| EX
    end

    subgraph "Execution Layer"
        EX --> |Action| GSM[Game State Machine]
        GSM --> |Broadcast| WSB[WebSocket Broadcast]
    end

    style GS fill:#e1f5fe
    style EX fill:#c8e6c9
    style WSB fill:#ffccbc
```

## 2. **Bot Lifecycle Diagram** (Best for Operations)
Shows bot activation, deactivation, and state transitions.

```mermaid
stateDiagram-v2
    [*] --> HumanPlayer: Player Joins

    HumanPlayer --> BotActive: Disconnect
    BotActive --> HumanPlayer: Reconnect

    state HumanPlayer {
        [*] --> Connected
        Connected --> Playing: Game Action
        Playing --> Connected: Action Complete
    }

    state BotActive {
        [*] --> PreservingState
        PreservingState --> TakingControl
        TakingControl --> MakingDecisions
        MakingDecisions --> ExecutingActions
        ExecutingActions --> MakingDecisions: Next Turn

        state PreservingState {
            SaveOriginalBot: original_is_bot = is_bot
            SaveAvatar: original_avatar = avatar_color
            SetBotFlag: is_bot = True
        }

        state MakingDecisions {
            AnalyzeGameState --> CalculateStrategy
            CalculateStrategy --> SelectAction
        }
    }

    BotActive --> RoomCleanup: All Players Disconnected
    RoomCleanup --> [*]: Timeout
```

## 3. **Bot Strategy Matrix** (Best for AI Logic)
Shows different bot personalities and their decision weights.

```mermaid
graph LR
    subgraph "Bot Personalities"
        B1[Bot 1<br/>Aggressive]
        B2[Bot 2<br/>Balanced]
        B3[Bot 3<br/>Conservative]
        B4[Bot 4<br/>Adaptive]
    end

    subgraph "Decision Factors"
        SF[Starter Factor<br/>0-1.0]
        RF[Responder Factor<br/>0-1.0]
        UF[Urgency Factor<br/>0-1.0]
        CF[Combo Factor<br/>0-1.0]
    end

    subgraph "Weights"
        B1 --> |0.8| SF
        B1 --> |0.6| RF
        B1 --> |0.4| UF
        B1 --> |0.9| CF

        B2 --> |0.5| SF
        B2 --> |0.5| RF
        B2 --> |0.5| UF
        B2 --> |0.5| CF

        B3 --> |0.3| SF
        B3 --> |0.7| RF
        B3 --> |0.8| UF
        B3 --> |0.2| CF

        B4 --> |Dynamic| SF
        B4 --> |Dynamic| RF
        B4 --> |Dynamic| UF
        B4 --> |Dynamic| CF
    end
```

## 4. **Bot-Human Interaction Flow** (Best for UX)
Shows how bots interact with human players seamlessly.

```mermaid
sequenceDiagram
    participant H1 as Human 1
    participant H2 as Human 2
    participant B3 as Bot 3 (was Human)
    participant B4 as Bot 4
    participant GS as Game Server

    H1->>GS: Play pieces
    GS->>H1: Update game state
    GS->>H2: Broadcast update
    GS->>B3: Broadcast update
    GS->>B4: Broadcast update

    Note over H2: Disconnects
    GS->>B3: Human 2 disconnected
    Note over H2: Bot takes over

    B3->>GS: Calculate move (300ms delay)
    GS->>H1: Bot 3 played
    GS->>B4: Bot 3 played

    B4->>GS: Calculate move (300ms delay)
    GS->>H1: Bot 4 played
    GS->>B3: Bot 4 played

    Note over H2: Reconnects
    H2->>GS: Reconnect request
    GS->>H2: Restore state
    Note over H2: Human control restored
```

## 5. **Bot Performance Dashboard** (Best for Monitoring)
Shows bot performance metrics and decision quality.

```mermaid
graph TB
    subgraph "Performance Metrics"
        RT[Response Time<br/>avg: 287ms]
        WR[Win Rate<br/>32%]
        DR[Declaration Accuracy<br/>78%]
        MQ[Move Quality<br/>85%]
    end

    subgraph "Decision Breakdown"
        SD[Starter Decisions<br/>156 total]
        RD[Responder Decisions<br/>423 total]
        UD[Urgency Decisions<br/>89 total]
    end

    subgraph "Error Tracking"
        TO[Timeouts: 0]
        IV[Invalid Moves: 2]
        CE[Calculation Errors: 0]
    end

    RT --> Dashboard
    WR --> Dashboard
    DR --> Dashboard
    MQ --> Dashboard

    SD --> Dashboard
    RD --> Dashboard
    UD --> Dashboard

    TO --> Dashboard
    IV --> Dashboard
    CE --> Dashboard

    Dashboard[Bot Performance Dashboard]
```

## Recommendation

For the Liap Tui documentation, I recommend using **Option 1 (Bot Decision-Making Flow)** as the primary diagram because:

1. **Technical Clarity**: Shows the complete AI architecture from input to output
2. **Debugging Aid**: Developers can trace decision paths
3. **Comprehensive**: Covers all phases (Declaration, Turn, Execution)
4. **Modular Design**: Shows clear separation of concerns

You could supplement with **Option 4 (Bot-Human Interaction)** to show the seamless takeover functionality, as this is a key feature of the system.

## Implementation Notes

- Use **Option 1** in the AI Architecture documentation
- Use **Option 4** in the Disconnect/Reconnect documentation
- Include **Option 2** in the Operations guide
- Consider **Option 5** for monitoring documentation
