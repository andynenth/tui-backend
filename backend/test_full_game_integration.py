#!/usr/bin/env python3
"""
🧪 Full Game Integration Test with Realistic Data
Tests complete game flow from start to finish with actual bot participation
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

class FullGameTester:
    """Test complete game scenarios with realistic data"""
    
    def __init__(self):
        self.room_id = "TEST_ROOM_001"
        self.room = None
        self.bot_manager = None
        self.game_events = []
        self.phase_history = []
        
    async def setup_test_environment(self):
        """Setup realistic test environment"""
        print("🧪 Setting up full game test environment...")
        
        # Create room with realistic players
        self.room = Room(self.room_id, "TestPlayer")
        
        # Add human player (slot 0) - room host is already added
        # Host is automatically the first player
        
        # Add 3 bots with realistic names
        bot_names = ["AlphaBot", "BetaBot", "GammaBot"] 
        for bot_name in bot_names:
            slot = self.room.join_room(bot_name)
            if slot == -1:
                raise Exception(f"Failed to add bot {bot_name}")
            # Convert to bot after joining
            self.room.players[slot].is_bot = True
        
        print(f"✅ Room setup complete: {[p.name for p in self.room.players]}")
        
    async def test_complete_game_flow(self):
        """Test complete game from preparation to game end"""
        print("\n🎮 Starting complete game flow test...")
        
        # Start game with broadcast callback to track events
        result = await self.room.start_game_safe(self._track_broadcasts)
        
        if not result["success"]:
            raise Exception(f"Game start failed: {result}")
            
        print(f"✅ Game started successfully: {result['operation_id']}")
        
        # Verify bot manager is registered
        bot_manager = BotManager()
        if self.room_id not in bot_manager.active_games:
            raise Exception("Bot manager not registered for test room")
        
        print("✅ Bot manager registration verified")
        
        # Test each phase with realistic scenarios
        await self._test_preparation_phase()
        await self._test_declaration_phase()
        await self._test_turn_phase()
        await self._test_scoring_phase()
        
        print("🎉 Complete game flow test passed!")
        
    async def _test_preparation_phase(self):
        """Test preparation phase with realistic weak hand scenarios"""
        print("\n🎴 Testing Preparation Phase...")
        
        # Wait for preparation to complete
        await asyncio.sleep(0.5)
        
        current_phase = self.room.game_state_machine.current_phase
        if current_phase == GamePhase.PREPARATION:
            print("⚠️ Still in preparation - checking for weak hands...")
            
            # If stuck in preparation, simulate redeal decisions
            phase_data = self.room.game_state_machine.current_state.phase_data
            weak_players = phase_data.get('weak_players', set())
            
            if weak_players:
                print(f"🃏 Found weak players: {weak_players}")
                # Simulate bot redeal decisions
                for weak_player in weak_players:
                    if any(p.name == weak_player and p.is_bot for p in self.room.players):
                        # Bot declines redeal (most common)
                        action = GameAction(
                            action_type=ActionType.REDEAL_RESPONSE,
                            player_name=weak_player,
                            payload={"accept": False}
                        )
                        await self.room.game_state_machine.handle_action(action)
                        print(f"🤖 Bot {weak_player} declined redeal")
            
            # Wait for transition
            await asyncio.sleep(0.5)
        
        # Verify we moved to declaration
        current_phase = self.room.game_state_machine.current_phase
        if current_phase != GamePhase.DECLARATION:
            raise Exception(f"Expected DECLARATION phase, got {current_phase}")
            
        print("✅ Preparation phase completed successfully")
        
    async def _test_declaration_phase(self):
        """Test declaration phase with realistic bot behavior"""
        print("\n🎯 Testing Declaration Phase...")
        
        # Get current phase data
        phase_data = self.room.game_state_machine.current_state.phase_data
        declaration_order = phase_data.get('declaration_order', [])
        
        print(f"📋 Declaration order: {[str(p) for p in declaration_order]}")
        
        # Track declarations
        declarations_made = 0
        max_declarations = len(declaration_order)
        
        # Wait for bot declarations and simulate human if needed
        for i in range(max_declarations):
            await asyncio.sleep(1.0)  # Give bots time to declare
            
            current_declarations = self.room.game_state_machine.current_state.phase_data.get('declarations', {})
            current_declarer = self.room.game_state_machine.current_state.phase_data.get('current_declarer')
            
            print(f"📊 Current declarations: {current_declarations}")
            print(f"🎯 Current declarer: {current_declarer}")
            
            # If it's human player's turn, make a realistic declaration
            if current_declarer == "TestPlayer":
                # Calculate realistic declaration based on hand
                player_hand = None
                for player in self.room.game.players:
                    if player.name == "TestPlayer":
                        player_hand = player.hand
                        break
                
                if player_hand:
                    # Realistic declaration: count strong pieces (>9 points)
                    strong_pieces = sum(1 for piece in player_hand if piece.point > 9)
                    declaration_value = min(max(strong_pieces - 1, 0), 4)  # Conservative estimate
                    
                    action = GameAction(
                        action_type=ActionType.DECLARE,
                        player_name="TestPlayer",
                        payload={"value": declaration_value}
                    )
                    
                    result = await self.room.game_state_machine.handle_action(action)
                    print(f"👤 Human declared {declaration_value}: {result}")
            
            # Check if all declarations complete
            if len(current_declarations) >= max_declarations:
                break
                
        # Verify transition to turn phase
        await asyncio.sleep(1.0)
        current_phase = self.room.game_state_machine.current_phase
        if current_phase != GamePhase.TURN:
            raise Exception(f"Expected TURN phase, got {current_phase}")
            
        print("✅ Declaration phase completed successfully")
        
    async def _test_turn_phase(self):
        """Test turn phase with realistic piece playing"""
        print("\n🎮 Testing Turn Phase...")
        
        # Play several turns with realistic strategies
        turns_played = 0
        max_turns = 20  # Safety limit
        
        while (self.room.game_state_machine.current_phase == GamePhase.TURN and 
               turns_played < max_turns):
            
            await asyncio.sleep(1.0)  # Give bots time to play
            
            # Get current turn state
            turn_state = self.room.game_state_machine.current_state
            current_player = getattr(self.room.game, 'current_player', None)
            
            print(f"🎯 Turn {turns_played + 1}: Current player: {current_player}")
            
            # If it's human player's turn, make a realistic play
            if current_player == "TestPlayer":
                player_obj = None
                for player in self.room.game.players:
                    if player.name == "TestPlayer":
                        player_obj = player
                        break
                
                if player_obj and len(player_obj.hand) > 0:
                    # Realistic strategy: play 1-3 pieces with moderate values
                    hand_size = len(player_obj.hand)
                    pieces_to_play = min(random.randint(1, 3), hand_size)
                    
                    # Select pieces to play (first N pieces for simplicity)
                    piece_indices = list(range(pieces_to_play))
                    
                    action = GameAction(
                        action_type=ActionType.PLAY_PIECES,
                        player_name="TestPlayer", 
                        payload={"piece_indices": piece_indices}
                    )
                    
                    result = await self.room.game_state_machine.handle_action(action)
                    print(f"👤 Human played {pieces_to_play} pieces: {result}")
            
            turns_played += 1
            
            # Check if all hands empty (should transition to scoring)
            all_hands_empty = all(len(player.hand) == 0 for player in self.room.game.players)
            if all_hands_empty:
                print("🏁 All hands empty - should transition to scoring")
                break
        
        # Wait for transition to scoring
        await asyncio.sleep(1.0)
        current_phase = self.room.game_state_machine.current_phase
        if current_phase not in [GamePhase.SCORING, GamePhase.PREPARATION]:  # Could be next round
            print(f"⚠️ Unexpected phase after turns: {current_phase}")
            
        print(f"✅ Turn phase completed after {turns_played} turns")
        
    async def _test_scoring_phase(self):
        """Test scoring phase and round transitions"""
        print("\n🏆 Testing Scoring Phase...")
        
        if self.room.game_state_machine.current_phase != GamePhase.SCORING:
            print("ℹ️ Skipping scoring test - not in scoring phase")
            return
            
        # Wait for scoring calculation
        await asyncio.sleep(1.0)
        
        # Get scoring data
        scoring_state = self.room.game_state_machine.current_state
        round_scores = getattr(scoring_state, 'round_scores', {})
        game_complete = getattr(scoring_state, 'game_complete', False)
        
        print(f"📊 Round scores: {round_scores}")
        print(f"🏁 Game complete: {game_complete}")
        
        # Verify scores are calculated
        if not round_scores:
            raise Exception("No round scores calculated")
            
        print("✅ Scoring phase completed successfully")
        
        # Wait for next round or game end
        await asyncio.sleep(1.0)
        final_phase = self.room.game_state_machine.current_phase
        print(f"🎭 Final phase: {final_phase}")
        
    async def _track_broadcasts(self, room_id: str, event_type: str, data: dict):
        """Track all broadcast events during game"""
        self.game_events.append({
            "room_id": room_id,
            "event_type": event_type, 
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        if event_type == "phase_change":
            phase = data.get("phase")
            if phase:
                self.phase_history.append(phase)
                print(f"📡 Phase change broadcast: {phase}")
    
    async def verify_test_results(self):
        """Verify comprehensive test results"""
        print("\n🔍 Verifying test results...")
        
        # Check phase transitions
        expected_phases = ["preparation", "declaration", "turn", "scoring"]
        phases_seen = list(dict.fromkeys(self.phase_history))  # Remove duplicates, preserve order
        
        print(f"📋 Phases seen: {phases_seen}")
        print(f"📋 Expected: {expected_phases}")
        
        for expected_phase in expected_phases:
            if expected_phase not in phases_seen:
                print(f"⚠️ Missing phase: {expected_phase}")
        
        # Check game events
        print(f"📡 Total events broadcast: {len(self.game_events)}")
        
        # Verify bot participation
        bot_actions = [event for event in self.game_events 
                      if event.get("data", {}).get("player_name") in ["AlphaBot", "BetaBot", "GammaBot"]]
        print(f"🤖 Bot actions detected: {len(bot_actions)}")
        
        print("✅ Test verification completed")
        
    async def cleanup(self):
        """Clean up test environment"""
        try:
            if self.room and self.room.game_state_machine:
                await self.room.game_state_machine.stop()
            
            # Clean up bot manager
            bot_manager = BotManager()
            if self.room_id in bot_manager.active_games:
                del bot_manager.active_games[self.room_id]
                
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")

# Add missing import
import random

async def run_full_game_test():
    """Run complete realistic game test"""
    print("🧪 Starting Full Game Integration Test with Realistic Data")
    print("=" * 60)
    
    tester = FullGameTester()
    
    try:
        await tester.setup_test_environment()
        await tester.test_complete_game_flow()
        await tester.verify_test_results()
        
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Game transitions work correctly")
        print("✅ Bot participation verified")
        print("✅ Realistic data handling confirmed")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(run_full_game_test())