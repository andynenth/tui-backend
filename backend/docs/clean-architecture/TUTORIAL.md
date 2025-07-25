# Clean Architecture Tutorial

## Introduction

This tutorial will guide you through implementing a new feature using the clean architecture. We'll add a "spectator mode" feature that allows users to watch games without playing.

## Prerequisites

- Understanding of Python async/await
- Basic knowledge of domain-driven design
- Familiarity with the game rules

## Tutorial: Adding Spectator Mode

### Step 1: Define Domain Concepts

First, let's think about what "spectating" means in our domain:
- A spectator can watch a game but not participate
- Spectators don't affect game state
- Room has a separate spectator limit

**Add to `domain/entities/room.py`:**
```python
class Room(Entity):
    def __init__(self, ...):
        # ... existing code ...
        self._spectators: List[Player] = []
        self._max_spectators: int = 10
    
    def add_spectator(self, spectator: Player) -> None:
        """Add a spectator to the room."""
        if len(self._spectators) >= self._max_spectators:
            raise DomainException("Spectator limit reached")
        
        if spectator.player_id in [p.player_id for p in self._players]:
            raise DomainException("Player cannot be spectator in same room")
        
        self._spectators.append(spectator)
        
        # Emit domain event
        self._events.append(
            SpectatorJoined(
                room_id=self.room_id.value,
                spectator_id=spectator.player_id.value,
                spectator_name=spectator.name,
                timestamp=datetime.utcnow()
            )
        )
```

### Step 2: Create Domain Event

**Create `domain/events/spectator_events.py`:**
```python
from dataclasses import dataclass
from datetime import datetime
from .base import DomainEvent


@dataclass(frozen=True)
class SpectatorJoined(DomainEvent):
    """Event emitted when a spectator joins a room."""
    room_id: str
    spectator_id: str
    spectator_name: str
    timestamp: datetime


@dataclass(frozen=True)
class SpectatorLeft(DomainEvent):
    """Event emitted when a spectator leaves."""
    room_id: str
    spectator_id: str
    timestamp: datetime
```

### Step 3: Create DTOs

**Add to `application/dto/room_management.py`:**
```python
@dataclass
class JoinAsSpectatorRequest:
    """Request to join a room as spectator."""
    spectator_id: str
    spectator_name: str
    room_code: Optional[str] = None
    room_id: Optional[str] = None


@dataclass
class JoinAsSpectatorResponse:
    """Response from joining as spectator."""
    success: bool
    room_id: Optional[str] = None
    error: Optional[str] = None
    game_in_progress: bool = False
    current_game_state: Optional[Dict[str, Any]] = None
```

### Step 4: Implement Use Case

**Create `application/use_cases/room_management/join_as_spectator.py`:**
```python
from application.base import UseCase
from application.interfaces import UnitOfWork, EventPublisher
from application.dto.room_management import (
    JoinAsSpectatorRequest,
    JoinAsSpectatorResponse
)
from domain.entities import Player
from domain.value_objects import PlayerId
from domain.exceptions import DomainException


class JoinAsSpectatorUseCase(UseCase[JoinAsSpectatorRequest, JoinAsSpectatorResponse]):
    """Use case for joining a room as a spectator."""
    
    def __init__(self, uow: UnitOfWork, publisher: EventPublisher):
        self._uow = uow
        self._publisher = publisher
    
    async def execute(self, request: JoinAsSpectatorRequest) -> JoinAsSpectatorResponse:
        """Execute the use case."""
        async with self._uow:
            # Find room
            if request.room_code:
                room = await self._uow.rooms.get_by_code(request.room_code)
            elif request.room_id:
                room = await self._uow.rooms.get_by_id(RoomId(request.room_id))
            else:
                return JoinAsSpectatorResponse(
                    success=False,
                    error="Must provide room_code or room_id"
                )
            
            if not room:
                return JoinAsSpectatorResponse(
                    success=False,
                    error="Room not found"
                )
            
            # Create spectator
            spectator = Player(
                player_id=PlayerId(request.spectator_id),
                name=request.spectator_name,
                is_spectator=True
            )
            
            try:
                # Add spectator to room
                room.add_spectator(spectator)
                
                # Save changes
                await self._uow.rooms.update(room)
                await self._uow.commit()
                
                # Publish events
                for event in room.collect_events():
                    await self._publisher.publish(event)
                
                # Get current game state if game in progress
                game_state = None
                if room.is_in_game:
                    game = await self._uow.games.get_active_by_room(room.room_id)
                    if game:
                        game_state = self._build_spectator_game_state(game)
                
                return JoinAsSpectatorResponse(
                    success=True,
                    room_id=room.room_id.value,
                    game_in_progress=room.is_in_game,
                    current_game_state=game_state
                )
                
            except DomainException as e:
                return JoinAsSpectatorResponse(
                    success=False,
                    error=str(e)
                )
    
    def _build_spectator_game_state(self, game) -> Dict[str, Any]:
        """Build game state visible to spectators."""
        # Spectators can see most things except player hands
        return {
            'phase': game.current_phase,
            'round': game.round_number,
            'turn': game.turn_number,
            'current_player': game.current_player_id,
            'declared_counts': game.get_declared_counts(),
            'scores': game.get_scores(),
            'last_play': game.get_last_play()
        }
```

### Step 5: Add to WebSocket Adapter

**Update `infrastructure/adapters/clean_architecture_adapter.py`:**
```python
class CleanArchitectureAdapter:
    def __init__(self, legacy_handlers):
        # ... existing code ...
        self._use_case_map = {
            # ... existing mappings ...
            'join_as_spectator': self._handle_join_as_spectator,
        }
    
    async def _handle_join_as_spectator(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle spectator join using clean architecture."""
        request = JoinAsSpectatorRequest(
            spectator_id=context['player_id'],
            spectator_name=data['player_name'],
            room_code=data.get('room_code'),
            room_id=data.get('room_id')
        )
        
        uow = get_unit_of_work()
        publisher = get_event_publisher()
        use_case = JoinAsSpectatorUseCase(uow, publisher)
        
        response = await use_case.execute(request)
        return response.to_dict()
```

### Step 6: Write Tests

**Create `tests/test_application/test_spectator_use_case.py`:**
```python
import pytest
from unittest.mock import Mock, AsyncMock
from application.use_cases.room_management.join_as_spectator import (
    JoinAsSpectatorUseCase
)
from application.dto.room_management import JoinAsSpectatorRequest
from domain.entities import Room
from domain.value_objects import RoomId


@pytest.mark.asyncio
async def test_join_as_spectator_success():
    """Test successful spectator join."""
    # Arrange
    uow = Mock()
    publisher = Mock()
    
    # Mock room
    room = Mock(spec=Room)
    room.room_id = RoomId("room1")
    room.is_in_game = False
    room.add_spectator = Mock()
    room.collect_events = Mock(return_value=[])
    
    uow.rooms.get_by_code = AsyncMock(return_value=room)
    uow.rooms.update = AsyncMock()
    uow.commit = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock()
    
    publisher.publish = AsyncMock()
    
    use_case = JoinAsSpectatorUseCase(uow, publisher)
    
    # Act
    request = JoinAsSpectatorRequest(
        spectator_id="spec1",
        spectator_name="Spectator 1",
        room_code="ROOM1"
    )
    response = await use_case.execute(request)
    
    # Assert
    assert response.success is True
    assert response.room_id == "room1"
    assert response.error is None
    
    room.add_spectator.assert_called_once()
    uow.rooms.update.assert_called_once_with(room)
    uow.commit.assert_called_once()


@pytest.mark.asyncio  
async def test_join_as_spectator_room_not_found():
    """Test spectator join with invalid room."""
    # Arrange
    uow = Mock()
    publisher = Mock()
    
    uow.rooms.get_by_code = AsyncMock(return_value=None)
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock()
    
    use_case = JoinAsSpectatorUseCase(uow, publisher)
    
    # Act
    request = JoinAsSpectatorRequest(
        spectator_id="spec1",
        spectator_name="Spectator 1",
        room_code="INVALID"
    )
    response = await use_case.execute(request)
    
    # Assert
    assert response.success is False
    assert response.error == "Room not found"
```

### Step 7: Add Feature Flag

**Update `infrastructure/feature_flags.py`:**
```python
class FeatureFlags:
    # ... existing flags ...
    ENABLE_SPECTATOR_MODE = "enable_spectator_mode"
    
    def _load_defaults(self):
        self._flags = {
            # ... existing defaults ...
            self.ENABLE_SPECTATOR_MODE: False
        }
```

### Step 8: Gradual Rollout

Enable the feature gradually:

```python
# 1. Test internally
{
  "enable_spectator_mode": {
    "enabled": true,
    "whitelist": ["test_user_1", "test_user_2"]
  }
}

# 2. Roll out to percentage
{
  "enable_spectator_mode": {
    "enabled": true,
    "percentage": 25
  }
}

# 3. Full rollout
{
  "enable_spectator_mode": true
}
```

## Summary

You've successfully implemented a new feature using clean architecture:

1. **Domain Layer**: Added spectator concept to Room entity
2. **Domain Events**: Created events for spectator actions  
3. **Application Layer**: Implemented use case with clear boundaries
4. **Infrastructure**: Integrated with WebSocket adapter
5. **Testing**: Wrote unit tests for the use case
6. **Rollout**: Used feature flags for safe deployment

## Best Practices Demonstrated

✅ **Separation of Concerns**: Each layer has specific responsibilities  
✅ **Domain-Driven Design**: Business logic in domain entities  
✅ **Test-Driven Development**: Tests guide implementation  
✅ **Safe Deployment**: Feature flags enable gradual rollout  
✅ **Event-Driven**: Domain events communicate changes  

## Next Steps

Try implementing these features yourself:
1. Leave as spectator functionality
2. Spectator chat (can only talk to other spectators)
3. Promote spectator to player (if slot available)
4. Spectator statistics tracking

## Questions?

- Review the [Architecture Guide](README.md)
- Check [examples/](../examples/) for more examples
- Ask in #clean-architecture channel