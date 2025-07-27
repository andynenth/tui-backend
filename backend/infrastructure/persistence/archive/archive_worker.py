"""
Async archival worker for hybrid persistence.

Handles background archival of completed games with batching and monitoring.
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import logging
from collections import defaultdict
from enum import Enum
import time


from .archive_strategy import (
    ArchivalPolicy, ArchivalRequest, ArchivalResult,
    ArchivalTrigger, ArchivalPriority, ArchivalStrategy,
    IArchivalBackend
)


logger = logging.getLogger(__name__)


class WorkerState(Enum):
    """States of the archival worker."""
    IDLE = "idle"
    PROCESSING = "processing"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class WorkerMetrics:
    """Metrics for archival worker performance."""
    total_processed: int = 0
    total_succeeded: int = 0
    total_failed: int = 0
    total_batches: int = 0
    
    processing_time_total: float = 0.0
    processing_time_max: float = 0.0
    queue_size_current: int = 0
    queue_size_max: int = 0
    
    last_batch_time: Optional[datetime] = None
    last_error_time: Optional[datetime] = None
    last_error_message: Optional[str] = None
    
    by_entity_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_priority: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    def record_batch(self, size: int, duration: float, succeeded: int, failed: int):
        """Record batch processing metrics."""
        self.total_batches += 1
        self.total_processed += size
        self.total_succeeded += succeeded
        self.total_failed += failed
        
        self.processing_time_total += duration
        self.processing_time_max = max(self.processing_time_max, duration)
        self.last_batch_time = datetime.utcnow()
    
    def record_error(self, error: str):
        """Record error information."""
        self.last_error_time = datetime.utcnow()
        self.last_error_message = error
    
    def get_success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_processed == 0:
            return 0.0
        return self.total_succeeded / self.total_processed
    
    def get_average_batch_time(self) -> float:
        """Calculate average batch processing time."""
        if self.total_batches == 0:
            return 0.0
        return self.processing_time_total / self.total_batches


class ArchivalWorker:
    """
    Background worker for processing archival requests.
    
    Features:
    - Async processing with configurable concurrency
    - Request batching for efficiency
    - Priority-based processing
    - Automatic retries with backoff
    - Memory pressure handling
    - Comprehensive metrics
    """
    
    def __init__(
        self,
        strategy: ArchivalStrategy,
        policies: Dict[str, ArchivalPolicy],
        max_queue_size: int = 10000,
        batch_timeout: timedelta = timedelta(seconds=5),
        max_retries: int = 3,
        retry_delay: timedelta = timedelta(seconds=30)
    ):
        """
        Initialize archival worker.
        
        Args:
            strategy: Archival strategy to use
            policies: Policies by entity type
            max_queue_size: Maximum queue size before blocking
            batch_timeout: Maximum time to wait for batch
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay
        """
        self.strategy = strategy
        self.policies = policies
        self.max_queue_size = max_queue_size
        self.batch_timeout = batch_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Queues by priority
        self._queues: Dict[ArchivalPriority, asyncio.Queue] = {
            priority: asyncio.Queue(maxsize=max_queue_size // 4)
            for priority in ArchivalPriority
        }
        
        # Failed requests for retry
        self._retry_queue: asyncio.Queue = asyncio.Queue()
        self._retry_counts: Dict[str, int] = {}
        
        # State management
        self._state = WorkerState.IDLE
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        # Metrics
        self.metrics = WorkerMetrics()
        
        # Memory pressure handling
        self._memory_pressure = False
        self._last_memory_check = datetime.utcnow()
    
    async def start(self) -> None:
        """Start the archival worker."""
        if self._running:
            logger.warning("Archival worker already running")
            return
        
        logger.info("Starting archival worker")
        self._running = True
        self._state = WorkerState.IDLE
        
        # Start worker tasks
        self._tasks = [
            asyncio.create_task(self._process_loop()),
            asyncio.create_task(self._retry_loop()),
            asyncio.create_task(self._monitor_loop())
        ]
    
    async def stop(self, timeout: float = 30.0) -> None:
        """Stop the archival worker gracefully."""
        if not self._running:
            return
        
        logger.info("Stopping archival worker")
        self._state = WorkerState.STOPPING
        self._running = False
        
        # Wait for tasks to complete
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._tasks, return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for worker tasks to complete")
            # Cancel remaining tasks
            for task in self._tasks:
                if not task.done():
                    task.cancel()
        
        self._state = WorkerState.STOPPED
        logger.info("Archival worker stopped")
    
    async def submit(self, request: ArchivalRequest) -> bool:
        """
        Submit an archival request.
        
        Args:
            request: Archival request to process
            
        Returns:
            True if accepted, False if queue is full
        """
        # Check queue capacity
        queue = self._queues[request.priority]
        
        if queue.full():
            logger.warning(
                f"Archival queue full for priority {request.priority.name}, "
                f"rejecting request for {request.entity_id}"
            )
            return False
        
        # Add to appropriate queue
        await queue.put(request)
        
        # Update metrics
        self.metrics.queue_size_current = sum(q.qsize() for q in self._queues.values())
        self.metrics.queue_size_max = max(
            self.metrics.queue_size_max,
            self.metrics.queue_size_current
        )
        
        return True
    
    async def _process_loop(self) -> None:
        """Main processing loop."""
        while self._running:
            try:
                # Collect batch of requests
                batch = await self._collect_batch()
                
                if batch:
                    self._state = WorkerState.PROCESSING
                    await self._process_batch(batch)
                else:
                    self._state = WorkerState.IDLE
                    # No requests, wait a bit
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error in archival worker: {e}")
                self.metrics.record_error(str(e))
                await asyncio.sleep(1)  # Brief pause on error
    
    async def _collect_batch(self) -> List[ArchivalRequest]:
        """Collect a batch of requests to process."""
        batch = []
        batch_start = asyncio.get_event_loop().time()
        timeout = self.batch_timeout.total_seconds()
        
        # Process queues by priority
        for priority in sorted(ArchivalPriority, key=lambda p: p.value, reverse=True):
            queue = self._queues[priority]
            
            # Get policy for batch size
            # Use the first policy's batch_size as default
            batch_size = next(iter(self.policies.values())).batch_size
            
            # Collect from this priority queue
            while len(batch) < batch_size:
                try:
                    # Calculate remaining timeout
                    elapsed = asyncio.get_event_loop().time() - batch_start
                    remaining = max(0, timeout - elapsed)
                    
                    if remaining <= 0:
                        break
                    
                    # Try to get request with timeout
                    request = await asyncio.wait_for(
                        queue.get(),
                        timeout=min(remaining, 0.1)  # Check every 100ms
                    )
                    batch.append(request)
                    
                    # Update metrics
                    self.metrics.by_priority[priority.name] += 1
                    self.metrics.by_entity_type[request.entity_type] += 1
                    
                except asyncio.TimeoutError:
                    # No more requests in this queue
                    break
            
            if len(batch) >= batch_size:
                break
        
        # Update queue size metric
        self.metrics.queue_size_current = sum(q.qsize() for q in self._queues.values())
        
        return batch
    
    async def _process_batch(self, batch: List[ArchivalRequest]) -> None:
        """Process a batch of archival requests."""
        start_time = asyncio.get_event_loop().time()
        succeeded = 0
        failed = 0
        
        # Group by entity type for policy lookup
        by_type = defaultdict(list)
        for request in batch:
            by_type[request.entity_type].append(request)
        
        # Process each type group with appropriate policy
        for entity_type, requests in by_type.items():
            policy = self.policies.get(entity_type)
            if not policy:
                logger.warning(f"No policy found for entity type: {entity_type}")
                failed += len(requests)
                continue
            
            # Process concurrently up to policy limit
            semaphore = asyncio.Semaphore(policy.max_concurrent_archives)
            
            async def process_with_limit(req: ArchivalRequest):
                async with semaphore:
                    return await self._process_request(req, policy)
            
            # Process all requests for this type
            results = await asyncio.gather(
                *[process_with_limit(req) for req in requests],
                return_exceptions=True
            )
            
            # Count results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Exception processing request: {result}")
                    failed += 1
                    # Add to retry queue
                    await self._add_to_retry(requests[i])
                elif isinstance(result, ArchivalResult):
                    if result.success:
                        succeeded += 1
                    else:
                        failed += 1
                        # Add to retry queue
                        await self._add_to_retry(requests[i])
        
        # Record metrics
        duration = asyncio.get_event_loop().time() - start_time
        self.metrics.record_batch(len(batch), duration, succeeded, failed)
        
        logger.info(
            f"Processed archival batch: {len(batch)} requests, "
            f"{succeeded} succeeded, {failed} failed in {duration:.2f}s"
        )
    
    async def _process_request(
        self,
        request: ArchivalRequest,
        policy: ArchivalPolicy
    ) -> ArchivalResult:
        """Process a single archival request."""
        try:
            # Apply timeout from policy
            result = await asyncio.wait_for(
                self.strategy.archive_entity(request, policy),
                timeout=policy.archive_timeout.total_seconds()
            )
            
            if result.success:
                logger.debug(
                    f"Successfully archived {request.entity_id} to {result.archive_location}"
                )
                # Remove from retry tracking
                self._retry_counts.pop(request.entity_id, None)
            else:
                logger.warning(
                    f"Failed to archive {request.entity_id}: {result.error}"
                )
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(
                f"Timeout archiving {request.entity_id} after "
                f"{policy.archive_timeout.total_seconds()}s"
            )
            return ArchivalResult(
                entity_id=request.entity_id,
                entity_type=request.entity_type,
                success=False,
                error="Archive timeout"
            )
        except Exception as e:
            logger.error(f"Error archiving {request.entity_id}: {e}")
            return ArchivalResult(
                entity_id=request.entity_id,
                entity_type=request.entity_type,
                success=False,
                error=str(e)
            )
    
    async def _add_to_retry(self, request: ArchivalRequest) -> None:
        """Add request to retry queue if retry limit not exceeded."""
        retry_count = self._retry_counts.get(request.entity_id, 0)
        
        if retry_count < self.max_retries:
            self._retry_counts[request.entity_id] = retry_count + 1
            await self._retry_queue.put((datetime.utcnow(), request))
            logger.info(
                f"Added {request.entity_id} to retry queue "
                f"(attempt {retry_count + 1}/{self.max_retries})"
            )
        else:
            logger.error(
                f"Max retries exceeded for {request.entity_id}, "
                "archival request dropped"
            )
            self._retry_counts.pop(request.entity_id, None)
    
    async def _retry_loop(self) -> None:
        """Process retry queue with exponential backoff."""
        while self._running:
            try:
                # Get next retry item
                retry_time, request = await asyncio.wait_for(
                    self._retry_queue.get(),
                    timeout=5.0
                )
                
                # Calculate backoff delay
                retry_count = self._retry_counts.get(request.entity_id, 1)
                delay = self.retry_delay.total_seconds() * (2 ** (retry_count - 1))
                
                # Wait until retry time
                wait_until = retry_time + timedelta(seconds=delay)
                wait_seconds = (wait_until - datetime.utcnow()).total_seconds()
                
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)
                
                # Resubmit with high priority
                request.priority = ArchivalPriority.HIGH
                await self.submit(request)
                
            except asyncio.TimeoutError:
                # No retries pending
                continue
            except Exception as e:
                logger.error(f"Error in retry loop: {e}")
                await asyncio.sleep(1)
    
    async def _monitor_loop(self) -> None:
        """Monitor system health and adjust behavior."""
        while self._running:
            try:
                # Check memory pressure
                await self._check_memory_pressure()
                
                # Log metrics periodically
                if self.metrics.total_batches > 0 and self.metrics.total_batches % 100 == 0:
                    logger.info(
                        f"Archival worker stats: "
                        f"processed={self.metrics.total_processed}, "
                        f"success_rate={self.metrics.get_success_rate():.2%}, "
                        f"avg_batch_time={self.metrics.get_average_batch_time():.2f}s, "
                        f"queue_size={self.metrics.queue_size_current}"
                    )
                
                # Sleep for monitoring interval
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(5)
    
    async def _check_memory_pressure(self) -> None:
        """Check system memory and trigger archival if needed."""
        # Only check every minute
        if (datetime.utcnow() - self._last_memory_check) < timedelta(minutes=1):
            return
        
        self._last_memory_check = datetime.utcnow()
        
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            # Check if memory usage is high
            for policy in self.policies.values():
                if memory.percent > policy.memory_threshold_percent:
                    self._memory_pressure = True
                    logger.warning(
                        f"Memory pressure detected: {memory.percent}% used, "
                        f"threshold: {policy.memory_threshold_percent}%"
                    )
                    # Could trigger immediate archival here
                    break
            else:
                self._memory_pressure = False
                
        except ImportError:
            # psutil not available
            pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get current worker status."""
        return {
            'state': self._state.value,
            'running': self._running,
            'memory_pressure': self._memory_pressure,
            'queue_sizes': {
                priority.name: self._queues[priority].qsize()
                for priority in ArchivalPriority
            },
            'retry_queue_size': self._retry_queue.qsize(),
            'metrics': {
                'total_processed': self.metrics.total_processed,
                'success_rate': self.metrics.get_success_rate(),
                'queue_size_current': self.metrics.queue_size_current,
                'last_batch_time': self.metrics.last_batch_time.isoformat()
                    if self.metrics.last_batch_time else None,
                'by_entity_type': dict(self.metrics.by_entity_type),
                'by_priority': dict(self.metrics.by_priority)
            }
        }