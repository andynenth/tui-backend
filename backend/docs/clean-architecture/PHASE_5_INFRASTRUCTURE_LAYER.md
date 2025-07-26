# Phase 5: Infrastructure Layer Implementation Plan

## 1. Phase Overview

### Role of the Infrastructure Layer

The Infrastructure Layer serves as the foundation of our clean architecture, providing concrete implementations of interfaces defined in the Application Layer while managing all cross-cutting concerns. This layer handles:

- External system integrations (databases, message queues, external APIs)
- Framework-specific implementations (WebSocket handlers, HTTP middleware)
- System observability (logging, metrics, monitoring)
- Resource management (connection pooling, caching, rate limiting)
- Technical policies (retry logic, circuit breakers, timeouts)

### Why This Is the Most Complex Phase

Phase 5 represents the culmination of our architectural transformation, requiring:

1. **Multiple Integration Points**: Connecting to WebSockets, databases, event stores, and monitoring systems
2. **Cross-Cutting Concerns**: Implementing aspects that affect all layers without violating boundaries
3. **Performance Optimization**: Ensuring the clean architecture doesn't introduce latency
4. **Backward Compatibility**: Maintaining exact behavior for the existing frontend
5. **Production Readiness**: Adding enterprise features deferred from earlier phases

### Architectural Boundaries

The Infrastructure Layer must respect these boundaries:
- **Depends on**: Application and Domain layers (implements their interfaces)
- **Does not depend on**: Presentation layer or frontend
- **Provides to Application Layer**: Concrete implementations of repositories, event publishers, and external services
- **Isolated from Domain**: Domain entities never reference infrastructure code

## 2. Scope

### What Will Be Included

#### Core Infrastructure Components
1. **Repository Implementations**
   - Database-backed repositories (PostgreSQL/SQLite)
   - Caching layer for frequently accessed data
   - Transaction management and connection pooling

2. **Event Infrastructure**
   - Event Store implementation with persistence
   - Event replay and recovery mechanisms
   - Dead letter queue handling

3. **WebSocket Infrastructure**
   - Connection management and pooling
   - Message serialization/deserialization
   - Reconnection handling infrastructure

4. **Middleware Pipeline**
   - Request/response interceptors
   - Error handling middleware
   - Correlation ID tracking

#### Group 2 Infrastructure Features (from Phase 4.11)
1. **Rate Limiting**
   - Per-player rate limits
   - Per-room rate limits
   - WebSocket message throttling
   - Configurable limits with Redis backend

2. **Event Store & Recovery**
   - Persistent event storage
   - Event sourcing capabilities
   - Point-in-time recovery
   - Event replay mechanisms

3. **Health Monitoring**
   - Health check endpoints
   - Dependency health verification
   - Readiness and liveness probes
   - Circuit breaker status

4. **Logging Service**
   - Structured logging implementation
   - Log aggregation setup
   - Correlation ID propagation
   - Performance logging

5. **Metrics Collection**
   - Prometheus metrics integration
   - Custom game metrics
   - Performance counters
   - Resource utilization tracking

6. **Middleware Pipeline**
   - Authentication middleware
   - Authorization policies
   - Request validation
   - Response transformation

### What Will Not Be Included

1. **Frontend Changes**: No modifications to the existing frontend
2. **API Contract Changes**: All endpoints maintain current behavior
3. **New Features**: Only infrastructure supporting existing features
4. **External Service Integrations**: No new third-party services beyond monitoring

## 3. System Integration

### Application Layer Integration
- **Repository Interfaces**: Provide concrete implementations for all repository interfaces
- **Service Interfaces**: Implement external service adapters (EventPublisher, MetricsCollector)
- **Unit of Work**: Database transaction management implementation
- **Query Services**: Optimized read models for complex queries

### Domain Layer Integration
- **Event Handlers**: Subscribe to domain events and persist them
- **Entity Hydration**: Reconstruct domain entities from persistence
- **Value Object Serialization**: Handle complex type conversions

### WebSocket Communication Layer
- **Message Routing**: Direct WebSocket messages to appropriate use cases
- **Broadcasting Infrastructure**: Efficient room-based message distribution
- **Connection State Management**: Track and manage WebSocket lifecycle
- **Message Queue Integration**: Buffer messages for disconnected players

### State Machine Integration
- **State Persistence**: Save state machine snapshots
- **State Recovery**: Restore state from persistence
- **Event Replay**: Reconstruct state from event history
- **Concurrent Access Control**: Prevent state conflicts

### System Integration Checklist

#### State Machine Structure Analysis
- [ ] Map all state classes (PreparationState, DeclarationState, TurnState, ScoringState) and their transitions
- [ ] Document the `_valid_transitions` map from GameStateMachine for reference
- [ ] Identify all ActionType enum values and which states handle them
- [ ] Analyze the polling-based transition checker (0.5s interval) and its implications
- [ ] Document the state machine lifecycle from WAITING to GAME_OVER

#### WebSocket Layer Integration
- [ ] Create infrastructure adapter for converting WebSocket messages to GameAction objects
- [ ] Implement WebSocketActionQueue that wraps the state machine's action queue
- [ ] Build WebSocketBroadcaster that implements the automatic broadcasting contract
- [ ] Map all WebSocket event types to corresponding ActionType enum values
- [ ] Implement connection tracking for state machine broadcast targets
- [ ] Create WebSocket reconnection handler that restores state machine context
- [ ] Add WebSocket message validation before action queue submission

#### Domain Event Integration
- [ ] Implement EventStoreStateChangePublisher that persists all state changes
- [ ] Create DomainEventToStateTransition mapper for event-driven transitions
- [ ] Build StateChangeEventListener that subscribes to enterprise architecture events
- [ ] Wire PhaseChanged, TurnStarted, and ScoresCalculated events to infrastructure
- [ ] Implement event replay mechanism for state machine recovery
- [ ] Create event compaction strategy for phase_data change history
- [ ] Add event versioning support for state machine evolution

#### Persistence Infrastructure
- [ ] Implement StateSnapshotRepository for saving complete state machine state
- [ ] Create PhaseDataPersistence adapter for the enterprise architecture
- [ ] Build ActionHistoryRepository for storing all GameActions with timestamps
- [ ] Implement ChangeHistoryPersistence for the built-in change tracking
- [ ] Create atomic save operation for state + events + action queue
- [ ] Add optimistic locking for concurrent state modifications
- [ ] Implement state machine recovery from latest snapshot + events

#### Application Layer Bridges
- [ ] Create StateMachineUseCase base class for use cases that trigger state changes
- [ ] Implement StateMachineQueryService for read-only state access
- [ ] Build BotManagerNotificationAdapter for phase transition notifications
- [ ] Create RoomLifecycleAdapter to manage state machine creation/destruction
- [ ] Implement ActionValidationService that delegates to current state
- [ ] Add StateMachineMetricsCollector for performance monitoring
- [ ] Create StateMachineHealthCheck for monitoring processing loop

#### Message Queue Integration
- [ ] Implement PersistentActionQueue that backs the in-memory queue
- [ ] Create ActionQueueReplayService for crash recovery
- [ ] Build MessageQueueStateMachineAdapter for disconnected player actions
- [ ] Implement priority queue for critical state machine actions
- [ ] Add dead letter queue for failed action processing
- [ ] Create action deduplication mechanism for idempotency
- [ ] Implement queue overflow handling with backpressure

#### Concurrency and Access Control
- [ ] Implement distributed lock for state machine access (Redis-based)
- [ ] Create RoomLockManager that coordinates with state machine locks
- [ ] Build optimistic concurrency control for phase_data updates
- [ ] Implement action queue serialization for concurrent submissions
- [ ] Add transaction boundaries for state + event + broadcast operations
- [ ] Create conflict resolution strategy for simultaneous transitions
- [ ] Implement state machine pause/resume for maintenance

#### Monitoring and Observability
- [ ] Add OpenTelemetry spans for each state transition
- [ ] Implement state duration metrics (time spent in each phase)
- [ ] Create action processing latency metrics
- [ ] Add broadcast success/failure tracking
- [ ] Implement state machine event stream for debugging
- [ ] Create correlation ID propagation through state transitions
- [ ] Add state machine visualization endpoint for monitoring

#### Recovery and Resilience
- [ ] Implement state machine crash recovery from event store
- [ ] Create point-in-time recovery using snapshots + event replay
- [ ] Build state validation service to detect corruption
- [ ] Implement automatic state repair from event history
- [ ] Add circuit breaker for broadcast failures
- [ ] Create fallback mechanism for action processing failures
- [ ] Implement state machine migration for version upgrades

#### Testing Infrastructure
- [ ] Create StateMachineTestHarness for integration testing
- [ ] Implement deterministic action replay for debugging
- [ ] Build state transition fuzzer for edge case discovery
- [ ] Create load testing framework for concurrent actions
- [ ] Implement chaos testing for infrastructure failures
- [ ] Add state machine regression test suite
- [ ] Create performance benchmarking for state operations

## 4. Interaction Contracts

### Adapter Pattern
All infrastructure components will use the Adapter pattern to implement application interfaces:

```python
# Application Interface
class EventPublisher(ABC):
    async def publish(self, event: DomainEvent) -> None: ...

# Infrastructure Implementation
class WebSocketEventPublisher(EventPublisher):
    async def publish(self, event: DomainEvent) -> None:
        # Convert to WebSocket message
        # Broadcast to appropriate rooms
```

### Repository Pattern
Repositories will provide both synchronous and asynchronous operations:

```python
class SqlGameRepository(GameRepository):
    async def get_by_id(self, game_id: str) -> Optional[Game]:
        # SQL query with connection pooling
        # Entity hydration
        # Cache management
```

### Event Sourcing Pattern
Event store will support replay and projection:

```python
class EventStore:
    async def append(self, stream_id: str, events: List[Event]) -> None
    async def get_events(self, stream_id: str, from_version: int) -> List[Event]
    async def get_snapshot(self, stream_id: str) -> Optional[Snapshot]
```

### Middleware Stack Pattern
Request processing pipeline with composable middleware:

```python
class MiddlewarePipeline:
    def use(self, middleware: Middleware) -> None
    async def execute(self, context: RequestContext) -> Response
```

## 5. Risks and Design Considerations

### Failure Points
1. **Database Connection Loss**
   - Risk: Game state corruption
   - Mitigation: Implement connection retry with exponential backoff
   - Fallback: In-memory cache for critical operations

2. **Event Store Overflow**
   - Risk: Memory exhaustion from event accumulation
   - Mitigation: Implement event compaction and archiving
   - Monitoring: Alert on event count thresholds

3. **WebSocket Broadcast Storms**
   - Risk: Server overload from mass disconnections
   - Mitigation: Rate limit broadcasts, implement backpressure
   - Recovery: Gradual reconnection with jitter

4. **Cache Inconsistency**
   - Risk: Stale data serving
   - Mitigation: Cache invalidation on writes, TTL policies
   - Verification: Cache hit/miss metrics

### Observability Strategy
1. **Distributed Tracing**: OpenTelemetry integration
2. **Structured Logging**: JSON logs with correlation IDs
3. **Metrics Dashboard**: Grafana for real-time monitoring
4. **Error Tracking**: Sentry integration for production

### Performance Considerations
1. **Connection Pooling**: Prevent connection exhaustion
2. **Batch Operations**: Reduce database round trips
3. **Async I/O**: Non-blocking operations throughout
4. **Caching Strategy**: Multi-level caching (memory, Redis)

## 6. Detailed Checklist

### Database Infrastructure
- [ ] Implement PostgreSQL connection pooling with asyncpg
- [ ] Create database migrations for all entities
- [ ] Implement SqlRoomRepository with full CRUD operations
- [ ] Implement SqlGameRepository with optimized queries
- [ ] Implement SqlPlayerStatsRepository with aggregation support
- [ ] Add transaction management to SqlUnitOfWork
- [ ] Create database indexes for common queries
- [ ] Implement connection retry logic with circuit breaker
- [ ] Add database health check endpoint

### Event Store Implementation
- [ ] Design event storage schema with versioning
- [ ] Implement PostgreSQL-backed event store
- [ ] Create event serialization/deserialization layer
- [ ] Implement event stream per aggregate root
- [ ] Add event replay functionality
- [ ] Create snapshot storage mechanism
- [ ] Implement event compaction strategy
- [ ] Add event store health monitoring
- [ ] Create event recovery command-line tool

### Caching Layer
- [ ] Implement Redis connection pool
- [ ] Create CachedRoomRepository decorator
- [ ] Add cache warming on startup
- [ ] Implement cache invalidation on writes
- [ ] Add cache metrics (hit/miss rates)
- [ ] Create cache eviction policies
- [ ] Implement distributed cache for multi-instance

### Rate Limiting
- [ ] Implement token bucket algorithm
- [ ] Create Redis-backed rate limiter
- [ ] Add per-player rate limits (actions/minute)
- [ ] Add per-room rate limits (messages/second)
- [ ] Implement WebSocket message throttling
- [ ] Create rate limit headers for HTTP responses
- [ ] Add rate limit metrics
- [ ] Implement graceful degradation on limit

### Logging Infrastructure
- [ ] Configure structured logging with loguru
- [ ] Implement correlation ID propagation
- [ ] Add request/response logging middleware
- [ ] Create log shipping to centralized service
- [ ] Implement log level configuration
- [ ] Add performance logging for slow operations
- [ ] Create log retention policies
- [ ] Implement sensitive data masking

### Metrics Collection
- [ ] Set up Prometheus metrics registry
- [ ] Implement custom game metrics (games/hour, avg duration)
- [ ] Add WebSocket connection metrics
- [ ] Create database query performance metrics
- [ ] Implement cache performance metrics
- [ ] Add business metrics (player actions, win rates)
- [ ] Create metrics HTTP endpoint
- [ ] Implement metric aggregation for dashboards

### Health Monitoring
- [ ] Create /health endpoint with basic checks
- [ ] Implement /health/ready for Kubernetes
- [ ] Add /health/live for liveness probes
- [ ] Create dependency health checks (DB, Redis, etc)
- [ ] Implement health check caching
- [ ] Add circuit breaker status to health
- [ ] Create health history tracking
- [ ] Implement alerting thresholds

### Middleware Pipeline
- [ ] Create middleware base class/interface
- [ ] Implement correlation ID middleware
- [ ] Add request timing middleware
- [ ] Create error handling middleware
- [ ] Implement request validation middleware
- [ ] Add response compression middleware
- [ ] Create security headers middleware
- [ ] Implement request deduplication

### WebSocket Infrastructure
- [ ] Implement WebSocketConnectionPool
- [ ] Create message serialization layer
- [ ] Add binary message support for efficiency
- [ ] Implement room-based broadcast optimization
- [ ] Create connection state tracking
- [ ] Add heartbeat/ping mechanism
- [ ] Implement graceful shutdown handling
- [ ] Create WebSocket metrics collection

### Integration Adapters
- [ ] Implement WebSocketEventPublisher
- [ ] Create MetricsCollectorAdapter for Prometheus
- [ ] Implement LoggingServiceAdapter
- [ ] Create HealthCheckAdapter
- [ ] Implement RateLimiterAdapter
- [ ] Add CircuitBreakerAdapter
- [ ] Create CacheAdapter interface
- [ ] Implement NotificationAdapter

## 7. Documentation Alignment

### Documents Requiring Updates After Implementation

#### Architecture Documents
- `backend/docs/clean-architecture/ARCHITECTURE.md` - Add infrastructure details
- `backend/docs/clean-architecture/DEPENDENCIES.md` - Update with new dependencies
- `backend/docs/clean-architecture/DEPLOYMENT.md` - Add infrastructure requirements

#### API Documentation
- `backend/docs/api/WEBSOCKET_PROTOCOL.md` - Document any protocol optimizations
- `backend/docs/api/HEALTH_ENDPOINTS.md` - New health check documentation
- `backend/docs/api/METRICS_ENDPOINTS.md` - Metrics endpoint documentation

#### Configuration Guides
- `backend/docs/configuration/DATABASE.md` - Database setup and migrations
- `backend/docs/configuration/REDIS.md` - Cache and rate limit configuration
- `backend/docs/configuration/MONITORING.md` - Metrics and logging setup

#### Operational Guides
- `backend/docs/operations/BACKUP_RECOVERY.md` - Event store recovery procedures
- `backend/docs/operations/PERFORMANCE_TUNING.md` - Cache and connection pool tuning
- `backend/docs/operations/TROUBLESHOOTING.md` - Common infrastructure issues

## 8. Testing Readiness Plan

### Unit Tests
- Repository implementations with in-memory databases
- Event store with event ordering verification
- Rate limiter with various limit scenarios
- Cache decorator with hit/miss scenarios
- Middleware pipeline with order verification

### Integration Tests
- Database repositories with real PostgreSQL
- Redis cache with expiration testing
- Event store with concurrent writes
- WebSocket broadcasting with multiple connections
- Health checks with dependency failures

### System Tests
- Full game flow with infrastructure
- Performance tests with database queries
- Load tests for rate limiting
- Failover tests for connection loss
- Recovery tests for event replay

### Test Infrastructure
- Docker Compose for test dependencies
- Test data generators for load testing
- Performance benchmarking suite
- Chaos testing for failure scenarios

## 9. Phase Completion Criteria

### Functional Criteria
- [ ] All frontend requests continue to work without modification
- [ ] WebSocket messages maintain exact same format
- [ ] Game state persists across server restarts
- [ ] Events are stored and can be replayed
- [ ] Rate limiting prevents abuse without affecting normal play

### Performance Criteria
- [ ] Response time remains within 10% of current system
- [ ] Database queries execute in under 100ms
- [ ] Cache hit rate exceeds 80% for common operations
- [ ] WebSocket broadcasts complete in under 50ms

### Operational Criteria
- [ ] All infrastructure has health checks
- [ ] Metrics are collected and accessible
- [ ] Logs are structured and searchable
- [ ] System can recover from database outages
- [ ] Rate limits are configurable without restart

### Quality Criteria
- [ ] 90% unit test coverage for infrastructure code
- [ ] All integration points have error handling
- [ ] No direct database access from application layer
- [ ] All external calls have timeouts and retries

### Documentation Criteria
- [ ] All infrastructure components documented
- [ ] Deployment guide updated
- [ ] Monitoring setup documented
- [ ] Troubleshooting guide created

## Success Metrics

Upon completion of Phase 5:
1. The entire backend operates on clean architecture
2. No changes required to the frontend
3. System is production-ready with enterprise features
4. All phases of Task 3 are complete
5. Architecture supports future enhancements

## Next Steps

After Phase 5 completion:
1. Performance optimization pass
2. Security audit
3. Load testing and tuning
4. Production deployment planning
5. Post-implementation review