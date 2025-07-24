#!/usr/bin/env python3
"""
Compare specific golden master mismatches
"""

import json
import os
import asyncio
from typing import Dict, Any

from api.adapters.integrated_adapter_system import IntegratedAdapterSystem


class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.messages_sent = []
        self.room_id = None


async def mock_legacy_handler(websocket, message: Dict[str, Any]) -> Dict[str, Any]:
    """Mock legacy handler matching golden master responses"""
    action = message.get("action")
    data = message.get("data", {})
    
    # Return the exact responses from golden masters
    responses = {
        "ping": {
            "event": "pong",
            "data": {
                "timestamp": data.get("timestamp"),
                "server_time": 1234567890.0,
                "room_id": "test_room"  # This might be the difference
            }
        },
        "client_ready": {
            "event": "room_state_update",
            "data": {
                "slots": [],
                "host_name": ""
            }
        }
    }
    
    return responses.get(action, {
        "event": "error",
        "data": {"message": f"Unknown action: {action}"}
    })


async def compare_specific_case():
    """Compare a specific mismatch case"""
    
    # Load a specific golden master that's mismatching
    golden_file = "tests/contracts/golden_masters/ping_8f476e91.json"
    
    if os.path.exists(golden_file):
        with open(golden_file, 'r') as f:
            golden_data = json.load(f)
        
        print(f"🔍 Analyzing: {golden_file}")
        print("=" * 60)
        
        # Show golden master content
        print("\n📄 Golden Master Content:")
        print(f"Name: {golden_data.get('name')}")
        print(f"Request: {json.dumps(golden_data.get('request'), indent=2)}")
        print(f"Expected Response: {json.dumps(golden_data.get('response'), indent=2)}")
        
        # Run through adapter
        adapter_system = IntegratedAdapterSystem(mock_legacy_handler)
        ws = MockWebSocket()
        
        # Create message from golden master
        message = {
            "action": golden_data.get('name'),
            "data": golden_data.get('request')
        }
        
        # Get adapter response
        adapter_response = await adapter_system.handle_message(
            ws, message, golden_data.get('room_state')
        )
        
        print(f"\n🤖 Adapter Response: {json.dumps(adapter_response, indent=2)}")
        
        # Compare responses
        print("\n📊 Differences:")
        expected = golden_data.get('response', {})
        
        if adapter_response != expected:
            # Compare field by field
            all_keys = set(expected.keys()) | set(adapter_response.keys() if adapter_response else {})
            
            for key in all_keys:
                exp_val = expected.get(key)
                act_val = adapter_response.get(key) if adapter_response else None
                
                if exp_val != act_val:
                    print(f"  {key}:")
                    print(f"    Expected: {exp_val}")
                    print(f"    Actual:   {act_val}")
            
            # Check nested data
            if 'data' in expected and adapter_response and 'data' in adapter_response:
                exp_data = expected['data']
                act_data = adapter_response['data']
                
                if exp_data != act_data:
                    print("\n  data fields:")
                    all_data_keys = set(exp_data.keys()) | set(act_data.keys())
                    
                    for key in all_data_keys:
                        exp_val = exp_data.get(key)
                        act_val = act_data.get(key)
                        
                        if exp_val != act_val:
                            print(f"    {key}:")
                            print(f"      Expected: {exp_val}")
                            print(f"      Actual:   {act_val}")
        else:
            print("✅ Responses match!")
    else:
        print(f"❌ Golden master file not found: {golden_file}")
    
    # Check a regular (non-hash) golden master
    print("\n\n" + "=" * 60)
    regular_golden = "tests/contracts/golden_masters/ping.json"
    
    if os.path.exists(regular_golden):
        with open(regular_golden, 'r') as f:
            golden_data = json.load(f)
        
        print(f"🔍 Analyzing regular golden master: {regular_golden}")
        print(f"Expected Response: {json.dumps(golden_data.get('response'), indent=2)}")


if __name__ == "__main__":
    asyncio.run(compare_specific_case())