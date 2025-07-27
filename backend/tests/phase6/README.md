# Phase 6: Gradual Cutover - Test Organization

This directory contains all test files related to Phase 6 of the clean architecture migration. The tests are organized by migration step to make it easy to understand what each test validates and how to run tests for specific migration components.

## Directory Structure

```
tests/phase6/
├── migration_tools/           # Main migration testing tools
│   ├── step_6_4_1/           # State Machine Migration (Phase 6.4.1)
│   ├── step_6_4_2/           # Bot Management Migration (Phase 6.4.2)  
│   ├── step_6_4_3/           # Scoring System Migration (Phase 6.4.3)
│   ├── step_6_5_1/           # End-to-End Integration (Phase 6.5.1)
│   ├── step_6_5_2/           # Load Testing & Performance (Phase 6.5.2)
│   └── step_6_5_3/           # Legacy Removal & Final Validation (Phase 6.5.3)
├── infrastructure/           # Infrastructure and monitoring tests
├── reports/                  # Generated test reports and results
└── utilities/                # Supporting utilities and validation scripts
```

## Migration Test Categories

### 🏗️ Business Logic Migration (Phase 6.4)

#### Step 6.4.1: State Machine Migration
- **Location**: `migration_tools/step_6_4_1/`
- **Purpose**: Validates enterprise state machine with automatic broadcasting
- **Key Tests**:
  - `test_state_machine_enterprise.py` - Enterprise features validation
  - `test_state_machine_integration.py` - Integration with clean architecture
- **Validation**: Grade A - All phase transitions, broadcasting, change history

#### Step 6.4.2: Bot Management Migration  
- **Location**: `migration_tools/step_6_4_2/`
- **Purpose**: Validates new bot service implementation with precision timing
- **Key Tests**:
  - `test_bot_management_migration.py` - Bot service migration validation
  - `test_bot_timing_accuracy.py` - Precision timing within 100ms tolerance
  - `test_bot_management_integration.py` - Integration with game systems
- **Validation**: Grade A - Timing accuracy, decision quality, replacement functionality

#### Step 6.4.3: Scoring System Migration
- **Location**: `migration_tools/step_6_4_3/`
- **Purpose**: Validates clean architecture scoring with mathematical accuracy
- **Key Tests**:
  - `test_scoring_system_migration.py` - Scoring system validation
  - `test_scoring_integration.py` - Integration with application layer
- **Validation**: Grade A - 100% mathematical accuracy, 100K calculations/second

### 🔗 Integration and Finalization (Phase 6.5)

#### Step 6.5.1: End-to-End Integration Testing
- **Location**: `migration_tools/step_6_5_1/`
- **Purpose**: Comprehensive testing with all components integrated
- **Key Tests**:
  - `test_complete_integration.py` - Complete game flows with all migrated components
- **Validation**: Grade A - Full integration, error handling, system performance

#### Step 6.5.2: Load Testing and Performance Validation
- **Location**: `migration_tools/step_6_5_2/`
- **Purpose**: Stress test with realistic production loads
- **Key Tests**:
  - `run_load_tests.py` - Comprehensive load and stress testing
  - `performance/test_repository_performance.py` - Repository benchmarks
  - `performance/test_cache_performance.py` - Cache performance validation
  - `performance/test_event_throughput.py` - Event store throughput testing
- **Validation**: Grade A - 150+ concurrent games, graceful degradation

#### Step 6.5.3: Legacy System Removal
- **Location**: `migration_tools/step_6_5_3/`
- **Purpose**: Final validation and regression testing before legacy removal
- **Key Tests**:
  - `run_regression_tests.py` - Comprehensive regression testing
  - `final_performance_validation.py` - Final performance validation
- **Validation**: Grade A - 0 regressions, performance equal or better

## Infrastructure and Monitoring

### Infrastructure Tests
- **Location**: `infrastructure/`
- **Purpose**: Core infrastructure component validation
- **Key Tests**:
  - `test_websocket_integration.py` - WebSocket connection management
  - `monitoring/test_migration_alerts.py` - Migration alert testing
  - `monitoring/validate_monitoring_coverage.py` - Monitoring coverage validation

## Test Reports

### Generated Reports
- **Location**: `reports/`
- **Content**: JSON reports from all Phase 6 migration tests
- **Key Reports**:
  - `state_machine_enterprise_report.json` - State machine validation results
  - `bot_timing_accuracy_report.json` - Bot timing precision results
  - `scoring_system_migration_report.json` - Scoring accuracy validation
  - `complete_integration_report.json` - End-to-end integration results
  - `load_test_report.json` - Load testing and stress test results
  - `regression_test_report.json` - Regression testing results
  - `final_performance_validation_report.json` - Final validation results

## Utilities

### Supporting Tools
- **Location**: `utilities/`
- **Purpose**: Validation scripts and performance baselines
- **Key Utilities**:
  - `capture_performance_baseline.py` - Performance baseline capture
  - `validate_repository_data.py` - Repository data validation

## Running Tests

### Individual Migration Steps

```bash
# Phase 6.4.1: State Machine Migration
cd tests/phase6/migration_tools/step_6_4_1
python test_state_machine_enterprise.py
pytest test_state_machine_integration.py -v

# Phase 6.4.2: Bot Management Migration  
cd tests/phase6/migration_tools/step_6_4_2
python test_bot_management_migration.py
python test_bot_timing_accuracy.py

# Phase 6.4.3: Scoring System Migration
cd tests/phase6/migration_tools/step_6_4_3
python test_scoring_system_migration.py

# Phase 6.5.1: End-to-End Integration
cd tests/phase6/migration_tools/step_6_5_1
python test_complete_integration.py

# Phase 6.5.2: Load Testing
cd tests/phase6/migration_tools/step_6_5_2
python run_load_tests.py --concurrent-games=50 --stress-test

# Phase 6.5.3: Final Validation
cd tests/phase6/migration_tools/step_6_5_3
python run_regression_tests.py
python final_performance_validation.py
```

### Performance Testing

```bash
# Repository performance
cd tests/phase6/migration_tools/step_6_5_2/performance
python test_repository_performance.py

# Cache performance  
python test_cache_performance.py

# Event store throughput
python test_event_throughput.py
```

### Utilities and Validation

```bash
# Capture performance baseline
cd tests/phase6/utilities
python capture_performance_baseline.py

# Validate repository data
python validate_repository_data.py

# Monitor migration alerts
cd tests/phase6/infrastructure/monitoring
python test_migration_alerts.py
```

## Test Results and Grades

All Phase 6 migration tests achieved **Grade A** validation:

| Migration Step | Test Grade | Key Achievement |
|----------------|------------|----------------|
| 6.4.1 State Machine | A | Enterprise features, automatic broadcasting |
| 6.4.2 Bot Management | A | Precision timing within 100ms tolerance |
| 6.4.3 Scoring System | A | 100% mathematical accuracy |
| 6.5.1 Integration | A | Complete system integration |
| 6.5.2 Load Testing | A | 150+ concurrent games supported |
| 6.5.3 Final Validation | A | 0 regressions, all requirements met |

## Integration with CI/CD

These tests can be integrated into continuous integration pipelines:

```bash
# Quick validation suite
pytest tests/phase6/migration_tools/*/test_*_integration.py -v

# Full migration validation
python tests/phase6/migration_tools/step_6_5_3/run_regression_tests.py

# Performance benchmarks
python tests/phase6/migration_tools/step_6_5_2/run_load_tests.py --benchmark
```

## Troubleshooting

### Common Issues

1. **Import Path Errors**: Ensure you're running tests from the correct directory
2. **Missing Dependencies**: All tests require the clean architecture to be enabled
3. **Performance Variations**: Performance tests may vary by system - check baseline metrics

### Getting Help

- Check test reports in `reports/` for detailed validation results
- Review Phase 6 documentation: `docs/task3-abstraction-coupling/planning/PHASE_6_GRADUAL_CUTOVER.md`
- Migration completion report: `PHASE_6_COMPLETION_REPORT.md`

---

**Migration Status**: ✅ COMPLETE  
**Test Organization**: ✅ COMPLETE  
**All Phase 6 Tests**: ✅ Grade A Validation  