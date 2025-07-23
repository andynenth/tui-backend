# Task 3: Abstraction & Coupling - Detailed Execution Plan

> **STATUS: Phase 4 Complete ✅** - Clean API Layer has been successfully implemented. This document tracks both the original plan and actual implementation progress.

## Overview of Current Coupling Issues

### 1. **Layer Violations**
- Game engine imports WebSocket broadcast functions directly
- State machine manipulates game state attributes directly
- Domain objects know about infrastructure (networking, persistence)

### 2. **God Objects and Mixed Responsibilities**
- `socket_manager.py`: 1000+ lines handling connections, broadcasting, queuing, stats
- `Room` class: Manages players, game lifecycle, state machine, and bots
- `GameStateMachine`: Knows about game internals, broadcasting, bot management

### 3. **Tight Coupling Examples**
```python
# backend/engine/state_machine/base_state.py:188-190
from backend.socket_manager import broadcast
await broadcast(self.state_machine.room_id, "phase_change", data)

# backend/engine/state_machine/states/turn_state.py:162
game.turn_number += 1  # Direct mutation of game state

# backend/engine/bot_manager.py:469
result = self.game.declare(bot.name, value)  # Direct game method calls
```

### 4. **Missing Abstractions**
- No interfaces between layers
- No service layer between WebSocket and domain
- No event bus for decoupling
- No repository pattern for data access

## Proposed Architecture

### Layer Structure
```
┌─────────────────────────────────────────────┐
│          Presentation Layer                 │
│  (WebSocket Handlers, REST Endpoints)       │
├─────────────────────────────────────────────┤
│          Application Layer                  │
│  (Use Cases, Application Services)          │
├─────────────────────────────────────────────┤
│          Domain Layer                       │
│  (Game Logic, Business Rules, Entities)    │
├─────────────────────────────────────────────┤
│          Infrastructure Layer               │
│  (WebSocket, Database, External Services)   │
└─────────────────────────────────────────────┘
```

### Proposed Module Structure
```
backend/
├── domain/                    # Pure business logic
│   ├── entities/             # Domain objects
│   │   ├── game.py
│   │   ├── player.py
│   │   ├── piece.py
│   │   └── room.py
│   ├── value_objects/        # Immutable domain values
│   │   ├── play_result.py
│   │   └── game_state.py
│   ├── services/             # Domain services
│   │   ├── game_rules.py
│   │   ├── scoring.py
│   │   └── turn_resolution.py
│   ├── events/               # Domain events
│   │   ├── game_events.py
│   │   └── player_events.py
│   └── interfaces/           # Domain interfaces
│       ├── game_repository.py
│       ├── event_publisher.py
│       └── bot_strategy.py
│
├── application/              # Application services
│   ├── use_cases/           # Business use cases
│   │   ├── create_room.py
│   │   ├── join_room.py
│   │   ├── play_turn.py
│   │   └── declare_piles.py
│   ├── services/            # Application services
│   │   ├── game_service.py
│   │   ├── room_service.py
│   │   └── bot_service.py
│   └── interfaces/          # Application interfaces
│       └── notification_service.py
│
├── infrastructure/          # External concerns
│   ├── websocket/          # WebSocket implementation
│   │   ├── connection_manager.py
│   │   ├── broadcast_service.py
│   │   └── websocket_adapter.py
│   ├── persistence/        # Data persistence
│   │   ├── game_repository_impl.py
│   │   └── event_store_impl.py
│   ├── state_machine/      # State machine implementation
│   │   ├── game_state_machine.py
│   │   └── state_adapter.py
│   └── bot/               # Bot implementation
│       ├── ai_strategy.py
│       └── bot_manager_impl.py
│
└── api/                    # API layer
    ├── websocket/         # WebSocket handlers
    │   └── game_handler.py
    └── rest/              # REST endpoints
        └── game_controller.py
```

## Specific Decoupling Areas

### 1. **Game Logic vs State I/O**
**Current Problem**: State machine directly modifies game attributes
```python
# BAD: Direct mutation
game.turn_number += 1
game.pile_counts[player_name] = count
```

**Solution**: Command pattern with immutable updates
```python
# GOOD: Through interface
game_service.execute_command(IncrementTurnCommand())
new_state = game_service.update_pile_count(player_name, count)
```

### 2. **Domain vs Infrastructure Events**
**Current Problem**: Domain emits infrastructure events
```python
# BAD: Domain knows about WebSocket
await broadcast(room_id, "phase_change", data)
```

**Solution**: Domain events with infrastructure adapters
```python
# GOOD: Domain emits pure events
self.event_publisher.publish(PhaseChangedEvent(old_phase, new_phase))
# Infrastructure subscribes and broadcasts
```

### 3. **Bot Management Abstraction**
**Current Problem**: Bot manager directly calls game methods
```python
# BAD: Tight coupling
result = self.game.declare(bot.name, value)
```

**Solution**: Bot strategy interface
```python
# GOOD: Through interface
decision = await self.bot_strategy.make_declaration(game_state)
command = DeclareCommand(bot.name, decision.value)
await self.game_service.execute(command)
```

## Interfaces and Abstractions to Introduce

### 1. **Domain Interfaces**
```python
# domain/interfaces/game_repository.py
from abc import ABC, abstractmethod
from typing import Optional
from domain.entities.game import Game

class GameRepository(ABC):
    @abstractmethod
    async def save(self, game: Game) -> None:
        pass
    
    @abstractmethod
    async def get(self, game_id: str) -> Optional[Game]:
        pass

# domain/interfaces/event_publisher.py
from abc import ABC, abstractmethod
from domain.events.base import DomainEvent

class EventPublisher(ABC):
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        pass
```

### 2. **Application Interfaces**
```python
# application/interfaces/notification_service.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class NotificationService(ABC):
    @abstractmethod
    async def notify_room(self, room_id: str, event_type: str, data: Dict[str, Any]) -> None:
        pass
    
    @abstractmethod
    async def notify_player(self, player_id: str, event_type: str, data: Dict[str, Any]) -> None:
        pass
```

### 3. **Port Adapters**
```python
# infrastructure/websocket/websocket_adapter.py
from application.interfaces.notification_service import NotificationService
from infrastructure.websocket.broadcast_service import BroadcastService

class WebSocketNotificationAdapter(NotificationService):
    def __init__(self, broadcast_service: BroadcastService):
        self._broadcast_service = broadcast_service
    
    async def notify_room(self, room_id: str, event_type: str, data: Dict[str, Any]) -> None:
        await self._broadcast_service.broadcast_to_room(room_id, event_type, data)
```

## Example Refactored Boundaries

### Before: Tight Coupling
```python
# backend/engine/state_machine/states/turn_state.py
async def _process_action(self, action: GameAction):
    game = self.state_machine.game
    game.turn_number += 1  # Direct mutation
    
    # Direct broadcast
    from backend.socket_manager import broadcast
    await broadcast(self.state_machine.room_id, "turn_played", {
        "player": action.player_name,
        "pieces": pieces
    })
```

### After: Clean Boundaries
```python
# domain/use_cases/play_turn.py
class PlayTurnUseCase:
    def __init__(self, game_service: GameService, event_publisher: EventPublisher):
        self._game_service = game_service
        self._event_publisher = event_publisher
    
    async def execute(self, room_id: str, player_name: str, pieces: List[int]) -> PlayResult:
        # Get game through service
        game = await self._game_service.get_game(room_id)
        
        # Execute turn through domain logic
        result = game.play_turn(player_name, pieces)
        
        # Save state
        await self._game_service.save_game(game)
        
        # Publish domain event
        await self._event_publisher.publish(
            TurnPlayedEvent(room_id, player_name, pieces, result)
        )
        
        return result
```

## Step-by-Step Execution Checklist

### Phase 1: Create Domain Layer (Week 1) ✅ COMPLETE
- [x] Create `backend/domain/` directory structure
- [x] Move `game.py` to `domain/entities/game.py`
  - [x] Remove all imports from infrastructure/api layers
  - [x] Make all attributes private with proper accessors
  - [x] Remove direct broadcast calls (no broadcast dependencies found)
- [x] Move `player.py` to `domain/entities/player.py`
  - [x] Ensure no infrastructure dependencies
  - [x] Removed UI concerns (avatar color) and connection tracking
- [x] Move `piece.py` to `domain/entities/piece.py`
  - [x] Made immutable with `@dataclass(frozen=True)`
  - [x] Separated deck building into `PieceDeck` factory
- [x] Create `domain/value_objects/` for immutable values
  - [x] Create `PlayResult` value object
  - [x] Create `GameState` value object with `GamePhase` enum
  - [x] Create `TurnPlay` value object (instead of Declaration)
- [x] Move pure business logic to `domain/services/`
  - [x] Move `rules.py` → `domain/services/game_rules.py`
  - [x] Move `scoring.py` → `domain/services/scoring.py` with `RoundScore` VO
  - [x] Move `turn_resolution.py` → `domain/services/turn_resolution.py`
- [x] Create domain events in `domain/events/`
  - [x] Create base `DomainEvent` class with metadata and `AggregateEvent`
  - [x] Create `GameStartedEvent`, `TurnPlayedEvent`, `PhaseChangedEvent`
  - [x] Create `PlayerJoinedEvent`, `PlayerLeftEvent`
  - [x] Added many more: `RoundStartedEvent`, `GameEndedEvent`, etc.
- [x] Define domain interfaces in `domain/interfaces/`
  - [x] Create `GameRepository` interface with full CRUD operations
  - [x] Create `EventPublisher` interface with `EventSubscriber` and `EventStore`
  - [x] Create `BotStrategy` interface with `BotDecision` value object

### Phase 2: Create Application Layer (Week 2) ✅ COMPLETE
- [x] Create `backend/application/` directory structure
- [x] Create use cases in `application/use_cases/`
  - [x] `CreateRoomUseCase` - orchestrates room creation
  - [x] `JoinRoomUseCase` - handles player joining
  - [x] `StartGameUseCase` - initiates game
  - [x] `PlayTurnUseCase` - processes turn
  - [x] `DeclarePilesUseCase` - handles declarations
- [x] Create application services in `application/services/`
  - [x] `GameService` - orchestrates game operations
  - [x] `RoomService` - manages rooms
  - [x] `BotService` - coordinates bot actions
- [x] Define application interfaces
  - [x] `NotificationService` - abstraction for notifications
  - [x] `AuthenticationService` - player authentication
- [x] Implement command pattern
  - [x] Create base `Command` class with metadata and timestamps
  - [x] Create specific commands for each game action (12+ commands)
  - [x] Create `CommandHandler` base and `CommandBus` for routing

### Phase 3: Refactor Infrastructure Layer (Week 3) ✅ COMPLETE
- [x] Create `backend/infrastructure/` directory structure
- [x] Move WebSocket code to `infrastructure/websocket/`
  - [x] Extract broadcasting to `BroadcastService` with message sequencing
  - [x] Create `WebSocketNotificationAdapter` implementing NotificationService
  - [x] Separate connection management with health monitoring
- [x] Create persistence implementations
  - [x] Implement `GameRepository` interface (InMemory + FileBased)
  - [x] Implement `EventStore` with proper abstraction
  - [x] Create `RoomRepository` with join code management
- [x] Refactor state machine
  - [x] Move to `infrastructure/state_machine/`
  - [x] Create `StateAdapter` to bridge with domain
  - [x] Override broadcast to use NotificationService
- [x] Refactor bot management
  - [x] Implement `BotStrategy` interface with Easy/Medium strategies
  - [x] Create `SimpleBotStrategyFactory` for strategy creation
  - [x] Remove direct game dependencies

### Phase 4: Create Clean API Layer (Week 4) ✅ COMPLETE
- [x] Refactor WebSocket handlers
  - [x] Use only application services and commands
  - [x] Remove direct domain access
  - [x] Implement proper error handling with CommandResult
- [x] Create handler for each use case
  - [x] `RoomHandler` - room operations (settings, kick, transfer, close)
  - [x] `GameHandler` - game operations (create, join, play, declare)
  - [x] `UnifiedHandler` - routes to appropriate handlers
- [x] Implement dependency injection
  - [x] Create DependencyContainer with all services
  - [x] Wire up all dependencies in single location
  - [x] Remove global singletons

### Phase 5: Event System Implementation (Week 5) ✅ COMPLETE
- [x] Create event bus infrastructure
  - [x] Implement `EventBus` class with priority and filtering
  - [x] Create event handlers (Notification, State, Bot, Audit)
  - [x] Set up subscriptions in DependencyContainer
- [x] Replace direct broadcasts with events
  - [x] Domain publishes domain events via EventPublisher
  - [x] Infrastructure subscribes and broadcasts via handlers
- [x] Implement event sourcing integration
  - [x] Store domain events with EventStore
  - [x] Enable event replay with EventReplayer
  - [x] Create event projections for read models
- [x] Create event documentation
  - [x] Migration guide (EVENT_SYSTEM_MIGRATION.md)
  - [x] Complete documentation (EVENT_SYSTEM_DOCUMENTATION.md)

### Phase 6: Testing and Migration (Week 6)
- [ ] Create unit tests for domain layer
  - [ ] No infrastructure dependencies
  - [ ] Pure business logic tests
- [ ] Create integration tests for application layer
  - [ ] Mock infrastructure interfaces
  - [ ] Test use case flows
- [ ] Create adapter tests
  - [ ] Test infrastructure implementations
  - [ ] Verify interface contracts
- [ ] Migration strategy
  - [ ] Create compatibility layer
  - [ ] Gradual migration path
  - [ ] Update documentation

## Implementation Progress

### Phase 1 Implementation Details (COMPLETE)

**Key Decisions Made:**
1. **Immutable Value Objects**: Used `@dataclass(frozen=True)` for all value objects
2. **Private State**: Made all entity state private with property accessors
3. **Factory Pattern**: Separated `PieceDeck` from `Piece` entity
4. **Rich Domain Events**: Added comprehensive event types beyond initial plan
5. **Service Pattern**: Domain services are stateless with class methods
6. **No Infrastructure**: Confirmed game.py had no infrastructure dependencies

**Phase 1 Files Created:**
```
backend/domain/
├── __init__.py (domain facade)
├── entities/
│   ├── game.py (600+ lines, fully refactored)
│   ├── player.py (150+ lines, cleaned)
│   └── piece.py (120+ lines, immutable)
├── value_objects/
│   ├── game_state.py
│   ├── play_result.py
│   └── turn_play.py
├── services/
│   ├── game_rules.py (300+ lines)
│   ├── scoring.py (150+ lines)
│   └── turn_resolution.py (150+ lines)
├── events/
│   ├── base.py (event infrastructure)
│   ├── game_events.py (15+ event types)
│   └── player_events.py (7+ event types)
└── interfaces/
    ├── game_repository.py
    ├── event_publisher.py
    └── bot_strategy.py
```

### Phase 2 Implementation Details (COMPLETE)

**Key Decisions Made:**
1. **Command Pattern**: Full command/handler architecture with bus
2. **Use Case Classes**: Dedicated class per major operation
3. **Result Objects**: Type-safe results from all use cases
4. **Service Layer**: Rich application services for orchestration
5. **Interface Design**: Small, focused interfaces (ISP)
6. **Async Throughout**: All operations async for scalability

**Phase 2 Files Created:**
```
backend/application/
├── __init__.py (application facade)
├── commands/
│   ├── base.py (250+ lines, command infrastructure)
│   ├── room_commands.py (7 command types)
│   └── game_commands.py (12 command types)
├── use_cases/
│   ├── create_room.py (150+ lines)
│   ├── join_room.py (150+ lines)
│   ├── start_game.py (150+ lines)
│   ├── play_turn.py (200+ lines)
│   └── declare_piles.py (150+ lines)
├── services/
│   ├── game_service.py (300+ lines)
│   ├── room_service.py (250+ lines)
│   └── bot_service.py (350+ lines)
└── interfaces/
    ├── notification_service.py (100+ lines)
    └── authentication_service.py (100+ lines)
```

### Phase 3 Implementation Details (COMPLETE)

**Key Decisions Made:**
1. **Adapter Pattern**: All infrastructure adapts to domain/app interfaces
2. **Multiple Implementations**: In-memory and file-based options
3. **State Machine Bridge**: Adapter wraps existing state machine
4. **Bot Strategies**: Pluggable AI with factory pattern
5. **Connection Management**: Centralized WebSocket handling
6. **Event Infrastructure**: Full pub/sub with history

**Phase 3 Files Created:**
```
backend/infrastructure/
├── __init__.py (infrastructure facade)
├── websocket/
│   ├── connection_manager.py (200+ lines)
│   ├── broadcast_service.py (250+ lines)
│   └── notification_adapter.py (150+ lines)
├── persistence/
│   ├── game_repository_impl.py (300+ lines)
│   ├── room_repository_impl.py (250+ lines)
│   └── event_publisher_impl.py (200+ lines)
├── state_machine/
│   └── state_adapter.py (250+ lines)
├── bot/
│   └── ai_strategy.py (400+ lines)
└── auth/
    └── simple_auth_adapter.py (200+ lines)
```

**Phase 3 Challenges Resolved:**
- Bridged existing state machine without full rewrite
- Overrode broadcast function to use NotificationService
- Created multiple repository implementations for flexibility
- Implemented bot strategies following domain interface
- Maintained backward compatibility during migration

### Phase 4 Implementation Details (COMPLETE)

**Key Decisions Made:**
1. **Unified Handler**: Single entry point routing to specific handlers
2. **Command-Only API**: All operations go through command bus
3. **DI Container**: Centralized dependency configuration
4. **Additional Use Cases**: Created missing room/bot management cases
5. **Clean Separation**: API knows only about application layer
6. **Error Consistency**: All responses follow same format

**Phase 4 Files Created:**
```
backend/api/
├── websocket/
│   ├── game_handler.py (250+ lines)
│   ├── room_handler.py (150+ lines)
│   └── endpoints.py (150+ lines)
├── dependencies.py (300+ lines)
├── app.py (60+ lines)
└── application/use_cases/
    ├── room_management.py (200+ lines)
    └── bot_management.py (150+ lines)
```

## Success Criteria

1. **No direct dependencies between layers** - Domain doesn't import from infrastructure ✅
2. **All cross-layer communication through interfaces** - Dependency inversion ✅
3. **Single responsibility per class** - No god objects ✅
4. **Testable domain logic** - Pure functions, no side effects ✅
5. **Event-driven communication** - Loose coupling through events ✅
6. **Clear boundaries** - Explicit interfaces between layers ✅

## Risk Mitigation

1. **Gradual Migration**: Keep old code working while building new structure
2. **Feature Flags**: Toggle between old and new implementations
3. **Compatibility Adapters**: Bridge old and new code
4. **Comprehensive Testing**: Ensure behavior preservation
5. **Documentation**: Clear migration guides for team

This plan transforms the tightly coupled architecture into a clean, maintainable system with proper abstractions and clear boundaries between concerns.

## Current Status

✅ **Phase 1 COMPLETE** - Domain Layer fully implemented with:
- Clean domain entities with proper encapsulation
- Immutable value objects
- Stateless domain services
- Comprehensive domain events
- Well-defined interfaces for infrastructure

✅ **Phase 2 COMPLETE** - Application Layer fully implemented with:
- Command pattern for all user actions
- Use cases for major operations
- Application services for orchestration
- Clean interfaces for infrastructure
- Consistent error handling and results

✅ **Phase 3 COMPLETE** - Infrastructure Layer fully implemented with:
- WebSocket adapters with connection management and broadcasting
- Multiple repository implementations (in-memory and file-based)
- Event publisher and store for event sourcing
- State machine adapter bridging old and new architecture
- Bot AI strategies with factory pattern
- Simple authentication with token management

✅ **Phase 4 COMPLETE** - Clean API Layer fully implemented with:
- WebSocket handlers using only application commands
- Dependency injection container managing all dependencies
- Additional use cases for room and bot management
- Unified routing for all WebSocket events
- Clean separation from domain and infrastructure

✅ **Phase 5 COMPLETE** - Event System fully implemented with:
- Event bus infrastructure with priority-based handler execution
- Game event handlers for notifications, state updates, bot actions, and audit
- Event sourcing support with replay and projections
- Complete migration from direct broadcasts to event publishing
- Comprehensive documentation for migration and usage

**Next Step**: Phase 6 - Testing and Migration for comprehensive test coverage and migration strategy.