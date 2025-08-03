# Complete Dataflow Analysis

Generated from actual codebase analysis

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [WebSocket Event Flow](#websocket-event-flow)
3. [Game State Machine](#game-state-machine)
4. [Component Communication](#component-communication)
5. [Complete Data Flow](#complete-data-flow)
6. [User Journey - Create & Join](#user-journey---create-&-join)
7. [User Journey - Gameplay](#user-journey---gameplay)
8. [Backend Processing Flow](#backend-processing-flow)
9. [Frontend State Management](#frontend-state-management)
10. [Error Handling Flow](#error-handling-flow)

---

## System Architecture Overview

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
        React[React 19.1.0 App]
        Router[React Router DOM]
    end
    
    subgraph "Frontend Components"
        Pages[Page Components<br/>Start/Lobby/Room/Game]
        GameUI[Game UI<br/>Board/Hand/Pieces]
        Common[Common UI<br/>Buttons/Modals/Toasts]
    end
    
    subgraph "Frontend Services"
        NetworkService[Network Service<br/>WebSocket Manager]
        StateManager[State Manager<br/>Game State Cache]
        SoundManager[Sound Manager<br/>Audio Effects]
    end
    
    subgraph "Network Layer"
        WebSocket[WebSocket<br/>Bidirectional]
        REST[REST API<br/>Health/Debug Only]
    end
    
    subgraph "Backend API"
        FastAPI[FastAPI Server]
        WSHandler[WebSocket Handler<br/>23 Event Types]
        APIRoutes[API Routes<br/>Debug/Health]
    end
    
    subgraph "Game Logic"
        StateMachine[State Machine<br/>4 Phases]
        GameEngine[Game Engine<br/>Rules & Validation]
        Scoring[Scoring System<br/>Points Calculation]
    end
    
    subgraph "Data Management"
        RoomManager[Room Manager<br/>Active Rooms]
        PlayerManager[Player Manager<br/>Connections]
        EventStore[Event Store<br/>Game History]
    end
    
    Browser --> React
    React --> Router
    Router --> Pages
    Pages --> GameUI
    Pages --> Common
    
    GameUI --> NetworkService
    Common --> NetworkService
    NetworkService --> StateManager
    NetworkService -.-> WebSocket
    
    Pages -.-> REST
    
    WebSocket --> WSHandler
    REST --> APIRoutes
    
    WSHandler --> StateMachine
    StateMachine --> GameEngine
    GameEngine --> Scoring
    
    WSHandler --> RoomManager
    RoomManager --> PlayerManager
    StateMachine --> EventStore
    
    style WebSocket stroke:#00ff00,stroke-width:3px
    style WSHandler stroke:#00ff00,stroke-width:3px
```

[Back to top](#complete-dataflow-analysis)

---

## WebSocket Event Flow

```mermaid
flowchart TB
    subgraph "Lobby Events"
        L1[request_room_list] --> L1R[room_list_update]
        L2[create_room] --> L2R[room_created]
        L3[join_room] --> L3R[room_joined]
    end
    
    subgraph "Room Management"
        R1[client_ready] --> R1R[room_state_update]
        R2[add_bot] --> R2R[room_update]
        R3[remove_player] --> R3R[room_update]
        R4[leave_room] --> R4R[player_left]
    end
    
    subgraph "Game Lifecycle"
        G1[start_game] --> G1R[game_started]
        G2[leave_game] --> G2R[game_ended]
    end
    
    subgraph "Game Actions"
        A1[declare] --> A1R[declaration_made]
        A2[play] --> A2R[play_made]
        A3[request_redeal] --> A3R[redeal_requested]
        A4[accept_redeal] --> A4R[redeal_accepted]
        A5[decline_redeal] --> A5R[redeal_declined]
    end
    
    subgraph "Infrastructure"
        I1[ping] --> I1R[pong]
        I2[sync_request] --> I2R[sync_response]
        I3[ack] --> I3R[✓]
    end
    
    Client[Frontend Client] ==> L1
    Client ==> L2
    Client ==> L3
    Client ==> R1
    Client ==> G1
    Client ==> A1
    
    L1R ==> Broadcast[Broadcast to Clients]
    L2R ==> Broadcast
    L3R ==> Broadcast
    R1R ==> Broadcast
    G1R ==> Broadcast
    A1R ==> Broadcast
```

[Back to top](#complete-dataflow-analysis)

---

## Game State Machine

```mermaid
stateDiagram-v2
    [*] --> Waiting: Room Created
    
    Waiting --> Preparation: start_game
    
    state Preparation {
        [*] --> DealCards
        DealCards --> CheckWeakHands
        CheckWeakHands --> RedealRequest: weak hand
        CheckWeakHands --> Ready: normal hand
        RedealRequest --> RedealVoting
        RedealVoting --> DealCards: accepted
        RedealVoting --> Ready: declined
        Ready --> [*]
    }
    
    Preparation --> Declaration: All Ready
    
    state Declaration {
        [*] --> WaitingDeclarations
        WaitingDeclarations --> ProcessDeclaration: declare
        ProcessDeclaration --> WaitingDeclarations: next player
        ProcessDeclaration --> [*]: all declared
    }
    
    Declaration --> Turn: Declarations Complete
    
    state Turn {
        [*] --> CurrentPlayerTurn
        CurrentPlayerTurn --> ValidatePlay: play
        ValidatePlay --> ApplyPlay: valid
        ValidatePlay --> CurrentPlayerTurn: invalid
        ApplyPlay --> ResolvePile
        ResolvePile --> NextPlayer
        NextPlayer --> CurrentPlayerTurn: pieces remain
        NextPlayer --> [*]: round complete
    }
    
    Turn --> Scoring: Round Over
    
    state Scoring {
        [*] --> CalculateScores
        CalculateScores --> ApplyMultipliers
        ApplyMultipliers --> CheckWinCondition
        CheckWinCondition --> GameOver: winner found
        CheckWinCondition --> NextRound: continue
        NextRound --> [*]
    }
    
    Scoring --> Preparation: Next Round
    Scoring --> [*]: Game Over
    
    note right of Preparation: Cards dealt, weak hand checks
    note right of Declaration: Players declare pile targets
    note right of Turn: Players play pieces
    note right of Scoring: Calculate and apply scores
```

[Back to top](#complete-dataflow-analysis)

---

## Component Communication

```mermaid
graph TB
    subgraph "Page Components"
        StartPage[StartPage]
        LobbyPage[LobbyPage]
        RoomPage[RoomPage]
        GamePage[GamePage]
    end
    
    subgraph "Game Components"
        GameBoard[GameBoard]
        PlayerHand[PlayerHand]
        DeclarationUI[DeclarationUI]
        ScoringDisplay[ScoringDisplay]
    end
    
    subgraph "Network Layer"
        NetworkService[NetworkService]
        WebSocketConnection[WebSocket Connection]
    end
    
    subgraph "State Management"
        GameState[Game State]
        RoomState[Room State]
        PlayerState[Player State]
    end
    
    StartPage -->|create_room| NetworkService
    StartPage -->|join_room| NetworkService
    
    LobbyPage -->|request_room_list| NetworkService
    LobbyPage -->|join_room| NetworkService
    
    RoomPage -->|add_bot| NetworkService
    RoomPage -->|remove_player| NetworkService
    RoomPage -->|start_game| NetworkService
    
    GamePage --> GameBoard
    GamePage --> PlayerHand
    GamePage --> DeclarationUI
    GamePage --> ScoringDisplay
    
    GameBoard -->|play| NetworkService
    PlayerHand -->|select pieces| GameState
    DeclarationUI -->|declare| NetworkService
    
    NetworkService <--> WebSocketConnection
    NetworkService --> GameState
    NetworkService --> RoomState
    NetworkService --> PlayerState
    
    GameState --> GameBoard
    GameState --> PlayerHand
    RoomState --> RoomPage
    PlayerState --> PlayerHand
```

[Back to top](#complete-dataflow-analysis)

---

## Complete Data Flow

```mermaid
graph LR
    subgraph "User Actions"
        UA1[Create Room]
        UA2[Join Room]
        UA3[Start Game]
        UA4[Make Declaration]
        UA5[Play Pieces]
    end
    
    subgraph "Frontend Processing"
        FP1[Validate Input]
        FP2[Update Local State]
        FP3[Send WebSocket]
        FP4[Receive Response]
        FP5[Update UI]
    end
    
    subgraph "Network Transport"
        NT1[WebSocket Send]
        NT2[WebSocket Receive]
        NT3[Message Queue]
    end
    
    subgraph "Backend Processing"
        BP1[Receive Message]
        BP2[Validate Action]
        BP3[Update Game State]
        BP4[Apply Rules]
        BP5[Calculate Results]
        BP6[Broadcast Updates]
    end
    
    subgraph "State Updates"
        SU1[Room State]
        SU2[Game State]
        SU3[Player State]
        SU4[Phase State]
    end
    
    subgraph "Client Updates"
        CU1[Update Display]
        CU2[Enable/Disable Actions]
        CU3[Show Notifications]
        CU4[Play Sounds]
    end
    
    UA1 --> FP1
    UA2 --> FP1
    UA3 --> FP1
    UA4 --> FP1
    UA5 --> FP1
    
    FP1 --> FP2
    FP2 --> FP3
    FP3 --> NT1
    
    NT1 --> BP1
    BP1 --> BP2
    BP2 --> BP3
    BP3 --> BP4
    BP4 --> BP5
    BP5 --> BP6
    
    BP3 --> SU1
    BP3 --> SU2
    BP3 --> SU3
    BP3 --> SU4
    
    BP6 --> NT2
    NT2 --> FP4
    FP4 --> FP5
    
    FP5 --> CU1
    FP5 --> CU2
    FP5 --> CU3
    FP5 --> CU4
```

[Back to top](#complete-dataflow-analysis)

---

## User Journey - Create & Join

```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant React
    participant NetworkService
    participant WebSocket
    participant Backend
    participant RoomManager
    participant GameEngine
    
    rect rgb(200, 255, 200)
        Note over User,GameEngine: Create Room Flow
        User->>Browser: Click "Create Room"
        Browser->>React: Handle button click
        React->>React: Generate room settings
        React->>NetworkService: createRoom(settings)
        NetworkService->>WebSocket: send({action: 'create_room', data})
        WebSocket->>Backend: WebSocket message
        Backend->>RoomManager: create_room(host_id)
        RoomManager->>GameEngine: initialize_game()
        GameEngine-->>RoomManager: game instance
        RoomManager-->>Backend: room_code
        Backend->>WebSocket: broadcast('room_created', {room_code})
        WebSocket->>NetworkService: receive event
        NetworkService->>React: update state
        React->>Browser: Navigate to /room/[code]
        Browser-->>User: Show room with code
    end
    
    rect rgb(200, 200, 255)
        Note over User,GameEngine: Join Room Flow
        User->>Browser: Enter room code
        Browser->>React: Handle form submit
        React->>NetworkService: joinRoom(code, name)
        NetworkService->>WebSocket: send({action: 'join_room', room_code, player_name})
        WebSocket->>Backend: WebSocket message
        Backend->>RoomManager: validate_room(code)
        
        alt Room exists and has space
            RoomManager->>GameEngine: add_player(player)
            GameEngine-->>RoomManager: success
            RoomManager-->>Backend: player added
            Backend->>WebSocket: broadcast('player_joined', player_data)
            Backend->>WebSocket: send('room_joined', room_state)
            WebSocket->>NetworkService: receive events
            NetworkService->>React: update players
            React->>Browser: Show room
            Browser-->>User: Display game room
        else Room full or not found
            Backend->>WebSocket: send('error', {message})
            WebSocket->>NetworkService: receive error
            NetworkService->>React: show error
            React->>Browser: Display error
            Browser-->>User: Show error message
        end
    end
```

[Back to top](#complete-dataflow-analysis)

---

## User Journey - Gameplay

```mermaid
sequenceDiagram
    participant User
    participant UI
    participant NetworkService
    participant Backend
    participant StateMachine
    participant GameEngine
    
    rect rgb(255, 255, 200)
        Note over User,GameEngine: Start Game
        User->>UI: Click "Start Game"
        UI->>NetworkService: startGame()
        NetworkService->>Backend: send('start_game')
        Backend->>StateMachine: transition(PREPARATION)
        StateMachine->>GameEngine: deal_cards()
        GameEngine-->>StateMachine: hands dealt
        StateMachine->>Backend: broadcast('game_started')
        Backend-->>UI: Update to game view
        UI-->>User: Show game board & hand
    end
    
    rect rgb(255, 200, 200)
        Note over User,GameEngine: Declaration Phase
        User->>UI: Select pile count
        UI->>UI: Validate selection
        UI->>NetworkService: declare(count)
        NetworkService->>Backend: send('declare', {count})
        Backend->>StateMachine: handle_declaration()
        StateMachine->>GameEngine: record_declaration()
        GameEngine-->>StateMachine: updated
        StateMachine->>Backend: broadcast('declaration_made')
        Backend-->>UI: Update declarations
        UI-->>User: Show who declared
    end
    
    rect rgb(200, 255, 255)
        Note over User,GameEngine: Playing Phase
        User->>UI: Select pieces
        UI->>UI: Highlight valid plays
        User->>UI: Confirm play
        UI->>NetworkService: play(pieces)
        NetworkService->>Backend: send('play', {pieces})
        Backend->>StateMachine: handle_play()
        StateMachine->>GameEngine: validate_play()
        
        alt Valid play
            GameEngine->>GameEngine: apply_play()
            GameEngine-->>StateMachine: play accepted
            StateMachine->>Backend: broadcast('play_made')
            Backend-->>UI: Update board
            UI-->>User: Show played pieces
        else Invalid play
            GameEngine-->>StateMachine: validation error
            StateMachine->>Backend: send('error')
            Backend-->>UI: Show error
            UI-->>User: Display error message
        end
    end
    
    rect rgb(255, 200, 255)
        Note over User,GameEngine: Scoring Phase
        StateMachine->>GameEngine: calculate_scores()
        GameEngine->>GameEngine: Compare declarations
        GameEngine->>GameEngine: Apply multipliers
        GameEngine-->>StateMachine: scores
        StateMachine->>Backend: broadcast('round_scored')
        Backend-->>UI: Update scores
        UI-->>User: Show score animation
        
        alt Game continues
            StateMachine->>StateMachine: Next round
            StateMachine->>Backend: broadcast('new_round')
        else Game over
            StateMachine->>Backend: broadcast('game_ended')
            Backend-->>UI: Show winner
            UI-->>User: Display results
        end
    end
```

[Back to top](#complete-dataflow-analysis)

---

## Backend Processing Flow

```mermaid
flowchart TB
    subgraph "WebSocket Entry"
        WS[WebSocket Message] --> Parse[Parse JSON]
        Parse --> Validate[Validate Schema]
    end
    
    subgraph "Authentication"
        Validate --> Auth[Check Player Auth]
        Auth --> Room[Verify Room Access]
    end
    
    subgraph "Action Router"
        Room --> Router{Action Type}
        Router -->|lobby| LobbyHandler[Lobby Handler]
        Router -->|room| RoomHandler[Room Handler]
        Router -->|game| GameHandler[Game Handler]
        Router -->|infra| InfraHandler[Infra Handler]
    end
    
    subgraph "Game Processing"
        GameHandler --> SM[State Machine]
        SM --> Phase{Current Phase}
        Phase -->|PREP| PrepHandler[Preparation Handler]
        Phase -->|DECL| DeclHandler[Declaration Handler]
        Phase -->|TURN| TurnHandler[Turn Handler]
        Phase -->|SCORE| ScoreHandler[Scoring Handler]
        
        PrepHandler --> Engine[Game Engine]
        DeclHandler --> Engine
        TurnHandler --> Engine
        ScoreHandler --> Engine
    end
    
    subgraph "State Updates"
        Engine --> UpdateState[Update Game State]
        UpdateState --> EventStore[Store Event]
        UpdateState --> Cache[Update Cache]
    end
    
    subgraph "Broadcasting"
        Cache --> Broadcast[Prepare Broadcast]
        Broadcast --> Filter[Filter Recipients]
        Filter --> Send[Send to Clients]
    end
    
    subgraph "Error Handling"
        Parse -.->|error| ErrorHandler[Error Handler]
        Validate -.->|error| ErrorHandler
        Auth -.->|error| ErrorHandler
        Engine -.->|error| ErrorHandler
        ErrorHandler --> ErrorResponse[Send Error Response]
    end
```

[Back to top](#complete-dataflow-analysis)

---

## Frontend State Management

```mermaid
graph TB
    subgraph "Network Events"
        WSReceive[WebSocket Message]
        WSError[WebSocket Error]
        WSClose[Connection Lost]
    end
    
    subgraph "Event Processing"
        EventRouter[Event Router]
        EventValidation[Validate Event]
        EventQueue[Event Queue]
    end
    
    subgraph "State Updates"
        GameStateUpdate[Game State]
        RoomStateUpdate[Room State]
        PlayerStateUpdate[Player State]
        UIStateUpdate[UI State]
    end
    
    subgraph "React Context"
        GameContext[Game Context]
        RoomContext[Room Context]
        PlayerContext[Player Context]
    end
    
    subgraph "Component Updates"
        PageRerender[Page Re-render]
        GameBoardUpdate[Game Board Update]
        PlayerListUpdate[Player List Update]
        NotificationShow[Show Notifications]
    end
    
    subgraph "Local Storage"
        SaveState[Save State]
        LoadState[Load State]
    end
    
    WSReceive --> EventRouter
    WSError --> EventRouter
    WSClose --> EventRouter
    
    EventRouter --> EventValidation
    EventValidation --> EventQueue
    EventQueue --> GameStateUpdate
    EventQueue --> RoomStateUpdate
    EventQueue --> PlayerStateUpdate
    EventQueue --> UIStateUpdate
    
    GameStateUpdate --> GameContext
    RoomStateUpdate --> RoomContext
    PlayerStateUpdate --> PlayerContext
    
    GameContext --> PageRerender
    GameContext --> GameBoardUpdate
    RoomContext --> PlayerListUpdate
    UIStateUpdate --> NotificationShow
    
    GameStateUpdate --> SaveState
    LoadState --> GameStateUpdate
```

[Back to top](#complete-dataflow-analysis)

---

## Error Handling Flow

```mermaid
flowchart TB
    subgraph "Error Sources"
        NetworkError[Network Error]
        ValidationError[Validation Error]
        GameRuleError[Game Rule Error]
        StateError[State Error]
        AuthError[Auth Error]
    end
    
    subgraph "Error Capture"
        TryCatch[Try-Catch Block]
        ErrorBoundary[React Error Boundary]
        WSErrorHandler[WebSocket Error Handler]
    end
    
    subgraph "Error Processing"
        ErrorLogger[Log Error]
        ErrorClassify{Classify Error}
        ErrorFormat[Format Message]
    end
    
    subgraph "User Notification"
        Toast[Toast Notification]
        Modal[Error Modal]
        InlineError[Inline Error]
    end
    
    subgraph "Recovery Actions"
        Retry[Retry Action]
        Reconnect[Reconnect WebSocket]
        RefreshState[Refresh State]
        Fallback[Fallback UI]
    end
    
    NetworkError --> WSErrorHandler
    ValidationError --> TryCatch
    GameRuleError --> TryCatch
    StateError --> ErrorBoundary
    AuthError --> TryCatch
    
    TryCatch --> ErrorLogger
    ErrorBoundary --> ErrorLogger
    WSErrorHandler --> ErrorLogger
    
    ErrorLogger --> ErrorClassify
    
    ErrorClassify -->|User Error| ErrorFormat
    ErrorClassify -->|System Error| ErrorFormat
    ErrorClassify -->|Network Error| Reconnect
    
    ErrorFormat --> Toast
    ErrorFormat --> Modal
    ErrorFormat --> InlineError
    
    Toast --> Retry
    Modal --> RefreshState
    Reconnect --> RefreshState
    RefreshState --> Fallback
```

[Back to top](#complete-dataflow-analysis)

---

