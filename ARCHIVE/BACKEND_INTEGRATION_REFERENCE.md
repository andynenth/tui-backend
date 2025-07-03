# 🔌 **BACKEND INTEGRATION REFERENCE**

## **Overview**
This document provides a complete reference for connecting the new frontend architecture to the existing backend system. The backend is production-ready with a complete state machine, comprehensive WebSocket communication, and full bot integration.

---

## **📁 BACKEND DIRECTORY STRUCTURE**

```
backend/
├── api/
│   └── routes/
│       ├── routes.py          # REST API endpoints
│       └── ws.py             # WebSocket event handlers ⭐ CRITICAL
├── engine/
│   ├── game.py               # Core Game class
│   ├── room.py               # Room management
│   ├── bot_manager.py        # Bot AI logic ⭐ PRODUCTION READY
│   └── state_machine/        # ⭐ COMPLETE STATE SYSTEM
│       ├── game_state_machine.py
│       └── states/
│           ├── preparation_state.py
│           ├── declaration_state.py
│           ├── turn_state.py
│           └── scoring_state.py
├── socket_manager.py         # WebSocket connection management
└── shared_instances.py       # Singleton managers
```

---

## **🌐 WEBSOCKET COMMUNICATION PROTOCOL**

### **Connection Endpoints**
```javascript
// Room-specific game communication
const gameWs = new WebSocket(`ws://localhost:5050/ws/${roomId}`);

// Lobby for room discovery
const lobbyWs = new WebSocket('ws://localhost:5050/ws/lobby');
```

### **Message Format**
```javascript
// Standard WebSocket message structure
{
  event: "event_name",
  data: { /* event-specific payload */ }
}
```

---

## **📤 EVENTS BACKEND SENDS TO FRONTEND**

### **🏠 Lobby Events**
```javascript
// Room list updates (sent automatically)
{
  event: "room_list_update",
  data: {
    rooms: [
      {
        room_id: "ABC123",
        host_name: "PlayerName", 
        occupied_slots: 2,
        total_slots: 4,
        started: false
      }
    ],
    timestamp: 1735234567890,
    reason: "new_room_created" | "room_updated" | "room_closed"
  }
}

// Room creation confirmation (direct response)
{
  event: "room_created",
  data: {
    room_id: "ABC123",
    host_name: "PlayerName",
    success: true
  }
}

// Room joining confirmation (direct response)
{
  event: "room_joined", 
  data: {
    room_id: "ABC123",
    player_name: "PlayerName",
    assigned_slot: 2,
    success: true
  }
}
```

### **🎮 Room Management Events**
```javascript
// Room state updates (broadcast to all room clients)
{
  event: "room_update",
  data: {
    players: {
      P1: {name: "HostName", is_bot: false, is_host: true},
      P2: {name: "PlayerName", is_bot: false, is_host: false}, 
      P3: {name: "Bot 3", is_bot: true, is_host: false},
      P4: null
    },
    host_name: "HostName",
    room_id: "ABC123",
    started: false
  }
}

// Player kicked notification
{
  event: "player_kicked",
  data: {
    player: "PlayerName",
    reason: "Host assigned a bot to your slot"
  }
}

// Room closure notification
{
  event: "room_closed",
  data: {
    message: "Room closed by host", 
    reason: "host_left"
  }
}
```

### **🎯 Game Phase Events**
```javascript
// Phase transitions with complete game state ⭐ MOST IMPORTANT
{
  event: "phase_change",
  data: {
    phase: "preparation" | "declaration" | "turn" | "scoring",
    allowed_actions: ["declare", "play_pieces", "accept_redeal"],
    phase_data: {
      // PREPARATION PHASE
      weak_players: ["Bot 2"],
      current_weak_player: "Bot 2", 
      redeal_multiplier: 1,
      
      // DECLARATION PHASE  
      declaration_order: ["Bot 2", "Bot 3", "Bot 4", "Andy"],
      current_declarer_index: 2,
      declarations: {
        "Bot 2": 2,
        "Bot 3": 1
      },
      declaration_total: 3,
      
      // TURN PHASE
      current_turn_starter: "Bot 2",
      turn_order: ["Bot 2", "Bot 3", "Bot 4", "Andy"],
      current_turn_plays: [
        {player: "Bot 2", pieces: ["R1", "B5"], piece_count: 2}
      ],
      required_piece_count: 2,
      
      // SCORING PHASE
      round_scores: {"Andy": 5, "Bot 2": -2},
      total_scores: {"Andy": 15, "Bot 2": 8},
      game_over: false,
      winners: []
    },
    players: {
      "Andy": {
        hand: ["GENERAL_RED", "SOLDIER_BLUE_5", "CAVALRY_GREEN_3"],
        hand_size: 8,
        declared: 0,
        pile_count: 0,
        score: 15
      },
      "Bot 2": {
        hand: ["CHARIOT_BLACK_7", "ELEPHANT_RED_10"],
        hand_size: 8,
        declared: 2,
        pile_count: 0, 
        score: 8
      }
    }
  }
}

// Bot/Player declarations (broadcast to all)
{
  event: "declare",
  data: {
    player: "Bot 2",
    value: 2,
    is_bot: true
  }
}

// Piece playing (broadcast to all)
{
  event: "play", 
  data: {
    player: "Andy",
    pieces: ["GENERAL_RED", "SOLDIER_BLUE_5"],
    indices: [0, 1],
    valid: true,
    play_type: "PAIR"
  }
}

// Turn resolution (broadcast to all)
{
  event: "turn_resolved",
  data: {
    plays: [
      {player: "Andy", pieces: ["R1", "B5"], piece_count: 2},
      {player: "Bot 2", pieces: ["G3", "G4"], piece_count: 2}
    ],
    winner: "Andy",
    pile_count: 2
  }
}

// Round scoring (broadcast to all)
{
  event: "score",
  data: {
    summary: {
      "Andy": {declared: 3, actual: 2, score: -1, total: 14},
      "Bot 2": {declared: 2, actual: 2, score: 7, total: 15}
    },
    redeal_multiplier: 1,
    game_over: false,
    winners: []
  }
}
```

### **❌ Error Events**
```javascript
{
  event: "error",
  data: {
    message: "Room is full",
    type: "join_room_error" | "room_creation_error" | "game_error"
  }
}
```

---

## **📥 EVENTS FRONTEND SENDS TO BACKEND**

### **🏠 Lobby Events**
```javascript
{event: "client_ready", data: {}}
{event: "request_room_list", data: {player_name: "Andy"}}
{event: "get_rooms", data: {player_name: "Andy"}}        // Alternative name
{event: "create_room", data: {player_name: "Andy"}}
{event: "join_room", data: {room_id: "ABC123", player_name: "Andy"}}
```

### **🎮 Room Management Events**
```javascript
{event: "get_room_state", data: {}}
{event: "remove_player", data: {slot_id: 2}}             // slot_id: 1-4
{event: "add_bot", data: {slot_id: 3}}                   // slot_id: 1-4  
{event: "leave_room", data: {player_name: "Andy"}}
{event: "start_game", data: {}}
```

### **🎯 Game Action Events**
```javascript
// Declaration phase
{event: "declare", data: {player_name: "Andy", declaration: 3}}

// Turn phase  
{event: "play_pieces", data: {player_name: "Andy", indices: [0, 1, 2]}}

// Preparation phase
{event: "request_redeal", data: {player_name: "Andy"}}
{event: "accept_redeal", data: {player_name: "Andy"}}
{event: "decline_redeal", data: {player_name: "Andy"}}

// General
{event: "player_ready", data: {player_name: "Andy"}}
```

---

## **🏗️ CRITICAL INTEGRATION PATTERNS**

### **1. Connection Management**
```javascript
// NetworkService should handle both connections
class NetworkService {
  connectToLobby() {
    this.lobbyWs = new WebSocket('ws://localhost:5050/ws/lobby');
  }
  
  connectToRoom(roomId) {
    this.gameWs = new WebSocket(`ws://localhost:5050/ws/${roomId}`);
  }
}
```

### **2. State Synchronization**
```javascript
// GameService should listen for phase_change events
gameWs.onmessage = (event) => {
  const {event: eventType, data} = JSON.parse(event.data);
  
  if (eventType === 'phase_change') {
    // ⭐ CRITICAL: This contains ALL game state
    this.updateGameState({
      phase: data.phase,
      phaseData: data.phase_data,
      playerHands: data.players,
      allowedActions: data.allowed_actions
    });
  }
};
```

### **3. Action Sending**
```javascript
// GameService action methods
async makeDeclaration(value) {
  this.networkService.send('declare', {
    player_name: this.playerName,
    declaration: value
  });
}

async playPieces(indices) {
  this.networkService.send('play_pieces', {
    player_name: this.playerName, 
    indices: indices
  });
}
```

---

## **🤖 BOT SYSTEM INTEGRATION**

### **Automatic Bot Behavior**
- ✅ **Redeal Decisions**: Bots automatically accept/decline redeals (70% decline rate)
- ✅ **Declarations**: Bots automatically declare when their turn comes
- ✅ **Piece Playing**: Bots automatically play pieces during turns
- ✅ **No Frontend Needed**: Bots work completely independent of frontend

### **Bot Event Flow**
1. **State Machine** transitions to new phase
2. **Bot Manager** receives `phase_change` notification
3. **Bot Manager** automatically makes decisions for bot players
4. **Actions** sent through same state machine as human players
5. **Events** broadcast to all clients (including bot actions)

### **Frontend Bot Handling**
```javascript
// Frontend just needs to display bot actions
socket.on('declare', (data) => {
  if (data.is_bot) {
    // Display: "Bot 2 declared 3 piles"
    this.updateDeclarations(data.player, data.value);
  }
});
```

---

## **🔄 GAME FLOW SUMMARY**

### **Phase 1: Lobby → Room → Game Start**
1. **Connect to Lobby**: `ws://localhost:5050/ws/lobby`
2. **Get Room List**: Send `request_room_list` → Receive `room_list_update`
3. **Create/Join Room**: Send `create_room`/`join_room` → Receive confirmation
4. **Connect to Room**: `ws://localhost:5050/ws/{roomId}`  
5. **Start Game**: Send `start_game` → State machine initializes

### **Phase 2: Game Phases (Automatic State Machine)**
1. **PREPARATION**: Cards dealt → Weak hands → Redeal decisions
2. **DECLARATION**: Declaration order → Bot auto-declarations → Human input
3. **TURN**: Turn-based piece playing → Winner determination  
4. **SCORING**: Score calculation → Next round or game end

### **Phase 3: Real-time Updates**
- **All state changes** broadcast via `phase_change` events
- **Player actions** (declarations, plays) broadcast to all clients
- **Bot actions** handled automatically, events sent to frontend
- **Error handling** via `error` events

---

## **⚠️ CRITICAL BACKEND FEATURES**

### **✅ Production Ready Components**
- **State Machine**: Complete 4-phase game flow with 78+ passing tests
- **Bot Manager**: Fully automated bot decision making  
- **WebSocket Broadcasting**: Real-time state synchronization
- **Action Validation**: Backend validates all player actions
- **Error Handling**: Comprehensive error events and recovery

### **✅ Thread Safety**
- **Action Queue**: Prevents race conditions in state machine
- **Async Operations**: All operations use `async/await` patterns
- **Safe Room Operations**: `assign_slot_safe()` prevents conflicts

### **✅ Data Integrity**
- **Single Source of Truth**: State machine holds authoritative game state
- **Event Sequencing**: All events properly ordered and broadcast
- **State Validation**: Invalid actions rejected with error events

---

## **🎯 FRONTEND REQUIREMENTS**

### **Must Handle These Events**
1. **`phase_change`** - Most critical, contains complete game state
2. **`room_update`** - Room player changes 
3. **`declare`** - Bot and player declarations
4. **`play`** - Piece playing actions
5. **`error`** - All error scenarios

### **Must Send These Events**  
1. **`declare`** - Player declarations (with player_name)
2. **`play_pieces`** - Piece playing (with player_name and indices)
3. **Room management** - join_room, leave_room, add_bot, etc.

### **State Management Requirements**
- **Single Source**: One service to hold all game state from `phase_change` events
- **Real-time Updates**: UI updates immediately when events received
- **Action Validation**: Send actions and handle success/error responses
- **Connection Recovery**: Handle disconnections and missed events

---

**This backend system is production-ready and handles all game logic, bot AI, and state management. The frontend just needs to send actions and display the state updates it receives.**