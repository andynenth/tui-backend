# Phase 7: Legacy Code Removal - Safe Cleanup Strategy

**Document Purpose**: Comprehensive plan for safely identifying, marking, tracking, and removing legacy code after successful Phase 6 migration completion.

**Timeline**: Post Phase 6.5 completion  
**Risk Level**: Low (after full migration validation)  
**Execution Window**: 3-4 weeks (updated based on 202 legacy files)  

## Executive Summary

Phase 7 focuses on the complete and safe removal of legacy code components after the clean architecture migration has been successfully validated in production. This phase ensures a clean, maintainable codebase while preserving the ability to rollback if unexpected issues arise.

### Key Principles
- **Safety First**: Extensive validation before any permanent removal
- **Gradual Isolation**: Move to quarantine before deletion
- **Comprehensive Tracking**: Complete audit trail of all changes
- **Rollback Ready**: Maintain restoration capability throughout process
- **Zero Downtime**: No service interruption during cleanup

## Navigation
- [Phase 6 Gradual Cutover](./PHASE_6_GRADUAL_CUTOVER.md) - Prerequisites
- [Main Architecture Plan](./TASK_3_ABSTRACTION_COUPLING_PLAN.md) - Overall strategy
- [Implementation Status](./PHASE_5_IMPLEMENTATION_STATUS.md) - Component readiness
- [Legacy vs Clean Identification Guide](../implementation/guides/LEGACY_VS_CLEAN_IDENTIFICATION_GUIDE.md) - How to identify component types

## Prerequisites

### Required Completion Status
- ✅ **Phase 6.5**: Complete migration and validation finished
- ✅ **Performance Validation**: New architecture meets or exceeds legacy performance
- ✅ **Stability Period**: 2+ weeks of stable production operation
- ✅ **Test Coverage**: 100% test pass rate on new architecture
- ✅ **Monitoring**: No critical issues detected in new components

### Pre-Removal Validation Checklist
- [ ] All feature flags successfully migrated to new architecture
- [ ] Zero legacy code usage detected in monitoring
- [ ] Performance baselines maintained or improved
- [ ] Error rates within acceptable thresholds (<0.1%)
- [ ] User experience impact assessment completed
- [ ] All 6 cross-dependencies from clean to legacy resolved
- [ ] All 8 hybrid files reviewed and refactored as needed
- [ ] **NEW**: WebSocket room validation updated to use clean architecture repositories (ws.py lines 280-306)

## Current Architecture Analysis Results

Based on the automated analysis using `tools/identify_architecture_type.py` (2025-07-27):

### Distribution Summary
- **Clean Architecture**: 311 files (57.7%) - Ready for production ✅ KEEP
- **Legacy**: 202 files (37.5%) - Scheduled for removal ❌ REMOVE
- **Enterprise**: 17 files (3.2%) - Modern state machine ✅ KEEP
- **Hybrid**: 8 files (1.5%) - Need partial cleanup ⚠️ PARTIAL
- **Bridge**: 1 file (0.2%) - Adapter wrapper ✅ KEEP

### Critical Components to PRESERVE
1. **ALL Clean Architecture Files** (311 files in `application/`, `domain/`, `infrastructure/`)
2. **Enterprise State Machine** (`engine/state_machine/` - 17 files)
3. **Adapter System** (`api/adapters/` - handles WebSocket integration)
4. **WebSocket Infrastructure** (`api/routes/ws.py` - lines 1-327 only)
5. **Bridge Components** (facilitate architecture communication)

### Key Findings
- ✅ Clean architecture is handling 100% of traffic via adapters
- ⚠️ 6 clean files have legacy dependencies that need resolution
- ⚠️ 8 hybrid files need review for partial legacy code removal
- ✅ Enterprise state machine is modern and should be preserved

## Legacy Code Inventory

### Primary Legacy Components Identified

Based on the automated analysis, we have identified **202 legacy files (37.5%)** that need removal:

#### 1. Core Legacy Files
```
backend/
├── socket_manager.py              # Legacy WebSocket management
├── engine/                        # Legacy engine (except state_machine/)
│   ├── room_manager.py           # Legacy room management
│   ├── async_room_manager.py     # Legacy async room management
│   ├── room.py                   # Legacy room implementation
│   ├── async_room.py             # Legacy async room wrapper
│   ├── game.py                   # Legacy game logic
│   ├── async_game.py             # Legacy async game wrapper
│   ├── bot_manager.py            # Legacy bot management
│   ├── player.py                 # Legacy player management
│   ├── scoring.py                # Legacy scoring implementation
│   ├── rules.py                  # Legacy game rules
│   ├── ai.py                     # Legacy AI implementation
│   └── win_conditions.py         # Legacy win condition logic
└── shared_instances.py           # Legacy shared state management
```

**⚠️ CRITICAL WARNING**: The `engine/state_machine/` directory contains **17 enterprise architecture files** and should **NEVER** be removed. This is modern, production-ready code that implements:
- Game phase transitions (PREPARATION, DECLARATION, TURN, SCORING)
- Automatic event broadcasting
- State change history tracking
- JSON-safe serialization
- This is NOT legacy code - it's the enterprise architecture implementation!

#### 2. Hybrid Components (Need Partial Cleanup)
Based on analysis, **8 hybrid files (1.5%)** need review:
```
backend/api/routes/
├── ws.py                         # Hybrid - Infrastructure with legacy handlers (after line 327)
│                                 # PRIORITY FIX: Lines 280-306 use legacy room_manager
│                                 # Should use clean architecture repositories instead
├── ws_legacy_handlers.py         # Legacy handlers to be removed
└── ws_integration_patch.py       # May contain legacy integration code
```

#### 3. Legacy Test Files
Many test files contain legacy patterns or test legacy components:
```
backend/tests/
├── test_async_*.py              # Tests for legacy async wrappers
├── test_bot_manager_*.py        # Tests for legacy bot manager
├── test_engine_*.py             # Tests for legacy engine components
└── test_socket_manager.py       # Legacy socket manager tests
```

#### 4. Cross-Dependencies Warning
The automated analysis found **6 clean architecture files with legacy dependencies** that need attention:
- Clean files importing from `engine.*` or `socket_manager`
- These dependencies must be resolved before Phase 7 execution

### Replacement Mapping

| Legacy Component | Clean Architecture Replacement | Feature Flag |
|------------------|--------------------------------|-------------|
| `socket_manager.py` | `infrastructure/websocket/connection_manager.py` | `USE_LEGACY_SOCKET_MANAGER` |
| `engine/room_manager.py` | `infrastructure/repositories/optimized_room_repository.py` | `USE_LEGACY_ROOM_MANAGER` |
| `engine/game.py` | `domain/entities/game.py` + `application/services/game_application_service.py` | `USE_LEGACY_GAME_LOGIC` |
| `engine/bot_manager.py` | `infrastructure/services/simple_bot_service.py` | `USE_LEGACY_BOT_MANAGER` |
| `engine/scoring.py` | `domain/services/scoring_service.py` | `USE_LEGACY_SCORING` |

## Legacy Marking Strategy

### File-Level Marking System

#### 1. Legacy Header Template
Add to the top of each legacy file:
```python
"""
LEGACY_CODE: This file is scheduled for removal after Phase 6 migration
REPLACEMENT: {path_to_new_implementation}
REMOVAL_TARGET: Phase 7.{phase_number}
FEATURE_FLAG: {controlling_feature_flag}
DEPENDENCIES: {list_of_dependent_legacy_files}
LAST_MODIFIED: {date}
MIGRATION_STATUS: READY_FOR_REMOVAL
"""
```

#### 2. Function-Level Deprecation
For individual functions marked for removal:
```python
import warnings
from typing import Any

def legacy_function_name() -> Any:
    """
    DEPRECATED: This function will be removed in Phase 7.2
    Use: backend.application.services.new_service.new_method() instead
    Feature Flag: USE_LEGACY_FUNCTION_NAME
    """
    warnings.warn(
        f"{legacy_function_name.__name__} is deprecated and will be removed in Phase 7.2. "
        f"Use NewService.new_method() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # ... existing function implementation
```

### Central Legacy Registry

#### Legacy Registry File: `backend/legacy_registry.json`
```json
{
  "registry_version": "1.0",
  "creation_date": "2025-07-27",
  "legacy_files": [
    {
      "path": "backend/socket_manager.py",
      "replacement": "backend/infrastructure/websocket/connection_manager.py",
      "feature_flag": "USE_LEGACY_SOCKET_MANAGER",
      "removal_phase": "7.2",
      "dependencies": ["shared_instances.py"],
      "lines_of_code": 1000,
      "last_modified": "2025-07-15",
      "migration_status": "ready_for_removal",
      "risk_level": "medium"
    },
    {
      "path": "backend/engine/room_manager.py", 
      "replacement": "backend/infrastructure/repositories/optimized_room_repository.py",
      "feature_flag": "USE_LEGACY_ROOM_MANAGER",
      "removal_phase": "7.2",
      "dependencies": ["engine/room.py", "socket_manager.py"],
      "lines_of_code": 500,
      "last_modified": "2025-07-10",
      "migration_status": "ready_for_removal", 
      "risk_level": "low"
    }
  ],
  "removal_stats": {
    "total_legacy_files": 202,
    "total_lines_to_remove": 15000,
    "hybrid_files_to_review": 8,
    "clean_files_with_legacy_deps": 6,
    "estimated_cleanup_time": "3-4 weeks"
  }
}
```

## Safe Removal Process

### Phase 7.0: Priority WebSocket Fix (Immediate)

#### Step 7.0.1: Update ws.py to Use Clean Architecture
**Objective**: Fix the room validation issue by using clean architecture repositories

**Actions**:
1. Replace legacy `room_manager.get_room()` with clean architecture repository call
2. Update imports to use clean architecture dependencies
3. Remove the "Room not found" warning that occurs when rooms exist only in clean architecture
4. Test WebSocket connections to ensure they find rooms created in clean architecture

**Code Changes Required**:
- Replace lines 280-306 in `backend/api/routes/ws.py`
- Import `get_unit_of_work` from `infrastructure.dependencies`
- Use `uow.rooms.get_by_id(room_id)` instead of `room_manager.get_room(room_id)`

**Frontend Integration Validation Checklist**:
- [ ] **Lobby Events Work Correctly**:
  - [ ] `room_created` event sent when room created (frontend expects: `{room_id, host_name, ...}`)
  - [ ] `room_list_update` event sent with room list (frontend expects: `{rooms: [...]}`)
  - [ ] `room_joined` event sent when joining room (frontend navigates to room page)
  - [ ] `error` event sent on failures (frontend shows error message)
- [ ] **Room Events Function Properly**:
  - [ ] `room_update` event sent when room state changes (frontend updates player list)
  - [ ] `game_started` event sent when game begins (frontend navigates to game page)
  - [ ] `room_closed` event sent when room closes (frontend returns to lobby)
  - [ ] `room_not_found` event NOT sent for valid rooms in clean architecture
- [ ] **Connection Flow Remains Intact**:
  - [ ] Frontend can connect to `/ws/lobby` for lobby operations
  - [ ] Frontend can connect to `/ws/{room_id}` for room operations
  - [ ] WebSocket registration/unregistration still works
  - [ ] Heartbeat/ping-pong mechanism continues functioning

### Phase 7.1: Legacy Code Audit and Marking (Week 1)

#### Step 7.1.1: Comprehensive Legacy Scan
**Objective**: Identify all remaining legacy code components

**Actions**:
1. Run automated legacy code scanner
2. Create complete inventory of legacy files
3. Map dependencies between legacy components
4. Identify any missed legacy code patterns

**Tools to Create**:
```bash
# backend/tools/legacy_scanner.py
python tools/legacy_scanner.py --scan-all --output legacy_inventory.json
# Scans entire codebase for legacy patterns and dependencies
```

**Available Tools**:
```bash
# backend/tools/identify_architecture_type.py - Already implemented!
python tools/identify_architecture_type.py --directory backend --output architecture_analysis.json
# Analyzes and classifies all files as legacy, clean, hybrid, or bridge

# Check a specific file
python tools/identify_architecture_type.py --file path/to/file.py --verbose

# Current statistics: 202 legacy files (37.5%), 311 clean files (57.7%), 8 hybrid files (1.5%)
```

**Validation**:
- Complete legacy file inventory created
- All dependencies mapped accurately
- No legacy code usage detected in new architecture

#### Step 7.1.2: Legacy Registry Creation
**Objective**: Create central tracking system for legacy removal

**Actions**:
1. Generate `legacy_registry.json` from scan results
2. Add header markers to all legacy files
3. Create removal timeline and phasing plan
4. Set up legacy usage monitoring

**Validation**:
- All legacy files properly marked
- Registry accurately reflects current state
- Monitoring detects any legacy usage

#### Step 7.1.3: Dependency Analysis
**Objective**: Understand legacy code interconnections

**Actions**:
1. Create dependency graph of legacy components
2. Identify removal order based on dependencies
3. Plan for handling circular dependencies
4. Validate new architecture doesn't depend on legacy

**Tools to Create**:
```bash
# backend/tools/dependency_analyzer.py
python tools/dependency_analyzer.py --generate-graph --output legacy_deps.svg
```

### Phase 7.2: Legacy Code Isolation (Week 2)

#### Step 7.2.1: Create Legacy Quarantine Directory
**Objective**: Isolate legacy code before removal

**Actions**:
1. Create `backend/legacy/` directory structure
2. Move legacy files to quarantine directory
3. Update imports to use quarantine paths
4. Validate system still functions correctly

**Directory Structure**:
```
backend/
├── legacy/                    # NEW: Legacy quarantine area
│   ├── README.md             # Documentation of quarantined code
│   ├── engine/               # Moved legacy engine components
│   ├── socket_manager.py     # Moved legacy socket manager
│   ├── shared_instances.py   # Moved legacy shared state
│   └── tests/                # Moved legacy-specific tests
```

#### Step 7.2.2: Update Import Paths
**Objective**: Redirect any remaining legacy imports to quarantine

**Actions**:
1. Update imports to use `backend.legacy.` paths
2. Add import guards to detect legacy usage
3. Test all functionality after import updates
4. Monitor for any broken imports

**Import Guard Example**:
```python
# In files that might still import legacy code
try:
    from backend.legacy.socket_manager import SocketManager
    import warnings
    warnings.warn(
        "Using quarantined legacy code. This will be removed soon.",
        PendingDeprecationWarning
    )
except ImportError:
    # Legacy code no longer available - system should use new implementation
    raise ImportError("Legacy SocketManager has been removed. Use new WebSocket infrastructure.")
```

#### Step 7.2.3: Quarantine Validation
**Objective**: Ensure quarantine doesn't break system functionality

**Testing Protocol**:
```bash
# Run full test suite with quarantined code
python -m pytest tests/ --legacy-quarantined -v
# Test system startup and basic functionality  
python test_quarantine_validation.py
# Monitor for any performance impact
python benchmark_post_quarantine.py
```

**Frontend Functionality Validation Checklist**:
- [ ] **WebSocket Connection Tests**:
  - [ ] Frontend can connect to `/ws/lobby` without errors
  - [ ] Frontend can connect to `/ws/{room_id}` without errors
  - [ ] No import errors in server logs during connection
  - [ ] WebSocket handshake completes successfully
- [ ] **End-to-End Flow Tests**:
  - [ ] Player can enter name and reach lobby
  - [ ] Player can create room and receive `room_created` event
  - [ ] Player can see room list via `room_list_update` event
  - [ ] Player can join room and receive `room_joined` event
  - [ ] Players see each other via `room_update` events
  - [ ] Host can start game and all players receive `game_started`
  - [ ] Game phases work correctly (preparation, declaration, turn, scoring)
  - [ ] Players can leave room and others receive updates
- [ ] **Error Handling Tests**:
  - [ ] Invalid room ID shows appropriate error message
  - [ ] Full room prevents joining with clear message
  - [ ] Network disconnection is handled gracefully
  - [ ] Reconnection works without breaking game state

### Phase 7.3: Final Validation and Safety Checks (Week 3)

#### Step 7.3.1: Legacy Usage Detection
**Objective**: Confirm no active legacy code usage

**Actions**:
1. Run comprehensive legacy usage scan
2. Monitor production logs for legacy warnings
3. Analyze performance metrics for any impact
4. Confirm all feature flags point to new architecture

**Tools to Create**:
```bash
# backend/tools/legacy_usage_detector.py
python tools/legacy_usage_detector.py --production-scan --duration 72h
```

#### Step 7.3.2: Pre-Removal Safety Validation
**Objective**: Final safety checks before permanent removal

**Validation Checklist**:
- [ ] No legacy code imports detected in active codebase
- [ ] All legacy feature flags disabled and pointing to new architecture
- [ ] Performance metrics equal or better than legacy baseline
- [ ] Error rates within acceptable thresholds
- [ ] Full test suite passes without legacy code
- [ ] Production monitoring shows stable operation

#### Step 7.3.3: Rollback Procedure Testing
**Objective**: Ensure rollback capability before permanent removal

**Actions**:
1. Test complete rollback procedure from quarantine
2. Validate rollback completes within target timeframe (<5 minutes)
3. Test partial rollback of individual components
4. Document any rollback issues discovered

### Phase 7.4: Complete Removal and Cleanup

#### Step 7.4.1: Permanent Legacy Code Removal
**Objective**: Remove quarantined legacy code permanently

**Actions**:
1. Create backup of quarantined code (archived)
2. Remove `backend/legacy/` directory completely
3. Clean up legacy-related feature flags
4. Remove legacy-specific dependencies

**Safety Protocol**:
```bash
# Create final backup before removal
tar -czf legacy_code_backup_$(date +%Y%m%d).tar.gz backend/legacy/
# Move backup to secure archive location
mv legacy_code_backup_*.tar.gz /secure/archive/legacy_backups/
# Remove legacy directory
rm -rf backend/legacy/
```

#### Step 7.4.2: Final Cleanup and Optimization
**Objective**: Clean up remaining legacy artifacts

**Actions**:
1. Remove unused imports and dependencies
2. Clean up legacy-related configuration
3. Update documentation to remove legacy references
4. Optimize new architecture performance

#### Step 7.4.3: Post-Removal Validation
**Objective**: Confirm successful cleanup

**Final Validation**:
```bash
# Verify no legacy imports remain
python tools/scan_legacy_imports.py --strict
# Confirm all tests pass
python -m pytest tests/ --no-legacy -v
# Performance validation
python benchmark_clean_architecture.py
# Production health check
curl /api/health/post-cleanup-validation
```

**Complete Frontend Integration Validation**:
- [ ] **All WebSocket Events Function Correctly**:
  - [ ] Lobby events: `room_created`, `room_list_update`, `room_joined`, `error`
  - [ ] Room events: `room_update`, `game_started`, `room_closed`
  - [ ] Game events: All phase transitions work correctly
  - [ ] Connection events: `connected`, `disconnected`, `reconnected`
- [ ] **Full Game Flow Works End-to-End**:
  - [ ] Players can create and join rooms
  - [ ] Room state synchronizes across all players
  - [ ] Game can be started by host
  - [ ] All game phases execute correctly
  - [ ] Scoring and winner determination work
  - [ ] Players can start new rounds
  - [ ] Players can leave and rejoin gracefully
- [ ] **Performance Meets Requirements**:
  - [ ] WebSocket latency < 100ms for local connections
  - [ ] Room creation/join < 500ms
  - [ ] Game state updates propagate < 200ms
  - [ ] No memory leaks after extended play
- [ ] **Error Recovery Works**:
  - [ ] Disconnection/reconnection preserves game state
  - [ ] Invalid actions show appropriate errors
  - [ ] System recovers from transient failures
  - [ ] No orphaned rooms or ghost players

## Automation Tools

### Tool 1: Legacy Code Scanner
**File**: `backend/tools/legacy_scanner.py`

**Purpose**: Identify all legacy code components and their dependencies

**Features**:
- Scans for legacy file patterns
- Identifies legacy imports and dependencies
- Generates comprehensive inventory
- Creates removal timeline suggestions

### Tool 2: Legacy Usage Monitor
**File**: `backend/tools/legacy_monitor.py`

**Purpose**: Monitor active usage of legacy code components

**Features**:
- Real-time monitoring of legacy code usage
- Integration with application logging
- Alerts when legacy code is accessed
- Usage statistics and reporting

### Tool 3: Safe Removal Validator
**File**: `backend/tools/removal_validator.py`

**Purpose**: Validate safety of removing specific legacy components

**Features**:
- Dependency analysis before removal
- Import impact assessment
- Test suite validation
- Performance impact prediction

### Tool 4: Rollback Manager
**File**: `backend/tools/rollback_manager.py`

**Purpose**: Manage rollback procedures for legacy code restoration

**Features**:
- Automated rollback execution
- Partial component restoration
- Rollback validation testing
- Rollback timing measurement

## Rollback and Recovery Procedures

### Emergency Rollback (Critical Issues)
```bash
# Immediate legacy restoration
python tools/rollback_manager.py --emergency --component all
# Restore from backup
tar -xzf /secure/archive/legacy_backups/legacy_code_backup_YYYYMMDD.tar.gz
# Re-enable legacy feature flags
export ENABLE_ALL_LEGACY_FLAGS=true
# Restart services
systemctl restart liap-backend
```

### Partial Rollback (Specific Component)
```bash
# Restore specific legacy component
python tools/rollback_manager.py --component socket_manager
# Re-enable specific feature flag
export USE_LEGACY_SOCKET_MANAGER=true
# Restart affected services only
systemctl restart liap-websocket-service
```

### Rollback Validation
After any rollback:
1. Health check: `curl /api/health/rollback-validation`
2. Functionality test: `python test_rollback_functionality.py`
3. Performance check: `python benchmark_rollback_performance.py`
4. Monitor for 30 minutes for stability

## Success Criteria

### Technical Success Metrics
- ✅ Zero legacy imports in active codebase
- ✅ All legacy feature flags removed
- ✅ Performance equal or better than pre-removal baseline
- ✅ Test coverage maintained at >95%
- ✅ Error rates remain <0.1%

### Cleanup Success Metrics
- ✅ Codebase size reduced by estimated 15,000+ lines (202 legacy files)
- ✅ Maintainability improved (37.5% reduction in codebase complexity)
- ✅ Build time improved or maintained
- ✅ Memory usage optimized
- ✅ Documentation updated and accurate

### Operational Success Metrics
- ✅ Zero downtime during removal process
- ✅ No user-facing functionality lost
- ✅ Support team requires no additional training
- ✅ System reliability maintained or improved

## Risk Mitigation

### Identified Risks and Mitigations

#### 1. Undiscovered Legacy Dependencies
**Risk**: Some legacy code usage not detected during scanning
**Mitigation**: 
- Multiple scanning tools and manual review
- Extended monitoring period before removal
- Staged removal with validation at each step

#### 2. Performance Regression After Removal
**Risk**: Unexpected performance impact from legacy removal
**Mitigation**:
- Comprehensive performance testing before removal
- Real-time monitoring during removal
- Immediate rollback capability

#### 3. Hidden Integration Points
**Risk**: Legacy code integrated in unexpected ways
**Mitigation**:
- Thorough dependency analysis
- Extended testing period in quarantine
- Gradual removal with validation

#### 4. Data Migration Issues
**Risk**: Legacy data formats not properly migrated
**Mitigation**:
- Data format validation before removal
- Migration testing with production data copies
- Backup and restoration procedures

## Documentation Updates

### During Legacy Removal
- Update all architectural documentation
- Remove legacy references from API documentation
- Update deployment and operational procedures
- Create legacy removal timeline documentation

### Post-Removal Documentation
- **Final Architecture Documentation**: Clean architecture only
- **Migration Lessons Learned**: Document the complete migration experience
- **Operational Procedures**: Updated for new architecture
- **Troubleshooting Guides**: Remove legacy troubleshooting steps

## Timeline and Milestones

### Immediate: Phase 7.0 (Priority WebSocket Fix)
- **Day 1**: Update ws.py to use clean architecture repositories
- **Day 1**: Test and validate WebSocket functionality

### Week 1: Phase 7.1 (Audit and Marking)
- **Days 1-2**: Legacy code scanning and inventory
- **Days 3-4**: Registry creation and file marking
- **Days 5-7**: Dependency analysis and validation

### Week 2: Phase 7.2 (Isolation)
- **Days 1-3**: Quarantine directory creation and file movement
- **Days 4-5**: Import path updates and testing
- **Days 6-7**: Quarantine validation and monitoring

### Week 3: Phase 7.3 (Final Validation)
- **Days 1-3**: Legacy usage detection and analysis
- **Days 4-5**: Pre-removal safety validation
- **Days 6-7**: Rollback procedure testing

### Week 4: Phase 7.4 (Removal and Cleanup)
- **Days 1-2**: Permanent legacy code removal
- **Days 3-4**: Final cleanup and optimization
- **Days 5-7**: Post-removal validation and monitoring

## Monitoring and Metrics

### Key Metrics to Track
- **Legacy Code Usage**: Real-time monitoring of any legacy access
- **Performance Impact**: Before/after performance comparison
- **Error Rates**: Monitor for any increase in errors
- **System Stability**: Overall system health metrics
- **User Experience**: End-user impact assessment

### Alerting Rules
- Alert if any legacy code accessed unexpectedly
- Alert if performance degrades >10% during removal
- Alert if error rates increase >0.05%
- Alert if system health checks fail

## Next Steps After Phase 7

### Immediate (Post-Removal)
1. **System Optimization**: Optimize new architecture performance
2. **Documentation Finalization**: Complete all documentation updates
3. **Team Training**: Train team on clean architecture maintenance
4. **Monitoring Enhancement**: Improve monitoring and alerting

### Medium Term (1-3 months)
1. **Performance Tuning**: Fine-tune new architecture performance
2. **Feature Enhancement**: Add new features using clean architecture
3. **Scalability Testing**: Test system scalability improvements
4. **Code Quality Metrics**: Establish ongoing quality monitoring

### Long Term (3+ months)
1. **Architecture Evolution**: Plan next architectural improvements
2. **Technology Upgrades**: Leverage clean architecture for upgrades
3. **Team Expansion**: Use clean architecture for easier onboarding
4. **System Growth**: Scale system using clean architecture patterns

---

## Final System Architecture After Phase 7

After successful completion of Phase 7, the system will have:

### What Remains (✅ KEEP)
1. **Clean Architecture Components** (311 files):
   - `domain/` - Entities, value objects, and domain events
   - `application/` - Use cases, DTOs, and interfaces
   - `infrastructure/` - Repositories, services, and external integrations

2. **Enterprise State Machine** (17 files in `engine/state_machine/`):
   - Modern game phase management
   - Automatic event broadcasting
   - State change history

3. **WebSocket Infrastructure**:
   - `api/routes/ws.py` (cleaned up, lines 1-327)
   - `api/adapters/` - All adapter files for WebSocket integration
   - Connection management and message routing

4. **Frontend** (unchanged):
   - All React components and pages
   - WebSocket event handlers
   - Game UI and state management

### What Gets Removed (❌ DELETE)
1. **Legacy Engine Files** (202 files):
   - Old room/game management
   - Legacy async wrappers
   - Old scoring and rules
   - Legacy bot management

2. **Legacy Infrastructure**:
   - `socket_manager.py`
   - `shared_instances.py`
   - Legacy test files

### Frontend Functionality Guarantee
The frontend will continue to work exactly as before because:
1. All WebSocket events remain the same (`room_created`, `room_update`, etc.)
2. Message formats are preserved by the adapter layer
3. Game flow and phases remain identical
4. Error handling and recovery mechanisms are maintained

## Conclusion

Phase 7 provides a comprehensive, safe approach to removing legacy code after successful migration to clean architecture. The emphasis on safety, validation, and rollback capability ensures that legacy code removal enhances rather than risks the system's stability and maintainability.

**Key Success Factors**:
- Thorough planning and inventory before removal
- Gradual isolation and validation at each step
- Comprehensive tooling for automation and safety
- Continuous monitoring and immediate rollback capability
- Complete documentation and team communication
- Frontend functionality preserved throughout

**Ready for Execution**: After Phase 6.5 completion and production validation period.

---
**Last Updated**: 2025-07-28  
**Document Version**: 1.2  
**Changes in v1.2**:
- Added Phase 7.0 for immediate WebSocket fix (user chose Option 2)
- Updated ws.py priority fix to use clean architecture repositories
- Removed dependency on legacy repository bridge pattern
- Added specific line numbers for ws.py changes (lines 280-306)

**Changes in v1.1**: 
- Updated legacy file count from 12 to 202 based on automated analysis
- Added current architecture distribution statistics
- Identified 6 cross-dependencies and 8 hybrid files needing attention
- Updated timeline from 2-3 weeks to 3-4 weeks
- Added reference to `tools/identify_architecture_type.py` tool

**Execution Trigger**: Phase 6.5 successful completion + 2 weeks stable operation