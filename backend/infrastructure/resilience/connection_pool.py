"""
Connection pooling for external resources.

Manages connection pools with health checking and automatic recovery.
"""

from typing import TypeVar, Generic, Callable, Optional, Any, Dict, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import asynccontextmanager, contextmanager
from enum import Enum
import asyncio
import threading
import time
import logging
import queue
from abc import ABC, abstractmethod
import weakref


logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Connection states."""
    IDLE = "idle"
    IN_USE = "in_use"
    TESTING = "testing"
    INVALID = "invalid"
    CLOSED = "closed"


class PoolExhaustedError(Exception):
    """Raised when connection pool is exhausted."""
    pass


@dataclass
class ConnectionPoolConfig:
    """Configuration for connection pool."""
    min_size: int = 2
    max_size: int = 10
    max_overflow: int = 5
    timeout: timedelta = timedelta(seconds=30)
    idle_timeout: timedelta = timedelta(minutes=10)
    max_lifetime: timedelta = timedelta(hours=1)
    validation_interval: timedelta = timedelta(minutes=5)
    retry_attempts: int = 3
    retry_delay: timedelta = timedelta(seconds=1)
    
    def __post_init__(self):
        """Validate configuration."""
        if self.min_size < 0:
            raise ValueError("min_size must be non-negative")
        if self.max_size < self.min_size:
            raise ValueError("max_size must be >= min_size")
        if self.max_overflow < 0:
            raise ValueError("max_overflow must be non-negative")


@dataclass
class PooledConnection:
    """Wrapper for pooled connections."""
    connection: Any
    pool: 'ConnectionPool'
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: datetime = field(default_factory=datetime.utcnow)
    last_validated_at: datetime = field(default_factory=datetime.utcnow)
    state: ConnectionState = ConnectionState.IDLE
    use_count: int = 0
    
    def is_expired(self, max_lifetime: timedelta) -> bool:
        """Check if connection has exceeded max lifetime."""
        return datetime.utcnow() - self.created_at > max_lifetime
    
    def is_idle_expired(self, idle_timeout: timedelta) -> bool:
        """Check if connection has been idle too long."""
        if self.state != ConnectionState.IDLE:
            return False
        return datetime.utcnow() - self.last_used_at > idle_timeout
    
    def needs_validation(self, validation_interval: timedelta) -> bool:
        """Check if connection needs validation."""
        return datetime.utcnow() - self.last_validated_at > validation_interval
    
    def mark_used(self) -> None:
        """Mark connection as used."""
        self.last_used_at = datetime.utcnow()
        self.use_count += 1
        self.state = ConnectionState.IN_USE
    
    def mark_idle(self) -> None:
        """Mark connection as idle."""
        self.state = ConnectionState.IDLE
    
    def mark_invalid(self) -> None:
        """Mark connection as invalid."""
        self.state = ConnectionState.INVALID


@dataclass
class ConnectionPoolStats:
    """Statistics for connection pool."""
    total_created: int = 0
    total_destroyed: int = 0
    total_checkouts: int = 0
    total_returns: int = 0
    total_timeouts: int = 0
    total_validation_failures: int = 0
    current_size: int = 0
    current_idle: int = 0
    current_in_use: int = 0
    current_overflow: int = 0
    wait_time_total: float = 0.0
    wait_time_max: float = 0.0
    
    def record_checkout(self, wait_time: float = 0.0) -> None:
        """Record connection checkout."""
        self.total_checkouts += 1
        self.wait_time_total += wait_time
        self.wait_time_max = max(self.wait_time_max, wait_time)
    
    def get_average_wait_time(self) -> float:
        """Get average wait time."""
        if self.total_checkouts == 0:
            return 0.0
        return self.wait_time_total / self.total_checkouts


T = TypeVar('T')


class ConnectionFactory(ABC, Generic[T]):
    """Abstract factory for creating connections."""
    
    @abstractmethod
    def create(self) -> T:
        """Create a new connection."""
        pass
    
    @abstractmethod
    def validate(self, connection: T) -> bool:
        """Validate a connection."""
        pass
    
    @abstractmethod
    def destroy(self, connection: T) -> None:
        """Destroy a connection."""
        pass
    
    @abstractmethod
    async def create_async(self) -> T:
        """Create a new connection asynchronously."""
        pass
    
    @abstractmethod
    async def validate_async(self, connection: T) -> bool:
        """Validate a connection asynchronously."""
        pass
    
    @abstractmethod
    async def destroy_async(self, connection: T) -> None:
        """Destroy a connection asynchronously."""
        pass


class ConnectionPool(Generic[T]):
    """
    Generic connection pool implementation.
    
    Manages a pool of reusable connections with health checking,
    automatic recovery, and overflow handling.
    """
    
    def __init__(
        self,
        factory: ConnectionFactory[T],
        config: Optional[ConnectionPoolConfig] = None
    ):
        """Initialize connection pool."""
        self.factory = factory
        self.config = config or ConnectionPoolConfig()
        self.stats = ConnectionPoolStats()
        
        # Connection storage
        self._idle_connections: queue.Queue[PooledConnection] = queue.Queue()
        self._in_use_connections: Set[PooledConnection] = set()
        self._all_connections: List[PooledConnection] = []
        
        # Synchronization
        self._lock = threading.RLock()
        self._not_empty = threading.Condition(self._lock)
        self._shutdown = False
        
        # Background tasks
        self._maintenance_task = None
        
        # Initialize minimum connections
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """Initialize pool with minimum connections."""
        for _ in range(self.config.min_size):
            try:
                conn = self._create_connection()
                self._idle_connections.put(conn)
            except Exception as e:
                logger.error(f"Failed to create initial connection: {e}")
    
    def _create_connection(self) -> PooledConnection:
        """Create a new pooled connection."""
        connection = self.factory.create()
        pooled = PooledConnection(connection, self)
        
        with self._lock:
            self._all_connections.append(pooled)
            self.stats.total_created += 1
            self.stats.current_size = len(self._all_connections)
        
        return pooled
    
    def _destroy_connection(self, pooled: PooledConnection) -> None:
        """Destroy a pooled connection."""
        try:
            self.factory.destroy(pooled.connection)
        except Exception as e:
            logger.error(f"Error destroying connection: {e}")
        
        pooled.state = ConnectionState.CLOSED
        
        with self._lock:
            self._all_connections.remove(pooled)
            self.stats.total_destroyed += 1
            self.stats.current_size = len(self._all_connections)
    
    def _validate_connection(self, pooled: PooledConnection) -> bool:
        """Validate a pooled connection."""
        try:
            pooled.state = ConnectionState.TESTING
            is_valid = self.factory.validate(pooled.connection)
            
            if is_valid:
                pooled.last_validated_at = datetime.utcnow()
                pooled.state = ConnectionState.IDLE
            else:
                pooled.mark_invalid()
                self.stats.total_validation_failures += 1
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            pooled.mark_invalid()
            self.stats.total_validation_failures += 1
            return False
    
    def acquire(self, timeout: Optional[float] = None) -> T:
        """
        Acquire a connection from the pool.
        
        Args:
            timeout: Timeout in seconds (uses config timeout if None)
            
        Returns:
            Connection object
            
        Raises:
            PoolExhaustedError: If pool is exhausted and timeout reached
        """
        if self._shutdown:
            raise RuntimeError("Pool is shutdown")
        
        if timeout is None:
            timeout = self.config.timeout.total_seconds()
        
        start_time = time.time()
        
        while True:
            with self._lock:
                # Try to get idle connection
                if not self._idle_connections.empty():
                    pooled = self._idle_connections.get_nowait()
                    
                    # Validate connection if needed
                    if (pooled.is_expired(self.config.max_lifetime) or
                        pooled.needs_validation(self.config.validation_interval)):
                        
                        if not self._validate_connection(pooled):
                            self._destroy_connection(pooled)
                            continue
                    
                    # Mark as in use
                    pooled.mark_used()
                    self._in_use_connections.add(pooled)
                    
                    # Update stats
                    wait_time = time.time() - start_time
                    self.stats.record_checkout(wait_time)
                    self.stats.current_idle = self._idle_connections.qsize()
                    self.stats.current_in_use = len(self._in_use_connections)
                    
                    return pooled.connection
                
                # Check if can create new connection
                current_size = len(self._all_connections)
                overflow_count = max(0, current_size - self.config.max_size)
                
                if current_size < self.config.max_size:
                    # Create within normal capacity
                    try:
                        pooled = self._create_connection()
                        pooled.mark_used()
                        self._in_use_connections.add(pooled)
                        
                        wait_time = time.time() - start_time
                        self.stats.record_checkout(wait_time)
                        self.stats.current_in_use = len(self._in_use_connections)
                        
                        return pooled.connection
                        
                    except Exception as e:
                        logger.error(f"Failed to create connection: {e}")
                        # Continue to wait
                
                elif overflow_count < self.config.max_overflow:
                    # Create overflow connection
                    try:
                        pooled = self._create_connection()
                        pooled.mark_used()
                        self._in_use_connections.add(pooled)
                        
                        self.stats.current_overflow = overflow_count + 1
                        wait_time = time.time() - start_time
                        self.stats.record_checkout(wait_time)
                        self.stats.current_in_use = len(self._in_use_connections)
                        
                        return pooled.connection
                        
                    except Exception as e:
                        logger.error(f"Failed to create overflow connection: {e}")
                
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    self.stats.total_timeouts += 1
                    raise PoolExhaustedError(
                        f"Connection pool exhausted (timeout={timeout}s)"
                    )
                
                # Wait for connection to become available
                remaining = timeout - elapsed
                self._not_empty.wait(min(remaining, 1.0))
    
    def release(self, connection: T) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            connection: Connection to release
        """
        with self._lock:
            # Find pooled connection
            pooled = None
            for pc in self._in_use_connections:
                if pc.connection == connection:
                    pooled = pc
                    break
            
            if pooled is None:
                logger.warning("Attempted to release unknown connection")
                return
            
            # Remove from in-use set
            self._in_use_connections.remove(pooled)
            self.stats.total_returns += 1
            
            # Check if should destroy
            if (pooled.state == ConnectionState.INVALID or
                pooled.is_expired(self.config.max_lifetime)):
                self._destroy_connection(pooled)
            else:
                # Return to idle pool
                pooled.mark_idle()
                self._idle_connections.put(pooled)
            
            # Update stats
            self.stats.current_idle = self._idle_connections.qsize()
            self.stats.current_in_use = len(self._in_use_connections)
            
            # Check overflow
            current_size = len(self._all_connections)
            if current_size > self.config.max_size:
                self.stats.current_overflow = current_size - self.config.max_size
            else:
                self.stats.current_overflow = 0
            
            # Notify waiters
            self._not_empty.notify()
    
    def close_all(self) -> None:
        """Close all connections in the pool."""
        self._shutdown = True
        
        with self._lock:
            # Close all connections
            for pooled in self._all_connections[:]:
                self._destroy_connection(pooled)
            
            self._idle_connections = queue.Queue()
            self._in_use_connections.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            'config': {
                'min_size': self.config.min_size,
                'max_size': self.config.max_size,
                'max_overflow': self.config.max_overflow
            },
            'current': {
                'size': self.stats.current_size,
                'idle': self.stats.current_idle,
                'in_use': self.stats.current_in_use,
                'overflow': self.stats.current_overflow
            },
            'totals': {
                'created': self.stats.total_created,
                'destroyed': self.stats.total_destroyed,
                'checkouts': self.stats.total_checkouts,
                'returns': self.stats.total_returns,
                'timeouts': self.stats.total_timeouts,
                'validation_failures': self.stats.total_validation_failures
            },
            'performance': {
                'average_wait_time': self.stats.get_average_wait_time(),
                'max_wait_time': self.stats.wait_time_max
            }
        }
    
    @contextmanager
    def connection(self, timeout: Optional[float] = None):
        """
        Context manager for connection checkout.
        
        Example:
            with pool.connection() as conn:
                # Use connection
                pass
        """
        conn = self.acquire(timeout)
        try:
            yield conn
        finally:
            self.release(conn)
    
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.close_all()


class AsyncConnectionPool(Generic[T]):
    """
    Asynchronous connection pool implementation.
    
    Async version of ConnectionPool for use with asyncio.
    """
    
    def __init__(
        self,
        factory: ConnectionFactory[T],
        config: Optional[ConnectionPoolConfig] = None
    ):
        """Initialize async connection pool."""
        self.factory = factory
        self.config = config or ConnectionPoolConfig()
        self.stats = ConnectionPoolStats()
        
        # Connection storage
        self._idle_connections: asyncio.Queue[PooledConnection] = asyncio.Queue()
        self._in_use_connections: Set[PooledConnection] = set()
        self._all_connections: List[PooledConnection] = []
        
        # Synchronization
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Condition()
        self._shutdown = False
        
        # Background tasks
        self._maintenance_task = None
    
    async def initialize(self) -> None:
        """Initialize pool with minimum connections."""
        for _ in range(self.config.min_size):
            try:
                conn = await self._create_connection()
                await self._idle_connections.put(conn)
            except Exception as e:
                logger.error(f"Failed to create initial connection: {e}")
    
    async def _create_connection(self) -> PooledConnection:
        """Create a new pooled connection."""
        connection = await self.factory.create_async()
        pooled = PooledConnection(connection, self)
        
        async with self._lock:
            self._all_connections.append(pooled)
            self.stats.total_created += 1
            self.stats.current_size = len(self._all_connections)
        
        return pooled
    
    async def _destroy_connection(self, pooled: PooledConnection) -> None:
        """Destroy a pooled connection."""
        try:
            await self.factory.destroy_async(pooled.connection)
        except Exception as e:
            logger.error(f"Error destroying connection: {e}")
        
        pooled.state = ConnectionState.CLOSED
        
        async with self._lock:
            self._all_connections.remove(pooled)
            self.stats.total_destroyed += 1
            self.stats.current_size = len(self._all_connections)
    
    async def _validate_connection(self, pooled: PooledConnection) -> bool:
        """Validate a pooled connection."""
        try:
            pooled.state = ConnectionState.TESTING
            is_valid = await self.factory.validate_async(pooled.connection)
            
            if is_valid:
                pooled.last_validated_at = datetime.utcnow()
                pooled.state = ConnectionState.IDLE
            else:
                pooled.mark_invalid()
                self.stats.total_validation_failures += 1
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            pooled.mark_invalid()
            self.stats.total_validation_failures += 1
            return False
    
    async def acquire(self, timeout: Optional[float] = None) -> T:
        """Acquire a connection from the pool asynchronously."""
        if self._shutdown:
            raise RuntimeError("Pool is shutdown")
        
        if timeout is None:
            timeout = self.config.timeout.total_seconds()
        
        start_time = time.time()
        
        while True:
            async with self._lock:
                # Try to get idle connection
                if not self._idle_connections.empty():
                    pooled = await self._idle_connections.get()
                    
                    # Validate connection if needed
                    if (pooled.is_expired(self.config.max_lifetime) or
                        pooled.needs_validation(self.config.validation_interval)):
                        
                        if not await self._validate_connection(pooled):
                            await self._destroy_connection(pooled)
                            continue
                    
                    # Mark as in use
                    pooled.mark_used()
                    self._in_use_connections.add(pooled)
                    
                    # Update stats
                    wait_time = time.time() - start_time
                    self.stats.record_checkout(wait_time)
                    self.stats.current_idle = self._idle_connections.qsize()
                    self.stats.current_in_use = len(self._in_use_connections)
                    
                    return pooled.connection
                
                # Check if can create new connection
                current_size = len(self._all_connections)
                overflow_count = max(0, current_size - self.config.max_size)
                
                if current_size < self.config.max_size:
                    # Create within normal capacity
                    try:
                        pooled = await self._create_connection()
                        pooled.mark_used()
                        self._in_use_connections.add(pooled)
                        
                        wait_time = time.time() - start_time
                        self.stats.record_checkout(wait_time)
                        self.stats.current_in_use = len(self._in_use_connections)
                        
                        return pooled.connection
                        
                    except Exception as e:
                        logger.error(f"Failed to create connection: {e}")
                
                elif overflow_count < self.config.max_overflow:
                    # Create overflow connection
                    try:
                        pooled = await self._create_connection()
                        pooled.mark_used()
                        self._in_use_connections.add(pooled)
                        
                        self.stats.current_overflow = overflow_count + 1
                        wait_time = time.time() - start_time
                        self.stats.record_checkout(wait_time)
                        self.stats.current_in_use = len(self._in_use_connections)
                        
                        return pooled.connection
                        
                    except Exception as e:
                        logger.error(f"Failed to create overflow connection: {e}")
            
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                self.stats.total_timeouts += 1
                raise PoolExhaustedError(
                    f"Connection pool exhausted (timeout={timeout}s)"
                )
            
            # Wait for connection to become available
            remaining = timeout - elapsed
            async with self._not_empty:
                try:
                    await asyncio.wait_for(
                        self._not_empty.wait(),
                        timeout=min(remaining, 1.0)
                    )
                except asyncio.TimeoutError:
                    continue
    
    async def release(self, connection: T) -> None:
        """Release a connection back to the pool asynchronously."""
        async with self._lock:
            # Find pooled connection
            pooled = None
            for pc in self._in_use_connections:
                if pc.connection == connection:
                    pooled = pc
                    break
            
            if pooled is None:
                logger.warning("Attempted to release unknown connection")
                return
            
            # Remove from in-use set
            self._in_use_connections.remove(pooled)
            self.stats.total_returns += 1
            
            # Check if should destroy
            if (pooled.state == ConnectionState.INVALID or
                pooled.is_expired(self.config.max_lifetime)):
                await self._destroy_connection(pooled)
            else:
                # Return to idle pool
                pooled.mark_idle()
                await self._idle_connections.put(pooled)
            
            # Update stats
            self.stats.current_idle = self._idle_connections.qsize()
            self.stats.current_in_use = len(self._in_use_connections)
            
            # Check overflow
            current_size = len(self._all_connections)
            if current_size > self.config.max_size:
                self.stats.current_overflow = current_size - self.config.max_size
            else:
                self.stats.current_overflow = 0
        
        # Notify waiters
        async with self._not_empty:
            self._not_empty.notify()
    
    async def close_all(self) -> None:
        """Close all connections in the pool."""
        self._shutdown = True
        
        async with self._lock:
            # Close all connections
            for pooled in self._all_connections[:]:
                await self._destroy_connection(pooled)
            
            self._idle_connections = asyncio.Queue()
            self._in_use_connections.clear()
    
    @asynccontextmanager
    async def connection(self, timeout: Optional[float] = None):
        """
        Async context manager for connection checkout.
        
        Example:
            async with pool.connection() as conn:
                # Use connection
                pass
        """
        conn = await self.acquire(timeout)
        try:
            yield conn
        finally:
            await self.release(conn)