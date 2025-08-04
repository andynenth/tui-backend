# Deep Codebase Analysis - Complete Data Flows

## Analysis Summary

- **API Routes**: 20
- **WebSocket Events**: 0
- **React Components**: 55
- **Game Phases**: 1
- **Data Flows**: 39
- **Game Features**: 5

## Complete System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        Browser[Browser Client]
        React[React 19.1.0]
        Router[React Router]
        Pages[Page Components]
        Components[UI Components]
        Services[Service Layer]
        Network[Network Service]
    end
    
    subgraph "Communication Layer"
        WebSocket[WebSocket Connection]
        REST[REST API]
    end
    
    subgraph "Backend Layer"
        FastAPI[FastAPI Server]
        WSHandler[WebSocket Handler]
        APIRoutes[API Routes]
        Middleware[Middleware]
    end
    
    subgraph "Business Logic"
        StateMachine[State Machine]
        GameEngine[Game Engine]
        Rules[Game Rules]
        Scoring[Scoring System]
    end
    
    subgraph "Data Layer"
        GameState[(Game State)]
        Rooms[(Room Manager)]
        Players[(Player Data)]
    end
    
    Browser --> React
    React --> Router
    Router --> Pages
    Pages --> Components
    Components --> Services
    Services --> Network
    Network -.WebSocket.-> WebSocket
    Network -.HTTP.-> REST
    
    WebSocket --> WSHandler
    REST --> APIRoutes
    WSHandler --> StateMachine
    APIRoutes --> Middleware
    
    StateMachine --> GameEngine
    GameEngine --> Rules
    GameEngine --> Scoring
    
    StateMachine --> GameState
    WSHandler --> Rooms
    GameEngine --> Players
```

## WebSocket Communication Map

```mermaid
graph LR
    subgraph Frontend
        FE[Frontend Client]
    end

    subgraph Backend
        BE[Backend Server]
    end


```

## Frontend Component Hierarchy

```mermaid
graph TD
    App[App Root]

    App --> Pages
    subgraph Pages
        LobbyPage[LobbyPage]
        RoomPage[RoomPage]
        TutorialPage[TutorialPage]
        GamePage[GamePage]
        StartPage[StartPage]
    end

    Pages --> UIComponents
    subgraph UIComponents
        EnhancedPlayerAvatar[EnhancedPlayerAvatar]
        ToastNotification[ToastNotification]
        Layout[Layout]
        LoadingOverlay[LoadingOverlay]
        ErrorBoundary[ErrorBoundary]
        SettingsModal[SettingsModal]
        Input[Input]
        GameWithDisconnectHandling[GameWithDisconnectHandling]
        Modal[Modal]
        Button[Button]
    end

    GamePhases --> Services
    subgraph Services
        instances[instances]
        createMockNetworkService[createMockNetworkService]
    end

```

## Backend State Machine

```mermaid
stateDiagram-v2
    [*] --> Waiting: Room Created

    state Game {
        Game : handle_action()
    }


```

## Complete Data Flow

```mermaid
graph TB
    EnhancedPlayerAvatar[EnhancedPlayerAvatar]
    ConnectionIndicator[ConnectionIndicator]
    GamePage[GamePage]
    SettingsButton[SettingsButton]
    PlayerAvatar[PlayerAvatar]
    StartPage[StartPage]
    Layout[Layout]
    TruncatedName[TruncatedName]
    GameContainer[GameContainer]
    HostIndicator[HostIndicator]
    SettingsModal[SettingsModal]
    RoomPage[RoomPage]
    ErrorBoundary[ErrorBoundary]
    ToastContainer[ToastContainer]
    ConnectionQuality[ConnectionQuality]


```

## API Endpoints

```mermaid
graph LR
    Client[Client]
    Server[Server]

    subgraph WEBSOCKET
        WEBSOCKET0["/ws/{room_id}"]
    end
    Client -->|WEBSOCKET| WEBSOCKET
    WEBSOCKET --> Server

    subgraph GET
        GET0["/api/debug/events/{room_id}"]
        GET1["/api/debug/replay/{room_id}"]
        GET2["/api/debug/events/{room_id}/sequence/{seq}"]
        GET3["/api/debug/export/{room_id}"]
        GET4["/api/debug/stats"]
    end
    Client -->|GET| GET
    GET --> Server

    subgraph POST
        POST0["/api/debug/cleanup"]
        POST1["/event-store/cleanup"]
        POST2["/recovery/trigger/{procedure_name}"]
    end
    Client -->|POST| POST
    POST --> Server


```

## Game Features

```mermaid
graph TD
    GameEngine[Game Engine]

    GameEngine --> Game[Game]
    Game --> Game[Game]
    Game --> getweakhandplayers[get_weak_hand_players]
    Game --> hasweakhandplayers[has_weak_hand_players]
    Game --> executeredealforplayer[execute_redeal_for_player]
    GameEngine --> Rules[Rules]
    Rules --> getplaytype[get_play_type]
    Rules --> isvalidplay[is_valid_play]
    Rules --> ispair[is_pair]
    GameEngine --> Scoring[Scoring]
    Scoring --> calculatescore[calculate_score]
    Scoring --> calculateroundscores[calculate_round_scores]
    GameEngine --> Player[Player]
    Player --> Player[Player]
    Player --> hasredgeneral[has_red_general]
    Player --> recorddeclaration[record_declaration]
    Player --> resetfornextround[reset_for_next_round]
    GameEngine --> Piece[Piece]
    Piece --> Piece[Piece]
    Piece --> name[name]
    Piece --> color[color]
    Piece --> todict[to_dict]

```

## Game Play Sequence

```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant React
    participant NetworkService
    participant WebSocket
    participant FastAPI
    participant StateMachine
    participant GameEngine
    participant Database
    
    Note over User,Database: Room Creation Flow
    User->>Browser: Click Create Room
    Browser->>React: Handle Click
    React->>NetworkService: createRoom()
    NetworkService->>WebSocket: send('create_room')
    WebSocket->>FastAPI: WebSocket Message
    FastAPI->>GameEngine: create_game()
    GameEngine->>Database: Store Game State
    Database-->>GameEngine: Game ID
    GameEngine-->>FastAPI: Game Created
    FastAPI-->>WebSocket: broadcast('room_created')
    WebSocket-->>NetworkService: Receive Event
    NetworkService-->>React: Update State
    React-->>Browser: Render Room
    Browser-->>User: Show Room Code
    
    Note over User,Database: Game Play Flow
    User->>Browser: Make Move
    Browser->>React: Handle Input
    React->>NetworkService: play(pieces)
    NetworkService->>WebSocket: send('play', data)
    WebSocket->>FastAPI: WebSocket Message
    FastAPI->>StateMachine: handle_play()
    StateMachine->>GameEngine: validate_play()
    GameEngine->>GameEngine: Apply Rules
    GameEngine-->>StateMachine: Play Valid
    StateMachine->>Database: Update State
    StateMachine-->>FastAPI: broadcast_changes()
    FastAPI-->>WebSocket: broadcast('play_made')
    WebSocket-->>NetworkService: Receive Update
    NetworkService-->>React: Update Game State
    React-->>Browser: Render Changes
    Browser-->>User: Show Updated Board
```

