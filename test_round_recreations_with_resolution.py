#!/usr/bin/env python3
"""
Test framework to recreate game rounds using turn resolution system.
This properly tracks plays and winners through the game's resolution logic.

Starting with Round 1 from game_play_history_rounds_1_8.md
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


class RoundRecreatorWithResolution:
    """Recreates specific game rounds using turn resolution system"""
    
    def __init__(self):
        self.players = []
        self.game = None
        self.bot_manager = None
        self.turn_history = []  # List of TurnResult objects
        
    def setup_round_1(self):
        """Set up the exact initial conditions from Round 1"""
        print("\n" + "="*80)
        print("RECREATING ROUND 1 WITH TURN RESOLUTION SYSTEM")
        print("="*80)
        
        # Create players - treat all as bots for testing
        self.players = [
            Player("Alexanderium", is_bot=True),  # Treat as bot for AI testing
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
            Player("Bot 4", is_bot=True)
        ]
        
        # Create game instance
        self.game = Game(players=self.players)
        self.bot_manager = BotManager()
        
        # Set up exact initial hands from game history
        hands = {
            "Alexanderium": [
                "SOLDIER_BLACK", "SOLDIER_BLACK", "CANNON_BLACK", "CANNON_RED",
                "HORSE_RED", "ELEPHANT_RED", "ADVISOR_RED", "GENERAL_RED"
            ],
            "Bot 2": [
                "CHARIOT_BLACK", "ADVISOR_BLACK", "SOLDIER_RED", "SOLDIER_RED",
                "SOLDIER_RED", "CANNON_RED", "CHARIOT_RED", "ADVISOR_RED"
            ],
            "Bot 3": [
                "SOLDIER_BLACK", "HORSE_BLACK", "HORSE_BLACK", "ELEPHANT_BLACK",
                "GENERAL_BLACK", "HORSE_RED", "CHARIOT_RED", "ELEPHANT_RED"
            ],
            "Bot 4": [
                "SOLDIER_BLACK", "SOLDIER_BLACK", "CANNON_BLACK", "CHARIOT_BLACK",
                "ELEPHANT_BLACK", "ADVISOR_BLACK", "SOLDIER_RED", "SOLDIER_RED"
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
    
    def simulate_turn(self, turn_number: int, starter_name: str, required_count: int) -> TurnResult:
        """Simulate a turn and return the resolution"""
        print(f"\n" + "="*80)
        print(f"TURN {turn_number} (Starter: {starter_name}, Required: {required_count} pieces)")
        print(f"="*80)
        
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
            
            # Get strategic play
            pieces_to_play = choose_strategic_play(current_hand, context)
            
            # Validate play
            is_valid = True
            if player.name == starter_name:
                is_valid = is_valid_play(pieces_to_play)
                if not is_valid:
                    print(f"  ⚠️ Invalid play for starter!")
            
            turn_plays.append(TurnPlay(player=player, pieces=pieces_to_play, is_valid=is_valid))
        
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
            print("\n❌ No valid plays - no winner")
        
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
    
    def run_full_analysis(self):
        """Run the complete Round 1 recreation with turn resolution"""
        self.setup_round_1()
        self.test_declarations()
        
        # Play turns until all hands are empty
        turn_number = 1
        current_starter = "Alexanderium"  # First player starts round
        
        while True:
            # Check if all players have empty hands
            all_empty = True
            for player in self.players:
                current_hand = self.get_current_hand(player)
                if len(current_hand) > 0:
                    all_empty = False
                    break
            
            if all_empty:
                print("\n" + "="*80)
                print("ALL HANDS EMPTY - ROUND COMPLETE")
                break
            
            # Determine required piece count
            if turn_number == 1:
                required_count = 3
            elif turn_number == 2:
                required_count = 2
            else:
                required_count = 1
            
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
            
            # Safety check to prevent infinite loops
            if turn_number > 10:
                print("\n⚠️ Safety limit reached - stopping after 10 turns")
                break
        
        # Summary
        print("\n" + "="*80)
        print("ROUND SUMMARY")
        print("="*80)
        
        final_counts = self.get_pile_counts()
        for player in self.players:
            declared = getattr(player, 'declared', 0)
            captured = final_counts[player.name]
            status = "AT TARGET" if captured == declared else f"Need {declared - captured} more"
            print(f"{player.name}: {captured}/{declared} piles - {status}")


if __name__ == "__main__":
    recreator = RoundRecreatorWithResolution()
    recreator.run_full_analysis()
    
    print("\n" + "="*80)
    print("ROUND 1 RECREATION WITH TURN RESOLUTION COMPLETE")
    print("="*80)