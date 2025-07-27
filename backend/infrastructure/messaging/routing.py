"""
Message routing system for directing messages to appropriate queues.

Provides flexible routing patterns for message distribution.
"""

import re
import fnmatch
from typing import Dict, List, Optional, Callable, Set, Tuple, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging
import asyncio

from .base import (
    Message,
    IMessageRouter,
    IMessageQueue,
    T
)


logger = logging.getLogger(__name__)


@dataclass
class RoutePattern:
    """Pattern for message routing."""
    pattern: str
    destinations: Set[str] = field(default_factory=set)
    filter_func: Optional[Callable[[Message[Any]], bool]] = None
    metadata_filters: Dict[str, Any] = field(default_factory=dict)
    priority_threshold: Optional[int] = None
    
    def matches(self, routing_key: str, message: Message[Any]) -> bool:
        """Check if pattern matches routing key and message."""
        # Check pattern match
        if not self._pattern_matches(routing_key):
            return False
        
        # Check filter function
        if self.filter_func and not self.filter_func(message):
            return False
        
        # Check metadata filters
        for key, value in self.metadata_filters.items():
            msg_value = message.metadata.headers.get(key)
            if msg_value != value:
                return False
        
        # Check priority threshold
        if self.priority_threshold is not None:
            if message.priority.value < self.priority_threshold:
                return False
        
        return True
    
    def _pattern_matches(self, routing_key: str) -> bool:
        """Check if pattern matches routing key."""
        # Override in subclasses for different pattern types
        return fnmatch.fnmatch(routing_key, self.pattern)


class MessageRouter(IMessageRouter):
    """
    Base message router implementation.
    
    Features:
    - Pattern-based routing
    - Multiple destinations
    - Filter functions
    - Route management
    """
    
    def __init__(self, name: str = "router"):
        """Initialize message router."""
        self.name = name
        self._routes: Dict[str, RoutePattern] = {}
        self._queues: Dict[str, IMessageQueue[Any]] = {}
        self._lock = asyncio.Lock()
        self._stats = {
            'routed': 0,
            'unroutable': 0,
            'by_destination': {}
        }
    
    def register_queue(self, name: str, queue: IMessageQueue[Any]) -> None:
        """Register a queue for routing."""
        self._queues[name] = queue
    
    async def route(
        self,
        message: Message[Any],
        routing_key: Optional[str] = None
    ) -> List[str]:
        """Route message to destinations."""
        async with self._lock:
            # Use default routing key if not provided
            if routing_key is None:
                routing_key = message.metadata.destination or "*"
            
            destinations = set()
            
            # Find matching routes
            for pattern in self._routes.values():
                if pattern.matches(routing_key, message):
                    destinations.update(pattern.destinations)
            
            # Route to destinations
            routed_to = []
            for dest_name in destinations:
                queue = self._queues.get(dest_name)
                if queue:
                    try:
                        await queue.enqueue(message)
                        routed_to.append(dest_name)
                        
                        # Update stats
                        self._stats['by_destination'][dest_name] = \
                            self._stats['by_destination'].get(dest_name, 0) + 1
                    except Exception as e:
                        logger.error(f"Failed to route to {dest_name}: {e}")
            
            if routed_to:
                self._stats['routed'] += 1
            else:
                self._stats['unroutable'] += 1
                logger.warning(f"No route found for key: {routing_key}")
            
            return routed_to
    
    def register_route(
        self,
        pattern: str,
        destination: str,
        filter_func: Optional[Callable[[Message[Any]], bool]] = None
    ) -> None:
        """Register a routing rule."""
        if pattern not in self._routes:
            self._routes[pattern] = RoutePattern(pattern)
        
        route = self._routes[pattern]
        route.destinations.add(destination)
        
        if filter_func:
            # Combine with existing filter
            existing_filter = route.filter_func
            if existing_filter:
                route.filter_func = lambda msg: existing_filter(msg) and filter_func(msg)
            else:
                route.filter_func = filter_func
    
    def unregister_route(
        self,
        pattern: str,
        destination: Optional[str] = None
    ) -> bool:
        """Unregister routing rule."""
        if pattern not in self._routes:
            return False
        
        if destination:
            # Remove specific destination
            self._routes[pattern].destinations.discard(destination)
            
            # Remove pattern if no destinations left
            if not self._routes[pattern].destinations:
                del self._routes[pattern]
        else:
            # Remove entire pattern
            del self._routes[pattern]
        
        return True
    
    def get_routes(self) -> Dict[str, List[str]]:
        """Get all registered routes."""
        return {
            pattern: list(route.destinations)
            for pattern, route in self._routes.items()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        return {
            **self._stats,
            'total_routes': len(self._routes),
            'total_queues': len(self._queues)
        }


class TopicRouter(MessageRouter):
    """
    Topic-based message router.
    
    Uses dot-separated topic patterns like MQTT.
    Examples: "game.room.created", "player.*.joined"
    """
    
    def __init__(self, name: str = "topic_router"):
        """Initialize topic router."""
        super().__init__(name)
    
    def register_route(
        self,
        pattern: str,
        destination: str,
        filter_func: Optional[Callable[[Message[Any]], bool]] = None
    ) -> None:
        """Register topic-based route."""
        # Convert wildcard patterns
        # * matches single level, # matches multiple levels
        regex_pattern = pattern.replace('.', '\\.')
        regex_pattern = regex_pattern.replace('*', '[^.]+')
        regex_pattern = regex_pattern.replace('#', '.*')
        regex_pattern = f"^{regex_pattern}$"
        
        if pattern not in self._routes:
            self._routes[pattern] = TopicRoutePattern(pattern, regex_pattern)
        
        route = self._routes[pattern]
        route.destinations.add(destination)
        
        if filter_func:
            existing_filter = route.filter_func
            if existing_filter:
                route.filter_func = lambda msg: existing_filter(msg) and filter_func(msg)
            else:
                route.filter_func = filter_func


class TopicRoutePattern(RoutePattern):
    """Route pattern for topic-based routing."""
    
    def __init__(self, pattern: str, regex_pattern: str):
        """Initialize topic route pattern."""
        super().__init__(pattern)
        self.regex = re.compile(regex_pattern)
    
    def _pattern_matches(self, routing_key: str) -> bool:
        """Check if topic pattern matches."""
        return bool(self.regex.match(routing_key))


class DirectRouter(MessageRouter):
    """
    Direct routing to exact queue names.
    
    No pattern matching, just direct queue mapping.
    """
    
    async def route(
        self,
        message: Message[Any],
        routing_key: Optional[str] = None
    ) -> List[str]:
        """Route directly to named queue."""
        async with self._lock:
            # Use routing key as queue name
            queue_name = routing_key or message.metadata.destination
            
            if not queue_name:
                self._stats['unroutable'] += 1
                return []
            
            queue = self._queues.get(queue_name)
            if queue:
                try:
                    await queue.enqueue(message)
                    self._stats['routed'] += 1
                    self._stats['by_destination'][queue_name] = \
                        self._stats['by_destination'].get(queue_name, 0) + 1
                    return [queue_name]
                except Exception as e:
                    logger.error(f"Failed to route to {queue_name}: {e}")
            
            self._stats['unroutable'] += 1
            return []


class PatternRouter(MessageRouter):
    """
    Pattern-based router with multiple matching strategies.
    
    Supports:
    - Glob patterns (*.txt, data/*)
    - Regex patterns
    - Custom matchers
    """
    
    def __init__(self, name: str = "pattern_router"):
        """Initialize pattern router."""
        super().__init__(name)
        self._pattern_types: Dict[str, str] = {}  # pattern -> type
    
    def register_glob_route(
        self,
        pattern: str,
        destination: str,
        filter_func: Optional[Callable[[Message[Any]], bool]] = None
    ) -> None:
        """Register glob pattern route."""
        self._pattern_types[pattern] = "glob"
        super().register_route(pattern, destination, filter_func)
    
    def register_regex_route(
        self,
        pattern: str,
        destination: str,
        filter_func: Optional[Callable[[Message[Any]], bool]] = None
    ) -> None:
        """Register regex pattern route."""
        self._pattern_types[pattern] = "regex"
        
        if pattern not in self._routes:
            self._routes[pattern] = RegexRoutePattern(pattern)
        
        route = self._routes[pattern]
        route.destinations.add(destination)
        
        if filter_func:
            existing_filter = route.filter_func
            if existing_filter:
                route.filter_func = lambda msg: existing_filter(msg) and filter_func(msg)
            else:
                route.filter_func = filter_func


class RegexRoutePattern(RoutePattern):
    """Route pattern using regular expressions."""
    
    def __init__(self, pattern: str):
        """Initialize regex route pattern."""
        super().__init__(pattern)
        self.regex = re.compile(pattern)
    
    def _pattern_matches(self, routing_key: str) -> bool:
        """Check if regex pattern matches."""
        return bool(self.regex.match(routing_key))


class ContentBasedRouter(MessageRouter):
    """
    Routes messages based on content inspection.
    
    Examines message payload and metadata for routing decisions.
    """
    
    def __init__(self, name: str = "content_router"):
        """Initialize content-based router."""
        super().__init__(name)
        self._content_rules: List[ContentRule] = []
    
    def add_content_rule(
        self,
        rule_func: Callable[[Message[Any]], Optional[str]],
        priority: int = 0
    ) -> None:
        """
        Add content-based routing rule.
        
        Args:
            rule_func: Function that returns destination or None
            priority: Rule priority (higher evaluated first)
        """
        self._content_rules.append(ContentRule(rule_func, priority))
        self._content_rules.sort(key=lambda r: r.priority, reverse=True)
    
    async def route(
        self,
        message: Message[Any],
        routing_key: Optional[str] = None
    ) -> List[str]:
        """Route based on content inspection."""
        async with self._lock:
            # Try content rules first
            for rule in self._content_rules:
                destination = rule.func(message)
                if destination:
                    queue = self._queues.get(destination)
                    if queue:
                        try:
                            await queue.enqueue(message)
                            self._stats['routed'] += 1
                            self._stats['by_destination'][destination] = \
                                self._stats['by_destination'].get(destination, 0) + 1
                            return [destination]
                        except Exception as e:
                            logger.error(f"Failed to route to {destination}: {e}")
            
            # Fall back to pattern routing
            return await super().route(message, routing_key)


@dataclass
class ContentRule:
    """Content-based routing rule."""
    func: Callable[[Message[Any]], Optional[str]]
    priority: int