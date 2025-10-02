# Bot Takeover Flow - Vertical State Transition

Simple and clear vertical flow, focusing on the player's journey through disconnect and reconnect.

```mermaid
graph TD
    subgraph "Normal Play"
        HP[Human Playing]
    end

    HP -->|Connection Lost| D[Disconnected State]

    subgraph "Disconnect Handling"
        D --> SS[State Saved]
        SS --> BA[Bot Activated]
        BA --> BP[Bot Playing]
    end

    BP -->|Player Returns| RC[Reconnection Check]

    subgraph "Reconnect Process"
        RC --> RS[Restore State]
        RS --> HP2[Human Playing Again]
    end

    style HP fill:#90EE90
    style D fill:#FFB6C1
    style SS fill:#FFE4B5
    style BA fill:#87CEEB
    style BP fill:#87CEEB
    style RC fill:#DDA0DD
    style RS fill:#F0E68C
    style HP2 fill:#90EE90
```

## Alternative Vertical Layout (With More Detail)

```mermaid
graph TD
    Start([Player Connected]) --> HP[👤 Human Playing]

    HP -->|Network Issue| D[📵 Connection Lost]
    HP -->|Browser Refresh| D

    D --> Check{Game Started?}

    Check -->|Yes| SS[💾 Save State]
    Check -->|No| Remove[Remove from Room]

    SS --> BA[🤖 Bot Activated]
    BA --> BP[Bot Continues Playing]

    BP --> Wait[⏳ Awaiting Reconnection]

    Wait -->|Player Returns| RC[🔄 Reconnection]

    RC --> Verify[Verify Session]
    Verify --> RS[Restore Original State]
    RS --> HP2[👤 Human Playing Again]

    Remove --> End([Player Left Room])

    style HP fill:#90EE90,stroke:#333,stroke-width:2px
    style D fill:#FFB6C1,stroke:#333,stroke-width:2px
    style SS fill:#FFE4B5,stroke:#333,stroke-width:2px
    style BA fill:#87CEEB,stroke:#333,stroke-width:2px
    style BP fill:#87CEEB,stroke:#333,stroke-width:2px
    style RC fill:#DDA0DD,stroke:#333,stroke-width:2px
    style RS fill:#F0E68C,stroke:#333,stroke-width:2px
    style HP2 fill:#90EE90,stroke:#333,stroke-width:2px
```

## Compact Vertical Version

```mermaid
graph TD
    HP[Human Playing]
    HP -->|Disconnect| D[Connection Lost]
    D --> SS[State Saved]
    SS --> BA[Bot Activated]
    BA --> BP[Bot Playing]
    BP -->|Reconnect| RC[Check Session]
    RC --> RS[Restore State]
    RS --> HP2[Human Playing]

    style HP fill:#90EE90
    style HP2 fill:#90EE90
    style BA fill:#87CEEB
    style BP fill:#87CEEB
    style D fill:#FFB6C1
```

The vertical layout makes it easier to follow the flow from top to bottom, showing the natural progression of states during a disconnect/reconnect cycle.
