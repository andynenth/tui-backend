# Undocumented Features and Files List

## Last Updated: 2025-09-02

This document lists specific features, files, and components that currently lack teaching documentation.

## 1. AI System Components

### Core AI Files
- `backend/ai_debug_simple.py` - AI debugging framework
- `backend/services/ai_logger.py` - AI decision logging service
- `backend/services/ai_bug_detector.py` - Automatic bug detection
- `backend/tools/benchmark_ai_debug.py` - AI performance benchmarking

### AI Testing Infrastructure
- `tests/ai_regression/` - Entire regression test suite
  - `ai_decision_framework.py` - Test framework for AI decisions
  - `run_all_regression_tests.py` - Regression test runner
  - `test_never_win_combo.py` - Specific bug regression tests
  - Multiple other regression test files

### AI Analysis Documentation (Not in Teaching Materials)
- `docs/analysis/AI_DECLARATION_ANALYSIS.md`
- `docs/analysis/AI_COMPREHENSIVE_ANALYSIS_REPORT.md`
- `docs/ai-development/` - Various AI development docs

## 2. Monitoring and Observability

### Monitoring Services
- `backend/services/monitoring_service.py` - Metrics collection
- `backend/services/alert_service.py` - Alert management
- `backend/api/services/health_monitor.py` - Health monitoring

### Monitoring Endpoints
- `/api/metrics` - General metrics endpoint
- `/api/metrics/play-history` - Play history specific metrics
- `/api/health/performance` - Performance health checks
- `/api/alerts` - Alert management

### Monitoring Routes
- `backend/api/routes/monitoring.py` - All monitoring endpoints

## 3. Player Activity Monitoring

### Core Implementation
- Player activity tracking in `backend/socket_manager.py`
- Idle detection and bot takeover logic
- Grace period handling for disconnections

### Documentation (Exists but not in Teaching Materials)
- `docs/PLAYER_ACTIVITY_MONITOR.md`
- `PLAYER_ACTIVITY_MONITOR_PROGRESS.md`
- `PLAYER_ACTIVITY_MONITOR_TEST_REPORT.md`

## 4. Testing Infrastructure

### Testing Utilities
- `test_player_activity_monitor.py` - Activity monitor tests
- `test_enterprise_architecture.py` - Enterprise pattern validation
- `test_turn_number_sync.py` - Sync bug prevention tests

### Testing Documentation (Not in Teaching Materials)
- `docs/testing/` - Entire testing documentation directory
  - `refresh-bug/` - Reconnection bug documentation
  - `guides/ai_websocket_testing_guide.md`
  - Various test reports

## 5. Logging and Analysis Tools

### Game Analysis
- `backend/docs/GAME_LOG_STRUCTURE.md` - Log format documentation
- `backend/docs/AI_LOGGING_AND_ANALYSIS_PLAN.md` - Logging strategy
- `backend/docs/AI_DATA_AVAILABILITY_SUMMARY.md` - Data availability

### Performance Analysis
- Play history performance monitoring
- Response time tracking and alerting
- Cache performance metrics

## 6. Bug Fix Documentation (Not in Teaching Materials)

### AI Bug Fixes
- `docs/ai-development/FIX_HISTORY.md` - AI fix history
- `docs/ai-development/AI_BUG_FIX_CHECKLIST.md` - Fix process
- Various bug analysis documents

### Reconnection Bug Fixes
- `docs/testing/refresh-bug/05_reconnection_fix_summary.md`
- Multiple test reports and fix documentation

## 7. Operational Tools

### Debug Endpoints
- `/api/debug/room-stats` - Room statistics
- Event store recovery endpoints
- System stats endpoints

### Production Tools
- Docker health checks
- AWS ECS integration points
- Load balancer health endpoints

## 8. Code Quality Tools

### Quality Tracking
- `CODE_QUALITY_CHECKLIST.md` - Quality checklist
- `CODE_QUALITY_TRACKING_GUIDE.md` - Tracking guide
- Various analysis reports

## Summary Statistics

- **Undocumented Services**: 8+ new services
- **Undocumented Endpoints**: 10+ new API endpoints
- **Undocumented Test Suites**: 15+ test files
- **Existing Docs Not in Teaching Materials**: 20+ documents

## Recommendations

1. **Highest Priority**: AI debugging and testing infrastructure (most complex, most used)
2. **High Priority**: Monitoring and observability (critical for production)
3. **Medium Priority**: Consolidate existing documentation into teaching materials
4. **Low Priority**: Operational tools and quality tracking

## Notes

- Many features have partial documentation but aren't integrated into the teaching materials
- The AI system has evolved significantly with bug fixes and improvements
- Monitoring is a completely new system added after the initial documentation
- Testing infrastructure has grown substantially with regression suites