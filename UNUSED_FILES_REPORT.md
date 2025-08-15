# Unused Files Report - Liap Tui Project

Generated on: August 15, 2025

## Executive Summary

This report identifies unused files in both backend and frontend codebases. Files are categorized by type and risk level for deletion.

## Backend Unused Files

### 🔴 **High Priority - Safe to Delete** (11 files)

#### Migration/Example Scripts (2 files)
- `backend/api/websocket/migration_example.py` - Example migration script
- `backend/async_migration_example.py` - Async migration example

#### Shadow Mode Files (2 files - deprecated feature)
- `backend/api/shadow_mode_integration.py` - Shadow mode integration
- `backend/api/shadow_mode_manager.py` - Shadow mode manager

#### Standalone Tools/Scripts (3 files)
- `backend/benchmark_async.py` - Async benchmark utility
- `backend/capture_from_live_server.py` - Live server capture tool
- `backend/start_golden_master_capture.py` - Golden master capture starter

#### Deprecated Code (1 file)
- `backend/engine/ai_simplified.py` - Simplified AI (replaced by `ai.py`)

#### Unused Features (3 files)
- `backend/api/models/request_models.py` - Unused request models
- `backend/api/websocket/state_sync.py` - Unused WebSocket state sync
- `backend/services/play_history_simple.py` - Simplified play history (replaced by `play_history_db.py`)

### 🟡 **Medium Priority - Review Before Deleting** (1 file)
- `backend/utils/error_handling.py` - Unused error handling utilities (might be for future use)

### 🟢 **Keep - Required Files**
- All `__init__.py` files (required for Python package structure)
- All test files in `backend/tests/` (15 files - part of test suite)
- `backend/api/shadow_mode.py` (still imported somewhere)

## Frontend Unused Files

### 🔴 **High Priority - Safe to Delete** (19 files)

#### Unused Components (13 files)
1. `frontend/src/components/EnhancedPlayerAvatar.jsx` - Duplicate of PlayerAvatar
2. `frontend/src/components/EnhancedToastContainer.jsx` - Duplicate of ToastContainer
3. `frontend/src/components/GameWithDisconnectHandling.jsx` - Unused wrapper component
4. `frontend/src/components/Input.jsx` - Exported but never imported
5. `frontend/src/components/Layout.jsx` - Exported but never imported
6. `frontend/src/components/LazyRoute.jsx` - Exported but never imported
7. `frontend/src/components/Modal.jsx` - Exported but never imported
8. `frontend/src/components/PlayerSlot.jsx` - Exported but never imported
9. `frontend/src/components/ReconnectionProgress.jsx` - Never imported
10. `frontend/src/components/game/index.js` - Empty export file
11. `frontend/src/components/game/shared/FooterTimer.jsx` - Never imported
12. `frontend/src/components/game/shared/PieceTray.jsx` - Never imported
13. `frontend/src/components/game/shared/PlayerAvatarTest.jsx` - Test component

#### Unused Utilities (1 file)
- `frontend/src/utils/roomHelpers.js` - Never imported

#### Unused Services (2 files)
- `frontend/src/services/ErrorHandlingService.ts` - Never imported
- `frontend/src/services/types.ts` - Never imported

#### Coverage Files (3 files)
- `frontend/coverage/lcov-report/block-navigation.js`
- `frontend/coverage/lcov-report/prettify.js`
- `frontend/coverage/lcov-report/sorter.js`

### 🟢 **Keep - Required Files**
- All test files (*.test.js/jsx/ts) - 7 files
- Mock files in `__mocks__` directories
- Configuration files (jest.config.js, postcss.config.js, etc.)

## Documentation & Configuration Files

### 🔴 **Potentially Outdated Documentation**
Many documentation files may be outdated or redundant:
- Multiple deployment guides in `docs/deployment/`
- Several AI development planning documents that may be completed
- Various analysis and investigation documents

### 🟡 **Review Needed**
- `backend/` contains several markdown files that might be better moved to `docs/`
- Some configuration files might be redundant (e.g., multiple docker-compose files)

## Summary Statistics

- **Backend**: 11 files safe to delete, 1 needs review
- **Frontend**: 19 files safe to delete
- **Total files safe to delete**: 30 files
- **Total test files (keep)**: 22 files
- **Documentation files needing review**: ~50+ files

## Recommended Actions

1. **Immediate**: Delete all files marked as "High Priority - Safe to Delete"
2. **Review**: Examine "Medium Priority" files with team before deletion
3. **Documentation Cleanup**: Organize and consolidate documentation files
4. **Test Suite**: Keep all test files but ensure they're still relevant
5. **Configuration**: Review and consolidate configuration files

## Commands to Clean Up

```bash
# Backend cleanup (review each file before deleting)
rm backend/api/websocket/migration_example.py
rm backend/async_migration_example.py
rm backend/api/shadow_mode_integration.py
rm backend/api/shadow_mode_manager.py
rm backend/benchmark_async.py
rm backend/capture_from_live_server.py
rm backend/start_golden_master_capture.py
rm backend/engine/ai_simplified.py
rm backend/api/models/request_models.py
rm backend/api/websocket/state_sync.py
rm backend/services/play_history_simple.py

# Frontend cleanup
rm frontend/src/components/EnhancedPlayerAvatar.jsx
rm frontend/src/components/EnhancedToastContainer.jsx
rm frontend/src/components/GameWithDisconnectHandling.jsx
rm frontend/src/components/Input.jsx
rm frontend/src/components/Layout.jsx
rm frontend/src/components/LazyRoute.jsx
rm frontend/src/components/Modal.jsx
rm frontend/src/components/PlayerSlot.jsx
rm frontend/src/components/ReconnectionProgress.jsx
rm frontend/src/components/game/index.js
rm frontend/src/components/game/shared/FooterTimer.jsx
rm frontend/src/components/game/shared/PieceTray.jsx
rm frontend/src/components/game/shared/PlayerAvatarTest.jsx
rm frontend/src/utils/roomHelpers.js
rm frontend/src/services/ErrorHandlingService.ts
rm frontend/src/services/types.ts
rm -rf frontend/coverage/lcov-report/
```

## Notes

- This analysis was performed using static import analysis
- Some files might be dynamically imported or used in ways not detected
- Always backup before deleting files
- Consider using version control to track deletions