# Phase 5: Infrastructure Layer Technical Design

**Document Purpose**: Technical patterns, contracts, and design decisions for infrastructure implementation with focus on maintaining real-time performance while preparing for future persistence needs.

## Navigation
- [Main Planning Document](./PHASE_5_INFRASTRUCTURE_LAYER.md)
- [Implementation Checklist](./PHASE_5_IMPLEMENTATION_CHECKLIST.md)
- [Testing Plan](./PHASE_5_TESTING_PLAN.md)
- [Progress Tracking](./INFRASTRUCTURE_PROGRESS_TRACKING.md)

## Design Philosophy

Based on the Database Integration Readiness Report, this infrastructure layer prioritizes:
1. **Zero-latency operations** for active games
2. **In-memory performance** matching current system
3. **Async persistence** for completed games only
4. **Future-ready abstractions** without current performance cost

## Architectural Patterns

### Adapter Pattern Implementation
All infrastructure components will implement application interfaces using the Adapter pattern:

```python
# Application Interface (from application layer)
class EventPublisher(ABC):
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event."""
        pass

# Infrastructure Implementation
class WebSocketEventPublisher(EventPublisher):
    def __init__(self, socket_manager: SocketManager):
        self._socket_manager = socket_manager
        self._serializer = EventSerializer()
    
    async def publish(self, event: DomainEvent) -> None:
        """Convert domain event to WebSocket message and broadcast."""
        # Convert to WebSocket message format
        message = self._serializer.to_websocket_message(event)
        
        # Determine broadcast scope
        room_id = self._extract_room_id(event)
        
        # Broadcast to appropriate rooms
        await self._socket_manager.broadcast(room_id, message)
```

### Repository Pattern Implementation
Repositories maintain in-memory performance while supporting future persistence:

```python
class InMemoryGameRepository(GameRepository):
    def __init__(self):
        self._games: Dict[str, Game] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._access_count: Dict[str, int] = {}  # For LRU eviction
        self._archive_queue: asyncio.Queue = asyncio.Queue()
    
    async def get_by_id(self, game_id: str) -> Optional[Game]:
        # O(1) lookup, no I/O latency
        if game_id in self._games:
            self._access_count[game_id] += 1
            return self._games[game_id]
        return None
    
    async def save(self, game: Game) -> None:
        """Save game in memory with async archival for completed games."""
        async with self._get_lock(game.id):
            self._games[game.id] = game
            
            # Queue for archival if game is complete
            if game.is_complete():
                await self._archive_queue.put(game.to_dict())
    
    async def _archive_completed_games(self):
        """Background task to archive completed games without blocking."""
        while True:
            try:
                game_data = await self._archive_queue.get()
                # Async write to persistent storage (S3, PostgreSQL, etc.)
                await self._async_persist(game_data)
                # Remove from memory after successful archival
                game_id = game_data['id']
                if game_id in self._games and self._games[game_id].is_complete():
                    del self._games[game_id]
            except Exception as e:
                logger.error(f"Failed to archive game: {e}")
                # Game stays in memory, retry later
```

### Hybrid Repository Pattern
Supports both in-memory and future database backends:

```python
class HybridGameRepository(GameRepository):
    def __init__(self, memory_repo: GameRepository, persistent_repo: Optional[GameRepository] = None):
        self._memory = memory_repo
        self._persistent = persistent_repo  # Can be None initially
    
    async def get_by_id(self, game_id: str) -> Optional[Game]:
        # Always try memory first (instant)
        if game := await self._memory.get_by_id(game_id):
            return game
        
        # Only check persistent storage for completed games
        if self._persistent and not self._is_active_game(game_id):
            return await self._persistent.get_by_id(game_id)
        
        return None
```

### Event Sourcing Pattern
Hybrid event store that doesn't impact game performance:

```python
class HybridEventStore(EventStore):
    def __init__(self):
        self._memory_buffer = deque(maxlen=10000)  # Recent events in memory
        self._completed_game_events: Dict[str, List[Event]] = {}
        self._archive_queue = asyncio.Queue()
        self._serializer = EventSerializer()
    
    async def append(self, stream_id: str, events: List[Event]) -> None:
        """Append events without blocking game operations."""
        # Always append to memory buffer (instant)
        for event in events:
            self._memory_buffer.append((stream_id, event))
        
        # Check if this is a game completion event
        if self._is_game_complete_event(events):
            # Move to completed games collection
            if stream_id not in self._completed_game_events:
                self._completed_game_events[stream_id] = []
            self._completed_game_events[stream_id].extend(events)
            
            # Queue for async archival
            await self._archive_queue.put({
                'stream_id': stream_id,
                'events': [self._serializer.serialize(e) for e in events]
            })
    
    async def get_recent_events(self, stream_id: str, limit: int = 100) -> List[Event]:
        """Get recent events from memory buffer (instant access)."""
        return [
            event for sid, event in self._memory_buffer 
            if sid == stream_id
        ][-limit:]
    
    async def get_events(
        self, 
        stream_id: str, 
        from_version: int = 0
    ) -> List[Event]:
        """Get events from stream, using snapshots for efficiency."""
        # Find nearest snapshot
        snapshot = await self._get_latest_snapshot(stream_id, from_version)
        
        start_version = snapshot.version if snapshot else from_version
        
        # Load events after snapshot
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM events 
                WHERE stream_id = $1 AND version > $2
                ORDER BY version
            """, stream_id, start_version)
        
        events = [self._serializer.deserialize(row) for row in rows]
        
        # Apply events to snapshot state if available
        if snapshot:
            return self._apply_to_snapshot(snapshot, events)
        
        return events
    
    async def get_snapshot(self, stream_id: str) -> Optional[Snapshot]:
        """Get latest snapshot for a stream."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM snapshots
                WHERE stream_id = $1
                ORDER BY version DESC
                LIMIT 1
            """, stream_id)
        
        return self._deserialize_snapshot(row) if row else None
```

### Middleware Stack Pattern
Composable middleware pipeline for request processing:

```python
class MiddlewarePipeline:
    def __init__(self):
        self._middlewares: List[Middleware] = []
    
    def use(self, middleware: Middleware) -> None:
        """Add middleware to pipeline."""
        self._middlewares.append(middleware)
    
    async def execute(self, context: RequestContext) -> Response:
        """Execute middleware pipeline."""
        # Build the chain
        def build_chain(index: int):
            if index >= len(self._middlewares):
                return self._final_handler
            
            middleware = self._middlewares[index]
            next_handler = build_chain(index + 1)
            
            return lambda ctx: middleware.handle(ctx, next_handler)
        
        chain = build_chain(0)
        return await chain(context)
    
    async def _final_handler(self, context: RequestContext) -> Response:
        """Final handler if no middleware handles the request."""
        return Response(status=404, body="Not Found")

# Example middleware implementations
class CorrelationIdMiddleware(Middleware):
    async def handle(
        self, 
        context: RequestContext, 
        next_handler: Handler
    ) -> Response:
        # Extract or generate correlation ID
        correlation_id = context.headers.get(
            'X-Correlation-ID',
            str(uuid.uuid4())
        )
        
        # Add to context
        context.correlation_id = correlation_id
        
        # Process request
        response = await next_handler(context)
        
        # Add to response
        response.headers['X-Correlation-ID'] = correlation_id
        
        return response

class RateLimitMiddleware(Middleware):
    def __init__(self, rate_limiter: RateLimiter):
        self._rate_limiter = rate_limiter
    
    async def handle(
        self, 
        context: RequestContext, 
        next_handler: Handler
    ) -> Response:
        # Check rate limit
        player_id = context.player_id
        if not await self._rate_limiter.allow(player_id):
            return Response(
                status=429,
                body={"error": "Rate limit exceeded"},
                headers={"Retry-After": "60"}
            )
        
        return await next_handler(context)
```

## Design Patterns and Principles

### Unit of Work Pattern
Managing consistency in memory with async persistence:

```python
class InMemoryUnitOfWork(UnitOfWork):
    def __init__(self):
        self._repositories: Dict[str, Repository] = {}
        self._changes: List[Tuple[str, str, Any]] = []  # (repo, method, args)
        self._lock = asyncio.Lock()
    
    async def __aenter__(self):
        await self._lock.acquire()
        self._changes.clear()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                await self.rollback()
            else:
                await self.commit()
        finally:
            self._lock.release()
    
    @property
    def games(self) -> GameRepository:
        if 'games' not in self._repositories:
            self._repositories['games'] = InMemoryGameRepository()
        return self._repositories['games']
    
    @property
    def rooms(self) -> RoomRepository:
        if 'rooms' not in self._repositories:
            self._repositories['rooms'] = InMemoryRoomRepository()
        return self._repositories['rooms']
    
    async def commit(self) -> None:
        """Apply all changes atomically in memory."""
        # All changes are already applied in memory
        # Just track for potential async persistence
        if self._has_completed_games():
            await self._queue_for_archival()
    
    async def rollback(self) -> None:
        """Rollback not needed for in-memory operations."""
        # In-memory operations are atomic at method level
        pass
```

### Circuit Breaker Pattern
Preventing cascading failures:

```python
class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._expected_exception = expected_exception
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = CircuitState.CLOSED
    
    async def call(self, func: Callable, *args, **kwargs):
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self._expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        return (
            self._last_failure_time and
            time.time() - self._last_failure_time >= self._recovery_timeout
        )
    
    def _on_success(self):
        self._failure_count = 0
        self._state = CircuitState.CLOSED
    
    def _on_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self._failure_threshold:
            self._state = CircuitState.OPEN
```

### Decorator Pattern for Caching
Adding caching behavior to repositories:

```python
class CachedRepositoryDecorator(Repository):
    def __init__(
        self,
        repository: Repository,
        cache: Cache,
        ttl: int = 300  # 5 minutes default
    ):
        self._repository = repository
        self._cache = cache
        self._ttl = ttl
    
    async def get_by_id(self, entity_id: str) -> Optional[Entity]:
        # Try cache first
        cache_key = f"{self._repository.__class__.__name__}:{entity_id}"
        
        if cached := await self._cache.get(cache_key):
            return self._deserialize(cached)
        
        # Fetch from repository
        entity = await self._repository.get_by_id(entity_id)
        
        if entity:
            # Cache the result
            await self._cache.set(
                cache_key,
                self._serialize(entity),
                ttl=self._ttl
            )
        
        return entity
    
    async def save(self, entity: Entity) -> None:
        # Save to repository
        await self._repository.save(entity)
        
        # Invalidate cache
        cache_key = f"{self._repository.__class__.__name__}:{entity.id}"
        await self._cache.delete(cache_key)
    
    def _serialize(self, entity: Entity) -> str:
        return json.dumps(entity.to_dict())
    
    def _deserialize(self, data: str) -> Entity:
        return self._repository.entity_class.from_dict(json.loads(data))
```

## Risk Mitigation Strategies

### Memory Pressure Management
**Risk**: Out of memory errors with many concurrent games

**Mitigation Strategy**:
```python
class MemoryBoundedGameRepository:
    def __init__(self, max_games: int = 10000, max_memory_mb: int = 4096):
        self._games: OrderedDict[str, Game] = OrderedDict()
        self._max_games = max_games
        self._max_memory = max_memory_mb * 1024 * 1024
        self._memory_monitor = MemoryMonitor()
    
    async def save(self, game: Game) -> None:
        # Check memory pressure
        if await self._check_memory_pressure():
            await self._evict_completed_games()
        
        # LRU eviction if at capacity
        if len(self._games) >= self._max_games:
            # Only evict completed games
            for game_id, old_game in list(self._games.items()):
                if old_game.is_complete():
                    await self._archive_game(old_game)
                    del self._games[game_id]
                    break
            else:
                # No completed games to evict
                raise MemoryError("Game capacity reached with all active games")
        
        self._games[game.id] = game
        self._games.move_to_end(game.id)  # LRU ordering
    
    async def _check_memory_pressure(self) -> bool:
        current_usage = self._memory_monitor.get_process_memory()
        return current_usage > self._max_memory * 0.8  # 80% threshold
```

### Event Buffer Management
**Risk**: Memory exhaustion from event accumulation

**Mitigation Strategy**:
```python
class BoundedEventStore(EventStore):
    def __init__(self, max_events_per_game: int = 1000):
        self._events: Dict[str, deque] = {}
        self._max_events = max_events_per_game
        self._total_event_count = 0
        self._max_total_events = 100000
    
    async def append(self, stream_id: str, events: List[Event]) -> None:
        """Append events with automatic overflow handling."""
        if stream_id not in self._events:
            self._events[stream_id] = deque(maxlen=self._max_events)
        
        # Check total event count
        if self._total_event_count + len(events) > self._max_total_events:
            await self._compact_completed_games()
        
        # Append events (old events automatically dropped by deque)
        self._events[stream_id].extend(events)
        self._total_event_count += len(events)
        
        # Archive if game complete
        if self._is_game_complete(events):
            await self._archive_and_remove(stream_id)
```

### WebSocket Broadcast Storms
**Risk**: Server overload from mass reconnections

**Mitigation Strategy**:
```python
class ThrottledBroadcaster:
    def __init__(self, base_broadcaster: Broadcaster):
        self._base_broadcaster = base_broadcaster
        self._rate_limiter = TokenBucket(
            capacity=1000,  # messages
            refill_rate=100  # per second
        )
        self._queue = asyncio.Queue(maxsize=10000)
        self._processing_task = None
    
    async def broadcast(self, room_id: str, message: dict) -> None:
        # Check rate limit
        if not self._rate_limiter.consume(1):
            # Queue for later delivery
            try:
                await self._queue.put((room_id, message))
            except asyncio.QueueFull:
                logger.warning(f"Broadcast queue full for room {room_id}")
            return
        
        # Direct broadcast
        await self._base_broadcaster.broadcast(room_id, message)
    
    async def _process_queue(self):
        """Process queued messages with rate limiting."""
        while True:
            room_id, message = await self._queue.get()
            
            # Wait for rate limit capacity
            while not self._rate_limiter.consume(1):
                await asyncio.sleep(0.1)
            
            await self._base_broadcaster.broadcast(room_id, message)
```

### Cache Inconsistency
**Risk**: Serving stale data after updates

**Mitigation Strategy**:
```python
class ConsistentCache:
    def __init__(self, redis_pool: aioredis.Redis):
        self._redis = redis_pool
        self._local_cache = {}
        self._version_key_prefix = "version:"
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        # Increment version
        version_key = f"{self._version_key_prefix}{key}"
        version = await self._redis.incr(version_key)
        
        # Store with version
        cache_data = {
            "value": value,
            "version": version,
            "timestamp": time.time()
        }
        
        await self._redis.setex(
            key,
            ttl,
            json.dumps(cache_data)
        )
        
        # Update local cache
        self._local_cache[key] = cache_data
    
    async def get(self, key: str) -> Optional[Any]:
        # Check local cache first
        if key in self._local_cache:
            local_data = self._local_cache[key]
            
            # Verify version
            version_key = f"{self._version_key_prefix}{key}"
            current_version = await self._redis.get(version_key)
            
            if current_version and int(current_version) == local_data["version"]:
                return local_data["value"]
        
        # Fetch from Redis
        data = await self._redis.get(key)
        if not data:
            return None
        
        cache_data = json.loads(data)
        self._local_cache[key] = cache_data
        
        return cache_data["value"]
    
    async def invalidate(self, key: str) -> None:
        # Increment version to invalidate all copies
        version_key = f"{self._version_key_prefix}{key}"
        await self._redis.incr(version_key)
        
        # Remove from caches
        await self._redis.delete(key)
        self._local_cache.pop(key, None)
```

## Performance Optimization Strategies

### Performance Configuration
```python
MEMORY_REPOSITORY_CONFIG = {
    "max_active_games": 10000,
    "max_memory_mb": 4096,
    "eviction_check_interval": 60,  # seconds
    "gc_completed_games_after": 300,  # seconds
    "event_buffer_size": 10000,
    "archive_batch_size": 100,
}

# Redis only for rate limiting and caching
REDIS_CONFIG = {
    "rate_limit_window": 60,  # seconds
    "rate_limit_max_requests": 60,
    "cache_ttl": 300,  # seconds
    "max_connections": 10,
}

# Async persistence for completed games only
ARCHIVE_CONFIG = {
    "backend": "s3",  # or "postgresql", "filesystem"
    "batch_size": 100,
    "flush_interval": 60,  # seconds
    "compression": "gzip",
    "retention_days": 90,
}
```

### Async Archival Operations
```python
class AsyncGameArchiver:
    def __init__(self, backend: ArchiveBackend):
        self._backend = backend
        self._queue = asyncio.Queue(maxsize=10000)
        self._batch_size = 100
        self._flush_interval = 60.0  # seconds
        self._worker_task = None
    
    async def archive_game(self, game_data: dict) -> None:
        """Queue game for archival without blocking."""
        try:
            self._queue.put_nowait(game_data)
        except asyncio.QueueFull:
            # Log but don't block game operations
            logger.warning(f"Archive queue full, dropping game {game_data['id']}")
    
    async def _archive_worker(self):
        """Background worker for archiving games."""
        batch = []
        last_flush = time.time()
        
        while True:
            try:
                # Get with timeout for periodic flushing
                timeout = self._flush_interval - (time.time() - last_flush)
                game_data = await asyncio.wait_for(
                    self._queue.get(), 
                    timeout=max(0.1, timeout)
                )
                batch.append(game_data)
                
                # Flush if batch full
                if len(batch) >= self._batch_size:
                    await self._flush_batch(batch)
                    batch.clear()
                    last_flush = time.time()
                    
            except asyncio.TimeoutError:
                # Periodic flush
                if batch:
                    await self._flush_batch(batch)
                    batch.clear()
                last_flush = time.time()
```

### Async I/O Optimization
```python
class OptimizedGameService:
    def __init__(self, repositories: Dict[str, Repository]):
        self._repos = repositories
    
    async def get_game_state(self, game_id: str) -> GameState:
        # Parallel fetch of related data
        game_task = self._repos['games'].get_by_id(game_id)
        stats_task = self._repos['stats'].get_by_game_id(game_id)
        events_task = self._repos['events'].get_recent(game_id, limit=10)
        
        # Wait for all concurrently
        game, stats, events = await asyncio.gather(
            game_task, stats_task, events_task
        )
        
        return GameState(game=game, stats=stats, recent_events=events)
```

### Game State Caching
```python
class GameStateCache:
    def __init__(self):
        self._active_games: Dict[str, Game] = {}  # Hot cache
        self._game_summaries: LRUCache = LRUCache(maxsize=1000)  # Read cache
        self._stats_cache: TTLCache = TTLCache(maxsize=100, ttl=60)  # Analytics
    
    def get_active_game(self, game_id: str) -> Optional[Game]:
        """Get active game with O(1) access."""
        return self._active_games.get(game_id)
    
    def get_game_summary(self, game_id: str) -> Optional[dict]:
        """Get cached game summary for UI display."""
        return self._game_summaries.get(game_id)
    
    def cache_game_completion(self, game: Game) -> None:
        """Cache completed game summary before archival."""
        summary = {
            'id': game.id,
            'winner': game.winner,
            'duration': game.duration,
            'final_scores': game.get_final_scores(),
            'completed_at': game.completed_at
        }
        self._game_summaries[game.id] = summary
        
        # Remove from active cache
        self._active_games.pop(game.id, None)
```

## Configuration Management

### Environment-Based Configuration
```python
class InfrastructureConfig:
    def __init__(self):
        # Memory limits
        self.max_active_games = int(os.getenv("MAX_ACTIVE_GAMES", "10000"))
        self.max_memory_mb = int(os.getenv("MAX_MEMORY_MB", "4096"))
        
        # Redis for rate limiting only
        self.redis_url = os.getenv(
            "REDIS_URL",
            "redis://localhost:6379"
        )
        self.rate_limit_per_minute = int(
            os.getenv("RATE_LIMIT_PER_MINUTE", "60")
        )
        
        # Archive configuration
        self.archive_backend = os.getenv("ARCHIVE_BACKEND", "s3")
        self.archive_url = os.getenv("ARCHIVE_URL", "")
        self.archive_retention_days = int(
            os.getenv("ARCHIVE_RETENTION_DAYS", "90")
        )
        
    @property
    def is_production(self) -> bool:
        return os.getenv("ENVIRONMENT") == "production"
    
    def get_pool_config(self) -> dict:
        if self.is_production:
            return {
                "min_size": 20,
                "max_size": 50,
                "max_queries": 100000,
            }
        return {
            "min_size": 5,
            "max_size": 10,
            "max_queries": 50000,
        }
```

### Feature Toggles
```python
class FeatureFlags:
    def __init__(self, config_source: ConfigSource):
        self._config = config_source
        self._cache = {}
        self._refresh_interval = 60  # seconds
        self._last_refresh = 0
    
    async def is_enabled(self, feature: str) -> bool:
        await self._refresh_if_needed()
        return self._cache.get(feature, False)
    
    async def _refresh_if_needed(self):
        if time.time() - self._last_refresh > self._refresh_interval:
            self._cache = await self._config.get_all_flags()
            self._last_refresh = time.time()

# Usage in infrastructure
if await feature_flags.is_enabled("use_event_sourcing"):
    repository = EventSourcedGameRepository(event_store)
else:
    repository = SqlGameRepository(db_pool)
```