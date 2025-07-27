# Phase 6: Gradual Cutover - Progressive Migration Plan

**Document Purpose**: Comprehensive step-by-step migration plan from legacy system to clean architecture using isolated, test-driven integration.

**Timeline**: 5 weeks  
**Risk Level**: Low (due to progressive approach)  
**Rollback Time**: < 2 minutes per component  

## Executive Summary

Phase 6 implements the final migration from the legacy WebSocket-based architecture to the clean architecture using a methodical, component-by-component approach. Each integration step is isolated, thoroughly tested, and validated before proceeding to the next component.

### Key Principles
- **One Component at a Time**: Single-focus integration steps
- **Test-First Validation**: Immediate testing after each integration
- **Progressive Gates**: No advancement without validation
- **Instant Rollback**: Feature flags enable immediate reversion
- **Zero Downtime**: Seamless transition for users

## Navigation
- [Phase 5 Implementation Status](./PHASE_5_IMPLEMENTATION_STATUS.md) - Prerequisites
- [Phase 5 Test Coverage Report](../status/PHASE_5_TEST_COVERAGE_REPORT.md) - Testing readiness
- [Main Architecture Plan](./TASK_3_ABSTRACTION_COUPLING_PLAN.md) - Overall strategy

## Prerequisites (Phase 6.0)

### Critical Blockers to Resolve First

#### 6.0.1: Infrastructure Test Suite Repair
**Status**: 🚨 **BLOCKING** - Must be completed before any migration
- **Issue**: Phase 5 infrastructure tests cannot execute due to import/dependency issues
- **Impact**: Cannot validate infrastructure components before migration
- **Required Actions**:
  1. Fix import errors in all 13 infrastructure test files
  2. Resolve MRO (Method Resolution Order) conflicts
  3. Complete missing domain object implementations
  4. Validate all performance benchmarks

**Success Criteria**:
- ✅ All 13 infrastructure test files execute successfully
- ✅ Test coverage >90% on all components
- ✅ Performance benchmarks meet targets (<0.1ms lookups, >80% cache hit rates)

#### 6.0.2: Component Readiness Validation
**Status**: ⚠️ **NEEDS VERIFICATION**
- **Phase 1**: ✅ Complete - 22 API adapters operational
- **Phase 2**: ✅ Complete - Event system implemented
- **Phase 3**: ✅ Complete - Domain layer with entities
- **Phase 4**: ✅ Complete - Application layer and use cases
- **Phase 5**: ✅ Complete - Infrastructure layer (tests blocked)

**Required Actions**:
1. Verify each phase component is functional
2. Test integration points between phases
3. Confirm feature flags are operational
4. Validate monitoring and observability

#### 6.0.3: Production Environment Preparation
**Required Infrastructure**:
- Monitoring dashboards operational
- Alerting rules configured and tested
- Feature flag system enabled
- Rollback procedures documented and tested
- Performance baselines established

## Migration Phases

### Phase 6.1: Foundation Layer Migration (Week 1)

#### Step 6.1.1: Feature Flags System Migration
**Objective**: Enable clean architecture feature flags with rollback capability

**Pre-Integration Checklist**:
- [ ] Feature flag infrastructure tested
- [ ] Rollback procedures verified
- [ ] Monitoring alerts configured

**Integration Actions**:
1. Enable feature flag system in production
2. Configure percentage-based rollout controls
3. Test flag toggling functionality
4. Verify instant rollback capability

**Testing Protocol**:
```bash
# Test feature flag functionality
python -m pytest tests/infrastructure/test_feature_flags.py -v
# Validate rollback speed
python test_rollback_timing.py
# Monitor flag state changes
curl /api/health/feature-flags
```

**Validation Gates**:
- ✅ Feature flags respond within 10ms
- ✅ Rollback completes within 30 seconds
- ✅ All flag states logged correctly
- ✅ No errors in monitoring systems

**Rollback Procedure**:
```bash
# Immediate rollback if issues
export ENABLE_CLEAN_ARCHITECTURE=false
systemctl restart liap-backend
```

#### Step 6.1.2: Logging and Observability Migration
**Objective**: Cut over to new logging infrastructure with correlation tracking

**Pre-Integration Checklist**:
- [ ] Log aggregation system ready
- [ ] Correlation ID generation tested
- [ ] Log shipping configured

**Integration Actions**:
1. Enable new logging infrastructure
2. Configure structured logging with correlation IDs
3. Switch log shipping to centralized service
4. Test log aggregation and search

**Testing Protocol**:
```bash
# Test structured logging
python -m pytest tests/infrastructure/test_observability.py -v
# Validate correlation ID propagation
python test_correlation_tracking.py
# Check log aggregation
curl /api/health/logging
```

**Validation Gates**:
- ✅ All logs include correlation IDs
- ✅ Log aggregation working correctly
- ✅ Search and filtering functional
- ✅ Performance impact <5ms per request

#### Step 6.1.3: Health Check Migration
**Objective**: Switch to new health check endpoints with dependency monitoring

**Pre-Integration Checklist**:
- [ ] Health check endpoints tested
- [ ] Dependency monitoring configured
- [ ] Alerting thresholds set

**Integration Actions**:
1. Enable new health check system
2. Configure dependency health monitoring
3. Update load balancer health checks
4. Test alerting functionality

**Testing Protocol**:
```bash
# Test health endpoints
curl /health/ready && curl /health/live
# Validate dependency checks
python -m pytest tests/infrastructure/test_health.py -v
# Test alerting
python simulate_dependency_failure.py
```

**Validation Gates**:
- ✅ Health checks respond within 100ms
- ✅ Dependency monitoring accurate
- ✅ Alerting triggers correctly
- ✅ Load balancer integration working

### Phase 6.2: Core Infrastructure Migration (Week 2)

#### Step 6.2.1: In-Memory Repository Migration
**Objective**: Switch to optimized repository implementations

**Pre-Integration Checklist**:
- [ ] Repository performance benchmarked
- [ ] Memory usage monitoring enabled
- [ ] Data migration scripts ready

**Integration Actions**:
1. Enable optimized repository implementations
2. Migrate existing data to new repositories
3. Monitor memory usage and performance
4. Validate data consistency

**Testing Protocol**:
```bash
# Performance benchmarks
python -m pytest tests/infrastructure/test_optimized_repositories.py -v
# Memory usage validation
python test_memory_monitoring.py
# Data consistency checks
python validate_repository_data.py
```

**Validation Gates**:
- ✅ Lookup performance <0.1ms (99th percentile)
- ✅ Memory usage within configured limits
- ✅ Data consistency 100% validated
- ✅ No memory leaks detected

#### Step 6.2.2: Caching Layer Migration
**Objective**: Enable new cache infrastructure with eviction policies

**Pre-Integration Checklist**:
- [ ] Cache backends configured
- [ ] Eviction policies tested
- [ ] Cache warming scripts ready

**Integration Actions**:
1. Enable new caching infrastructure
2. Warm cache with frequently accessed data
3. Monitor cache hit rates and performance
4. Test cache invalidation

**Testing Protocol**:
```bash
# Cache functionality tests
python -m pytest tests/infrastructure/test_caching.py -v
# Performance validation
python test_cache_performance.py
# Hit rate monitoring
curl /api/health/cache-metrics
```

**Validation Gates**:
- ✅ Cache hit rate >80%
- ✅ Response time <1ms for cache hits
- ✅ Eviction policies working correctly
- ✅ Cache invalidation accurate

#### Step 6.2.3: Event Store Migration
**Objective**: Switch to hybrid event persistence with archival

**Pre-Integration Checklist**:
- [ ] Event store performance tested
- [ ] Archival strategy configured
- [ ] Event replay validated

**Integration Actions**:
1. Enable hybrid event store
2. Start event persistence for new events
3. Configure automatic archival
4. Test event replay functionality

**Testing Protocol**:
```bash
# Event store tests
python -m pytest tests/infrastructure/test_event_store.py -v
# Performance validation
python test_event_throughput.py
# Replay functionality
python test_event_replay.py
```

**Validation Gates**:
- ✅ Event throughput >10,000 events/second
- ✅ Event replay accuracy 100%
- ✅ Archival process working
- ✅ No event loss detected

### Phase 6.3: Application Layer Migration (Week 3)

#### Step 6.3.1: Connection Management Migration
**Objective**: Cut over WebSocket connection handling to clean architecture

**Pre-Integration Checklist**:
- [ ] WebSocket infrastructure tested
- [ ] Connection pooling configured
- [ ] Reconnection logic validated

**Integration Actions**:
1. Enable new WebSocket connection manager
2. Migrate existing connections gradually
3. Monitor connection stability
4. Test reconnection scenarios

**Testing Protocol**:
```bash
# WebSocket integration tests
python -m pytest tests/infrastructure/test_websocket_integration.py -v
# Connection stability test
python test_connection_stability.py
# Reconnection testing
python test_reconnection_scenarios.py
```

**Validation Gates**:
- ✅ No connection drops during migration
- ✅ Reconnection success rate >99%
- ✅ Connection latency unchanged
- ✅ Memory usage stable

#### Step 6.3.2: Room Management Migration
**Objective**: Switch room operations to clean architecture

**Pre-Integration Checklist**:
- [ ] Room management adapters tested
- [ ] State synchronization validated
- [ ] Performance benchmarked

**Integration Actions**:
1. Enable clean architecture room operations
2. Migrate room state to new format
3. Test all room operations (create, join, leave)
4. Validate state consistency

**Testing Protocol**:
```bash
# Room management tests
python -m pytest tests/integration/test_room_operations.py -v
# State consistency validation
python test_room_state_sync.py
# Performance benchmarks
python benchmark_room_operations.py
```

**Validation Gates**:
- ✅ All room operations working correctly
- ✅ State consistency maintained
- ✅ Performance equal or better than legacy
- ✅ No data corruption

#### Step 6.3.3: Game Actions Migration
**Objective**: Enable clean architecture game logic

**Pre-Integration Checklist**:
- [ ] Game action handlers tested
- [ ] State machine integration validated
- [ ] Business rules verified

**Integration Actions**:
1. Enable clean architecture game actions
2. Test all game operations (declare, play, redeal)
3. Validate business rule enforcement
4. Monitor game state accuracy

**Testing Protocol**:
```bash
# Game action tests
python -m pytest tests/integration/test_game_actions.py -v
# Business rule validation
python test_game_rules_enforcement.py
# End-to-end game flow
python test_complete_game_flow.py
```

**Validation Gates**:
- ✅ All game actions working correctly
- ✅ Business rules enforced accurately
- ✅ Game state transitions valid
- ✅ No gameplay disruption

### Phase 6.4: Business Logic Migration (Week 4)

#### Step 6.4.1: State Machine Migration
**Objective**: Cut over to clean architecture state machine with enterprise features

**Pre-Integration Checklist**:
- [ ] State machine enterprise features tested
- [ ] Phase transitions validated
- [ ] Broadcasting system verified

**Integration Actions**:
1. Enable clean architecture state machine
2. Migrate existing game states
3. Test all phase transitions
4. Validate enterprise broadcasting

**Testing Protocol**:
```bash
# State machine tests
python -m pytest tests/test_enterprise_architecture.py -v
# Phase transition testing
python test_all_phase_transitions.py
# Broadcasting validation
python test_enterprise_broadcasting.py
```

**Validation Gates**:
- ✅ All phase transitions working
- ✅ Enterprise broadcasting functional
- ✅ Change history accurate
- ✅ Performance maintained

#### Step 6.4.2: Bot Management Migration
**Objective**: Switch to new bot service implementation

**Pre-Integration Checklist**:
- [ ] Bot service implementation tested
- [ ] Bot timing validated
- [ ] Decision algorithms verified

**Integration Actions**:
1. Enable new bot management service
2. Test bot decision making
3. Validate bot timing (0.5-1.5s delays)
4. Test bot replacement functionality

**Testing Protocol**:
```bash
# Bot management tests
python -m pytest tests/test_bot_manager.py -v
# Bot timing validation
python test_bot_timing_accuracy.py
# Decision algorithm testing
python test_bot_decision_quality.py
```

**Validation Gates**:
- ✅ Bot behavior matches legacy exactly
- ✅ Timing accuracy within 100ms
- ✅ Decision quality maintained
- ✅ Replacement functionality working

#### Step 6.4.3: Scoring System Migration
**Objective**: Enable clean architecture scoring with mathematical accuracy

**Pre-Integration Checklist**:
- [ ] Scoring algorithms tested
- [ ] Mathematical accuracy verified
- [ ] Win condition logic validated

**Integration Actions**:
1. Enable clean architecture scoring
2. Test all scoring scenarios
3. Validate mathematical accuracy
4. Test win condition detection

**Testing Protocol**:
```bash
# Scoring system tests
python -m pytest tests/test_scoring_accuracy.py -v
# Mathematical validation
python test_scoring_edge_cases.py
# Win condition testing
python test_win_condition_detection.py
```

**Validation Gates**:
- ✅ Scoring 100% mathematically accurate
- ✅ All edge cases handled correctly
- ✅ Win conditions detected properly
- ✅ Performance maintained

### Phase 6.5: Integration and Finalization (Week 5)

#### Step 6.5.1: End-to-End Integration Testing
**Objective**: Comprehensive testing with all components integrated

**Integration Actions**:
1. Run complete game flows with all components
2. Test concurrent game scenarios
3. Validate system-wide performance
4. Test error handling and recovery

**Testing Protocol**:
```bash
# End-to-end integration tests
python -m pytest tests/test_complete_integration.py -v
# Concurrent game testing
python test_concurrent_games.py
# System performance validation
python benchmark_full_system.py
```

**Validation Gates**:
- ✅ Complete games run successfully
- ✅ Concurrent games handled correctly
- ✅ System performance meets targets
- ✅ Error recovery working

#### Step 6.5.2: Load Testing and Performance Validation
**Objective**: Stress test with realistic production loads

**Integration Actions**:
1. Execute load testing scenarios
2. Monitor system behavior under stress
3. Validate performance benchmarks
4. Test system limits and recovery

**Testing Protocol**:
```bash
# Load testing
python run_load_tests.py --concurrent-games=100
# Stress testing
python stress_test_system.py --peak-load
# Performance validation
python validate_performance_benchmarks.py
```

**Validation Gates**:
- ✅ System handles expected load
- ✅ Performance degrades gracefully
- ✅ Recovery after overload working
- ✅ No data corruption under stress

#### Step 6.5.3: Legacy System Removal
**Objective**: Clean removal of legacy code paths

**Integration Actions**:
1. Disable all legacy feature flags
2. Remove legacy code paths
3. Clean up unused dependencies
4. Update documentation

**Testing Protocol**:
```bash
# Final validation tests
python -m pytest tests/ -v --legacy-disabled
# Regression testing
python run_regression_tests.py
# Performance final check
python final_performance_validation.py
```

**Validation Gates**:
- ✅ No functionality regression
- ✅ Performance equal or better
- ✅ Clean codebase
- ✅ Documentation updated

## Rollback Procedures

### Immediate Rollback (Emergency)
```bash
# Emergency rollback to legacy system
export ENABLE_CLEAN_ARCHITECTURE=false
export ROLLBACK_REASON="emergency"
systemctl restart liap-backend
# Verify rollback successful
curl /api/health/architecture-status
```

### Component-Specific Rollback
For each component, specific rollback flags are available:
```bash
# Repository rollback
export USE_OPTIMIZED_REPOSITORIES=false
# Cache rollback  
export USE_NEW_CACHE=false
# Event store rollback
export USE_HYBRID_EVENT_STORE=false
# State machine rollback
export USE_CLEAN_STATE_MACHINE=false
```

### Rollback Validation
After any rollback:
1. Run health checks: `curl /api/health/detailed`
2. Test core functionality
3. Monitor for 10 minutes
4. Confirm user impact resolved

## Monitoring and Alerting

### Key Metrics to Monitor
- **Response Time**: <50ms (99th percentile)
- **Error Rate**: <0.1%
- **Memory Usage**: Within configured limits
- **Cache Hit Rate**: >80%
- **Connection Stability**: >99% uptime

### Critical Alerts
- Performance degradation >20%
- Error rate >0.5%
- Memory usage >90%
- Connection failures >1%
- Cache hit rate <70%

### Monitoring Dashboard
Real-time dashboard available at: `/admin/migration-dashboard`
- Component status indicators
- Performance metrics
- Error tracking
- Migration progress

## Success Criteria

### Technical Criteria
- ✅ Zero downtime during migration
- ✅ No functionality regression
- ✅ Performance equal or better than legacy
- ✅ All tests passing
- ✅ Error rate <0.1%

### Business Criteria
- ✅ User experience unchanged
- ✅ Game accuracy maintained
- ✅ System reliability improved
- ✅ Maintainability enhanced

## Risk Mitigation

### High Risk Scenarios
1. **Database corruption**: Automatic backups before each step
2. **Performance degradation**: Continuous monitoring with auto-rollback
3. **Connection instability**: Gradual migration with fallback
4. **State inconsistency**: Validation checks at each step

### Mitigation Strategies
- Comprehensive testing at each step
- Immediate rollback capability
- Real-time monitoring and alerting
- Progressive traffic routing
- Automated validation checks

## Documentation Updates

### During Migration
- Update operational runbooks
- Document any issues encountered
- Track performance baselines
- Record lessons learned

### Post-Migration
- Archive legacy documentation
- Update system architecture docs
- Create new operational procedures
- Document migration lessons learned

---

## Next Steps

1. **Immediate**: Fix Phase 5 infrastructure test execution issues
2. **Week 1**: Execute Phase 6.0 (Prerequisites) and 6.1 (Foundation)
3. **Week 2**: Execute Phase 6.2 (Core Infrastructure)
4. **Week 3**: Execute Phase 6.3 (Application Layer)
5. **Week 4**: Execute Phase 6.4 (Business Logic)
6. **Week 5**: Execute Phase 6.5 (Integration & Finalization)

**Status**: Ready for execution pending infrastructure test fixes

---
**Last Updated**: 2025-07-27  
**Document Version**: 1.0  
**Next Review**: Weekly during migration