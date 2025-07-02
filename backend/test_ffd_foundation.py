#!/usr/bin/env python3
"""
Foundation-First Development (FFD) Testing Framework

This script validates that the 8ca1ca8 foundation works correctly by running
a complete game simulation and monitoring for stability issues.
"""

import asyncio
import time
import logging
import sys
import os
from typing import Dict, List

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

class FFDTester:
    """Foundation stability tester"""
    
    def __init__(self):
        self.game = None
        self.state_machine = None
        self.test_results = {}
        self.start_time = None
        
    async def setup_game(self) -> bool:
        """Set up a test game with 4 players"""
        try:
            logger.info("🎮 Setting up test game...")
            
            # Create players
            players = [
                Player("Alice"),
                Player("Bob"),  
                Player("Charlie"),
                Player("David")
            ]
            
            # Create game
            self.game = Game(players)
            
            # Mock broadcast callback for testing
            async def mock_broadcast(event_type: str, data: dict):
                logger.debug(f"📤 Mock broadcast: {event_type}")
                
            # Create state machine
            self.state_machine = GameStateMachine(self.game, mock_broadcast)
            self.game.room_id = "test-room"
            
            logger.info("✅ Game setup complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Game setup failed: {e}")
            return False
    
    async def test_polling_stability(self) -> bool:
        """Test that the polling loop runs stably"""
        try:
            logger.info("🔍 Testing polling loop stability...")
            
            # Start state machine
            await self.state_machine.start()
            
            # Let it run for 5 seconds
            await asyncio.sleep(5.0)
            
            # Check if still running
            if self.state_machine.is_running:
                logger.info("✅ Polling loop stable after 5 seconds")
                return True
            else:
                logger.error("❌ Polling loop stopped unexpectedly")
                return False
                
        except Exception as e:
            logger.error(f"❌ Polling stability test failed: {e}")
            return False
    
    async def test_state_transitions(self) -> bool:
        """Test basic state transitions"""
        try:
            logger.info("🔄 Testing state transitions...")
            
            # Should start in PREPARATION phase
            initial_phase = self.state_machine.get_current_phase()
            if initial_phase.value != "preparation":
                logger.error(f"❌ Expected preparation phase, got {initial_phase}")
                return False
                
            logger.info("✅ Started in correct PREPARATION phase")
            
            # Wait for automatic transition to DECLARATION phase
            max_wait = 10.0
            wait_time = 0.0
            while wait_time < max_wait:
                current_phase = self.state_machine.get_current_phase()
                if current_phase.value == "declaration":
                    logger.info("✅ Transitioned to DECLARATION phase")
                    return True
                    
                await asyncio.sleep(0.5)
                wait_time += 0.5
            
            logger.error("❌ Failed to transition to DECLARATION phase")
            return False
            
        except Exception as e:
            logger.error(f"❌ State transition test failed: {e}")
            return False
    
    async def test_action_processing(self) -> bool:
        """Test that actions are processed correctly"""
        try:
            logger.info("🎯 Testing action processing...")
            
            # Wait for declaration phase
            while self.state_machine.get_current_phase().value != "declaration":
                await asyncio.sleep(0.1)
            
            # Submit a declaration action
            action = GameAction(
                player_name="Alice",
                action_type=ActionType.DECLARE,
                payload={"value": 2}
            )
            
            result = await self.state_machine.handle_action(action)
            
            if result.get("success"):
                logger.info("✅ Action processed successfully")
                return True
            else:
                logger.error("❌ Action processing failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Action processing test failed: {e}")
            return False
    
    async def test_memory_stability(self) -> bool:
        """Test that memory usage remains stable"""
        try:
            logger.info("🧠 Testing memory stability...")
            
            import psutil
            process = psutil.Process()
            
            # Get initial memory
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            logger.info(f"📊 Initial memory: {initial_memory:.1f} MB")
            
            # Run for 10 seconds with actions
            for i in range(20):
                action = GameAction(
                    player_name="Alice", 
                    action_type=ActionType.DECLARE,
                    payload={"value": i % 4}
                )
                await self.state_machine.handle_action(action)
                await asyncio.sleep(0.5)
            
            # Check final memory
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_growth = final_memory - initial_memory
            
            logger.info(f"📊 Final memory: {final_memory:.1f} MB")
            logger.info(f"📊 Memory growth: {memory_growth:.1f} MB")
            
            # Fail if memory grew by more than 50MB
            if memory_growth > 50:
                logger.error(f"❌ Excessive memory growth: {memory_growth:.1f} MB")
                return False
            else:
                logger.info("✅ Memory usage stable")
                return True
                
        except ImportError:
            logger.warning("⚠️ psutil not available, skipping memory test")
            return True
        except Exception as e:
            logger.error(f"❌ Memory stability test failed: {e}")
            return False
    
    async def test_error_recovery(self) -> bool:
        """Test that system recovers from errors gracefully"""
        try:
            logger.info("🛡️ Testing error recovery...")
            
            # Submit an invalid action
            invalid_action = GameAction(
                player_name="NonExistentPlayer",
                action_type=ActionType.DECLARE, 
                payload={"value": "invalid"}
            )
            
            result = await self.state_machine.handle_action(invalid_action)
            
            # Should handle gracefully
            if result.get("success") == False:
                logger.info("✅ Invalid action rejected gracefully")
            else:
                logger.warning("⚠️ Invalid action was accepted")
            
            # Check that system is still running
            await asyncio.sleep(1.0)
            
            if self.state_machine.is_running:
                logger.info("✅ System recovered from error")
                return True
            else:
                logger.error("❌ System crashed after error")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error recovery test failed: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all FFD foundation tests"""
        logger.info("🚀 Starting Foundation-First Development tests...")
        self.start_time = time.time()
        
        tests = [
            ("Setup", self.setup_game),
            ("Polling Stability", self.test_polling_stability),
            ("State Transitions", self.test_state_transitions), 
            ("Action Processing", self.test_action_processing),
            ("Memory Stability", self.test_memory_stability),
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
    
    def print_summary(self, results: Dict[str, bool]):
        """Print test summary"""
        total_time = time.time() - self.start_time
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎯 FFD FOUNDATION TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Passed: {passed}/{total}")
        logger.info(f"❌ Failed: {total - passed}/{total}")
        logger.info(f"⏱️  Time: {total_time:.1f}s")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED - Foundation is stable!")
        else:
            logger.error("💥 SOME TESTS FAILED - Foundation needs attention!")
        
        logger.info(f"{'='*60}")

async def main():
    """Main test runner"""
    tester = FFDTester()
    results = await tester.run_all_tests()
    tester.print_summary(results)
    
    # Exit with proper code
    if all(results.values()):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    asyncio.run(main())