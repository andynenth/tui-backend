#!/usr/bin/env python3
"""
Verify adapter integration files are ready
"""

import os
import glob

def verify_files():
    """Verify all required files for adapter integration exist"""
    
    print("🔍 Verifying Adapter Integration Files\n")
    
    required_files = [
        # Adapter implementations
        ("api/adapters/connection_adapters.py", "Connection adapters"),
        ("api/adapters/room_adapters.py", "Room adapters"),
        ("api/adapters/lobby_adapters.py", "Lobby adapters"),
        ("api/adapters/game_adapters.py", "Game adapters"),
        ("api/adapters/integrated_adapter_system.py", "Integrated adapter system"),
        
        # Integration files
        ("api/routes/ws_adapter_wrapper.py", "WebSocket adapter wrapper"),
        ("WS_INTEGRATION_GUIDE.md", "Integration guide"),
        
        # Test files
        ("tests/adapters/test_connection_adapters.py", "Connection adapter tests"),
        ("tests/adapters/test_room_adapters.py", "Room adapter tests"),
        ("tests/adapters/test_lobby_adapters.py", "Lobby adapter tests"),
        ("tests/adapters/test_game_adapters.py", "Game adapter tests"),
    ]
    
    print("Required Files:")
    print("-" * 60)
    
    all_exist = True
    for file_path, description in required_files:
        exists = os.path.exists(file_path)
        status = "✅" if exists else "❌"
        print(f"{status} {description:<30} - {file_path}")
        if not exists:
            all_exist = False
    
    print("\n" + "=" * 60)
    
    if all_exist:
        print("✅ All required files exist!")
    else:
        print("❌ Some files are missing!")
        return False
    
    # Check adapter counts
    print("\n📊 Adapter Implementation Stats:")
    print("-" * 60)
    
    adapter_files = {
        "Connection": "api/adapters/connection_adapters.py",
        "Room": "api/adapters/room_adapters.py",
        "Lobby": "api/adapters/lobby_adapters.py",
        "Game": "api/adapters/game_adapters.py"
    }
    
    total_adapters = 0
    for category, file_path in adapter_files.items():
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                # Count adapter classes
                adapter_count = content.count("Adapter:")
                total_adapters += adapter_count
                print(f"{category:<15} {adapter_count:>2} adapters")
    
    print(f"{'Total':<15} {total_adapters:>2} adapters")
    
    # Check integration guide
    print("\n📋 Integration Steps Summary:")
    print("-" * 60)
    
    if os.path.exists("WS_INTEGRATION_GUIDE.md"):
        print("✅ Integration guide available")
        print("\nKey steps:")
        print("1. Add import: from api.routes.ws_adapter_wrapper import adapter_wrapper")
        print("2. Add adapter check after message validation")
        print("3. Set environment variables for rollout")
        print("4. Monitor adapter status endpoint")
    else:
        print("❌ Integration guide missing!")
    
    # Environment variables
    print("\n🔧 Environment Variables for Rollout:")
    print("-" * 60)
    print("ADAPTER_ENABLED=false          # Set to 'true' to enable")
    print("ADAPTER_ROLLOUT_PERCENTAGE=0   # 0-100 (start low, increase gradually)")
    print("SHADOW_MODE_ENABLED=false      # Set to 'true' for shadow testing")
    print("SHADOW_MODE_PERCENTAGE=1       # Shadow mode sample rate")
    
    print("\n📈 Recommended Rollout Plan:")
    print("-" * 60)
    print("1. Shadow mode at 1%    - Test without affecting users")
    print("2. Shadow mode at 10%   - Broader testing")
    print("3. Live rollout at 1%   - Start real usage")
    print("4. Increase to 5%       - Monitor for issues")
    print("5. Increase to 25%      - Quarter of traffic")
    print("6. Increase to 50%      - Half of traffic")
    print("7. Full rollout 100%    - Complete migration")
    
    return True


def check_ws_py():
    """Check if ws.py exists and show integration point"""
    print("\n\n🔍 Checking ws.py Integration Point")
    print("=" * 60)
    
    ws_file = "api/routes/ws.py"
    if not os.path.exists(ws_file):
        print(f"❌ {ws_file} not found!")
        return
    
    print(f"✅ {ws_file} exists")
    
    with open(ws_file, 'r') as f:
        lines = f.readlines()
    
    # Find validation section
    validation_line = None
    for i, line in enumerate(lines):
        if "validate_websocket_message" in line:
            validation_line = i
            break
    
    if validation_line:
        print(f"\n📍 Integration point found at line {validation_line + 1}")
        print("   Add adapter check after message validation")
        print("\nCode to add:")
        print("-" * 40)
        print("""
            # ===== ADAPTER INTEGRATION START =====
            adapter_response = await adapter_wrapper.try_handle_with_adapter(
                registered_ws, message, room_id
            )
            
            if adapter_response is not None:
                if adapter_response:
                    await registered_ws.send_json(adapter_response)
                continue
            # ===== ADAPTER INTEGRATION END =====
""")
    else:
        print("⚠️  Could not find validation section automatically")
        print("   Look for 'validate_websocket_message' in ws.py")


if __name__ == "__main__":
    if verify_files():
        check_ws_py()
        print("\n✅ Adapter system is ready for integration!")
        print("📖 See WS_INTEGRATION_GUIDE.md for detailed instructions")
    else:
        print("\n❌ Fix missing files before proceeding")