# WebSocket Message Formats - Complete Schema Reference

## Table of Contents
1. [Overview](#overview)
2. [Message Structure](#message-structure)
3. [Client → Server Messages](#client--server-messages)
4. [Server → Client Messages](#server--client-messages)
5. [Error Messages](#error-messages)
6. [Lobby Messages](#lobby-messages)
7. [Room Messages](#room-messages)
8. [Game Messages](#game-messages)
9. [Special Messages](#special-messages)
10. [Message Flow Examples](#message-flow-examples)

## Overview

This document provides a comprehensive reference for all WebSocket message formats used in the Liap Tui application. All messages are JSON-encoded text messages following a consistent structure.

### Design Principles

1. **Consistency**: All messages follow the same base structure
2. **Type Safety**: Clear field types and validation rules
3. **Extensibility**: Room for future additions without breaking changes
4. **Debugging**: Human-readable format for easy debugging

## Message Structure

### Base Message Format

All messages follow this base structure:

```typescript
// Client → Server
interface ClientMessage {
  event: string;        // Event type (e.g., "play", "declare")
  data: any;           // Event-specific payload
  room_id: string;     // Target room ID
  sequence?: number;   // Optional client sequence number
  timestamp?: number;  // Optional client timestamp
}

// Server → Client
interface ServerMessage {
  event: string;        // Event type
  data: any;           // Event-specific payload
  error?: {            // Optional error information
    code: string;
    message: string;
    details?: any;
  };
  room_id?: string;    // Room context (if applicable)
  sequence?: number;   // Echo of client sequence
  server_time?: number; // Server timestamp
}
```

### Data Type Definitions

```typescript
// Common types used across messages
type PlayerId = string;
type RoomId = string;
type PieceId = string;

interface Player {
  name: string;
  score: number;
  position: number;
  is_host: boolean;
  is_bot: boolean;
  connection_status: 'connected' | 'disconnected';
}

interface Piece {
  id: string;
  rank: 'GENERAL' | 'ADVISOR' | 'ELEPHANT' | 'HORSE' | 
        'CHARIOT' | 'CANNON' | 'SOLDIER';
  color: 'RED' | 'BLACK';
  point: number;
}

interface Room {
  room_id: string;
  host: string;
  players: string[];
  settings: {
    max_players: number;
    is_public: boolean;
    allow_bots: boolean;
  };
  state: 'WAITING' | 'STARTING' | 'IN_GAME' | 'FINISHED';
}
```

## Client → Server Messages

### Connection Messages

#### Join Room
```json
{
  "event": "join_room",
  "data": {
    "player_name": "Alice",
    "room_code": "ABCD1234"
  },
  "room_id": "lobby",
  "sequence": 1
}
```

#### Leave Room
```json
{
  "event": "leave_room",
  "data": {
    "player_name": "Alice"
  },
  "room_id": "ABCD1234",
  "sequence": 2
}
```

#### Heartbeat
```json
{
  "event": "ping",
  "data": {},
  "room_id": "ABCD1234",
  "sequence": 3
}
```

### Room Management Messages

#### Create Room
```json
{
  "event": "create_room",
  "data": {
    "player_name": "Alice",
    "room_settings": {
      "max_players": 4,
      "is_public": true,
      "allow_bots": true
    }
  },
  "room_id": "lobby",
  "sequence": 4
}
```

#### Start Game
```json
{
  "event": "start_game",
  "data": {
    "player_name": "Alice"
  },
  "room_id": "ABCD1234",
  "sequence": 5
}
```

### Game Action Messages

#### Declare Piles
```json
{
  "event": "declare",
  "data": {
    "player_name": "Alice",
    "declaration": 3
  },
  "room_id": "ABCD1234",
  "sequence": 6
}
```

#### Play Pieces
```json
{
  "event": "play",
  "data": {
    "player_name": "Alice",
    "piece_ids": ["p1", "p2", "p3"]
  },
  "room_id": "ABCD1234",
  "sequence": 7
}
```

#### Accept Redeal
```json
{
  "event": "accept_redeal",
  "data": {
    "player_name": "Alice"
  },
  "room_id": "ABCD1234",
  "sequence": 8
}
```

#### Decline Redeal
```json
{
  "event": "decline_redeal",
  "data": {
    "player_name": "Alice"
  },
  "room_id": "ABCD1234",
  "sequence": 9
}
```

## Server → Client Messages

### Connection Response Messages

#### Join Success
```json
{
  "event": "joined_room",
  "data": {
    "room": {
      "room_id": "ABCD1234",
      "host": "Alice",
      "players": ["Alice", "Bob"],
      "settings": {
        "max_players": 4,
        "is_public": true
      },
      "state": "WAITING"
    },
    "is_reconnection": false
  },
  "sequence": 1
}
```

#### Heartbeat Response
```json
{
  "event": "pong",
  "data": {
    "server_time": 1673890123456
  },
  "sequence": 3
}
```

### Room Update Messages

#### Player Joined
```json
{
  "event": "player_joined",
  "data": {
    "player": "Bob",
    "players": ["Alice", "Bob"],
    "total": 2
  },
  "room_id": "ABCD1234"
}
```

#### Player Left
```json
{
  "event": "player_left",
  "data": {
    "player": "Bob",
    "players": ["Alice"],
    "total": 1,
    "new_host": "Alice"
  },
  "room_id": "ABCD1234"
}
```

#### Room Created
```json
{
  "event": "room_created",
  "data": {
    "room_id": "ABCD1234",
    "host": "Alice",
    "players": ["Alice"],
    "settings": {
      "max_players": 4,
      "is_public": true
    }
  }
}
```

### Game State Messages

#### Game Started
```json
{
  "event": "game_started",
  "data": {
    "room_id": "ABCD1234",
    "game_state": {
      "phase": "PREPARATION",
      "round_number": 1,
      "players": [
        {
          "name": "Alice",
          "position": 0,
          "score": 0,
          "is_host": true,
          "is_bot": false
        },
        {
          "name": "Bob",
          "position": 1,
          "score": 0,
          "is_host": false,
          "is_bot": false
        }
      ]
    }
  },
  "room_id": "ABCD1234"
}
```

#### Phase Change
```json
{
  "event": "phase_change",
  "data": {
    "phase": "DECLARATION",
    "phase_data": {
      "declarations": {
        "Alice": null,
        "Bob": null,
        "Carol": null,
        "David": null
      },
      "waiting_for": ["Alice", "Bob", "Carol", "David"],
      "timeout": 30,
      "sequence_number": 5,
      "timestamp": 1673890123456
    },
    "game_state": {
      "round_number": 1,
      "turn_number": 0,
      "scores": {
        "Alice": 0,
        "Bob": 0,
        "Carol": 0,
        "David": 0
      }
    },
    "reason": "All players received cards"
  },
  "room_id": "ABCD1234"
}
```

#### Hand Update
```json
{
  "event": "hand_updated",
  "data": {
    "pieces": [
      {
        "id": "p1",
        "rank": "GENERAL",
        "color": "RED",
        "point": 10
      },
      {
        "id": "p2",
        "rank": "ADVISOR",
        "color": "BLACK",
        "point": 10
      },
      {
        "id": "p3",
        "rank": "ELEPHANT",
        "color": "RED",
        "point": 9
      }
    ],
    "total": 8
  },
  "room_id": "ABCD1234",
  "private": true
}
```

### Turn-Specific Messages

#### Turn Results
```json
{
  "event": "phase_change",
  "data": {
    "phase": "TURN_RESULTS",
    "phase_data": {
      "plays": [
        {
          "player": "Alice",
          "pieces": [
            {"rank": "GENERAL", "color": "RED", "point": 10},
            {"rank": "ADVISOR", "color": "BLACK", "point": 10}
          ],
          "play_type": "MIXED_COLOR"
        },
        {
          "player": "Bob",
          "pieces": [
            {"rank": "HORSE", "color": "RED", "point": 7},
            {"rank": "HORSE", "color": "RED", "point": 7}
          ],
          "play_type": "PAIR"
        },
        {
          "player": "Carol",
          "pieces": [],
          "play_type": "PASS"
        }
      ],
      "winner": "Alice",
      "winning_play_type": "MIXED_COLOR",
      "pile_size": 5
    }
  },
  "room_id": "ABCD1234"
}
```

### Scoring Messages

#### Round Scoring
```json
{
  "event": "phase_change",
  "data": {
    "phase": "SCORING",
    "phase_data": {
      "round_number": 1,
      "scores": {
        "Alice": {
          "declared": 3,
          "captured": 3,
          "difference": 0,
          "points": 9,
          "round_total": 9,
          "game_total": 9
        },
        "Bob": {
          "declared": 2,
          "captured": 1,
          "difference": -1,
          "points": -3,
          "round_total": -3,
          "game_total": -3
        }
      },
      "multiplier": 1,
      "special_scoring": []
    }
  },
  "room_id": "ABCD1234"
}
```

### Game Over Message

```json
{
  "event": "phase_change",
  "data": {
    "phase": "GAME_OVER",
    "phase_data": {
      "winners": ["Alice"],
      "final_scores": {
        "Alice": 52,
        "Bob": 31,
        "Carol": 28,
        "David": 15
      },
      "win_condition": "FIRST_TO_50",
      "rounds_played": 7,
      "game_duration": 1234567,
      "statistics": {
        "total_piles": 112,
        "largest_pile": 8,
        "perfect_declarations": {
          "Alice": 4,
          "Bob": 2,
          "Carol": 3,
          "David": 1
        }
      }
    }
  },
  "room_id": "ABCD1234"
}
```

## Error Messages

### Standard Error Format

```json
{
  "event": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context"
    }
  },
  "sequence": 10
}
```

### Common Error Codes

#### Room Errors
```json
{
  "event": "error",
  "error": {
    "code": "ROOM_NOT_FOUND",
    "message": "The room ABCD1234 does not exist",
    "details": {
      "room_id": "ABCD1234"
    }
  }
}
```

```json
{
  "event": "error",
  "error": {
    "code": "ROOM_FULL",
    "message": "The room is already at maximum capacity",
    "details": {
      "current_players": 4,
      "max_players": 4
    }
  }
}
```

#### Game Errors
```json
{
  "event": "error",
  "error": {
    "code": "NOT_YOUR_TURN",
    "message": "It's not your turn to play",
    "details": {
      "current_player": "Bob",
      "your_name": "Alice"
    }
  }
}
```

```json
{
  "event": "error",
  "error": {
    "code": "INVALID_PLAY",
    "message": "Cannot play pieces of different colors",
    "details": {
      "pieces": ["GENERAL_RED", "ADVISOR_BLACK"],
      "reason": "color_mismatch"
    }
  }
}
```

## Lobby Messages

### Room List Update
```json
{
  "event": "room_list",
  "data": {
    "rooms": [
      {
        "room_id": "ABCD1234",
        "host": "Alice",
        "players": 2,
        "max_players": 4,
        "created_at": "2024-01-15T10:30:00Z"
      },
      {
        "room_id": "EFGH5678",
        "host": "Charlie",
        "players": 3,
        "max_players": 4,
        "created_at": "2024-01-15T10:25:00Z"
      }
    ],
    "total": 2
  }
}
```

## Room Messages

### Player Status Updates

#### Player Disconnected
```json
{
  "event": "player_disconnected",
  "data": {
    "player": "Bob",
    "bot_activated": true,
    "timeout": 300
  },
  "room_id": "ABCD1234"
}
```

#### Player Reconnected
```json
{
  "event": "player_reconnected",
  "data": {
    "player": "Bob",
    "bot_deactivated": true
  },
  "room_id": "ABCD1234"
}
```

### Host Transfer
```json
{
  "event": "host_changed",
  "data": {
    "old_host": "Alice",
    "new_host": "Bob",
    "reason": "host_left"
  },
  "room_id": "ABCD1234"
}
```

## Game Messages

### Special Game Events

#### Weak Hand Notification
```json
{
  "event": "weak_hand_detected",
  "data": {
    "players_with_weak_hands": ["Bob", "Carol"],
    "redeal_multiplier": 1,
    "waiting_for_responses": true,
    "timeout": 30
  },
  "room_id": "ABCD1234"
}
```

#### Redeal Result
```json
{
  "event": "redeal_complete",
  "data": {
    "accepted_by": ["Bob"],
    "declined_by": ["Carol"],
    "new_multiplier": 2,
    "cards_redealt": true
  },
  "room_id": "ABCD1234"
}
```

#### Bot Action
```json
{
  "event": "bot_action",
  "data": {
    "player": "Bob",
    "action_type": "play",
    "action_data": {
      "piece_ids": ["p4", "p5"]
    },
    "thinking_time": 2.5
  },
  "room_id": "ABCD1234"
}
```

## Special Messages

### Custom Events

The state machine can broadcast custom events:

```json
{
  "event": "special_combo",
  "data": {
    "player": "Alice",
    "combo_type": "DOUBLE_GENERAL",
    "bonus_points": 10,
    "message": "Alice played a Double General!"
  },
  "room_id": "ABCD1234"
}
```

### Debug Messages

For development environments:

```json
{
  "event": "debug_state",
  "data": {
    "current_phase": "TURN",
    "sequence_number": 42,
    "phase_data": { /* ... */ },
    "recent_changes": [ /* ... */ ],
    "performance_metrics": {
      "broadcast_time": 2.3,
      "state_update_time": 1.1
    }
  },
  "room_id": "ABCD1234"
}
```

## Message Flow Examples

### Complete Game Start Flow

```javascript
// 1. Alice creates room
→ {"event": "create_room", "data": {"player_name": "Alice"}}
← {"event": "room_created", "data": {"room_id": "ABCD1234"}}

// 2. Bob joins
→ {"event": "join_room", "data": {"player_name": "Bob", "room_code": "ABCD1234"}}
← {"event": "joined_room", "data": {"room": {...}}}
← {"event": "player_joined", "data": {"player": "Bob", "total": 2}}

// 3. Carol and David join (similar flow)
// ...

// 4. Alice starts game
→ {"event": "start_game", "data": {"player_name": "Alice"}}
← {"event": "game_started", "data": {"game_state": {...}}}
← {"event": "phase_change", "data": {"phase": "PREPARATION"}}
← {"event": "hand_updated", "data": {"pieces": [...]}} // To each player
```

### Complete Turn Flow

```javascript
// 1. Turn starts
← {"event": "phase_change", "data": {"phase": "TURN", "phase_data": {"current_player": "Alice"}}}

// 2. Alice plays
→ {"event": "play", "data": {"player_name": "Alice", "piece_ids": ["p1", "p2"]}}

// 3. Other players notified
← {"event": "phase_change", "data": {"phase": "TURN", "phase_data": {"current_plays": {...}}}}

// 4. All players complete
// ...

// 5. Show results
← {"event": "phase_change", "data": {"phase": "TURN_RESULTS", "phase_data": {"winner": "Alice"}}}

// 6. Next turn or scoring
← {"event": "phase_change", "data": {"phase": "TURN"}} // OR
← {"event": "phase_change", "data": {"phase": "SCORING"}}
```

### Error Handling Flow

```javascript
// 1. Invalid action attempt
→ {"event": "play", "data": {"player_name": "Alice", "piece_ids": ["p1", "p5"]}}

// 2. Error response
← {
  "event": "error",
  "error": {
    "code": "INVALID_PLAY",
    "message": "Cannot play pieces of different colors",
    "details": {
      "pieces": ["GENERAL_RED", "HORSE_BLACK"]
    }
  },
  "sequence": 15
}

// 3. Client handles error and retries
→ {"event": "play", "data": {"player_name": "Alice", "piece_ids": ["p1", "p3"]}}

// 4. Success
← {"event": "phase_change", "data": {"phase": "TURN", "phase_data": {...}}}
```

## Message Validation

### Required Fields

All messages must include:
- `event`: Non-empty string
- `data`: Object (can be empty {})

Client messages must include:
- `room_id`: Valid room identifier

### Field Constraints

```typescript
// Validation rules
interface ValidationRules {
  player_name: {
    type: 'string';
    minLength: 1;
    maxLength: 20;
    pattern: /^[a-zA-Z0-9_-]+$/;
  };
  
  declaration: {
    type: 'number';
    min: 0;
    max: 8;
    integer: true;
  };
  
  piece_ids: {
    type: 'array';
    minItems: 0;
    maxItems: 6;
    items: {
      type: 'string';
      pattern: /^p\d+$/;
    };
  };
  
  room_id: {
    type: 'string';
    length: 8;
    pattern: /^[A-Z0-9]{8}$/;
  };
}
```

## Summary

The message format system provides:

1. **Consistency**: All messages follow the same structure
2. **Type Safety**: Clear types and validation rules
3. **Extensibility**: Easy to add new message types
4. **Debugging**: Human-readable format
5. **Completeness**: Covers all game scenarios

This comprehensive message format ensures reliable communication between client and server throughout the game lifecycle.