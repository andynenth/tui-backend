# Room Management System Fix Plan

## Executive Summary

This document tracks the comprehensive fix for the room management system's architectural mismatches. The system currently has 216 attribute mismatches across 19 files due to a disconnect between the domain layer (what entities actually have) and the application layer (what use cases expect).

**Goal**: Create a robust room management system where:
- No more AttributeError exceptions
- Lobby displays real rooms (not mock data)
- All layers are properly aligned
- System is maintainable and testable

## Root Cause Analysis

### 1. DTO Missing Fields Issue
**Problem**: Request DTOs don't include base fields like `request_id`
```python
# Current (broken)
class GetRoomStateRequest(Request):
    room_id: str
    # Missing request_id field!

# Use case expects
response = GetRoomStateResponse(
    request_id=request.request_id,  # AttributeError!
)
```

**Latest Error from log.txt**:
```
api.adapters.room_adapters - ERROR - [ROOM_STATE_DEBUG] Error getting room state: 'GetRoomStateRequest' object has no attribute 'request_id'
```

### 2. Domain/Application Layer Mismatch
**Problem**: 216 attribute mismatches between what exists and what's expected

| Domain Entity Has | Use Cases Expect | Count |
|------------------|------------------|-------|
| room.room_id | room.id | 45 |
| room.host_name | room.host_id | 23 |
| room.game | room.current_game | 18 |
| player.name | player.id | 38 |
| (no settings) | room.settings.* | 31 |
| (no created_at) | room.created_at | 15 |
| **Total** | | **216** |

### 3. Lobby Returns Mock Data
**Problem**: Lobby adapter returns hardcoded data instead of real rooms
```python
# Current lobby_adapters.py
mock_rooms = [
    {"room_id": "room_abc123", "host_name": "Alice", ...}
]
```

### 4. Repository Interface Gaps
**Problem**: Use cases call methods that don't exist
```python
# Use case calls
all_rooms = await self._uow.rooms.list_active(limit=1000)  # Method doesn't exist!
current_room = await self._uow.rooms.find_by_player(player_id)  # Method doesn't exist!
```

## Implementation Plan

### Phase 1: DTO Base Field Fixes ⏳

**Objective**: Fix immediate AttributeError for request_id

#### Tasks:
- [ ] Update all Request DTOs to include base fields
- [ ] Add request_id field with default factory
- [ ] Update Response DTOs for consistency
- [ ] Test DTO instantiation

#### Code Example:
```python
# Fixed GetRoomStateRequest
@dataclass
class GetRoomStateRequest(Request):
    room_id: str
    requesting_player_id: Optional[str] = None
    include_game_state: bool = True
    # Add base fields
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
```

### Phase 2: Property Mapping Layer ⏳

**Objective**: Systematically handle all 216 attribute mismatches

#### Tasks:
- [ ] Create PropertyMapper class
- [ ] Add room entity mapping methods
- [ ] Add player entity mapping methods
- [ ] Add ID generation strategies
- [ ] Create defensive property access helpers

#### Code Example:
```python
class PropertyMapper:
    """Maps between domain entities and use case expectations."""
    
    @staticmethod
    def map_room_for_use_case(room: Room) -> dict:
        """Convert domain Room to what use cases expect."""
        return {
            'id': room.room_id,
            'code': room.room_id,
            'name': f"{room.host_name}'s Room",
            'host_id': f"{room.room_id}_p0",  # Generated
            'current_game': room.game,
            'created_at': datetime.utcnow(),  # Generated
            'player_count': len([s for s in room.slots if s]),
            'settings': {
                'max_players': room.max_slots,
                'is_private': False  # Default
            }
        }
    
    @staticmethod
    def get_safe(obj, attr, default=None):
        """Safely get attribute with fallback."""
        return getattr(obj, attr, default)
```

### Phase 3: Repository Enhancements ⏳

**Objective**: Add missing repository methods

#### Tasks:
- [ ] Add list_active() method to RoomRepository interface
- [ ] Add find_by_player() method to RoomRepository interface  
- [ ] Implement methods in InMemoryRoomRepository
- [ ] Add get_by_id() alias for consistency
- [ ] Update unit of work interface

#### Code Example:
```python
# Updated repository interface
class RoomRepository(ABC):
    # Existing methods...
    
    @abstractmethod
    async def list_active(self, limit: int = 100) -> List[Room]:
        """Get list of active rooms."""
        pass
    
    @abstractmethod
    async def find_by_player(self, player_id: str) -> Optional[Room]:
        """Find room containing a player by ID."""
        pass
```

### Phase 4: Lobby Integration ⏳

**Objective**: Connect lobby to real room data

#### Tasks:
- [ ] Remove mock data from lobby_adapters
- [ ] Import and use GetRoomListUseCase
- [ ] Map use case response to WebSocket format
- [ ] Handle filters and pagination
- [ ] Test lobby room listing

#### Code Example:
```python
async def _handle_get_rooms(websocket, message, room_state, broadcast_func):
    """Get real rooms from clean architecture."""
    # Get dependencies
    uow = get_unit_of_work()
    use_case = GetRoomListUseCase(uow)
    
    # Create request
    request = GetRoomListRequest(
        player_id=message.get("data", {}).get("player_id"),
        include_full=True,
        include_in_game=True
    )
    
    # Execute use case
    response = await use_case.execute(request)
    
    # Map to WebSocket format
    return {
        "event": "room_list",
        "data": {
            "rooms": [_map_room_summary(r) for r in response.rooms],
            "total_count": response.total_items
        }
    }
```

### Phase 5: Systematic Use Case Updates ⏳

**Objective**: Fix all 19 use case files

#### Files to Update:

**Room Management (6 files):**
- [ ] room_management/create_room.py
- [ ] room_management/get_room_state.py
- [ ] room_management/join_room.py
- [ ] room_management/leave_room.py
- [ ] room_management/add_bot.py
- [ ] room_management/remove_player.py

**Game (9 files):**
- [ ] game/start_game.py
- [ ] game/declare.py
- [ ] game/play.py
- [ ] game/accept_redeal.py
- [ ] game/decline_redeal.py
- [ ] game/handle_redeal_decision.py
- [ ] game/request_redeal.py
- [ ] game/leave_game.py
- [ ] game/mark_player_ready.py

**Lobby (2 files):**
- [ ] lobby/get_room_list.py
- [ ] lobby/get_room_details.py

**Connection (3 files):**
- [ ] connection/sync_client_state.py
- [ ] connection/mark_client_ready.py
- [ ] connection/handle_ping.py

#### Update Pattern:
```python
# Before
is_host = slot.id == room.host_id

# After  
is_host = slot.name == room.host_name
```

### Phase 6: Integration Testing ⏳

**Objective**: Verify entire system works

#### Test Scenarios:
- [ ] Create room → appears in lobby
- [ ] Join room → updates player count
- [ ] Get room state → returns all players
- [ ] Start game → room status updates
- [ ] Leave room → player removed
- [ ] Bot management → add/remove bots

## Progress Tracking

### Overall Progress: 0/6 Phases Complete

| Phase | Status | Started | Completed | Notes |
|-------|--------|---------|-----------|-------|
| 1. DTO Fixes | ⏳ Pending | - | - | |
| 2. Property Mapper | ⏳ Pending | - | - | |
| 3. Repository | ⏳ Pending | - | - | |
| 4. Lobby | ⏳ Pending | - | - | |
| 5. Use Cases | ⏳ Pending | - | - | |
| 6. Testing | ⏳ Pending | - | - | |

### Detailed Checklist

#### DTO Fixes (0/15)
- [ ] GetRoomStateRequest
- [ ] CreateRoomRequest
- [ ] JoinRoomRequest
- [ ] LeaveRoomRequest
- [ ] AddBotRequest
- [ ] RemoveBotRequest
- [ ] UpdateRoomSettingsRequest
- [ ] StartGameRequest
- [ ] DeclareRequest
- [ ] PlayRequest
- [ ] HandleRedealRequest
- [ ] GetGameStateRequest
- [ ] GetRoomListRequest
- [ ] GetPlayerStatsRequest
- [ ] UpdatePlayerProfileRequest

#### Property Mappings (0/5)
- [ ] Room → UseCase mapping
- [ ] Player → UseCase mapping
- [ ] Game → UseCase mapping
- [ ] ID generation helpers
- [ ] Safe property access helpers

#### Repository Methods (0/4)
- [ ] list_active()
- [ ] find_by_player()
- [ ] get_by_id() alias
- [ ] Update interfaces

#### Use Case Updates (0/19)
**Room Management:**
- [ ] create_room.py
- [ ] get_room_state.py
- [ ] join_room.py
- [ ] leave_room.py
- [ ] add_bot.py
- [ ] remove_player.py

**Game:**
- [ ] start_game.py
- [ ] declare.py
- [ ] play.py
- [ ] accept_redeal.py
- [ ] decline_redeal.py
- [ ] handle_redeal_decision.py
- [ ] request_redeal.py
- [ ] leave_game.py
- [ ] mark_player_ready.py

**Lobby:**
- [ ] get_room_list.py
- [ ] get_room_details.py

**Connection:**
- [ ] sync_client_state.py
- [ ] mark_client_ready.py
- [ ] handle_ping.py

## Testing Strategy

### Unit Tests
- Test PropertyMapper conversions
- Test repository new methods
- Test DTO field presence

### Integration Tests
- Test complete flows (create → join → play)
- Test lobby updates
- Test error scenarios

### Manual Testing Checklist
- [ ] Create room via UI
- [ ] See room in lobby
- [ ] Join room
- [ ] Start game
- [ ] Complete a round
- [ ] Leave room

## Success Criteria

1. **No AttributeErrors**: Can create room, join, and play without crashes
2. **Real Lobby Data**: Lobby shows actual rooms, not mock data
3. **Player Display**: Room shows player names, not "Waiting..."
4. **Consistent IDs**: Same ID format across all layers
5. **All Tests Pass**: Unit and integration tests green

## Notes

- This fix addresses architectural debt from phased implementation
- Future consideration: Add IDs to domain entities to avoid generation
- Consider using AutoMapper pattern for complex mappings
- Document mapping rules for future developers

---
*Last Updated*: 2025-07-27 (Corrected file list based on actual codebase verification)
*Status*: Planning Complete, Implementation Pending