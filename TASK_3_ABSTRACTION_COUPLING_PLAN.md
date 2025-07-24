# Task 3: Abstraction & Coupling - Detailed Execution Plan

## ⚠️ IMPORTANT: Lessons Learned from Previous Integration Failure

### What Went Wrong in Commit 4d54b43
1. **Big Bang Integration**: Attempted to switch entire system at once by changing `start.sh` entry point
2. **Missing Event Classes**: Application layer expected events that weren't implemented, causing runtime errors
3. **Disconnected Implementation**: Components were "100% complete but 0% integrated" - they existed but weren't connected
4. **No Incremental Testing**: Couldn't verify individual components before full cutover
5. **No Rollback Path**: Once switched, the system was broken with no way back

### Key Insight
> "All these files have been modified. Based on the error messages and what I've seen, it seems the clean architecture implementation is incomplete - there are many missing event classes that the application layer expects."

## New Phased Approach to Prevent Integration Failures

### Core Principles
1. **Adapter Pattern First**: Create adapters that work alongside existing code, not replacements
2. **Event-First Development**: Implement ALL events before any component uses them
3. **Incremental Integration**: Each phase must be integrated and tested in production
4. **Feature Flags**: Gradual rollout with ability to instantly rollback
5. **No Big Bang**: Old system keeps running while new system is built alongside

### Phase Overview

| Phase | Focus | Key Deliverable | Integration Strategy | Checklist File |
|-------|-------|-----------------|---------------------|----------------|
| **Phase 0** | Feature Inventory | Complete feature catalog & behavioral tests | Shadow mode validation | [PHASE_0_FEATURE_INVENTORY.md](./PHASE_0_FEATURE_INVENTORY.md) |
| **Phase 1** | Clean API Layer | API Adapters wrapping existing handlers | Side-by-side operation | [PHASE_1_CLEAN_API_LAYER.md](./PHASE_1_CLEAN_API_LAYER.md) |
| **Phase 2** | Event System | Complete event implementation | Parallel event publishing | [PHASE_2_EVENT_SYSTEM.md](./PHASE_2_EVENT_SYSTEM.md) |
| **Phase 3** | Domain Layer | Pure business logic | Behind interfaces only | [PHASE_3_DOMAIN_LAYER.md](./PHASE_3_DOMAIN_LAYER.md) |
| **Phase 4** | Application Layer | Use cases with adapters | Feature-flagged operations | [PHASE_4_APPLICATION_LAYER.md](./PHASE_4_APPLICATION_LAYER.md) |
| **Phase 5** | Infrastructure | Repositories and services | Gradual data migration | [PHASE_5_INFRASTRUCTURE.md](./PHASE_5_INFRASTRUCTURE.md) |
| **Phase 6** | Gradual Cutover | Progressive feature enablement | Monitored rollout | [PHASE_6_GRADUAL_CUTOVER.md](./PHASE_6_GRADUAL_CUTOVER.md) |

### Why Phase 0 is Critical

The previous attempt failed partly because features were missed or behaved differently in the new implementation. Phase 0 prevents this by:
- **Cataloging every feature** before any code changes
- **Creating behavioral tests** that document exact current behavior
- **Setting up shadow mode** to detect any discrepancies
- **Establishing clear acceptance criteria** for migration success

Without Phase 0, you risk building a "clean" architecture that doesn't actually do everything the current system does.

### Why This Approach Works

#### ❌ Previous Approach (Failed)
```
1. Build all components separately
2. Switch entry point
3. Hope everything works
4. System crashes with missing dependencies
```

#### ✅ New Approach (Incremental)
```
0. Document every feature and behavior first
1. Build adapter for one endpoint
2. Route 1% of traffic through it
3. Monitor and verify it works
4. Gradually increase traffic
5. Only then build next component
```

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

## New Phased Implementation Approach

The old "big bang" approach of implementing everything separately and then switching over has been replaced with an incremental, integrated approach. Each phase now includes:

1. **Implementation** - Build the components
2. **Integration** - Connect to the live system using adapters
3. **Testing** - Verify in production environment
4. **Stabilization** - Monitor and fix issues before proceeding

### Implementation Phases

Please refer to the individual phase checklists for detailed implementation steps:

1. **[PHASE_1_CLEAN_API_LAYER.md](./PHASE_1_CLEAN_API_LAYER.md)** - Create API adapters alongside existing handlers
2. **[PHASE_2_EVENT_SYSTEM.md](./PHASE_2_EVENT_SYSTEM.md)** - Implement complete event system first
3. **[PHASE_3_DOMAIN_LAYER.md](./PHASE_3_DOMAIN_LAYER.md)** - Build pure domain logic
4. **[PHASE_4_APPLICATION_LAYER.md](./PHASE_4_APPLICATION_LAYER.md)** - Create use cases with adapters
5. **[PHASE_5_INFRASTRUCTURE.md](./PHASE_5_INFRASTRUCTURE.md)** - Implement repositories and services
6. **[PHASE_6_GRADUAL_CUTOVER.md](./PHASE_6_GRADUAL_CUTOVER.md)** - Progressive feature enablement

### Critical Success Factors

1. **No Phase Skipping** - Each phase must be completed and verified before proceeding
2. **Integration First** - Every component must be integrated and tested, not just implemented
3. **Feature Flags** - All new features behind flags for instant rollback
4. **Monitoring** - Comprehensive logging and metrics for each phase
5. **Documentation** - Update as you go, not at the end

## Success Criteria

1. **No direct dependencies between layers** - Domain doesn't import from infrastructure
2. **All cross-layer communication through interfaces** - Dependency inversion
3. **Single responsibility per class** - No god objects
4. **Testable domain logic** - Pure functions, no side effects
5. **Event-driven communication** - Loose coupling through events
6. **Clear boundaries** - Explicit interfaces between layers

## Risk Mitigation

1. **Gradual Migration**: Keep old code working while building new structure
2. **Feature Flags**: Toggle between old and new implementations
3. **Compatibility Adapters**: Bridge old and new code
4. **Comprehensive Testing**: Ensure behavior preservation
5. **Documentation**: Clear migration guides for team

## What Makes This Approach Different

### Previous Failed Approach (Commit 4d54b43)
- **Built in Isolation**: Created all clean architecture components without connecting them
- **Big Bang Switch**: Changed entry point hoping everything would work
- **Missing Dependencies**: Application layer expected events that didn't exist
- **No Testing Path**: Couldn't verify components before full switch
- **Result**: "100% complete but 0% integrated" - system crashed on startup

### New Incremental Approach
- **Built with Integration**: Each component is connected to live system immediately
- **Adapter Pattern**: New code wraps old code, doesn't replace it
- **Event-First**: Implement all events before anything uses them
- **Continuous Testing**: Each component tested in production before next phase
- **Result**: Gradual, stable migration with rollback capability at each step

### Example: Phase 1 API Adapter
Instead of replacing the WebSocket handler:
```python
# Old approach: Replace everything
# ❌ Delete ws.py, create new handler, hope it works

# New approach: Wrap and forward
# ✅ Create adapter that calls existing ws.py
class WebSocketAdapter:
    def __init__(self, legacy_handler, command_bus):
        self.legacy = legacy_handler
        self.commands = command_bus
    
    async def handle_message(self, message):
        if feature_flag('use_clean_architecture'):
            return await self.commands.execute(message)
        else:
            return await self.legacy.handle(message)
```

This ensures the system keeps working while we build the new architecture alongside it.

## Frontend Compatibility Throughout Migration

### Current Frontend Interface
The frontend exclusively uses WebSocket for ALL game operations:
- **NO REST endpoints used for game logic** (only WebSocket)
- **All game actions via WebSocket messages**
- **All game state updates via WebSocket broadcasts**

### Compatibility Strategy
1. **Message Contract Preservation**: All WebSocket messages maintain exact same structure
2. **Adapter Pattern**: New architecture wraps old, doesn't replace
3. **Feature Flags**: Gradual rollout with instant rollback
4. **Shadow Mode Validation**: Compare every response for differences
5. **Zero Frontend Changes**: Backend migration is completely transparent

### What This Means
- ✅ Frontend continues working without ANY modifications
- ✅ No coordinated deployments needed
- ✅ Players experience zero disruption
- ✅ Can rollback instantly if issues detected

### Contract Testing Implementation Status

**✅ COMPLETED (Ready for Use):**
- ✅ All 21 WebSocket message contracts defined (`backend/tests/contracts/websocket_contracts.py`)
- ✅ Golden master capture framework implemented (`backend/tests/contracts/golden_master.py`)
- ✅ Parallel test runner for comparing behaviors (`backend/tests/contracts/parallel_runner.py`)
- ✅ Example test suite with usage patterns (`backend/tests/contracts/test_websocket_contracts.py`)
- ✅ Comprehensive documentation (`backend/CONTRACT_TESTING_README.md`)
- ✅ Capture script ready to run (`backend/tests/contracts/capture_golden_masters.py`)

**⚠️ REQUIRED Before Each Phase:**
1. **Before Phase 1**: Run `python backend/tests/contracts/capture_golden_masters.py` to establish baseline
2. **During Each Phase**: Run `pytest backend/tests/contracts/` after every change
3. **Phase Completion**: Verify 100% contract test pass rate

**Contract Testing Integration Points:**
- **Phase 0**: ✅ Contract framework built and ready
- **Phase 1**: Test each adapter against golden masters
- **Phase 2**: Verify use cases maintain compatibility
- **Phase 3**: Ensure repositories don't break contracts
- **Phase 4**: Test async operations maintain timing
- **Phase 5**: Final validation before legacy removal

## Start with Phase 1

Begin implementation with [PHASE_1_CLEAN_API_LAYER.md](./PHASE_1_CLEAN_API_LAYER.md)