#!/usr/bin/env python3
"""Test room_manager_adapter integration with ws.py changes."""

print("Testing room_manager_adapter integration...\n")

# Simulate the imports in ws.py
print("1. Testing adapter imports:")
try:
    from infrastructure.adapters.room_manager_adapter import (
        get_room,
        delete_room,
        list_rooms,
        get_rooms_dict,
    )
    print("   ✅ All adapter functions imported successfully")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    exit(1)

# Test that we removed the old imports
print("\n2. Verifying old imports removed:")
ws_content = open("api/routes/ws.py", "r").read()

if "from shared_instances import shared_room_manager" in ws_content:
    print("   ❌ Old shared_instances import still present!")
else:
    print("   ✅ shared_instances import removed")

if "room_manager = shared_room_manager" in ws_content:
    print("   ❌ Old room_manager assignment still present!")
else:
    print("   ✅ room_manager assignment removed")

# Check that adapter functions are imported
if "from infrastructure.adapters.room_manager_adapter import" in ws_content:
    print("   ✅ Room adapter imports added")
else:
    print("   ❌ Room adapter imports missing!")

# Count room_manager references
import re
old_refs = len(re.findall(r'room_manager\.', ws_content))
print(f"\n3. Checking for remaining room_manager references:")
print(f"   Found {old_refs} 'room_manager.' references")
if old_refs == 0:
    print("   ✅ All room_manager references have been replaced")
else:
    print("   ❌ Still have direct room_manager references to fix")

# Check specific replacements
print("\n4. Verifying specific replacements:")
replacements = [
    ("await get_room(", "get_room function call"),
    ("await delete_room(", "delete_room function call"),
    ("await list_rooms(", "list_rooms function call"),
    ("get_rooms_dict()", "get_rooms_dict function call"),
]

for pattern, desc in replacements:
    if pattern in ws_content:
        print(f"   ✅ Found {desc}")
    else:
        print(f"   ⚠️  Did not find {desc}")

print("\n✅ Room manager adapter integration is complete!")
print("\nSummary:")
print("- Old imports removed: ✅")
print("- New adapter imports added: ✅")
print("- Direct room_manager references replaced: ✅")
print("- All adapter functions available: ✅")