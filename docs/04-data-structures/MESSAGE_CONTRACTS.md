# Message Contracts and Formats

## Overview

This document defines the complete message contracts and formats for the Liap Tui WebSocket API. It serves as the authoritative source for message schemas, validation rules, and type definitions.

## Table of Contents

1. [Contract Principles](#contract-principles)
2. [Base Message Structure](#base-message-structure)
3. [Type Definitions](#type-definitions)
4. [Event Categories](#event-categories)
5. [Client Messages](#client-messages)
6. [Server Messages](#server-messages)
7. [Validation Rules](#validation-rules)
8. [Message Flow Examples](#message-flow-examples)
9. [Contract Testing](#contract-testing)
10. [Version Management](#version-management)

## Contract Principles

1. **Type Safety**: All messages have strictly defined schemas
2. **Validation**: Both client and server validate all messages
3. **Consistency**: Same patterns across all message types
4. **Extensibility**: Room for additions without breaking changes
5. **Clarity**: Self-documenting field names and structures

## Base Message Structure

### Client → Server Format
```javascript
// Client message structure
{
    event: string;              // Required: Event name
    data: object;               // Required: Event payload

    // Optional metadata
    sequence?: number;          // Client-side sequence number
    timestamp?: number;         // Client timestamp (ms)
    version?: string;           // API version
}
```

### Server → Client Format
```javascript
// Server message structure
{
    event: string;              // Required: Event type
    data: object;               // Required: Event data

    // Optional fields
    error?: {                   // Error information
        code: string;           // Error code
        message: string;        // Human-readable message
        type?: string;          // Error category
        details?: any;          // Additional context
        field?: string;         // Field that caused error
    };
    room_id?: string;           // Room context
    sequence?: number;          // Echo of client sequence
    server_time?: number;       // Server timestamp
    correlation_id?: string;    // Request correlation
}
```

## Type Definitions

### Core Types
```javascript
// Type definitions (JavaScript with JSDoc comments)
/**
 * @typedef {string} PlayerId - Unique player ID
 * @typedef {string} RoomId - Room identifier (6-8 chars)
 * @typedef {string} PieceId - Piece identifier
 */

// Constants for enumerated values
const PieceRank = {
    GENERAL: "GENERAL",
    ADVISOR: "ADVISOR",
    ELEPHANT: "ELEPHANT",
    CHARIOT: "CHARIOT",
    HORSE: "HORSE",
    CANNON: "CANNON",
    SOLDIER: "SOLDIER"
};

const PieceColor = {
    RED: "RED",
    BLACK: "BLACK"
};

const GamePhase = {
    WAITING: "waiting",
    PREPARATION: "preparation",
    ROUND_START: "round_start",  // New phase
    DECLARATION: "declaration",
    TURN: "turn",
    TURN_RESULTS: "turn_results",
    SCORING: "scoring",
    GAME_OVER: "game_over"
};

const PlayType = {
    SINGLE: "SINGLE",
    PAIR: "PAIR",
    TRIPLE: "TRIPLE",
    STRAIGHT: "STRAIGHT",
    DOUBLE_STRAIGHT: "DOUBLE_STRAIGHT",
    MIXED_COLOR: "MIXED_COLOR",
    PASS: "PASS"
};
```

### Data Models
```javascript
/**
 * @typedef {Object} Player
 * @property {string} name - Display name
 * @property {number} slot - Position (1-4)
 * @property {boolean} is_bot - AI player
 * @property {boolean} is_host - Room host
 * @property {boolean} is_connected - Connection status
 * @property {number} [score] - Total score
 * @property {number} [declared] - Declared piles
 * @property {number} [captured_piles] - Actual piles
 * @property {number} [hand_size] - Cards in hand
 * @property {Piece[]} [hand] - Actual hand (private)
 */

/**
 * @typedef {Object} Piece
 * @property {string} id - Unique identifier
 * @property {string} kind - e.g., "GENERAL_RED"
 * @property {string} rank - Piece type
 * @property {string} color - RED or BLACK
 * @property {number} point - Point value
 */

/**
 * @typedef {Object} Room
 * @property {string} room_id - Unique room ID
 * @property {string} host_name - Host player name
 * @property {(Player|null)[]} players - 4 slots
 * @property {boolean} started - Game started
 * @property {RoomSettings} [settings] - Room configuration
 * @property {string} [created_at] - Creation timestamp
 */

/**
 * @typedef {Object} RoomSettings
 * @property {number} max_players - Always 4
 * @property {boolean} is_public - Public visibility
 * @property {boolean} allow_bots - Bot players allowed
 * @property {number} [time_limit] - Turn time limit (seconds)
 */
```

## Event Categories

### Event Classification
```javascript
const EventCategory = {
    // Connection lifecycle
    CONNECTION: "connection",   // ready, ping, sync

    // Room management
    ROOM: "room",              // create, join, leave

    // Game flow
    GAME: "game",              // start, phase changes

    // Player actions
    ACTION: "action",          // declare, play, redeal

    // System events
    SYSTEM: "system",          // errors, broadcasts
};

// Event naming convention: category_action
// Examples: room_create, game_start, action_play
```

## Client Messages

### Connection Events

#### client_ready
```javascript
// Client ready message
{
    event: "client_ready",
    data: {}
}

#### ping
```javascript
// Ping message for keepalive
{
    event: "ping",
    data: {
        timestamp: number,      // Client time in ms
        sequence?: number       // Optional sequence
    }
}

### Room Management

#### create_room
```javascript
// Create room request
{
    event: "create_room",
    data: {
        player_name: string,    // 1-50 characters
        settings?: {
            is_public?: boolean,   // Default: true
            allow_bots?: boolean   // Default: true
        }
    }
}

// Validation
const playerNameRegex = /^[a-zA-Z0-9 ]+$/;
const maxNameLength = 50;

#### join_room
```javascript
// Join room request
{
    event: "join_room",
    data: {
        room_id: string,        // Target room
        player_name: string,    // Player name
        rejoin_token?: string   // For reconnection
    }
}

### Game Actions

#### declare
```javascript
// Declaration request
{
    event: "declare",
    data: {
        player_name: string,    // Must match connected player
        value: number           // 0-8, total ≠ 8
    }
}

// Validation
const isValidDeclaration = (value, totalSoFar, isLastPlayer) => {
    if (value < 0 || value > 8) return false;
    if (isLastPlayer && totalSoFar + value === 8) return false;
    return true;
};

#### play / play_pieces
```javascript
// Play pieces request
{
    event: "play" | "play_pieces",
    data: {
        player_name: string,    // Must match connected player
        indices: number[],      // Hand indices (0-based)
        // OR
        piece_indices?: number[] // Alternative field name
    }
}

// Validation
const isValidPlay = (indices, handSize, requiredCount) => {
    if (indices.length < 1 || indices.length > 6) return false;
    if (indices.some(i => i < 0 || i >= handSize)) return false;
    if (requiredCount && indices.length !== requiredCount) return false;
    return true;
};

## Server Messages

### Room Events

#### room_created
```javascript
// Room created response
{
    event: "room_created",
    data: {
        room_id: string,        // New room ID
        host_name: string,      // Creator name
        success: boolean,       // Always true
        join_token?: string     // For direct join
    }
}

#### room_update
```javascript
// Room state update
{
    event: "room_update",
    data: {
        room_id: string,
        host_name: string,
        started: boolean,
        players: Array<{
            slot: number,       // 1-4
            name: string,
            is_bot: boolean,
            is_host: boolean,
            is_connected: boolean
        } | null>,              // null for empty slots

        // Optional fields
        settings?: RoomSettings,
        spectators?: number     // Count of spectators
    }
}

### Game State Events

#### phase_change
```javascript
// Phase change notification
{
    event: "phase_change",
    data: {
        // Core fields
        phase: GamePhase,       // Current phase
        round: number,          // Round number (1+)
        sequence: number,       // Event sequence
        timestamp: number,      // Server timestamp
        reason: string,         // Human-readable reason

        // Game context
        allowed_actions: string[], // Available actions
        timeout?: number,       // Phase timeout (seconds)

        // Phase-specific data
        phase_data: PhaseData,  // Varies by phase

        // Player states
        players: Record<string, PlayerState>
    }
}

// Phase-specific data types
// PhaseData can be one of:
// - PreparationData
// - RoundStartData (new)
// - DeclarationData
// - TurnData
// - TurnResultsData
// - ScoringData
// - GameOverData

/**
 * @typedef {Object} RoundStartData
 * @property {number} round_number - Current round
 * @property {string} round_starter - Player who starts
 * @property {string} starter_reason - Why they start
 */

/**
 * @typedef {Object} DeclarationData
 * @property {string} current_declarer - Active player
 * @property {string[]} declaration_order - Turn order
 * @property {Object.<string, number|null>} declarations
 * @property {number} total_declared - Sum so far
 * @property {number} redeal_multiplier - Score multiplier
 */

/**
 * @typedef {Object} TurnData
 * @property {number} turn_number - Current turn
 * @property {string} current_player - Active player
 * @property {number|null} required_piece_count
 * @property {Object.<string, Play>} current_plays
 * @property {string[]} passes - Who passed
 * @property {number} pile_count - Pieces in pile
 */

### Error Messages

#### error
```javascript
// Error message
{
    event: "error",
    data: {
        message: string,        // User-friendly message
        type: ErrorType,        // Category
        code: string,           // Error code

        // Optional context
        details?: any,          // Additional info
        field?: string,         // Related field
        recovery?: string       // Suggested action
    },

    // Correlation
    sequence?: number,          // Echo request sequence
    correlation_id?: string     // Request correlation
}

const ErrorType = {
    VALIDATION: "validation_error",
    PERMISSION: "permission_error",
    GAME_STATE: "game_error",
    CONNECTION: "connection_error",
    SYSTEM: "system_error"
};

## Validation Rules

### Input Sanitization
```javascript
// Text fields
const sanitizeText = (text) => {
    return text
        .replace(/[<>&"']/g, '') // Remove HTML chars
        .trim()
        .substring(0, 50);       // Length limit
};

// Arrays
const validateArray = (arr, maxLength = 100) => {
    return Array.isArray(arr) && arr.length <= maxLength;
};
```

### Field Validation
```javascript
const ValidationRules = {
    player_name: {
        type: 'string',
        pattern: /^[a-zA-Z0-9 ]+$/,
        minLength: 1,
        maxLength: 50
    },

    room_id: {
        type: 'string',
        pattern: /^[A-Z0-9]{6,8}$/,
        minLength: 6,
        maxLength: 8
    },

    declaration: {
        type: 'number',
        min: 0,
        max: 8,
        integer: true
    },

    piece_indices: {
        type: 'array',
        minItems: 0,
        maxItems: 6,
        items: {
            type: 'number',
            min: 0,
            max: 31
        }
    }
};

### Business Rules
```javascript
// Declaration validation
const validateDeclaration = (
    value,
    totalSoFar,
    isLastPlayer,
    previousZeros
) => {
    // Basic range
    if (value < 0 || value > 8) return false;

    // Can't make total = 8
    if (isLastPlayer && totalSoFar + value === 8) return false;

    // After 2 zeros, must declare non-zero
    if (previousZeros >= 2 && value === 0) return false;

    return true;
};

// Play validation
const validatePlay = (
    pieces,
    requiredCount
) => {
    // Check count
    if (requiredCount && pieces.length !== requiredCount) return false;

    // Check valid combination
    return isValidCombination(pieces);
};

## Message Flow Examples

### Complete Game Creation Flow
```javascript
// 1. Alice connects to lobby
→ ws://localhost:8000/ws/lobby
← (connection established)

// 2. Client ready
→ { event: "client_ready", data: {} }

// 3. Create room
→ {
    event: "create_room",
    data: { player_name: "Alice" }
}
← {
    event: "room_created",
    data: {
        room_id: "ROOM123",
        host_name: "Alice"
    }
}

// 4. Disconnect from lobby, connect to room
→ ws://localhost:8000/ws/ROOM123
← (connection established)

// 5. Client ready for room
→ { event: "client_ready", data: {} }
← {
    event: "room_update",
    data: {
        room_id: "ROOM123",
        players: [{ name: "Alice", slot: 1, ... }]
    }
}

// 6. Add bots
→ { event: "add_bot", data: { slot_id: 2 } }
← { event: "room_update", data: { ... } }
// Repeat for slots 3 and 4

// 7. Start game
→ { event: "start_game", data: {} }
← { event: "game_started", data: { success: true } }
← {
    event: "phase_change",
    data: { phase: "preparation", ... }
}
← {
    event: "phase_change",
    data: { phase: "round_start", ... }
}

### Turn Sequence Flow
```javascript
// 1. Turn starts
← {
    event: "phase_change",
    data: {
        phase: "turn",
        phase_data: {
            current_player: "Alice",
            required_piece_count: null
        }
    }
}

// 2. Alice plays
→ {
    event: "play",
    data: {
        player_name: "Alice",
        indices: [0, 1]
    }
}

// 3. Update for all players
← {
    event: "phase_change",
    data: {
        phase: "turn",
        phase_data: {
            current_player: "Bob",
            required_piece_count: 2,
            current_plays: {
                "Alice": { pieces: [...], type: "PAIR" }
            }
        }
    }
}

// 4. Continue until all play/pass
// ...

// 5. Show results
← {
    event: "phase_change",
    data: {
        phase: "turn_results",
        phase_data: {
            winner: "Carol",
            winning_play: { ... },
            all_plays: [ ... ]
        }
    }
}

### Error Handling Flow
```javascript
// 1. Invalid action
→ {
    event: "play",
    data: {
        player_name: "Alice",
        indices: [0, 1, 2]  // Wrong count
    },
    sequence: 42
}

// 2. Error response
← {
    event: "error",
    data: {
        message: "Must play 2 pieces",
        type: "validation_error",
        code: "INVALID_PIECE_COUNT",
        details: {
            required: 2,
            provided: 3
        }
    },
    sequence: 42
}

// 3. Retry with correct count
→ {
    event: "play",
    data: {
        player_name: "Alice",
        indices: [0, 1]
    },
    sequence: 43
}

// 4. Success
← { event: "phase_change", data: { ... } }

## Contract Testing

### Schema Validation
```javascript
import Ajv from 'ajv';

const ajv = new Ajv();

// Define schemas
const schemas = {
    create_room: {
        type: 'object',
        required: ['event', 'data'],
        properties: {
            event: { const: 'create_room' },
            data: {
                type: 'object',
                required: ['player_name'],
                properties: {
                    player_name: {
                        type: 'string',
                        pattern: '^[a-zA-Z0-9 ]+$',
                        minLength: 1,
                        maxLength: 50
                    }
                }
            }
        }
    }
};

// Validate message
const validate = ajv.compile(schemas.create_room);
const valid = validate(message);
if (!valid) {
    console.error(validate.errors);
}
```

### Contract Tests
```javascript
describe('Message Contracts', () => {
    it('should validate create_room message', () => {
        const message = {
            event: 'create_room',
            data: { player_name: 'Alice' }
        };

        expect(validateMessage(message)).toBe(true);
    });

    it('should reject invalid player name', () => {
        const message = {
            event: 'create_room',
            data: { player_name: '<script>' }
        };

        const result = validateMessage(message);
        expect(result.valid).toBe(false);
        expect(result.errors[0].field).toBe('player_name');
    });
});
```

### Integration Contract Tests
```python
import pytest
from websocket_client import GameClient

@pytest.mark.contract
async def test_room_creation_contract():
    """Test complete room creation flow matches contract"""
    client = GameClient()

    # Connect and create room
    await client.connect("lobby")
    response = await client.create_room("TestPlayer")

    # Verify response format
    assert response["event"] == "room_created"
    assert "room_id" in response["data"]
    assert len(response["data"]["room_id"]) in range(6, 9)
```

## Version Management

### API Versioning
```javascript
// Client includes version
{
    event: "client_ready",
    data: {},
    version: "2.0"
}

// Server may respond with version info
{
    event: "server_ready",
    data: {
        version: "2.0",
        min_version: "1.5",
        features: ["websocket", "ai_players"]
    }
}

### Breaking Changes Policy
1. **Minor versions** (2.0 → 2.1): Backward compatible
2. **Major versions** (2.x → 3.0): May break compatibility
3. **Deprecation period**: 3 months minimum
4. **Version negotiation**: Client/server agree on version

### Backward Compatibility
```javascript
// Support multiple message formats
const handlePlay = (data) => {
    // New format
    const indices = data.indices || data.piece_indices;

    // Legacy format support
    if (data.pieces) {
        return handleLegacyPlay(data.pieces);
    }

    return processPlay(indices);
};

## Best Practices

1. **Always validate** both client and server side
2. **Use consistent naming** across all messages
3. **Include correlation IDs** for tracking
4. **Version your API** from the start
5. **Document all changes** in changelog
6. **Test contracts** automatically
7. **Monitor contract violations** in production

## Security Considerations

1. **Input sanitization** - Remove dangerous characters
2. **Length limits** - Prevent resource exhaustion
3. **Rate limiting** - Prevent spam/DOS
4. **Type validation** - Ensure correct data types
5. **Permission checks** - Validate authorization
6. **Audit logging** - Track sensitive operations

---

*Last Updated: January 2025*
*This is the authoritative message contract specification*
