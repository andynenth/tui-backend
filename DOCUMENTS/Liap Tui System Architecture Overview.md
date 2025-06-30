# Liap Tui System Architecture Overview

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        U[User]
        B[Browser]
        
        subgraph "Frontend Application"
            UI[React UI Components]
            GS[GameService<br/>State Management]
            NS[NetworkService<br/>WebSocket Client]
            RS[RecoveryService<br/>Error Recovery]
            SI[ServiceIntegration<br/>Orchestration]
        end
    end
    
    subgraph "Network Layer"
        WS1[WebSocket<br/>Lobby Connection]
        WS2[WebSocket<br/>Game Connection]
        HTTP[HTTP/REST API]
    end
    
    subgraph "Backend Application"
        subgraph "API Layer"
            WSAPI[WebSocket Routes<br/>ws.py]
            RESTAPI[REST Routes<br/>routes.py]
            SM[Socket Manager<br/>Connection Handler]
        end
        
        subgraph "Business Logic"
            RM[Room Manager<br/>Game Rooms]
            
            subgraph "State Machine"
                GSM[Game State Machine]
                PS[Preparation State]
                DS[Declaration State]
                TS[Turn State]
                SS[Scoring State]
            end
            
            BM[Bot Manager<br/>AI Players]
            GE[Game Engine<br/>Core Logic]
        end
        
        subgraph "Enterprise Services"
            ES[Event Store<br/>Event Sourcing]
            HM[Health Monitor<br/>System Health]
            RM2[Recovery Manager<br/>Fault Recovery]
        end
    end
    
    subgraph "Infrastructure"
        DB[(SQLite DB<br/>Event Storage)]
        LOG[Structured Logging]
        MON[Monitoring<br/>Metrics]
    end
    
    %% User interactions
    U --> B
    B --> UI
    
    %% Frontend connections
    UI --> GS
    GS --> NS
    NS --> SI
    RS --> SI
    
    %% Network connections
    NS --> WS1
    NS --> WS2
    UI --> HTTP
    
    %% Backend connections
    WS1 --> WSAPI
    WS2 --> WSAPI
    HTTP --> RESTAPI
    
    WSAPI --> SM
    RESTAPI --> RM
    
    SM --> GSM
    RM --> GSM
    
    GSM --> PS
    GSM --> DS
    GSM --> TS
    GSM --> SS
    
    GSM --> BM
    GSM --> GE
    GSM --> ES
    
    ES --> DB
    HM --> MON
    RM2 --> ES
    
    GSM --> LOG
```

## Component Responsibilities

### Frontend Components

#### **UI Layer (React Components)**
- Pure presentation components
- No business logic
- Receives props from container components
- Handles user interactions

#### **GameService (TypeScript)**
```typescript
class GameService {
  - Single source of truth for game state
  - Processes backend events
  - Validates user actions
  - Notifies UI of state changes
}
```

#### **NetworkService (TypeScript)**
```typescript
class NetworkService {
  - Manages WebSocket connections
  - Handles reconnection logic
  - Message queuing
  - Connection health monitoring
}
```

#### **RecoveryService (TypeScript)**
```typescript
class RecoveryService {
  - Detects connection failures
  - Implements recovery strategies
  - Synchronizes missed events
  - Maintains service health
}
```

### Backend Components

#### **State Machine (Python)**
```python
class GameStateMachine:
    """
    Enterprise architecture with:
    - Automatic state broadcasting
    - Event sourcing
    - Action queue processing
    - Thread-safe operations
    """
```

#### **Bot Manager (Python)**
```python
class BotManager:
    """
    Autonomous bot system:
    - Receives phase_change events
    - Makes intelligent decisions
    - Acts through state machine
    - No frontend dependency
    """
```

#### **Event Store (Python)**
```python
class EventStore:
    """
    Event sourcing system:
    - Persists all game events
    - Enables state reconstruction
    - Supports client recovery
    - Provides audit trail
    """
```

## Data Flow Patterns

### 1. **User Action Flow**
```mermaid
sequenceDiagram
    User->>UI: Click/Input
    UI->>GameService: Action request
    GameService->>GameService: Validate action
    GameService->>NetworkService: Send message
    NetworkService->>Backend: WebSocket message
    Backend->>StateMachine: Process action
    StateMachine->>StateMachine: Update state
    StateMachine->>Backend: Auto-broadcast
    Backend->>NetworkService: State update
    NetworkService->>GameService: Update event
    GameService->>UI: Re-render
```

### 2. **Bot Action Flow**
```mermaid
sequenceDiagram
    StateMachine->>BotManager: Phase change
    BotManager->>BotManager: Check bot turns
    BotManager->>BotManager: AI decision
    BotManager->>StateMachine: Bot action
    StateMachine->>StateMachine: Process action
    StateMachine->>Backend: Auto-broadcast
    Backend->>Frontend: Bot action event
```

### 3. **Recovery Flow**
```mermaid
sequenceDiagram
    NetworkService->>NetworkService: Detect disconnect
    NetworkService->>RecoveryService: Connection lost
    RecoveryService->>RecoveryService: Start recovery
    RecoveryService->>Backend: Reconnect
    Backend->>EventStore: Get missed events
    EventStore->>Backend: Event list
    Backend->>RecoveryService: Send events
    RecoveryService->>GameService: Replay events
    GameService->>UI: Update state
```

## Key Design Patterns

### 1. **Enterprise State Machine Pattern**
- Single source of truth
- Automatic broadcasting
- No manual state manipulation
- Complete audit trail

### 2. **Event Sourcing Pattern**
- All state changes as events
- Complete history retention
- State reconstruction capability
- Debugging and audit support

### 3. **Command Pattern (Actions)**
```python
class GameAction:
    player_name: str
    action_type: ActionType
    payload: Dict[str, Any]
    timestamp: float
    sequence_id: int
```

### 4. **Observer Pattern**
- Frontend services observe state changes
- UI components observe GameService
- Decoupled event notification

### 5. **Singleton Pattern**
- NetworkService instance
- GameService instance
- BotManager instance
- Ensures single source of truth

## Technology Stack

### Frontend
- **React 19.1.0** - UI framework
- **TypeScript** - Type safety
- **ESBuild** - Fast bundling
- **Tailwind CSS** - Styling
- **PixiJS** - Game graphics

### Backend
- **Python 3.9+** - Core language
- **FastAPI** - Web framework
- **WebSockets** - Real-time communication
- **SQLite** - Event storage
- **asyncio** - Asynchronous processing

### Infrastructure
- **Docker** - Containerization
- **Poetry** - Python dependency management
- **npm** - JavaScript dependency management

## Security & Performance

### Security Measures
- Input validation at all layers
- WebSocket message validation
- Action authorization checks
- Rate limiting consideration

### Performance Optimizations
- Event-driven architecture (no polling)
- Efficient WebSocket protocol
- Message batching for recovery
- Lazy loading of game assets
- Connection pooling

## Scalability Considerations

### Horizontal Scaling
- Stateless REST API
- Room-based isolation
- Independent game instances
- Load balancer ready

### Vertical Scaling
- Async/await throughout
- Efficient data structures
- Minimal memory footprint
- Optimized algorithms

## Monitoring & Observability

### Health Monitoring
```python
/health          # Basic health check
/health/detailed # Comprehensive status
/health/metrics  # Prometheus metrics
```

### Logging
- Structured JSON logs
- Correlation IDs
- Event tracking
- Error aggregation

### Metrics
- WebSocket connections
- Active games
- Message throughput
- Error rates
- Recovery attempts

# Liap Tui Data Flow Sequence Diagrams

## Overview

This document contains comprehensive sequence diagrams showing the data flow in the Liap Tui multiplayer board game system. The system uses WebSocket communication, an enterprise state machine architecture, and automatic bot management.

## 1. Connection & Room Management Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant NetworkService
    participant LobbyWS as Lobby WebSocket
    participant Backend
    participant RoomManager

    User->>Frontend: Visit http://localhost:5050
    Frontend->>NetworkService: connectToLobby()
    NetworkService->>LobbyWS: Connect ws://localhost:5050/ws/lobby
    LobbyWS-->>NetworkService: Connection established
    
    NetworkService->>LobbyWS: send("client_ready", {})
    LobbyWS->>Backend: Process client_ready
    Backend->>RoomManager: list_rooms()
    RoomManager-->>Backend: Available rooms list
    Backend->>LobbyWS: send("room_list_update", {rooms: [...]})
    LobbyWS-->>NetworkService: Receive room list
    NetworkService-->>Frontend: Update available rooms

    Note over Frontend: User sees lobby with available rooms
```

## 2. Game Creation & Starting Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant NetworkService
    participant GameWS as Game WebSocket
    participant Backend
    participant StateMachine
    participant BotManager

    User->>Frontend: Click "Create Room"
    Frontend->>NetworkService: send("create_room", {player_name: "Alice"})
    NetworkService->>Backend: WebSocket message
    Backend->>Backend: room_manager.create_room("Alice")
    Backend-->>NetworkService: send("room_created", {room_id: "ABC123"})
    
    Frontend->>NetworkService: connectToRoom("ABC123")
    NetworkService->>GameWS: Connect ws://localhost:5050/ws/ABC123
    GameWS-->>NetworkService: Connection established
    
    User->>Frontend: Add bots and start game
    Frontend->>NetworkService: send("add_bot", {slot_id: 2})
    Frontend->>NetworkService: send("add_bot", {slot_id: 3})
    Frontend->>NetworkService: send("add_bot", {slot_id: 4})
    
    Frontend->>NetworkService: send("start_game", {})
    NetworkService->>Backend: Start game request
    Backend->>StateMachine: Initialize & start(PREPARATION)
    StateMachine->>BotManager: Register game
    
    StateMachine->>Backend: broadcast("phase_change", {phase: "preparation", ...})
    Backend-->>NetworkService: Phase change event
    NetworkService-->>Frontend: Update game state
```

## 3. Preparation Phase Flow (with Weak Hand/Redeal)

```mermaid
sequenceDiagram
    participant Frontend
    participant NetworkService
    participant Backend
    participant StateMachine
    participant PreparationState
    participant BotManager

    StateMachine->>PreparationState: Enter PREPARATION phase
    PreparationState->>PreparationState: Deal 8 cards to each player
    PreparationState->>PreparationState: Check for weak hands
    
    alt Weak hands found
        PreparationState->>Backend: update_phase_data({weak_players: ["Bot 2"], ...})
        Backend->>NetworkService: broadcast("phase_change", {phase_data: {weak_players: [...]}})
        NetworkService-->>Frontend: Display weak hand notification
        
        PreparationState->>BotManager: handle_game_event("redeal_decision_needed")
        BotManager->>BotManager: Bot decides (70% decline)
        BotManager->>StateMachine: handle_action(REDEAL_RESPONSE, {accept: false})
        
        Backend->>NetworkService: broadcast("phase_change", {updated state})
        NetworkService-->>Frontend: Update UI
    else No weak hands
        PreparationState->>PreparationState: Determine starter (GENERAL_RED holder)
        PreparationState->>Backend: update_phase_data({round_starter: "Bot 2"})
    end
    
    PreparationState->>StateMachine: Transition to DECLARATION
    StateMachine->>Backend: broadcast("phase_change", {phase: "declaration", ...})
```

## 4. Declaration Phase Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant GameService
    participant NetworkService
    participant Backend
    participant DeclarationState
    participant BotManager

    Backend->>NetworkService: broadcast("phase_change", {phase: "declaration", current_declarer: "Bot 2"})
    NetworkService->>GameService: Process phase change
    GameService-->>Frontend: Update UI (show declaration phase)
    
    loop For each player in declaration order
        alt Bot player's turn
            DeclarationState->>BotManager: Bot's turn to declare
            BotManager->>BotManager: Calculate declaration (AI logic)
            BotManager->>DeclarationState: handle_action(DECLARE, {value: 2})
            DeclarationState->>Backend: broadcast_custom_event("declare", {player: "Bot 2", value: 2})
            Backend-->>NetworkService: Declaration event
            NetworkService-->>Frontend: Update declarations display
        else Human player's turn
            Frontend-->>User: Show declaration options (0-8, total ≠ 8)
            User->>Frontend: Select declaration (e.g., 3)
            Frontend->>GameService: makeDeclaration(3)
            GameService->>NetworkService: send("declare", {player_name: "Alice", value: 3})
            NetworkService->>Backend: Declaration message
            Backend->>DeclarationState: handle_action(DECLARE, {value: 3})
            DeclarationState->>Backend: broadcast_custom_event("declare", {player: "Alice", value: 3})
        end
        
        DeclarationState->>DeclarationState: Update declarations & check total
    end
    
    DeclarationState->>StateMachine: All declared, transition to TURN
    StateMachine->>Backend: broadcast("phase_change", {phase: "turn", ...})
```

## 5. Turn Phase Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant NetworkService
    participant Backend
    participant TurnState
    participant BotManager

    Backend->>NetworkService: broadcast("phase_change", {phase: "turn", current_player: "Alice"})
    NetworkService-->>Frontend: Update to turn phase
    
    Note over Frontend: Alice (starter) plays first, sets piece count
    
    User->>Frontend: Select 2 pieces to play
    Frontend->>NetworkService: send("play", {player_name: "Alice", piece_indices: [0, 1]})
    NetworkService->>Backend: Play pieces message
    Backend->>TurnState: handle_action(PLAY_PIECES, {pieces: [...]})
    TurnState->>TurnState: Validate play, set required_piece_count = 2
    TurnState->>Backend: broadcast_custom_event("play", {player: "Alice", pieces: [...], required_count: 2})
    
    loop For remaining players
        alt Bot's turn
            BotManager->>BotManager: Select best 2 pieces (AI logic)
            BotManager->>TurnState: handle_action(PLAY_PIECES, {pieces: [...]})
        else Human's turn
            Frontend-->>User: Must play exactly 2 pieces
            User->>Frontend: Select pieces
            Frontend->>NetworkService: send("play", {...})
        end
        
        TurnState->>Backend: broadcast_custom_event("play", {player data})
    end
    
    TurnState->>TurnState: Determine winner (highest play value)
    TurnState->>Backend: broadcast_custom_event("turn_complete", {winner: "Alice", ...})
    Backend-->>Frontend: Show turn results
    
    alt More pieces in hands
        TurnState->>TurnState: Start next turn
    else All hands empty
        TurnState->>StateMachine: Transition to SCORING
    end
```

## 6. Scoring Phase Flow

```mermaid
sequenceDiagram
    participant Frontend
    participant NetworkService
    participant Backend
    participant ScoringState
    participant StateMachine

    StateMachine->>ScoringState: Enter SCORING phase
    ScoringState->>ScoringState: Calculate scores for each player
    
    Note over ScoringState: Score calculation:<br/>Declared 0, got 0: +3 points<br/>Declared X, got X: X+5 points<br/>Declared X, got Y: penalty<br/>Apply redeal multiplier

    ScoringState->>Backend: update_phase_data({<br/>round_scores: {...},<br/>total_scores: {...},<br/>game_over: false<br/>})
    Backend->>NetworkService: broadcast("phase_change", {phase: "scoring", ...})
    NetworkService-->>Frontend: Display scoring UI
    
    alt Game not over (no one reached 50 points)
        ScoringState->>ScoringState: Increment round number
        ScoringState->>StateMachine: Transition to PREPARATION
        StateMachine->>Backend: Start next round
    else Game over (winner reached 50+ points)
        ScoringState->>Backend: update_phase_data({game_over: true, winners: ["Alice"]})
        Backend->>NetworkService: broadcast("game_ended", {winners: ["Alice"], ...})
        NetworkService-->>Frontend: Show game over screen
    end
```

## 7. Error Recovery & Reconnection Flow

```mermaid
sequenceDiagram
    participant Frontend
    participant NetworkService
    participant RecoveryService
    participant Backend
    participant EventStore

    Note over NetworkService: Connection lost
    NetworkService->>NetworkService: Detect disconnect
    NetworkService->>RecoveryService: Connection lost
    RecoveryService->>RecoveryService: Start recovery procedure
    
    loop Exponential backoff retry
        RecoveryService->>NetworkService: Attempt reconnection
        NetworkService->>Backend: Connect WebSocket
        
        alt Connection successful
            Backend-->>NetworkService: Connected
            NetworkService->>Backend: send("sync_request", {last_sequence: 123})
            Backend->>EventStore: get_events_since(room_id, 123)
            EventStore-->>Backend: Missed events
            Backend->>NetworkService: send_batch(missed_events)
            NetworkService->>RecoveryService: Recovery complete
            RecoveryService-->>Frontend: State synchronized
        else Connection failed
            NetworkService-->>RecoveryService: Retry with backoff
        end
    end
    
    Note over Frontend: UI shows connection status throughout
```

## 8. Bot Interaction Flow

```mermaid
sequenceDiagram
    participant StateMachine
    participant GameState
    participant BotManager
    participant BotAI
    participant Backend

    Note over BotManager: Bots act independently of frontend
    
    StateMachine->>Backend: broadcast("phase_change", {phase: "turn", current_player: "Bot 2"})
    Backend->>BotManager: Phase change notification
    BotManager->>BotManager: Check if current player is bot
    
    alt Bot's turn
        BotManager->>BotAI: Calculate best move
        BotAI->>BotAI: Analyze hand, game state
        BotAI-->>BotManager: Recommended action
        
        BotManager->>StateMachine: handle_action(PLAY_PIECES, {pieces: [...]})
        StateMachine->>GameState: Process bot action
        GameState->>Backend: broadcast_custom_event("play", {player: "Bot 2", ...})
        
        Note over Backend: Bot actions broadcast same as human actions
    end
    
    Backend-->>Frontend: Bot action events (for display only)
```

## Key Architectural Patterns

### 1. **Enterprise State Machine**
- Single source of truth for game state
- Automatic broadcasting on all state changes
- Event sourcing with complete audit trail
- No manual broadcast calls needed

### 2. **WebSocket Message Protocol**
```javascript
// Standard message format
{
  event: "event_name",
  data: { /* event-specific payload */ },
  sequence: 123,        // For ordered delivery
  timestamp: 1234567890 // For synchronization
}
```

### 3. **Phase Change Events**
The most important event type, containing complete game state:
```javascript
{
  event: "phase_change",
  data: {
    phase: "turn",
    phase_data: { /* phase-specific data */ },
    players: { /* player hands and info */ },
    allowed_actions: ["play_pieces"],
    sequence: 456,
    timestamp: 1234567890,
    reason: "All players declared"
  }
}
```

### 4. **Action Queue Pattern**
- Prevents race conditions
- Ensures ordered processing
- Thread-safe state updates

### 5. **Automatic Bot Behavior**
- Bots receive same events as humans
- Act through same state machine
- No special bot handling in frontend
- AI decisions made server-side

## Error Handling

All errors follow consistent pattern:
```javascript
{
  event: "error",
  data: {
    message: "Descriptive error message",
    type: "error_category",
    context: { /* relevant context */ }
  }
}
```

## Summary

This architecture ensures:
- **Reliability**: Enterprise patterns prevent sync bugs
- **Scalability**: Event-driven design supports many concurrent games
- **Maintainability**: Single source of truth, clear separation of concerns
- **Performance**: Efficient WebSocket communication, no polling
- **Robustness**: Automatic recovery, comprehensive error handling

# WebSocket Events Reference

## Event Flow Diagram

```mermaid
graph TB
    subgraph "Frontend → Backend Events"
        FE[Frontend] --> |"client_ready"| BE[Backend]
        FE --> |"create_room"| BE
        FE --> |"join_room"| BE
        FE --> |"start_game"| BE
        FE --> |"declare"| BE
        FE --> |"play"| BE
        FE --> |"accept_redeal"| BE
        FE --> |"decline_redeal"| BE
        FE --> |"leave_room"| BE
    end

    subgraph "Backend → Frontend Events"
        BE2[Backend] --> |"phase_change"| FE2[Frontend]
        BE2 --> |"room_update"| FE2
        BE2 --> |"declare"| FE2
        BE2 --> |"play"| FE2
        BE2 --> |"turn_complete"| FE2
        BE2 --> |"score"| FE2
        BE2 --> |"game_ended"| FE2
        BE2 --> |"error"| FE2
    end
```

## Event Details

### Frontend → Backend Events

#### 1. **client_ready**
```javascript
{
  event: "client_ready",
  data: {}
}
```
Sent when WebSocket connection is established.

#### 2. **create_room**
```javascript
{
  event: "create_room",
  data: {
    player_name: "Alice"
  }
}
```

#### 3. **join_room**
```javascript
{
  event: "join_room",
  data: {
    room_id: "ABC123",
    player_name: "Bob"
  }
}
```

#### 4. **start_game**
```javascript
{
  event: "start_game",
  data: {}
}
```

#### 5. **declare** (Declaration Phase)
```javascript
{
  event: "declare",
  data: {
    player_name: "Alice",
    value: 3  // 0-8, total of all declarations ≠ 8
  }
}
```

#### 6. **play** (Turn Phase)
```javascript
{
  event: "play",
  data: {
    player_name: "Alice",
    piece_indices: [0, 1, 2]  // Indices of pieces in hand
  }
}
```

#### 7. **accept_redeal** / **decline_redeal**
```javascript
{
  event: "accept_redeal",
  data: {
    player_name: "Alice"
  }
}
```

### Backend → Frontend Events

#### 1. **phase_change** (Most Important)
```javascript
{
  event: "phase_change",
  data: {
    phase: "preparation" | "declaration" | "turn" | "scoring",
    round: 1,
    allowed_actions: ["declare", "play_pieces"],
    phase_data: {
      // Phase-specific data (see below)
    },
    players: {
      "Alice": {
        hand: ["GENERAL_RED(14)", "SOLDIER_BLACK(1)"],
        hand_size: 8,
        is_bot: false
      },
      "Bot 2": {
        hand: ["ELEPHANT_RED(10)", "CHARIOT_BLACK(7)"],
        hand_size: 8,
        is_bot: true
      }
    },
    sequence: 123,
    timestamp: 1735234567890,
    reason: "All players declared"
  }
}
```

##### Phase-Specific Data:

**Preparation Phase:**
```javascript
phase_data: {
  weak_players: ["Bot 2"],
  current_weak_player: "Bot 2",
  redeal_multiplier: 1,
  round_starter: "Alice"
}
```

**Declaration Phase:**
```javascript
phase_data: {
  declaration_order: ["Alice", "Bot 2", "Bot 3", "Bot 4"],
  current_declarer: "Bot 2",
  declarations: {
    "Alice": 3
  },
  declaration_total: 3
}
```

**Turn Phase:**
```javascript
phase_data: {
  current_turn_starter: "Alice",
  turn_order: ["Alice", "Bot 2", "Bot 3", "Bot 4"],
  current_player: "Bot 2",
  required_piece_count: 2,  // Set by first player
  turn_plays: {
    "Alice": {
      pieces: ["GENERAL_RED(14)", "ELEPHANT_RED(10)"],
      play_type: "PAIR",
      play_value: 24,
      is_valid: true
    }
  },
  current_turn_number: 1
}
```

**Scoring Phase:**
```javascript
phase_data: {
  round_scores: {
    "Alice": { declared: 3, actual: 2, final_score: -2 },
    "Bot 2": { declared: 2, actual: 2, final_score: 14 }  // 7 × 2 multiplier
  },
  total_scores: {
    "Alice": 23,
    "Bot 2": 28
  },
  redeal_multiplier: 2,
  game_over: false,
  winners: []
}
```

#### 2. **room_update**
```javascript
{
  event: "room_update",
  data: {
    players: {
      P1: {name: "Alice", is_bot: false, is_host: true},
      P2: {name: "Bob", is_bot: false, is_host: false},
      P3: {name: "Bot 3", is_bot: true, is_host: false},
      P4: null
    },
    host_name: "Alice",
    room_id: "ABC123",
    started: false
  }
}
```

#### 3. **declare** (Broadcast)
```javascript
{
  event: "declare",
  data: {
    player: "Bot 2",
    value: 2,
    is_bot: true
  }
}
```

#### 4. **play** (Broadcast)
```javascript
{
  event: "play",
  data: {
    player: "Alice",
    pieces: ["GENERAL_RED(14)", "ELEPHANT_RED(10)"],
    play_type: "STRAIGHT",
    play_value: 24,
    is_valid: true,
    next_player: "Bot 2",
    required_count: 2
  }
}
```

#### 5. **turn_complete**
```javascript
{
  event: "turn_complete",
  data: {
    winner: "Alice",
    winning_play: {
      pieces: ["GENERAL_RED(14)", "ELEPHANT_RED(10)"],
      play_type: "STRAIGHT",
      play_value: 24
    },
    player_piles: {
      "Alice": 3,
      "Bot 2": 0,
      "Bot 3": 1,
      "Bot 4": 0
    },
    turn_number: 1,
    next_starter: "Alice",
    all_hands_empty: false,
    will_continue: true
  }
}
```

#### 6. **game_ended**
```javascript
{
  event: "game_ended",
  data: {
    winners: ["Alice"],
    final_scores: {
      "Alice": 52,
      "Bot 2": 38,
      "Bot 3": 25,
      "Bot 4": 19
    },
    reason: "50_points_reached"
  }
}
```

#### 7. **error**
```javascript
{
  event: "error",
  data: {
    message: "Room is full",
    type: "join_room_error",
    details: {
      room_id: "ABC123",
      current_players: 4,
      max_players: 4
    }
  }
}
```

## Connection Architecture

```mermaid
graph LR
    subgraph "Frontend Services"
        NS[NetworkService<br/>WebSocket Manager]
        GS[GameService<br/>State Management]
        RS[RecoveryService<br/>Error Recovery]
    end
    
    subgraph "WebSocket Connections"
        LWS[Lobby WebSocket<br/>ws://host/ws/lobby]
        GWS[Game WebSocket<br/>ws://host/ws/roomId]
    end
    
    subgraph "Backend Systems"
        SM[State Machine<br/>Game Logic]
        BM[Bot Manager<br/>AI Players]
        ES[Event Store<br/>Event Sourcing]
    end
    
    NS <--> LWS
    NS <--> GWS
    LWS <--> SM
    GWS <--> SM
    SM <--> BM
    SM <--> ES
    GS <--> NS
    RS <--> NS
```

## Key Principles

1. **Single Source of Truth**: The `phase_change` event contains the complete authoritative game state
2. **No Polling**: All updates are event-driven via WebSocket
3. **Automatic Broadcasting**: State machine automatically broadcasts all changes
4. **Bot Integration**: Bots act through the same event system as humans
5. **Error Recovery**: Sequence numbers enable missed event recovery
6. **Type Safety**: Frontend TypeScript services provide full type checking