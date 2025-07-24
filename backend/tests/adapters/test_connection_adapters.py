"""
Tests for connection-related WebSocket adapters.
Verifies adapters match the contract requirements.
"""

import asyncio
import json
from pathlib import Path

# Since we can't use pytest, create simple test framework
class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def assert_equal(self, actual, expected, message=""):
        if actual == expected:
            self.passed += 1
            print(f"  ✅ {message}")
        else:
            self.failed += 1
            self.errors.append(f"{message}: expected {expected}, got {actual}")
            print(f"  ❌ {message}: expected {expected}, got {actual}")
    
    def assert_in(self, key, dictionary, message=""):
        if key in dictionary:
            self.passed += 1
            print(f"  ✅ {message}")
        else:
            self.failed += 1
            self.errors.append(f"{message}: key '{key}' not found")
            print(f"  ❌ {message}: key '{key}' not found")
    
    def assert_not_none(self, value, message=""):
        if value is not None:
            self.passed += 1
            print(f"  ✅ {message}")
        else:
            self.failed += 1
            self.errors.append(f"{message}: value is None")
            print(f"  ❌ {message}: value is None")
    
    def print_summary(self):
        print(f"\nTest Summary: {self.passed} passed, {self.failed} failed")
        if self.errors:
            print("Errors:")
            for error in self.errors:
                print(f"  - {error}")


async def test_ping_adapter():
    """Test PingAdapter against contract requirements"""
    print("\nTesting PingAdapter")
    print("-" * 40)
    
    from api.adapters.connection_adapters import PingAdapter
    adapter = PingAdapter()
    result = TestResult()
    
    # Test 1: Basic ping with timestamp
    print("\nTest 1: Ping with timestamp")
    message = {"action": "ping", "data": {"timestamp": 1234567890}}
    response = await adapter.handle(None, message)
    
    result.assert_equal(response["event"], "pong", "Response event is 'pong'")
    result.assert_in("timestamp", response["data"], "Timestamp echoed back")
    result.assert_equal(response["data"]["timestamp"], 1234567890, "Timestamp value matches")
    result.assert_in("server_time", response["data"], "Server time included")
    result.assert_not_none(response["data"]["server_time"], "Server time has value")
    
    # Test 2: Ping without timestamp
    print("\nTest 2: Ping without timestamp")
    message = {"action": "ping", "data": {}}
    response = await adapter.handle(None, message)
    
    result.assert_equal(response["event"], "pong", "Response event is 'pong'")
    result.assert_in("server_time", response["data"], "Server time included")
    result.assert_equal("timestamp" in response["data"], False, "No timestamp in response")
    
    # Test 3: Ping with room state
    print("\nTest 3: Ping with room state")
    message = {"action": "ping", "data": {"timestamp": 9999}}
    room_state = {"room_id": "ABC123"}
    response = await adapter.handle(None, message, room_state)
    
    result.assert_in("room_id", response["data"], "Room ID included")
    result.assert_equal(response["data"]["room_id"], "ABC123", "Room ID matches")
    
    # Compare with golden master
    print("\nComparing with golden master...")
    golden_master_path = Path("tests/contracts/golden_masters")
    ping_masters = list(golden_master_path.glob("ping_*.json"))
    
    if ping_masters:
        with open(ping_masters[0], 'r') as f:
            golden = json.load(f)
            golden_response = golden.get("response", {})
            
            # Check structure matches
            if golden_response:
                result.assert_equal(
                    response["event"], 
                    golden_response["event"], 
                    "Event matches golden master"
                )
                result.assert_equal(
                    set(response["data"].keys()) - {"server_time"},  # Exclude dynamic field
                    set(golden_response["data"].keys()) - {"server_time"},
                    "Response keys match golden master"
                )
    
    result.print_summary()
    return result.failed == 0


async def test_client_ready_adapter():
    """Test ClientReadyAdapter against contract requirements"""
    print("\nTesting ClientReadyAdapter")
    print("-" * 40)
    
    from api.adapters.connection_adapters import ClientReadyAdapter
    adapter = ClientReadyAdapter()
    result = TestResult()
    
    # Test 1: Client ready in lobby
    print("\nTest 1: Client ready in lobby")
    message = {"action": "client_ready", "data": {"player_name": "TestPlayer"}}
    response = await adapter.handle(None, message)
    
    result.assert_equal(response["event"], "room_state_update", "Response event is 'room_state_update'")
    result.assert_in("slots", response["data"], "Slots field included")
    result.assert_in("host_name", response["data"], "Host name field included")
    
    # Test 2: Client ready in room
    print("\nTest 2: Client ready in room")
    room_state = {
        "room_id": "ABC123",
        "players": [{"name": "Alice", "slot": 0}],
        "host_name": "Alice"
    }
    response = await adapter.handle(None, message, room_state)
    
    result.assert_equal(response["event"], "room_state_update", "Response event is 'room_state_update'")
    result.assert_equal(response["data"]["slots"], room_state["players"], "Slots match room state")
    result.assert_equal(response["data"]["host_name"], "Alice", "Host name matches")
    
    result.print_summary()
    return result.failed == 0


async def test_ack_adapter():
    """Test AckAdapter against contract requirements"""
    print("\nTesting AckAdapter")
    print("-" * 40)
    
    from api.adapters.connection_adapters import AckAdapter
    adapter = AckAdapter()
    result = TestResult()
    
    # Test: Ack returns no response
    print("\nTest: Ack returns no response")
    message = {"action": "ack", "data": {"sequence": 123, "client_id": "client123"}}
    response = await adapter.handle(None, message)
    
    result.assert_equal(response, None, "Ack returns None (no response)")
    
    result.print_summary()
    return result.failed == 0


async def main():
    """Run all adapter tests"""
    print("=" * 60)
    print("Connection Adapter Tests")
    print("=" * 60)
    
    all_passed = True
    
    # Run tests
    all_passed &= await test_ping_adapter()
    all_passed &= await test_client_ready_adapter()
    all_passed &= await test_ack_adapter()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All adapter tests passed!")
    else:
        print("❌ Some adapter tests failed!")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)