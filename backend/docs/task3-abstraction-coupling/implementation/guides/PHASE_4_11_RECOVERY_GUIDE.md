# Phase 4.11: Core Feature Recovery Implementation Guide

## Purpose

This guide provides step-by-step instructions for implementing the reconnection system recovery in Phase 4.11. Follow these steps exactly to ensure proper integration without breaking existing functionality.

## Pre-Implementation Checklist

- [ ] Confirm all Phase 4.1-4.10 tests are passing
- [ ] Create a branch: `phase-4-11-reconnection-recovery`
- [ ] Review original reconnection implementation in:
  - `api/routes/ws.py` (disconnect/reconnect handling)
  - `api/websocket/connection_manager.py`
  - `api/websocket/message_queue.py`
  - `engine/bot_manager.py` (bot timing)

## Step 1: Domain Events (Phase 2 Retrofit)

### 1.1 Create Connection Events

```python
# domain/events/connection_events.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from domain.events.base import DomainEvent

@dataclass(frozen=True)
class PlayerDisconnectedEvent(DomainEvent):
    """Emitted when a player disconnects from the game"""
    room_id: str
    player_name: str
    disconnect_time: datetime
    was_bot_activated: bool
    
@dataclass(frozen=True)
class PlayerReconnectedEvent(DomainEvent):
    """Emitted when a player reconnects to the game"""
    room_id: str
    player_name: str
    reconnect_time: datetime
    messages_queued: int
    bot_was_deactivated: bool

@dataclass(frozen=True)
class BotActivatedEvent(DomainEvent):
    """Emitted when a bot takes over for a disconnected player"""
    room_id: str
    player_name: str
    activation_time: datetime
    
@dataclass(frozen=True)
class BotDeactivatedEvent(DomainEvent):
    """Emitted when a bot is deactivated on player return"""
    room_id: str
    player_name: str
    deactivation_time: datetime
```

### 1.2 Create Message Queue Events

```python
# domain/events/message_queue_events.py
from dataclasses import dataclass
from typing import Dict, Any
from domain.events.base import DomainEvent

@dataclass(frozen=True)
class MessageQueuedEvent(DomainEvent):
    """Emitted when a message is queued for a disconnected player"""
    room_id: str
    player_name: str
    event_type: str
    is_critical: bool
    
@dataclass(frozen=True)
class QueuedMessagesDeliveredEvent(DomainEvent):
    """Emitted when queued messages are delivered on reconnect"""
    room_id: str
    player_name: str
    message_count: int
    oldest_message_age_seconds: float
```

### 1.3 Update Event Exports

```python
# domain/events/__init__.py
# Add to existing exports:
from .connection_events import (
    PlayerDisconnectedEvent,
    PlayerReconnectedEvent,
    BotActivatedEvent,
    BotDeactivatedEvent
)
from .message_queue_events import (
    MessageQueuedEvent,
    QueuedMessagesDeliveredEvent
)
```

## Step 2: Domain Models (Phase 3 Retrofit)

### 2.1 Update Player Entity

```python
# domain/entities/player.py
# Add to existing Player class:

    # Connection tracking fields
    is_connected: bool = True
    disconnect_time: Optional[datetime] = None
    original_is_bot: bool = False  # Was this originally a bot?
    
    def disconnect(self) -> None:
        """Mark player as disconnected"""
        self.is_connected = False
        self.disconnect_time = datetime.utcnow()
        
    def activate_bot(self) -> None:
        """Convert player to bot on disconnect"""
        if not self.original_is_bot:
            self.is_bot = True
            
    def reconnect(self) -> None:
        """Mark player as reconnected"""
        self.is_connected = True
        self.disconnect_time = None
        
    def deactivate_bot(self) -> None:
        """Restore human control on reconnect"""
        if not self.original_is_bot:
            self.is_bot = False
```

### 2.2 Create Connection Entity

```python
# domain/entities/connection.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List

class ConnectionStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected" 
    RECONNECTING = "reconnecting"

@dataclass
class PlayerConnection:
    """Tracks player connection state"""
    player_id: str
    room_id: str
    websocket_id: Optional[str]
    status: ConnectionStatus
    last_activity: datetime
    disconnect_count: int = 0
    
    def disconnect(self) -> None:
        """Handle disconnection"""
        self.status = ConnectionStatus.DISCONNECTED
        self.websocket_id = None
        self.disconnect_count += 1
        
    def reconnect(self, websocket_id: str) -> None:
        """Handle reconnection"""
        self.status = ConnectionStatus.CONNECTED
        self.websocket_id = websocket_id
        self.last_activity = datetime.utcnow()
```

### 2.3 Create Message Queue Entities

```python
# domain/entities/message_queue.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

@dataclass
class QueuedMessage:
    """A message queued for a disconnected player"""
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    sequence: int
    is_critical: bool = False
    
@dataclass
class PlayerQueue:
    """Message queue for a specific player"""
    player_name: str
    room_id: str
    messages: List[QueuedMessage] = field(default_factory=list)
    max_size: int = 100
    last_sequence: int = 0
    
    def add_message(self, event_type: str, data: Dict[str, Any], is_critical: bool = False) -> None:
        """Add a message to the queue"""
        self.last_sequence += 1
        message = QueuedMessage(
            event_type=event_type,
            data=data,
            timestamp=datetime.utcnow(),
            sequence=self.last_sequence,
            is_critical=is_critical
        )
        self.messages.append(message)
        self._trim_if_needed()
        
    def _trim_if_needed(self) -> None:
        """Trim queue keeping critical messages"""
        if len(self.messages) <= self.max_size:
            return
            
        critical = [m for m in self.messages if m.is_critical]
        non_critical = [m for m in self.messages if not m.is_critical]
        
        remaining_space = self.max_size - len(critical)
        if remaining_space > 0:
            self.messages = critical + non_critical[-remaining_space:]
        else:
            self.messages = critical[-self.max_size:]
            
    def get_messages_since(self, sequence: int) -> List[QueuedMessage]:
        """Get all messages after a sequence number"""
        return [m for m in self.messages if m.sequence > sequence]
        
    def clear(self) -> None:
        """Clear all messages"""
        self.messages.clear()
```

## Step 3: Application Layer (Phase 4 Retrofit)

### 3.1 Create Disconnect Use Case

```python
# application/use_cases/connection/handle_player_disconnect.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from application.interfaces import UnitOfWork, EventPublisher
from domain.events.connection_events import PlayerDisconnectedEvent, BotActivatedEvent

@dataclass
class HandlePlayerDisconnectRequest:
    room_id: str
    player_name: str
    websocket_id: str
    disconnect_time: datetime

@dataclass
class HandlePlayerDisconnectResponse:
    success: bool
    bot_activated: bool
    message_queue_created: bool

class HandlePlayerDisconnectUseCase:
    def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher):
        self._uow = uow
        self._event_publisher = event_publisher
        
    async def execute(self, request: HandlePlayerDisconnectRequest) -> HandlePlayerDisconnectResponse:
        async with self._uow:
            # Get game and player
            game = await self._uow.games.get_by_room_id(request.room_id)
            if not game:
                return HandlePlayerDisconnectResponse(False, False, False)
                
            player = game.get_player(request.player_name)
            if not player:
                return HandlePlayerDisconnectResponse(False, False, False)
                
            # Handle disconnection
            player.disconnect()
            bot_activated = False
            
            # Activate bot if game is in progress and player was human
            if game.is_started and not player.original_is_bot:
                player.activate_bot()
                bot_activated = True
                
                # Emit bot activation event
                await self._event_publisher.publish(
                    BotActivatedEvent(
                        room_id=request.room_id,
                        player_name=request.player_name,
                        activation_time=datetime.utcnow()
                    )
                )
            
            # Create message queue
            await self._uow.message_queues.create_queue(request.room_id, request.player_name)
            
            # Save changes
            await self._uow.games.save(game)
            await self._uow.commit()
            
            # Emit disconnect event
            await self._event_publisher.publish(
                PlayerDisconnectedEvent(
                    room_id=request.room_id,
                    player_name=request.player_name,
                    disconnect_time=request.disconnect_time,
                    was_bot_activated=bot_activated
                )
            )
            
            return HandlePlayerDisconnectResponse(
                success=True,
                bot_activated=bot_activated,
                message_queue_created=True
            )
```

### 3.2 Create Reconnect Use Case

```python
# application/use_cases/connection/handle_player_reconnect.py
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime
from application.interfaces import UnitOfWork, EventPublisher
from domain.events.connection_events import PlayerReconnectedEvent, BotDeactivatedEvent

@dataclass
class HandlePlayerReconnectRequest:
    room_id: str
    player_name: str
    websocket_id: str

@dataclass
class HandlePlayerReconnectResponse:
    success: bool
    bot_deactivated: bool
    queued_messages: List[Dict[str, Any]]

class HandlePlayerReconnectUseCase:
    def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher):
        self._uow = uow
        self._event_publisher = event_publisher
        
    async def execute(self, request: HandlePlayerReconnectRequest) -> HandlePlayerReconnectResponse:
        async with self._uow:
            # Get game and player
            game = await self._uow.games.get_by_room_id(request.room_id)
            if not game:
                return HandlePlayerReconnectResponse(False, False, [])
                
            player = game.get_player(request.player_name)
            if not player:
                return HandlePlayerReconnectResponse(False, False, [])
                
            # Get queued messages
            queue = await self._uow.message_queues.get_queue(request.room_id, request.player_name)
            queued_messages = []
            if queue:
                queued_messages = [
                    {
                        "event_type": msg.event_type,
                        "data": msg.data,
                        "timestamp": msg.timestamp.isoformat(),
                        "is_critical": msg.is_critical
                    }
                    for msg in queue.messages
                ]
            
            # Handle reconnection
            player.reconnect()
            bot_deactivated = False
            
            # Deactivate bot if it was activated
            if player.is_bot and not player.original_is_bot:
                player.deactivate_bot()
                bot_deactivated = True
                
                # Cancel room cleanup if all bots
                game.check_human_players()
                
                # Emit bot deactivation event
                await self._event_publisher.publish(
                    BotDeactivatedEvent(
                        room_id=request.room_id,
                        player_name=request.player_name,
                        deactivation_time=datetime.utcnow()
                    )
                )
            
            # Clear message queue
            if queue:
                await self._uow.message_queues.clear_queue(request.room_id, request.player_name)
            
            # Save changes
            await self._uow.games.save(game)
            await self._uow.commit()
            
            # Emit reconnect event
            await self._event_publisher.publish(
                PlayerReconnectedEvent(
                    room_id=request.room_id,
                    player_name=request.player_name,
                    reconnect_time=datetime.utcnow(),
                    messages_queued=len(queued_messages),
                    bot_was_deactivated=bot_deactivated
                )
            )
            
            return HandlePlayerReconnectResponse(
                success=True,
                bot_deactivated=bot_deactivated,
                queued_messages=queued_messages
            )
```

### 3.3 Create Bot Timing Use Case

```python
# application/use_cases/bot/schedule_bot_action.py
import asyncio
import random
from dataclasses import dataclass
from typing import Optional
from application.interfaces import UnitOfWork

@dataclass
class ScheduleBotActionRequest:
    player_name: str
    action_type: str
    min_delay: float = 0.5
    max_delay: float = 1.5

@dataclass
class ScheduleBotActionResponse:
    scheduled: bool
    delay_seconds: float

class ScheduleBotActionUseCase:
    """Ensures bot actions have realistic delays"""
    
    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        
    async def execute(self, request: ScheduleBotActionRequest) -> ScheduleBotActionResponse:
        # Calculate delay (matching current implementation)
        delay = random.uniform(request.min_delay, request.max_delay)
        
        # Wait for the delay
        await asyncio.sleep(delay)
        
        return ScheduleBotActionResponse(
            scheduled=True,
            delay_seconds=delay
        )
```

## Step 4: Infrastructure Integration

### 4.1 Update Repository Interfaces

```python
# application/interfaces/repositories.py
# Add to existing interfaces:

class IMessageQueueRepository(ABC):
    @abstractmethod
    async def create_queue(self, room_id: str, player_name: str) -> None:
        pass
        
    @abstractmethod
    async def get_queue(self, room_id: str, player_name: str) -> Optional[PlayerQueue]:
        pass
        
    @abstractmethod
    async def queue_message(
        self, room_id: str, player_name: str, 
        event_type: str, data: Dict[str, Any], is_critical: bool = False
    ) -> None:
        pass
        
    @abstractmethod
    async def clear_queue(self, room_id: str, player_name: str) -> None:
        pass
        
class IConnectionRepository(ABC):
    @abstractmethod
    async def save_connection(self, connection: PlayerConnection) -> None:
        pass
        
    @abstractmethod
    async def get_connection(self, room_id: str, player_name: str) -> Optional[PlayerConnection]:
        pass
```

### 4.2 Update WebSocket Adapter

```python
# infrastructure/adapters/websocket_adapter.py
# Add to handle_disconnect method:

async def handle_disconnect(self, websocket_id: str, room_id: str) -> None:
    """Handle player disconnection"""
    # Get player info from connection manager
    player_name = self._get_player_name(websocket_id)
    if not player_name:
        return
        
    # Use disconnect use case
    request = HandlePlayerDisconnectRequest(
        room_id=room_id,
        player_name=player_name,
        websocket_id=websocket_id,
        disconnect_time=datetime.utcnow()
    )
    response = await self._disconnect_use_case.execute(request)
    
    if response.bot_activated:
        # Bot manager will handle bot actions via phase_change events
        pass

# Add to handle_reconnect method:
async def handle_reconnect(self, websocket_id: str, room_id: str, player_name: str) -> None:
    """Handle player reconnection"""
    # Use reconnect use case
    request = HandlePlayerReconnectRequest(
        room_id=room_id,
        player_name=player_name,
        websocket_id=websocket_id
    )
    response = await self._reconnect_use_case.execute(request)
    
    if response.queued_messages:
        # Send queued messages to player
        await self._send_queued_messages(websocket_id, response.queued_messages)
```

## Step 5: Testing

### 5.1 Domain Entity Tests

```python
# tests/domain/test_connection_entities.py
import pytest
from datetime import datetime
from domain.entities.player import Player
from domain.entities.connection import PlayerConnection, ConnectionStatus
from domain.entities.message_queue import PlayerQueue

def test_player_disconnect_flow():
    """Test player disconnect/reconnect flow"""
    player = Player("Alice", is_bot=False)
    
    # Disconnect
    player.disconnect()
    assert not player.is_connected
    assert player.disconnect_time is not None
    
    # Activate bot
    player.activate_bot()
    assert player.is_bot
    assert not player.original_is_bot
    
    # Reconnect
    player.reconnect()
    assert player.is_connected
    assert player.disconnect_time is None
    
    # Deactivate bot
    player.deactivate_bot()
    assert not player.is_bot

def test_message_queue_limits():
    """Test message queue size limits"""
    queue = PlayerQueue("Alice", "room1")
    
    # Add 150 messages (50 critical, 100 non-critical)
    for i in range(50):
        queue.add_message("critical_event", {"i": i}, is_critical=True)
    for i in range(100):
        queue.add_message("normal_event", {"i": i}, is_critical=False)
        
    # Should keep all critical + some non-critical
    assert len(queue.messages) == 100
    critical_count = sum(1 for m in queue.messages if m.is_critical)
    assert critical_count == 50
```

### 5.2 Integration Test

```python
# tests/integration/test_reconnection_integration.py
import pytest
from tests.helpers import create_test_game, create_test_room

@pytest.mark.asyncio
async def test_full_reconnection_flow(test_uow, event_publisher):
    """Test complete disconnect/reconnect cycle"""
    # Setup
    room = create_test_room("test1")
    game = create_test_game(room)
    
    # Player disconnects
    disconnect_use_case = HandlePlayerDisconnectUseCase(test_uow, event_publisher)
    disconnect_response = await disconnect_use_case.execute(
        HandlePlayerDisconnectRequest(
            room_id="test1",
            player_name="Alice",
            websocket_id="ws1",
            disconnect_time=datetime.utcnow()
        )
    )
    
    assert disconnect_response.success
    assert disconnect_response.bot_activated
    
    # Queue some messages
    await test_uow.message_queues.queue_message(
        "test1", "Alice", "phase_change", {"phase": "turn"}, is_critical=True
    )
    
    # Player reconnects
    reconnect_use_case = HandlePlayerReconnectUseCase(test_uow, event_publisher)
    reconnect_response = await reconnect_use_case.execute(
        HandlePlayerReconnectRequest(
            room_id="test1",
            player_name="Alice",
            websocket_id="ws2"
        )
    )
    
    assert reconnect_response.success
    assert reconnect_response.bot_deactivated
    assert len(reconnect_response.queued_messages) == 1
```

## Post-Implementation Checklist

- [ ] All new tests passing
- [ ] No regression in existing tests
- [ ] Bot timing matches original (0.5-1.5s)
- [ ] Message queuing works correctly
- [ ] Reconnection restores full state
- [ ] Documentation updated
- [ ] Create PR for review

## Rollback Plan

If issues arise:
1. The changes are all additive - remove new files
2. Remove new imports from existing files
3. No existing interfaces were modified
4. Feature flags can disable the new system

## Notes

- Keep all changes additive - don't modify existing interfaces
- Match exact behavior - no "improvements"
- Test thoroughly at each step
- Document any discoveries or deviations