# Liap Tui - Complete Clean Architecture Implementation Plan

## 📋 Project Context
- **Project**: Liap Tui Online Board Game
- **Current Issues**: Circular imports, mixed layers, no tests
- **Goal**: Implement full clean architecture for learning and portfolio
- **Timeline**: Flexible (no deadline pressure)
- **Team**: Solo developer
- **Strategy**: Gradual refactoring with learning focus

## 🏗️ Target Architecture Structure

```
backend/
├── domain/                      # Core Business Logic (No external dependencies)
│   ├── __init__.py
│   ├── entities/               # Core business objects
│   │   ├── __init__.py
│   │   ├── player.py          # Player entity
│   │   ├── game.py            # Game aggregate root
│   │   ├── room.py            # Room entity
│   │   └── piece.py           # Game piece value object
│   ├── value_objects/          # Immutable values
│   │   ├── __init__.py
│   │   ├── game_phase.py      # GamePhase enum
│   │   ├── game_state.py      # Immutable game state
│   │   └── play_result.py     # Result of playing pieces
│   └── interfaces/             # Abstract interfaces
│       ├── __init__.py
│       ├── bot_strategy.py     # Interface for bot AI
│       ├── game_repository.py  # Interface for game storage
│       └── event_publisher.py  # Interface for events
│
├── application/                 # Use Cases & Business Rules
│   ├── __init__.py
│   ├── services/               # Application services
│   │   ├── __init__.py
│   │   ├── game_service.py    # Game orchestration
│   │   ├── room_service.py    # Room management
│   │   ├── bot_service.py     # Bot coordination
│   │   └── phase_service.py   # Phase management
│   ├── use_cases/              # Specific use cases
│   │   ├── __init__.py
│   │   ├── start_game.py      # Start game use case
│   │   ├── handle_redeal.py   # Redeal phase logic
│   │   ├── make_declaration.py # Declaration logic
│   │   └── play_turn.py       # Turn execution
│   └── dto/                    # Data Transfer Objects
│       ├── __init__.py
│       ├── game_events.py     # Event definitions
│       └── api_responses.py   # Response formats
│
├── infrastructure/              # External Dependencies
│   ├── __init__.py
│   ├── bot/                    # Bot implementations
│   │   ├── __init__.py
│   │   ├── ai_bot_strategy.py # Concrete bot AI
│   │   └── bot_manager_impl.py # Bot management
│   ├── persistence/            # Data storage
│   │   ├── __init__.py
│   │   └── in_memory_game_repository.py
│   ├── websocket/              # Real-time communication
│   │   ├── __init__.py
│   │   ├── connection_manager.py
│   │   └── event_dispatcher.py
│   └── game_engine/            # Game mechanics
│       ├── __init__.py
│       ├── phase_manager_impl.py
│       └── game_flow_controller_impl.py
│
├── presentation/                # API Layer
│   ├── __init__.py
│   ├── api/                    # REST endpoints
│   │   ├── __init__.py
│   │   ├── dependencies.py    # FastAPI dependencies
│   │   └── endpoints/
│   │       ├── __init__.py
│   │       ├── room_endpoints.py
│   │       ├── game_endpoints.py
│   │       └── health_endpoints.py
│   └── websocket/              # WebSocket handlers
│       ├── __init__.py
│       └── handlers.py
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── domain/                 # Domain tests
│   ├── application/            # Use case tests
│   ├── infrastructure/         # Integration tests
│   └── e2e/                    # End-to-end tests
│
├── scripts/                     # Development tools
│   ├── check_architecture.py   # Verify layer dependencies
│   └── migration_status.py     # Show progress
│
├── container.py                 # Dependency Injection Container
├── PROGRESS.md                  # Migration progress tracker
├── CONFIDENCE.md               # Learning journal
└── ARCHITECTURE.md             # Architecture documentation
```

## 📅 Implementation Timeline

### Week 1: Foundation & Domain Layer
**Goal**: Establish structure and pure domain logic

#### Day 1: Setup & Immediate Fixes (4 hours)
- [ ] Fix Player import in bot_manager.py
- [ ] Update FastAPI to use lifespan context manager
- [ ] Create folder structure (all folders, even if empty)
- [ ] Initialize git branch: `feature/clean-architecture`
- [ ] Create `scripts/check_architecture.py`
- [ ] Create tracking files: PROGRESS.md, CONFIDENCE.md

#### Day 2-3: Domain Entities (8 hours)
- [ ] Create `domain/entities/player.py` with tests
- [ ] Create `domain/entities/piece.py` (game pieces)
- [ ] Create `domain/value_objects/game_phase.py`
- [ ] Document learnings about entities vs value objects

#### Day 4-5: Domain Core (8 hours)
- [ ] Create `domain/entities/game.py` (aggregate root)
- [ ] Create `domain/entities/room.py`
- [ ] Create `domain/value_objects/game_state.py`
- [ ] Implement core game rules in domain

#### Day 6-7: Domain Interfaces (6 hours)
- [ ] Create `domain/interfaces/bot_strategy.py`
- [ ] Create `domain/interfaces/game_repository.py`
- [ ] Create `domain/interfaces/event_publisher.py`
- [ ] Verify domain has ZERO external dependencies

**Checkpoint 1**: Domain layer complete and tested

### Week 2: Application Layer
**Goal**: Implement use cases and orchestration

#### Day 8-9: Core Use Cases (8 hours)
- [ ] Create `application/use_cases/start_game.py`
- [ ] Create `application/use_cases/handle_redeal.py`
- [ ] Create `application/dto/game_events.py`
- [ ] Write tests for each use case

#### Day 10-11: Application Services (8 hours)
- [ ] Create `application/services/game_service.py`
- [ ] Create `application/services/room_service.py`
- [ ] Create `application/services/phase_service.py`
- [ ] Ensure services only orchestrate, not implement

#### Day 12-14: More Use Cases (10 hours)
- [ ] Create `application/use_cases/make_declaration.py`
- [ ] Create `application/use_cases/play_turn.py`
- [ ] Create `application/services/bot_service.py`
- [ ] Document use case patterns learned

**Checkpoint 2**: Application layer complete with no infrastructure deps

### Week 3: Infrastructure Layer
**Goal**: Implement external dependencies

#### Day 15-16: Bot Infrastructure (8 hours)
- [ ] Create `infrastructure/bot/ai_bot_strategy.py`
- [ ] Create `infrastructure/bot/bot_manager_impl.py`
- [ ] Migrate existing bot AI logic
- [ ] Test bot behavior in isolation

#### Day 17-18: Game Infrastructure (8 hours)
- [ ] Create `infrastructure/game_engine/phase_manager_impl.py`
- [ ] Create `infrastructure/game_engine/game_flow_controller_impl.py`
- [ ] Create `infrastructure/persistence/in_memory_game_repository.py`
- [ ] Ensure all implement domain interfaces

#### Day 19-21: WebSocket Infrastructure (10 hours)
- [ ] Create `infrastructure/websocket/connection_manager.py`
- [ ] Create `infrastructure/websocket/event_dispatcher.py`
- [ ] Migrate WebSocket logic from current system
- [ ] Test real-time features

**Checkpoint 3**: Infrastructure layer complete

### Week 4: Presentation & Integration
**Goal**: Wire everything together

#### Day 22-23: API Layer (8 hours)
- [ ] Create `presentation/api/dependencies.py`
- [ ] Create `presentation/api/endpoints/room_endpoints.py`
- [ ] Create `presentation/api/endpoints/game_endpoints.py`
- [ ] Ensure endpoints only call use cases

#### Day 24-25: WebSocket Handlers (8 hours)
- [ ] Create `presentation/websocket/handlers.py`
- [ ] Wire WebSocket to use cases
- [ ] Test real-time features end-to-end

#### Day 26-27: Dependency Injection (8 hours)
- [ ] Create `container.py` with full DI setup
- [ ] Update `main.py` to use new architecture
- [ ] Add feature toggle for gradual migration
- [ ] Test entire system with new architecture

#### Day 28: Cleanup & Documentation (6 hours)
- [ ] Remove old code (after confirming new works)
- [ ] Write ARCHITECTURE.md
- [ ] Update README.md
- [ ] Create blog post about journey

**Checkpoint 4**: Full migration complete

## 📊 Progress Tracking

### Daily Checklist Template
```markdown
## Day [X] - [Date] - [Focus Area]

### 🎯 Today's Goals:
- [ ] Specific file/component to create
- [ ] Tests to write
- [ ] Documentation to update

### ✅ Completed:
- What was actually done
- Any surprises or learnings

### 🚧 Blockers:
- Any issues encountered
- Questions that need answers

### 📚 Learned:
- New concepts understood
- Patterns discovered
- Mistakes to avoid

### 🔮 Tomorrow:
- Next file/component to tackle
- Research needed

### 💭 Confidence Level: X/10
- Current understanding
- Areas still unclear
```

## 🛡️ Architecture Rules & Checks

### Layer Dependencies (MUST FOLLOW)
```python
# Domain Layer Rules:
- NO imports from: application, infrastructure, presentation
- NO framework imports: fastapi, websockets, databases
- ONLY stdlib imports: typing, dataclasses, enum, abc

# Application Layer Rules:
- CAN import from: domain
- NO imports from: infrastructure, presentation
- NO framework imports

# Infrastructure Layer Rules:
- CAN import from: domain (interfaces only)
- CAN use any frameworks/libraries
- MUST implement domain interfaces

# Presentation Layer Rules:
- CAN import from: application, domain (DTOs only)
- CAN use web frameworks
- NO business logic
```

### Architecture Validation Script
```python
# scripts/check_architecture.py
#!/usr/bin/env python3

import os
import re
from pathlib import Path

def check_layer_dependencies():
    """Verify architectural boundaries"""
    violations = []
    
    # Check domain purity
    domain_files = Path('backend/domain').rglob('*.py')
    for file in domain_files:
        content = file.read_text()
        # Check for forbidden imports
        forbidden = ['application', 'infrastructure', 'presentation', 'fastapi', 'websocket']
        for bad_import in forbidden:
            if f'from {bad_import}' in content or f'import {bad_import}' in content:
                violations.append(f"Domain violation: {file} imports {bad_import}")
    
    # Check application doesn't import infrastructure
    app_files = Path('backend/application').rglob('*.py')
    for file in app_files:
        content = file.read_text()
        if 'from infrastructure' in content or 'import infrastructure' in content:
            violations.append(f"Application violation: {file} imports infrastructure")
    
    return violations

if __name__ == "__main__":
    violations = check_layer_dependencies()
    if violations:
        print("❌ Architecture violations found:")
        for v in violations:
            print(f"  - {v}")
        exit(1)
    else:
        print("✅ Architecture is clean!")
```

## 🚀 Migration Strategy

### Phase 1: Parallel Development
- Keep old system running at all times
- Build new system alongside
- Use feature flags to switch between them

### Phase 2: Gradual Switchover
```python
# main.py
USE_NEW_ARCHITECTURE = os.getenv("USE_NEW_ARCH", "false") == "true"

if USE_NEW_ARCHITECTURE:
    from presentation.api import create_app
    from container import DIContainer
    container = DIContainer()
    app = create_app(container)
else:
    # Existing code
    from backend.api.main import app
```

### Phase 3: Endpoint Migration
- Migrate one endpoint at a time
- Test thoroughly before moving next
- Keep both versions until all migrated

## 🎯 Success Metrics

### Technical Metrics
- [ ] Zero circular imports
- [ ] 100% domain layer test coverage
- [ ] All layers respect boundaries
- [ ] Can swap implementations via DI

### Learning Metrics
- [ ] Can explain each pattern used
- [ ] Understand why each decision made
- [ ] Could teach someone else
- [ ] Portfolio-ready code

## 📚 Learning Resources

### Must Read
1. "Clean Architecture" by Robert Martin - Chapters 11-17
2. "Domain-Driven Design" by Eric Evans - Chapters 5-6
3. "Dependency Injection Principles, Practices, and Patterns"

### Patterns to Study
- Repository Pattern
- Use Case Pattern
- Dependency Injection
- Strategy Pattern
- Observer Pattern (for events)

## 🔧 Troubleshooting Guide

### Common Issues

#### Circular Import in New Code
**Symptom**: Import error when creating new modules
**Solution**: You're violating layer boundaries. Check which layer should own the code.

#### "Where does X belong?"
**Domain**: Core business rules, entities, value objects
**Application**: Use case orchestration, workflow
**Infrastructure**: External systems, frameworks, databases
**Presentation**: User interface, API endpoints

#### Testing Difficulties
**Symptom**: Need entire system to test one component
**Solution**: Add interface, inject dependencies

## 📝 Final Notes

### Remember
1. **Go slow** - Understanding > Speed
2. **Test everything** - Build testing habit
3. **Document learnings** - Future reference
4. **Commit often** - Easy rollback
5. **Ask questions** - Document uncertainties

### When Stuck
1. Review this plan
2. Check architecture rules
3. Look at completed examples
4. Take a break
5. Do simpler task first

### Celebrate Milestones
- Domain complete: 🎉
- First use case works: 🎊
- Infrastructure done: 🎯
- Full migration: 🏆

---
*Last Updated: [Current Date]*
*Version: 1.0*