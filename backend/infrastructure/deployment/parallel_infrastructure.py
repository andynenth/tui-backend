"""
Parallel infrastructure setup for blue-green deployment.

This module provides infrastructure management for running parallel
environments during state persistence rollout.
"""

import os
import json
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
import asyncio
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentConfig:
    """Configuration for a deployment environment."""
    
    name: str  # e.g., "blue", "green"
    host: str
    port: int
    health_check_path: str = "/health"
    metrics_path: str = "/metrics"
    active: bool = False
    version: Optional[str] = None
    deployed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "health_check_path": self.health_check_path,
            "metrics_path": self.metrics_path,
            "active": self.active,
            "version": self.version,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None
        }
    
    @property
    def base_url(self) -> str:
        """Get base URL for this environment."""
        return f"http://{self.host}:{self.port}"


class ParallelInfrastructureManager:
    """Manages parallel deployment environments."""
    
    def __init__(self, config_file: str = "infrastructure_config.json"):
        """Initialize infrastructure manager."""
        self.config_file = config_file
        self.environments: Dict[str, EnvironmentConfig] = {}
        self._load_config()
        
    def _load_config(self):
        """Load infrastructure configuration."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    
                for env_data in config.get("environments", []):
                    env = EnvironmentConfig(**env_data)
                    if env.deployed_at:
                        env.deployed_at = datetime.fromisoformat(env.deployed_at)
                    self.environments[env.name] = env
                    
                logger.info(f"Loaded {len(self.environments)} environments")
                
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                
    def _save_config(self):
        """Save infrastructure configuration."""
        config = {
            "environments": [
                env.to_dict() for env in self.environments.values()
            ]
        }
        
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)
            
    async def setup_environment(
        self,
        env_name: str,
        port: int,
        version: str,
        copy_from: Optional[str] = None
    ) -> EnvironmentConfig:
        """
        Set up a new deployment environment.
        
        Args:
            env_name: Environment name (e.g., "blue", "green")
            port: Port to run the service on
            version: Version to deploy
            copy_from: Optional environment to copy data from
            
        Returns:
            Environment configuration
        """
        logger.info(f"Setting up environment '{env_name}' on port {port}")
        
        # Create environment config
        env = EnvironmentConfig(
            name=env_name,
            host="localhost",  # In production, would be different hosts
            port=port,
            version=version,
            deployed_at=datetime.utcnow()
        )
        
        # Deploy the service
        success = await self._deploy_service(env, copy_from)
        
        if success:
            self.environments[env_name] = env
            self._save_config()
            logger.info(f"Environment '{env_name}' setup complete")
        else:
            logger.error(f"Failed to setup environment '{env_name}'")
            
        return env
        
    async def _deploy_service(
        self,
        env: EnvironmentConfig,
        copy_from: Optional[str] = None
    ) -> bool:
        """Deploy service to an environment."""
        try:
            # In production, this would:
            # 1. Deploy to actual servers/containers
            # 2. Copy data if needed
            # 3. Run migrations
            # 4. Start the service
            
            # For now, simulate deployment
            deploy_script = f"""
#!/bin/bash
# Deploy script for {env.name} environment

# Create environment directory
mkdir -p deployments/{env.name}

# Copy application
cp -r ../. deployments/{env.name}/

# Set environment variables
cat > deployments/{env.name}/.env << EOF
PORT={env.port}
ENVIRONMENT={env.name}
VERSION={env.version}
FF_USE_STATE_PERSISTENCE=true
EOF

# Start service (in production would use systemd/docker)
cd deployments/{env.name}
# python -m uvicorn main:app --port {env.port} &

echo "Deployment complete for {env.name}"
            """
            
            # Write and execute deploy script
            script_path = f"deploy_{env.name}.sh"
            with open(script_path, "w") as f:
                f.write(deploy_script)
                
            os.chmod(script_path, 0o755)
            
            result = subprocess.run(
                ["bash", script_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Deployment successful: {result.stdout}")
                
                # Copy data if needed
                if copy_from and copy_from in self.environments:
                    await self._copy_data(copy_from, env.name)
                    
                return True
            else:
                logger.error(f"Deployment failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Deployment error: {e}")
            return False
            
    async def _copy_data(self, source_env: str, target_env: str):
        """Copy data between environments."""
        logger.info(f"Copying data from {source_env} to {target_env}")
        
        # In production, would copy:
        # - Database snapshots
        # - Redis data
        # - File storage
        # - Configuration
        
        # For now, simulate data copy
        await asyncio.sleep(2)
        logger.info("Data copy complete")
        
    async def health_check(self, env_name: str) -> Tuple[bool, Dict[str, Any]]:
        """Check health of an environment."""
        if env_name not in self.environments:
            return False, {"error": f"Environment '{env_name}' not found"}
            
        env = self.environments[env_name]
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{env.base_url}{env.health_check_path}"
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return True, data
                    else:
                        return False, {
                            "status_code": response.status,
                            "error": "Health check failed"
                        }
                        
        except Exception as e:
            return False, {"error": str(e)}
            
    async def get_metrics(self, env_name: str) -> Optional[Dict[str, Any]]:
        """Get metrics from an environment."""
        if env_name not in self.environments:
            return None
            
        env = self.environments[env_name]
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{env.base_url}{env.metrics_path}"
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        # Parse Prometheus metrics
                        text = await response.text()
                        return self._parse_metrics(text)
                        
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            
        return None
        
    def _parse_metrics(self, metrics_text: str) -> Dict[str, Any]:
        """Parse Prometheus metrics format."""
        metrics = {}
        
        for line in metrics_text.split('\n'):
            if line and not line.startswith('#'):
                parts = line.split()
                if len(parts) >= 2:
                    metric_name = parts[0]
                    metric_value = float(parts[1])
                    metrics[metric_name] = metric_value
                    
        return metrics
        
    def get_active_environment(self) -> Optional[EnvironmentConfig]:
        """Get the currently active environment."""
        for env in self.environments.values():
            if env.active:
                return env
        return None
        
    def get_inactive_environment(self) -> Optional[EnvironmentConfig]:
        """Get an inactive environment for deployment."""
        for env in self.environments.values():
            if not env.active:
                return env
        return None
        
    async def switch_active_environment(self, new_active: str) -> bool:
        """
        Switch active environment (blue/green switch).
        
        Args:
            new_active: Name of environment to make active
            
        Returns:
            True if successful
        """
        if new_active not in self.environments:
            logger.error(f"Environment '{new_active}' not found")
            return False
            
        # Deactivate all environments
        for env in self.environments.values():
            env.active = False
            
        # Activate the new one
        self.environments[new_active].active = True
        self._save_config()
        
        logger.info(f"Switched active environment to '{new_active}'")
        return True
        
    async def validate_deployment(
        self,
        env_name: str,
        checks: List[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate a deployment is ready.
        
        Args:
            env_name: Environment to validate
            checks: List of checks to perform
            
        Returns:
            Tuple of (success, results)
        """
        if checks is None:
            checks = ["health", "metrics", "features", "performance"]
            
        results = {
            "environment": env_name,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        all_passed = True
        
        # Health check
        if "health" in checks:
            passed, data = await self.health_check(env_name)
            results["checks"]["health"] = {
                "passed": passed,
                "data": data
            }
            all_passed = all_passed and passed
            
        # Metrics availability
        if "metrics" in checks:
            metrics = await self.get_metrics(env_name)
            passed = metrics is not None
            results["checks"]["metrics"] = {
                "passed": passed,
                "data": metrics
            }
            all_passed = all_passed and passed
            
        # Feature flag check
        if "features" in checks:
            passed, features = await self._check_features(env_name)
            results["checks"]["features"] = {
                "passed": passed,
                "data": features
            }
            all_passed = all_passed and passed
            
        # Performance check
        if "performance" in checks:
            passed, perf = await self._check_performance(env_name)
            results["checks"]["performance"] = {
                "passed": passed,
                "data": perf
            }
            all_passed = all_passed and passed
            
        results["all_passed"] = all_passed
        return all_passed, results
        
    async def _check_features(self, env_name: str) -> Tuple[bool, Dict[str, Any]]:
        """Check feature flags are configured correctly."""
        env = self.environments.get(env_name)
        if not env:
            return False, {"error": "Environment not found"}
            
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{env.base_url}/api/feature-flags"
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check critical flags
                        critical_flags = [
                            "use_state_persistence",
                            "enable_state_snapshots"
                        ]
                        
                        all_present = all(
                            flag in data.get("flags", {})
                            for flag in critical_flags
                        )
                        
                        return all_present, data
                        
        except Exception as e:
            logger.error(f"Feature check failed: {e}")
            
        return False, {"error": "Failed to check features"}
        
    async def _check_performance(self, env_name: str) -> Tuple[bool, Dict[str, Any]]:
        """Run basic performance check."""
        env = self.environments.get(env_name)
        if not env:
            return False, {"error": "Environment not found"}
            
        try:
            # Run a simple performance test
            latencies = []
            
            async with aiohttp.ClientSession() as session:
                for _ in range(10):
                    start = datetime.utcnow()
                    
                    async with session.get(
                        f"{env.base_url}/health",
                        timeout=5
                    ) as response:
                        if response.status == 200:
                            end = datetime.utcnow()
                            latency_ms = (end - start).total_seconds() * 1000
                            latencies.append(latency_ms)
                            
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                max_latency = max(latencies)
                
                # Pass if average latency < 100ms
                passed = avg_latency < 100
                
                return passed, {
                    "avg_latency_ms": round(avg_latency, 2),
                    "max_latency_ms": round(max_latency, 2),
                    "samples": len(latencies)
                }
                
        except Exception as e:
            logger.error(f"Performance check failed: {e}")
            
        return False, {"error": "Performance check failed"}


# Convenience functions
async def setup_blue_green_environments(
    blue_port: int = 8001,
    green_port: int = 8002,
    version: str = "1.0.0"
) -> ParallelInfrastructureManager:
    """Set up blue/green deployment environments."""
    manager = ParallelInfrastructureManager()
    
    # Set up blue environment
    blue_env = await manager.setup_environment(
        "blue",
        blue_port,
        version
    )
    
    # Set up green environment
    green_env = await manager.setup_environment(
        "green",
        green_port,
        version
    )
    
    # Make blue active by default
    await manager.switch_active_environment("blue")
    
    return manager


async def perform_blue_green_switch(
    manager: ParallelInfrastructureManager,
    new_version: str
) -> bool:
    """
    Perform blue/green deployment switch.
    
    Args:
        manager: Infrastructure manager
        new_version: Version to deploy
        
    Returns:
        True if successful
    """
    # Get current environments
    active_env = manager.get_active_environment()
    inactive_env = manager.get_inactive_environment()
    
    if not active_env or not inactive_env:
        logger.error("Missing active or inactive environment")
        return False
        
    logger.info(f"Deploying {new_version} to {inactive_env.name} environment")
    
    # Deploy to inactive environment
    success = await manager.setup_environment(
        inactive_env.name,
        inactive_env.port,
        new_version,
        copy_from=active_env.name
    )
    
    if not success:
        logger.error("Deployment failed")
        return False
        
    # Validate deployment
    passed, results = await manager.validate_deployment(inactive_env.name)
    
    if not passed:
        logger.error(f"Validation failed: {results}")
        return False
        
    # Switch traffic
    logger.info(f"Switching traffic to {inactive_env.name}")
    await manager.switch_active_environment(inactive_env.name)
    
    return True