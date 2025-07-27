# Legacy vs Clean Architecture Identification Guide

**Purpose**: This guide provides clear criteria for identifying which components belong to the legacy system versus the clean architecture implementation. Essential for safe and progressive rollout.

**Last Updated**: 2025-07-27  
**Current State**: Clean architecture ACTIVE via adapter-only mode (Phase 6 complete, Phase 7 pending)

## Quick Reference Decision Tree

```
Is the file/component Legacy or Clean Architecture?
│
├─ Located in domain/, application/, or infrastructure/ directories?
│  └─ YES → ✅ CLEAN ARCHITECTURE
│
├─ Located in engine/ directory (except state_machine/)?
│  └─ YES → ❌ LEGACY
│
├─ Named with "legacy" in filename or marked as legacy?
│  └─ YES → ❌ LEGACY
│
├─ Located in api/adapters/ directory?
│  └─ YES → ✅ CLEAN ARCHITECTURE (Bridge Components)
│
├─ Directly imports from socket_manager.py?
│  └─ YES → ❌ LEGACY
│
├─ Uses dependency injection and interfaces?
│  └─ YES → ✅ CLEAN ARCHITECTURE
│
└─ Mixed business logic with I/O operations?
   └─ YES → ❌ LEGACY
```

## Directory Structure Classification

### ✅ Clean Architecture Directories

```
backend/
├── domain/                     # ✅ CLEAN - Pure business logic
│   ├── entities/              # Business entities (Game, Player, Room)
│   ├── events/                # Domain events  
│   ├── interfaces/            # Port interfaces
│   ├── services/              # Domain services (scoring, rules)
│   └── value_objects/         # Immutable value objects
│
├── application/               # ✅ CLEAN - Application logic
│   ├── commands/              # Command objects
│   ├── dto/                   # Data transfer objects
│   ├── exceptions/            # Application-specific exceptions
│   ├── interfaces/            # Application port interfaces
│   ├── services/              # Application services
│   └── use_cases/             # Use case implementations
│
├── infrastructure/            # ✅ CLEAN - External concerns
│   ├── adapters/              # Infrastructure adapters
│   ├── caching/               # Caching implementations
│   ├── event_store/           # Event persistence
│   ├── events/                # Event infrastructure
│   ├── messaging/             # Message queue infrastructure
│   ├── monitoring/            # Observability and metrics
│   ├── persistence/           # Data persistence
│   ├── rate_limiting/         # Rate limiting implementations
│   ├── repositories/          # Repository implementations
│   ├── resilience/            # Circuit breakers, retry logic
│   ├── services/              # Infrastructure services
│   ├── state_persistence/     # State machine persistence
│   └── websocket/             # WebSocket infrastructure
│
└── api/
    └── adapters/              # ✅ CLEAN - WebSocket adapters
        ├── connection_adapters.py
        ├── game_adapters.py
        ├── lobby_adapters.py
        ├── room_adapters.py
        └── integrated_adapter_system.py
```

### ❌ Legacy Directories

```
backend/
├── engine/                    # ❌ LEGACY - Old game engine
│   ├── game.py               # Legacy game logic
│   ├── player.py             # Legacy player management
│   ├── room.py               # Legacy room implementation
│   ├── room_manager.py       # Legacy room manager
│   ├── bot_manager.py        # Legacy bot management
│   ├── scoring.py            # Legacy scoring
│   ├── rules.py              # Legacy game rules
│   ├── ai.py                 # Legacy AI implementation
│   └── async_*.py            # Legacy async wrappers
│
├── socket_manager.py         # ❌ LEGACY - WebSocket management
├── shared_instances.py       # ❌ LEGACY - Shared state
│
└── api/
    └── routes/
        └── ws_legacy_handlers.py  # ❌ LEGACY - Old handlers
```

### ⚡ Hybrid/Bridge Components

```
backend/
├── api/
│   └── routes/
│       ├── ws.py             # ⚡ HYBRID - Infrastructure with legacy handlers
│       └── ws_adapter_wrapper.py  # ⚡ BRIDGE - Routes to adapters
│
└── engine/
    └── state_machine/        # ⚡ ENTERPRISE - Modern state machine
        ├── game_state_machine.py
        └── states/           # Modern state implementations
```

## File-Level Identification Patterns

### Clean Architecture Characteristics

1. **Import Patterns** (Clean)
```python
# ✅ Clean imports - from clean architecture layers
from domain.entities import Game, Player
from domain.services.scoring_service import ScoringService
from application.use_cases.game.play import PlayUseCase
from infrastructure.repositories import GameRepository
```

2. **Dependency Injection** (Clean)
```python
# ✅ Constructor injection
class GameApplicationService:
    def __init__(
        self,
        game_repository: GameRepository,
        event_publisher: EventPublisher,
        scoring_service: ScoringService
    ):
        self._game_repository = game_repository
        self._event_publisher = event_publisher
        self._scoring_service = scoring_service
```

3. **Pure Functions** (Clean)
```python
# ✅ No side effects, pure business logic
def calculate_score(declaration: Declaration, actual_piles: int) -> Score:
    difference = abs(declaration.target_piles - actual_piles)
    return Score(value=difference * MULTIPLIER)
```

4. **Event-Driven** (Clean)
```python
# ✅ Domain events for communication
await self._event_publisher.publish(
    GameStartedEvent(
        game_id=game.id,
        players=[p.to_dict() for p in game.players]
    )
)
```

### Legacy Characteristics

1. **Import Patterns** (Legacy)
```python
# ❌ Legacy imports - direct infrastructure coupling
from backend.socket_manager import broadcast, register
from shared_instances import shared_room_manager, shared_bot_manager
from engine.game import Game as LegacyGame
import backend.socket_manager
```

2. **Direct State Mutation** (Legacy)
```python
# ❌ Direct mutation without events
async def play_pieces(self, pieces):
    self.current_pile.extend(pieces)
    self.player.hand.remove_pieces(pieces)
    await broadcast(self.room_id, "play", {"pieces": pieces})
```

3. **Mixed Responsibilities** (Legacy)
```python
# ❌ Business logic mixed with I/O
class RoomManager:
    async def create_room(self, name):
        room = Room(name)
        self.rooms[room.id] = room
        await broadcast("lobby", "room_created", room.to_dict())  # I/O in business logic
        return room
```

4. **Global State Access** (Legacy)
```python
# ❌ Access to global shared state
from shared_instances import shared_room_manager
room = await shared_room_manager.get_room(room_id)
```

## Component Mapping Reference

| Component Type | Legacy Location | Clean Architecture Location | Status |
|----------------|-----------------|----------------------------|---------|
| **Room Management** | `engine/room_manager.py` | `infrastructure/repositories/optimized_room_repository.py` | ✅ Migrated |
| **Game Logic** | `engine/game.py` | `domain/entities/game.py` + `application/services/game_application_service.py` | ✅ Migrated |
| **Player Management** | `engine/player.py` | `domain/entities/player.py` | ✅ Migrated |
| **Scoring** | `engine/scoring.py` | `domain/services/scoring_service.py` | ✅ Migrated |
| **Bot Management** | `engine/bot_manager.py` | `infrastructure/services/simple_bot_service.py` | ✅ Migrated |
| **WebSocket** | `socket_manager.py` | `infrastructure/websocket/connection_manager.py` | ✅ Migrated |
| **State Machine** | N/A (was embedded) | `engine/state_machine/` (Enterprise) | ✅ Enhanced |
| **Event System** | N/A (was broadcasts) | `domain/events/` + `infrastructure/events/` | ✅ New |

## Traffic Flow Analysis

### Current Architecture (Phase 6 Complete)

```
WebSocket Request → ws.py → adapter_wrapper → Clean Architecture
                      ↓
                 (Lines 316-327)
                      ↓
              Adapter System (100%)
                      ↓
           Clean Architecture Components
                      ↓
              Response to Client
              
Legacy handlers (line 328+) are NEVER reached
```

### Legacy Architecture (Pre-Migration)

```
WebSocket Request → ws.py → Legacy Handlers
                      ↓
              shared_room_manager
                      ↓
               engine/*.py
                      ↓
             socket_manager
                      ↓
            Response to Client
```

## Identification Tools and Commands

### 1. Check Import Dependencies
```bash
# Find legacy imports in a file
grep -E "(socket_manager|shared_instances|backend\.engine\.|from engine\.)" <filename>

# Find clean architecture imports
grep -E "(from (domain|application|infrastructure)\.|api\.adapters)" <filename>
```

### 2. Identify Architecture Type
```bash
# Check if file is in clean architecture directories
find backend/domain backend/application backend/infrastructure -name "*.py" | grep <filename>

# Check if file is in legacy directories  
find backend/engine -name "*.py" | grep <filename>
```

### 3. Pattern Analysis
```bash
# Find files with legacy patterns
grep -r "shared_room_manager\|shared_bot_manager" backend/

# Find files using dependency injection
grep -r "def __init__.*:.*Repository\|.*Service\|.*Publisher" backend/
```

## Common Confusion Points

### 1. `ws.py` - Why It's Hybrid
- **Infrastructure Role**: Handles WebSocket connections (needed)
- **Legacy Handlers**: Contains old business logic (bypassed)
- **Integration Point**: Lines 316-327 route to adapters
- **Future**: Phase 7 will clean up legacy handlers

### 2. State Machine - Why It's Enterprise
- Located in `engine/` but is NOT legacy
- Built with enterprise patterns:
  - Automatic broadcasting
  - Event sourcing
  - JSON-safe serialization
  - Single source of truth
- Uses `update_phase_data()` pattern

### 3. Adapters - Bridge Components
- Located in `api/adapters/`
- Bridge between WebSocket and clean architecture
- Handle 100% of traffic in adapter-only mode
- Will remain after Phase 7 cleanup

## Phase 7 Impact

When Phase 7 executes, these components will be removed:

### Will Be Removed ❌
- `engine/*.py` (except state_machine/)
- `socket_manager.py`
- `shared_instances.py`  
- Legacy handlers in `ws.py` (after line 327)
- `ws_legacy_handlers.py`
- Legacy test files

### Will Remain ✅
- All `domain/` components
- All `application/` components
- All `infrastructure/` components
- All `api/adapters/` components
- `engine/state_machine/` (Enterprise)
- WebSocket infrastructure in `ws.py`

## Quick Identification Checklist

For any file or component, ask:

1. **Directory Check**: Is it in domain/, application/, or infrastructure/?
   - YES → Clean Architecture ✅
   - NO → Continue checking

2. **Legacy Markers**: Does it have "legacy" in name or comments?
   - YES → Legacy ❌
   - NO → Continue checking

3. **Import Analysis**: Does it import from socket_manager or shared_instances?
   - YES → Legacy ❌
   - NO → Continue checking

4. **Pattern Check**: Does it use dependency injection and interfaces?
   - YES → Clean Architecture ✅
   - NO → Likely Legacy ❌

5. **Responsibility Check**: Does it mix business logic with I/O?
   - YES → Legacy ❌
   - NO → Clean Architecture ✅

## Summary

- **Clean Architecture**: Well-organized in dedicated directories, uses DI, pure functions, events
- **Legacy**: Mixed responsibilities, global state, direct I/O, located in engine/
- **Current State**: Clean architecture handles 100% traffic via adapters
- **Next Phase**: Phase 7 will remove legacy components entirely

Use this guide to confidently identify component types during the progressive rollout.