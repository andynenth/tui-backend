# Original User Workflow Design: Lobby → Room Creation → Room Joining

**Date**: 2025-07-29  
**Analysis**: Complete user journey workflow as originally designed  
**Flow**: Player enters lobby → Creates room → Other players join → Game starts  

## Complete User Journey Workflow

### 🎮 **Phase 1: Player Enters Lobby**

#### **Frontend Action**: Player clicks "Enter Lobby" 
```javascript
// StartPage.jsx → LobbyPage.jsx
const handleSubmit = (data) => {
    app.updatePlayerName(data.playerName);  // Store locally
    navigate('/lobby');                     // Navigate to lobby
};
```

#### **Step 1.1: WebSocket Connection to Lobby**
```javascript
// LobbyPage.jsx:33
useEffect(() => {
    const initializeLobby = async () => {
        await networkService.connectToRoom('lobby', {
            playerName: app.playerName
        });
    };
    initializeLobby();
}, []);
```

#### **Step 1.2: Backend Lobby Connection**
```python
# api/routes/ws.py:345
@router.websocket("/ws/{room_id}")  # room_id = "lobby"
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    # Generate WebSocket ID
    websocket._ws_id = str(uuid.uuid4())
    
    # Register with lobby (no room lookup needed for lobby)
    connection_id = await register("lobby", websocket)
```

#### **Step 1.3: Send Initial Room List**
```python
# api/routes/ws.py:408
elif event_name == "client_ready":
    # Send initial room list when client connects to lobby
    available_rooms = await room_manager.list_rooms()
    
    await registered_ws.send_json({
        "event": "room_list_update",
        "data": {
            "rooms": available_rooms,
            "timestamp": asyncio.get_event_loop().time(),
            "initial": True,
        },
    })
```

**Result**: Player sees lobby with list of available rooms to join.

---

### 🏠 **Phase 2: Player Creates Room**

#### **Step 2.1: Frontend Room Creation Request**
```javascript
// LobbyPage.jsx:151-154
const handleCreateRoom = () => {
    networkService.send('lobby', 'create_room', {
        player_name: app.playerName
    });
};
```

#### **Step 2.2: Backend Routes to Use Case**
```python
# application/websocket/message_router.py:98
if websocket_config.should_use_use_case(event):  # "create_room" = True
    response = await self._route_to_use_case(websocket, message, room_id, event)
```

#### **Step 2.3: Use Case Dispatcher**
```python
# application/websocket/use_case_dispatcher.py:410
async def _handle_create_room(self, context: DispatchContext, data: Dict[str, Any]):
    # Extract player info from WebSocket message
    player_name = data.get("player_name")
    
    # Create DTO request
    request = CreateRoomRequest(
        host_player_id=f"lobby_{player_name}",  # Temporary ID for lobby
        host_player_name=player_name,
        max_players=4,
        room_name=f"{player_name}'s Room"
    )
    
    # Execute use case
    response = await self.create_room_use_case.execute(request)
    return self._format_create_room_response(response)
```

#### **Step 2.4: Create Room Use Case Execution**
```python
# application/use_cases/room_management/create_room.py:73
async def execute(self, request: CreateRoomRequest) -> CreateRoomResponse:
    async with self._uow:
        # Generate unique room code (6 characters)
        room_code = await self._generate_unique_code()  # e.g., "ABC123"
        
        # Create domain Room entity
        room = Room(
            room_id=room_code,           # "ABC123"
            host_name=request.host_player_name,  # "Alice"
            max_slots=4
        )
        
        # Room.__post_init__ automatically:
        # - Adds host to slot 0: room.slots[0] = Player("Alice", is_bot=False)
        # - Fills bots in slots 1-3: room.slots[1-3] = Bot players
        
        # Save room to repository
        await self._uow.rooms.save(room)
        
        # Create response DTO
        room_info = self._create_room_info(room, host_player)
        return CreateRoomResponse(room_info=room_info, join_code=room_code)
```

#### **Step 2.5: Domain Room Initialization** 
```python
# domain/entities/room.py:139
def __post_init__(self):
    # Add host to first slot
    self.add_player(self.host_name, is_bot=False, slot=0)
    
    # Fill remaining slots with bots  
    for i in range(1, 4):
        bot_name = f"Bot {i+1}"
        self.add_player(bot_name, is_bot=True, slot=i)
    
    # Result: self.slots = [Player("Alice"), Player("Bot 2"), Player("Bot 3"), Player("Bot 4")]
```

#### **Step 2.6: DTO Creation with Correct IDs**
```python
# application/use_cases/room_management/create_room.py:195
def _create_room_info(self, room: Room, host_player: Player) -> RoomInfo:
    players = []
    for i, slot in enumerate(room.slots):  # i = 0,1,2,3
        if slot:
            player_info = PlayerInfo(
                player_id=f"{room.room_id}_p{i}",  # "ABC123_p0", "ABC123_p1", etc.
                player_name=slot.name,             # "Alice", "Bot 2", etc.
                is_bot=slot.is_bot,                # False, True, True, True
                is_host=(i == 0),                  # True, False, False, False
                seat_position=i,                   # 0, 1, 2, 3
                status=PlayerStatus.CONNECTED
            )
            players.append(player_info)
    
    return RoomInfo(
        room_id=room.room_id,     # "ABC123"
        host_id=f"{room.room_id}_p0",  # "ABC123_p0"
        players=players,          # [Host, Bot1, Bot2, Bot3] with correct IDs
        max_players=4,
        game_in_progress=False
    )
```

#### **Step 2.7: WebSocket Response to Client**
```python
# application/websocket/use_case_dispatcher.py:427
return {
    "event": "room_created",
    "data": {
        "success": True,
        "room_id": response.room_info.room_id,  # "ABC123"
        "room_code": response.join_code,        # "ABC123"
        "host_name": response.room_info.host_id, # Host info
        "room_info": self._format_room_info(response.room_info)  # Complete room data
    }
}
```

#### **Step 2.8: Frontend Receives Response & Navigates**
```javascript
// LobbyPage.jsx:62-93
const handleRoomCreated = (event) => {
    const roomData = eventData.data;
    if (roomData.room_id && roomData.room_id !== 'lobby') {
        navigate(`/room/${roomData.room_id}`);  // Navigate to /room/ABC123
    }
};
```

**Result**: Room "ABC123" created with Alice as host in slot 0, bots in slots 1-3. Alice navigates to room page.

---

### 🚪 **Phase 3: Other Players Join Room**

#### **Step 3.1: Player 2 Sees Room in Lobby**
```javascript
// LobbyPage.jsx receives room_list_update with new room "ABC123"
// Shows: "Alice's Room - 1/4 players"
```

#### **Step 3.2: Player 2 Clicks Join**
```javascript
// LobbyPage.jsx:169-172
const handleJoinRoom = (roomId) => {
    networkService.send('lobby', 'join_room', {
        room_id: roomId,          // "ABC123"
        player_name: app.playerName  // "Bob"
    });
};
```

#### **Step 3.3: Backend Join Room Use Case**
```python
# application/use_cases/room_management/join_room.py:59
async def execute(self, request: JoinRoomRequest) -> JoinRoomResponse:
    async with self._uow:
        # Find the room
        room = await self._uow.rooms.get_by_id(request.room_id)  # Get "ABC123"
        
        if not room:
            raise ResourceNotFoundException("Room not found")
        
        # Add player to room (domain logic)
        slot_assigned = room.add_player(request.player_name, is_bot=False)
        
        # Save updated room
        await self._uow.rooms.save(room)
        
        # Create response
        room_info = self._create_room_info(room)
        return JoinRoomResponse(
            room_info=room_info,
            seat_position=slot_assigned,  # Slot where player was added
            is_host=False
        )
```

#### **Step 3.4: Domain Room Add Player**
```python
# domain/entities/room.py:182
def add_player(self, name: str, is_bot: bool = False, slot: Optional[int] = None) -> int:
    # Find first available slot or replace bot
    for i, player in enumerate(self.slots):
        if player is None:
            # Empty slot found
            self.slots[i] = Player(name=name, is_bot=is_bot)
            return i
    
    # No empty slots, replace first bot
    if not is_bot:
        for i, player in enumerate(self.slots):
            if player and player.is_bot:
                old_bot = player.name
                self.slots[i] = Player(name=name, is_bot=is_bot)
                return i  # Return slot index where player was added
    
    raise ValueError("No available slots")
```

#### **Step 3.5: Room State After Join**
```python
# Room "ABC123" now has:
room.slots = [
    Player("Alice", is_bot=False),   # Slot 0 - Host
    Player("Bob", is_bot=False),     # Slot 1 - Joined player (replaces Bot 2)
    Player("Bot 3", is_bot=True),    # Slot 2 - Still a bot
    Player("Bot 4", is_bot=True)     # Slot 3 - Still a bot  
]
```

#### **Step 3.6: Update Room Info DTO**
```python
# When creating room info, Bob gets:
PlayerInfo(
    player_id="ABC123_p1",      # Slot 1
    player_name="Bob",
    is_bot=False,
    is_host=False,              # Only slot 0 is host
    seat_position=1,
    status=PlayerStatus.CONNECTED
)
```

#### **Step 3.7: Broadcast Room Update**
```python
# All clients in room "ABC123" receive:
{
    "event": "room_update", 
    "data": {
        "room_id": "ABC123",
        "players": [
            {"player_id": "ABC123_p0", "name": "Alice", "is_host": true, "seat_position": 0},
            {"player_id": "ABC123_p1", "name": "Bob", "is_host": false, "seat_position": 1},
            {"player_id": "ABC123_p2", "name": "Bot 3", "is_bot": true, "seat_position": 2},
            {"player_id": "ABC123_p3", "name": "Bot 4", "is_bot": true, "seat_position": 3}
        ]
    }
}
```

#### **Step 3.8: Player 2 Navigates to Room**
```javascript
// LobbyPage.jsx:96-109
const handleRoomJoined = (event) => {
    const joinData = eventData.data;
    if (joinData.room_id) {
        navigate(`/room/${joinData.room_id}`);  // Navigate to /room/ABC123
    }
};
```

**Result**: Bob joins room in slot 1, both Alice and Bob now see updated room with 2 human players + 2 bots.

---

### 🎮 **Phase 4: Room Page Display**

#### **Step 4.1: Players Connect to Room WebSocket**
```javascript
// RoomPage.jsx:39-41
useEffect(() => {
    const initializeRoom = async () => {
        await networkService.connectToRoom(roomId, {
            playerName: app.playerName
        });
        // Request current room state
        networkService.send(roomId, 'get_room_state', { room_id: roomId });
    };
    initializeRoom();
}, [roomId, app.playerName]);
```

#### **Step 4.2: Get Room State Use Case**
```python
# application/use_cases/room_management/get_room_state.py
async def execute(self, request: GetRoomStateRequest) -> GetRoomStateResponse:
    async with self._uow:
        room = await self._uow.rooms.get_by_id(request.room_id)
        
        if not room:
            raise ResourceNotFoundException("Room not found")
        
        # Convert to DTO with correct slot-based IDs
        room_info = self._create_room_info(room)
        
        return GetRoomStateResponse(
            success=True,
            room_info=room_info
        )
```

#### **Step 4.3: Frontend Displays Room Correctly**
```javascript
// RoomPage.jsx:202-208
{[1, 2, 3, 4].map((position) => {
    const player = roomData?.players?.[position - 1];  // Access slots 0,1,2,3
    const playerName = player ? (player.is_bot ? `Bot ${position}` : player.name) : 'Waiting...';
    
    return (
        <div key={position} className="rp-playerSeat">
            <div className="rp-playerName">{playerName}</div>
            {player?.is_host && <span className="rp-hostBadge">Host</span>}
        </div>
    );
})}
```

**Expected Display**:
- Position 1: "Alice" [Host Badge]
- Position 2: "Bob"  
- Position 3: "Bot 3"
- Position 4: "Bot 4"

---

### 🎯 **Phase 5: Game Start**

#### **Step 5.1: Host Starts Game**
```javascript
// RoomPage.jsx:118-123
const startGame = () => {
    networkService.send(roomId, 'start_game', {});
};
```

#### **Step 5.2: Start Game Use Case**
```python
# application/use_cases/game/start_game.py
async def execute(self, request: StartGameRequest) -> StartGameResponse:
    async with self._uow:
        room = await self._uow.rooms.get_by_id(request.room_id)
        
        # Create game with players from room slots
        game = Game(
            game_id=room.room_id,
            players=[slot for slot in room.slots if slot is not None]
        )
        
        # Update room status
        room.game = game
        room.status = RoomStatus.IN_GAME
        
        await self._uow.rooms.save(room)
        
        return StartGameResponse(success=True, game_started=True)
```

**Result**: Game starts with players in correct slot order, maintaining consistent IDs throughout.

---

## 🎯 **Key Design Principles (As Originally Intended)**

### ✅ **Consistent ID Generation**:
- **Lobby Phase**: No permanent IDs needed
- **Room Creation**: Host gets `{room_id}_p0`  
- **Room Joining**: Players get `{room_id}_p{slot_index}`
- **Game Start**: Same IDs maintained throughout

### ✅ **Slot-Based Architecture**:
- Room always has 4 slots (0-3)
- Host always in slot 0
- Players fill slots 1-3, replacing bots
- Frontend maps directly to slot positions

### ✅ **Clean Data Flow**:
- Domain entities manage business logic
- Use cases orchestrate operations  
- DTOs provide consistent data format
- WebSocket delivers real-time updates

### ✅ **State Consistency**:
- Single source of truth in domain Room entity
- All IDs generated from slot positions
- No external ID generation systems

## 🐛 **Where the Bug Breaks This Flow**

The **connection manager hash-based ID generation** breaks the clean flow by creating IDs that don't match the domain's slot-based structure, causing the frontend to receive players with IDs like `ABC123_p24` instead of `ABC123_p1`, making them invisible to the slot-based display logic.

**The original design was correct** - it just needs the connection manager bug fixed to work as intended.

---

**Summary**: The workflow was designed to maintain **slot-based consistency** from room creation through game start, with the domain layer managing all player positioning and the infrastructure layer simply transmitting the correct data.