# Component Interaction Diagrams

## Overview

This document provides visual representations of how components interact across the Clean Architecture and Engine Layer boundary. These diagrams help prevent architectural confusion by clearly showing proper interaction patterns.

## Clean Architecture Flow (State Persistence)

```mermaid
graph TB
    subgraph "API Layer"
        WS[WebSocket Handler]
        RP[REST API]
    end
    
    subgraph "Application Layer"
        UC[Use Cases]
        SMA[StateManagementAdapter]
    end
    
    subgraph "Infrastructure Layer"
        SPM[StatePersistenceManager]
        ES[EventStore]
        CEP[CompositeEventPublisher]
    end
    
    subgraph "Domain Layer"
        E[Entities]
        VO[Value Objects]
        DE[Domain Events]
    end
    
    WS --> UC
    RP --> UC
    UC --> SMA
    UC --> E
    UC --> DE
    SMA --> SPM
    SMA --> ES
    SMA --> CEP
    
    classDef clean fill:#e1f5fe
    classDef adapter fill:#fff3e0
    
    class WS,RP,UC,SPM,ES,CEP,E,VO,DE clean
    class SMA adapter
```

## Engine Layer Flow (State Machine)

```mermaid
graph TB
    subgraph "Engine Layer"
        GSM[GameStateMachine]
        BM[BotManager]
        GM[GameMechanics]
    end
    
    subgraph "Domain Layer (Shared)"
        E[Entities]
        VO[Value Objects]
        DE[Domain Events]
    end
    
    GSM --> BM
    GSM --> GM
    GSM --> E
    BM --> E
    GM --> E
    GM --> DE
    
    classDef engine fill:#fce4ec
    classDef shared fill:#f3e5f5
    
    class GSM,BM,GM engine
    class E,VO,DE shared
```

## Cross-System Integration via Adapter Pattern

```mermaid
sequenceDiagram
    participant API as API Layer
    participant UC as Use Case
    participant SMA as StateManagementAdapter
    participant FF as Feature Flags
    participant GSM as GameStateMachine
    participant SPM as StatePersistenceManager
    
    API->>UC: Start Game Request
    UC->>SMA: track_game_start()
    SMA->>FF: Check USE_STATE_PERSISTENCE
    
    alt Feature Flag Enabled
        SMA->>SPM: Persist state snapshot
        SMA->>GSM: Get current state
        GSM-->>SMA: Game state
        SMA->>SPM: Save to database
    else Feature Flag Disabled
        SMA->>UC: No-op (graceful degradation)
    end
    
    UC-->>API: Success response
```

## Forbidden Interaction Pattern (WRONG)

```mermaid
graph TB
    subgraph "Clean Architecture (WRONG)"
        UC[Use Case]
        GSM[GameStateMachine]
    end
    
    UC -.->|❌ FORBIDDEN| GSM
    
    classDef wrong fill:#ffebee,stroke:#f44336,stroke-width:3px
    classDef forbidden stroke:#f44336,stroke-width:2px,stroke-dasharray: 5 5
    
    class UC,GSM wrong
```

## Correct Interaction Pattern (RIGHT)

```mermaid
graph TB
    subgraph "Clean Architecture (CORRECT)"
        UC[Use Case]
        SMA[StateManagementAdapter]
    end
    
    subgraph "Engine Layer"
        GSM[GameStateMachine]
    end
    
    UC --> SMA
    SMA -.->|Adapter Pattern| GSM
    
    classDef correct fill:#e8f5e8,stroke:#4caf50,stroke-width:2px
    classDef adapter fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    
    class UC correct
    class SMA adapter
    class GSM correct
```

## Feature Flag Decision Flow

```mermaid
flowchart TD
    Start([Component Needs State]) --> Check{Check Feature Flag}
    Check -->|USE_STATE_PERSISTENCE = True| Persist[Use StateManagementAdapter]
    Check -->|USE_STATE_PERSISTENCE = False| Skip[Skip state operations]
    
    Persist --> Adapter[StateManagementAdapter.enabled]
    Adapter -->|True| Bridge[Bridge to GameStateMachine]
    Adapter -->|False| Graceful[Graceful degradation]
    
    Skip --> Continue[Continue without state]
    Bridge --> Continue
    Graceful --> Continue
    Continue --> End([Complete operation])
    
    classDef decision fill:#fff3e0
    classDef action fill:#e1f5fe
    classDef result fill:#e8f5e8
    
    class Check,Adapter decision
    class Persist,Skip,Bridge,Graceful action
    class Continue,End result
```

## State Management Architecture Overview

```mermaid
graph TB
    subgraph "Clean Architecture System"
        direction TB
        API --> APP
        APP --> INF
        
        subgraph API["API Layer"]
            WS[WebSocket]
            REST[REST API]
        end
        
        subgraph APP["Application Layer"]
            UC[Use Cases]
            SMA[StateManagementAdapter]
        end
        
        subgraph INF["Infrastructure Layer"]
            DB[(Database)]
            Cache[(Cache)]
            Events[Event Store]
        end
    end
    
    subgraph "Engine System"
        GSM[GameStateMachine]
        Bots[Bot Management]
        Rules[Game Rules]
    end
    
    subgraph "Domain (Shared)"
        Entities[Game Entities]
        ValueObj[Value Objects]
        DomainEvents[Domain Events]
    end
    
    %% Clean Architecture internal flow
    WS --> UC
    REST --> UC
    UC --> SMA
    SMA --> DB
    SMA --> Events
    
    %% Engine internal flow
    GSM --> Bots
    GSM --> Rules
    
    %% Shared domain access
    UC --> Entities
    UC --> DomainEvents
    GSM --> Entities
    Rules --> DomainEvents
    
    %% Adapter bridge (controlled interaction)
    SMA -.->|Controlled via Feature Flags| GSM
    
    classDef clean fill:#e1f5fe,stroke:#01579b
    classDef engine fill:#fce4ec,stroke:#880e4f
    classDef shared fill:#f3e5f5,stroke:#4a148c
    classDef adapter fill:#fff8e1,stroke:#e65100
    
    class API,APP,INF,WS,REST,UC,DB,Cache,Events clean
    class GSM,Bots,Rules engine
    class Entities,ValueObj,DomainEvents shared
    class SMA adapter
```

## Component Responsibility Matrix

| Layer | Components | Responsibilities | Can Import From | Cannot Import From |
|-------|------------|------------------|-----------------|-------------------|
| **Domain** | Entities, Value Objects, Events | Core business logic | Nothing | All other layers |
| **Application** | Use Cases, Adapters | Application logic, orchestration | Domain | Infrastructure, API, Engine |
| **Infrastructure** | Persistence, Event Store | External concerns | Domain, Application | API, Engine |
| **API** | WebSocket, REST | External interfaces | Domain, Application, Infrastructure | Engine |
| **Engine** | StateMachine, Bots, Rules | Game mechanics | Domain (minimal) | Application, Infrastructure, API |

## Validation Checkpoints

Each interaction must pass these checkpoints:

1. **Import Direction Check**: Verify dependency flow follows Clean Architecture rules
2. **Feature Flag Check**: Ensure feature flags control cross-system interactions
3. **Adapter Pattern Check**: Verify adapters mediate between systems
4. **Null Safety Check**: Confirm graceful handling when features are disabled
5. **Boundary Respect Check**: Ensure each system maintains its responsibilities

## Common Anti-Patterns to Avoid

### ❌ Direct Engine Import in Use Case
```python
# WRONG - Use case directly importing Engine
from backend.engine.game_state_machine import GameStateMachine

class StartGameUseCase:
    def __init__(self, game_machine: GameStateMachine):  # ❌ Direct dependency
        self._game_machine = game_machine
```

### ✅ Correct Adapter Pattern
```python
# CORRECT - Use case with adapter
from backend.application.adapters.state_management_adapter import StateManagementAdapter

class StartGameUseCase:
    def __init__(self, state_adapter: StateManagementAdapter):  # ✅ Adapter dependency
        self._state_adapter = state_adapter
        
    def execute(self, game_id: str):
        if self._state_adapter and self._state_adapter.enabled:  # ✅ Feature flag check
            self._state_adapter.track_game_start(game_id)
```

## Integration Points Summary

- **Domain Events**: Shared communication mechanism between systems
- **StateManagementAdapter**: Clean Architecture's bridge to Engine Layer
- **Feature Flags**: Runtime control over system integration
- **Graceful Degradation**: Systems work independently when features disabled

This architecture prevents tight coupling while enabling controlled interaction between Clean Architecture and Engine Layer systems.