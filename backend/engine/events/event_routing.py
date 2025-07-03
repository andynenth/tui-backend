# backend/engine/events/event_routing.py

import asyncio
import logging
from typing import Dict, List, Set, Optional, Callable, Any, Pattern
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime, timedelta

from .event_types import GameEvent, EventType, EventPriority
from .event_handlers import IEventHandler

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Event routing strategies."""
    BROADCAST = "broadcast"  # Send to all matching handlers
    ROUND_ROBIN = "round_robin"  # Send to handlers in rotation
    PRIORITY = "priority"  # Send to highest priority handler first
    RANDOM = "random"  # Send to random matching handler
    FIRST_MATCH = "first_match"  # Send to first matching handler


@dataclass
class RoutingRule:
    """
    🎯 **Routing Rule** - Defines how events are routed to handlers
    
    Configurable routing rules with pattern matching and conditions.
    """
    
    # Rule identification
    name: str
    priority: int = 0
    enabled: bool = True
    
    # Event matching criteria
    event_types: Optional[Set[EventType]] = None
    event_pattern: Optional[Pattern] = None
    room_filter: Optional[str] = None
    player_filter: Optional[str] = None
    
    # Routing configuration
    strategy: RoutingStrategy = RoutingStrategy.BROADCAST
    target_handlers: Optional[Set[str]] = None
    exclude_handlers: Optional[Set[str]] = None
    
    # Conditions
    conditions: List[Callable[[GameEvent], bool]] = field(default_factory=list)
    
    # Rate limiting
    max_events_per_second: Optional[float] = None
    max_events_per_minute: Optional[int] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_matched: Optional[datetime] = None
    match_count: int = 0
    
    def matches(self, event: GameEvent) -> bool:
        """Check if this rule matches the given event."""
        try:
            # Check event type filter
            if self.event_types and event.event_type not in self.event_types:
                return False
            
            # Check event pattern
            if self.event_pattern and not self.event_pattern.match(event.event_type.value):
                return False
            
            # Check room filter
            if self.room_filter and event.room_id != self.room_filter:
                return False
            
            # Check player filter
            if self.player_filter and event.player_id != self.player_filter:
                return False
            
            # Check custom conditions
            for condition in self.conditions:
                if not condition(event):
                    return False
            
            # Check rate limiting
            if not self._check_rate_limits():
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ RULE_ERROR: Error checking rule {self.name}: {str(e)}")
            return False
    
    def _check_rate_limits(self) -> bool:
        """Check if rate limits allow processing."""
        now = datetime.now()
        
        # Check per-second limit
        if self.max_events_per_second:
            if self.last_matched:
                time_diff = (now - self.last_matched).total_seconds()
                if time_diff < (1.0 / self.max_events_per_second):
                    return False
        
        # Check per-minute limit would need more sophisticated tracking
        # For now, we'll use a simple approximation
        if self.max_events_per_minute:
            # This is a simplified check - in production, you'd want
            # a sliding window counter
            pass
        
        return True
    
    def record_match(self):
        """Record that this rule matched an event."""
        self.match_count += 1
        self.last_matched = datetime.now()


class EventRouter:
    """
    🎯 **Event Router** - Intelligent event routing system
    
    Routes events to appropriate handlers based on configurable rules,
    patterns, and conditions with support for multiple routing strategies.
    """
    
    def __init__(self):
        self.routing_rules: List[RoutingRule] = []
        self.handler_registry: Dict[str, IEventHandler] = {}
        self.handler_rotation: Dict[str, int] = {}  # For round-robin
        self.routing_stats: Dict[str, Dict[str, Any]] = {}
        self.default_strategy = RoutingStrategy.BROADCAST
        
    def add_rule(self, rule: RoutingRule):
        """Add a routing rule."""
        self.routing_rules.append(rule)
        
        # Sort rules by priority (highest first)
        self.routing_rules.sort(key=lambda r: r.priority, reverse=True)
        
        # Initialize stats
        self.routing_stats[rule.name] = {
            "matches": 0,
            "last_match": None,
            "handlers_used": set(),
            "errors": 0
        }
        
        logger.info(f"📋 RULE_ADDED: {rule.name} (priority: {rule.priority})")
    
    def remove_rule(self, name: str):
        """Remove a routing rule by name."""
        self.routing_rules = [r for r in self.routing_rules if r.name != name]
        
        if name in self.routing_stats:
            del self.routing_stats[name]
        
        logger.info(f"📋 RULE_REMOVED: {name}")
    
    def register_handler(self, name: str, handler: IEventHandler):
        """Register a named handler for routing."""
        self.handler_registry[name] = handler
        logger.debug(f"📝 HANDLER_REGISTERED: {name}")
    
    def unregister_handler(self, name: str):
        """Unregister a handler."""
        if name in self.handler_registry:
            del self.handler_registry[name]
            logger.debug(f"📝 HANDLER_UNREGISTERED: {name}")
    
    async def route_event(self, event: GameEvent, available_handlers: List[IEventHandler]) -> List[IEventHandler]:
        """
        Route an event to appropriate handlers based on routing rules.
        
        Args:
            event: The event to route
            available_handlers: List of available handlers
            
        Returns:
            List of handlers that should process the event
        """
        try:
            # Find matching rules
            matching_rules = self._find_matching_rules(event)
            
            if not matching_rules:
                # No specific rules, use default strategy
                return self._apply_default_routing(event, available_handlers)
            
            # Apply the highest priority matching rule
            primary_rule = matching_rules[0]
            handlers = await self._apply_rule(primary_rule, event, available_handlers)
            
            # Record rule usage
            primary_rule.record_match()
            self._update_routing_stats(primary_rule, handlers)
            
            logger.debug(f"📋 RULE_APPLIED: {primary_rule.name} -> {len(handlers)} handlers")
            return handlers
            
        except Exception as e:
            logger.error(f"❌ ROUTING_ERROR: Failed to route event {event.event_id}: {str(e)}")
            # Fallback to default routing
            return self._apply_default_routing(event, available_handlers)
    
    def _find_matching_rules(self, event: GameEvent) -> List[RoutingRule]:
        """Find all rules that match the event."""
        matching_rules = []
        
        for rule in self.routing_rules:
            if rule.enabled and rule.matches(event):
                matching_rules.append(rule)
        
        return matching_rules
    
    async def _apply_rule(self, rule: RoutingRule, event: GameEvent, available_handlers: List[IEventHandler]) -> List[IEventHandler]:
        """Apply a specific routing rule."""
        # Filter handlers based on rule criteria
        filtered_handlers = self._filter_handlers(rule, available_handlers)
        
        if not filtered_handlers:
            logger.warning(f"⚠️ NO_HANDLERS: No handlers available for rule {rule.name}")
            return []
        
        # Apply routing strategy
        if rule.strategy == RoutingStrategy.BROADCAST:
            return filtered_handlers
        
        elif rule.strategy == RoutingStrategy.ROUND_ROBIN:
            return self._round_robin_select(rule.name, filtered_handlers)
        
        elif rule.strategy == RoutingStrategy.PRIORITY:
            return self._priority_select(filtered_handlers)
        
        elif rule.strategy == RoutingStrategy.RANDOM:
            return self._random_select(filtered_handlers)
        
        elif rule.strategy == RoutingStrategy.FIRST_MATCH:
            return [filtered_handlers[0]]
        
        else:
            logger.warning(f"⚠️ UNKNOWN_STRATEGY: {rule.strategy} for rule {rule.name}")
            return filtered_handlers
    
    def _filter_handlers(self, rule: RoutingRule, handlers: List[IEventHandler]) -> List[IEventHandler]:
        """Filter handlers based on rule criteria."""
        filtered = []
        
        for handler in handlers:
            handler_name = handler.get_handler_name()
            
            # Check target handlers filter
            if rule.target_handlers and handler_name not in rule.target_handlers:
                continue
            
            # Check exclude handlers filter
            if rule.exclude_handlers and handler_name in rule.exclude_handlers:
                continue
            
            filtered.append(handler)
        
        return filtered
    
    def _round_robin_select(self, rule_name: str, handlers: List[IEventHandler]) -> List[IEventHandler]:
        """Select handler using round-robin strategy."""
        if not handlers:
            return []
        
        # Get or initialize rotation index
        if rule_name not in self.handler_rotation:
            self.handler_rotation[rule_name] = 0
        
        # Select next handler
        index = self.handler_rotation[rule_name]
        selected_handler = handlers[index % len(handlers)]
        
        # Update rotation
        self.handler_rotation[rule_name] = (index + 1) % len(handlers)
        
        return [selected_handler]
    
    def _priority_select(self, handlers: List[IEventHandler]) -> List[IEventHandler]:
        """Select handler based on priority (if handlers have priority)."""
        # For now, just return the first handler
        # In a more sophisticated implementation, handlers would have priority attributes
        return [handlers[0]] if handlers else []
    
    def _random_select(self, handlers: List[IEventHandler]) -> List[IEventHandler]:
        """Select random handler."""
        if not handlers:
            return []
        
        import random
        return [random.choice(handlers)]
    
    def _apply_default_routing(self, event: GameEvent, available_handlers: List[IEventHandler]) -> List[IEventHandler]:
        """Apply default routing strategy."""
        if self.default_strategy == RoutingStrategy.BROADCAST:
            return available_handlers
        else:
            return self._apply_rule(
                RoutingRule(name="default", strategy=self.default_strategy),
                event,
                available_handlers
            )
    
    def _update_routing_stats(self, rule: RoutingRule, handlers: List[IEventHandler]):
        """Update routing statistics."""
        if rule.name in self.routing_stats:
            stats = self.routing_stats[rule.name]
            stats["matches"] += 1
            stats["last_match"] = datetime.now()
            stats["handlers_used"].update(h.get_handler_name() for h in handlers)
    
    def get_routing_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get routing statistics."""
        return self.routing_stats.copy()
    
    def get_rule_stats(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific rule."""
        return self.routing_stats.get(rule_name)
    
    def clear_stats(self):
        """Clear all routing statistics."""
        for stats in self.routing_stats.values():
            stats["matches"] = 0
            stats["last_match"] = None
            stats["handlers_used"] = set()
            stats["errors"] = 0


# Utility functions for creating common routing rules

def create_event_type_rule(
    name: str,
    event_types: Set[EventType],
    strategy: RoutingStrategy = RoutingStrategy.BROADCAST,
    priority: int = 0
) -> RoutingRule:
    """Create a rule that routes specific event types."""
    return RoutingRule(
        name=name,
        event_types=event_types,
        strategy=strategy,
        priority=priority
    )


def create_room_rule(
    name: str,
    room_id: str,
    strategy: RoutingStrategy = RoutingStrategy.BROADCAST,
    priority: int = 0
) -> RoutingRule:
    """Create a rule that routes events for a specific room."""
    return RoutingRule(
        name=name,
        room_filter=room_id,
        strategy=strategy,
        priority=priority
    )


def create_player_rule(
    name: str,
    player_id: str,
    strategy: RoutingStrategy = RoutingStrategy.BROADCAST,
    priority: int = 0
) -> RoutingRule:
    """Create a rule that routes events for a specific player."""
    return RoutingRule(
        name=name,
        player_filter=player_id,
        strategy=strategy,
        priority=priority
    )


def create_pattern_rule(
    name: str,
    pattern: str,
    strategy: RoutingStrategy = RoutingStrategy.BROADCAST,
    priority: int = 0
) -> RoutingRule:
    """Create a rule that routes events matching a regex pattern."""
    return RoutingRule(
        name=name,
        event_pattern=re.compile(pattern),
        strategy=strategy,
        priority=priority
    )


def create_priority_rule(
    name: str,
    event_priority: EventPriority,
    strategy: RoutingStrategy = RoutingStrategy.PRIORITY,
    priority: int = 0
) -> RoutingRule:
    """Create a rule that routes events based on priority."""
    
    def priority_condition(event: GameEvent) -> bool:
        return event.priority == event_priority
    
    return RoutingRule(
        name=name,
        conditions=[priority_condition],
        strategy=strategy,
        priority=priority
    )


def create_conditional_rule(
    name: str,
    condition: Callable[[GameEvent], bool],
    strategy: RoutingStrategy = RoutingStrategy.BROADCAST,
    priority: int = 0
) -> RoutingRule:
    """Create a rule with a custom condition."""
    return RoutingRule(
        name=name,
        conditions=[condition],
        strategy=strategy,
        priority=priority
    )


def create_rate_limited_rule(
    name: str,
    event_types: Set[EventType],
    max_per_second: float,
    strategy: RoutingStrategy = RoutingStrategy.BROADCAST,
    priority: int = 0
) -> RoutingRule:
    """Create a rate-limited routing rule."""
    return RoutingRule(
        name=name,
        event_types=event_types,
        max_events_per_second=max_per_second,
        strategy=strategy,
        priority=priority
    )