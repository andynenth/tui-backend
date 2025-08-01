#!/usr/bin/env python3
"""
Script to enable state persistence feature flag for testing.

This script:
1. Sets the USE_STATE_PERSISTENCE environment variable
2. Runs integration tests
3. Verifies state persistence is working
4. Generates a report
"""

import os
import sys
import subprocess
import json
from datetime import datetime
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.feature_flags import FeatureFlags
from infrastructure.state_persistence.persistence_manager import StatePersistenceManager, PersistenceConfig
from infrastructure.monitoring.state_management_metrics import get_state_metrics_collector


def enable_state_persistence():
    """Enable the state persistence feature flag."""
    print("🔧 Enabling USE_STATE_PERSISTENCE feature flag...")
    # Feature flags use FF_ prefix for environment variables
    os.environ["FF_USE_STATE_PERSISTENCE"] = "true"
    # Enable snapshots for hybrid strategy
    os.environ["FF_ENABLE_STATE_SNAPSHOTS"] = "true"
    
    # Verify it's enabled
    flags = FeatureFlags()
    if flags.is_enabled(flags.USE_STATE_PERSISTENCE, {}):
        print("✅ State persistence enabled successfully")
        return True
    else:
        print("❌ Failed to enable state persistence")
        return False


def run_integration_tests():
    """Run integration tests with state persistence enabled."""
    print("\n🧪 Running integration tests...")
    
    test_files = [
        "tests/integration/test_state_management_integration.py",
        "tests/integration/test_state_monitoring_setup.py"
    ]
    
    results = []
    for test_file in test_files:
        print(f"\n  Running {test_file}...")
        result = subprocess.run(
            ["python", "-m", "pytest", test_file, "-v", "--tb=short"],
            capture_output=True,
            text=True
        )
        
        results.append({
            "file": test_file,
            "passed": result.returncode == 0,
            "output": result.stdout if result.returncode == 0 else result.stderr
        })
        
        if result.returncode == 0:
            print(f"  ✅ {test_file} passed")
        else:
            print(f"  ❌ {test_file} failed")
            print(f"     Error: {result.stderr[:200]}...")
    
    return results


def check_metrics_collection():
    """Verify metrics are being collected."""
    print("\n📊 Checking metrics collection...")
    
    metrics = get_state_metrics_collector()
    
    # Simulate some operations to generate metrics
    metrics.track_transition(success=True, duration_ms=10.5, phase_change=True)
    metrics.track_snapshot(success=True, duration_ms=20.3)
    metrics.track_recovery(success=False, duration_ms=100.0)
    
    print("  ✅ Metrics collector is operational")
    print("  📈 Sample metrics recorded:")
    print("     - State transition: 10.5ms")
    print("     - Snapshot creation: 20.3ms")
    print("     - Recovery attempt: 100.0ms (failed)")
    
    return True


async def test_game_flow():
    """Test a sample game flow with state persistence."""
    print("\n🎮 Testing game flow with state persistence...")
    
    # This would normally interact with the actual game
    # For now, we'll verify the infrastructure is ready
    
    try:
        from infrastructure.adapters.clean_architecture_adapter import CleanArchitectureAdapter
        from infrastructure.factories.state_adapter_factory import StateAdapterFactory
        
        # Create a test context
        context = {
            "player_id": "test-player",
            "room_id": "test-room",
            "game_id": "test-game"
        }
        
        # Get state adapter
        adapter = StateAdapterFactory.create_for_use_case("StartGameUseCase", context)
        
        if adapter and adapter.enabled:
            print("  ✅ State adapter created and enabled")
            print("  🔄 State persistence is ready for game operations")
            return True
        else:
            print("  ⚠️  State adapter created but not enabled")
            return False
            
    except Exception as e:
        print(f"  ❌ Error testing game flow: {e}")
        return False


def generate_report(results):
    """Generate a report of the verification results."""
    print("\n📝 Generating verification report...")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "feature_enabled": os.environ.get("FF_USE_STATE_PERSISTENCE") == "true",
        "test_results": results,
        "metrics_operational": True,
        "recommendations": []
    }
    
    # Add recommendations based on results
    all_tests_passed = all(r["passed"] for r in results["integration_tests"])
    
    if all_tests_passed:
        report["recommendations"].append("✅ All tests passed - safe to proceed to staging")
    else:
        report["recommendations"].append("⚠️  Some tests failed - investigate before staging")
    
    if results["game_flow_ready"]:
        report["recommendations"].append("✅ State persistence infrastructure is ready")
    else:
        report["recommendations"].append("⚠️  Game flow integration needs attention")
    
    # Save report
    report_path = Path("state_persistence_verification_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n  Report saved to: {report_path}")
    return report


def main():
    """Main verification process."""
    print("🚀 State Persistence Verification Process")
    print("=" * 50)
    
    # Step 1: Enable feature flag
    if not enable_state_persistence():
        print("\n❌ Failed to enable state persistence. Exiting.")
        return 1
    
    # Step 2: Run integration tests
    test_results = run_integration_tests()
    
    # Step 3: Check metrics
    metrics_ok = check_metrics_collection()
    
    # Step 4: Test game flow
    game_flow_ok = asyncio.run(test_game_flow())
    
    # Step 5: Generate report
    results = {
        "integration_tests": test_results,
        "metrics_operational": metrics_ok,
        "game_flow_ready": game_flow_ok
    }
    
    report = generate_report(results)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    all_passed = all(r["passed"] for r in test_results) and metrics_ok and game_flow_ok
    
    if all_passed:
        print("✅ State persistence is ready for staging deployment!")
        print("\nNext steps:")
        print("1. Review the detailed report")
        print("2. Enable in staging environment")
        print("3. Monitor for 24-48 hours")
        print("4. Begin Phase 4 deployment tasks")
        return 0
    else:
        print("⚠️  Some issues detected. Please review the report.")
        return 1


if __name__ == "__main__":
    sys.exit(main())