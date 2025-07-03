# 🎮 How Liap Tui Works - Complete System Overview

## Table of Contents
1. [Game Overview](#game-overview)
2. [System Architecture](#system-architecture)
3. [Game Flow](#game-flow)
4. [State Management](#state-management)
5. [Network Communication](#network-communication)
6. [Bot System](#bot-system)
7. [Monitoring & Recovery](#monitoring--recovery)
8. [Common Issues & Solutions](#common-issues--solutions)

## Game Overview

Liap Tui is a real-time multiplayer card game where 4 players compete to match their declared pile counts.

### Game Rules Summary
- **Players**: Always 4 (humans or bots)
- **Cards**: 32 total, 8 per player per round
- **Objective**: Declare how many piles you'll win, then achieve it
- **Scoring**: Points based on matching declaration (with multipliers)
- **Winner**: First to 50 points or highest after 20 rounds

## System Architecture

### High-Level Overview
```
┌─────────────────┐     WebSocket      ┌──────────────────┐
│                 │ ←---------------→   │                  │
│  React Frontend │                     │  Python Backend  │
│   (Browser)     │     Events/State    │    (FastAPI)     │
│                 │ ←---------------→   │                  │
└─────────────────┘                     └──────────────────┘
        ↓                                        ↓
   Local State                            State Machine
   UI Updates                             Event Sourcing
                                         Bot Management
```

### Backend Architecture

#### Core Components

1. **FastAPI Application** (`main.py`)
   - REST endpoints for room management
   - WebSocket endpoint for real-time gameplay
   - Health monitoring endpoints

2. **State Machine** (`backend/engine/state_machine/`)
   - Controls game flow through 4 phases
   - Handles all game actions
   - Ensures valid state transitions

3. **Game Engine** (`backend/engine/`)
   - Core game logic and rules
   - Player and card management
   - Score calculation

4. **Socket Manager** (`socket_manager.py`)
   - WebSocket connection handling
   - Message broadcasting
   - Connection recovery

### Frontend Architecture

1. **React 19 Application**
   - Single-page application
   - Real-time UI updates
   - WebSocket integration

2. **Service Layer** (`frontend/src/services/`)
   - `NetworkService`: WebSocket management
   - `GameService`: Game state management
   - `ServiceIntegration`: Coordinates services

3. **Component Structure**
   - Pages: Top-level routing
   - Components: Reusable UI elements
   - Phases: Game phase-specific UI

## Game Flow

### 1. Room Creation & Joining
```mermaid
sequenceDiagram
    participant Player as Player Browser
    participant Frontend as React Frontend
    participant NetworkService as NetworkService.ts
    participant SocketManager as SocketManager.py
    participant GameManager as Game.py
    participant StateMachine as GameStateMachine.py

    Player->>Frontend: Navigate to /game/room123
    Frontend->>NetworkService: connectToRoom("room123")
    NetworkService->>NetworkService: createConnection(url, roomId)
    NetworkService->>SocketManager: WebSocket connect ws://localhost:5050/ws/room123
    SocketManager->>SocketManager: add_connection(websocket, room_id)
    SocketManager->>GameManager: create_or_get_room(room_id)
    GameManager->>GameManager: add_player(player_name, is_bot=false)
    GameManager->>SocketManager: broadcast_room_update()
    SocketManager->>NetworkService: room_update event
    NetworkService->>Frontend: 'message' event with room data
    Frontend->>Frontend: updateGameState(newState)
```

### 2. Game Start (Host Action)
```mermaid
sequenceDiagram
    participant Host as Host Player
    participant Frontend as React Frontend
    participant NetworkService as NetworkService.ts
    participant SocketManager as SocketManager.py
    participant StateMachine as GameStateMachine.py
    participant PhaseManager as PhaseManager.py
    participant Game as Game.py

    Host->>Frontend: Click "Start Game" button
    Frontend->>NetworkService: send(roomId, "action", {action_type: "start_game"})
    NetworkService->>SocketManager: WebSocket message
    SocketManager->>StateMachine: process_action(GameAction)
    StateMachine->>ActionProcessor: validate_action(action)
    ActionProcessor->>StateMachine: validation_result
    StateMachine->>PhaseManager: _immediate_transition_to(GamePhase.PREPARATION)
    PhaseManager->>PreparationState: on_enter()
    PreparationState->>Game: deal_cards()
    Game->>Game: reset_round(), shuffle_and_deal()
    PreparationState->>PreparationState: update_phase_data({cards_dealt: true})
    PreparationState->>EventBroadcaster: broadcast_phase_change()
    EventBroadcaster->>SocketManager: broadcast(room_id, "phase_change", data)
    SocketManager->>Frontend: WebSocket phase_change event
    Frontend->>Frontend: updateGameState(preparationPhase)
```

### 3. Game Phases (Detailed Interactions)

#### PREPARATION Phase - Weak Hand Detection & Redeal
```mermaid
sequenceDiagram
    participant Player as Player Browser
    participant PreparationState as PreparationState.py
    participant Game as Game.py
    participant EventBroadcaster as EventBroadcaster.py
    participant SocketManager as SocketManager.py

    PreparationState->>Game: get_weak_hand_players(include_details=true)
    Game->>Game: Check each player.hand for pieces > 9 points
    Game->>PreparationState: weak_players_list
    
    alt Weak hands found
        PreparationState->>EventBroadcaster: broadcast_custom_event("weak_hands_detected")
        EventBroadcaster->>SocketManager: broadcast(room_id, event_data)
        SocketManager->>Player: weak_hands_detected event
        Player->>PreparationState: send redeal_request action
        PreparationState->>Game: execute_redeal_for_player(player_name)
        Game->>Game: shuffle_and_deal_player(player), redeal_multiplier++
        PreparationState->>PreparationState: update_phase_data({redeal_info})
        PreparationState->>EventBroadcaster: broadcast_phase_change()
    else No weak hands
        PreparationState->>PhaseManager: auto_transition_to(GamePhase.DECLARATION)
    end
```

#### DECLARATION Phase - Player Declarations
```mermaid
sequenceDiagram
    participant Player as Player Browser
    participant DeclarationState as DeclarationState.py
    participant Game as Game.py
    participant Rules as rules.py
    participant PhaseManager as PhaseManager.py

    Player->>DeclarationState: send declare action {target_piles: 3}
    DeclarationState->>Rules: get_valid_declares(game, player_name)
    Rules->>Game: Check declaration history, enforce rules
    Rules->>DeclarationState: valid_declarations_list
    
    alt Valid declaration
        DeclarationState->>Game: set_player_declaration(player_name, target_piles)
        Game->>Game: player_declarations[player_name] = target_piles
        DeclarationState->>DeclarationState: update_phase_data({declarations})
        DeclarationState->>DeclarationState: check_all_players_declared()
        
        alt All declared & total ≠ 8
            DeclarationState->>PhaseManager: auto_transition_to(GamePhase.TURN)
            PhaseManager->>TurnState: on_enter()
            TurnState->>Game: setup_turn_order()
        else Invalid total (= 8)
            DeclarationState->>EventBroadcaster: broadcast_custom_event("invalid_total")
        end
    else Invalid declaration
        DeclarationState->>EventBroadcaster: broadcast_custom_event("invalid_declaration")
    end
```

#### TURN Phase - Card Playing
```mermaid
sequenceDiagram
    participant CurrentPlayer as Current Player
    participant TurnState as TurnState.py
    participant Game as Game.py
    participant Rules as rules.py
    participant TurnResolution as turn_resolution.py
    participant BotManager as BotManager.py

    TurnState->>Game: get_current_player()
    Game->>TurnState: current_player_name
    
    alt Human Player Turn
        CurrentPlayer->>TurnState: send play_pieces {piece_indices: [0,1]}
        TurnState->>Rules: is_valid_play(player, pieces, required_count)
        Rules->>TurnState: validation_result
        
        alt Valid play
            TurnState->>Game: execute_play(player_name, piece_indices)
            Game->>Game: remove_pieces_from_hand(), add_to_current_turn_plays()
            TurnState->>TurnState: update_phase_data({current_turn_plays})
            TurnState->>TurnState: check_turn_complete()
            
            alt Turn complete (all played)
                TurnState->>TurnResolution: resolve_turn(current_turn_plays)
                TurnResolution->>Game: determine_winner(), update_piles_won()
                TurnState->>Game: advance_to_next_turn()
                TurnState->>TurnState: update_phase_data({turn_results})
            end
        end
        
    else Bot Player Turn
        TurnState->>BotManager: get_bot_action(game_state, player_name)
        BotManager->>BotManager: analyze_hand(), calculate_strategy()
        BotManager->>TurnState: bot_action {piece_indices}
        TurnState->>Game: execute_play(bot_name, piece_indices)
    end
```

#### SCORING Phase - Round Completion
```mermaid
sequenceDiagram
    participant ScoringState as ScoringState.py
    participant Game as Game.py
    participant Scoring as scoring.py
    participant WinConditions as win_conditions.py
    participant PhaseManager as PhaseManager.py

    ScoringState->>Game: get_round_results()
    Game->>ScoringState: {piles_won, declarations, redeal_multiplier}
    ScoringState->>Scoring: calculate_round_scores(players, piles_won, declarations, multiplier)
    Scoring->>Scoring: Compare actual vs declared, apply formulas
    Scoring->>ScoringState: round_scores_dict
    
    ScoringState->>Game: apply_round_scores(round_scores)
    Game->>Game: Update player.total_score for each player
    ScoringState->>WinConditions: is_game_over(game)
    WinConditions->>Game: Check win conditions (50 points or 20 rounds)
    WinConditions->>ScoringState: game_over_status
    
    alt Game Over
        ScoringState->>WinConditions: get_winners(game)
        WinConditions->>ScoringState: winners_list
        ScoringState->>ScoringState: update_phase_data({game_over: true, winners})
        ScoringState->>EventBroadcaster: broadcast_custom_event("game_over")
    else Continue Next Round
        ScoringState->>Game: advance_to_next_round()
        Game->>Game: round_number++, reset_round_state()
        ScoringState->>PhaseManager: auto_transition_to(GamePhase.PREPARATION)
    end
```

### 4. Phase Transitions (Enterprise Architecture)
```mermaid
stateDiagram-v2
    [*] --> PREPARATION : GameStateMachine.start()
    
    PREPARATION --> DECLARATION : PhaseManager._immediate_transition_to()
    note right of PREPARATION : PreparationState.update_phase_data()<br/>EventBroadcaster.broadcast_phase_change()
    
    DECLARATION --> TURN : All players declared & total ≠ 8
    note right of DECLARATION : DeclarationState.check_all_players_declared()<br/>Game.setup_turn_order()
    
    TURN --> TURN : Player plays cards
    note right of TURN : TurnState.update_phase_data()<br/>Game.execute_play()
    
    TURN --> SCORING : All turns completed
    note right of TURN : TurnResolution.resolve_turn()<br/>Game.advance_to_next_turn()
    
    SCORING --> PREPARATION : Next round
    note right of SCORING : Scoring.calculate_round_scores()<br/>Game.advance_to_next_round()
    
    SCORING --> [*] : Game over
    note right of SCORING : WinConditions.is_game_over()<br/>WinConditions.get_winners()
```

### 5. Enterprise Architecture Broadcast Pattern
```mermaid
sequenceDiagram
    participant State as Any GameState
    participant EventBroadcaster as EventBroadcaster.py
    participant SocketManager as SocketManager.py
    participant ActionQueue as ActionQueue.py
    participant Frontend as All Clients

    State->>State: update_phase_data(changes, reason)
    State->>State: self.phase_data.update(changes)
    State->>EventBroadcaster: broadcast_phase_change()
    EventBroadcaster->>EventBroadcaster: serialize_game_state()
    EventBroadcaster->>ActionQueue: store_event(GameAction)
    EventBroadcaster->>SocketManager: broadcast(room_id, "phase_change", data)
    SocketManager->>SocketManager: _process_broadcast_queue()
    SocketManager->>Frontend: WebSocket message to all clients
    Frontend->>Frontend: Handle 'phase_change' event
    
    Note over State,Frontend: ✅ Automatic, guaranteed broadcasting<br/>✅ Event sourcing for debugging<br/>✅ No manual broadcast() calls needed
```

## State Management

### Backend State Machine

The state machine uses an **Enterprise Architecture** pattern:

```python
# All state changes go through this method
async def update_phase_data(self, changes: dict, reason: str):
    # Update state
    self.phase_data.update(changes)
    
    # Automatic broadcasting
    await self.broadcast_phase_change()
    
    # Event sourcing
    await self.event_store.store(self.create_event())
```

**Key Features:**
- Automatic broadcasting on state changes
- Event sourcing for debugging/replay
- Human-readable change reasons
- Prevents manual broadcast errors

### Frontend State Management

Currently uses a **singleton GameService** pattern:
```typescript
class GameService {
    private state: GameState;
    private listeners: Set<Listener>;
    
    setState(newState: GameState) {
        this.state = newState;
        this.notifyListeners();
    }
}
```

**Known Issues:**
- Asynchronous React updates cause delays
- Heavy debug logging blocks UI thread
- State updates not atomic

## Network Communication

### WebSocket Protocol

All communication uses WebSocket with JSON messages:

```typescript
// Client to Server
{
    "event": "action",
    "data": {
        "action_type": "play_pieces",
        "player_name": "Alice",
        "piece_indices": [0, 1]
    }
}

// Server to Client
{
    "event": "phase_change",
    "data": {
        "phase": "TURN",
        "phase_data": {...},
        "allowed_actions": ["play_pieces"]
    }
}
```

### Key Events

**From Client:**
- `action` - Player game actions
- `sync_request` - Request state sync
- `client_ready` - Client connected
- `ack` - Message acknowledgment

**From Server:**
- `phase_change` - Game state updates
- `play` - Card play notifications
- `turn_complete` - Turn results
- `game_over` - Game end

### Connection Recovery

The NetworkService handles disconnections:
1. Automatic reconnection with exponential backoff
2. Message queuing during disconnection
3. State sync after reconnection
4. Event replay from last known sequence

## Bot System

### Bot Manager

Bots make decisions based on game state:

```python
class BotManager:
    async def get_bot_action(self, game_state, player_name):
        # Analyze game state
        # Make strategic decision
        # Return appropriate action
```

### Bot Strategies

1. **Declaration**: Analyze hand strength
2. **Card Play**: Consider turn order and winning probability
3. **Timing**: 1-3 second delays for human-like play

## Monitoring & Recovery

### Health Monitoring System

Tracks system health with adaptive intervals:
- **Healthy**: Check every 2-5 minutes
- **Warning**: Check every 30-60 seconds
- **Critical**: Check every 10-30 seconds

### Automatic Recovery Procedures

1. **Stale Connections**: Clean dead WebSocket connections
2. **Memory Pressure**: Clear caches and old data
3. **Client Desync**: Force state synchronization
4. **High Message Queue**: Clear old pending messages

### Monitoring Endpoints

- `/health` - Basic health check
- `/health/detailed` - Component status
- `/health/metrics` - Prometheus format
- `/recovery/status` - Recovery procedures

## Common Issues & Solutions

### Issue 1: "Cards Not Removed From Hand"

**Symptom**: Player sees cards in hand after playing them

**Current Cause**: 
1. Backend removes cards immediately
2. Frontend has async state update delay
3. UI shows old state briefly

**Workaround**: Wait 1-2 seconds for UI update

**Planned Fix**: Unified state store with atomic updates

### Issue 2: "Wrong Player Showing as Current"

**Symptom**: UI shows incorrect current player

**Current Cause**:
1. Multiple state update paths
2. Race condition between updates
3. Derived state calculation timing

**Workaround**: Refresh page to resync

**Planned Fix**: Single source of truth pattern

### Issue 3: "Bot Plays Out of Turn"

**Symptom**: Bot attempts invalid play

**Current Cause**:
1. Bot manager using stale state
2. Async notification delays
3. State machine/bot manager desync

**Workaround**: Game self-corrects on next turn

**Planned Fix**: Synchronous bot notifications

## Development Workflow

### Running Locally
```bash
# Start everything
./start.sh

# Backend only
cd backend && python main.py

# Frontend only
cd frontend && npm run dev
```

### Testing
```bash
# Backend tests
cd backend && python -m pytest tests/ -v

# Specific test files
python test_full_game_flow.py
python test_turn_state_debug.py
```

### Code Quality
```bash
# Python
source venv/bin/activate
cd backend && black . && pylint engine/ api/

# TypeScript
cd frontend && npm run lint && npm run type-check
```

## Architecture Decisions

### Why State Machine?
- Enforces valid game flow
- Prevents illegal state transitions
- Centralizes game logic
- Enables event sourcing

### Why WebSocket?
- Real-time gameplay requirement
- Bi-directional communication
- Lower latency than polling
- Persistent connections

### Why Enterprise Architecture?
- Automatic state broadcasting
- Prevents sync bugs
- Built-in event sourcing
- Debugging capabilities

### Why Monitoring System?
- Proactive issue detection
- Automatic recovery
- Performance tracking
- Production reliability

## Future Improvements

The refactoring plan addresses:
1. **State synchronization delays**
2. **God class decomposition**
3. **Circular dependency removal**
4. **Event system unification**

These improvements will make the system more maintainable and eliminate recurring bugs.