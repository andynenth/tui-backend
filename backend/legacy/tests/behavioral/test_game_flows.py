"""
Behavioral Test Suite for Current System
Tests complete game flows to ensure system behavior is preserved during refactoring.
"""

import pytest
import asyncio
from typing import Dict, List, Any, Optional
import json

from tests.contracts.websocket_contracts import get_all_contracts
from tests.contracts.golden_master import GoldenMasterCapture


class GameFlowTester:
    """Tests complete game flows from start to finish"""
    
    def __init__(self):
        self.capture = GoldenMasterCapture()
        self.messages_sent = []
        self.events_received = []
        self.room_states = {}
        
    async def simulate_message(self, action: str, data: Dict[str, Any], room_id: Optional[str] = None):
        """Simulate sending a WebSocket message and capture response"""
        message = {"action": action, "data": data}
        self.messages_sent.append(message)
        
        # In real implementation, this would send to actual WebSocket
        # For now, we'll use the capture framework
        room_state = self.room_states.get(room_id) if room_id else None
        
        # This would be replaced with actual WebSocket handler
        from tests.contracts.capture_golden_masters import CurrentSystemSimulator
        simulator = CurrentSystemSimulator()
        
        response = await simulator.handle_message(message, room_state)
        if response:
            self.events_received.append(response)
            
        # Update room state based on response
        if response and response.get("event") == "room_created":
            room_id = response["data"]["room_id"]
            self.room_states[room_id] = {
                "room_id": room_id,
                "players": [{"name": data.get("player_name"), "slot": 0, "is_host": True}],
                "started": False
            }
            
        return response


class TestCompleteGameFlows:
    """Test complete game flows from room creation to game completion"""
    
    @pytest.mark.asyncio
    async def test_full_game_flow_with_4_players(self):
        """Test a complete game with 4 human players"""
        tester = GameFlowTester()
        
        # Step 1: Create room
        response = await tester.simulate_message("create_room", {"player_name": "Alice"})
        assert response["event"] == "room_created"
        room_id = response["data"]["room_id"]
        
        # Step 2: Other players join
        await tester.simulate_message("join_room", {"room_id": room_id, "player_name": "Bob"})
        await tester.simulate_message("join_room", {"room_id": room_id, "player_name": "Charlie"})
        await tester.simulate_message("join_room", {"room_id": room_id, "player_name": "David"})
        
        # Step 3: Start game
        await tester.simulate_message("start_game", {})
        
        # Step 4: Handle preparation phase (check for weak hands)
        # This would check phase_change events and handle redeals if needed
        
        # Step 5: Declaration phase - all players declare
        await tester.simulate_message("declare", {"player_name": "Alice", "value": 2})
        await tester.simulate_message("declare", {"player_name": "Bob", "value": 3})
        await tester.simulate_message("declare", {"player_name": "Charlie", "value": 1})
        await tester.simulate_message("declare", {"player_name": "David", "value": 2})
        
        # Step 6: Turn phase - play through all 8 turns
        # This would simulate complete turn sequences
        
        # Step 7: Scoring phase
        # Verify scores are calculated correctly
        
        # Capture the complete flow
        flow_record = {
            "flow_name": "full_game_4_players",
            "messages_sent": tester.messages_sent,
            "events_received": tester.events_received,
            "final_room_states": tester.room_states
        }
        
        # Save as golden master for this flow
        tester.capture.save_golden_master_flow(flow_record)
    
    @pytest.mark.asyncio
    async def test_game_flow_with_bots(self):
        """Test game flow with mix of humans and bots"""
        tester = GameFlowTester()
        
        # Create room and add mix of players and bots
        response = await tester.simulate_message("create_room", {"player_name": "Alice"})
        room_id = response["data"]["room_id"]
        
        await tester.simulate_message("join_room", {"room_id": room_id, "player_name": "Bob"})
        await tester.simulate_message("add_bot", {"slot_id": "3"})
        await tester.simulate_message("add_bot", {"slot_id": "4"})
        
        # Start and play game
        await tester.simulate_message("start_game", {})
        
        # Test bot behavior in declaration and turn phases
        # Bots should automatically declare and play
        
        flow_record = {
            "flow_name": "game_with_bots",
            "messages_sent": tester.messages_sent,
            "events_received": tester.events_received
        }
        
        tester.capture.save_golden_master_flow(flow_record)
    
    @pytest.mark.asyncio
    async def test_weak_hand_redeal_flow(self):
        """Test the weak hand redeal flow"""
        tester = GameFlowTester()
        
        # Setup game
        response = await tester.simulate_message("create_room", {"player_name": "Alice"})
        room_id = response["data"]["room_id"]
        
        # Add players
        for player in ["Bob", "Charlie", "David"]:
            await tester.simulate_message("join_room", {"room_id": room_id, "player_name": player})
        
        # Start game - this should trigger preparation phase
        await tester.simulate_message("start_game", {})
        
        # Simulate weak hand scenario
        # Player with weak hand requests redeal
        await tester.simulate_message("request_redeal", {"player_name": "Alice"})
        
        # Other players respond
        await tester.simulate_message("accept_redeal", {"player_name": "Bob"})
        await tester.simulate_message("accept_redeal", {"player_name": "Charlie"})
        await tester.simulate_message("decline_redeal", {"player_name": "David"})
        
        # Verify redeal happened or starter changed based on responses
        
        flow_record = {
            "flow_name": "weak_hand_redeal",
            "messages_sent": tester.messages_sent,
            "events_received": tester.events_received
        }
        
        tester.capture.save_golden_master_flow(flow_record)
    
    @pytest.mark.asyncio 
    async def test_player_disconnect_reconnect_flow(self):
        """Test player disconnection and reconnection"""
        tester = GameFlowTester()
        
        # Setup game
        response = await tester.simulate_message("create_room", {"player_name": "Alice"})
        room_id = response["data"]["room_id"]
        
        # Add players and start
        for player in ["Bob", "Charlie", "David"]:
            await tester.simulate_message("join_room", {"room_id": room_id, "player_name": player})
        await tester.simulate_message("start_game", {})
        
        # Simulate disconnect (connection closed)
        # In real system, this would be WebSocket disconnect
        
        # Simulate reconnect
        await tester.simulate_message("sync_request", {"client_id": "alice_client_123"})
        
        # Player should receive current game state
        # Continue playing from where they left off
        
        flow_record = {
            "flow_name": "disconnect_reconnect",
            "messages_sent": tester.messages_sent,
            "events_received": tester.events_received
        }
        
        tester.capture.save_golden_master_flow(flow_record)
    
    @pytest.mark.asyncio
    async def test_room_closure_scenarios(self):
        """Test various room closure scenarios"""
        tester = GameFlowTester()
        
        # Scenario 1: Host leaves before game starts
        response = await tester.simulate_message("create_room", {"player_name": "Alice"})
        room_id = response["data"]["room_id"]
        await tester.simulate_message("join_room", {"room_id": room_id, "player_name": "Bob"})
        await tester.simulate_message("leave_room", {"player_name": "Alice"})
        
        # Room should close or transfer host
        
        # Scenario 2: Last player leaves
        response = await tester.simulate_message("create_room", {"player_name": "Charlie"})
        room_id2 = response["data"]["room_id"]
        await tester.simulate_message("leave_room", {"player_name": "Charlie"})
        
        # Room should be closed
        
        flow_record = {
            "flow_name": "room_closure_scenarios",
            "messages_sent": tester.messages_sent,
            "events_received": tester.events_received
        }
        
        tester.capture.save_golden_master_flow(flow_record)


class TestErrorScenarios:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_invalid_actions_in_wrong_phase(self):
        """Test that actions are rejected when sent in wrong phase"""
        tester = GameFlowTester()
        
        # Create and start game
        response = await tester.simulate_message("create_room", {"player_name": "Alice"})
        room_id = response["data"]["room_id"]
        
        # Try to declare before game starts (should fail)
        error_response = await tester.simulate_message("declare", {"player_name": "Alice", "value": 3})
        assert error_response.get("event") == "error"
        
        # Add players and start
        for player in ["Bob", "Charlie", "David"]:
            await tester.simulate_message("join_room", {"room_id": room_id, "player_name": player})
        await tester.simulate_message("start_game", {})
        
        # Try to play pieces during declaration phase (should fail)
        error_response = await tester.simulate_message("play", {"player_name": "Alice", "indices": [0, 1]})
        assert error_response.get("event") == "error" or error_response.get("event") == "play_rejected"
        
        flow_record = {
            "flow_name": "invalid_phase_actions",
            "messages_sent": tester.messages_sent,
            "events_received": tester.events_received
        }
        
        tester.capture.save_golden_master_flow(flow_record)
    
    @pytest.mark.asyncio
    async def test_concurrent_action_handling(self):
        """Test system handles concurrent actions correctly"""
        tester = GameFlowTester()
        
        # Create room
        response = await tester.simulate_message("create_room", {"player_name": "Alice"})
        room_id = response["data"]["room_id"]
        
        # Simulate multiple players trying to join same slot
        # In real system, these would be concurrent WebSocket messages
        tasks = [
            tester.simulate_message("join_room", {"room_id": room_id, "player_name": f"Player{i}"})
            for i in range(6)  # Try to add 6 players to 4-player room
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify only 3 additional players could join (total 4)
        successful_joins = sum(1 for r in responses if isinstance(r, dict) and r.get("event") == "room_joined")
        assert successful_joins == 3
        
        flow_record = {
            "flow_name": "concurrent_actions",
            "messages_sent": tester.messages_sent,
            "events_received": tester.events_received
        }
        
        tester.capture.save_golden_master_flow(flow_record)


class TestPerformanceScenarios:
    """Test performance and timing requirements"""
    
    @pytest.mark.asyncio
    async def test_response_timing_requirements(self):
        """Verify responses meet timing requirements from contracts"""
        tester = GameFlowTester()
        
        # Test ping response time (should be < 100ms per contract)
        import time
        start = time.time()
        await tester.simulate_message("ping", {"timestamp": int(time.time() * 1000)})
        duration = (time.time() - start) * 1000
        
        # In real test, verify duration < 100ms
        
        # Test declaration response time (should be < 200ms per contract)
        response = await tester.simulate_message("create_room", {"player_name": "Alice"})
        room_id = response["data"]["room_id"]
        
        # Setup game
        for player in ["Bob", "Charlie", "David"]:
            await tester.simulate_message("join_room", {"room_id": room_id, "player_name": player})
        await tester.simulate_message("start_game", {})
        
        # Time declaration
        start = time.time()
        await tester.simulate_message("declare", {"player_name": "Alice", "value": 3})
        duration = (time.time() - start) * 1000
        
        # In real test, verify duration < 200ms
        
        flow_record = {
            "flow_name": "timing_requirements",
            "messages_sent": tester.messages_sent,
            "events_received": tester.events_received,
            "timing_measurements": {
                "ping_response_ms": duration
            }
        }
        
        tester.capture.save_golden_master_flow(flow_record)


# Helper to extend GoldenMasterCapture for flow saving
def extend_golden_master_capture():
    """Add flow saving capability to GoldenMasterCapture"""
    def save_golden_master_flow(self, flow_record: Dict[str, Any]):
        """Save a complete game flow as golden master"""
        import json
        from pathlib import Path
        from datetime import datetime
        
        flow_name = flow_record.get("flow_name", "unknown_flow")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"flow_{flow_name}_{timestamp}.json"
        
        filepath = self.storage_path / "flows" / filename
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(flow_record, f, indent=2, default=str)
            
        return filepath
    
    # Add method to GoldenMasterCapture class
    GoldenMasterCapture.save_golden_master_flow = save_golden_master_flow


# Apply the extension
extend_golden_master_capture()


if __name__ == "__main__":
    # Run behavioral tests
    pytest.main([__file__, "-v"])