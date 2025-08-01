"""
Load balancer configuration for traffic splitting.

This module provides load balancer management for gradual traffic
migration between blue/green environments during state persistence rollout.
"""

import os
import json
import asyncio
import aiohttp
import random
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class TrafficStrategy(Enum):
    """Traffic distribution strategies."""
    
    PERCENTAGE = "percentage"      # Random percentage split
    CANARY = "canary"             # Specific users/features
    GRADUAL = "gradual"           # Time-based gradual shift
    STICKY = "sticky"             # Session-based routing
    WEIGHTED = "weighted"         # Weighted round-robin


@dataclass
class BackendConfig:
    """Configuration for a backend server."""
    
    name: str
    url: str
    weight: float = 1.0
    health_check_url: Optional[str] = None
    max_connections: int = 1000
    timeout_seconds: int = 30
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    
    # Runtime state
    active_connections: int = 0
    failed_requests: int = 0
    circuit_breaker_open: bool = False
    circuit_breaker_opened_at: Optional[datetime] = None
    
    @property
    def is_healthy(self) -> bool:
        """Check if backend is healthy."""
        if self.circuit_breaker_open:
            # Check if circuit breaker timeout has passed
            if self.circuit_breaker_opened_at:
                elapsed = (datetime.utcnow() - self.circuit_breaker_opened_at).seconds
                if elapsed > self.circuit_breaker_timeout:
                    # Reset circuit breaker
                    self.circuit_breaker_open = False
                    self.circuit_breaker_opened_at = None
                    self.failed_requests = 0
                    return True
            return False
        return True
        
    def record_failure(self):
        """Record a failed request."""
        self.failed_requests += 1
        
        if self.failed_requests >= self.circuit_breaker_threshold:
            self.circuit_breaker_open = True
            self.circuit_breaker_opened_at = datetime.utcnow()
            logger.warning(f"Circuit breaker opened for {self.name}")
            
    def record_success(self):
        """Record a successful request."""
        if self.failed_requests > 0:
            self.failed_requests = max(0, self.failed_requests - 1)


@dataclass
class TrafficRule:
    """Rule for traffic routing."""
    
    name: str
    strategy: TrafficStrategy
    backends: Dict[str, float] = field(default_factory=dict)  # backend -> percentage
    conditions: Dict[str, Any] = field(default_factory=dict)
    sticky_sessions: bool = False
    gradual_shift_minutes: int = 60
    start_time: Optional[datetime] = None
    
    def matches(self, context: Dict[str, Any]) -> bool:
        """Check if rule matches the request context."""
        for key, value in self.conditions.items():
            if key not in context:
                return False
                
            if isinstance(value, list):
                if context[key] not in value:
                    return False
            else:
                if context[key] != value:
                    return False
                    
        return True
        
    def get_backend_weights(self) -> Dict[str, float]:
        """Get current backend weights based on strategy."""
        if self.strategy == TrafficStrategy.GRADUAL and self.start_time:
            # Calculate gradual shift
            elapsed = (datetime.utcnow() - self.start_time).total_seconds() / 60
            progress = min(1.0, elapsed / self.gradual_shift_minutes)
            
            # Assume shifting from first to second backend
            backends = list(self.backends.keys())
            if len(backends) >= 2:
                weights = {}
                weights[backends[0]] = 100 * (1 - progress)
                weights[backends[1]] = 100 * progress
                return weights
                
        return self.backends


class LoadBalancer:
    """Load balancer for traffic distribution."""
    
    def __init__(self, config_file: str = "load_balancer_config.json"):
        """Initialize load balancer."""
        self.config_file = config_file
        self.backends: Dict[str, BackendConfig] = {}
        self.rules: List[TrafficRule] = []
        self.default_backend: Optional[str] = None
        self.session_affinity: Dict[str, str] = {}  # session_id -> backend
        self._stats: Dict[str, Dict[str, int]] = {}  # backend -> metric -> count
        
        self._load_config()
        
    def _load_config(self):
        """Load load balancer configuration."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    
                # Load backends
                for backend_data in config.get("backends", []):
                    backend = BackendConfig(**backend_data)
                    self.backends[backend.name] = backend
                    
                # Load rules
                for rule_data in config.get("rules", []):
                    rule = TrafficRule(
                        name=rule_data["name"],
                        strategy=TrafficStrategy(rule_data["strategy"]),
                        backends=rule_data.get("backends", {}),
                        conditions=rule_data.get("conditions", {}),
                        sticky_sessions=rule_data.get("sticky_sessions", False),
                        gradual_shift_minutes=rule_data.get("gradual_shift_minutes", 60)
                    )
                    if "start_time" in rule_data:
                        rule.start_time = datetime.fromisoformat(rule_data["start_time"])
                    self.rules.append(rule)
                    
                self.default_backend = config.get("default_backend")
                
                logger.info(f"Loaded {len(self.backends)} backends and {len(self.rules)} rules")
                
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                
    def _save_config(self):
        """Save load balancer configuration."""
        config = {
            "backends": [
                {
                    "name": backend.name,
                    "url": backend.url,
                    "weight": backend.weight,
                    "health_check_url": backend.health_check_url,
                    "max_connections": backend.max_connections,
                    "timeout_seconds": backend.timeout_seconds
                }
                for backend in self.backends.values()
            ],
            "rules": [
                {
                    "name": rule.name,
                    "strategy": rule.strategy.value,
                    "backends": rule.backends,
                    "conditions": rule.conditions,
                    "sticky_sessions": rule.sticky_sessions,
                    "gradual_shift_minutes": rule.gradual_shift_minutes,
                    "start_time": rule.start_time.isoformat() if rule.start_time else None
                }
                for rule in self.rules
            ],
            "default_backend": self.default_backend
        }
        
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)
            
    def add_backend(self, backend: BackendConfig):
        """Add a backend server."""
        self.backends[backend.name] = backend
        self._save_config()
        logger.info(f"Added backend: {backend.name}")
        
    def remove_backend(self, name: str):
        """Remove a backend server."""
        if name in self.backends:
            del self.backends[name]
            self._save_config()
            logger.info(f"Removed backend: {name}")
            
    def add_rule(self, rule: TrafficRule):
        """Add a traffic rule."""
        self.rules.append(rule)
        self._save_config()
        logger.info(f"Added rule: {rule.name}")
        
    async def route_request(self, context: Dict[str, Any]) -> Optional[BackendConfig]:
        """
        Route a request to appropriate backend.
        
        Args:
            context: Request context (user_id, session_id, etc.)
            
        Returns:
            Selected backend or None
        """
        # Check session affinity first
        session_id = context.get("session_id")
        if session_id and session_id in self.session_affinity:
            backend_name = self.session_affinity[session_id]
            backend = self.backends.get(backend_name)
            if backend and backend.is_healthy:
                return backend
                
        # Find matching rule
        for rule in self.rules:
            if rule.matches(context):
                backend = await self._select_backend_by_rule(rule, context)
                if backend:
                    # Store session affinity if needed
                    if rule.sticky_sessions and session_id:
                        self.session_affinity[session_id] = backend.name
                    return backend
                    
        # Use default backend
        if self.default_backend:
            backend = self.backends.get(self.default_backend)
            if backend and backend.is_healthy:
                return backend
                
        # Fallback to any healthy backend
        for backend in self.backends.values():
            if backend.is_healthy:
                return backend
                
        return None
        
    async def _select_backend_by_rule(
        self,
        rule: TrafficRule,
        context: Dict[str, Any]
    ) -> Optional[BackendConfig]:
        """Select backend based on rule."""
        weights = rule.get_backend_weights()
        
        if rule.strategy == TrafficStrategy.PERCENTAGE:
            return self._select_by_percentage(weights, context)
        elif rule.strategy == TrafficStrategy.CANARY:
            return self._select_by_canary(weights, context)
        elif rule.strategy == TrafficStrategy.WEIGHTED:
            return self._select_by_weighted_round_robin(weights)
        elif rule.strategy in [TrafficStrategy.GRADUAL, TrafficStrategy.STICKY]:
            return self._select_by_percentage(weights, context)
            
        return None
        
    def _select_by_percentage(
        self,
        weights: Dict[str, float],
        context: Dict[str, Any]
    ) -> Optional[BackendConfig]:
        """Select backend by percentage distribution."""
        # Use consistent hashing for stable assignment
        user_id = context.get("user_id", "anonymous")
        hash_input = f"{user_id}:{datetime.utcnow().date()}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        random_value = (hash_value % 10000) / 100.0  # 0-100
        
        cumulative = 0.0
        for backend_name, percentage in weights.items():
            cumulative += percentage
            if random_value < cumulative:
                backend = self.backends.get(backend_name)
                if backend and backend.is_healthy:
                    return backend
                    
        return None
        
    def _select_by_canary(
        self,
        weights: Dict[str, float],
        context: Dict[str, Any]
    ) -> Optional[BackendConfig]:
        """Select backend for canary deployment."""
        # Check if user is in canary group
        user_id = context.get("user_id")
        if not user_id:
            return None
            
        # Use feature flag or user attribute
        is_canary = context.get("canary", False)
        
        if is_canary:
            # Route to canary backend (typically the new version)
            for backend_name in weights:
                if "canary" in backend_name.lower() or "green" in backend_name.lower():
                    backend = self.backends.get(backend_name)
                    if backend and backend.is_healthy:
                        return backend
                        
        # Route to stable backend
        for backend_name in weights:
            if "stable" in backend_name.lower() or "blue" in backend_name.lower():
                backend = self.backends.get(backend_name)
                if backend and backend.is_healthy:
                    return backend
                    
        return None
        
    def _select_by_weighted_round_robin(
        self,
        weights: Dict[str, float]
    ) -> Optional[BackendConfig]:
        """Select backend using weighted round-robin."""
        # Simple weighted random selection
        total_weight = sum(weights.values())
        if total_weight == 0:
            return None
            
        rand = random.uniform(0, total_weight)
        cumulative = 0.0
        
        for backend_name, weight in weights.items():
            cumulative += weight
            if rand <= cumulative:
                backend = self.backends.get(backend_name)
                if backend and backend.is_healthy:
                    return backend
                    
        return None
        
    async def health_check_all(self) -> Dict[str, bool]:
        """Run health checks on all backends."""
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for name, backend in self.backends.items():
                if backend.health_check_url:
                    try:
                        async with session.get(
                            backend.health_check_url,
                            timeout=5
                        ) as response:
                            results[name] = response.status == 200
                            
                            if response.status == 200:
                                backend.record_success()
                            else:
                                backend.record_failure()
                                
                    except Exception as e:
                        logger.error(f"Health check failed for {name}: {e}")
                        results[name] = False
                        backend.record_failure()
                else:
                    results[name] = backend.is_healthy
                    
        return results
        
    def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics."""
        stats = {
            "backends": {},
            "rules": len(self.rules),
            "active_sessions": len(self.session_affinity)
        }
        
        for name, backend in self.backends.items():
            stats["backends"][name] = {
                "healthy": backend.is_healthy,
                "weight": backend.weight,
                "active_connections": backend.active_connections,
                "failed_requests": backend.failed_requests,
                "circuit_breaker_open": backend.circuit_breaker_open
            }
            
        return stats
        
    def update_traffic_split(
        self,
        rule_name: str,
        new_weights: Dict[str, float]
    ):
        """Update traffic split for a rule."""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.backends = new_weights
                self._save_config()
                logger.info(f"Updated traffic split for rule '{rule_name}'")
                return
                
        logger.error(f"Rule '{rule_name}' not found")
        
    def start_gradual_shift(
        self,
        from_backend: str,
        to_backend: str,
        duration_minutes: int = 60
    ):
        """Start gradual traffic shift between backends."""
        rule = TrafficRule(
            name=f"gradual_shift_{datetime.utcnow().timestamp()}",
            strategy=TrafficStrategy.GRADUAL,
            backends={from_backend: 100.0, to_backend: 0.0},
            gradual_shift_minutes=duration_minutes,
            start_time=datetime.utcnow()
        )
        
        self.add_rule(rule)
        logger.info(f"Started gradual shift from {from_backend} to {to_backend} over {duration_minutes} minutes")


# Convenience functions for common patterns
def create_blue_green_load_balancer(
    blue_url: str = "http://localhost:8001",
    green_url: str = "http://localhost:8002"
) -> LoadBalancer:
    """Create load balancer for blue/green deployment."""
    lb = LoadBalancer()
    
    # Add backends
    lb.add_backend(BackendConfig(
        name="blue",
        url=blue_url,
        health_check_url=f"{blue_url}/health"
    ))
    
    lb.add_backend(BackendConfig(
        name="green",
        url=green_url,
        health_check_url=f"{green_url}/health"
    ))
    
    # Default all traffic to blue
    lb.add_rule(TrafficRule(
        name="default",
        strategy=TrafficStrategy.PERCENTAGE,
        backends={"blue": 100.0, "green": 0.0}
    ))
    
    lb.default_backend = "blue"
    
    return lb


def create_canary_load_balancer(
    stable_url: str,
    canary_url: str,
    canary_percentage: float = 5.0
) -> LoadBalancer:
    """Create load balancer for canary deployment."""
    lb = LoadBalancer()
    
    # Add backends
    lb.add_backend(BackendConfig(
        name="stable",
        url=stable_url,
        health_check_url=f"{stable_url}/health"
    ))
    
    lb.add_backend(BackendConfig(
        name="canary",
        url=canary_url,
        health_check_url=f"{canary_url}/health"
    ))
    
    # Canary rule for specific users
    lb.add_rule(TrafficRule(
        name="canary_users",
        strategy=TrafficStrategy.CANARY,
        backends={"stable": 100.0 - canary_percentage, "canary": canary_percentage},
        conditions={"canary": True}
    ))
    
    # Default rule
    lb.add_rule(TrafficRule(
        name="default",
        strategy=TrafficStrategy.PERCENTAGE,
        backends={"stable": 100.0 - canary_percentage, "canary": canary_percentage}
    ))
    
    return lb


async def perform_gradual_traffic_shift(
    lb: LoadBalancer,
    from_backend: str,
    to_backend: str,
    duration_minutes: int,
    health_check_interval: int = 60
) -> bool:
    """
    Perform gradual traffic shift with health monitoring.
    
    Args:
        lb: Load balancer instance
        from_backend: Source backend name
        to_backend: Target backend name
        duration_minutes: Duration of shift
        health_check_interval: Health check interval in seconds
        
    Returns:
        True if successful
    """
    # Start gradual shift
    lb.start_gradual_shift(from_backend, to_backend, duration_minutes)
    
    # Monitor health during shift
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    while datetime.utcnow() < end_time:
        # Run health checks
        health_results = await lb.health_check_all()
        
        # Check if target backend is healthy
        if not health_results.get(to_backend, False):
            logger.error(f"Target backend {to_backend} is unhealthy, stopping shift")
            return False
            
        # Log progress
        elapsed = (datetime.utcnow() - start_time).total_seconds() / 60
        progress = min(100, (elapsed / duration_minutes) * 100)
        logger.info(f"Traffic shift progress: {progress:.1f}%")
        
        # Sleep until next check
        await asyncio.sleep(health_check_interval)
        
    logger.info("Traffic shift completed successfully")
    return True