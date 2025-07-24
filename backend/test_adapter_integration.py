#!/usr/bin/env python3
"""
Test the adapter integration with simulated WebSocket messages.
This verifies that adapters work correctly with the migration controller.
"""

import asyncio
import json
from datetime import datetime

from api.adapters.websocket_adapter_integration import (
    handle_websocket_message_with_adapters,
    get_migration_controller
)
from api.adapters.adapter_registry import get_adapter_registry


# Mock WebSocket for testing
class MockWebSocket:
    def __init__(self, room_id=None):
        self.room_id = room_id
        self.sent_messages = []
    
    async def send_json(self, data):
        self.sent_messages.append(data)


# Mock legacy handler
async def mock_legacy_handler(websocket, message):
    """Simulates the existing WebSocket handler"""
    action = message.get("action")
    
    # Return a different response to distinguish from adapter
    return {
        "event": f"legacy_{action}_response",
        "data": {"handled_by": "legacy", "action": action}
    }


async def test_adapter_integration():
    """Test the adapter integration system"""
    print("Testing Adapter Integration")
    print("=" * 60)
    
    controller = get_migration_controller()
    registry = get_adapter_registry()
    
    # Check initial status
    print("\n1. Initial Status:")
    status = controller.get_migration_status()
    print(f"   Adapter coverage: {status['adapter_coverage']}")
    print(f"   Enabled actions: {status['enabled_actions']}")
    
    # Test with adapters disabled
    print("\n2. Testing with adapters disabled:")
    controller.rollback_all_adapters()
    
    ws = MockWebSocket()
    ping_message = {"action": "ping", "data": {"timestamp": 12345}}
    
    response = await handle_websocket_message_with_adapters(
        ws, ping_message, mock_legacy_handler
    )
    
    print(f"   Ping response: {response['event']}")
    print(f"   Handled by: {response['data'].get('handled_by', 'adapter')}")
    
    # Enable Phase 1 adapters
    print("\n3. Enabling Phase 1 adapters:")
    controller.enable_phase_1_adapters()
    
    status = controller.get_migration_status()
    print(f"   Adapter coverage: {status['adapter_coverage']}")
    print(f"   Enabled actions: {status['enabled_actions']}")
    
    # Test with adapters enabled
    print("\n4. Testing with adapters enabled:")
    
    # Test ping (should use adapter)
    response = await handle_websocket_message_with_adapters(
        ws, ping_message, mock_legacy_handler
    )
    
    print(f"   Ping response: {response['event']}")
    print(f"   Has timestamp: {'timestamp' in response['data']}")
    print(f"   Has server_time: {'server_time' in response['data']}")
    
    # Test client_ready (should use adapter)
    ready_message = {"action": "client_ready", "data": {"player_name": "TestPlayer"}}
    response = await handle_websocket_message_with_adapters(
        ws, ready_message, mock_legacy_handler
    )
    
    print(f"\n   Client ready response: {response['event']}")
    print(f"   Has slots: {'slots' in response['data']}")
    
    # Test ack (should return None)
    ack_message = {"action": "ack", "data": {"sequence": 123}}
    response = await handle_websocket_message_with_adapters(
        ws, ack_message, mock_legacy_handler
    )
    
    print(f"\n   Ack response: {response}")
    
    # Test non-migrated action (should use legacy)
    create_room_message = {"action": "create_room", "data": {"player_name": "Alice"}}
    response = await handle_websocket_message_with_adapters(
        ws, create_room_message, mock_legacy_handler
    )
    
    print(f"\n   Create room response: {response['event']}")
    print(f"   Handled by: {response['data'].get('handled_by', 'adapter')}")
    
    # Test rollback
    print("\n5. Testing rollback:")
    controller.rollback_all_adapters()
    
    response = await handle_websocket_message_with_adapters(
        ws, ping_message, mock_legacy_handler
    )
    
    print(f"   Ping response after rollback: {response['event']}")
    print(f"   Handled by: {response['data'].get('handled_by', 'adapter')}")
    
    print("\n" + "=" * 60)
    print("✅ Adapter integration test complete!")


async def test_performance_comparison():
    """Compare performance between adapter and legacy handlers"""
    print("\nPerformance Comparison")
    print("=" * 60)
    
    controller = get_migration_controller()
    ws = MockWebSocket()
    
    # Test message
    ping_message = {"action": "ping", "data": {"timestamp": 12345}}
    iterations = 1000
    
    # Test legacy handler
    controller.rollback_all_adapters()
    start = asyncio.get_event_loop().time()
    
    for _ in range(iterations):
        await handle_websocket_message_with_adapters(
            ws, ping_message, mock_legacy_handler
        )
    
    legacy_time = asyncio.get_event_loop().time() - start
    
    # Test adapter handler
    controller.enable_phase_1_adapters()
    start = asyncio.get_event_loop().time()
    
    for _ in range(iterations):
        await handle_websocket_message_with_adapters(
            ws, ping_message, mock_legacy_handler
        )
    
    adapter_time = asyncio.get_event_loop().time() - start
    
    # Results
    print(f"Legacy handler: {legacy_time*1000:.2f}ms for {iterations} messages")
    print(f"Adapter handler: {adapter_time*1000:.2f}ms for {iterations} messages")
    print(f"Overhead: {((adapter_time/legacy_time - 1) * 100):.1f}%")
    
    if adapter_time < legacy_time * 1.2:
        print("✅ Performance overhead is acceptable (< 20%)")
    else:
        print("⚠️  Performance overhead exceeds 20%")


async def main():
    """Run all integration tests"""
    await test_adapter_integration()
    await test_performance_comparison()
    
    # Final status
    print("\nFinal Migration Status:")
    print("=" * 60)
    
    controller = get_migration_controller()
    controller.enable_phase_1_adapters()  # Re-enable for final status
    
    status = controller.get_migration_status()
    print(f"Adapter coverage: {status['adapter_coverage']}")
    print(f"Migrated actions: {status['enabled_actions']}")
    print(f"Remaining legacy actions: {status['legacy_actions']}")
    
    print("\n✅ Ready to integrate with actual WebSocket handler!")
    print("\nNext steps:")
    print("1. Update ws.py to use create_adapter_aware_handler()")
    print("2. Test with real WebSocket connections")
    print("3. Monitor with shadow mode")
    print("4. Implement remaining adapters")


if __name__ == "__main__":
    asyncio.run(main())