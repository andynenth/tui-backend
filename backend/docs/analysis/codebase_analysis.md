# Codebase Analysis - Data Flow Diagrams

Generated from actual code analysis

## System Architecture

```mermaid
graph TB
    subgraph Frontend
        React[React 19.1.0]
        Components[UI Components]
        Services[Service Layer]
        WebSocketClient[WebSocket Client]
    end
    
    subgraph Backend
        FastAPI[FastAPI Server]
        WebSocketHandler[WebSocket Handler]
        StateMachine[State Machine]
        GameEngine[Game Engine]
    end
    
    subgraph DataFlow
        Events[(Game Events)]
        State[(Game State)]
    end
    
    React --> Components
    Components --> Services
    Services --> WebSocketClient
    WebSocketClient -.WebSocket.-> WebSocketHandler
    WebSocketHandler --> StateMachine
    StateMachine --> GameEngine
    GameEngine --> State
    State --> Events
    Events -.Broadcast.-> WebSocketClient

    subgraph "REST Endpoints"
        API0["GET /"]
    end
```

## WebSocket Event Flow

```mermaid
graph LR
    Client[Frontend Client]
    Server[WebSocket Server]

    Client -->|decline_redeal| Server
    Server -->|game_ended| Client
    Client -->|start_game| Server
    Server -->|success| Client
    Client -->|accept_redeal| Server
    Server -->|game_ended| Client
    Client -->|join_room| Server
    Server -->|room_update| Client
    Server -->|player_reconnected| Client
    Client -->|declare| Server
    Server -->|declare| Client
    Server -->|room_update| Client
    Client -->|play| Server
    Server -->|| Client
    Server -->|player_disconnected| Client
    Client -->|create_room| Server
    Server -->|room_update| Client
    Client -->|leave_room| Server
    Server -->|declare| Client
    Server -->|room_closed| Client

```

## Game State Machine

```mermaid
stateDiagram-v2
    Game
    Game : handle_action()

```

## Frontend Components

```mermaid
graph TD
    App[App Root]

```

## Game Flow Sequence

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant WebSocket
    participant StateMachine
    participant GameEngine

    User->>Frontend: Create Room
    Frontend->>WebSocket: create_room
    WebSocket->>GameEngine: Initialize Game
    GameEngine->>StateMachine: Set PREPARATION
    StateMachine-->>WebSocket: room_created
    WebSocket-->>Frontend: room_created
    Frontend-->>User: Show Room

    User->>Frontend: Join Room
    Frontend->>WebSocket: join_room
    WebSocket-->>Frontend: player_joined

    User->>Frontend: Start Game
    Frontend->>WebSocket: start_game
    WebSocket->>StateMachine: Handle start
    StateMachine->>GameEngine: Deal cards
    GameEngine-->>StateMachine: Cards dealt
    StateMachine-->>WebSocket: phase_change
    WebSocket-->>Frontend: game_started

    loop Game Rounds
        Frontend->>WebSocket: declare
        WebSocket->>StateMachine: Handle declaration
        StateMachine-->>WebSocket: declaration_made
        WebSocket-->>Frontend: Update UI

        Frontend->>WebSocket: play
        WebSocket->>GameEngine: Validate play
        GameEngine->>StateMachine: Update state
        StateMachine-->>WebSocket: play_made
        WebSocket-->>Frontend: Update board
    end

```

