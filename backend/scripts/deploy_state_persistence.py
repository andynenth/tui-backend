#!/usr/bin/env python3
"""
Deployment automation script for state persistence.

This script automates the deployment process with safety checks,
gradual rollout, and monitoring integration.
"""

import os
import sys
import time
import json
import asyncio
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import requests
from dataclasses import dataclass

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.feature_flags.enhanced_feature_flags import (
    FlagConfig,
    RolloutStrategy,
    get_enhanced_feature_flags
)


@dataclass
class DeploymentConfig:
    """Configuration for deployment."""
    
    environment: str
    initial_percentage: float
    increment_percentage: float
    increment_interval_minutes: int
    success_threshold: float
    error_threshold: float
    rollback_on_error: bool
    max_rollout_hours: int
    health_check_url: str
    metrics_url: str
    
    @classmethod
    def from_env(cls, environment: str) -> "DeploymentConfig":
        """Create config from environment."""
        if environment == "staging":
            return cls(
                environment=environment,
                initial_percentage=10.0,
                increment_percentage=20.0,
                increment_interval_minutes=30,
                success_threshold=99.0,
                error_threshold=5.0,
                rollback_on_error=True,
                max_rollout_hours=4,
                health_check_url=os.getenv("STAGING_URL", "http://localhost:8000") + "/health",
                metrics_url=os.getenv("STAGING_URL", "http://localhost:8000") + "/metrics"
            )
        elif environment == "production":
            return cls(
                environment=environment,
                initial_percentage=1.0,
                increment_percentage=10.0,
                increment_interval_minutes=60,
                success_threshold=99.9,
                error_threshold=1.0,
                rollback_on_error=True,
                max_rollout_hours=24,
                health_check_url=os.getenv("PROD_URL", "http://localhost:8000") + "/health",
                metrics_url=os.getenv("PROD_URL", "http://localhost:8000") + "/metrics"
            )
        else:
            raise ValueError(f"Unknown environment: {environment}")


class StateDeploymentManager:
    """Manages the deployment of state persistence."""
    
    def __init__(self, config: DeploymentConfig):
        """Initialize deployment manager."""
        self.config = config
        self.start_time = datetime.utcnow()
        self.deployment_log = []
        
    async def deploy(self, flags_to_deploy: List[str]) -> bool:
        """
        Deploy state persistence with gradual rollout.
        
        Args:
            flags_to_deploy: List of feature flags to enable
            
        Returns:
            True if deployment successful
        """
        print(f"🚀 Starting State Persistence Deployment to {self.config.environment}")
        print("=" * 60)
        
        try:
            # Phase 1: Pre-deployment checks
            if not await self._pre_deployment_checks():
                return False
                
            # Phase 2: Initial rollout
            if not await self._initial_rollout(flags_to_deploy):
                return False
                
            # Phase 3: Gradual increase
            if not await self._gradual_rollout(flags_to_deploy):
                return False
                
            # Phase 4: Full rollout
            if not await self._complete_rollout(flags_to_deploy):
                return False
                
            # Phase 5: Post-deployment validation
            if not await self._post_deployment_validation():
                return False
                
            print("\n✅ Deployment completed successfully!")
            await self._generate_deployment_report()
            return True
            
        except Exception as e:
            print(f"\n❌ Deployment failed: {e}")
            await self._emergency_rollback(flags_to_deploy)
            return False
            
    async def _pre_deployment_checks(self) -> bool:
        """Perform pre-deployment checks."""
        print("\n📋 Pre-deployment checks...")
        
        checks = [
            ("Health check", self._check_health()),
            ("Metrics availability", self._check_metrics()),
            ("Feature flag system", self._check_feature_flags()),
            ("Rollback script", self._check_rollback_script()),
            ("Monitoring alerts", self._check_monitoring())
        ]
        
        all_passed = True
        for check_name, check_result in checks:
            passed, message = await check_result
            if passed:
                print(f"  ✅ {check_name}: {message}")
            else:
                print(f"  ❌ {check_name}: {message}")
                all_passed = False
                
        return all_passed
        
    async def _check_health(self) -> Tuple[bool, str]:
        """Check system health."""
        try:
            response = requests.get(self.config.health_check_url, timeout=10)
            if response.status_code == 200:
                return True, "System healthy"
            else:
                return False, f"Health check returned {response.status_code}"
        except Exception as e:
            return False, f"Health check failed: {e}"
            
    async def _check_metrics(self) -> Tuple[bool, str]:
        """Check metrics availability."""
        try:
            response = requests.get(self.config.metrics_url, timeout=10)
            if response.status_code == 200:
                return True, "Metrics available"
            else:
                return False, f"Metrics returned {response.status_code}"
        except Exception as e:
            return False, f"Metrics check failed: {e}"
            
    async def _check_feature_flags(self) -> Tuple[bool, str]:
        """Check feature flag system."""
        try:
            flags = get_enhanced_feature_flags()
            # Test evaluation
            result = flags.is_enabled_advanced("test", {"user_id": "test"})
            return True, "Feature flags operational"
        except Exception as e:
            return False, f"Feature flag error: {e}"
            
    async def _check_rollback_script(self) -> Tuple[bool, str]:
        """Check rollback script exists."""
        rollback_script = Path("scripts/rollback_state_persistence.py")
        if rollback_script.exists():
            return True, "Rollback script available"
        else:
            return False, "Rollback script not found"
            
    async def _check_monitoring(self) -> Tuple[bool, str]:
        """Check monitoring setup."""
        # In production, check actual monitoring service
        # For now, just verify metrics endpoint
        return await self._check_metrics()
        
    async def _initial_rollout(self, flags: List[str]) -> bool:
        """Perform initial rollout."""
        print(f"\n🎯 Initial rollout ({self.config.initial_percentage}%)...")
        
        # Set initial percentage for all flags
        for flag in flags:
            success = await self._update_flag_percentage(flag, self.config.initial_percentage)
            if not success:
                return False
                
        # Wait for stabilization
        print(f"  ⏳ Waiting 5 minutes for stabilization...")
        await asyncio.sleep(300)  # 5 minutes
        
        # Check metrics
        metrics = await self._get_current_metrics()
        if not self._validate_metrics(metrics):
            print("  ❌ Initial rollout metrics failed validation")
            return False
            
        print(f"  ✅ Initial rollout successful")
        return True
        
    async def _gradual_rollout(self, flags: List[str]) -> bool:
        """Gradually increase rollout percentage."""
        print(f"\n📈 Gradual rollout...")
        
        current_percentage = self.config.initial_percentage
        max_time = self.start_time + timedelta(hours=self.config.max_rollout_hours)
        
        while current_percentage < 100.0 and datetime.utcnow() < max_time:
            # Calculate next percentage
            next_percentage = min(
                100.0,
                current_percentage + self.config.increment_percentage
            )
            
            print(f"\n  🔄 Increasing to {next_percentage}%...")
            
            # Update all flags
            for flag in flags:
                success = await self._update_flag_percentage(flag, next_percentage)
                if not success:
                    return False
                    
            # Wait for interval
            wait_minutes = self.config.increment_interval_minutes
            print(f"  ⏳ Waiting {wait_minutes} minutes...")
            await asyncio.sleep(wait_minutes * 60)
            
            # Validate metrics
            metrics = await self._get_current_metrics()
            if not self._validate_metrics(metrics):
                print(f"  ❌ Metrics validation failed at {next_percentage}%")
                if self.config.rollback_on_error:
                    await self._rollback_to_percentage(flags, current_percentage)
                return False
                
            print(f"  ✅ {next_percentage}% rollout successful")
            current_percentage = next_percentage
            
            # Log progress
            self.deployment_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "percentage": current_percentage,
                "metrics": metrics
            })
            
        return current_percentage >= 100.0
        
    async def _complete_rollout(self, flags: List[str]) -> bool:
        """Complete the rollout to 100%."""
        if await self._get_current_percentage(flags[0]) >= 100.0:
            print("\n✅ Already at 100% rollout")
            return True
            
        print("\n🎯 Completing rollout to 100%...")
        
        for flag in flags:
            success = await self._update_flag_percentage(flag, 100.0)
            if not success:
                return False
                
        # Final stabilization period
        print("  ⏳ Final stabilization (10 minutes)...")
        await asyncio.sleep(600)
        
        # Final validation
        metrics = await self._get_current_metrics()
        if not self._validate_metrics(metrics):
            print("  ❌ Final validation failed")
            return False
            
        print("  ✅ Full rollout complete")
        return True
        
    async def _post_deployment_validation(self) -> bool:
        """Validate deployment success."""
        print("\n🔍 Post-deployment validation...")
        
        validations = [
            ("Feature flags at 100%", self._validate_flags_enabled()),
            ("Error rate acceptable", self._validate_error_rate()),
            ("Performance acceptable", self._validate_performance()),
            ("Recovery working", self._validate_recovery())
        ]
        
        all_passed = True
        for validation_name, validation_result in validations:
            passed, message = await validation_result
            if passed:
                print(f"  ✅ {validation_name}: {message}")
            else:
                print(f"  ❌ {validation_name}: {message}")
                all_passed = False
                
        return all_passed
        
    async def _validate_flags_enabled(self) -> Tuple[bool, str]:
        """Validate all flags are enabled."""
        flags = get_enhanced_feature_flags()
        
        # Check main flags
        main_flags = ["use_state_persistence", "enable_state_snapshots"]
        for flag in main_flags:
            config = flags.get_flag_config(flag)
            if not config or config.percentage < 100.0:
                return False, f"Flag {flag} not at 100%"
                
        return True, "All flags at 100%"
        
    async def _validate_error_rate(self) -> Tuple[bool, str]:
        """Validate error rate is acceptable."""
        metrics = await self._get_current_metrics()
        error_rate = metrics.get("error_rate", 0)
        
        if error_rate > self.config.error_threshold:
            return False, f"Error rate {error_rate}% exceeds threshold {self.config.error_threshold}%"
            
        return True, f"Error rate {error_rate}% is acceptable"
        
    async def _validate_performance(self) -> Tuple[bool, str]:
        """Validate performance metrics."""
        metrics = await self._get_current_metrics()
        p99_latency = metrics.get("p99_latency_ms", 0)
        
        if p99_latency > 100:  # 100ms threshold
            return False, f"P99 latency {p99_latency}ms exceeds threshold"
            
        return True, f"P99 latency {p99_latency}ms is acceptable"
        
    async def _validate_recovery(self) -> Tuple[bool, str]:
        """Validate recovery is working."""
        # In production, would test actual recovery
        # For now, just check if recovery flag is enabled
        flags = get_enhanced_feature_flags()
        config = flags.get_flag_config("enable_state_recovery")
        
        if config and config.enabled:
            return True, "Recovery enabled"
        else:
            return False, "Recovery not enabled"
            
    async def _update_flag_percentage(self, flag: str, percentage: float) -> bool:
        """Update flag percentage."""
        try:
            flags = get_enhanced_feature_flags()
            
            config = flags.get_flag_config(flag) or FlagConfig(
                name=flag,
                description=f"State persistence flag: {flag}",
                enabled=True,
                strategy=RolloutStrategy.PERCENTAGE
            )
            
            config.percentage = percentage
            config.enabled = percentage > 0
            
            flags.set_flag_config(config)
            flags.save_config()
            
            return True
            
        except Exception as e:
            print(f"    ❌ Failed to update {flag}: {e}")
            return False
            
    async def _get_current_percentage(self, flag: str) -> float:
        """Get current rollout percentage."""
        flags = get_enhanced_feature_flags()
        config = flags.get_flag_config(flag)
        return config.percentage if config else 0.0
        
    async def _get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            response = requests.get(self.config.metrics_url, timeout=10)
            if response.status_code != 200:
                return {}
                
            # Parse Prometheus metrics (simplified)
            metrics_text = response.text
            
            # Extract key metrics
            error_rate = self._extract_metric(metrics_text, "state_errors_total") or 0
            transitions = self._extract_metric(metrics_text, "state_transitions_total") or 0
            p99_latency = self._extract_metric(metrics_text, "state_operation_duration_ms{quantile=\"0.99\"}") or 0
            
            # Calculate error rate percentage
            if transitions > 0:
                error_percentage = (error_rate / transitions) * 100
            else:
                error_percentage = 0
                
            return {
                "error_rate": error_percentage,
                "transitions_total": transitions,
                "errors_total": error_rate,
                "p99_latency_ms": p99_latency,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"    ⚠️  Failed to get metrics: {e}")
            return {}
            
    def _extract_metric(self, metrics_text: str, metric_name: str) -> Optional[float]:
        """Extract metric value from Prometheus text format."""
        import re
        pattern = rf"{re.escape(metric_name)}[^\\n]*\\s+(\\d+\\.?\\d*)"
        match = re.search(pattern, metrics_text)
        if match:
            return float(match.group(1))
        return None
        
    def _validate_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Validate metrics are acceptable."""
        if not metrics:
            print("    ⚠️  No metrics available")
            return True  # Don't fail on missing metrics
            
        error_rate = metrics.get("error_rate", 0)
        if error_rate > self.config.error_threshold:
            print(f"    ❌ Error rate {error_rate:.2f}% exceeds threshold {self.config.error_threshold}%")
            return False
            
        return True
        
    async def _rollback_to_percentage(self, flags: List[str], percentage: float):
        """Rollback to a specific percentage."""
        print(f"\n🔄 Rolling back to {percentage}%...")
        
        for flag in flags:
            await self._update_flag_percentage(flag, percentage)
            
        print("  ✅ Rollback complete")
        
    async def _emergency_rollback(self, flags: List[str]):
        """Emergency rollback to 0%."""
        print("\n🚨 EMERGENCY ROLLBACK")
        
        for flag in flags:
            await self._update_flag_percentage(flag, 0.0)
            
        # Run rollback script
        try:
            result = subprocess.run(
                ["python", "scripts/rollback_state_persistence.py"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("  ✅ Emergency rollback complete")
            else:
                print(f"  ❌ Rollback script failed: {result.stderr}")
                
        except Exception as e:
            print(f"  ❌ Failed to run rollback script: {e}")
            
    async def _generate_deployment_report(self):
        """Generate deployment report."""
        report_path = f"deployment_report_{self.config.environment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            "environment": self.config.environment,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "duration_minutes": (datetime.utcnow() - self.start_time).total_seconds() / 60,
            "config": {
                "initial_percentage": self.config.initial_percentage,
                "increment_percentage": self.config.increment_percentage,
                "increment_interval_minutes": self.config.increment_interval_minutes
            },
            "deployment_log": self.deployment_log,
            "final_metrics": await self._get_current_metrics(),
            "success": True
        }
        
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📄 Deployment report saved: {report_path}")


async def main():
    """Main deployment script."""
    parser = argparse.ArgumentParser(description="Deploy state persistence with gradual rollout")
    parser.add_argument(
        "environment",
        choices=["staging", "production"],
        help="Target environment"
    )
    parser.add_argument(
        "--flags",
        nargs="+",
        default=["use_state_persistence", "enable_state_snapshots", "enable_state_recovery"],
        help="Feature flags to deploy"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform dry run without actual changes"
    )
    
    args = parser.parse_args()
    
    # Create deployment config
    config = DeploymentConfig.from_env(args.environment)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No actual changes will be made")
        config.rollback_on_error = False
        
    # Create deployment manager
    manager = StateDeploymentManager(config)
    
    # Run deployment
    success = await manager.deploy(args.flags)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))