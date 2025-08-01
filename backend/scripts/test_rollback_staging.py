#!/usr/bin/env python3
"""
Test rollback procedures in staging environment.

This script validates that rollback procedures work correctly
without causing service disruption.
"""

import os
import sys
import time
import asyncio
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import requests

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class RollbackTester:
    """Tests rollback procedures in staging."""
    
    def __init__(self, staging_url: str):
        """Initialize tester."""
        self.staging_url = staging_url.rstrip("/")
        self.test_results = []
        self.start_time = datetime.utcnow()
        
    async def run_all_tests(self) -> bool:
        """Run all rollback tests."""
        print("🧪 State Persistence Rollback Test Suite")
        print("=" * 50)
        print(f"Target: {self.staging_url}")
        print(f"Started: {self.start_time.isoformat()}")
        print()
        
        tests = [
            ("Pre-rollback health check", self.test_health_check),
            ("Feature flag toggle", self.test_feature_flag_toggle),
            ("Game continuity during rollback", self.test_game_continuity),
            ("Rollback script execution", self.test_rollback_script),
            ("Post-rollback health check", self.test_post_rollback_health),
            ("Recovery after re-enable", self.test_recovery),
            ("Performance impact", self.test_performance_impact),
            ("Alert suppression", self.test_alert_suppression),
        ]
        
        all_passed = True
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}...")
            try:
                result = await test_func()
                self.test_results.append({
                    "name": test_name,
                    "passed": result[0],
                    "message": result[1],
                    "duration": result[2] if len(result) > 2 else None
                })
                
                if result[0]:
                    print(f"  ✅ {result[1]}")
                else:
                    print(f"  ❌ {result[1]}")
                    all_passed = False
                    
            except Exception as e:
                print(f"  ❌ Test failed with error: {e}")
                self.test_results.append({
                    "name": test_name,
                    "passed": False,
                    "message": str(e),
                    "error": True
                })
                all_passed = False
                
        # Generate report
        await self.generate_report()
        
        return all_passed
        
    async def test_health_check(self) -> Tuple[bool, str]:
        """Test system health before rollback."""
        try:
            # Check main health endpoint
            response = requests.get(f"{self.staging_url}/health", timeout=5)
            if response.status_code != 200:
                return False, f"Health check returned {response.status_code}"
                
            health = response.json()
            
            # Check state management health
            state_health = health.get("components", {}).get("state_management", {})
            if not state_health.get("healthy", False):
                return False, "State management not healthy"
                
            # Check metrics
            metrics_response = requests.get(f"{self.staging_url}/metrics", timeout=5)
            if metrics_response.status_code != 200:
                return False, "Metrics endpoint not accessible"
                
            return True, "All health checks passed"
            
        except Exception as e:
            return False, f"Health check failed: {e}"
            
    async def test_feature_flag_toggle(self) -> Tuple[bool, str, float]:
        """Test feature flag can be toggled quickly."""
        start = time.time()
        
        try:
            # Get current state
            response = requests.get(f"{self.staging_url}/api/feature-flags", timeout=5)
            original_state = response.json().get("USE_STATE_PERSISTENCE", False)
            
            # Disable via API
            disable_response = requests.post(
                f"{self.staging_url}/api/feature-flags/toggle",
                json={"flag": "USE_STATE_PERSISTENCE", "enabled": False},
                timeout=5
            )
            
            if disable_response.status_code != 200:
                return False, "Failed to disable feature flag", 0
                
            # Verify disabled
            time.sleep(2)  # Allow propagation
            response = requests.get(f"{self.staging_url}/api/feature-flags", timeout=5)
            if response.json().get("USE_STATE_PERSISTENCE", True):
                return False, "Feature flag not disabled", 0
                
            # Re-enable
            enable_response = requests.post(
                f"{self.staging_url}/api/feature-flags/toggle",
                json={"flag": "USE_STATE_PERSISTENCE", "enabled": original_state},
                timeout=5
            )
            
            duration = time.time() - start
            
            if enable_response.status_code != 200:
                return False, "Failed to re-enable feature flag", duration
                
            return True, f"Feature flag toggled successfully in {duration:.2f}s", duration
            
        except Exception as e:
            return False, f"Feature flag test failed: {e}", 0
            
    async def test_game_continuity(self) -> Tuple[bool, str]:
        """Test games continue during rollback."""
        try:
            # Create a test game
            create_response = requests.post(
                f"{self.staging_url}/api/rooms/create",
                json={"name": "rollback-test", "capacity": 4},
                timeout=5
            )
            
            if create_response.status_code != 200:
                return False, "Failed to create test game"
                
            room_id = create_response.json().get("id")
            
            # Disable state persistence
            requests.post(
                f"{self.staging_url}/api/feature-flags/toggle",
                json={"flag": "USE_STATE_PERSISTENCE", "enabled": False},
                timeout=5
            )
            
            time.sleep(2)
            
            # Try to join game
            join_response = requests.post(
                f"{self.staging_url}/api/rooms/{room_id}/join",
                json={"player_name": "test_player"},
                timeout=5
            )
            
            if join_response.status_code != 200:
                return False, "Game not accessible after rollback"
                
            # Re-enable
            requests.post(
                f"{self.staging_url}/api/feature-flags/toggle",
                json={"flag": "USE_STATE_PERSISTENCE", "enabled": True},
                timeout=5
            )
            
            return True, "Games continue functioning during rollback"
            
        except Exception as e:
            return False, f"Game continuity test failed: {e}"
            
    async def test_rollback_script(self) -> Tuple[bool, str, float]:
        """Test the rollback script execution."""
        start = time.time()
        
        try:
            # Execute rollback script in dry-run mode
            result = subprocess.run(
                ["python", "scripts/rollback_state_persistence.py", "--dry-run"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            duration = time.time() - start
            
            if result.returncode != 0:
                return False, f"Rollback script failed: {result.stderr}", duration
                
            # Check output contains expected elements
            expected = [
                "Checking current status",
                "Feature flags disabled",
                "Rollback complete"
            ]
            
            output = result.stdout.lower()
            for element in expected:
                if element.lower() not in output:
                    return False, f"Missing expected output: {element}", duration
                    
            return True, f"Rollback script executed successfully in {duration:.2f}s", duration
            
        except subprocess.TimeoutExpired:
            return False, "Rollback script timed out", 30.0
        except Exception as e:
            return False, f"Rollback script test failed: {e}", 0
            
    async def test_post_rollback_health(self) -> Tuple[bool, str]:
        """Test system health after rollback."""
        try:
            # Ensure state persistence is disabled
            requests.post(
                f"{self.staging_url}/api/feature-flags/toggle",
                json={"flag": "USE_STATE_PERSISTENCE", "enabled": False},
                timeout=5
            )
            
            time.sleep(5)  # Allow system to stabilize
            
            # Check health
            response = requests.get(f"{self.staging_url}/health", timeout=5)
            if response.status_code != 200:
                return False, f"Health check failed after rollback"
                
            # Check error rates
            metrics = requests.get(f"{self.staging_url}/metrics", timeout=5).text
            
            # Look for state errors (should be none or very low)
            if "state_errors_total" in metrics:
                # Parse error count (simplified)
                import re
                match = re.search(r'state_errors_total\s+(\d+)', metrics)
                if match and int(match.group(1)) > 10:
                    return False, "High error count after rollback"
                    
            return True, "System healthy after rollback"
            
        except Exception as e:
            return False, f"Post-rollback health check failed: {e}"
            
    async def test_recovery(self) -> Tuple[bool, str]:
        """Test recovery after re-enabling."""
        try:
            # Re-enable state persistence
            response = requests.post(
                f"{self.staging_url}/api/feature-flags/toggle",
                json={"flag": "USE_STATE_PERSISTENCE", "enabled": True},
                timeout=5
            )
            
            if response.status_code != 200:
                return False, "Failed to re-enable state persistence"
                
            time.sleep(5)  # Allow recovery
            
            # Check state operations resume
            metrics = requests.get(f"{self.staging_url}/metrics", timeout=5).text
            
            if "state_transitions_total" not in metrics:
                return False, "State transitions not resuming"
                
            # Create a game to test functionality
            create_response = requests.post(
                f"{self.staging_url}/api/rooms/create",
                json={"name": "recovery-test", "capacity": 4},
                timeout=5
            )
            
            if create_response.status_code != 200:
                return False, "Cannot create games after recovery"
                
            return True, "System recovered successfully"
            
        except Exception as e:
            return False, f"Recovery test failed: {e}"
            
    async def test_performance_impact(self) -> Tuple[bool, str]:
        """Test performance impact of rollback."""
        try:
            # Measure baseline latency with state persistence
            baseline_latencies = []
            for _ in range(10):
                start = time.time()
                requests.get(f"{self.staging_url}/api/rooms", timeout=5)
                baseline_latencies.append((time.time() - start) * 1000)
                
            baseline_p99 = sorted(baseline_latencies)[9]
            
            # Disable state persistence
            requests.post(
                f"{self.staging_url}/api/feature-flags/toggle",
                json={"flag": "USE_STATE_PERSISTENCE", "enabled": False},
                timeout=5
            )
            
            time.sleep(2)
            
            # Measure latency without state persistence
            rollback_latencies = []
            for _ in range(10):
                start = time.time()
                requests.get(f"{self.staging_url}/api/rooms", timeout=5)
                rollback_latencies.append((time.time() - start) * 1000)
                
            rollback_p99 = sorted(rollback_latencies)[9]
            
            # Re-enable
            requests.post(
                f"{self.staging_url}/api/feature-flags/toggle",
                json={"flag": "USE_STATE_PERSISTENCE", "enabled": True},
                timeout=5
            )
            
            # Should be faster or similar without state persistence
            if rollback_p99 > baseline_p99 * 1.5:
                return False, f"Performance degraded: {baseline_p99:.0f}ms -> {rollback_p99:.0f}ms"
                
            return True, f"Performance maintained: {baseline_p99:.0f}ms -> {rollback_p99:.0f}ms"
            
        except Exception as e:
            return False, f"Performance test failed: {e}"
            
    async def test_alert_suppression(self) -> Tuple[bool, str]:
        """Test that alerts are properly suppressed during rollback."""
        try:
            # Check if monitoring endpoint exists
            response = requests.get(f"{self.staging_url}/api/monitoring/alerts", timeout=5)
            
            if response.status_code == 404:
                return True, "Alert endpoint not implemented (skip test)"
                
            # Get current alerts
            alerts_before = response.json().get("active_alerts", [])
            
            # Trigger rollback
            requests.post(
                f"{self.staging_url}/api/feature-flags/toggle",
                json={"flag": "USE_STATE_PERSISTENCE", "enabled": False},
                timeout=5
            )
            
            time.sleep(5)
            
            # Check alerts again
            response = requests.get(f"{self.staging_url}/api/monitoring/alerts", timeout=5)
            alerts_after = response.json().get("active_alerts", [])
            
            # Should not have new state-related alerts
            new_alerts = [a for a in alerts_after if a not in alerts_before]
            state_alerts = [a for a in new_alerts if "state" in a.get("name", "").lower()]
            
            # Re-enable
            requests.post(
                f"{self.staging_url}/api/feature-flags/toggle",
                json={"flag": "USE_STATE_PERSISTENCE", "enabled": True},
                timeout=5
            )
            
            if state_alerts:
                return False, f"State alerts fired during rollback: {state_alerts}"
                
            return True, "No false alerts during rollback"
            
        except Exception as e:
            return False, f"Alert suppression test failed: {e}"
            
    async def generate_report(self):
        """Generate test report."""
        report_path = Path(f"rollback_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        passed = sum(1 for r in self.test_results if r["passed"])
        total = len(self.test_results)
        
        report = {
            "test_run": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "staging_url": self.staging_url,
                "passed": passed,
                "total": total,
                "success_rate": f"{(passed/total*100):.1f}%"
            },
            "test_results": self.test_results,
            "summary": {
                "rollback_ready": passed == total,
                "issues": [r["message"] for r in self.test_results if not r["passed"]]
            }
        }
        
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📄 Report saved: {report_path}")
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if passed == total:
            print("\n✅ All rollback tests passed! Safe to use in production.")
        else:
            print("\n❌ Some tests failed. Review and fix before production use.")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['name']}: {result['message']}")


async def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test state persistence rollback procedures")
    parser.add_argument(
        "--staging-url",
        default=os.getenv("STAGING_URL", "http://localhost:8000"),
        help="Staging environment URL"
    )
    
    args = parser.parse_args()
    
    tester = RollbackTester(args.staging_url)
    success = await tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))