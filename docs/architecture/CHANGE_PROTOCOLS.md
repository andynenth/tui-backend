# Architecture Change Protocols

**Purpose:** Mandatory checklists and protocols to prevent architectural confusion and ensure proper system boundaries.

## 🚨 MANDATORY PRE-CHANGE CHECKLIST

Before making ANY architectural change, developers MUST complete this checklist:

### 1. System Identification
- [ ] I have identified which system this change affects:
  - [ ] Clean Architecture (business logic, data persistence, APIs)
  - [ ] Engine Layer (game mechanics, state machine, bots)
  - [ ] Integration between both systems
- [ ] I have consulted the [Quick Architecture Reference](./QUICK_ARCHITECTURE_REFERENCE.md)
- [ ] I have reviewed [ADR-001](./ADR-001-Clean-Architecture-vs-Engine-Layer.md)

### 2. Component Analysis
- [ ] I have identified the specific components involved:
  - [ ] Domain entities/value objects (Clean Architecture)
  - [ ] Use cases/application services (Clean Architecture)
  - [ ] Infrastructure/adapters (Clean Architecture)
  - [ ] State machines/game logic (Engine Layer)
  - [ ] Bot management (Engine Layer)
- [ ] I understand the responsibility of each component

### 3. Boundary Validation
- [ ] My change does NOT violate architectural boundaries:
  - [ ] No direct imports from Engine Layer into Clean Architecture
  - [ ] No business logic in Engine Layer
  - [ ] No game mechanics in Clean Architecture
  - [ ] No circular dependencies created
- [ ] Integration points use proper adapter patterns

### 4. Feature Flag Review
- [ ] I have checked relevant feature flags:
  - [ ] `USE_STATE_PERSISTENCE` for Clean Architecture state
  - [ ] `USE_EVENT_SOURCING` for event persistence
  - [ ] `USE_CLEAN_ARCHITECTURE` for Clean Architecture features
- [ ] I understand which flags control my changes

---

## 📋 CHANGE-SPECIFIC PROTOCOLS

### For Clean Architecture Changes

#### Adding New Use Cases
- [ ] Use case follows Clean Architecture layers
- [ ] Dependencies point inward (Dependency Inversion)
- [ ] Domain events are used for side effects
- [ ] State changes go through `StateManagementAdapter`
- [ ] No direct Engine Layer imports

**Template Checklist:**
```
[ ] Use case in application/use_cases/ directory
[ ] Implements UseCase[Request, Response] interface
[ ] Uses UnitOfWork for data access
[ ] Publishes domain events for side effects
[ ] Uses StateManagementAdapter for state tracking
[ ] Tests cover business scenarios
[ ] No Engine Layer dependencies
```

#### Modifying Domain Entities
- [ ] Changes maintain domain integrity
- [ ] Business rules stay in domain layer
- [ ] Events are emitted for state changes
- [ ] No persistence concerns in entities
- [ ] No Engine Layer concepts mixed in

**Template Checklist:**
```
[ ] Entity in domain/entities/ directory
[ ] Business rules encapsulated in entity
[ ] Domain events emitted on state changes
[ ] No database/persistence code
[ ] No Engine Layer imports
[ ] Immutable value objects used
```

#### Infrastructure Changes
- [ ] Adapters implement application interfaces
- [ ] External dependencies isolated
- [ ] Feature flags respected
- [ ] Circuit breakers for resilience
- [ ] No business logic in infrastructure

**Template Checklist:**
```
[ ] Adapter implements application interface
[ ] External system dependencies isolated
[ ] Feature flags control behavior
[ ] Error handling and resilience
[ ] No business rules in infrastructure
[ ] Proper logging and metrics
```

### For Engine Layer Changes

#### Game Mechanics Modifications
- [ ] Changes stay within Engine Layer
- [ ] No business logic mixed with game rules
- [ ] State machine patterns maintained
- [ ] Bot behavior encapsulated
- [ ] No direct database access

**Template Checklist:**
```
[ ] Code in backend/engine/ directory
[ ] Game rules separate from business rules
[ ] State machine transitions valid
[ ] No Clean Architecture imports
[ ] No direct persistence code
[ ] Bot logic encapsulated
```

#### State Machine Updates
- [ ] Phase transitions follow game rules
- [ ] State changes are atomic
- [ ] No business validation in state machine
- [ ] Communicates with Clean Architecture via events
- [ ] No persistence concerns

**Template Checklist:**
```
[ ] State machine in engine/state_machine/
[ ] Valid state transitions only
[ ] Atomic state changes
[ ] Event-based communication outward
[ ] No business rule validation
[ ] No direct database access
```

### For Integration Changes

#### Adapter Modifications
- [ ] Adapter bridges systems properly
- [ ] No leakage of concepts between systems
- [ ] Feature flags control integration
- [ ] Error handling for both systems
- [ ] Clear separation of concerns

**Template Checklist:**
```
[ ] Adapter in application/adapters/
[ ] Bridges systems without leaking concepts
[ ] Feature flag controlled
[ ] Handles errors from both systems
[ ] Maps between domain and engine concepts
[ ] No business logic in adapter
```

---

## 🔍 VALIDATION PROCEDURES

### Pre-Commit Validation
Run these commands before committing:

```bash
# 1. Architecture boundary check
python scripts/validate_architecture.py

# 2. Import dependency check  
python scripts/check_dependencies.py

# 3. Feature flag consistency
python scripts/validate_feature_flags.py

# 4. Run relevant tests
pytest backend/tests/architecture/
pytest backend/tests/integration/
```

### Code Review Requirements
Reviewers MUST verify:

- [ ] Checklist was completed and documented
- [ ] Architectural boundaries maintained
- [ ] Feature flags properly used
- [ ] Tests cover architectural scenarios
- [ ] Documentation updated if needed
- [ ] No architectural debt introduced

### Post-Change Verification
After changes are merged:

- [ ] Integration tests pass
- [ ] Feature flags work as expected
- [ ] Performance metrics stable
- [ ] No architectural violations detected
- [ ] Monitoring shows healthy system

---

## ⚠️ COMMON VIOLATION PATTERNS TO AVOID

### ❌ NEVER Do These

1. **Import Engine Layer in Clean Architecture**
   ```python
   # DON'T DO THIS
   from backend.engine.state_machine import GameStateMachine
   ```

2. **Put Business Logic in Engine Layer**
   ```python
   # DON'T DO THIS - belongs in use case
   class GameStateMachine:
       def validate_user_permission(self, user_id):
   ```

3. **Direct Database Access in Engine**
   ```python
   # DON'T DO THIS - use adapters
   class BotManager:
       def save_state(self):
           database.save(...)
   ```

4. **Mix Game Mechanics with Business Rules**
   ```python
   # DON'T DO THIS
   class Game:  # Domain entity
       def calculate_bot_difficulty(self):  # Engine concern
   ```

5. **Bypass Feature Flags**
   ```python
   # DON'T DO THIS
   if True:  # Should check USE_STATE_PERSISTENCE
       state_adapter.track_change(...)
   ```

### ✅ ALWAYS Do These

1. **Use Proper Adapters**
   ```python
   # DO THIS
   class StateManagementAdapter:
       def track_phase_change(self, ...):
   ```

2. **Respect System Boundaries**
   ```python
   # DO THIS - Clean Architecture use case
   class StartGameUseCase:
       def __init__(self, state_adapter: StateManagementAdapter):
   ```

3. **Check Feature Flags**
   ```python
   # DO THIS
   if feature_flags.is_enabled(USE_STATE_PERSISTENCE):
       state_adapter.track_change(...)
   ```

4. **Separate Concerns Properly**
   ```python
   # DO THIS - Engine handles game mechanics
   class GameStateMachine:
       def transition_to_next_phase(self):
   
   # DO THIS - Clean Architecture handles business logic
   class StartGameUseCase:
       def validate_room_ready(self):
   ```

---

## 📝 CHANGE REQUEST TEMPLATE

When proposing architectural changes, use this template:

```markdown
# Architecture Change Request

## Change Summary
Brief description of proposed change.

## System Impact
- [ ] Clean Architecture affected: [components]
- [ ] Engine Layer affected: [components]  
- [ ] Integration points affected: [adapters]

## Boundary Analysis
- [ ] No architectural boundaries violated
- [ ] Proper separation of concerns maintained
- [ ] Feature flags properly utilized

## Pre-Change Checklist
- [ ] Completed mandatory checklist
- [ ] Reviewed Quick Architecture Reference
- [ ] Consulted relevant ADRs
- [ ] Identified all affected components

## Implementation Plan
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Testing Strategy
- [ ] Unit tests for affected components
- [ ] Integration tests for system boundaries
- [ ] Architecture validation tests
- [ ] Feature flag testing

## Risk Assessment
- Low/Medium/High risk change
- Potential impact areas
- Rollback strategy

## Documentation Updates
- [ ] ADRs updated if needed
- [ ] Quick Reference updated if needed
- [ ] Code comments added/updated
```

---

## 🚨 EMERGENCY PROCEDURES

### If You Realize You've Mixed Architectures

1. **STOP IMMEDIATELY**
   - Don't continue down the wrong path
   - Don't commit the mixed code

2. **ASSESS THE DAMAGE**
   - Run `python scripts/check_dependencies.py`
   - Review what boundaries were crossed
   - Identify affected components

3. **CLEAN SEPARATION**
   - Move Engine Layer code to proper location
   - Move Clean Architecture code to proper location
   - Create proper adapters for integration
   - Remove direct dependencies

4. **VALIDATE FIX**
   - Run architecture validation scripts
   - Check feature flags work correctly
   - Run integration tests
   - Verify boundaries are clean

5. **DOCUMENT LESSONS**
   - Update this protocol if needed
   - Share learnings with team
   - Consider additional safeguards

---

## 🔧 AUTOMATION SUPPORT

### Pre-Commit Hooks
Install these hooks to catch violations early:

```bash
# In .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: architecture-check
        name: Architecture Boundary Check
        entry: python scripts/validate_architecture.py
        language: system
        types: [python]
        
      - id: dependency-check
        name: Import Dependency Check
        entry: python scripts/check_dependencies.py
        language: system
        types: [python]
        
      - id: feature-flag-check
        name: Feature Flag Validation
        entry: python scripts/validate_feature_flags.py
        language: system
        types: [python]
```

### IDE Configuration
Configure your IDE to warn about violations:

```json
// VS Code settings.json
{
  "python.linting.pylintArgs": [
    "--load-plugins=architecture_checker"
  ],
  "python.analysis.extraPaths": [
    "./scripts"
  ]
}
```

---

## 📚 TRAINING RESOURCES

### Required Reading
- [ADR-001: Clean Architecture vs Engine Layer](./ADR-001-Clean-Architecture-vs-Engine-Layer.md)
- [Quick Architecture Reference](./QUICK_ARCHITECTURE_REFERENCE.md)
- [Clean Architecture Principles](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

### Hands-On Exercises
1. Complete architecture boundary identification exercise
2. Practice using feature flags correctly
3. Implement proper adapter patterns
4. Review violation examples and fixes

### Team Agreements
- All team members complete architectural training
- Pair programming for complex architectural changes
- Regular architecture reviews in sprint planning
- Incident post-mortems include architectural analysis

---

**Version:** 1.0.0  
**Last Updated:** 2025-01-01  
**Next Review:** 2025-02-01  
**Maintainer:** Development Team

---

*This document is living documentation. Update it as we learn from violations and improve our processes.*