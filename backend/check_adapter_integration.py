#!/usr/bin/env python3
"""
Quick check of adapter integration status
"""

import os
import json


def check_integration_status():
    """Check the status of adapter integration"""
    print("🔍 Adapter Integration Status Check")
    print("=" * 60)
    
    # Check if files exist
    files_to_check = [
        ("WebSocket Handler", "api/routes/ws.py"),
        ("Adapter Wrapper", "api/routes/ws_adapter_wrapper.py"),
        ("Integration Guide", "WS_INTEGRATION_GUIDE.md"),
        ("Deployment Runbook", "ADAPTER_DEPLOYMENT_RUNBOOK.md"),
        ("Metrics Collector", "adapter_metrics_collector.py"),
        ("Shadow Monitor", "monitor_shadow_mode.py"),
    ]
    
    print("\n📁 Required Files:")
    all_exist = True
    for name, path in files_to_check:
        exists = os.path.exists(path)
        status = "✅" if exists else "❌"
        print(f"  {status} {name:<20} - {path}")
        if not exists:
            all_exist = False
    
    # Check if integration is in ws.py
    print("\n🔧 Integration Status:")
    if os.path.exists("api/routes/ws.py"):
        with open("api/routes/ws.py", 'r') as f:
            content = f.read()
            
        has_import = "from api.routes.ws_adapter_wrapper import adapter_wrapper" in content
        has_integration = "adapter_wrapper.try_handle_with_adapter" in content
        has_status_endpoint = "get_adapter_status" in content
        
        print(f"  {'✅' if has_import else '❌'} Adapter wrapper imported")
        print(f"  {'✅' if has_integration else '❌'} Adapter integration added")
        print(f"  {'✅' if has_status_endpoint else '❌'} Status endpoint added")
    
    # Check environment
    print("\n🌍 Current Environment:")
    adapter_enabled = os.getenv("ADAPTER_ENABLED", "false")
    rollout_percentage = os.getenv("ADAPTER_ROLLOUT_PERCENTAGE", "0")
    shadow_enabled = os.getenv("SHADOW_MODE_ENABLED", "false")
    
    print(f"  ADAPTER_ENABLED: {adapter_enabled}")
    print(f"  ADAPTER_ROLLOUT_PERCENTAGE: {rollout_percentage}")
    print(f"  SHADOW_MODE_ENABLED: {shadow_enabled}")
    
    # Summary
    print("\n📊 Summary:")
    if all_exist and has_import and has_integration:
        print("  ✅ Adapter system is fully integrated!")
        print("\n  Next steps:")
        print("  1. Set ADAPTER_ENABLED=true to enable adapters")
        print("  2. Set ADAPTER_ROLLOUT_PERCENTAGE=1 to start rollout")
        print("  3. Monitor with: python3 adapter_metrics_collector.py")
    else:
        print("  ❌ Integration incomplete - check missing items above")
    
    # Test scripts
    print("\n🧪 Available Test Scripts:")
    test_scripts = [
        "test_adapter_integration_live.py - Test with live server",
        "monitor_shadow_mode.py - Monitor shadow mode execution",
        "adapter_metrics_collector.py - Collect performance metrics",
        "tests/contracts/test_adapter_contracts.py - Run contract tests",
    ]
    
    for script in test_scripts:
        print(f"  • {script}")


if __name__ == "__main__":
    check_integration_status()