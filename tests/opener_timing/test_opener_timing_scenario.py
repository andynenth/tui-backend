#!/usr/bin/env python3
"""
Test framework to test Single Opener Random Timing Feature with specific hand data.
Uses hands designed to better showcase opener timing scenarios.
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.engine.piece import Piece
from backend.engine.player import Player
from backend.engine.game import Game
from backend.engine.bot_manager import BotManager
from backend.engine.ai import choose_declare_strategic
from backend.engine.ai_turn_strategy import TurnPlayContext, choose_strategic_play
from backend.engine.turn_resolution import TurnPlay, TurnResult, resolve_turn
from backend.engine.rules import is_valid_play


class OpenerTimingTestScenario:
    """Test scenario designed to showcase Single Opener Random Timing Feature"""
    
    def __init__(self):
        self.players = []
        self.game = None
        self.bot_manager = None
        self.turn_history = []  # List of TurnResult objects
        
    def setup_opener_scenario(self):
        """Set up hands designed to test opener timing feature"""
        print("\n" + "="*80)
        print("SINGLE OPENER TIMING FEATURE TEST SCENARIO")
        print("="*80)
        
        # Create players - treat all as bots for testing
        self.players = [
            Player("Bot 1", is_bot=True),
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
            Player("Bot 4", is_bot=True)
        ]
        
        # Create game instance
        self.game = Game(players=self.players)
        self.bot_manager = BotManager()
        
        # Set up hands designed to showcase opener timing
        hands = {
            "Bot 1": [
                "SOLDIER_BLACK", "SOLDIER_BLACK", "SOLDIER_BLACK", "ELEPHANT_BLACK",
                "ELEPHANT_BLACK", "ELEPHANT_RED", "ADVISOR_RED", "GENERAL_RED"
            ],
            "Bot 2": [
                "CHARIOT_BLACK", "ADVISOR_BLACK", "SOLDIER_RED", "SOLDIER_RED",
                "SOLDIER_RED", "CANNON_RED", "CHARIOT_RED", "ADVISOR_RED"
            ],
            "Bot 3": [
                "CANNON_BLACK", "HORSE_BLACK", "HORSE_BLACK", "CANNON_RED",
                "GENERAL_BLACK", "HORSE_RED", "CHARIOT_BLACK", "ELEPHANT_RED"
            ],
            "Bot 4": [
                "SOLDIER_BLACK", "SOLDIER_BLACK", "CANNON_BLACK", "CHARIOT_BLACK",
                "HORSE_RED", "ADVISOR_BLACK", "SOLDIER_RED", "SOLDIER_RED"
            ]
        }
        
        # Convert to Piece objects and set hands
        for player in self.players:
            piece_names = hands[player.name]
            player.hand = [Piece(name) for name in piece_names]
            print(f"\n{player.name} initial hand:")
            print(f"  {[f'{p.name}({p.point})' for p in player.hand]}")
    
    def test_declarations(self):
        """Test the declaration phase with debug output"""
        print("\n" + "="*60)
        print("DECLARATION PHASE ANALYSIS")
        print("="*60)
        
        # Test each bot's declaration decision
        previous_declarations = []
        
        for i, player in enumerate(self.players):
            # All players use bot declaration logic
            print(f"\n{'='*40}")
            print(f"ANALYZING {player.name.upper()} DECLARATION")
            print(f"{'='*40}")
            
            # Set bot name in pieces for logging
            for piece in player.hand:
                piece._bot_name = player.name
            
            # Call strategic declaration with debug output
            declared = choose_declare_strategic(
                hand=player.hand,
                is_first_player=(i == 0),
                position_in_order=i,
                previous_declarations=previous_declarations.copy(),
                must_declare_nonzero=False,
                verbose=True
            )
            
            previous_declarations.append(declared)
            player.declared = declared
            
            print(f"\n🎯 {player.name} FINAL DECLARATION: {declared}")
            print(f"Previous declarations so far: {previous_declarations}")
    
    def simulate_turn(self, turn_number: int, starter_name: str, required_count: Optional[int]) -> TurnResult:
        """Simulate a turn and return the resolution"""
        print(f"\n" + "="*80)
        print(f"TURN {turn_number} (Starter: {starter_name})")
        print("="*80)
        
        # Calculate current pile counts from history
        pile_counts = self.get_pile_counts()
        print(f"Current pile counts: {pile_counts}")
        
        # Check if any bot is at target
        for player in self.players:
            if hasattr(player, 'declared') and pile_counts[player.name] == player.declared:
                print(f"⚠️ {player.name} is at target ({pile_counts[player.name]}/{player.declared})")
        
        # Collect turn plays
        turn_plays = []
        
        # Process players in order (starter first)
        # Find starter
        starter = next(p for p in self.players if p.name == starter_name)
        other_players = [p for p in self.players if p.name != starter_name]
        ordered_players = [starter] + other_players
        
        for player in ordered_players:
            # Get current hand (remove previously played pieces)
            current_hand = self.get_current_hand(player)
            
            # All players use bot logic
            print(f"\n{'='*40}")
            print(f"{player.name.upper()} DECISION")
            print(f"{'='*40}")
            print(f"Current hand: {[f'{p.name}({p.point})' for p in current_hand]}")
            
            # Create context
            context = TurnPlayContext(
                my_name=player.name,
                my_hand=current_hand,
                my_captured=pile_counts[player.name],
                my_declared=player.declared,
                required_piece_count=required_count,
                turn_number=turn_number,
                pieces_per_player=8 - turn_number + 1,
                am_i_starter=(player.name == starter_name),
                current_plays=[],
                revealed_pieces=[],
                player_states={
                    p.name: {"captured": pile_counts[p.name], "declared": getattr(p, 'declared', 0)}
                    for p in self.players
                }
            )
            
            # Add special debug for opener timing check
            # Check for STARTERS choosing piece count
            if player.name == starter_name and required_count is None:
                print(f"\n🎲 OPENER TIMING CHECK for {player.name} (STARTER):")
                # Import needed functions
                from backend.engine.ai_turn_strategy import generate_strategic_plan, detect_opener_only_plan, should_randomly_play_opener
                
                # Generate plan to check if opener-only
                plan = generate_strategic_plan(current_hand, context)
                has_openers = detect_opener_only_plan(plan)
                
                print(f"   - Has openers for random timing: {'YES' if has_openers else 'NO'}")
                if has_openers:
                    print(f"     • {len(plan.assigned_openers)} openers: {[f'{p.name}({p.point})' for p in plan.assigned_openers]}")
                    print(f"     • {len(plan.assigned_combos)} combos: {[f'{t}: {[p.name for p in pieces]}' for t, pieces in plan.assigned_combos[:2]]}")
                    
                    # Check random timing
                    hand_size = len(current_hand)
                    threshold = 0.35 if hand_size >= 6 else 0.40 if hand_size >= 4 else 0.50
                    
                    # Save current random state to show actual roll
                    saved_state = random.getstate()
                    roll = random.random()
                    random.setstate(saved_state)  # Restore state so game logic uses same roll
                    
                    will_play_singles = roll < threshold
                    
                    print(f"   - Hand size: {hand_size} pieces")
                    print(f"   - Random threshold: {int(threshold * 100)}%")
                    print(f"   - Random roll: {roll:.3f} ({int(roll * 100)}%)")
                    print(f"   - Result: {roll:.3f} < {threshold:.2f}? {'✅ YES' if will_play_singles else '❌ NO'}")
                    print(f"   - Decision: {'Play SINGLES due to random timing!' if will_play_singles else 'Use normal strategy'}")
                else:
                    print(f"   - No openers assigned in plan - normal strategy applies")
            
            # Check for RESPONDERS when required=1
            elif player.name != starter_name and required_count == 1:
                print(f"\n🎲 OPENER TIMING CHECK for {player.name} (RESPONDER, required=1):")
                from backend.engine.ai_turn_strategy import generate_strategic_plan, detect_opener_only_plan, should_randomly_play_opener
                
                # Generate plan to check if opener-only
                plan = generate_strategic_plan(current_hand, context)
                has_openers = detect_opener_only_plan(plan)
                
                print(f"   - Has openers for random timing: {'YES' if has_openers else 'NO'}")
                if has_openers:
                    print(f"     • {len(plan.assigned_openers)} openers: {[f'{p.name}({p.point})' for p in plan.assigned_openers]}")
                    print(f"     • {len(plan.assigned_combos)} combos: {[f'{t}: {[p.name for p in pieces]}' for t, pieces in plan.assigned_combos[:2]]}")
                    
                    # Check random timing
                    hand_size = len(current_hand)
                    threshold = 0.35 if hand_size >= 6 else 0.40 if hand_size >= 4 else 0.50
                    
                    # Save current random state to show actual roll
                    saved_state = random.getstate()
                    roll = random.random()
                    random.setstate(saved_state)  # Restore state so game logic uses same roll
                    
                    will_play_singles = roll < threshold
                    
                    print(f"   - Hand size: {hand_size} pieces")
                    print(f"   - Random threshold: {int(threshold * 100)}%")
                    print(f"   - Random roll: {roll:.3f} ({int(roll * 100)}%)")
                    print(f"   - Result: {roll:.3f} < {threshold:.2f}? {'✅ YES' if will_play_singles else '❌ NO'}")
                    print(f"   - Decision: {'Play opener randomly!' if will_play_singles else 'Use normal disposal strategy'}")
                else:
                    print(f"   - No openers assigned in plan - normal strategy applies")
            
            # Get strategic play
            pieces_to_play = choose_strategic_play(current_hand, context)
            
            # Validate play
            is_valid = True
            if player.name == starter_name:
                is_valid = is_valid_play(pieces_to_play)
                if not is_valid:
                    print(f"  ⚠️ Invalid play for starter!")
            
            turn_plays.append(TurnPlay(player=player, pieces=pieces_to_play, is_valid=is_valid))
            
            # If this is the starter and required_count was None, update it
            if player.name == starter_name and required_count is None:
                required_count = len(pieces_to_play)
                print(f"\n  🎲 Starter sets required count: {required_count} pieces")
        
        # Resolve the turn
        turn_result = resolve_turn(turn_plays)
        
        print(f"\n" + "-"*60)
        print("TURN RESOLUTION:")
        for play in turn_result.plays:
            pieces_str = [f'{p.name}({p.point})' for p in play.pieces]
            total_value = sum(p.point for p in play.pieces)
            print(f"  {play.player.name}: {pieces_str} = {total_value} pts - Valid: {play.is_valid}")
        
        if turn_result.winner:
            winner_pieces = [f'{p.name}({p.point})' for p in turn_result.winner.pieces]
            print(f"\n🏆 WINNER: {turn_result.winner.player.name} with {winner_pieces}")
        else:
            print(f"\n❌ No valid plays - no winner")
        
        return turn_result
    
    def get_pile_counts(self) -> Dict[str, int]:
        """Calculate pile counts from turn history"""
        counts = {player.name: 0 for player in self.players}
        for turn_result in self.turn_history:
            if turn_result.winner:
                # Piles captured = number of pieces played
                piles_won = len(turn_result.winner.pieces)
                counts[turn_result.winner.player.name] += piles_won
        return counts
    
    def get_current_hand(self, player: Player) -> List[Piece]:
        """Get player's current hand after removing played pieces"""
        current_hand = player.hand.copy()
        
        # Remove pieces played in previous turns
        for turn_result in self.turn_history:
            for play in turn_result.plays:
                if play.player.name == player.name:
                    for piece in play.pieces:
                        # Remove piece by matching both name and point
                        for i, hand_piece in enumerate(current_hand):
                            if hand_piece.name == piece.name and hand_piece.point == piece.point:
                                current_hand.pop(i)
                                break
        
        return current_hand
    
    def run_opener_timing_test(self):
        """Run the test focused on opener timing scenarios"""
        self.setup_opener_scenario()
        self.test_declarations()
        
        # Play a few turns to test opener timing
        turn_number = 1
        current_starter = "Bot 1"  # First player starts round
        
        for _ in range(5):  # Run 5 turns maximum
            # Check if all players have empty hands
            all_empty = True
            for player in self.players:
                current_hand = self.get_current_hand(player)
                if len(current_hand) > 0:
                    all_empty = False
                    break
            
            if all_empty:
                print("\n" + "="*80)
                print("ALL HANDS EMPTY - TEST COMPLETE")
                break
            
            required_count = None  # Will be set by starter
            
            print("\n" + "#"*80)
            print(f"TURN {turn_number}: {current_starter} starts")
            
            # Simulate the turn
            turn_result = self.simulate_turn(turn_number, current_starter, required_count)
            self.turn_history.append(turn_result)
            
            # Determine next starter
            if turn_result.winner:
                current_starter = turn_result.winner.player.name
            # else keep the same starter
            
            turn_number += 1
        
        # Summary
        print("\n" + "="*80)
        print("OPENER TIMING TEST SUMMARY")
        print("="*80)
        
        final_counts = self.get_pile_counts()
        for player in self.players:
            declared = getattr(player, 'declared', 0)
            captured = final_counts[player.name]
            status = "AT TARGET" if captured == declared else f"Need {declared - captured} more"
            print(f"{player.name}: {captured}/{declared} piles - {status}")


if __name__ == "__main__":
    test = OpenerTimingTestScenario()
    test.run_opener_timing_test()
    
    print("\n" + "="*80)
    print("SINGLE OPENER TIMING FEATURE TEST COMPLETE")
    print("="*80)