# API Contracts - Frontend-Backend Interface Specification

## Table of Contents
1. [Overview](#overview)
2. [WebSocket Event Types](#websocket-event-types)
3. [Message Format Standards](#message-format-standards)
4. [Client-to-Server Events](#client-to-server-events)
5. [Server-to-Client Events](#server-to-client-events)
6. [Error Codes](#error-codes)
7. [State Synchronization](#state-synchronization)
8. [Type Definitions](#type-definitions)
9. [Version Management](#version-management)
10. [Testing Contracts](#testing-contracts)

## Overview

This document defines the complete API contract between the frontend and backend. Since Liap Tui uses WebSocket exclusively for game operations, all contracts are event-based.

### Contract Principles

1. **Type Safety**: All messages have defined schemas
2. **Versioning**: Support for backward compatibility
3. **Validation**: Both sides validate messages
4. **Error Handling**: Clear error codes and messages
5. **State Consistency**: Guaranteed synchronization

## WebSocket Event Types

### Event Categories

```typescript
// Event type definitions
enum EventCategory {
    // Connection events
    CONNECTION = "connection",
    
    // Room management
    ROOM = "room",
    
    // Game flow
    GAME = "game",
    
    // Player actions
    ACTION = "action",
    
    // System events
    SYSTEM = "system",
    
    // Error events
    ERROR = "error"
}

// Complete event type enumeration
enum EventType {
    // Connection events
    CONNECTED = "connected",
    DISCONNECTED = "disconnected",
    RECONNECTED = "reconnected",
    
    // Room events
    CREATE_ROOM = "create_room",
    JOIN_ROOM = "join_room",
    LEAVE_ROOM = "leave_room",
    ROOM_CREATED = "room_created",
    ROOM_JOINED = "room_joined",
    ROOM_LEFT = "room_left",
    PLAYER_JOINED = "player_joined",
    PLAYER_LEFT = "player_left",
    ROOM_LIST = "room_list",
    
    // Game events
    START_GAME = "start_game",
    GAME_STARTED = "game_started",
    PHASE_CHANGE = "phase_change",
    HAND_UPDATED = "hand_updated",
    GAME_OVER = "game_over",
    
    // Action events
    DECLARE = "declare",
    PLAY = "play",
    ACCEPT_REDEAL = "accept_redeal",
    DECLINE_REDEAL = "decline_redeal",
    
    // Response events
    DECLARATION_ACCEPTED = "declaration_accepted",
    PLAY_ACCEPTED = "play_accepted",
    REDEAL_DECISION_ACCEPTED = "redeal_decision_accepted",
    
    // System events
    PING = "ping",
    PONG = "pong",
    SERVER_TIME = "server_time",
    
    // Error events
    ERROR = "error",
    VALIDATION_ERROR = "validation_error"
}
```

## Message Format Standards

### Base Message Structure

```typescript
// All messages follow this base structure
interface BaseMessage {
    event: string;              // Event type
    data?: any;                 // Event-specific data
    timestamp?: number;         // Client timestamp (optional)
    sequence?: number;          // Message sequence number (optional)
    version?: string;           // API version (optional)
}

// Client -> Server message
interface ClientMessage extends BaseMessage {
    event: string;
    data: any;
    client_id?: string;         // Optional client identifier
}

// Server -> Client message
interface ServerMessage extends BaseMessage {
    event: string;
    data?: any;
    room_id?: string;           // Room context
    server_time?: number;       // Server timestamp
    sequence_number?: number;   // Server sequence for ordering
}
```

### Type-Safe Message Definitions

```typescript
// Define specific message types
type ClientEventMap = {
    // Room events
    create_room: {
        room_name: string;
        player_name: string;
        is_public?: boolean;
    };
    
    join_room: {
        player_name: string;
    };
    
    leave_room: {
        player_name: string;
    };
    
    // Game events
    start_game: {
        player_name: string;
    };
    
    // Action events
    declare: {
        player_name: string;
        declaration: number;
    };
    
    play: {
        player_name: string;
        piece_ids: string[];
    };
    
    accept_redeal: {
        player_name: string;
    };
    
    decline_redeal: {
        player_name: string;
    };
    
    // System events
    ping: {
        client_time: number;
    };
};

type ServerEventMap = {
    // Connection events
    connected: {
        connection_id: string;
        room_id: string;
        player_name?: string;
    };
    
    // Room events
    room_created: {
        room_id: string;
        room_name: string;
    };
    
    player_joined: {
        player_name: string;
        position: number;
        is_bot: boolean;
    };
    
    // Game events
    phase_change: {
        phase: GamePhase;
        phase_data: PhaseData;
        game_state: GameState;
        sequence_number: number;
        server_time: number;
    };
    
    // System events
    pong: {
        client_time: number;
        server_time: number;
    };
    
    // Error events
    error: {
        code: string;
        message: string;
        details?: any;
    };
};
```

## Client-to-Server Events

### Room Management

```typescript
// CREATE_ROOM
{
    "event": "create_room",
    "data": {
        "room_name": "Alice's Room",
        "player_name": "Alice",
        "is_public": true
    }
}

// Response: room_created
{
    "event": "room_created",
    "data": {
        "room_id": "ABCD1234",
        "room_name": "Alice's Room",
        "creator": "Alice",
        "created_at": 1673890123.456
    }
}

// JOIN_ROOM
{
    "event": "join_room",
    "data": {
        "player_name": "Bob"
    }
}

// Response: Multiple events
// 1. room_joined (to sender)
{
    "event": "room_joined",
    "data": {
        "room_id": "ABCD1234",
        "room_name": "Alice's Room",
        "players": [
            {"name": "Alice", "position": 0, "is_bot": false},
            {"name": "Bob", "position": 1, "is_bot": false}
        ],
        "game_state": null
    }
}

// 2. player_joined (to others)
{
    "event": "player_joined",
    "data": {
        "player_name": "Bob",
        "position": 1,
        "is_bot": false,
        "timestamp": 1673890130.123
    }
}
```

### Game Actions

```typescript
// START_GAME
{
    "event": "start_game",
    "data": {
        "player_name": "Alice"
    }
}

// Response: phase_change (to all)
{
    "event": "phase_change",
    "data": {
        "phase": "PREPARATION",
        "phase_data": {
            "weak_hands": ["Bob", "Carol"],
            "redeal_multiplier": 1,
            "waiting_for_decisions": true
        },
        "game_state": {
            "round_number": 1,
            "turn_number": 0,
            "players": [...],
            "scores": {"Alice": 0, "Bob": 0, "Carol": 0, "David": 0}
        },
        "sequence_number": 1,
        "server_time": 1673890140.789
    }
}

// DECLARE
{
    "event": "declare",
    "data": {
        "player_name": "Alice",
        "declaration": 3
    }
}

// Response: declaration_accepted (to sender)
{
    "event": "declaration_accepted",
    "data": {
        "player": "Alice",
        "declaration": 3
    }
}

// PLAY
{
    "event": "play",
    "data": {
        "player_name": "Alice",
        "piece_ids": ["p1", "p2"]
    }
}

// Response: play_accepted (to sender)
{
    "event": "play_accepted",
    "data": {
        "player": "Alice",
        "pieces_played": ["p1", "p2"],
        "play_type": "PAIR"
    }
}
```

### Weak Hand Decisions

```typescript
// ACCEPT_REDEAL
{
    "event": "accept_redeal",
    "data": {
        "player_name": "Bob"
    }
}

// DECLINE_REDEAL
{
    "event": "decline_redeal",
    "data": {
        "player_name": "Carol"
    }
}

// Response: redeal_decision_accepted
{
    "event": "redeal_decision_accepted",
    "data": {
        "player": "Bob",
        "decision": "accept"
    }
}

// If redeal happens: phase_change with new hands
{
    "event": "phase_change",
    "data": {
        "phase": "PREPARATION",
        "phase_data": {
            "weak_hands": [],
            "redeal_multiplier": 2,
            "redeal_complete": true
        },
        "game_state": {...}
    }
}
```

## Server-to-Client Events

### Connection Management

```typescript
// CONNECTED
{
    "event": "connected",
    "data": {
        "connection_id": "conn_123abc",
        "room_id": "ABCD1234",
        "player_name": "Alice",
        "reconnected": false
    }
}

// DISCONNECTED
{
    "event": "disconnected",
    "data": {
        "code": 1000,
        "reason": "Normal closure",
        "wasClean": true
    }
}

// RECONNECTED
{
    "event": "reconnected",
    "data": {
        "connection_id": "conn_456def",
        "room_id": "ABCD1234",
        "player_name": "Alice",
        "missed_events": 3,
        "game_state": {...}  // Current state for sync
    }
}
```

### Game State Updates

```typescript
// PHASE_CHANGE - Most important event
{
    "event": "phase_change",
    "data": {
        "phase": "TURN",
        "phase_data": {
            "current_player": "Alice",
            "turn_number": 5,
            "required_piece_count": 2,
            "current_plays": {
                "Alice": {
                    "pieces": [
                        {"id": "p1", "rank": "GENERAL", "color": "RED", "point": 10},
                        {"id": "p2", "rank": "GENERAL", "color": "BLACK", "point": 10}
                    ],
                    "play_type": "PAIR"
                }
            },
            "last_winner": "David",
            "current_pile_count": 8
        },
        "game_state": {
            "round_number": 1,
            "turn_number": 5,
            "players": [
                {
                    "name": "Alice",
                    "position": 0,
                    "score": 15,
                    "is_active": true,
                    "is_bot": false
                },
                // ... other players
            ],
            "pile_counts": {
                "Alice": 2,
                "Bob": 1,
                "Carol": 0,
                "David": 1
            }
        },
        "sequence_number": 42,
        "server_time": 1673890200.123
    }
}

// HAND_UPDATED - Private to each player
{
    "event": "hand_updated",
    "data": {
        "pieces": [
            {"id": "p3", "rank": "ADVISOR", "color": "RED", "point": 10},
            {"id": "p4", "rank": "ELEPHANT", "color": "BLACK", "point": 9},
            // ... remaining pieces
        ],
        "count": 6
    },
    "private": true
}

// GAME_OVER
{
    "event": "game_over",
    "data": {
        "winners": ["Alice"],  // Can be multiple in case of tie
        "final_scores": {
            "Alice": 52,
            "Bob": 45,
            "Carol": 38,
            "David": 41
        },
        "rounds_played": 8,
        "game_duration": 1234.56,  // seconds
        "statistics": {
            "total_turns": 89,
            "perfect_declarations": 3,
            "redeals": 1
        }
    }
}
```

### Special Events

```typescript
// SPECIAL_BONUS - Animated celebrations
{
    "event": "special_bonus",
    "data": {
        "player": "Alice",
        "bonus_type": "PERFECT_DECLARATION",
        "bonus_points": 5,
        "message": "Alice achieved perfect declaration!",
        "animation": "celebration"
    }
}

// PLAYER_TIMEOUT - When player doesn't act
{
    "event": "player_timeout",
    "data": {
        "player": "Bob",
        "action": "declare",
        "auto_action": {
            "type": "declare",
            "value": 0
        },
        "timeout_seconds": 30
    }
}

// BOT_ACTIVATED - When player disconnects
{
    "event": "bot_activated",
    "data": {
        "player": "Carol",
        "reason": "disconnected",
        "bot_difficulty": "medium"
    }
}
```

## Error Codes

### Error Code Structure

```typescript
interface GameError {
    code: string;           // Unique error code
    message: string;        // Human-readable message
    details?: any;          // Additional context
    timestamp: number;      // When error occurred
    recoverable: boolean;   // Can retry?
}

// Error categories and codes
enum ErrorCode {
    // Connection errors (1xxx)
    CONNECTION_FAILED = "1001",
    AUTHENTICATION_FAILED = "1002",
    ROOM_NOT_FOUND = "1003",
    ROOM_FULL = "1004",
    ALREADY_IN_ROOM = "1005",
    
    // Game errors (2xxx)
    GAME_NOT_STARTED = "2001",
    NOT_YOUR_TURN = "2002",
    INVALID_PLAY = "2003",
    INVALID_DECLARATION = "2004",
    ALREADY_DECLARED = "2005",
    NO_PIECES_SELECTED = "2006",
    
    // Validation errors (3xxx)
    INVALID_MESSAGE_FORMAT = "3001",
    MISSING_REQUIRED_FIELD = "3002",
    INVALID_FIELD_TYPE = "3003",
    OUT_OF_RANGE = "3004",
    
    // System errors (4xxx)
    RATE_LIMITED = "4001",
    SERVER_ERROR = "4002",
    MAINTENANCE_MODE = "4003",
    VERSION_MISMATCH = "4004"
}
```

### Error Response Format

```typescript
// Standard error response
{
    "event": "error",
    "error": {
        "code": "2002",
        "message": "It's not your turn",
        "details": {
            "current_player": "Bob",
            "your_position": 2
        },
        "timestamp": 1673890250.789,
        "recoverable": false
    }
}

// Validation error with field details
{
    "event": "validation_error",
    "error": {
        "code": "3002",
        "message": "Missing required fields",
        "details": {
            "missing_fields": ["player_name"],
            "received_data": {
                "declaration": 3
            }
        },
        "timestamp": 1673890260.123,
        "recoverable": true
    }
}
```

## State Synchronization

### Synchronization Protocol

```typescript
// State sync request (client -> server)
{
    "event": "sync_request",
    "data": {
        "last_sequence": 41,        // Last known sequence
        "client_state_hash": "abc123"  // Optional state hash
    }
}

// State sync response (server -> client)
{
    "event": "sync_response",
    "data": {
        "current_sequence": 45,
        "missed_events": [
            // Replay of missed events
            {"sequence": 42, "event": "play_accepted", "data": {...}},
            {"sequence": 43, "event": "phase_change", "data": {...}},
            {"sequence": 44, "event": "hand_updated", "data": {...}},
            {"sequence": 45, "event": "player_action", "data": {...}}
        ],
        "full_state": {
            // Complete current state
            "phase": "TURN",
            "phase_data": {...},
            "game_state": {...}
        }
    }
}
```

### Heartbeat Protocol

```typescript
// Client heartbeat
{
    "event": "ping",
    "data": {
        "client_time": 1673890270000,
        "sequence": 123
    }
}

// Server response
{
    "event": "pong",
    "data": {
        "client_time": 1673890270000,
        "server_time": 1673890270050,
        "latency": 50,  // milliseconds
        "sequence": 123
    }
}
```

## Type Definitions

### Core Game Types

```typescript
// TypeScript definitions for frontend
interface Player {
    name: string;
    position: number;
    score: number;
    is_active: boolean;
    is_bot: boolean;
}

interface Piece {
    id: string;
    rank: PieceRank;
    color: PieceColor;
    point: number;
}

enum PieceRank {
    GENERAL = "GENERAL",
    ADVISOR = "ADVISOR",
    ELEPHANT = "ELEPHANT",
    HORSE = "HORSE",
    CHARIOT = "CHARIOT",
    CANNON = "CANNON",
    SOLDIER = "SOLDIER"
}

enum PieceColor {
    RED = "RED",
    BLACK = "BLACK"
}

enum GamePhase {
    NOT_STARTED = "NOT_STARTED",
    PREPARATION = "PREPARATION",
    DECLARATION = "DECLARATION",
    TURN = "TURN",
    SCORING = "SCORING",
    GAME_OVER = "GAME_OVER"
}

interface PhaseData {
    // Phase-specific data
    [key: string]: any;
}

interface GameState {
    round_number: number;
    turn_number: number;
    players: Player[];
    scores: Record<string, number>;
    phase: GamePhase;
    phase_data: PhaseData;
}
```

### Python Backend Types

```python
# Python type definitions for backend
from typing import Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel

class PieceRank(str, Enum):
    GENERAL = "GENERAL"
    ADVISOR = "ADVISOR"
    ELEPHANT = "ELEPHANT"
    HORSE = "HORSE"
    CHARIOT = "CHARIOT"
    CANNON = "CANNON"
    SOLDIER = "SOLDIER"

class PieceColor(str, Enum):
    RED = "RED"
    BLACK = "BLACK"

class Piece(BaseModel):
    id: str
    rank: PieceRank
    color: PieceColor
    point: int

class Player(BaseModel):
    name: str
    position: int
    score: int = 0
    is_active: bool = True
    is_bot: bool = False

class GamePhase(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    PREPARATION = "PREPARATION"
    DECLARATION = "DECLARATION"
    TURN = "TURN"
    SCORING = "SCORING"
    GAME_OVER = "GAME_OVER"

class ClientMessage(BaseModel):
    event: str
    data: Dict[str, Any]
    client_id: Optional[str] = None
    timestamp: Optional[float] = None

class ServerMessage(BaseModel):
    event: str
    data: Optional[Dict[str, Any]] = None
    room_id: Optional[str] = None
    server_time: Optional[float] = None
    sequence_number: Optional[int] = None
```

## Version Management

### API Versioning

```typescript
// Version in message headers
{
    "event": "connect",
    "version": "1.0.0",
    "data": {...}
}

// Version negotiation
{
    "event": "version_info",
    "data": {
        "client_version": "1.0.0",
        "supported_versions": ["1.0.0", "0.9.0"],
        "minimum_version": "0.9.0"
    }
}

// Server version response
{
    "event": "version_accepted",
    "data": {
        "server_version": "1.0.1",
        "negotiated_version": "1.0.0",
        "features": {
            "weak_hand_redeal": true,
            "bot_players": true,
            "replay_system": false
        }
    }
}
```

### Breaking Changes Policy

```typescript
// Deprecation notice
{
    "event": "deprecation_warning",
    "data": {
        "deprecated_feature": "old_play_format",
        "removal_version": "2.0.0",
        "alternative": "Use 'play' event with piece_ids array",
        "documentation": "https://docs.liaptui.com/migration/v2"
    }
}
```

## Testing Contracts

### Contract Tests

```typescript
// Contract test example
describe('API Contract Tests', () => {
    it('should validate phase_change event', () => {
        const message = {
            event: 'phase_change',
            data: {
                phase: 'TURN',
                phase_data: {
                    current_player: 'Alice',
                    turn_number: 5,
                    required_piece_count: 2
                },
                game_state: {
                    round_number: 1,
                    turn_number: 5,
                    players: []
                },
                sequence_number: 42,
                server_time: 1673890200.123
            }
        };
        
        expect(validateServerMessage(message)).toBe(true);
        expect(message.data.phase).toBeOneOf(Object.values(GamePhase));
        expect(message.data.sequence_number).toBeGreaterThan(0);
    });
});
```

### Mock Server Responses

```typescript
// Mock server for testing
class MockGameServer {
    private sequence = 0;
    
    handleMessage(message: ClientMessage): ServerMessage[] {
        switch (message.event) {
            case 'join_room':
                return [
                    this.createRoomJoined(message.data.player_name),
                    this.createPlayerJoined(message.data.player_name)
                ];
            
            case 'play':
                return [
                    this.createPlayAccepted(
                        message.data.player_name,
                        message.data.piece_ids
                    ),
                    this.createPhaseChange()
                ];
            
            default:
                return [this.createError('UNKNOWN_EVENT')];
        }
    }
    
    private createPhaseChange(): ServerMessage {
        return {
            event: 'phase_change',
            data: {
                phase: 'TURN',
                phase_data: {...},
                game_state: {...},
                sequence_number: ++this.sequence,
                server_time: Date.now() / 1000
            }
        };
    }
}
```

### Validation Schemas

```typescript
// JSON Schema validation
const phaseChangeSchema = {
    type: 'object',
    required: ['event', 'data'],
    properties: {
        event: { const: 'phase_change' },
        data: {
            type: 'object',
            required: ['phase', 'phase_data', 'game_state', 'sequence_number'],
            properties: {
                phase: { enum: Object.values(GamePhase) },
                phase_data: { type: 'object' },
                game_state: { $ref: '#/definitions/gameState' },
                sequence_number: { type: 'integer', minimum: 0 },
                server_time: { type: 'number' }
            }
        }
    }
};

// Validate messages
import Ajv from 'ajv';
const ajv = new Ajv();
const validate = ajv.compile(phaseChangeSchema);

if (!validate(message)) {
    console.error('Validation errors:', validate.errors);
}
```

## Summary

The API contracts provide:

1. **Type Safety**: Complete TypeScript and Python type definitions
2. **Clear Events**: Well-defined event types and payloads
3. **Error Handling**: Comprehensive error codes and recovery
4. **State Sync**: Robust synchronization protocol
5. **Versioning**: Support for API evolution
6. **Testing**: Contract tests and validation

This ensures reliable communication between frontend and backend with clear expectations on both sides.