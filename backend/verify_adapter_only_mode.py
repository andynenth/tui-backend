#!/usr/bin/env python3
"""
Verify that adapter-only mode is properly configured and active.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Check environment variables
print("🔍 Checking Environment Variables:")
print("-" * 50)

adapter_vars = {
    "ADAPTER_ENABLED": os.getenv("ADAPTER_ENABLED", "not set"),
    "ADAPTER_ROLLOUT_PERCENTAGE": os.getenv("ADAPTER_ROLLOUT_PERCENTAGE", "not set"),
}

ff_vars = {
    "FF_USE_CLEAN_ARCHITECTURE": os.getenv("FF_USE_CLEAN_ARCHITECTURE", "not set"),
    "FF_USE_CONNECTION_ADAPTERS": os.getenv("FF_USE_CONNECTION_ADAPTERS", "not set"),
    "FF_USE_ROOM_ADAPTERS": os.getenv("FF_USE_ROOM_ADAPTERS", "not set"),
    "FF_USE_GAME_ADAPTERS": os.getenv("FF_USE_GAME_ADAPTERS", "not set"),
    "FF_USE_LOBBY_ADAPTERS": os.getenv("FF_USE_LOBBY_ADAPTERS", "not set"),
}

print("Adapter Routing Variables:")
for key, value in adapter_vars.items():
    status = "✅" if value.lower() in ["true", "100"] else "❌"
    print(f"  {status} {key}: {value}")

print("\nFeature Flag Variables:")
for key, value in ff_vars.items():
    status = "✅" if value.lower() == "true" else "⚠️"
    print(f"  {status} {key}: {value}")

# Check adapter wrapper status
print("\n🔍 Checking Adapter System Status:")
print("-" * 50)

try:
    from api.routes.ws_adapter_wrapper import adapter_wrapper
    
    # Initialize if needed
    if not adapter_wrapper._initialized:
        adapter_wrapper.initialize()
    
    status = adapter_wrapper.get_status()
    
    print(f"Adapter Wrapper Status:")
    print(f"  Enabled: {status['enabled']} {'✅' if status['enabled'] else '❌'}")
    print(f"  Rollout: {status['rollout_percentage']}% {'✅' if status['rollout_percentage'] >= 100 else '❌'}")
    print(f"  Initialized: {status['initialized']} {'✅' if status['initialized'] else '❌'}")
    
    if 'adapter_system' in status:
        sys_status = status['adapter_system']
        print(f"\nIntegrated Adapter System:")
        print(f"  Global Enabled: {sys_status['global_enabled']} {'✅' if sys_status['global_enabled'] else '❌'}")
        print(f"  Adapter-Only Mode: {sys_status.get('adapter_only_mode', False)} {'✅' if sys_status.get('adapter_only_mode') else '❌'}")
        print(f"  Coverage: {sys_status['enabled_count']}/{sys_status['total_adapters']} ({sys_status['coverage_percent']}%)")
        
        print(f"\nPhase Coverage:")
        for phase, enabled in sys_status['phases'].items():
            print(f"    {phase}: {'✅' if enabled else '❌'}")
    
    # Final verdict
    print("\n🎯 Final Status:")
    print("-" * 50)
    
    adapter_only_active = (
        adapter_vars["ADAPTER_ENABLED"] == "true" and
        adapter_vars["ADAPTER_ROLLOUT_PERCENTAGE"] == "100" and
        status.get('adapter_system', {}).get('adapter_only_mode', False)
    )
    
    if adapter_only_active:
        print("✅ ADAPTER-ONLY MODE IS ACTIVE!")
        print("   - All traffic will be handled by clean architecture")
        print("   - Legacy code will NOT be executed")
        print("   - Any unhandled events will return errors")
    else:
        print("❌ ADAPTER-ONLY MODE IS NOT ACTIVE")
        print("   - Traffic may still go to legacy code")
        print("   - Check environment variables above")
        
except Exception as e:
    print(f"❌ Error checking adapter status: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("To enable adapter-only mode, ensure:")
print("  export ADAPTER_ENABLED=true")
print("  export ADAPTER_ROLLOUT_PERCENTAGE=100")
print("Then restart your server.")