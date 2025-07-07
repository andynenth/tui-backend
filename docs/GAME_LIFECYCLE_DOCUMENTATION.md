# Liap Tui Game Lifecycle Documentation

## Overview

This document provides a comprehensive technical reference for the Liap Tui game implementation, tracing the complete game lifecycle from room creation to game completion. It covers all 7 game phases with detailed information about API endpoints, WebSocket events, state management, UI components, and data structures.

## Table of Contents

1. [Game Phases Overview](#game-phases-overview)
2. [WebSocket Protocol](#websocket-protocol)
3. [Phase 1: WAITING](#phase-1-waiting)
4. [Phase 2: PREPARATION](#phase-2-preparation)
5. [Phase 3: DECLARATION](#phase-3-declaration)
6. [Phase 4: TURN](#phase-4-turn)
7. [Phase 5: TURN_RESULTS](#phase-5-turn_results)
8. [Phase 6: SCORING](#phase-6-scoring)
9. [Phase 7: GAME_OVER](#phase-7-game_over)
10. [State Management Patterns](#state-management-patterns)
11. [Data Structures Reference](#data-structures-reference)

---

## Game Phases Overview

The game flows through 7 distinct phases:

```
WAITING → PREPARATION → DECLARATION → TURN ↔ TURN_RESULTS → SCORING → GAME_OVER
                ↑                                                 ↓
                └─────────────────────────────────────────────────┘
                            (New Round)
```

Each phase has specific:
- Backend state handler
- Frontend UI component
- Allowed actions
- Transition conditions
- WebSocket events

---

## WebSocket Protocol

### Connection Endpoint
- **URL**: `/ws/{room_id}`
- **Special room**: `lobby` for room management

### Message Format

**Client → Server:**
```json
{
  "event": "event_name",
  "data": {
    // Event-specific payload
  }
}
```

**Server → Client:**
```json
{
  "event": "event_type",
  "data": {
    // Event data
    "timestamp": 1234567890.123,
    "room_id": "room_123",
    "sequence": 42,
    "_ack_required": true
  }
}
```

### Common Events

#### System Events
- `ack` - Message acknowledgment
- `sync_request` - Synchronization request
- `client_ready` - Connection established
- `error` - Error notification

#### Broadcast Events
- `phase_change` - Game phase transition
- `room_update` - Room state change
- `room_closed` - Room deletion
- `player_disconnected` - Player disconnect
- `player_reconnected` - Player reconnect

---

## Phase 1: WAITING

### Overview
Room setup phase where players join and prepare to start the game.

### Backend Handler
- **File**: `/backend/engine/state_machine/states/waiting_state.py`
- **Class**: `WaitingState`

### Frontend Components
- **Room Page**: `/frontend/src/pages/RoomPage.jsx`
- **Waiting UI**: `/frontend/src/components/game/WaitingUI.jsx`

### API Endpoints

| Method | Endpoint | Purpose | Request Body | Response |
|--------|----------|---------|--------------|----------|
| POST | `/create-room` | Create new room | `{"host_name": "string"}` | `{"room_id": "string", "success": bool}` |
| POST | `/join-room` | Join existing room | `{"room_id": "string", "player_name": "string"}` | `{"success": bool, "room": {...}}` |
| GET | `/list-rooms` | Get available rooms | - | `{"rooms": [{"room_id": "...", "host_name": "...", "occupied_slots": n}]}` |
| POST | `/start-game` | Start game (host only) | `{"room_id": "string"}` | `{"success": bool}` |

### WebSocket Events

#### Incoming (Client → Server)
- `get_room_state` - Request current room state
- `add_bot` - Add bot to slot: `{"slot_id": 1-4}`
- `remove_player` - Remove player: `{"slot_id": 1-4}`
- `leave_room` - Leave room: `{"player_name": "string"}`
- `start_game` - Start game: `{}`

#### Outgoing (Server → Client)
- `room_update` - Room state changed
- `room_closed` - Room was closed
- `game_started` - Game has started
- `player_kicked` - Player was removed

### State Structure

**Backend Phase Data:**
```python
{
  "connected_players": 3,
  "required_players": 4,
  "room_ready": false,
  "players": ["Player1", "Bot 2", "Player4"],
  "game_start_requested": false,
  "transitioning_to": "PREPARATION"
}
```

**Frontend State:**
```javascript
{
  room_id: "ROOM123",
  host_name: "Player1",
  started: false,
  players: [
    {name: "Player1", is_bot: false, is_host: true},
    {name: "Bot 2", is_bot: true, is_host: false},
    null,  // Empty slot
    {name: "Player4", is_bot: false, is_host: false}
  ],
  occupied_slots: 3,
  total_slots: 4
}
```

### Transition Conditions
- All 4 slots must be filled
- Host triggers `start_game`
- Creates Game instance and transitions to PREPARATION

---

## Phase 2: PREPARATION

### Overview
Cards are dealt, weak hands are checked, and redeal decisions are made.

### Backend Handler
- **File**: `/backend/engine/state_machine/states/preparation_state.py`
- **Class**: `PreparationState`

### Frontend Component
- **UI**: `/frontend/src/components/game/PreparationUI.jsx`

### WebSocket Events

#### Incoming (Client → Server)
- `accept_redeal` - Accept redeal: `{"player_name": "string"}`
- `decline_redeal` - Decline redeal: `{"player_name": "string"}`
- `redeal_decision` - Make decision: `{"player_name": "string", "accept": bool}`

#### Outgoing (Server → Client)
- `phase_change` - Automatic broadcast with:
  ```json
  {
    "phase": "preparation",
    "phase_data": {
      "weak_players": ["Player1", "Player3"],
      "weak_players_awaiting": ["Player1"],
      "redeal_decisions": {"Player3": false},
      "redeal_multiplier": 1,
      "timeout_seconds": 30
    },
    "players": {
      "Player1": {
        "hand": ["GENERAL_RED", "HORSE_BLACK", "SOLDIER_RED"],
        "hand_size": 3,
        "zero_declares_in_a_row": 0,
        "declared": 0,
        "score": 15
      },
      "Player2": {
        "hand": ["CANNON_BLACK", "ELEPHANT_RED"],
        "hand_size": 2,
        "zero_declares_in_a_row": 1,
        "declared": 0,
        "score": 8
      }
    }
  }
  ```
- `redeal_decision_needed` - Notify weak hand players

### Game Logic

#### Weak Hand Detection
- A hand is weak if no piece > 9 points
- All weak players decide simultaneously
- 30-second timeout for decisions
- First accepter becomes new starter

#### Piece Distribution
- 8 pieces dealt to each player
- 32 total pieces shuffled and distributed
- Pieces have point values and types

### State Structure

**Phase Data:**
```python
{
  "weak_players": ["Player1", "Player3"],
  "weak_players_awaiting": ["Player1"],
  "redeal_decisions": {"Player3": False},
  "redeal_multiplier": 1,
  "decision_timeout": 30.0,
  "all_decisions_made": false
}
```

### Transition Conditions
- No weak hands detected, OR
- All weak players have made decisions
- Transitions to DECLARATION phase

---

## Phase 3: DECLARATION

### Overview
Players declare their target pile count (0-8) in turn order.

### Backend Handler
- **File**: `/backend/engine/state_machine/states/declaration_state.py`
- **Class**: `DeclarationState`

### Frontend Component
- **UI**: `/frontend/src/components/game/DeclarationUI.jsx`

### WebSocket Events

#### Incoming (Client → Server)
- `declare` - Make declaration:
  ```json
  {
    "player_name": "string",
    "value": 0-8
  }
  ```

#### Outgoing (Server → Client)
- `phase_change` - Automatic broadcast with:
  ```json
  {
    "phase": "declaration",
    "phase_data": {
      "declaration_order": ["Player1", "Player2", "Player3", "Player4"],
      "current_declarer_index": 2,
      "current_declarer": "Player3",
      "declarations": {"Player1": 3, "Player2": 2},
      "declaration_total": 5
    },
    "players": {
      "Player1": {
        "hand": ["GENERAL_RED", "HORSE_BLACK", "SOLDIER_RED"],
        "hand_size": 3,
        "zero_declares_in_a_row": 0,
        "declared": 3,
        "score": 15
      },
      "Player2": {
        "hand": ["CANNON_BLACK", "ELEPHANT_RED"],
        "hand_size": 2,
        "zero_declares_in_a_row": 1,
        "declared": 2,
        "score": 8
      },
      "Player3": {
        "hand": ["CHARIOT_RED", "ADVISOR_BLACK"],
        "hand_size": 2,
        "zero_declares_in_a_row": 2,
        "declared": 0,
        "score": 12
      }
    }
  }
  ```

### Validation Rules

#### Backend Validation
- Value must be 0-8
- Must be player's turn
- Last player cannot make total = 8

#### Frontend Validation
- Same rules as backend
- Shows valid options to player
- Confirmation dialog before submit

### State Structure

**Phase Data:**
```python
{
  "declaration_order": ["Player1", "Player2", "Player3", "Player4"],
  "current_declarer_index": 2,
  "current_declarer": "Player3",
  "declarations": {"Player1": 3, "Player2": 2},
  "declaration_total": 5
}
```

### Transition Conditions
- All players have declared
- Automatically transitions to TURN phase

---

## Phase 4: TURN

### Overview
Players play pieces in turns, following the starter's piece count.

### Backend Handler
- **File**: `/backend/engine/state_machine/states/turn_state.py`
- **Class**: `TurnState`

### Frontend Component
- **UI**: `/frontend/src/components/game/TurnUI.jsx`

### WebSocket Events

#### Incoming (Client → Server)
- `play` / `play_pieces` - Play pieces:
  ```json
  {
    "player_name": "string",
    "pieces": [0, 2, 4]  // Indices in hand
  }
  ```

#### Outgoing (Server → Client)
- `phase_change` - Automatic broadcast with:
  ```json
  {
    "phase": "turn",
    "phase_data": {
      "current_turn_starter": "Player1",
      "current_player": "Player3",
      "turn_order": ["Player1", "Player2", "Player3", "Player4"],
      "current_player_index": 2,
      "required_piece_count": 3,
      "turn_plays": {
        "Player1": {"pieces": [...], "value": 12, "type": "PAIR"},
        "Player2": {"pieces": [...], "value": 18, "type": "THREE_OF_A_KIND"}
      },
      "turn_complete": false,
      "current_turn_number": 5
    },
    "players": {
      "Player1": {
        "hand": ["GENERAL_RED"],
        "hand_size": 1,
        "zero_declares_in_a_row": 0,
        "declared": 3,
        "score": 15
      },
      "Player2": {
        "hand": [],
        "hand_size": 0,
        "zero_declares_in_a_row": 1,
        "declared": 2,
        "score": 8
      }
    }
  }
  ```
- `play` - Custom event when player plays:
  ```json
  {
    "player": "Player1",
    "pieces": [...],
    "play_value": 15,
    "play_type": "THREE_OF_A_KIND"
  }
  ```
- `turn_complete` - Turn resolution:
  ```json
  {
    "winner": "Player2",
    "winning_play": {...},
    "player_piles": {"Player1": 2, "Player2": 3, ...}
  }
  ```

### Play Types and Rules

#### Valid Play Types
- **SINGLE**: 1 piece
- **PAIR**: 2 same name/color
- **THREE_OF_A_KIND**: 3 soldiers same color
- **STRAIGHT**: 3 pieces from group
- **FOUR_OF_A_KIND**: 4 soldiers same color
- **EXTENDED_STRAIGHT**: 4 pieces with duplicate
- **FIVE_OF_A_KIND**: 5 soldiers same color
- **DOUBLE_STRAIGHT**: 2+2+2 same color

#### Turn Rules
- Starter plays 1-6 pieces
- Others must match piece count
- Highest value/type wins
- Winner gets piles equal to piece count

### State Structure

**Phase Data:**
```python
{
  "current_turn_starter": "Player1",
  "current_player": "Player3",
  "turn_order": ["Player1", "Player2", "Player3", "Player4"],
  "current_player_index": 2,
  "required_piece_count": 3,
  "turn_plays": {
    "Player1": {"pieces": [...], "value": 12, "type": "PAIR"},
    "Player2": {"pieces": [...], "value": 18, "type": "THREE_OF_A_KIND"}
  },
  "turn_complete": false,
  "current_turn_number": 5
}
```

### Transition Conditions
- All players have played
- Turn marked complete
- Transitions to TURN_RESULTS phase

---

## Phase 5: TURN_RESULTS

### Overview
Display turn results for 7 seconds before continuing.

### Backend Handler
- **File**: `/backend/engine/state_machine/states/turn_results_state.py`
- **Class**: `TurnResultsState`

### Frontend Component
- **UI**: `/frontend/src/components/game/TurnResultsUI.jsx`

### WebSocket Events

#### Incoming
- No player actions allowed (display-only phase)

#### Outgoing
- `phase_change` - Contains turn results:
  ```json
  {
    "phase": "turn_results",
    "phase_data": {
      "turn_winner": "Player2",
      "winning_play": {
        "pieces": [...],
        "value": 18,
        "type": "THREE_OF_A_KIND",
        "piles_won": 3
      },
      "display_duration": 7.0,
      "next_phase": "turn",
      "auto_transition": true
    },
    "players": {
      "Player1": {
        "hand": ["GENERAL_RED"],
        "hand_size": 1,
        "zero_declares_in_a_row": 0,
        "declared": 3,
        "score": 15
      },
      "Player2": {
        "hand": [],
        "hand_size": 0,
        "zero_declares_in_a_row": 1,
        "declared": 2,
        "score": 8
      }
    }
  }
  ```

### Display Elements
- Winner crown with name
- Winning play details
- Piles won animation
- Current pile standings
- Next turn preview

### Auto-Transition Logic
- 7-second display timer
- Backend controls transition
- Next phase determined by:
  - If hands not empty → TURN
  - If all hands empty → SCORING

### State Structure

**Frontend Props:**
```javascript
{
  winner: "Player2",
  winningPlay: {
    pieces: [...],
    value: 18,
    type: "THREE_OF_A_KIND",
    pilesWon: 3
  },
  playerPiles: {"Player1": 2, "Player2": 6, ...},
  turnNumber: 5,
  nextStarter: "Player2"
}
```

---

## Phase 6: SCORING

### Overview
Calculate round scores and check for game winner.

### Backend Handler
- **File**: `/backend/engine/state_machine/states/scoring_state.py`
- **Class**: `ScoringState`

### Frontend Component
- **UI**: `/frontend/src/components/game/ScoringUI.jsx`

### Score Calculation

#### Scoring Rules
- Declared 0, captured 0 → +3 points
- Declared 0, captured >0 → -captured points
- Declared = captured (non-zero) → declared + 5 points
- Otherwise → -|declared - captured| points
- Final score × redeal_multiplier

#### Win Condition
- First to 50 points wins
- If multiple reach 50, highest score wins

### WebSocket Events

#### Outgoing
- `phase_change` - Contains scoring data:
  ```json
  {
    "phase": "scoring",
    "phase_data": {
      "round_scores": {
        "Player1": {"base": -2, "multiplied": -2},
        "Player2": {"base": 8, "multiplied": 8}
      },
      "total_scores": {"Player1": 23, "Player2": 51},
      "game_complete": true,
      "winners": ["Player2"],
      "redeal_multiplier": 1
    },
    "players": {
      "Player1": {
        "hand": [],
        "hand_size": 0,
        "zero_declares_in_a_row": 0,
        "declared": 3,
        "score": 23
      },
      "Player2": {
        "hand": [],
        "hand_size": 0,
        "zero_declares_in_a_row": 1,
        "declared": 2,
        "score": 51
      }
    }
  }
  ```

### Display Elements
- Player rankings table
- Individual score breakdowns
- Declared vs captured comparison
- Round and total scores
- Winner announcement (if any)

### State Structure

**Phase Data:**
```python
{
  "round_scores": {
    "Player1": {"base_score": -2, "multiplied_score": -2},
    "Player2": {"base_score": 8, "multiplied_score": 8}
  },
  "total_scores": {"Player1": 23, "Player2": 51},
  "game_complete": true,
  "winners": ["Player2"],
  "display_delay_complete": false,
  "scores_calculated": true
}
```

### Transition Conditions
- 7-second display delay complete
- If game_complete → GAME_OVER
- Otherwise → PREPARATION (next round)

---

## Phase 7: GAME_OVER

### Overview
Display final results and provide options to return to lobby.

### Backend Handler
- **File**: `/backend/engine/state_machine/states/game_over_state.py`
- **Class**: `GameOverState` (terminal state)

### Frontend Component
- **UI**: `/frontend/src/components/game/GameOverUI.jsx`

### WebSocket Events

#### Outgoing
- `phase_change` - Contains final data:
  ```json
  {
    "phase": "game_over",
    "phase_data": {
      "final_rankings": [
        {"name": "Player2", "score": 52, "rank": 1},
        {"name": "Player1", "score": 45, "rank": 2}
      ],
      "game_stats": {
        "total_rounds": 13,
        "game_duration": "25 min",
        "start_time": 1234567890,
        "end_time": 1234569390
      },
      "winners": ["Player2"]
    }
  }
  ```

### Display Elements
- Final rankings with medals
- Winner celebration
- Game statistics
- 15-second auto-redirect countdown
- "Back to Lobby" button

### Cleanup Process

#### Frontend Cleanup Chain
1. User action or timeout triggers cleanup
2. GameContainer calls cleanup action
3. ServiceIntegration disconnects from room
4. GameService resets state
5. NetworkService closes WebSocket
6. Navigate to `/lobby`

#### Backend Handling
- No automatic cleanup
- Room persists until empty
- Host leaving triggers room deletion

### State Structure

**Frontend Display Data:**
```javascript
{
  finalRankings: [
    {name: "Player2", score: 52, rank: 1},
    {name: "Player1", score: 45, rank: 2}
  ],
  gameStats: {
    totalRounds: 13,
    gameDuration: "25 min"
  },
  winners: ["Player2"],
  countdown: 15
}
```

---

## State Management Patterns

### Global vs Local State

#### Global State (Frontend GameService)
- Player name and ID
- Room and game connection status
- Current game phase
- All players' public information
- Shared game state (scores, piles, etc.)

#### Local State (React Components)
- UI-specific state (modals, selections)
- Animation states
- Form inputs
- Temporary selections

### Event Handling Mechanisms

#### WebSocket-Based Updates
- All phases use WebSocket for real-time updates
- No polling except for initial sync
- Automatic reconnection with state recovery

#### Enterprise Architecture (Backend)
- All state changes via `update_phase_data()`
- Automatic `phase_change` broadcasts
- JSON-safe serialization
- Complete change history

### Component Communication

#### Props Flow
```
ServiceIntegration
    ↓
GameContainer (orchestrator)
    ↓
Phase-specific UI Components
```

#### Event Flow
```
User Action → GameService → NetworkService → WebSocket → Backend
    ↑                                                        ↓
    ←────────── State Update ←── GameService ←── WebSocket ←┘
```

---

## Data Structures Reference

### Core Game Objects

#### Player
```python
{
  "name": str,
  "hand": List[Piece],
  "declared": int,  # 0-8
  "piles": int,     # Captured piles
  "score": int,     # Total score
  "is_bot": bool,
  "seat_number": int  # 1-4
}
```

#### Piece
```python
{
  "id": int,
  "kind": str,  # e.g., "GENERAL_RED"
  "name": str,  # e.g., "GENERAL"
  "color": str,  # "RED" or "BLACK"
  "point": int,  # Point value
  "symbol": str  # Unicode character
}
```

#### Room
```python
{
  "room_id": str,
  "host_name": str,
  "players": List[Optional[Player]],  # 4 slots
  "started": bool,
  "game": Optional[Game],
  "created_at": datetime
}
```

#### Game State Machine
```python
{
  "current_phase": GamePhase,
  "phase_data": dict,  # Phase-specific data
  "game": Game,
  "room": Room,
  "change_history": List[dict],  # Audit trail
  "sequence_number": int
}
```

### Frontend State Shape

```typescript
interface GameState {
  // Connection
  isConnected: boolean;
  roomId: string | null;
  playerName: string;
  
  // Game phase
  phase: Phase;
  phaseData: any;
  
  // Players
  players: Player[];
  myPlayerData: Player | null;
  
  // Game data
  myHand: Piece[];
  playerPiles: Record<string, number>;
  declarations: Record<string, number>;
  totalScores: Record<string, number>;
  
  // Turn state
  currentPlayer: string | null;
  turnNumber: number;
  requiredPieceCount: number | null;
  
  // Meta
  gameStarted: boolean;
  roundNumber: number;
  turnHistory: TurnPlay[];
}
```

---

## Summary

This documentation provides a complete technical reference for the Liap Tui game implementation. Each phase has clearly defined:

1. **Backend state handlers** with allowed actions
2. **Frontend UI components** with props and state
3. **WebSocket events** for real-time communication
4. **Validation rules** enforced at multiple layers
5. **State structures** for data consistency
6. **Transition logic** for phase progression

The system uses an enterprise architecture pattern with automatic state broadcasting, ensuring reliable synchronization between all connected clients. The frontend maintains a clear separation between global game state and local UI state, while the backend enforces all game rules through a comprehensive state machine implementation.

For UI redesign purposes, each phase has distinct visual requirements and user interactions that should be preserved while updating the visual design. The WebSocket-based architecture ensures real-time updates without polling, providing a smooth multiplayer experience.