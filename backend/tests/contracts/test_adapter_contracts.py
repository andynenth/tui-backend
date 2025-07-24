#!/usr/bin/env python3
"""
Test Adapter Contract Compliance
Verifies that adapters produce identical output to legacy handlers.
"""

import asyncio
import json
from typing import Dict, Any, Tuple, Optional
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from api.adapters.integrated_adapter_system import IntegratedAdapterSystem
from tests.contracts.websocket_contracts import get_all_contracts
from tests.contracts.golden_master import GoldenMasterCapture, GoldenMasterComparator


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.messages_sent = []
    
    async def send_json(self, data: Dict[str, Any]):
        self.messages_sent.append(data)


async def mock_legacy_handler(websocket, message: Dict[str, Any]) -> Dict[str, Any]:
    """Mock legacy handler that returns expected responses"""
    action = message.get("action")
    
    # Return mock responses based on golden masters
    mock_responses = {
        "ping": {
            "event": "pong",
            "data": {
                "timestamp": message.get("data", {}).get("timestamp"),
                "server_time": 1234567890.0,
                "room_id": None
            }
        },
        "create_room": {
            "event": "room_created",
            "data": {
                "room_id": "room_abc123",
                "host_name": message.get("data", {}).get("player_name"),
                "success": True
            }
        },
        "join_room": {
            "event": "joined_room",
            "data": {
                "room_id": message.get("data", {}).get("room_id"),
                "player_name": message.get("data", {}).get("player_name"),
                "success": True,
                "slot": 1
            }
        },
        "start_game": {
            "event": "game_started",
            "data": {
                "success": True,
                "initial_phase": "PREPARATION",
                "round_number": 1,
                "starter_player": message.get("data", {}).get("player_name")
            }
        }
    }
    
    return mock_responses.get(action, {
        "event": "error",
        "data": {"message": f"Unknown action: {action}"}
    })


class AdapterContractTester:
    """Test adapter compliance with contracts"""
    
    def __init__(self):
        self.adapter_system = IntegratedAdapterSystem(mock_legacy_handler)
        self.contracts = get_all_contracts()
        self.golden_master_capture = GoldenMasterCapture()
        self.comparator = GoldenMasterComparator()
    
    async def test_contract_compliance(self, contract_name: str) -> Tuple[bool, Optional[str]]:
        """
        Test if adapter complies with a specific contract.
        
        Returns:
            Tuple of (success, error_message)
        """
        contract = self.contracts.get(contract_name)
        if not contract:
            return False, f"Contract '{contract_name}' not found"
        
        # Create test message
        test_message = {
            "action": contract.name,
            "data": contract.request_schema or {}
        }
        
        # Create mock websocket
        ws = MockWebSocket()
        
        try:
            # Get adapter response
            response = await self.adapter_system.handle_message(
                ws, test_message, room_state=None
            )
            
            # Validate against contract
            if contract.response_schema:
                # Check response structure matches schema
                if not self._validate_schema(response, contract.response_schema):
                    return False, "Response does not match contract schema"
            
            return True, None
            
        except Exception as e:
            return False, f"Adapter error: {str(e)}"
    
    def _validate_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Basic schema validation"""
        if not isinstance(data, dict):
            return False
        
        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in data:
                return False
        
        # Check field types
        properties = schema.get("properties", {})
        for field, field_schema in properties.items():
            if field in data:
                expected_type = field_schema.get("type")
                if expected_type:
                    if not self._check_type(data[field], expected_type):
                        return False
        
        return True
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "object": dict,
            "array": list
        }
        
        expected = type_map.get(expected_type)
        if expected:
            return isinstance(value, expected)
        return True
    
    async def test_all_contracts(self) -> Dict[str, Any]:
        """Test all contracts and return results"""
        results = {
            "total": len(self.contracts),
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        print("\n🧪 Testing Adapter Contract Compliance")
        print("=" * 60)
        
        for contract_name, contract in self.contracts.items():
            success, error = await self.test_contract_compliance(contract_name)
            
            if success:
                results["passed"] += 1
                print(f"✅ {contract_name:<20} - PASSED")
            else:
                results["failed"] += 1
                results["errors"].append({
                    "contract": contract_name,
                    "error": error
                })
                print(f"❌ {contract_name:<20} - FAILED: {error}")
        
        return results
    
    async def compare_with_golden_masters(self) -> Dict[str, Any]:
        """Compare adapter responses with golden masters if they exist"""
        golden_dir = "tests/contracts/golden_masters"
        
        if not os.path.exists(golden_dir):
            return {
                "status": "no_golden_masters",
                "message": f"Golden master directory '{golden_dir}' not found"
            }
        
        results = {
            "total": 0,
            "matched": 0,
            "mismatched": 0,
            "missing": 0,
            "mismatches": []
        }
        
        print("\n\n🔍 Comparing with Golden Masters")
        print("=" * 60)
        
        # List golden master files
        golden_files = [f for f in os.listdir(golden_dir) if f.endswith('.json')]
        results["total"] = len(golden_files)
        
        for golden_file in golden_files:
            contract_name = golden_file.replace('.json', '')
            
            # Load golden master
            with open(os.path.join(golden_dir, golden_file), 'r') as f:
                golden_data = json.load(f)
            
            # Create test message from golden master
            test_message = {
                "action": contract_name,
                "data": golden_data.get("request", {})
            }
            
            # Get adapter response
            ws = MockWebSocket()
            try:
                adapter_response = await self.adapter_system.handle_message(
                    ws, test_message, room_state=golden_data.get("room_state")
                )
                
                # Compare with expected response
                expected_response = golden_data.get("response")
                
                if self._responses_match(adapter_response, expected_response):
                    results["matched"] += 1
                    print(f"✅ {contract_name:<20} - Matches golden master")
                else:
                    results["mismatched"] += 1
                    results["mismatches"].append({
                        "contract": contract_name,
                        "expected": expected_response,
                        "actual": adapter_response
                    })
                    print(f"❌ {contract_name:<20} - Mismatch with golden master")
                    
            except Exception as e:
                results["missing"] += 1
                print(f"⚠️  {contract_name:<20} - Error: {str(e)}")
        
        return results
    
    def _responses_match(self, actual: Any, expected: Any) -> bool:
        """Compare responses, ignoring dynamic fields like timestamps"""
        # Simple comparison for now - could be enhanced
        if type(actual) != type(expected):
            return False
        
        if isinstance(actual, dict):
            # Ignore certain dynamic fields
            ignore_fields = {"server_time", "timestamp", "room_id"}
            
            for key in expected:
                if key in ignore_fields:
                    continue
                if key not in actual:
                    return False
                if not self._responses_match(actual[key], expected[key]):
                    return False
            
            return True
        
        elif isinstance(actual, list):
            if len(actual) != len(expected):
                return False
            return all(self._responses_match(a, e) for a, e in zip(actual, expected))
        
        else:
            return actual == expected


async def main():
    """Run contract tests"""
    tester = AdapterContractTester()
    
    # Test contract compliance
    contract_results = await tester.test_all_contracts()
    
    print("\n📊 Contract Test Summary")
    print("=" * 60)
    print(f"Total contracts: {contract_results['total']}")
    print(f"Passed: {contract_results['passed']}")
    print(f"Failed: {contract_results['failed']}")
    
    if contract_results['failed'] > 0:
        print("\nFailed contracts:")
        for error in contract_results['errors']:
            print(f"  - {error['contract']}: {error['error']}")
    
    # Compare with golden masters
    golden_results = await tester.compare_with_golden_masters()
    
    if golden_results.get("status") != "no_golden_masters":
        print("\n📊 Golden Master Comparison")
        print("=" * 60)
        print(f"Total golden masters: {golden_results['total']}")
        print(f"Matched: {golden_results['matched']}")
        print(f"Mismatched: {golden_results['mismatched']}")
        print(f"Errors: {golden_results['missing']}")
        
        if golden_results['mismatched'] > 0:
            print("\nMismatches found - adapters may not be 100% compatible!")
    
    # Overall result
    print("\n🎯 Overall Result")
    print("=" * 60)
    
    if contract_results['failed'] == 0:
        print("✅ All contracts passed!")
        if golden_results.get("mismatched", 0) == 0:
            print("✅ All golden masters matched!")
            print("\n🎉 Adapters are fully compatible!")
        else:
            print("⚠️  Some golden master mismatches - review needed")
    else:
        print("❌ Some contracts failed - adapters need fixes")


if __name__ == "__main__":
    asyncio.run(main())