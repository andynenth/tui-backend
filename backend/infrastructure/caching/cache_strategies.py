"""
Cache invalidation strategies and warming capabilities.

This module provides sophisticated cache management strategies for
maintaining cache consistency and performance.
"""

import asyncio
from typing import Dict, Any, List, Set, Optional, Callable, TypeVar
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import re

from .base import ICache, ITaggedCache, CacheKeyBuilder


T = TypeVar('T')


class InvalidationStrategy(Enum):
    """Types of cache invalidation strategies."""
    IMMEDIATE = "immediate"      # Invalidate immediately
    DELAYED = "delayed"          # Invalidate after delay
    SCHEDULED = "scheduled"      # Invalidate at specific time
    CASCADE = "cascade"          # Invalidate related entries
    PATTERN = "pattern"          # Invalidate by key pattern


@dataclass
class InvalidationRule:
    """Defines a cache invalidation rule."""
    event_type: str
    strategy: InvalidationStrategy
    key_pattern: Optional[str] = None
    tags: Optional[Set[str]] = None
    delay: Optional[timedelta] = None
    cascade_rules: Optional[List['InvalidationRule']] = None
    condition: Optional[Callable[[Any], bool]] = None


class SmartInvalidator:
    """
    Advanced cache invalidation with multiple strategies.
    
    Supports:
    - Event-driven invalidation
    - Pattern-based invalidation
    - Tag-based invalidation
    - Cascading invalidation
    - Conditional invalidation
    """
    
    def __init__(self, cache: ICache, key_builder: Optional[CacheKeyBuilder] = None):
        self.cache = cache
        self.key_builder = key_builder or CacheKeyBuilder()
        self._rules: Dict[str, List[InvalidationRule]] = {}
        self._scheduled_invalidations: List[Tuple[datetime, str]] = []
        self._invalidation_task: Optional[asyncio.Task] = None
        
        # Metrics
        self._metrics = {
            'rules_triggered': 0,
            'keys_invalidated': 0,
            'patterns_matched': 0,
            'cascades_executed': 0
        }
    
    def add_rule(self, rule: InvalidationRule) -> None:
        """Add an invalidation rule."""
        if rule.event_type not in self._rules:
            self._rules[rule.event_type] = []
        self._rules[rule.event_type].append(rule)
    
    async def start(self) -> None:
        """Start background tasks."""
        if not self._invalidation_task:
            self._invalidation_task = asyncio.create_task(self._scheduled_worker())
    
    async def stop(self) -> None:
        """Stop background tasks."""
        if self._invalidation_task:
            self._invalidation_task.cancel()
            try:
                await self._invalidation_task
            except asyncio.CancelledError:
                pass
    
    async def handle_event(self, event_type: str, event_data: Any) -> int:
        """
        Handle an event and perform invalidations.
        
        Returns number of keys invalidated.
        """
        rules = self._rules.get(event_type, [])
        total_invalidated = 0
        
        for rule in rules:
            # Check condition
            if rule.condition and not rule.condition(event_data):
                continue
            
            self._metrics['rules_triggered'] += 1
            
            # Execute based on strategy
            if rule.strategy == InvalidationStrategy.IMMEDIATE:
                invalidated = await self._immediate_invalidation(rule, event_data)
                total_invalidated += invalidated
                
            elif rule.strategy == InvalidationStrategy.DELAYED:
                await self._delayed_invalidation(rule, event_data)
                
            elif rule.strategy == InvalidationStrategy.SCHEDULED:
                await self._scheduled_invalidation(rule, event_data)
                
            elif rule.strategy == InvalidationStrategy.CASCADE:
                invalidated = await self._cascade_invalidation(rule, event_data)
                total_invalidated += invalidated
                
            elif rule.strategy == InvalidationStrategy.PATTERN:
                invalidated = await self._pattern_invalidation(rule, event_data)
                total_invalidated += invalidated
        
        self._metrics['keys_invalidated'] += total_invalidated
        return total_invalidated
    
    async def _immediate_invalidation(
        self,
        rule: InvalidationRule,
        event_data: Any
    ) -> int:
        """Perform immediate invalidation."""
        keys_to_invalidate = set()
        
        # Key pattern invalidation
        if rule.key_pattern:
            pattern_keys = self._extract_keys_from_pattern(rule.key_pattern, event_data)
            keys_to_invalidate.update(pattern_keys)
        
        # Tag-based invalidation
        if rule.tags and isinstance(self.cache, ITaggedCache):
            for tag in rule.tags:
                tag_formatted = self._format_tag(tag, event_data)
                tagged_data = await self.cache.get_by_tag(tag_formatted)
                keys_to_invalidate.update(tagged_data.keys())
        
        # Perform invalidation
        invalidated = 0
        for key in keys_to_invalidate:
            if await self.cache.delete(key):
                invalidated += 1
        
        return invalidated
    
    async def _delayed_invalidation(
        self,
        rule: InvalidationRule,
        event_data: Any
    ) -> None:
        """Schedule delayed invalidation."""
        if not rule.delay:
            return
        
        async def delayed_task():
            await asyncio.sleep(rule.delay.total_seconds())
            await self._immediate_invalidation(rule, event_data)
        
        asyncio.create_task(delayed_task())
    
    async def _scheduled_invalidation(
        self,
        rule: InvalidationRule,
        event_data: Any
    ) -> None:
        """Schedule invalidation at specific time."""
        # Extract schedule time from event data
        schedule_time = event_data.get('invalidate_at')
        if isinstance(schedule_time, str):
            schedule_time = datetime.fromisoformat(schedule_time)
        
        if schedule_time:
            key_pattern = self._format_pattern(rule.key_pattern, event_data)
            self._scheduled_invalidations.append((schedule_time, key_pattern))
    
    async def _cascade_invalidation(
        self,
        rule: InvalidationRule,
        event_data: Any
    ) -> int:
        """Perform cascading invalidation."""
        self._metrics['cascades_executed'] += 1
        
        # First invalidate this rule
        total = await self._immediate_invalidation(rule, event_data)
        
        # Then cascade to related rules
        if rule.cascade_rules:
            for cascade_rule in rule.cascade_rules:
                # Create synthetic event for cascade
                cascade_event = {
                    **event_data,
                    'cascade_from': rule.event_type
                }
                invalidated = await self._immediate_invalidation(cascade_rule, cascade_event)
                total += invalidated
        
        return total
    
    async def _pattern_invalidation(
        self,
        rule: InvalidationRule,
        event_data: Any
    ) -> int:
        """Invalidate by key pattern matching."""
        if not rule.key_pattern:
            return 0
        
        pattern = self._format_pattern(rule.key_pattern, event_data)
        regex = self._pattern_to_regex(pattern)
        
        # Get all keys and match pattern
        # Note: This is inefficient for large caches
        # In production, use cache backend that supports pattern operations
        all_keys = await self.cache.list_keys() if hasattr(self.cache, 'list_keys') else []
        
        invalidated = 0
        for key in all_keys:
            if regex.match(key):
                if await self.cache.delete(key):
                    invalidated += 1
                    self._metrics['patterns_matched'] += 1
        
        return invalidated
    
    async def _scheduled_worker(self) -> None:
        """Background worker for scheduled invalidations."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                now = datetime.utcnow()
                due_invalidations = []
                remaining = []
                
                for schedule_time, pattern in self._scheduled_invalidations:
                    if schedule_time <= now:
                        due_invalidations.append(pattern)
                    else:
                        remaining.append((schedule_time, pattern))
                
                self._scheduled_invalidations = remaining
                
                # Process due invalidations
                for pattern in due_invalidations:
                    rule = InvalidationRule(
                        event_type="scheduled",
                        strategy=InvalidationStrategy.PATTERN,
                        key_pattern=pattern
                    )
                    await self._pattern_invalidation(rule, {})
                
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(5)
    
    def _extract_keys_from_pattern(self, pattern: str, data: Any) -> List[str]:
        """Extract cache keys from pattern and data."""
        formatted = self._format_pattern(pattern, data)
        # If pattern contains wildcards, return empty (use pattern matching instead)
        if '*' in formatted or '?' in formatted:
            return []
        return [formatted]
    
    def _format_pattern(self, pattern: str, data: Any) -> str:
        """Format pattern with data values."""
        # Replace {field} with values from data
        def replacer(match):
            field = match.group(1)
            value = self._get_nested_value(data, field)
            return str(value) if value is not None else ''
        
        return re.sub(r'\{(\w+(?:\.\w+)*)\}', replacer, pattern)
    
    def _format_tag(self, tag: str, data: Any) -> str:
        """Format tag with data values."""
        return self._format_pattern(tag, data)
    
    def _pattern_to_regex(self, pattern: str) -> re.Pattern:
        """Convert glob pattern to regex."""
        # Escape special regex chars except * and ?
        pattern = re.escape(pattern)
        # Convert glob wildcards to regex
        pattern = pattern.replace(r'\*', '.*').replace(r'\?', '.')
        return re.compile(f'^{pattern}$')
    
    def _get_nested_value(self, data: Any, path: str) -> Any:
        """Get nested value from data using dot notation."""
        parts = path.split('.')
        value = data
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
            
            if value is None:
                return None
        
        return value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get invalidation metrics."""
        return dict(self._metrics)


class CacheWarmer:
    """
    Sophisticated cache warming strategies.
    
    Pre-loads cache with frequently accessed data to improve performance.
    """
    
    def __init__(self, cache: ICache):
        self.cache = cache
        self._warm_up_tasks: List[WarmUpTask] = []
        self._warming_task: Optional[asyncio.Task] = None
        
        # Metrics
        self._metrics = {
            'warm_ups_executed': 0,
            'entries_warmed': 0,
            'warm_up_errors': 0,
            'last_warm_up': None
        }
    
    def add_task(
        self,
        name: str,
        loader: Callable,
        schedule: Optional[timedelta] = None,
        priority: int = 0,
        depends_on: Optional[List[str]] = None
    ) -> None:
        """
        Add a warm-up task.
        
        Args:
            name: Task name
            loader: Async function that loads data
            schedule: How often to run (None = only on startup)
            priority: Higher priority tasks run first
            depends_on: List of task names this depends on
        """
        task = WarmUpTask(
            name=name,
            loader=loader,
            schedule=schedule,
            priority=priority,
            depends_on=depends_on or []
        )
        self._warm_up_tasks.append(task)
        
        # Sort by priority
        self._warm_up_tasks.sort(key=lambda t: t.priority, reverse=True)
    
    async def start(self) -> None:
        """Start warming process."""
        # Initial warm-up
        await self.warm_up()
        
        # Start scheduled warming
        if not self._warming_task:
            self._warming_task = asyncio.create_task(self._warming_worker())
    
    async def stop(self) -> None:
        """Stop warming process."""
        if self._warming_task:
            self._warming_task.cancel()
            try:
                await self._warming_task
            except asyncio.CancelledError:
                pass
    
    async def warm_up(self) -> Dict[str, Any]:
        """
        Execute warm-up tasks respecting dependencies.
        
        Returns summary of warming results.
        """
        self._metrics['warm_ups_executed'] += 1
        self._metrics['last_warm_up'] = datetime.utcnow()
        
        results = {
            'tasks_executed': 0,
            'entries_loaded': 0,
            'errors': [],
            'task_results': {}
        }
        
        # Build dependency graph
        completed = set()
        
        while len(completed) < len(self._warm_up_tasks):
            made_progress = False
            
            for task in self._warm_up_tasks:
                if task.name in completed:
                    continue
                
                # Check dependencies
                if all(dep in completed for dep in task.depends_on):
                    # Execute task
                    try:
                        entries = await task.loader(self.cache)
                        completed.add(task.name)
                        made_progress = True
                        
                        results['tasks_executed'] += 1
                        results['entries_loaded'] += entries
                        results['task_results'][task.name] = {
                            'status': 'success',
                            'entries': entries
                        }
                        
                        self._metrics['entries_warmed'] += entries
                        
                    except Exception as e:
                        self._metrics['warm_up_errors'] += 1
                        results['errors'].append({
                            'task': task.name,
                            'error': str(e)
                        })
                        results['task_results'][task.name] = {
                            'status': 'error',
                            'error': str(e)
                        }
                        
                        # Mark as completed to avoid blocking dependents
                        completed.add(task.name)
                        made_progress = True
            
            if not made_progress:
                # Circular dependency or error
                break
        
        return results
    
    async def _warming_worker(self) -> None:
        """Background worker for scheduled warming."""
        # Calculate next run times
        next_runs: Dict[str, datetime] = {}
        now = datetime.utcnow()
        
        for task in self._warm_up_tasks:
            if task.schedule:
                next_runs[task.name] = now + task.schedule
        
        while True:
            try:
                # Sleep until next task
                if next_runs:
                    next_time = min(next_runs.values())
                    sleep_time = (next_time - datetime.utcnow()).total_seconds()
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)
                else:
                    # No scheduled tasks
                    await asyncio.sleep(3600)
                    continue
                
                # Find due tasks
                now = datetime.utcnow()
                due_tasks = [
                    task for task in self._warm_up_tasks
                    if task.name in next_runs and next_runs[task.name] <= now
                ]
                
                # Execute due tasks
                for task in due_tasks:
                    try:
                        entries = await task.loader(self.cache)
                        self._metrics['entries_warmed'] += entries
                        
                        # Schedule next run
                        if task.schedule:
                            next_runs[task.name] = now + task.schedule
                            
                    except Exception:
                        self._metrics['warm_up_errors'] += 1
                
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(60)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get warming metrics."""
        return dict(self._metrics)


@dataclass
class WarmUpTask:
    """Represents a cache warm-up task."""
    name: str
    loader: Callable
    schedule: Optional[timedelta]
    priority: int
    depends_on: List[str]


# Pre-built warming strategies

async def warm_frequently_accessed(
    cache: ICache,
    access_log: List[str],
    data_source: Callable,
    top_n: int = 100
) -> int:
    """
    Warm cache with most frequently accessed keys.
    
    Args:
        cache: Cache to warm
        access_log: List of accessed keys
        data_source: Function to load data
        top_n: Number of top keys to warm
        
    Returns:
        Number of entries warmed
    """
    from collections import Counter
    
    # Find most frequent keys
    key_counts = Counter(access_log)
    top_keys = [key for key, _ in key_counts.most_common(top_n)]
    
    # Load and cache
    warmed = 0
    for key in top_keys:
        try:
            value = await data_source(key)
            if value is not None:
                await cache.set(key, value)
                warmed += 1
        except Exception:
            pass
    
    return warmed


async def warm_by_pattern(
    cache: ICache,
    pattern: str,
    data_source: Callable,
    key_generator: Callable
) -> int:
    """
    Warm cache for keys matching a pattern.
    
    Args:
        cache: Cache to warm
        pattern: Pattern for keys to warm
        data_source: Function to load data
        key_generator: Function to generate keys from pattern
        
    Returns:
        Number of entries warmed
    """
    # Generate keys
    keys = key_generator(pattern)
    
    # Load and cache
    warmed = 0
    for key in keys:
        try:
            value = await data_source(key)
            if value is not None:
                await cache.set(key, value)
                warmed += 1
        except Exception:
            pass
    
    return warmed