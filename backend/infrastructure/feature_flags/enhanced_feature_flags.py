"""
Enhanced feature flag service with percentage rollout and A/B testing support.

This module extends the basic feature flags with advanced capabilities for
gradual rollout, A/B testing, and per-use-case configuration.
"""

import os
import json
import hashlib
import logging
from typing import Dict, Any, Optional, List, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import random

from .feature_flags import FeatureFlags, FeatureFlagType

logger = logging.getLogger(__name__)


class RolloutStrategy(Enum):
    """Strategies for feature rollout."""
    
    PERCENTAGE = "percentage"  # Random percentage of users
    WHITELIST = "whitelist"    # Specific users/rooms
    RING = "ring"              # Deploy in rings (internal -> beta -> GA)
    TEMPORAL = "temporal"      # Time-based rollout
    CANARY = "canary"          # Specific servers/regions
    

@dataclass
class FlagConfig:
    """Configuration for a feature flag."""
    
    name: str
    description: str
    enabled: bool = False
    strategy: RolloutStrategy = RolloutStrategy.PERCENTAGE
    percentage: float = 0.0  # 0-100
    whitelist: List[str] = field(default_factory=list)
    blacklist: List[str] = field(default_factory=list)
    rings: Dict[str, float] = field(default_factory=dict)  # ring_name -> percentage
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "strategy": self.strategy.value,
            "percentage": self.percentage,
            "whitelist": self.whitelist,
            "blacklist": self.blacklist,
            "rings": self.rings,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FlagConfig":
        """Create from dictionary."""
        data = data.copy()
        if "strategy" in data:
            data["strategy"] = RolloutStrategy(data["strategy"])
        if "start_time" in data and data["start_time"]:
            data["start_time"] = datetime.fromisoformat(data["start_time"])
        if "end_time" in data and data["end_time"]:
            data["end_time"] = datetime.fromisoformat(data["end_time"])
        return cls(**data)


@dataclass
class ExperimentConfig:
    """Configuration for A/B experiments."""
    
    name: str
    description: str
    enabled: bool = True
    variants: Dict[str, float] = field(default_factory=dict)  # variant -> percentage
    metrics: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    min_sample_size: int = 1000
    
    def get_variant(self, user_id: str) -> str:
        """Get variant for a user."""
        if not self.enabled or not self.variants:
            return "control"
            
        # Use consistent hashing for user assignment
        hash_value = int(hashlib.md5(f"{self.name}:{user_id}".encode()).hexdigest(), 16)
        random_value = (hash_value % 10000) / 100.0  # 0-100
        
        cumulative = 0.0
        for variant, percentage in self.variants.items():
            cumulative += percentage
            if random_value < cumulative:
                return variant
                
        return "control"


class EnhancedFeatureFlags(FeatureFlags):
    """Enhanced feature flags with advanced rollout capabilities."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize enhanced feature flags."""
        super().__init__(config_file)
        
        # Additional storage for enhanced configs
        self._flag_configs: Dict[str, FlagConfig] = {}
        self._experiments: Dict[str, ExperimentConfig] = {}
        self._use_case_overrides: Dict[str, Dict[str, Any]] = {}
        self._evaluation_callbacks: Dict[str, List[Callable]] = {}
        
        # Load enhanced configuration
        self._load_enhanced_config()
        
    def _load_enhanced_config(self):
        """Load enhanced configuration from file or environment."""
        config_path = os.getenv("FEATURE_FLAGS_CONFIG", "feature_flags.json")
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    
                # Load flag configurations
                for flag_data in config.get("flags", []):
                    flag_config = FlagConfig.from_dict(flag_data)
                    self._flag_configs[flag_config.name] = flag_config
                    
                # Load experiments
                for exp_data in config.get("experiments", []):
                    exp_config = ExperimentConfig(**exp_data)
                    self._experiments[exp_config.name] = exp_config
                    
                # Load use case overrides
                self._use_case_overrides = config.get("use_case_overrides", {})
                
                logger.info(f"Loaded enhanced config: {len(self._flag_configs)} flags, {len(self._experiments)} experiments")
                
            except Exception as e:
                logger.error(f"Failed to load enhanced config: {e}")
                
    def is_enabled_advanced(
        self,
        flag_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Advanced feature flag evaluation with rollout strategies.
        
        Args:
            flag_name: Name of the feature flag
            context: Evaluation context with user/room/game info
            
        Returns:
            True if feature is enabled for this context
        """
        context = context or {}
        
        # Check for use-case specific overrides
        use_case = context.get("use_case")
        if use_case and use_case in self._use_case_overrides:
            override = self._use_case_overrides[use_case].get(flag_name)
            if override is not None:
                return override
                
        # Get flag configuration
        flag_config = self._flag_configs.get(flag_name)
        if not flag_config:
            # Fall back to basic evaluation
            return self.is_enabled(flag_name, context)
            
        # Check if globally disabled
        if not flag_config.enabled:
            return False
            
        # Check blacklist
        user_id = context.get("user_id") or context.get("player_id")
        if user_id and user_id in flag_config.blacklist:
            return False
            
        # Check whitelist
        if flag_config.whitelist:
            if user_id and user_id in flag_config.whitelist:
                return True
            room_id = context.get("room_id")
            if room_id and room_id in flag_config.whitelist:
                return True
            # Not in whitelist
            return False
            
        # Check temporal constraints
        now = datetime.utcnow()
        if flag_config.start_time and now < flag_config.start_time:
            return False
        if flag_config.end_time and now > flag_config.end_time:
            return False
            
        # Apply rollout strategy
        if flag_config.strategy == RolloutStrategy.PERCENTAGE:
            return self._evaluate_percentage(flag_config, context)
        elif flag_config.strategy == RolloutStrategy.RING:
            return self._evaluate_ring(flag_config, context)
        elif flag_config.strategy == RolloutStrategy.CANARY:
            return self._evaluate_canary(flag_config, context)
            
        return False
        
    def _evaluate_percentage(self, flag_config: FlagConfig, context: Dict[str, Any]) -> bool:
        """Evaluate percentage-based rollout."""
        if flag_config.percentage <= 0:
            return False
        if flag_config.percentage >= 100:
            return True
            
        # Use consistent hashing for stable assignment
        user_id = context.get("user_id") or context.get("player_id") or "anonymous"
        hash_input = f"{flag_config.name}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        # Convert to 0-100 range
        user_percentage = (hash_value % 10000) / 100.0
        
        return user_percentage < flag_config.percentage
        
    def _evaluate_ring(self, flag_config: FlagConfig, context: Dict[str, Any]) -> bool:
        """Evaluate ring-based rollout."""
        user_ring = context.get("ring", "ga")  # Default to general availability
        
        if user_ring not in flag_config.rings:
            return False
            
        ring_percentage = flag_config.rings[user_ring]
        
        # Use same percentage logic within ring
        temp_config = FlagConfig(
            name=flag_config.name,
            description=flag_config.description,
            enabled=True,
            percentage=ring_percentage
        )
        
        return self._evaluate_percentage(temp_config, context)
        
    def _evaluate_canary(self, flag_config: FlagConfig, context: Dict[str, Any]) -> bool:
        """Evaluate canary deployment."""
        server_id = context.get("server_id", os.getenv("SERVER_ID", "default"))
        canary_servers = flag_config.metadata.get("canary_servers", [])
        
        return server_id in canary_servers
        
    def get_experiment_variant(
        self,
        experiment_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Get experiment variant for A/B testing.
        
        Args:
            experiment_name: Name of the experiment
            context: Context with user information
            
        Returns:
            Variant name (e.g., "control", "variant_a")
        """
        experiment = self._experiments.get(experiment_name)
        if not experiment:
            return "control"
            
        user_id = context.get("user_id") or context.get("player_id", "anonymous")
        return experiment.get_variant(user_id)
        
    def set_flag_config(self, flag_config: FlagConfig):
        """Set or update a flag configuration."""
        self._flag_configs[flag_config.name] = flag_config
        
    def get_flag_config(self, flag_name: str) -> Optional[FlagConfig]:
        """Get flag configuration."""
        return self._flag_configs.get(flag_name)
        
    def set_use_case_override(
        self,
        use_case: str,
        flag_name: str,
        enabled: bool
    ):
        """Set a use-case specific override."""
        if use_case not in self._use_case_overrides:
            self._use_case_overrides[use_case] = {}
        self._use_case_overrides[use_case][flag_name] = enabled
        
    def get_all_flag_configs(self) -> Dict[str, FlagConfig]:
        """Get all flag configurations."""
        return self._flag_configs.copy()
        
    def get_evaluation_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a report of all flag evaluations for given context.
        
        Useful for debugging and testing.
        """
        report = {
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
            "flags": {},
            "experiments": {}
        }
        
        # Evaluate all flags
        for flag_name, flag_config in self._flag_configs.items():
            report["flags"][flag_name] = {
                "enabled": self.is_enabled_advanced(flag_name, context),
                "strategy": flag_config.strategy.value,
                "config": flag_config.to_dict()
            }
            
        # Evaluate all experiments
        for exp_name, exp_config in self._experiments.items():
            report["experiments"][exp_name] = {
                "variant": self.get_experiment_variant(exp_name, context),
                "config": {
                    "name": exp_config.name,
                    "variants": exp_config.variants,
                    "enabled": exp_config.enabled
                }
            }
            
        return report
        
    def register_evaluation_callback(
        self,
        flag_name: str,
        callback: Callable[[str, bool, Dict[str, Any]], None]
    ):
        """
        Register a callback for flag evaluation tracking.
        
        Useful for metrics and logging.
        """
        if flag_name not in self._evaluation_callbacks:
            self._evaluation_callbacks[flag_name] = []
        self._evaluation_callbacks[flag_name].append(callback)
        
    def save_config(self, path: Optional[str] = None):
        """Save current configuration to file."""
        path = path or os.getenv("FEATURE_FLAGS_CONFIG", "feature_flags.json")
        
        config = {
            "flags": [fc.to_dict() for fc in self._flag_configs.values()],
            "experiments": [
                {
                    "name": exp.name,
                    "description": exp.description,
                    "enabled": exp.enabled,
                    "variants": exp.variants,
                    "metrics": exp.metrics,
                    "start_time": exp.start_time.isoformat() if exp.start_time else None,
                    "end_time": exp.end_time.isoformat() if exp.end_time else None,
                    "min_sample_size": exp.min_sample_size
                }
                for exp in self._experiments.values()
            ],
            "use_case_overrides": self._use_case_overrides
        }
        
        with open(path, "w") as f:
            json.dump(config, f, indent=2)
            
        logger.info(f"Saved feature flag config to {path}")


# Convenience functions for state persistence flags
def create_state_persistence_flags() -> List[FlagConfig]:
    """Create standard state persistence feature flags."""
    return [
        FlagConfig(
            name="use_state_persistence",
            description="Enable state persistence system",
            enabled=True,
            strategy=RolloutStrategy.PERCENTAGE,
            percentage=0.0  # Start at 0%, increase gradually
        ),
        FlagConfig(
            name="enable_state_snapshots",
            description="Enable periodic state snapshots",
            enabled=True,
            strategy=RolloutStrategy.PERCENTAGE,
            percentage=0.0
        ),
        FlagConfig(
            name="enable_state_recovery",
            description="Enable automatic state recovery",
            enabled=True,
            strategy=RolloutStrategy.PERCENTAGE,
            percentage=0.0
        ),
        FlagConfig(
            name="use_state_persistence_startgame",
            description="Enable state persistence for StartGameUseCase",
            enabled=True,
            strategy=RolloutStrategy.RING,
            rings={"internal": 100.0, "beta": 50.0, "ga": 0.0}
        ),
        FlagConfig(
            name="use_state_persistence_playturn",
            description="Enable state persistence for PlayTurnUseCase",
            enabled=True,
            strategy=RolloutStrategy.RING,
            rings={"internal": 100.0, "beta": 50.0, "ga": 0.0}
        ),
    ]


# Global enhanced feature flags instance
_enhanced_flags: Optional[EnhancedFeatureFlags] = None


def get_enhanced_feature_flags() -> EnhancedFeatureFlags:
    """Get the global enhanced feature flags instance."""
    global _enhanced_flags
    if _enhanced_flags is None:
        _enhanced_flags = EnhancedFeatureFlags()
    return _enhanced_flags