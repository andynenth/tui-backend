# Backend Documentation Structure

All markdown documentation files have been organized into the following structure:

## Documentation Organization

### Architecture Documentation
All architecture-related documentation is located under `docs/architecture/clean-migration/`:

#### Status Documents (`docs/architecture/clean-migration/status/`)
- `ARCHITECTURE_MIGRATION_STATUS.md` - Overall migration status tracking
- `CLEAN_ARCHITECTURE_FINAL_STATE.md` - Target architecture state
- `CURRENT_ARCHITECTURE_STATE.md` - Current state of the architecture
- `DOCUMENTATION_UPDATE_SUMMARY.md` - Summary of documentation updates
- `REVIEW_STATUS.md` - Code review status
- `TASK_3_DOCS_MOVED.md` - Task 3 documentation migration notes
- `WEBSOCKET_DOCS_REORGANIZATION_SUMMARY.md` - WebSocket docs reorganization

#### Reference Documents (`docs/architecture/clean-migration/reference/`)
- `ARCHITECTURE_VERIFICATION_GUIDE.md` - Guide for verifying architecture
- `ASYNC_PATTERNS_GUIDE.md` - Async/await patterns and best practices
- `CIRCULAR_IMPORT_CLEANUP_PLAN.md` - Plan for resolving circular imports
- `MODULE_ARCHITECTURE_ANALYSIS.md` - Analysis of module architecture
- `PHASE_IMPLEMENTATION_ROADMAP.md` - Roadmap for phase implementations
- `broadcast_adapter_migration_summary.md` - Broadcast adapter migration details
- `domain-model-reference.md` - Domain model reference guide

#### Phase 6 Documents (`docs/architecture/clean-migration/phase-6/`)
- `PHASE_4_COMPLETE_SUMMARY.md` - Phase 4 completion summary
- `PHASE_6_COMPLETION_REPORT.md` - Phase 6 completion report
- Plus subdirectories for:
  - `audits/` - Architecture audits
  - `fixes/` - Applied fixes
  - `patterns/` - Pattern implementations

#### Phase 7 Reports (`docs/architecture/clean-migration/phase-7/reports/`)
- `PHASE_7_FINAL_COMPLETION_REPORT.md` - Final Phase 7 report
- `PHASE_7_POST_REMOVAL_FIXES.md` - Post-removal fixes
- `phase7_1_validation.md` - Phase 7.1 validation
- `phase7_2_*.md` - Various Phase 7.2 documents
- `phase7_3_*.md` - Phase 7.3 validation documents
- `phase7_completion_report.md` - Overall Phase 7 completion
- `phase7_progress_summary.md` - Phase 7 progress tracking

### WebSocket Documentation
WebSocket-specific documentation is located under `docs/websocket/`:

#### Integration Fix Documentation (`docs/websocket/integration-fix/`)
- `INTEGRATION_FIX_PLAN.md` - Master plan for WebSocket fixes
- `PROJECT_COMPLETE_SUMMARY.md` - Project completion summary
- `PHASE_4_COMPLETION_REPORT.md` - Phase 4 completion details
- Subdirectories for each phase:
  - `phase-1/` - Immediate fixes
  - `phase-2/` - Infrastructure decoupling
  - `phase-3/` - Adapter removal

### Other Documentation Locations

#### Task 3 Documentation (`docs/task3-abstraction-coupling/`)
- Implementation guides
- Progress tracking
- Technical references
- Planning documents

#### Adapter Documentation (`docs/adapters/`)
- Adapter analysis
- Migration guides
- Cost/benefit analysis

#### Testing Documentation (`docs/testing/`)
- `PHASE_4_9_VALIDATION_SUMMARY.md` - Phase 4.9 validation summary
- `PHASE_TEST_GUIDE.md` - Guide for phase testing
- `ROUND_START_TEST_SUMMARY.md` - Round start test summary

## Quick Navigation

- **Current Architecture State**: `docs/architecture/clean-migration/status/CURRENT_ARCHITECTURE_STATE.md`
- **WebSocket Integration**: `docs/websocket/integration-fix/PROJECT_COMPLETE_SUMMARY.md`
- **Phase 7 Completion**: `docs/architecture/clean-migration/phase-7/reports/PHASE_7_FINAL_COMPLETION_REPORT.md`
- **Architecture Guide**: `docs/ARCHITECTURE_GUIDE.md`

## Note
All documentation has been organized to maintain a clean backend root directory while providing logical grouping of related documents. The structure follows the project's phase-based development approach and separates concerns between architecture migration, WebSocket integration, and task-specific documentation.