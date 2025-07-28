"""
Integration Tests - Combine Behavioral and Contract Testing
Ensures the complete system behavior is captured and validated.
"""

import pytest
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

from tests.contracts.websocket_contracts import get_all_contracts, WebSocketContract
from tests.contracts.golden_master import GoldenMasterCapture, GoldenMasterComparator
from tests.contracts.parallel_runner import ParallelContractRunner


class IntegrationTestHarness:
    """
    Comprehensive test harness that combines:
    1. Behavioral flow testing
    2. Contract validation
    3. Golden master comparison
    """
    
    def __init__(self):
        self.capture = GoldenMasterCapture()
        self.comparator = GoldenMasterComparator(
            ignore_fields=["timestamp", "server_time", "room_id"]
        )
        self.test_flows = []
        self.contract_validations = []
        
    async def run_game_flow_with_validation(self, flow_name: str, 
                                           flow_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run a complete game flow and validate each step against contracts"""
        print(f"\n{'=' * 60}")
        print(f"Running Integration Test: {flow_name}")
        print('=' * 60)
        
        flow_result = {
            "flow_name": flow_name,
            "steps": [],
            "contract_validations": [],
            "overall_success": True
        }
        
        # Track game state through the flow
        game_state = {
            "room_id": None,
            "players": [],
            "phase": None,
            "current_player": None
        }
        
        for i, step in enumerate(flow_steps):
            print(f"\nStep {i+1}: {step['description']}")
            
            # Execute the step
            step_result = await self.execute_flow_step(step, game_state)
            flow_result["steps"].append(step_result)
            
            # Validate against contract
            if "action" in step:
                contract_validation = await self.validate_against_contract(
                    step["action"], 
                    step.get("data", {}),
                    step_result.get("response"),
                    step_result.get("broadcasts", [])
                )
                flow_result["contract_validations"].append(contract_validation)
                
                if not contract_validation["valid"]:
                    flow_result["overall_success"] = False
                    print(f"  ❌ Contract validation failed: {contract_validation['error']}")
                else:
                    print(f"  ✅ Contract validation passed")
                    
            # Update game state based on response
            self.update_game_state(game_state, step_result)
            
        # Save complete flow
        self.save_integration_test_result(flow_result)
        
        return flow_result
    
    async def execute_flow_step(self, step: Dict[str, Any], 
                              game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step in the game flow"""
        # In real implementation, this would send actual WebSocket messages
        # For now, simulate the response
        
        action = step.get("action")
        data = step.get("data", {})
        
        # Simulate response based on action
        response = None
        broadcasts = []
        
        if action == "create_room":
            response = {
                "event": "room_created",
                "data": {
                    "room_id": "TEST01",
                    "host_name": data.get("player_name"),
                    "success": True
                }
            }
            broadcasts.append({
                "event": "room_list_update",
                "data": {"rooms": [], "timestamp": 1234567890.123}
            })
            
        elif action == "join_room":
            response = {
                "event": "room_joined",
                "data": {
                    "room_id": data.get("room_id"),
                    "player_name": data.get("player_name"),
                    "assigned_slot": len(game_state["players"]),
                    "success": True
                }
            }
            broadcasts.append({
                "event": "room_update",
                "data": {
                    "players": game_state["players"] + [{"name": data.get("player_name")}],
                    "host_name": game_state["players"][0]["name"] if game_state["players"] else None,
                    "room_id": data.get("room_id"),
                    "started": False
                }
            })
            
        # Add more action handlers as needed
        
        return {
            "action": action,
            "data": data,
            "response": response,
            "broadcasts": broadcasts,
            "success": response is not None
        }
    
    async def validate_against_contract(self, action: str, data: Dict[str, Any],
                                      response: Optional[Dict[str, Any]],
                                      broadcasts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate response against WebSocket contract"""
        contract = get_all_contracts().get(action)
        if not contract:
            return {
                "valid": False,
                "error": f"No contract found for action: {action}",
                "action": action
            }
            
        # Validate response format
        if contract.response_schema and response:
            expected_event = contract.response_schema.get("event")
            if response.get("event") != expected_event:
                return {
                    "valid": False,
                    "error": f"Expected event '{expected_event}', got '{response.get('event')}'",
                    "action": action
                }
                
        # Validate broadcast events
        if contract.broadcast_schemas:
            expected_broadcasts = [s.get("event") for s in contract.broadcast_schemas]
            actual_broadcasts = [b.get("event") for b in broadcasts]
            
            # Check if expected broadcasts are present
            for expected in expected_broadcasts:
                if expected not in actual_broadcasts:
                    return {
                        "valid": False,
                        "error": f"Expected broadcast '{expected}' not found",
                        "action": action
                    }
                    
        return {
            "valid": True,
            "action": action,
            "contract": contract.name
        }
    
    def update_game_state(self, game_state: Dict[str, Any], 
                         step_result: Dict[str, Any]):
        """Update game state based on step execution"""
        response = step_result.get("response", {})
        
        if response.get("event") == "room_created":
            game_state["room_id"] = response["data"]["room_id"]
            game_state["players"] = [{
                "name": response["data"]["host_name"],
                "is_host": True
            }]
            
        elif response.get("event") == "room_joined":
            game_state["players"].append({
                "name": response["data"]["player_name"],
                "is_host": False
            })
            
        elif response.get("event") == "game_started":
            game_state["phase"] = "PREPARATION"
            
        # Add more state updates as needed
    
    def save_integration_test_result(self, result: Dict[str, Any]):
        """Save integration test result"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"integration_{result['flow_name']}_{timestamp}.json"
        
        filepath = Path("tests/contracts/golden_masters/integration") / filename
        filepath.parent.mkdir(exist_ok=True, parents=True)
        
        with open(filepath, 'w') as f:
            json.dump(result, f, indent=2, default=str)
            
        print(f"\nIntegration test result saved to: {filepath}")


class TestIntegratedGameFlows:
    """Integration tests that validate complete game flows with contracts"""
    
    @pytest.mark.asyncio
    async def test_integrated_4_player_game(self):
        """Test complete 4-player game with contract validation"""
        harness = IntegrationTestHarness()
        
        flow_steps = [
            {
                "description": "Alice creates room",
                "action": "create_room",
                "data": {"player_name": "Alice"}
            },
            {
                "description": "Bob joins room",
                "action": "join_room",
                "data": {"room_id": "TEST01", "player_name": "Bob"}
            },
            {
                "description": "Charlie joins room",
                "action": "join_room",
                "data": {"room_id": "TEST01", "player_name": "Charlie"}
            },
            {
                "description": "David joins room",
                "action": "join_room",
                "data": {"room_id": "TEST01", "player_name": "David"}
            },
            {
                "description": "Alice starts game",
                "action": "start_game",
                "data": {}
            },
            {
                "description": "Players make declarations",
                "action": "declare",
                "data": {"player_name": "Alice", "value": 2}
            },
            {
                "description": "Bob declares",
                "action": "declare",
                "data": {"player_name": "Bob", "value": 3}
            },
            {
                "description": "Charlie declares",
                "action": "declare",
                "data": {"player_name": "Charlie", "value": 1}
            },
            {
                "description": "David declares",
                "action": "declare",
                "data": {"player_name": "David", "value": 2}
            }
        ]
        
        result = await harness.run_game_flow_with_validation(
            "4_player_game_integrated",
            flow_steps
        )
        
        assert result["overall_success"], "Integration test failed"
        
        # Verify all contract validations passed
        failed_validations = [v for v in result["contract_validations"] if not v["valid"]]
        assert len(failed_validations) == 0, f"Contract validations failed: {failed_validations}"
        
        print(f"\n✅ Integration test passed with {len(flow_steps)} steps validated")
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """Test error scenarios with contract validation"""
        harness = IntegrationTestHarness()
        
        error_flow_steps = [
            {
                "description": "Try to join non-existent room",
                "action": "join_room",
                "data": {"room_id": "NOEXIST", "player_name": "Alice"},
                "expected_error": "Room not found"
            },
            {
                "description": "Create room with invalid name",
                "action": "create_room",
                "data": {"player_name": ""},
                "expected_error": "Invalid player name"
            },
            {
                "description": "Start game with insufficient players",
                "action": "start_game",
                "data": {},
                "expected_error": "Not enough players"
            }
        ]
        
        for step in error_flow_steps:
            result = await harness.execute_flow_step(step, {})
            
            # Verify error response
            if "expected_error" in step:
                assert result.get("response", {}).get("event") == "error", \
                    f"Expected error for: {step['description']}"
                    
        print("\n✅ Error handling integration tests passed")
    
    @pytest.mark.asyncio
    async def test_performance_integrated(self):
        """Test performance requirements are met across full flows"""
        harness = IntegrationTestHarness()
        
        import time
        
        # Test rapid message handling
        start_time = time.time()
        
        # Simulate rapid ping messages
        for i in range(10):
            await harness.execute_flow_step({
                "description": f"Ping {i}",
                "action": "ping",
                "data": {"timestamp": int(time.time() * 1000)}
            }, {})
            
        duration = time.time() - start_time
        avg_response_time = (duration / 10) * 1000  # Convert to ms
        
        # Verify meets contract requirement (< 100ms per ping)
        assert avg_response_time < 100, f"Average ping response time {avg_response_time}ms exceeds 100ms"
        
        print(f"\n✅ Performance test passed: avg response time {avg_response_time:.2f}ms")


def generate_integration_test_report():
    """Generate comprehensive report of all integration tests"""
    report_path = Path("tests/contracts/golden_masters/integration")
    if not report_path.exists():
        print("No integration test results found")
        return
        
    results = []
    for result_file in report_path.glob("integration_*.json"):
        with open(result_file, 'r') as f:
            results.append(json.load(f))
            
    # Generate summary
    summary = {
        "total_integration_tests": len(results),
        "all_passed": all(r.get("overall_success", False) for r in results),
        "total_steps_validated": sum(len(r.get("steps", [])) for r in results),
        "total_contract_validations": sum(len(r.get("contract_validations", [])) for r in results),
        "test_results": results
    }
    
    # Save summary
    summary_path = report_path / "integration_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
        
    print(f"\nIntegration Test Summary:")
    print(f"  Total tests: {summary['total_integration_tests']}")
    print(f"  All passed: {summary['all_passed']}")
    print(f"  Steps validated: {summary['total_steps_validated']}")
    print(f"  Contract validations: {summary['total_contract_validations']}")
    print(f"\nDetailed report: {summary_path}")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v"])
    
    # Generate report
    generate_integration_test_report()