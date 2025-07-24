"""
Shadow Mode Infrastructure
Runs both current and refactored systems in parallel to compare behavior.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from tests.contracts.golden_master import GoldenMasterComparator


logger = logging.getLogger(__name__)


class ShadowModeState(Enum):
    """Shadow mode operational states"""
    DISABLED = "disabled"
    MONITORING = "monitoring"  # Log differences but use current system
    VALIDATING = "validating"  # Fail requests if differences detected
    MIGRATING = "migrating"   # Gradually shift traffic to new system
    

@dataclass
class ShadowComparison:
    """Result of comparing shadow responses"""
    request_id: str
    timestamp: datetime
    message: Dict[str, Any]
    current_response: Optional[Dict[str, Any]]
    shadow_response: Optional[Dict[str, Any]]
    current_broadcasts: List[Dict[str, Any]] = field(default_factory=list)
    shadow_broadcasts: List[Dict[str, Any]] = field(default_factory=list)
    current_duration_ms: float = 0.0
    shadow_duration_ms: float = 0.0
    differences: List[Dict[str, Any]] = field(default_factory=list)
    match: bool = True
    error: Optional[str] = None


class ShadowModeConfig:
    """Configuration for shadow mode operation"""
    
    def __init__(self):
        self.state = ShadowModeState.DISABLED
        self.sample_rate = 1.0  # Percentage of requests to shadow (0.0-1.0)
        self.timeout_ms = 5000  # Max time to wait for shadow response
        self.ignore_fields = ["timestamp", "server_time", "request_id"]
        self.fail_on_mismatch = False  # Whether to fail requests on mismatch
        self.log_mismatches = True
        self.metrics_enabled = True
        self.comparison_storage_enabled = True
        self.max_stored_comparisons = 10000
        

class ShadowModeOrchestrator:
    """Orchestrates shadow mode operations"""
    
    def __init__(self, config: Optional[ShadowModeConfig] = None):
        self.config = config or ShadowModeConfig()
        self.comparator = GoldenMasterComparator(
            ignore_fields=self.config.ignore_fields
        )
        self.current_handler: Optional[Callable] = None
        self.shadow_handler: Optional[Callable] = None
        self.comparisons: List[ShadowComparison] = []
        self.metrics = ShadowModeMetrics()
        
    def configure(self, 
                  current_handler: Callable,
                  shadow_handler: Optional[Callable] = None,
                  state: ShadowModeState = ShadowModeState.MONITORING):
        """Configure shadow mode handlers"""
        self.current_handler = current_handler
        self.shadow_handler = shadow_handler
        self.config.state = state
        
        logger.info(f"Shadow mode configured: state={state.value}")
        
    async def handle_message(self, 
                           websocket,
                           message: Dict[str, Any],
                           room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle message with shadow mode logic"""
        request_id = f"{message.get('action', 'unknown')}_{int(time.time() * 1000)}"
        
        # Always run current system
        current_task = asyncio.create_task(
            self._run_handler(self.current_handler, websocket, message, room_state, "current")
        )
        
        # Conditionally run shadow system
        shadow_task = None
        if self._should_shadow(message):
            shadow_task = asyncio.create_task(
                self._run_handler(self.shadow_handler, websocket, message, room_state, "shadow")
            )
            
        # Wait for current system
        current_result = await current_task
        
        # If shadowing, wait for shadow result and compare
        if shadow_task:
            try:
                # Wait with timeout
                shadow_result = await asyncio.wait_for(
                    shadow_task,
                    timeout=self.config.timeout_ms / 1000
                )
                
                # Compare results
                comparison = await self._compare_results(
                    request_id, message, current_result, shadow_result
                )
                
                # Handle comparison based on mode
                await self._handle_comparison(comparison)
                
            except asyncio.TimeoutError:
                logger.warning(f"Shadow timeout for {request_id}")
                self.metrics.record_timeout()
                
        # Always return current system response
        return current_result["response"]
    
    def _should_shadow(self, message: Dict[str, Any]) -> bool:
        """Determine if request should be shadowed"""
        if self.config.state == ShadowModeState.DISABLED:
            return False
            
        if not self.shadow_handler:
            return False
            
        # Sample based on configured rate
        import random
        return random.random() < self.config.sample_rate
        
    async def _run_handler(self,
                          handler: Callable,
                          websocket,
                          message: Dict[str, Any],
                          room_state: Optional[Dict[str, Any]],
                          handler_name: str) -> Dict[str, Any]:
        """Run a handler and capture response/broadcasts"""
        start_time = time.time()
        broadcasts = []
        response = None
        error = None
        
        # Mock broadcast function to capture broadcasts
        async def capture_broadcast(room_id: str, event: str, data: Dict[str, Any]):
            broadcasts.append({
                "room_id": room_id,
                "event": event,
                "data": data
            })
            
        try:
            # Run handler
            # This assumes handler interface - adjust as needed
            response = await handler(websocket, message, room_state, capture_broadcast)
        except Exception as e:
            error = str(e)
            logger.error(f"Handler {handler_name} error: {e}")
            
        duration_ms = (time.time() - start_time) * 1000
        
        return {
            "response": response,
            "broadcasts": broadcasts,
            "duration_ms": duration_ms,
            "error": error
        }
        
    async def _compare_results(self,
                             request_id: str,
                             message: Dict[str, Any],
                             current_result: Dict[str, Any],
                             shadow_result: Dict[str, Any]) -> ShadowComparison:
        """Compare current and shadow results"""
        comparison = ShadowComparison(
            request_id=request_id,
            timestamp=datetime.now(),
            message=message,
            current_response=current_result["response"],
            shadow_response=shadow_result["response"],
            current_broadcasts=current_result["broadcasts"],
            shadow_broadcasts=shadow_result["broadcasts"],
            current_duration_ms=current_result["duration_ms"],
            shadow_duration_ms=shadow_result["duration_ms"]
        )
        
        # Check for errors
        if current_result.get("error") or shadow_result.get("error"):
            comparison.match = False
            comparison.error = f"Handler error - Current: {current_result.get('error')}, Shadow: {shadow_result.get('error')}"
            return comparison
            
        # Compare responses
        if current_result["response"] and shadow_result["response"]:
            response_comparison = self.comparator.compare_responses(
                current_result["response"],
                shadow_result["response"]
            )
            if not response_comparison["match"]:
                comparison.match = False
                comparison.differences.extend(response_comparison["differences"])
                
        # Compare broadcasts
        broadcast_comparison = self.comparator.compare_broadcasts(
            current_result["broadcasts"],
            shadow_result["broadcasts"]
        )
        if not broadcast_comparison["match"]:
            comparison.match = False
            comparison.differences.extend(broadcast_comparison["differences"])
            
        # Compare performance
        if shadow_result["duration_ms"] > current_result["duration_ms"] * 1.5:
            comparison.differences.append({
                "type": "performance",
                "details": {
                    "current_ms": current_result["duration_ms"],
                    "shadow_ms": shadow_result["duration_ms"],
                    "ratio": shadow_result["duration_ms"] / current_result["duration_ms"]
                }
            })
            
        return comparison
        
    async def _handle_comparison(self, comparison: ShadowComparison):
        """Handle comparison result based on configuration"""
        # Record metrics
        self.metrics.record_comparison(comparison)
        
        # Store comparison if enabled
        if self.config.comparison_storage_enabled:
            self.comparisons.append(comparison)
            # Trim to max size
            if len(self.comparisons) > self.config.max_stored_comparisons:
                self.comparisons = self.comparisons[-self.config.max_stored_comparisons:]
                
        # Log mismatches
        if not comparison.match and self.config.log_mismatches:
            logger.warning(f"Shadow mismatch for {comparison.request_id}: {comparison.differences}")
            
        # Fail request if configured
        if not comparison.match and self.config.fail_on_mismatch:
            if self.config.state == ShadowModeState.VALIDATING:
                raise ValueError(f"Shadow validation failed: {comparison.differences}")
                
    def get_shadow_report(self) -> Dict[str, Any]:
        """Generate shadow mode report"""
        return {
            "config": {
                "state": self.config.state.value,
                "sample_rate": self.config.sample_rate,
                "timeout_ms": self.config.timeout_ms
            },
            "metrics": self.metrics.get_summary(),
            "recent_mismatches": [
                {
                    "request_id": c.request_id,
                    "timestamp": c.timestamp.isoformat(),
                    "message_action": c.message.get("action"),
                    "differences": c.differences
                }
                for c in self.comparisons[-10:]
                if not c.match
            ]
        }


class ShadowModeMetrics:
    """Track shadow mode metrics"""
    
    def __init__(self):
        self.total_requests = 0
        self.shadowed_requests = 0
        self.matches = 0
        self.mismatches = 0
        self.timeouts = 0
        self.errors = 0
        self.performance_degradations = 0
        
    def record_comparison(self, comparison: ShadowComparison):
        """Record comparison metrics"""
        self.shadowed_requests += 1
        
        if comparison.match:
            self.matches += 1
        else:
            self.mismatches += 1
            
        if comparison.error:
            self.errors += 1
            
        # Check for performance degradation
        if comparison.shadow_duration_ms > comparison.current_duration_ms * 1.5:
            self.performance_degradations += 1
            
    def record_timeout(self):
        """Record shadow timeout"""
        self.timeouts += 1
        self.shadowed_requests += 1
        
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        match_rate = (self.matches / self.shadowed_requests * 100) if self.shadowed_requests > 0 else 0
        
        return {
            "total_requests": self.total_requests,
            "shadowed_requests": self.shadowed_requests,
            "matches": self.matches,
            "mismatches": self.mismatches,
            "match_rate": f"{match_rate:.1f}%",
            "timeouts": self.timeouts,
            "errors": self.errors,
            "performance_degradations": self.performance_degradations
        }


# Global shadow mode instance
shadow_mode = ShadowModeOrchestrator()


def configure_shadow_mode(current_handler: Callable,
                         shadow_handler: Optional[Callable] = None,
                         config: Optional[ShadowModeConfig] = None):
    """Configure global shadow mode"""
    if config:
        shadow_mode.config = config
    shadow_mode.configure(current_handler, shadow_handler)
    

async def handle_with_shadow(websocket,
                           message: Dict[str, Any], 
                           room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle message with shadow mode"""
    return await shadow_mode.handle_message(websocket, message, room_state)


def get_shadow_report() -> Dict[str, Any]:
    """Get shadow mode report"""
    return shadow_mode.get_shadow_report()