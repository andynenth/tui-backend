#!/usr/bin/env python3
"""
🧪 Unit Test: Card Removal Fix Validation
Tests that cards are removed immediately when played, not delayed until turn completion.
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.game import Game
from engine.player import Player  
from engine.piece import Piece
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GameAction, ActionType, GamePhase


class TestCardRemovalFix:
    """Test suite for card removal fix"""
    
    def __init__(self):
        self.test_results = []
        
    async def setup_game(self):
        """Set up a test game with known pieces"""
        print("🧪 Setting up test game...")
        
        # Create players
        players = [
            Player("TestBot1", is_bot=True),
            Player("TestBot2", is_bot=True), 
            Player("TestBot3", is_bot=True),
            Player("TestHuman", is_bot=False)
        ]
        
        # Create known pieces for testing (using proper Piece constructor)
        test_pieces = [
            Piece("GENERAL_RED"),
            Piece("HORSE_BLACK"),
            Piece("CANNON_RED"),
            Piece("SOLDIER_BLACK"),
            Piece("ELEPHANT_RED"),
            Piece("ADVISOR_BLACK"),
            Piece("CHARIOT_RED"),
            Piece("SOLDIER_RED")
        ]
        
        # Give each player 2 pieces for quick testing
        for i, player in enumerate(players):
            player.hand = test_pieces[i*2:(i+1)*2].copy()
            print(f"🎮 {player.name} initial hand: {[str(p) for p in player.hand]} (size: {len(player.hand)})")
        
        # Create game
        game = Game(players)
        
        # Create state machine
        state_machine = GameStateMachine(game)
        
        return game, state_machine
    
    async def test_immediate_card_removal(self):
        """Test that cards are removed immediately when played"""
        print("\n🧪 TEST 1: Immediate Card Removal")
        print("=" * 50)
        
        try:
            game, state_machine = await self.setup_game()
            
            # Start the state machine and transition to TURN phase
            await state_machine.start()
            
            # Skip to turn phase by transitioning through states
            await state_machine._immediate_transition_to(GamePhase.PREPARATION, "Test setup")
            await state_machine._immediate_transition_to(GamePhase.DECLARATION, "Test setup") 
            await state_machine._immediate_transition_to(GamePhase.TURN, "Test setup")
            
            # Get the turn state
            turn_state = state_machine.current_state
            
            # Get first player
            first_player = game.players[0]  # TestBot1
            initial_hand_size = len(first_player.hand)
            initial_hand_pieces = first_player.hand.copy()
            
            print(f"📋 Before play: {first_player.name} has {initial_hand_size} pieces: {[str(p) for p in first_player.hand]}")
            
            # Create a play action - play the first piece
            piece_to_play = first_player.hand[0]
            action = GameAction(
                player_name=first_player.name,
                action_type=ActionType.PLAY_PIECES,
                payload={'pieces': [piece_to_play]},
                timestamp=datetime.now(),
                is_bot=True
            )
            
            # Execute the play
            print(f"🎯 Playing piece: {piece_to_play}")
            result = await turn_state._handle_play_pieces(action)
            
            # Check immediate removal
            after_play_hand_size = len(first_player.hand)
            after_play_pieces = first_player.hand.copy()
            
            print(f"📋 After play: {first_player.name} has {after_play_hand_size} pieces: {[str(p) for p in first_player.hand]}")
            
            # Validate immediate removal
            expected_size = initial_hand_size - 1
            if after_play_hand_size == expected_size:
                print("✅ PASS: Card removed immediately")
                self.test_results.append(("Immediate Removal", "PASS"))
            else:
                print(f"❌ FAIL: Expected hand size {expected_size}, got {after_play_hand_size}")
                self.test_results.append(("Immediate Removal", "FAIL"))
                return
            
            # Validate correct piece was removed
            if piece_to_play not in first_player.hand:
                print("✅ PASS: Correct piece removed")
                self.test_results.append(("Correct Piece Removed", "PASS"))
            else:
                print(f"❌ FAIL: Played piece {piece_to_play} still in hand")
                self.test_results.append(("Correct Piece Removed", "FAIL"))
                return
            
            # Validate remaining pieces are unchanged
            remaining_pieces = initial_hand_pieces.copy()
            remaining_pieces.remove(piece_to_play)
            if set(remaining_pieces) == set(after_play_pieces):
                print("✅ PASS: Other pieces unchanged")
                self.test_results.append(("Other Pieces Unchanged", "PASS"))
            else:
                print(f"❌ FAIL: Other pieces changed unexpectedly")
                self.test_results.append(("Other Pieces Unchanged", "FAIL"))
                
        except Exception as e:
            print(f"❌ TEST ERROR: {e}")
            import traceback
            traceback.print_exc()
            self.test_results.append(("Immediate Removal", "ERROR"))
    
    async def test_multiple_players_turn(self):
        """Test card removal across multiple players in a turn"""
        print("\n🧪 TEST 2: Multiple Players Turn")
        print("=" * 50)
        
        try:
            game, state_machine = await self.setup_game()
            
            # Start and transition to turn phase
            await state_machine.start()
            await state_machine._immediate_transition_to(GamePhase.PREPARATION, "Test setup")
            await state_machine._immediate_transition_to(GamePhase.DECLARATION, "Test setup")
            await state_machine._immediate_transition_to(GamePhase.TURN, "Test setup")
            
            turn_state = state_machine.current_state
            
            # Store initial hand sizes
            initial_hands = {}
            for player in game.players:
                initial_hands[player.name] = {
                    'size': len(player.hand),
                    'pieces': player.hand.copy()
                }
                print(f"📋 {player.name} initial: {len(player.hand)} pieces")
            
            # Have each player play one piece
            for i, player in enumerate(game.players):
                if len(player.hand) > 0:
                    piece_to_play = player.hand[0]
                    
                    action = GameAction(
                        player_name=player.name,
                        action_type=ActionType.PLAY_PIECES,
                        payload={'pieces': [piece_to_play]},
                        timestamp=datetime.now(),
                        is_bot=player.is_bot
                    )
                    
                    print(f"🎯 {player.name} playing: {piece_to_play}")
                    await turn_state._handle_play_pieces(action)
                    
                    # Check immediate removal
                    new_size = len(player.hand)
                    expected_size = initial_hands[player.name]['size'] - 1
                    
                    if new_size == expected_size:
                        print(f"✅ {player.name}: Hand size correct ({new_size})")
                    else:
                        print(f"❌ {player.name}: Expected {expected_size}, got {new_size}")
                        self.test_results.append((f"Multi-Player {player.name}", "FAIL"))
                        return
            
            print("✅ PASS: All players' cards removed immediately")
            self.test_results.append(("Multi-Player Card Removal", "PASS"))
            
        except Exception as e:
            print(f"❌ TEST ERROR: {e}")
            import traceback
            traceback.print_exc()
            self.test_results.append(("Multi-Player Card Removal", "ERROR"))
    
    async def test_no_double_removal(self):
        """Test that turn completion doesn't double-remove cards"""
        print("\n🧪 TEST 3: No Double Removal at Turn End")
        print("=" * 50)
        
        try:
            game, state_machine = await self.setup_game()
            
            # Start and transition to turn phase
            await state_machine.start()
            await state_machine._immediate_transition_to(GamePhase.PREPARATION, "Test setup")
            await state_machine._immediate_transition_to(GamePhase.DECLARATION, "Test setup")
            await state_machine._immediate_transition_to(GamePhase.TURN, "Test setup")
            
            turn_state = state_machine.current_state
            
            # Play pieces for all players to complete the turn
            players_to_test = game.players[:2]  # Test with first 2 players
            hand_sizes_after_play = {}
            
            for player in players_to_test:
                if len(player.hand) > 0:
                    piece_to_play = player.hand[0]
                    
                    action = GameAction(
                        player_name=player.name,
                        action_type=ActionType.PLAY_PIECES,
                        payload={'pieces': [piece_to_play]},
                        timestamp=datetime.now(),
                        is_bot=player.is_bot
                    )
                    
                    await turn_state._handle_play_pieces(action)
                    hand_sizes_after_play[player.name] = len(player.hand)
                    print(f"📋 After play: {player.name} has {len(player.hand)} pieces")
            
            # Simulate turn completion (this should NOT remove more cards)
            print("🏁 Simulating turn completion...")
            await turn_state._process_turn_completion()
            
            # Check that hand sizes haven't changed again
            all_correct = True
            for player in players_to_test:
                current_size = len(player.hand)
                expected_size = hand_sizes_after_play[player.name]
                
                if current_size == expected_size:
                    print(f"✅ {player.name}: No double removal ({current_size} pieces)")
                else:
                    print(f"❌ {player.name}: Double removal detected! {expected_size} -> {current_size}")
                    all_correct = False
            
            if all_correct:
                self.test_results.append(("No Double Removal", "PASS"))
            else:
                self.test_results.append(("No Double Removal", "FAIL"))
                
        except Exception as e:
            print(f"❌ TEST ERROR: {e}")
            import traceback
            traceback.print_exc()
            self.test_results.append(("No Double Removal", "ERROR"))
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🧪 CARD REMOVAL FIX - COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        
        await self.test_immediate_card_removal()
        await self.test_multiple_players_turn() 
        await self.test_no_double_removal()
        
        # Print summary
        print("\n📊 TEST RESULTS SUMMARY")
        print("=" * 30)
        
        passed = 0
        failed = 0
        errors = 0
        
        for test_name, result in self.test_results:
            status_emoji = "✅" if result == "PASS" else "❌" if result == "FAIL" else "⚠️"
            print(f"{status_emoji} {test_name}: {result}")
            
            if result == "PASS":
                passed += 1
            elif result == "FAIL":
                failed += 1
            else:
                errors += 1
        
        print(f"\n📈 SUMMARY: {passed} passed, {failed} failed, {errors} errors")
        
        if failed == 0 and errors == 0:
            print("🎉 ALL TESTS PASSED! Card removal fix is working correctly.")
            return True
        else:
            print("⚠️ Some tests failed. Card removal fix needs attention.")
            return False


async def main():
    """Run the test suite"""
    test_suite = TestCardRemovalFix()
    success = await test_suite.run_all_tests()
    
    if success:
        print("\n✅ CARD REMOVAL FIX VALIDATED")
        exit(0)
    else:
        print("\n❌ CARD REMOVAL FIX VALIDATION FAILED")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())