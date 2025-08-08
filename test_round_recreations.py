#!/usr/bin/env python3
"""
Test framework to recreate game rounds and analyze bot decision-making.
This helps us understand what bots were thinking during actual games.

Starting with Round 1 from game_play_history_rounds_1_8.md
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple
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


class RoundRecreator:
    """Recreates specific game rounds for analysis"""
    
    def __init__(self):
        self.players = []
        self.game = None
        self.bot_manager = None
        
    def setup_round_1(self):
        """Set up the exact initial conditions from Round 1"""
        print("\n" + "="*80)
        print("RECREATING ROUND 1 - EXACT CONDITIONS FROM GAME HISTORY")
        print("="*80)
        
        # Create players
        self.players = [
            Player("Alexanderium", is_bot=False),
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
            if player.name == "Alexanderium":
                # Human player declared 3
                declared = 3
                previous_declarations.append(declared)
                print(f"\n{player.name} (Human) declared: {declared}")
                continue
            
            # Bot declaration
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
    
    def test_turn_play(self, turn_number: int, starter_name: str, 
                      required_count: int, expected_plays: Dict[str, List[str]]):
        """Test a specific turn with debug output"""
        print(f"\n" + "="*80)
        print(f"TURN {turn_number} ANALYSIS (Starter: {starter_name}, Required: {required_count} pieces)")
        print(f"="*80)
        
        # Set up game state for this turn
        # In the actual game:
        # Turn 1: Alexanderium plays straight, bots forfeit -> Alexanderium wins
        # Turn 2: Bot 3 plays GENERAL(13), others play lower -> Bot 3 wins
        pile_counts = {
            "Alexanderium": 1 if turn_number >= 2 else 0,  # Won Turn 1
            "Bot 2": 0,
            "Bot 3": 1 if turn_number >= 3 else 0,  # Won Turn 2 with GENERAL
            "Bot 4": 0
        }
        
        # Check if any bot is at target
        if turn_number >= 3:
            for bot_name, captured in pile_counts.items():
                if bot_name != "Alexanderium" and captured > 0:
                    # Get the bot's declared value
                    for p in self.players:
                        if p.name == bot_name and hasattr(p, 'declared'):
                            if captured == p.declared:
                                print(f"\n⚠️ {bot_name} is at target ({captured}/{p.declared}) - should avoid overcapture!")
        
        # Test each bot's play decision
        for player in self.players:
            if not player.is_bot:
                continue
                
            print(f"\n{'='*40}")
            print(f"ANALYZING {player.name.upper()} PLAY DECISION")
            print(f"{'='*40}")
            
            # Get current hand by removing all previously played pieces
            played_piece_names = expected_plays.get(player.name, [])
            current_hand = []
            played_count = {}
            
            # Count how many of each piece type were played
            for piece_name in played_piece_names:
                # Convert from full name (e.g., "CHARIOT_RED") to short name (e.g., "CHARIOT")
                short_name = piece_name.split('_')[0]
                played_count[short_name] = played_count.get(short_name, 0) + 1
            
            # Remove played pieces from original hand
            for piece in player.hand:
                if played_count.get(piece.name, 0) > 0:
                    played_count[piece.name] -= 1
                else:
                    current_hand.append(piece)
            
            print(f"Pieces played so far: {played_piece_names}")
            print(f"Current hand: {[f'{p.name}({p.point})' for p in current_hand]}")
            
            # Create context for strategic play
            context = TurnPlayContext(
                my_name=player.name,
                my_hand=current_hand,
                my_captured=pile_counts[player.name],
                my_declared=player.declared if hasattr(player, 'declared') else 1,
                required_piece_count=required_count,
                turn_number=turn_number,
                pieces_per_player=8 - turn_number + 1,
                am_i_starter=(player.name == starter_name),
                current_plays=[],
                revealed_pieces=[],
                player_states={
                    "Alexanderium": {"captured": pile_counts["Alexanderium"], "declared": 3},
                    "Bot 2": {"captured": pile_counts["Bot 2"], "declared": player.declared if player.name == "Bot 2" else 4},
                    "Bot 3": {"captured": pile_counts["Bot 3"], "declared": player.declared if player.name == "Bot 3" else 3},
                    "Bot 4": {"captured": pile_counts["Bot 4"], "declared": player.declared if player.name == "Bot 4" else 1}
                }
            )
            
            # Call strategic play with debug output
            pieces_to_play = choose_strategic_play(current_hand, context)
    
    def run_full_analysis(self):
        """Run the complete Round 1 recreation"""
        self.setup_round_1()
        self.test_declarations()
        
        # Track cumulative pieces played by each bot
        played_pieces = {
            "Bot 2": [],
            "Bot 3": [],
            "Bot 4": []
        }
        
        # Turn 1: Alexanderium starts, plays 3 pieces
        print("\n" + "#"*80)
        print("TURN 1: Alexanderium plays STRAIGHT (GEN-ADV-ELE)")
        # Note: We're testing what bots SHOULD play, not what they historically played
        self.test_turn_play(1, "Alexanderium", 3, played_pieces)
        
        # Now add what the bots actually played in Turn 1 based on the new strategy
        # (This would normally come from the actual game, but for testing we'll use expected values)
        # Bot 2 should dispose: CHARIOT(8), CHARIOT(7), CANNON(4)
        played_pieces["Bot 2"].extend(["CHARIOT_RED", "CHARIOT_BLACK", "CANNON_RED"])
        # Bot 3 should dispose: ELEPHANT(10), ELEPHANT(9), CHARIOT(8)
        played_pieces["Bot 3"].extend(["ELEPHANT_RED", "ELEPHANT_BLACK", "CHARIOT_RED"])
        # Bot 4 should dispose: ADVISOR(11), ELEPHANT(9), CHARIOT(7)
        played_pieces["Bot 4"].extend(["ADVISOR_BLACK", "ELEPHANT_BLACK", "CHARIOT_BLACK"])
        
        # Turn 2: Bot 2 starts (won Turn 1), plays 1 piece
        print("\n" + "#"*80)
        print("TURN 2: Bot 2 starts, plays singles")
        self.test_turn_play(2, "Bot 2", 1, played_pieces)
        
        # Add what was played in Turn 2
        played_pieces["Bot 2"].append("SOLDIER_RED")
        played_pieces["Bot 3"].append("SOLDIER_BLACK")  # Weak piece disposal
        played_pieces["Bot 4"].append("SOLDIER_BLACK")  # Weak piece disposal
        
        # Turn 3: Bot 3 starts (won Turn 2), plays 1 piece - CRITICAL!
        print("\n" + "#"*80)
        print("TURN 3: Bot 3 starts (AT TARGET!) - CRITICAL MOMENT")
        self.test_turn_play(3, "Bot 3", 1, played_pieces)


if __name__ == "__main__":
    recreator = RoundRecreator()
    recreator.run_full_analysis()
    
    print("\n" + "="*80)
    print("ROUND 1 RECREATION COMPLETE")
    print("="*80)
    print("\nKey insights will be revealed by the debug logging above!")
    print("Look for:")
    print("1. Why Bot 3 declared only 1 pile")
    print("2. Why Bot 3 played all weak pieces in Turn 1")
    print("3. Whether overcapture avoidance activated in Turn 3")
    print("4. What Bot 3's execution plan was")