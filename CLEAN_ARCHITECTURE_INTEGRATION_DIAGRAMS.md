# Clean Architecture Integration Diagrams

**Document Purpose**: Visual representation of state machine integration with Clean Architecture patterns  
**Created**: 2025-01-08  
**Context**: Phase transition bug fix with Clean Architecture preservation

## Current vs Enhanced Architecture

### **Current Architecture Issue**

```mermaid
graph TD
    A[API Layer] --> B[Application Layer]
    B --> C[Domain Layer]
    B --> D[Infrastructure Layer]
    
    E[State Machine Engine] -.->|ISOLATED| C
    F[Event Sourcing] -.->|DISABLED| D
    
    G[Use Case: start_game.py] --> C
    G -.->|BYPASSES| E
    
    H[Domain: game.py] -.->|DUPLICATE LOGIC| E
    
    style E fill:#ff9999
    style F fill:#ff9999
    style G fill:#ffcc99
    style H fill:#ffcc99
```

**Problems:**
- State Machine operates independently from Clean Architecture
- Application layer bypasses state machine logic
- Domain logic duplicated between layers
- Event sourcing disabled breaks persistence chain

### **Enhanced Clean Architecture Integration**

```mermaid
graph TD
    A[API Layer] --> B[Application Layer]
    B --> C[Domain Layer]
    B --> D[Infrastructure Layer]
    
    subgraph "Domain Layer"
        C1[Game Entity]
        C2[GamePhase Enum]
        C3[Domain Events]
        C4[Business Rules]
    end
    
    subgraph "Application Layer"
        B1[Start Game Use Case]
        B2[State Machine Service Interface]
        B3[Event Publisher Interface]
    end
    
    subgraph "Infrastructure Layer"
        D1[State Machine Service Implementation]
        D2[Event Store Publisher]
        D3[WebSocket Publisher]
        D4[Composite Event Publisher]
    end
    
    B1 --> B2
    B2 --> D1
    D1 --> C1
    C1 --> C3
    B1 --> B3
    B3 --> D4
    D4 --> D2
    D4 --> D3
    
    E[Engine/State Machine] --> D1
    
    style D1 fill:#99ff99
    style D2 fill:#99ff99
    style B2 fill:#99ccff
    style C2 fill:#ffff99
```

**Solutions:**
- State Machine integrated as Infrastructure Service
- Application layer coordinates through interfaces
- Single source of truth for domain concepts
- Event sourcing enabled with proper flow

## State Machine Integration Flow

### **Clean Architecture Message Flow**

```mermaid
sequenceDiagram
    participant Client as WebSocket Client
    participant API as API Layer
    participant App as Application Layer
    participant Domain as Domain Layer
    participant SM as State Machine Service
    participant Events as Event Publisher
    participant Store as Event Store
    
    Client->>API: start_game message
    API->>App: StartGameUseCase.execute()
    
    Note over App: Clean Architecture Coordination
    App->>SM: coordinate_game_start()
    SM->>Domain: game.start_round()
    Domain->>Domain: Apply business rules
    Domain->>Domain: Emit domain events
    
    Note over SM: State Machine Phase Management
    SM->>SM: transition_to(PREPARATION)
    SM->>Domain: game.check_weak_hands()
    SM->>SM: Auto-progress to DECLARATION
    
    Note over App: Event Publishing
    App->>Events: publish(GameStarted)
    Events->>Store: persist_event()
    Events->>API: broadcast_to_room()
    
    API->>Client: game_started event
    API->>Client: phase_change event
```

### **Layer Responsibility Matrix**

```mermaid
graph LR
    subgraph "API Layer"
        A1[WebSocket Handling]
        A2[Message Routing]
        A3[Response Formatting]
    end
    
    subgraph "Application Layer"
        B1[Use Case Orchestration]
        B2[Interface Coordination]
        B3[Cross-Layer Communication]
    end
    
    subgraph "Domain Layer"
        C1[Business Logic]
        C2[Game Rules]
        C3[Event Definition]
        C4[State Validation]
    end
    
    subgraph "Infrastructure Layer"
        D1[State Machine Implementation]
        D2[Event Persistence]
        D3[WebSocket Broadcasting]
        D4[External Services]
    end
    
    A1 --> B1
    A2 --> B2
    B1 --> C1
    B2 --> D1
    C3 --> D2
    D2 --> D3
```

## Event Sourcing Integration

### **Event Flow with Clean Architecture**

```mermaid
graph TD
    subgraph "Domain Events"
        E1[GameStarted]
        E2[WeakHandsFound]
        E3[PhaseChanged]
        E4[RoundProgressed]
    end
    
    subgraph "Application Event Publishing"
        P1[Event Publisher Interface]
        P2[Composite Publisher]
    end
    
    subgraph "Infrastructure Event Handling"
        I1[WebSocket Publisher]
        I2[Event Store Publisher]
        I3[Monitoring Publisher]
    end
    
    subgraph "Persistence Layer"
        S1[SQLite Event Store]
        S2[In-Memory Cache]
        S3[WebSocket Connections]
    end
    
    E1 --> P1
    E2 --> P1
    E3 --> P1
    E4 --> P1
    
    P1 --> P2
    P2 --> I1
    P2 --> I2
    P2 --> I3
    
    I1 --> S3
    I2 --> S1
    I2 --> S2
    
    style P1 fill:#99ccff
    style P2 fill:#99ff99
    style I2 fill:#99ff99
```

### **State Machine Phase Transitions**

```mermaid
stateDiagram-v2
    [*] --> WAITING
    WAITING --> PREPARATION: start_game()
    
    state PREPARATION {
        [*] --> Dealing
        Dealing --> WeakHandCheck
        WeakHandCheck --> RedealIfNeeded
        RedealIfNeeded --> Complete
        Complete --> [*]
    }
    
    PREPARATION --> DECLARATION: auto_transition()
    DECLARATION --> TURN: all_declarations_complete()
    TURN --> TURN_RESULTS: turn_complete()
    TURN_RESULTS --> SCORING: round_complete()
    SCORING --> PREPARATION: next_round()
    SCORING --> GAME_OVER: game_complete()
    
    note right of PREPARATION: State Machine coordinates\nwith Domain business rules
    note right of DECLARATION: Events emitted through\nClean Architecture layers
```

## Performance and Monitoring

### **Clean Architecture Performance Impact**

```mermaid
graph LR
    subgraph "Performance Metrics"
        M1[Layer Communication Overhead]
        M2[Event Publishing Latency]
        M3[State Machine Integration Cost]
        M4[Memory Usage Impact]
    end
    
    subgraph "Monitoring Points"
        Mon1[Domain Event Timing]
        Mon2[Application Use Case Duration]
        Mon3[Infrastructure Service Latency]
        Mon4[API Response Time]
    end
    
    subgraph "Optimization Targets"
        O1[<10ms Event Latency]
        O2[<50ms Use Case Execution]
        O3[<5ms State Transition]
        O4[<100ms Total Response]
    end
    
    M1 --> Mon1
    M2 --> Mon2
    M3 --> Mon3
    M4 --> Mon4
    
    Mon1 --> O1
    Mon2 --> O2
    Mon3 --> O3
    Mon4 --> O4
```

### **Agent Deployment Architecture**

```mermaid
graph TD
    subgraph "Clean Architecture Lead"
        CL[Coordinate across layers]
        CL1[Ensure dependency inversion]
        CL2[Validate architecture compliance]
    end
    
    subgraph "Domain Integration Architect"
        DA[Design domain integration]
        DA1[Consolidate GamePhase enums]
        DA2[Preserve business rule purity]
    end
    
    subgraph "Application Layer Developer"
        AD[Modify use cases]
        AD1[State machine coordination]
        AD2[Interface implementation]
    end
    
    subgraph "Infrastructure Layer Developer"
        ID[Enable event sourcing]
        ID1[State machine service]
        ID2[Event publisher enhancement]
    end
    
    subgraph "State Machine Integration Expert"
        SME[Bridge engine with domain]
        SME1[Preserve Clean Architecture]
        SME2[Event integration]
    end
    
    CL --> DA
    CL --> AD
    CL --> ID
    DA --> SME
    AD --> SME
    ID --> SME
    
    style CL fill:#ff9999
    style DA fill:#99ff99
    style AD fill:#99ccff
    style ID fill:#ffff99
    style SME fill:#ff99ff
```

## Implementation Phases with Clean Architecture

### **Phase Progression with Layer Alignment**

```mermaid
gantt
    title Clean Architecture Phase Transition Fix
    dateFormat X
    axisFormat %s
    
    section Phase 1: Infrastructure
    Enable Event Sourcing: 0, 30m
    CompositeEventPublisher: 15m, 30m
    
    section Phase 2: Domain Layer
    Consolidate GamePhase: 30m, 60m
    Domain Event Integration: 45m, 75m
    
    section Phase 3: Application Layer
    Use Case Modification: 60m, 120m
    State Machine Interface: 90m, 150m
    
    section Phase 4: Integration
    Cross-Layer Testing: 120m, 180m
    Architecture Validation: 150m, 210m
    
    section Phase 5: Production
    Performance Validation: 180m, 240m
    Documentation Update: 210m, 270m
```

This integration approach ensures that the phase transition bug fix enhances rather than compromises the existing Clean Architecture implementation, providing a maintainable and scalable solution.