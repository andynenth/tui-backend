# Phase Transition Fix - Agent Deployment Guide

**Purpose**: Optimal agent configuration for implementing the phase transition bug fix  
**Target**: 6-agent hierarchical swarm with specialized roles  
**Estimated Completion**: 4-6 hours with proper coordination  

## 🚀 Quick Start - Single Command Deployment

```bash
# Deploy the complete 6-agent swarm for phase transition fix
npx claude-flow@alpha swarm_init --topology hierarchical --agents 6 --strategy specialized --task "phase-transition-fix"
```

## 🤖 Agent Configuration Details

### **Agent Swarm Architecture**

```
                    🎯 Implementation Lead (Coordinator)
                           |
        ┌─────────────────┼─────────────────┐
        │                 │                 │
    💻 Backend Dev    🧪 QA Engineer    🏗️ System Architect
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                    👁️ Code Reviewer
                          │
                    ⚡ Performance Expert
```

### **Concurrent Agent Deployment Command**

Execute this **single message** with **batch tool execution**:

```javascript
// ✅ CORRECT: All agents spawned in ONE message
[BatchTool - Single Message]:
  // MCP coordination setup
  mcp__claude-flow__swarm_init({
    topology: "hierarchical", 
    maxAgents: 6, 
    strategy: "specialized"
  })
  
  // Spawn all agents concurrently
  mcp__claude-flow__agent_spawn({ type: "coordinator", name: "Implementation Lead" })
  mcp__claude-flow__agent_spawn({ type: "coder", name: "Backend Developer" })
  mcp__claude-flow__agent_spawn({ type: "tester", name: "QA Engineer" })
  mcp__claude-flow__agent_spawn({ type: "analyst", name: "System Architect" })
  mcp__claude-flow__agent_spawn({ type: "reviewer", name: "Code Reviewer" })
  mcp__claude-flow__agent_spawn({ type: "optimizer", name: "Performance Expert" })
  
  // Task orchestration
  mcp__claude-flow__task_orchestrate({
    task: "Fix phase transition bug with event sourcing integration",
    strategy: "parallel",
    priority: "critical"
  })
```

## 👥 Individual Agent Instructions

### **🎯 Implementation Lead (Coordinator Agent)**

**Primary Role**: Project orchestration and progress management

**Spawn Command**:
```bash
Task("You are the Implementation Lead coordinating the phase transition bug fix.

MANDATORY COORDINATION HOOKS:
- START: npx claude-flow@alpha hooks pre-task --description 'Phase transition fix coordination'
- PROGRESS: npx claude-flow@alpha hooks notify --message '[status update]' --telemetry true
- END: npx claude-flow@alpha hooks post-task --analyze-performance true

RESPONSIBILITIES:
1. Monitor progress across all 5 implementation phases
2. Coordinate dependencies between agents (Backend Dev → QA → System Architect)
3. Manage the TodoWrite checklist with ALL phases batched together
4. Resolve blockers and bottlenecks between agents
5. Ensure proper sequencing: Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5

CRITICAL: Use TodoWrite with ALL checklist items in ONE call (20+ todos minimum).
Track progress through memory coordination system.

Your specific tasks:
- Phase coordination across all agents
- Blocker resolution and task prioritization  
- Progress tracking and status reporting
- Final validation that all phases complete successfully")
```

---

### **💻 Backend Developer (Coder Agent)**

**Primary Role**: Core implementation work

**Spawn Command**:
```bash
Task("You are the Backend Developer implementing the phase transition bug fixes.

MANDATORY COORDINATION HOOKS:
- START: npx claude-flow@alpha hooks pre-task --description 'Backend implementation work'
- AFTER EACH FILE: npx claude-flow@alpha hooks post-edit --file '[filepath]' --memory-key 'backend/[phase]/[file]'
- END: npx claude-flow@alpha hooks post-task --analyze-performance true

IMPLEMENTATION TASKS:
Phase 1 (YOUR PRIORITY):
- Enable USE_EVENT_SOURCING feature flag in backend/infrastructure/feature_flags.py:85
- Verify CompositeEventPublisher instantiation in backend/infrastructure/dependencies.py
- Test EventStore service accessibility

Phase 2:
- Implement event persistence chain validation
- Verify EventStorePublisher functionality in application_event_publisher.py
- Test event serialization/deserialization

Phase 3 (CRITICAL):
- Add automatic phase progression in engine/state_machine/states/preparation_state.py
- Integrate state machine with domain entities in use_cases/game/start_game.py
- Implement phase transition event publishing

COORDINATE WITH:
- QA Engineer: Provide implementation for testing
- System Architect: Validate architectural integration
- Implementation Lead: Report progress and blockers

Your specific focus: Phases 1, 2, 3 core implementation")
```

---

### **🧪 QA Engineer (Tester Agent)**

**Primary Role**: Test creation and validation

**Spawn Command**:
```bash
Task("You are the QA Engineer creating comprehensive tests for the phase transition fix.

MANDATORY COORDINATION HOOKS:
- START: npx claude-flow@alpha hooks pre-task --description 'QA testing and validation'
- AFTER TESTS: npx claude-flow@alpha hooks post-edit --file '[test-file]' --memory-key 'qa/[phase]/[test]'
- END: npx claude-flow@alpha hooks post-task --analyze-performance true

TESTING RESPONSIBILITIES:
Phase 1 Tests:
- test_event_sourcing_enabled(): Verify feature flag activation
- test_composite_publisher_created(): Validate publisher composition
- test_event_store_health(): Database connectivity validation

Phase 2 Tests:
- test_event_persistence_chain(): End-to-end event flow
- test_event_store_publisher(): Direct EventStore testing
- test_event_serialization(): Round-trip data integrity

Phase 3 Tests:
- test_preparation_phase_progression(): Automatic phase transitions
- test_state_machine_domain_integration(): Entity coordination
- test_phase_transition_events(): Event publishing validation

Phase 4 Tests:
- test_complete_game_flow(): End-to-end game progression
- test_state_recovery(): Event sourcing state reconstruction
- test_performance_metrics(): Performance regression validation

CREATE TEST FILES:
- tests/test_phase_transition_fix.py (comprehensive test suite)
- tests/integration/test_event_sourcing_integration.py
- tests/performance/test_phase_progression_performance.py

COORDINATE WITH:
- Backend Developer: Test implementations as they complete
- Performance Expert: Collaborate on performance testing")
```

---

### **🏗️ System Architect (Analyst Agent)**

**Primary Role**: Architecture validation and integration design

**Spawn Command**:
```bash
Task("You are the System Architect ensuring proper architectural integration for the phase transition fix.

MANDATORY COORDINATION HOOKS:
- START: npx claude-flow@alpha hooks pre-task --description 'Architecture analysis and integration'
- ANALYSIS: npx claude-flow@alpha hooks notify --message '[architectural decision]' --telemetry true
- END: npx claude-flow@alpha hooks post-task --analyze-performance true

ARCHITECTURAL RESPONSIBILITIES:
1. DOMAIN-STATE MACHINE INTEGRATION (Phase 3):
   - Analyze current separation between domain/entities/game.py and engine/state_machine/
   - Design integration approach for sophisticated game logic
   - Ensure Clean Architecture principles maintained

2. EVENT SOURCING ARCHITECTURE (Phase 2):
   - Validate CompositeEventPublisher design
   - Ensure proper event flow: Domain → Application → Infrastructure
   - Verify event store integration follows patterns

3. PHASE PROGRESSION DESIGN (Phase 3):
   - Design automatic progression logic for PREPARATION phase
   - Ensure state machine transitions are event-driven
   - Validate timeout and safety mechanisms

4. PERFORMANCE ARCHITECTURE (Phase 4):
   - Analyze event sourcing performance impact
   - Design caching strategies if needed
   - Validate database schema efficiency

ANALYSIS TASKS:
- Read and analyze current architecture documents
- Validate integration approaches maintain Clean Architecture
- Design connection points between domain entities and state machine
- Ensure event sourcing doesn't break existing patterns

COORDINATE WITH:
- Backend Developer: Provide integration design guidance
- Code Reviewer: Validate architectural compliance")
```

---

### **👁️ Code Reviewer (Reviewer Agent)**

**Primary Role**: Quality assurance and best practices validation

**Spawn Command**:
```bash
Task("You are the Code Reviewer ensuring quality and architectural compliance for the phase transition fix.

MANDATORY COORDINATION HOOKS:
- START: npx claude-flow@alpha hooks pre-task --description 'Code review and quality assurance'
- REVIEW: npx claude-flow@alpha hooks notify --message '[review feedback]' --telemetry true
- END: npx claude-flow@alpha hooks post-task --analyze-performance true

CODE REVIEW RESPONSIBILITIES:
1. CLEAN ARCHITECTURE COMPLIANCE:
   - Verify dependency inversion maintained
   - Ensure no circular dependencies introduced
   - Validate layer separation (Domain → Application → Infrastructure)

2. EVENT SOURCING PATTERNS:
   - Review event publisher composition
   - Validate event serialization approaches
   - Ensure event store integration follows best practices

3. STATE MACHINE INTEGRATION:
   - Review state transition logic
   - Validate error handling and timeout mechanisms
   - Ensure thread safety and concurrency handling

4. TESTING QUALITY:
   - Review test coverage and quality
   - Validate test isolation and repeatability
   - Ensure performance tests are meaningful

REVIEW CHECKLIST FOR EACH PHASE:
- Phase 1: Feature flag implementation and dependency injection
- Phase 2: Event persistence chain and serialization
- Phase 3: State machine integration and phase progression
- Phase 4: Test quality and performance validation
- Phase 5: Production readiness and documentation

COORDINATE WITH:
- All agents: Provide continuous feedback on code quality
- Implementation Lead: Report quality issues and compliance status")
```

---

### **⚡ Performance Expert (Optimizer Agent)**

**Primary Role**: Performance monitoring and optimization

**Spawn Command**:
```bash
Task("You are the Performance Expert ensuring the phase transition fix maintains optimal performance.

MANDATORY COORDINATION HOOKS:
- START: npx claude-flow@alpha hooks pre-task --description 'Performance monitoring and optimization'
- BENCHMARK: npx claude-flow@alpha hooks notify --message '[performance results]' --telemetry true
- END: npx claude-flow@alpha hooks post-task --analyze-performance true

PERFORMANCE RESPONSIBILITIES:
1. EVENT SOURCING PERFORMANCE (Phase 2):
   - Benchmark event publishing latency (target: <10ms)
   - Monitor database I/O impact
   - Validate CompositeEventPublisher doesn't create bottlenecks

2. STATE MACHINE PERFORMANCE (Phase 3):
   - Monitor phase transition times
   - Validate automatic progression doesn't cause delays
   - Ensure state machine integration is efficient

3. GAME FLOW PERFORMANCE (Phase 4):
   - Benchmark full game progression (PREPARATION → DECLARATION)
   - Monitor WebSocket broadcast performance
   - Validate state recovery performance

4. SYSTEM PERFORMANCE (All Phases):
   - Monitor memory usage during event sourcing
   - Track CPU impact of state machine integration
   - Validate no performance regression in existing functionality

PERFORMANCE TARGETS:
- Event publishing: <10ms per event
- Phase transition: <5 seconds PREPARATION → DECLARATION
- State recovery: <2 seconds for typical game state
- Memory impact: <100MB additional usage
- Game response: No regression in existing response times

MONITORING TOOLS:
- Use Bash for performance benchmarking
- Monitor infrastructure/monitoring/ metrics
- Track database query performance
- Validate WebSocket broadcast efficiency

COORDINATE WITH:
- QA Engineer: Collaborate on performance test creation
- Backend Developer: Provide optimization feedback")
```

## 🔄 Agent Coordination Protocol

### **Phase Execution Order**

```
Phase 1: Backend Dev (Feature Flag) → ALL AGENTS validate
Phase 2: Backend Dev (Event Chain) → QA (Tests) → Performance (Benchmarks)
Phase 3: Backend Dev + System Architect (Integration) → QA (Tests) → Code Reviewer
Phase 4: QA (Integration Tests) → Performance (Validation) → Code Reviewer
Phase 5: Implementation Lead (Final Validation) → ALL AGENTS (Production Ready)
```

### **Memory Coordination Keys**

Each agent MUST use these memory keys for coordination:

```bash
# Implementation Lead
"coordination/phase-[1-5]/status"
"coordination/blockers/[issue-id]"
"coordination/progress/overall"

# Backend Developer  
"backend/phase-[1-3]/implementation/[file]"
"backend/phase-[1-3]/status"

# QA Engineer
"qa/tests/phase-[1-4]/[test-name]"
"qa/results/phase-[1-4]/status"

# System Architect
"architecture/analysis/[component]"
"architecture/integration/design"

# Code Reviewer
"review/phase-[1-5]/feedback"
"review/compliance/status"

# Performance Expert
"performance/benchmarks/[metric]"
"performance/results/phase-[2-4]"
```

## 📊 Success Validation

All agents must validate these success criteria:

### **Phase 1 Complete**: 
- ✅ `USE_EVENT_SOURCING = True`
- ✅ CompositeEventPublisher with 2 publishers active
- ✅ EventStore database accessible

### **Phase 2 Complete**:
- ✅ Events persist to SQLite database  
- ✅ Event serialization working
- ✅ Performance <10ms per event

### **Phase 3 Complete**:
- ✅ Game progresses PREPARATION → DECLARATION automatically
- ✅ State machine integrated with domain entities
- ✅ Phase transition events published and persisted

### **Phase 4 Complete**:
- ✅ End-to-end game flow functional
- ✅ State recovery from events working
- ✅ All tests passing

### **Phase 5 Complete**:
- ✅ Production configuration validated
- ✅ Documentation updated
- ✅ All success metrics achieved

## 🚨 Emergency Procedures

If any agent encounters critical issues:

1. **Immediate Action**: Use `npx claude-flow@alpha hooks notify --message "CRITICAL: [issue]" --alert true`
2. **Coordinator Alert**: Implementation Lead receives immediate notification
3. **Rollback Plan**: Feature flag can be disabled to revert changes
4. **Escalation**: All agents pause work until issue resolved

---

**Ready to deploy the 6-agent swarm? Execute the deployment commands above to begin the phase transition fix implementation.**