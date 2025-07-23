# Module Architecture Analysis - Liap Tui Backend

## Current Directory Structure

```
backend/
├── api/                    # Web/API layer
│   ├── routes/            # HTTP and WebSocket endpoints
│   ├── websocket/         # WebSocket-specific infrastructure
│   ├── middleware/        # Cross-cutting concerns (rate limiting, etc.)
│   ├── services/          # API-level services (event store, health, recovery)
│   └── validation/        # Input validation
├── engine/                # Core game domain
│   ├── state_machine/     # Game flow control
│   │   ├── states/       # Individual game phase implementations
│   │   └── core.py       # State machine abstractions
│   ├── async_*.py        # Async variants of core classes
│   └── *.py              # Core game entities (game, player, piece, etc.)
├── shared_instances.py    # Global singletons
├── socket_manager.py      # WebSocket broadcasting infrastructure
└── config/               # Configuration modules
```

## Module Dependencies and Coupling Issues

### 1. **Circular Dependencies and Tight Coupling**

#### Global Singletons Pattern
- `shared_instances.py` creates global instances:
  - `shared_room_manager` (RoomManager)
  - `shared_bot_manager` (BotManager)
- These are imported throughout the codebase, creating tight coupling

#### WebSocket Infrastructure Coupling
- `socket_manager.py` imports `shared_instances` to access room_manager
- `ws.py` imports both `socket_manager` and `shared_instances`
- This creates a circular dependency chain

#### State Machine ↔ Game Engine Coupling
- `GameStateMachine` directly imports and wraps `Game` and `AsyncGame`
- State classes import game engine modules directly (`engine.rules`, `engine.scoring`)
- No abstraction layer between state machine and game logic

### 2. **Import Relationships**

#### API Layer → Engine Layer (Expected)
```python
# ws.py
from backend.shared_instances import shared_room_manager
from backend.socket_manager import broadcast, register, unregister
# Direct coupling to infrastructure and domain
```

#### Engine Layer → API Layer (Problematic)
```python
# socket_manager.py
from backend.shared_instances import shared_room_manager
# Domain importing from web layer - violation of dependency direction
```

#### State Machine → Game Engine (Tight Coupling)
```python
# game_state_machine.py
from engine.async_game import AsyncGame
from engine.game import Game
# Direct dependency on concrete implementations
```

### 3. **Missing Abstraction Layers**

#### No Domain/Application Boundary
- API routes directly manipulate domain objects
- No application services to orchestrate domain operations
- Business logic mixed with web concerns in `ws.py`

#### No Repository Pattern
- Direct manipulation of room/game collections in managers
- No abstraction for persistence or state storage

#### No Event Bus/Mediator
- Direct broadcasting calls throughout the code
- State changes tightly coupled to WebSocket broadcasting
- No abstraction for event propagation

#### No Dependency Injection
- Hard-coded dependencies using imports
- Global singleton pattern prevents testing and modularity
- No interfaces/protocols for key services

### 4. **Areas of Concern**

#### Mixed Responsibilities
1. **socket_manager.py**: 
   - WebSocket connection management
   - Message queuing and broadcasting
   - Rate limiting
   - Message acknowledgment/reliability
   - Statistics tracking
   - Direct room/game state access

2. **Room class**:
   - Player management
   - Game lifecycle
   - State machine integration
   - Disconnection handling
   - Bot management coordination

3. **GameStateMachine**:
   - State transitions
   - Action processing
   - Broadcasting (through callbacks)
   - Game adapter wrapping
   - Direct game manipulation

#### Infrastructure in Domain
- Broadcasting logic embedded in state machine base class
- WebSocket concerns in game state implementations
- Network-specific data (operation_id, timestamps) in domain events

#### Async Duplication
- Separate async versions of classes (AsyncGame, AsyncRoom, etc.)
- No unified async abstraction
- Adapter pattern used but not consistently

## Key Architectural Issues

1. **Layering Violations**: Domain layer depends on infrastructure (shared_instances)
2. **Global State**: Singleton pattern makes testing and modularity difficult  
3. **Missing Abstractions**: No interfaces between layers
4. **Mixed Concerns**: Business logic intertwined with infrastructure
5. **Tight Coupling**: Direct imports create rigid dependencies
6. **No Inversion of Control**: Dependencies flow inward rather than outward
7. **Infrastructure Leakage**: WebSocket/broadcasting concerns throughout domain

## Recommendations for Abstraction Layers

### 1. **Domain/Application Services Layer**
- Create application services to orchestrate domain operations
- Move business logic from ws.py to services
- Implement command/query separation

### 2. **Repository/Persistence Abstraction**
- Abstract room and game storage behind interfaces
- Enable different storage implementations
- Separate domain models from persistence

### 3. **Event/Message Bus**
- Decouple state changes from broadcasting
- Implement domain events separate from WebSocket events
- Enable multiple event handlers/subscribers

### 4. **Dependency Injection Container**
- Replace global singletons with DI
- Define interfaces for key services
- Enable testing and modularity

### 5. **Clean Architecture Boundaries**
- Domain layer with pure business logic
- Application layer for use cases
- Infrastructure layer for external concerns
- Clear dependency rules (inward only)

### 6. **Unified Async Abstraction**
- Single async interface for all game operations
- Remove duplicate async classes
- Consistent async patterns throughout