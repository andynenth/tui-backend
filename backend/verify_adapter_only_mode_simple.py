#!/usr/bin/env python3
"""
Simple verification that adapter-only mode is properly configured.
This version doesn't import any modules that create async tasks.
"""

import os
import sys

print("🔍 Checking Adapter-Only Mode Configuration:")
print("=" * 50)

# Check environment variables
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

print("\n🚦 Adapter Routing Variables (CRITICAL):")
print("-" * 50)
for key, value in adapter_vars.items():
    if key == "ADAPTER_ENABLED":
        status = "✅" if value.lower() == "true" else "❌"
    else:  # ADAPTER_ROLLOUT_PERCENTAGE
        status = "✅" if value == "100" else "❌"
    print(f"  {status} {key}: {value}")

print("\n🏗️ Feature Flag Variables (Informational):")
print("-" * 50)
for key, value in ff_vars.items():
    status = "✅" if value.lower() == "true" else "⚠️"
    print(f"  {status} {key}: {value}")

# Final verdict
print("\n🎯 Adapter-Only Mode Status:")
print("=" * 50)

adapter_enabled = adapter_vars["ADAPTER_ENABLED"].lower() == "true"
adapter_at_100 = adapter_vars["ADAPTER_ROLLOUT_PERCENTAGE"] == "100"

if adapter_enabled and adapter_at_100:
    print("✅ ADAPTER-ONLY MODE SHOULD BE ACTIVE!")
    print("   Configuration is correct for clean architecture only")
    print("\n   When server is running with these settings:")
    print("   - All traffic routes through clean architecture")
    print("   - Legacy code initialization still happens (but unused)")
    print("   - No fallback to legacy on adapter errors")
else:
    print("❌ ADAPTER-ONLY MODE IS NOT CONFIGURED")
    if not adapter_enabled:
        print("   - ADAPTER_ENABLED is not 'true'")
    if not adapter_at_100:
        print("   - ADAPTER_ROLLOUT_PERCENTAGE is not '100'")
    print("\n   Traffic will fall back to legacy code!")

print("\n📋 Expected Server Logs:")
print("-" * 50)
if adapter_enabled and adapter_at_100:
    print("You should see in server logs:")
    print('  - "Adapter system initialized in ADAPTER-ONLY MODE"')
    print('  - "ADAPTER-ONLY MODE ENABLED: No legacy fallback!"')
    print('  - Room creation logs from "api.adapters.room_adapters"')
else:
    print("You will see:")
    print('  - Legacy component initialization (BOT_MANAGER, etc.)')
    print('  - Mixed legacy and adapter logs')
    print('  - Potential synchronization issues')

print("\n💡 Note: The environment variables must be set")
print("   in the same shell/process as your server!")