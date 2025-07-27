# Cross-Dependency Analysis Report

**Generated**: 2025-07-27  
**Purpose**: Document and plan resolution of clean architecture files with legacy dependencies  
**Status**: 6 cross-dependencies found requiring resolution before Phase 7

## 🚨 Critical Finding

The analysis revealed **6 cross-dependencies** where clean architecture files import from legacy code. These must be resolved before Phase 7 can proceed safely.

## 📊 Dependency Breakdown

### 1. Event System Test Dependencies (3 instances)
**File**: `tests/events/validate_event_system.py`  
**Legacy Imports**:
- `from engine.state_machine.core import ...`
- `from engine.state_machine.event_config import ...`
- `from engine.state_machine.event_integration import ...`

**Issue**: Test file imports from engine directory, but these are actually ENTERPRISE architecture files (not legacy)  
**Risk Level**: LOW - These are valid imports from enterprise state machine  
**Resolution**: No action needed - these are false positives. The state machine is enterprise architecture and should be preserved.

### 2. Repository Factory Legacy Import
**File**: `infrastructure/persistence/repository_factory.py`  
**Legacy Import**: `from backend.engine.game import Game`  
**Risk Level**: HIGH - Infrastructure should not depend on legacy engine  
**Resolution Plan**:
1. Replace with: `from domain.entities.game import Game`
2. Update any Game-specific logic to use domain entity
3. Test repository creation with domain entities
4. Verify no functionality lost

### 3. Event Publishers Socket Manager Dependencies (2 instances)

#### WebSocket Event Publisher
**File**: `infrastructure/events/websocket_event_publisher.py`  
**Legacy Import**: `import socket_manager` or `from socket_manager import ...`  
**Risk Level**: HIGH - Critical infrastructure component using legacy code  
**Resolution Plan**:
1. Replace with clean WebSocket infrastructure
2. Use `infrastructure.websocket.connection_manager` instead
3. Update broadcast mechanism to use clean architecture
4. Test event publishing thoroughly

#### Application Event Publisher  
**File**: `infrastructure/events/application_event_publisher.py`  
**Legacy Import**: `import socket_manager` or `from socket_manager import ...`  
**Risk Level**: HIGH - Core event system using legacy broadcasting  
**Resolution Plan**:
1. Inject WebSocket publisher as dependency
2. Remove direct socket_manager usage
3. Use event-driven broadcasting instead
4. Ensure all events still reach clients

## 🔧 Resolution Strategy

### Priority Order
1. **HIGH Priority** (Week 1: July 29 - August 4)
   - Fix repository_factory.py Game import
   - Fix both event publisher socket_manager imports

2. **Validation** (Week 2: August 5 - August 9)
   - Rerun dependency analysis
   - Verify no new dependencies introduced
   - Test all affected components
   - Monitor production for issues

### Implementation Steps

#### Step 1: Fix Repository Factory
```python
# OLD (infrastructure/persistence/repository_factory.py)
from backend.engine.game import Game  # LEGACY

# NEW
from domain.entities.game import Game  # CLEAN
```

#### Step 2: Fix Event Publishers
```python
# OLD (infrastructure/events/websocket_event_publisher.py)
from socket_manager import broadcast  # LEGACY

# NEW  
from infrastructure.websocket.connection_manager import ConnectionManager
# Inject connection_manager as dependency
```

#### Step 3: Update Tests
- Add tests to prevent reintroduction of cross-dependencies
- Create architectural fitness functions
- Add to CI/CD pipeline

## 📋 Action Items

### Immediate Actions
1. [ ] Review each dependency in detail
2. [ ] Create feature branches for fixes
3. [ ] Update imports in identified files
4. [ ] Run full test suite after each change
5. [ ] Verify no functionality regression

### Testing Requirements
For each fixed dependency:
1. [ ] Unit tests pass
2. [ ] Integration tests pass
3. [ ] No new legacy imports introduced
4. [ ] Performance not degraded
5. [ ] Event flow works correctly

### Validation Commands
```bash
# After fixing, verify no cross-dependencies remain
cd backend && python tools/identify_architecture_type.py --directory . --output post_fix_analysis.json
grep -A10 "cross_dependencies" post_fix_analysis.json

# Check specific files
python tools/identify_architecture_type.py --file infrastructure/persistence/repository_factory.py --verbose
python tools/identify_architecture_type.py --file infrastructure/events/websocket_event_publisher.py --verbose
python tools/identify_architecture_type.py --file infrastructure/events/application_event_publisher.py --verbose
```

## ✅ Success Criteria

### All dependencies resolved when:
1. Architecture analysis shows 0 cross-dependencies
2. All tests continue to pass
3. No legacy imports in clean architecture files
4. Production metrics remain stable
5. Event system fully functional

### Prevention Measures
1. Add pre-commit hook to detect cross-dependencies
2. Include in CI/CD pipeline checks
3. Regular architecture analysis runs
4. Developer training on clean architecture boundaries

## 📅 Timeline

- **July 27**: Analysis complete, 6 dependencies identified
- **July 29-31**: Fix high-priority dependencies
- **August 1-4**: Testing and validation
- **August 5-7**: Final verification
- **August 8-9**: Production monitoring
- **August 10**: Final check before Phase 7 decision

## 🎯 Conclusion

The 6 cross-dependencies are manageable:
- 3 are false positives (enterprise state machine imports)
- 3 are real issues requiring code changes

With focused effort in the first week of the stability period, these can be resolved without impacting the Phase 7 timeline.

---
**Next Review**: July 29, 2025  
**Owner**: Architecture Team  
**Status**: Action Required