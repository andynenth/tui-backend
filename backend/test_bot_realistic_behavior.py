#!/usr/bin/env python3
"""
🤖 Bot Realistic Behavior Test
Tests bot AI decisions with actual game scenarios and realistic data
"""

import asyncio
import sys
import os
import json
from typing import List, Dict, Any

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from engine.room import Room
from engine.player import Player
from engine.bot_manager import BotManager
from engine.state_machine.core import GamePhase, ActionType, GameAction
from engine.game import Game
from engine.piece import Piece, PieceType, PieceColor

class BotBehaviorTester:
    """Test bot AI with realistic game scenarios"""
    
    def __init__(self):
        self.room_id = "BOT_TEST_001"
        self.room = None
        self.test_scenarios = []
        
    async def setup_bot_test_environment(self):
        """Setup environment with 4 bots for pure AI testing"""
        print("🤖 Setting up bot-only test environment...")
        
        self.room = Room(self.room_id, "AggressiveBot")
        
        # Add 4 bots with different AI personalities
        bot_configs = [
            {"name": "AggressiveBot", "strategy": "aggressive"},
            {"name": "ConservativeBot", "strategy": "conservative"}, 
            {"name": "BalancedBot", "strategy": "balanced"},
            {"name": "RandomBot", "strategy": "random"}
        ]
        
        # First bot is the host
        for i, config in enumerate(bot_configs):
            if i == 0:
                # Host is already added, just convert to bot
                self.room.players[0].is_bot = True
                self.room.players[0].name = config["name"]
            else:
                slot = self.room.join_room(config["name"])
                if slot == -1:
                    raise Exception(f"Failed to add bot {config['name']}")
                # Convert to bot after joining
                self.room.players[slot].is_bot = True
        
        print(f"✅ Bot setup complete: {[p.name for p in self.room.players]}")
    
    async def test_realistic_bot_scenarios(self):
        """Test multiple realistic game scenarios"""
        print("\n🎯 Testing realistic bot scenarios...")
        
        scenarios = [
            await self._test_weak_hand_scenario(),
            await self._test_declaration_strategies(),
            await self._test_turn_competition(),
            await self._test_endgame_behavior()
        ]
        
        passed_scenarios = sum(1 for result in scenarios if result)
        print(f"\n📊 Scenario Results: {passed_scenarios}/{len(scenarios)} passed")
        
        return all(scenarios)
    
    async def _test_weak_hand_scenario(self):
        """Test bot behavior with weak hands (realistic card distributions)"""
        print("\n🃏 Testing Weak Hand Scenario...")
        
        try:
            # Start fresh game
            result = await self.room.start_game_safe()
            if not result["success"]:
                raise Exception(f"Game start failed: {result}")
            
            # Force weak hands by manually setting player hands
            game = self.room.game
            
            # Create realistic weak hand (no pieces > 9 points)
            weak_pieces = [
                Piece(PieceType.SOLDIER, PieceColor.RED),    # 2 points
                Piece(PieceType.SOLDIER, PieceColor.BLACK),  # 1 point
                Piece(PieceType.CANNON, PieceColor.RED),     # 4 points
                Piece(PieceType.CANNON, PieceColor.BLACK),   # 3 points
                Piece(PieceType.HORSE, PieceColor.RED),      # 6 points
                Piece(PieceType.HORSE, PieceColor.BLACK),    # 5 points
                Piece(PieceType.CHARIOT, PieceColor.RED),    # 8 points
                Piece(PieceType.CHARIOT, PieceColor.BLACK),  # 7 points
            ]
            
            # Assign weak hand to first bot
            game.players[0].hand = weak_pieces.copy()
            print(f"🤖 {game.players[0].name} given weak hand: {[str(p) for p in weak_pieces]}")
            
            # Give other bots normal hands with strong pieces
            strong_pieces = [
                Piece(PieceType.GENERAL, PieceColor.RED),    # 14 points
                Piece(PieceType.GENERAL, PieceColor.BLACK),  # 13 points  
                Piece(PieceType.ADVISOR, PieceColor.RED),    # 12 points
                Piece(PieceType.ADVISOR, PieceColor.BLACK),  # 11 points
                Piece(PieceType.ELEPHANT, PieceColor.RED),   # 10 points
                Piece(PieceType.ELEPHANT, PieceColor.BLACK), # 9 points
                Piece(PieceType.HORSE, PieceColor.RED),      # 6 points
                Piece(PieceType.SOLDIER, PieceColor.RED),    # 2 points
            ]
            
            for i in range(1, 4):
                game.players[i].hand = strong_pieces.copy()
                print(f"🤖 {game.players[i].name} given strong hand")
            
            # Simulate weak hand detection
            state_machine = self.room.game_state_machine
            prep_state = state_machine.current_state
            
            # Manually trigger weak hand check
            prep_state.weak_players = {game.players[0].name}
            prep_state.current_weak_player = game.players[0].name
            
            print(f"🔍 Weak player detected: {prep_state.current_weak_player}")
            
            # Wait for bot to make redeal decision
            await asyncio.sleep(2.0)
            
            # Check if bot made a decision
            redeal_decisions = getattr(prep_state, 'redeal_decisions', {})
            print(f"🤖 Bot redeal decisions: {redeal_decisions}")
            
            if game.players[0].name in redeal_decisions:
                decision = redeal_decisions[game.players[0].name]
                print(f"✅ Bot made redeal decision: {decision}")
                return True
            else:
                print(f"❌ Bot did not make redeal decision")
                return False
                
        except Exception as e:
            print(f"❌ Weak hand scenario failed: {e}")
            return False
    
    async def _test_declaration_strategies(self):
        """Test bot declaration strategies with different hand strengths"""
        print("\n🎯 Testing Declaration Strategies...")
        
        try:
            # Reset to declaration phase
            await self._force_phase_transition(GamePhase.DECLARATION)
            
            # Wait for bot declarations
            max_wait = 10
            wait_time = 0
            
            while wait_time < max_wait:
                await asyncio.sleep(1.0)
                wait_time += 1
                
                if self.room.game_state_machine.current_phase != GamePhase.DECLARATION:
                    break
                    
                # Check declaration progress
                decl_state = self.room.game_state_machine.current_state
                declarations = decl_state.phase_data.get('declarations', {})
                declaration_order = decl_state.phase_data.get('declaration_order', [])
                
                print(f"📊 Declarations so far: {declarations}")
                
                if len(declarations) >= len(declaration_order):
                    break
            
            # Analyze bot declaration patterns
            final_declarations = self.room.game_state_machine.current_state.phase_data.get('declarations', {})
            
            if len(final_declarations) >= 4:
                print("✅ All bots made declarations")
                
                # Check for realistic declaration values (0-4 range)
                realistic_declarations = all(0 <= val <= 4 for val in final_declarations.values())
                
                if realistic_declarations:
                    print("✅ Bot declarations are in realistic range")
                    
                    # Check total ≠ 8 rule
                    total = sum(final_declarations.values())
                    if total != 8:
                        print(f"✅ Declaration total rule satisfied: {total} ≠ 8")
                        return True
                    else:
                        print(f"❌ Declaration total equals 8: {total}")
                        return False
                else:
                    print("❌ Bot declarations out of realistic range")
                    return False
            else:
                print(f"❌ Only {len(final_declarations)} declarations made")
                return False
                
        except Exception as e:
            print(f"❌ Declaration strategy test failed: {e}")
            return False
    
    async def _test_turn_competition(self):
        """Test bot turn-based competition with realistic piece playing"""
        print("\n🎮 Testing Turn Competition...")
        
        try:
            # Force transition to turn phase
            await self._force_phase_transition(GamePhase.TURN)
            
            turn_count = 0
            max_turns = 15
            bot_plays = {}
            
            while (self.room.game_state_machine.current_phase == GamePhase.TURN and 
                   turn_count < max_turns):
                
                await asyncio.sleep(1.5)  # Give bots time to think
                
                # Track current player and their play
                current_player = getattr(self.room.game, 'current_player', None)
                if current_player:
                    if current_player not in bot_plays:
                        bot_plays[current_player] = 0
                    bot_plays[current_player] += 1
                
                print(f"🎯 Turn {turn_count + 1}: {current_player} playing...")
                
                turn_count += 1
                
                # Check if hands are getting empty
                hand_sizes = [len(player.hand) for player in self.room.game.players]
                print(f"👋 Hand sizes: {hand_sizes}")
                
                if all(size == 0 for size in hand_sizes):
                    print("🏁 All hands empty - round complete")
                    break
            
            # Verify bot participation
            participating_bots = len([bot for bot in bot_plays if bot_plays[bot] > 0])
            
            if participating_bots >= 3:  # At least 3 bots should play
                print(f"✅ Good bot participation: {participating_bots} bots played")
                print(f"📊 Bot play counts: {bot_plays}")
                return True
            else:
                print(f"❌ Poor bot participation: only {participating_bots} bots played")
                return False
                
        except Exception as e:
            print(f"❌ Turn competition test failed: {e}")
            return False
    
    async def _test_endgame_behavior(self):
        """Test bot behavior in endgame scenarios"""
        print("\n🏁 Testing Endgame Behavior...")
        
        try:
            # Force transition to scoring phase
            await self._force_phase_transition(GamePhase.SCORING)
            
            # Wait for scoring calculation
            await asyncio.sleep(2.0)
            
            scoring_state = self.room.game_state_machine.current_state
            round_scores = getattr(scoring_state, 'round_scores', {})
            game_complete = getattr(scoring_state, 'game_complete', False)
            
            print(f"📊 Round scores calculated: {bool(round_scores)}")
            print(f"🏁 Game completion status: {game_complete}")
            
            # Verify scoring data exists
            if round_scores:
                # Check that all bots have scores
                bot_names = [p.name for p in self.room.players]
                bots_with_scores = sum(1 for bot in bot_names if bot in round_scores)
                
                if bots_with_scores >= 3:
                    print(f"✅ Scoring includes {bots_with_scores} bots")
                    return True
                else:
                    print(f"❌ Only {bots_with_scores} bots have scores")
                    return False
            else:
                print("❌ No round scores calculated")
                return False
                
        except Exception as e:
            print(f"❌ Endgame behavior test failed: {e}")
            return False
    
    async def _force_phase_transition(self, target_phase: GamePhase):
        """Force transition to specific phase for testing"""
        print(f"🔄 Forcing transition to {target_phase}")
        
        try:
            state_machine = self.room.game_state_machine
            await state_machine._immediate_transition_to(target_phase, "Test forced transition")
            
            # Wait for transition to complete
            await asyncio.sleep(0.5)
            
            if state_machine.current_phase == target_phase:
                print(f"✅ Successfully transitioned to {target_phase}")
            else:
                print(f"❌ Failed to transition to {target_phase}, still in {state_machine.current_phase}")
                
        except Exception as e:
            print(f"❌ Force transition failed: {e}")
    
    async def analyze_bot_performance(self):
        """Analyze overall bot AI performance"""
        print("\n📈 Analyzing Bot Performance...")
        
        # Get final game state
        game = self.room.game
        
        # Analyze declaration accuracy vs actual performance
        declarations = getattr(game, 'player_declarations', {})
        final_scores = {player.name: player.score for player in game.players}
        
        print(f"🎯 Final declarations: {declarations}")
        print(f"🏆 Final scores: {final_scores}")
        
        # Calculate declaration accuracy
        accuracy_scores = {}
        for player_name in declarations:
            declared = declarations[player_name]
            # In a real implementation, you'd compare against actual piles won
            # For now, assume score reflects performance
            actual_score = final_scores.get(player_name, 0)
            
            # Simple accuracy metric (this would be more sophisticated in real game)
            accuracy = max(0, 100 - abs(declared * 10 - actual_score))
            accuracy_scores[player_name] = accuracy
        
        print(f"📊 Declaration accuracy: {accuracy_scores}")
        
        avg_accuracy = sum(accuracy_scores.values()) / len(accuracy_scores) if accuracy_scores else 0
        print(f"📈 Average bot accuracy: {avg_accuracy:.1f}%")
        
        return avg_accuracy > 50  # Reasonable threshold
    
    async def cleanup(self):
        """Clean up test environment"""
        try:
            if self.room and self.room.game_state_machine:
                await self.room.game_state_machine.stop()
            
            bot_manager = BotManager()
            if self.room_id in bot_manager.active_games:
                del bot_manager.active_games[self.room_id]
                
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")

async def run_bot_behavior_test():
    """Run comprehensive bot behavior test"""
    print("🤖 Starting Bot Realistic Behavior Test")
    print("=" * 50)
    
    tester = BotBehaviorTester()
    
    try:
        await tester.setup_bot_test_environment()
        
        scenarios_passed = await tester.test_realistic_bot_scenarios()
        performance_good = await tester.analyze_bot_performance()
        
        if scenarios_passed and performance_good:
            print("\n🎉 ALL BOT TESTS PASSED!")
            print("✅ Bot AI behavior is realistic and functional")
            print("✅ Bots participate correctly in all phases")
            print("✅ Bot decision-making is within expected parameters")
        else:
            print("\n⚠️ SOME BOT TESTS FAILED")
            print(f"   Scenarios: {'✅' if scenarios_passed else '❌'}")
            print(f"   Performance: {'✅' if performance_good else '❌'}")
        
    except Exception as e:
        print(f"\n❌ BOT TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(run_bot_behavior_test())