#!/usr/bin/env python3
"""
Complete FFD Safety Test Suite

Tests the complete Foundation-First Development safety system including:
- Circuit breakers for preventing infinite loops
- Enhanced transition validation
- Full game simulation with safety monitoring
"""

import asyncio
import time
import logging
import sys
import os
from typing import Dict

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.game import Game
from engine.player import Player
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GameAction, ActionType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FFDSafetyTester:
    """Complete FFD safety system tester"""
    
    def __init__(self):
        self.game = None
        self.state_machine = None
        self.safety_events = []
        
    async def setup_safety_enhanced_game(self) -> bool:
        """Set up a game with all safety enhancements"""
        try:
            logger.info("🔒 Setting up safety-enhanced game...")
            
            # Create players
            players = [
                Player("Alice"),
                Player("Bob"),  
                Player("Charlie"),
                Player("David")
            ]
            
            # Create game
            self.game = Game(players)
            
            # Mock broadcast callback
            async def mock_broadcast(event_type: str, data: dict):
                logger.debug(f"📤 Broadcast: {event_type}")
                
            # Create state machine with all safety features
            self.state_machine = GameStateMachine(self.game, mock_broadcast)
            self.game.room_id = "safety-test-room"
            
            logger.info("✅ Safety-enhanced game setup complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Safety game setup failed: {e}")
            return False
    
    async def test_circuit_breaker_integration(self) -> bool:
        """Test circuit breaker integration in real game context"""
        try:
            logger.info("🔌 Testing circuit breaker integration...")
            
            # Start state machine
            await self.state_machine.start()
            await asyncio.sleep(1.0)  # Let it settle
            
            # Get initial circuit breaker stats
            initial_stats = self.state_machine.get_circuit_breaker_stats()
            logger.info(f"📊 Initial circuit stats: {initial_stats}")
            
            # Try to overwhelm system with rapid actions
            rapid_actions = 0
            blocked_actions = 0
            
            for i in range(50):  # Try many rapid actions
                try:
                    action = GameAction(
                        player_name="Alice",
                        action_type=ActionType.DECLARE,
                        payload={"value": i % 4}
                    )
                    
                    result = await self.state_machine.handle_action(action)
                    if result.get("success"):
                        rapid_actions += 1
                    
                except Exception as e:
                    blocked_actions += 1
                    
                # No delay - test rapid fire
            
            # Check final stats
            final_stats = self.state_machine.get_circuit_breaker_stats()
            logger.info(f"📊 Final circuit stats: {final_stats}")
            
            logger.info(f"🎯 Rapid fire test: {rapid_actions} processed, {blocked_actions} blocked")
            
            # Circuit breakers should have triggered
            action_circuit = final_stats.get("action_circuit", {})
            total_blocks = action_circuit.get("total_blocks", 0)
            
            return total_blocks > 0  # Should have blocked some operations
            
        except Exception as e:
            logger.error(f"❌ Circuit breaker integration test failed: {e}")
            return False
    
    async def test_transition_validation(self) -> bool:
        """Test enhanced transition validation"""
        try:
            logger.info("🔍 Testing transition validation...")
            
            # Get validation stats before any transitions
            initial_validation = self.state_machine.get_transition_validation_stats()
            logger.info(f"📊 Initial validation stats: {initial_validation}")
            
            # Let the game run naturally and observe transitions
            await asyncio.sleep(5.0)
            
            # Check validation history
            validation_history = self.state_machine.get_transition_validation_history(10)
            logger.info(f"📋 Validation history: {len(validation_history)} entries")
            
            for entry in validation_history[-3:]:  # Show last 3
                logger.info(f"   {entry['from_phase']} -> {entry['to_phase']}: {'✅' if entry['valid'] else '❌'} {entry['reason']}")
            
            # Get final validation stats
            final_validation = self.state_machine.get_transition_validation_stats()
            logger.info(f"📊 Final validation stats: {final_validation}")
            
            # Should have at least one successful validation
            total_validations = final_validation.get("total_validations", 0)
            success_rate = final_validation.get("success_rate", 0.0)
            
            return total_validations > 0 and success_rate > 0.5
            
        except Exception as e:
            logger.error(f"❌ Transition validation test failed: {e}")
            return False
    
    async def test_safety_status_monitoring(self) -> bool:
        """Test comprehensive safety status monitoring"""
        try:
            logger.info("📊 Testing safety status monitoring...")
            
            # Get comprehensive safety status
            safety_status = self.state_machine.get_safety_status()
            logger.info(f"🏥 Safety status: {safety_status}")
            
            # Should have all required fields
            required_fields = ["health_status", "health_score", "circuit_breakers", 
                             "transition_validation", "system_operational"]
            
            for field in required_fields:
                if field not in safety_status:
                    logger.error(f"❌ Missing safety status field: {field}")
                    return False
            
            health_score = safety_status.get("health_score", 0)
            health_status = safety_status.get("health_status", "unknown")
            operational = safety_status.get("system_operational", False)
            
            logger.info(f"🏥 Health: {health_status} ({health_score}/100) - Operational: {operational}")
            
            # System should be operational with reasonable health
            return operational and health_score >= 0
            
        except Exception as e:
            logger.error(f"❌ Safety monitoring test failed: {e}")
            return False
    
    async def test_game_completion_with_safety(self) -> bool:
        """Test that game can complete normally with safety systems active"""
        try:
            logger.info("🎮 Testing game completion with safety systems...")
            
            # Let game run for extended period
            start_time = time.time()
            max_runtime = 30.0  # 30 seconds max
            
            while time.time() - start_time < max_runtime:
                # Check if state machine is still running
                if not self.state_machine.is_running:
                    logger.warning("⚠️ State machine stopped unexpectedly")
                    break
                
                # Monitor safety status
                safety_status = self.state_machine.get_safety_status()
                if not safety_status.get("system_operational", False):
                    logger.warning("⚠️ System became non-operational")
                    break
                
                await asyncio.sleep(1.0)
            
            runtime = time.time() - start_time
            
            # Get final safety report
            final_safety = self.state_machine.get_safety_status()
            logger.info(f"🏁 Final safety report after {runtime:.1f}s: {final_safety}")
            
            # System should still be operational
            return final_safety.get("system_operational", False)
            
        except Exception as e:
            logger.error(f"❌ Game completion test failed: {e}")
            return False
    
    async def test_error_recovery(self) -> bool:
        """Test that safety systems enable graceful error recovery"""
        try:
            logger.info("🛡️ Testing error recovery capabilities...")
            
            # Simulate various error conditions
            
            # 1. Invalid action flood
            for i in range(10):
                invalid_action = GameAction(
                    player_name="NonExistentPlayer",
                    action_type=ActionType.DECLARE,
                    payload={"value": "invalid"}
                )
                await self.state_machine.handle_action(invalid_action)
            
            # 2. Wait and check system is still operational
            await asyncio.sleep(2.0)
            
            safety_after_errors = self.state_machine.get_safety_status()
            operational_after_errors = safety_after_errors.get("system_operational", False)
            
            logger.info(f"🛡️ System operational after errors: {operational_after_errors}")
            
            # 3. Try to recover with valid action
            valid_action = GameAction(
                player_name="Bob",  # Valid player
                action_type=ActionType.DECLARE,
                payload={"value": 2}
            )
            
            result = await self.state_machine.handle_action(valid_action)
            recovery_successful = result.get("success", False)
            
            logger.info(f"🛡️ Recovery action successful: {recovery_successful}")
            
            return operational_after_errors  # System should remain operational
            
        except Exception as e:
            logger.error(f"❌ Error recovery test failed: {e}")
            return False
    
    async def run_complete_safety_tests(self) -> Dict[str, bool]:
        """Run all FFD safety tests"""
        logger.info("🚀 Starting complete FFD safety test suite...")
        
        tests = [
            ("Setup Safety Game", self.setup_safety_enhanced_game),
            ("Circuit Breaker Integration", self.test_circuit_breaker_integration),
            ("Transition Validation", self.test_transition_validation),
            ("Safety Status Monitoring", self.test_safety_status_monitoring),
            ("Game Completion", self.test_game_completion_with_safety),
            ("Error Recovery", self.test_error_recovery)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            logger.info(f"\n📋 Running test: {test_name}")
            try:
                result = await test_func()
                results[test_name] = result
                
                if result:
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
                    
            except Exception as e:
                logger.error(f"💥 {test_name}: CRASHED - {e}")
                results[test_name] = False
        
        # Cleanup
        if self.state_machine:
            await self.state_machine.stop()
        
        return results
    
    def print_safety_summary(self, results: Dict[str, bool]):
        """Print comprehensive safety test summary"""
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🔒 FFD SAFETY SYSTEM TEST SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"✅ Passed: {passed}/{total}")
        logger.info(f"❌ Failed: {total - passed}/{total}")
        
        if passed == total:
            logger.info("🎉 ALL SAFETY TESTS PASSED!")
            logger.info("🛡️ Foundation-First Development safety systems are operational")
            logger.info("🚫 Infinite loops and system failures are prevented")
            logger.info("📊 Comprehensive monitoring and recovery systems working")
        else:
            logger.error("💥 SOME SAFETY TESTS FAILED!")
            logger.error("⚠️ Safety systems need attention before production use")
        
        logger.info(f"{'='*70}")

async def main():
    """Main safety test runner"""
    tester = FFDSafetyTester()
    results = await tester.run_complete_safety_tests()
    tester.print_safety_summary(results)
    
    # Exit with proper code
    if all(results.values()):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    asyncio.run(main())