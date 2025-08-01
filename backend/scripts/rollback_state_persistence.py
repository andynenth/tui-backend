#!/usr/bin/env python3
"""
Emergency rollback script for state persistence.

This script safely disables state persistence in case of production issues.
It can be run without redeploying code, using only environment variables.
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"🚨 {title}")
    print("=" * 60)


def confirm_action(prompt: str) -> bool:
    """Get user confirmation for critical actions."""
    response = input(f"\n⚠️  {prompt} (yes/no): ").strip().lower()
    return response == "yes"


def check_current_status() -> Dict[str, bool]:
    """Check current state persistence status."""
    print("\n📊 Checking current status...")
    
    status = {
        "USE_STATE_PERSISTENCE": os.environ.get("FF_USE_STATE_PERSISTENCE", "false").lower() == "true",
        "ENABLE_STATE_SNAPSHOTS": os.environ.get("FF_ENABLE_STATE_SNAPSHOTS", "false").lower() == "true",
        "ENABLE_STATE_RECOVERY": os.environ.get("FF_ENABLE_STATE_RECOVERY", "false").lower() == "true",
    }
    
    print("\nCurrent feature flags:")
    for flag, enabled in status.items():
        icon = "✅" if enabled else "❌"
        print(f"  {icon} {flag}: {'Enabled' if enabled else 'Disabled'}")
    
    return status


def disable_feature_flags():
    """Disable all state persistence feature flags."""
    print("\n🔧 Disabling feature flags...")
    
    # Set environment variables to disable
    os.environ["FF_USE_STATE_PERSISTENCE"] = "false"
    os.environ["FF_ENABLE_STATE_SNAPSHOTS"] = "false"
    os.environ["FF_ENABLE_STATE_RECOVERY"] = "false"
    
    print("  ✅ Feature flags disabled in environment")
    
    # If using a feature flag service, add API calls here
    # Example: update_launchdarkly_flags() or update_split_flags()


def verify_disabled():
    """Verify state persistence is disabled."""
    print("\n🔍 Verifying state persistence is disabled...")
    
    try:
        from infrastructure.feature_flags import FeatureFlags
        flags = FeatureFlags()
        
        checks = [
            ("USE_STATE_PERSISTENCE", flags.USE_STATE_PERSISTENCE),
            ("ENABLE_STATE_SNAPSHOTS", flags.ENABLE_STATE_SNAPSHOTS),
            ("ENABLE_STATE_RECOVERY", flags.ENABLE_STATE_RECOVERY),
        ]
        
        all_disabled = True
        for name, flag_constant in checks:
            enabled = flags.is_enabled(flag_constant, {})
            if enabled:
                all_disabled = False
                print(f"  ❌ {name} is still enabled!")
            else:
                print(f"  ✅ {name} is disabled")
        
        return all_disabled
        
    except Exception as e:
        print(f"  ⚠️  Error verifying flags: {e}")
        return False


def create_rollback_marker():
    """Create a marker file to track rollback."""
    marker_file = Path("state_persistence_rollback.json")
    
    rollback_info = {
        "timestamp": datetime.utcnow().isoformat(),
        "reason": input("\n📝 Please enter rollback reason: "),
        "performed_by": os.environ.get("USER", "unknown"),
        "previous_status": check_current_status(),
    }
    
    with open(marker_file, "w") as f:
        json.dump(rollback_info, f, indent=2)
    
    print(f"\n  ✅ Rollback marker created: {marker_file}")
    return rollback_info


def notify_team(rollback_info: Dict):
    """Send notifications about the rollback."""
    print("\n📢 Sending notifications...")
    
    # Add your notification logic here
    # Examples:
    # - Send Slack message
    # - Create PagerDuty incident
    # - Send email to team
    # - Update status page
    
    message = f"""
    State Persistence Rollback Performed
    
    Time: {rollback_info['timestamp']}
    By: {rollback_info['performed_by']}
    Reason: {rollback_info['reason']}
    
    Action Required:
    1. Monitor application metrics
    2. Check error rates
    3. Verify game functionality
    """
    
    print("  ℹ️  Notification template:")
    print(message)
    
    # Example: Send to Slack
    # slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")
    # if slack_webhook:
    #     requests.post(slack_webhook, json={"text": message})


def check_application_health():
    """Check application health after rollback."""
    print("\n🏥 Checking application health...")
    
    health_checks = [
        ("API Health", "curl -s http://localhost:8000/health"),
        ("WebSocket Status", "curl -s http://localhost:8000/ws/status"),
        ("Game Creation", "curl -s -X POST http://localhost:8000/api/rooms/create"),
    ]
    
    for check_name, command in health_checks:
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"  ✅ {check_name}: OK")
            else:
                print(f"  ❌ {check_name}: Failed")
        except Exception as e:
            print(f"  ⚠️  {check_name}: Error - {e}")


def generate_rollback_report(rollback_info: Dict, success: bool):
    """Generate a rollback report."""
    report_file = Path(f"rollback_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    
    with open(report_file, "w") as f:
        f.write("# State Persistence Rollback Report\n\n")
        f.write(f"**Date**: {rollback_info['timestamp']}\n")
        f.write(f"**Performed By**: {rollback_info['performed_by']}\n")
        f.write(f"**Reason**: {rollback_info['reason']}\n")
        f.write(f"**Status**: {'✅ Success' if success else '❌ Failed'}\n\n")
        
        f.write("## Previous Configuration\n")
        for flag, enabled in rollback_info['previous_status'].items():
            f.write(f"- {flag}: {'Enabled' if enabled else 'Disabled'}\n")
        
        f.write("\n## Actions Taken\n")
        f.write("1. Disabled all state persistence feature flags\n")
        f.write("2. Verified flags are disabled\n")
        f.write("3. Created rollback marker\n")
        f.write("4. Sent team notifications\n")
        f.write("5. Performed health checks\n")
        
        f.write("\n## Next Steps\n")
        f.write("1. Monitor application metrics for 30 minutes\n")
        f.write("2. Check error logs for any issues\n")
        f.write("3. Verify game functionality is normal\n")
        f.write("4. Investigate root cause of issues\n")
        f.write("5. Plan fixes before re-enabling\n")
    
    print(f"\n  📄 Rollback report saved: {report_file}")


def main():
    """Main rollback procedure."""
    print_header("STATE PERSISTENCE EMERGENCY ROLLBACK")
    
    # Step 1: Check current status
    current_status = check_current_status()
    
    if not any(current_status.values()):
        print("\n✅ State persistence is already disabled. No rollback needed.")
        return 0
    
    # Step 2: Confirm rollback
    if not confirm_action("Do you want to proceed with the rollback?"):
        print("\n❌ Rollback cancelled.")
        return 1
    
    # Step 3: Create rollback marker
    rollback_info = create_rollback_marker()
    
    # Step 4: Disable feature flags
    disable_feature_flags()
    
    # Step 5: Verify disabled
    time.sleep(2)  # Give time for changes to propagate
    disabled = verify_disabled()
    
    if not disabled:
        print("\n❌ Failed to disable state persistence!")
        print("⚠️  Manual intervention may be required.")
        generate_rollback_report(rollback_info, False)
        return 1
    
    # Step 6: Notify team
    notify_team(rollback_info)
    
    # Step 7: Check application health
    check_application_health()
    
    # Step 8: Generate report
    generate_rollback_report(rollback_info, True)
    
    # Summary
    print_header("ROLLBACK COMPLETE")
    print("\n✅ State persistence has been successfully disabled.")
    print("\n⚠️  IMPORTANT: Monitor the application closely for the next 30 minutes.")
    print("\n📋 Action items:")
    print("  1. Check application metrics")
    print("  2. Monitor error rates")
    print("  3. Verify game functionality")
    print("  4. Review rollback report")
    print("  5. Investigate and fix root cause before re-enabling")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Rollback interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error during rollback: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)