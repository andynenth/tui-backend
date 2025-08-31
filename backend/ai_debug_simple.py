#!/usr/bin/env python3
"""
Simplified AI Debug Mode for Liap Tui
Directly runs game logic without WebSocket infrastructure
"""

import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import sys
from pathlib import Path
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.rules import is_valid_play, get_play_type
from backend.engine.win_conditions import is_game_over, get_winners
import backend.engine.ai as ai
from backend.services.ai_logger import AILogger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleAIGame:
    """Run a single game with all AI players"""
    
    def __init__(self, ai_logger: AILogger, verbose: bool = False):
        self.ai_logger = ai_logger
        self.verbose = verbose
        self.game = None
        self.game_id = f"AI_{int(time.time() * 1000) % 1000000}"
        
    def setup_game(self):
        """Initialize game with 4 AI players"""
        # Create Player objects for the game
        players = []
        for i in range(4):
            name = f"Bot {i + 1}"
            player = Player(name, is_bot=True)
            # Add bot-specific attributes for tracking
            player._bot_name = name
            player._bot_zero_streak = 0
            players.append(player)
        
        # Create game with Player objects
        self.game = Game(players)
        
        player_names = [p.name for p in players]
        logger.info(f"Created game {self.game_id} with players: {player_names}")
        
    def run_game(self) -> Dict:
        """Run a complete game and return results"""
        self.setup_game()
        
        rounds_played = 0
        
        while not is_game_over(self.game) and rounds_played < 10:
            rounds_played += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"ROUND {rounds_played}")
            logger.info(f"{'='*60}")
            
            # Start new round
            self.game.deal_pieces()
            self._initialize_round()
            
            # Log game start AFTER dealing cards (only on first round)
            if rounds_played == 1:
                self.ai_logger.log_game_start(self.game_id, self.game)
            else:
                # Log round start for subsequent rounds
                self.ai_logger.log_round_start(rounds_played, self.game)
            
            # Run phases
            self._run_declaration_phase()
            self._run_turn_phase()
            self._run_scoring_phase(rounds_played)
            
        # Game complete
        winners = get_winners(self.game)
        winner_names = [w.name for w in winners] if winners else []
        final_scores = {p.name: p.score for p in self.game.players}
        
        # If no winner from get_winners, find highest scorer
        if not winner_names:
            max_score = max(p.score for p in self.game.players)
            winner_names = [p.name for p in self.game.players if p.score == max_score]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"GAME OVER - Winner: {winner_names[0] if winner_names else 'None'} - {max(final_scores.values())} pts")
        logger.info(f"Final Scores: {final_scores}")
        logger.info(f"{'='*60}")
        
        return {
            'winner': winner_names[0] if winner_names else None,
            'scores': final_scores,
            'rounds': rounds_played
        }
        
    def _initialize_round(self):
        """Initialize round state"""
        # Reset round-specific data
        self.game.turn_number = 0
        self.game.current_turn_plays = []
        self.game.required_piece_count = None
        self.game.last_turn_winner = None
        self.game.pile_counts = {p.name: 0 for p in self.game.players}
        
        # Reset player round data
        for player in self.game.players:
            player.declared = 0
            player.captured_piles = 0
            
        # Determine round starter
        if self.game.round_number == 1:
            # First round: player with RED GENERAL starts
            for player in self.game.players:
                if player.has_red_general():
                    self.game.round_starter = player.name
                    break
            else:
                # Fallback if no RED GENERAL (shouldn't happen)
                self.game.round_starter = self.game.players[0].name
        else:
            # Subsequent rounds: last round winner starts
            self.game.round_starter = self.game.last_round_winner or self.game.players[0].name
        
    def _run_declaration_phase(self):
        """Run declaration phase for all bots"""
        logger.info("\n--- DECLARATION PHASE ---")
        
        # Get declaration order starting from round starter
        declaration_order = self.game.get_player_order_from(self.game.round_starter)
        previous_declarations = []
        
        for position, player in enumerate(declaration_order):
            # Add tracking attributes
            player._bot_zero_streak = player.zero_declares_in_a_row
            
            # AI decides declaration
            declaration = ai.choose_declare(
                hand=player.hand,
                is_first_player=(position == 0),
                position_in_order=position,
                previous_declarations=previous_declarations,
                must_declare_nonzero=(player.zero_declares_in_a_row >= 2),
                verbose=self.verbose,
                ai_logger=self.ai_logger,
                player_name=player.name
            )
            
            # Apply last player rule
            if position == 3:
                total = sum(previous_declarations) + declaration
                if total == 8:
                    logger.warning(f"{player.name} cannot declare {declaration} (sum would be 8)")
                    # Find valid alternative
                    for alt in range(0, 9):
                        if alt != declaration and sum(previous_declarations) + alt != 8:
                            if player.zero_declares_in_a_row >= 2 and alt == 0:
                                continue  # Can't declare 0 with streak
                            declaration = alt
                            break
                            
            # Record declaration directly (bypass validation for simplicity)
            player.record_declaration(declaration)
            self.game.player_declarations[player.name] = declaration
            previous_declarations.append(declaration)
            
            logger.info(f"{player.name} declares: {declaration}")
            
    def _run_turn_phase(self):
        """Run all turns until round complete"""
        logger.info("\n--- TURN PHASE ---")
        
        turn_number = 0
        
        while not all(len(p.hand) == 0 for p in self.game.players):
            turn_number += 1
            
            # Determine turn order
            if turn_number == 1:
                # First turn: follow declaration order
                current_starter = self.game.round_starter
            else:
                # Subsequent turns: last winner starts
                current_starter = self.game.last_turn_winner.name if self.game.last_turn_winner else self.game.round_starter
                
            turn_order = self.game.get_player_order_from(current_starter)
            
            logger.info(f"\nTurn {turn_number} - Starter: {current_starter}")
            
            # Reset for new turn
            self.game.current_turn_plays = []
            self.game.required_piece_count = None
            
            # Collect all plays for this turn
            turn_plays_data = []
            
            # Each player plays
            for player in turn_order:
                if len(player.hand) == 0:
                    continue
                    
                # Determine required pieces
                if not self.game.current_turn_plays:
                    # First player sets the count
                    required = None
                else:
                    # Must match first player's count
                    required = self.game.required_piece_count
                    
                # Build context for strategic AI
                try:
                    from backend.engine.ai_turn_strategy import TurnPlayContext
                    
                    # Get the starter's play type if this is a responder
                    required_play_type = None
                    if self.game.current_turn_plays and not (player.name == current_starter):
                        # Get the first play (starter's play)
                        first_play = self.game.current_turn_plays[0]
                        required_play_type = get_play_type(first_play.pieces)
                        logger.debug(f"Responder {player.name} must match play type: {required_play_type}")
                    
                    context = TurnPlayContext(
                        my_name=player.name,
                        my_hand=player.hand,
                        my_captured=self.game.pile_counts.get(player.name, 0),
                        my_declared=player.declared,
                        required_piece_count=required,
                        turn_number=turn_number,
                        pieces_per_player=len(player.hand),
                        am_i_starter=(player.name == current_starter),
                        current_plays=[],  # Not tracking in simple mode
                        revealed_pieces=[],  # Not tracking in simple mode
                        player_states={
                            p.name: {
                                "captured": self.game.pile_counts.get(p.name, 0),
                                "declared": p.declared,
                            }
                            for p in self.game.players
                        },
                        required_play_type=required_play_type
                    )
                    
                    # Use strategic AI - returns list of play dictionaries
                    play_list = ai.choose_strategic_play_safe(
                        player.hand, 
                        context,
                        verbose=self.verbose
                    )
                    
                    # Extract pieces from play list
                    selected = []
                    if play_list and isinstance(play_list[0], dict):
                        # New format: list of play dictionaries
                        for play in play_list:
                            selected.extend(play['pieces'])
                    else:
                        # Old format: direct list of pieces
                        selected = play_list
                    
                    # Debug: Log what was returned
                    if selected:
                        logger.debug(f"AI returned {len(selected)} pieces: {[p.kind for p in selected]}")
                        logger.debug(f"Player hand contains: {[p.kind for p in player.hand]}")
                        
                except ImportError:
                    # Fallback to basic AI - returns pieces directly
                    selected = ai.choose_best_play(
                        player.hand,
                        required_count=required,
                        verbose=self.verbose
                    )
                
                # Always track hand before play for turn logging
                hand_before_list = [f"{p.name}_{p.color}" for p in player.hand]
                    
                # Log the play
                if self.ai_logger.should_log('decision'):
                    play_data = {
                        'turn_number': turn_number,
                        'required_piece_count': required,
                        'my_captured': self.game.pile_counts.get(player.name, 0),
                        'my_declared': player.declared,
                        'pieces_remaining': len(player.hand),
                        'selected_play': [f"{p.name}_{p.color}" for p in selected],
                        'play_type': get_play_type(selected),
                        'reasoning': f"{'Must win' if player.captured_piles < player.declared else 'Safe play'}",
                        'am_i_starter': (player.name == current_starter),
                        'last_turn_winner': self.game.last_turn_winner.name if self.game.last_turn_winner else None,
                        'piles_needed': max(0, player.declared - player.captured_piles),
                        'hand_before': hand_before_list
                    }
                    self.ai_logger.log_turn_play(player.name, play_data)
                    
                # Make the play - manually update game state instead of using play_turn
                # Remove pieces from hand
                # Important: The AI might return piece objects that aren't the exact same
                # objects in player.hand, so we need to match by kind and remove the
                # actual pieces from the hand
                pieces_to_remove = []
                selected_kinds = [p.kind for p in selected]
                
                for kind in selected_kinds:
                    # Find and remove the first piece of this kind from hand
                    for i, hand_piece in enumerate(player.hand):
                        if hand_piece.kind == kind and hand_piece not in pieces_to_remove:
                            pieces_to_remove.append(hand_piece)
                            break
                    else:
                        # Piece not found in hand - this is a bug
                        logger.error(f"ERROR: {player.name} trying to play {kind} but it's not in hand!")
                        logger.error(f"Hand: {[p.kind for p in player.hand]}")
                        logger.error(f"Already removing: {[p.kind for p in pieces_to_remove]}")
                        # Skip this piece
                        continue
                
                # Use the pieces we're removing for the play (not the original selected)
                selected = pieces_to_remove
                
                # Record hand after removing pieces (before actual removal)
                hand_after = [f"{p.name}_{p.color}" for p in player.hand if p not in pieces_to_remove]
                
                # Remove the pieces from hand
                for piece in pieces_to_remove:
                    player.hand.remove(piece)
                    
                # Add to current turn plays
                from backend.engine.turn_resolution import TurnPlay
                
                # Check if play is valid based on required count
                play_valid = is_valid_play(selected)
                if play_valid and required is not None:
                    # Must match the required count set by first player
                    play_valid = len(selected) == required
                    
                turn_play = TurnPlay(
                    player=player,
                    pieces=selected,
                    is_valid=play_valid
                )
                self.game.current_turn_plays.append(turn_play)
                
                # Set required piece count from first player
                if not self.game.required_piece_count and turn_play.is_valid:
                    self.game.required_piece_count = len(selected)
                    
                play_type = get_play_type(selected)
                points = sum(p.point for p in selected)
                logger.info(f"  {player.name} plays: {play_type} ({points} points) - {[p.name for p in selected]}")
                
                # Collect play data for turn logging
                turn_plays_data.append({
                    'player': player.name,
                    'pieces': [f"{p.name}_{p.color}" for p in selected],
                    'type': play_type,
                    'valid': play_valid,
                    'points': points,
                    'hand_before': hand_before_list,
                    'hand_after': hand_after
                })
                
            # Resolve turn and get winner data
            winner_data = self._resolve_turn(turn_number)
            
            # Log complete turn data
            self.ai_logger.log_turn_result(turn_number, {
                'required_pieces': self.game.required_piece_count,
                'starter': current_starter,
                'plays': turn_plays_data,
                'winner': winner_data.get('winner_name') if winner_data else None,
                'winning_pieces': winner_data.get('winning_pieces') if winner_data else [],
                'winning_type': winner_data.get('winning_type') if winner_data else None,
                'winning_points': winner_data.get('winning_points') if winner_data else 0,
                'pile_counts': dict(self.game.pile_counts),
                'next_starter': self.game.last_turn_winner.name if self.game.last_turn_winner else current_starter
            })
            
    def _resolve_turn(self, turn_number: int):
        """Determine turn winner and update game state"""
        if not self.game.current_turn_plays:
            return {}
            
        # Find winner based on highest point total
        winner_name = None
        best_score = -1
        winning_play = None
        
        for turn_play in self.game.current_turn_plays:
            # Skip invalid plays
            if not turn_play.is_valid:
                continue
                
            total = sum(p.point for p in turn_play.pieces)
            if total > best_score:
                best_score = total
                winner_name = turn_play.player.name
                winning_play = turn_play
                
        if winner_name:
            # Update game state
            winner = self.game.get_player(winner_name)
            self.game.last_turn_winner = winner
            
            # Award piles equal to the number of pieces played (as per game rules)
            piles_won = len(winning_play.pieces)
            winner.captured_piles += piles_won
            winner.turns_won += 1
            
            # Update pile counts
            if winner_name not in self.game.pile_counts:
                self.game.pile_counts[winner_name] = 0
            self.game.pile_counts[winner_name] += piles_won
            
            logger.info(f"  Turn {turn_number} winner: {winner_name} won {piles_won} piles (now has {winner.captured_piles} total)")
            
            # Return winner data
            return {
                'winner_name': winner_name,
                'winning_pieces': [f"{p.name}_{p.color}" for p in winning_play.pieces],
                'winning_type': get_play_type(winning_play.pieces),
                'winning_points': best_score
            }
        else:
            logger.warning(f"  Turn {turn_number}: No valid plays - no winner")
            return {}
        
    def _run_scoring_phase(self, round_number: int):
        """Score the round and update player scores"""
        logger.info("\n--- SCORING PHASE ---")
        
        round_summary = {
            'round_number': round_number,
            'player_stats': {}
        }
        
        for player in self.game.players:
            # Calculate score
            difference = abs(player.declared - player.captured_piles)
            
            if difference == 0:
                # Perfect prediction
                score_gained = 10 + player.declared * 2
                player.perfect_rounds += 1
            else:
                # Missed prediction
                score_gained = -difference * 2
                
            player.score += score_gained
            
            # Log performance
            accuracy = 1.0 if difference == 0 else 0.0
            round_summary['player_stats'][player.name] = {
                'declared': player.declared,
                'captured': player.captured_piles,
                'accuracy': accuracy,
                'score_gained': score_gained
            }
            
            logger.info(f"{player.name}: Declared {player.declared}, Got {player.captured_piles}, "
                       f"Score: {score_gained:+d} (Total: {player.score})")
                       
        # Log round end
        self.ai_logger.log_round_end(round_number, round_summary)
        
        # Determine round winner (player with highest score this round)
        round_scores = [(p.name, round_summary['player_stats'][p.name]['score_gained']) 
                       for p in self.game.players]
        round_scores.sort(key=lambda x: x[1], reverse=True)
        if round_scores[0][1] > 0:  # Only set winner if they had positive score
            self.game.last_round_winner = round_scores[0][0]
        
        # Increment round number
        self.game.round_number += 1
            

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run AI-only games for debugging (simplified version)'
    )
    
    parser.add_argument(
        '--games', 
        type=int, 
        default=1,
        help='Number of games to simulate (default: 1)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['summary', 'decision', 'detailed'],
        default='decision',
        help='Logging verbosity (default: decision)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed AI reasoning'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for logs'
    )
    
    args = parser.parse_args()
    
    # Statistics tracking
    results = []
    start_time = time.time()
    
    # Run games
    for game_num in range(args.games):
        logger.info(f"\n{'#'*60}")
        logger.info(f"Starting Game {game_num + 1}/{args.games}")
        logger.info(f"{'#'*60}")
        
        # Create logger for this game
        ai_logger = AILogger(args.log_level, args.output)
        
        # Run game
        game = SimpleAIGame(ai_logger, verbose=args.verbose)
        result = game.run_game()
        results.append(result)
        
        # Save logs
        game_duration = time.time() - start_time
        ai_logger.log_game_end(
            game.game_id,
            [result['winner']] if result['winner'] else [],
            result['scores'],
            result['rounds'],
            game_duration
        )
        
    # Print summary statistics
    if len(results) > 1:
        print_summary_statistics(results)
        
        
def print_summary_statistics(results: List[Dict]):
    """Print aggregate statistics from multiple games"""
    print(f"\n{'='*60}")
    print("SUMMARY STATISTICS")
    print(f"{'='*60}")
    
    # Win counts
    win_counts = {}
    all_scores = {}
    
    for result in results:
        winner = result['winner']
        if winner:
            win_counts[winner] = win_counts.get(winner, 0) + 1
            
        for player, score in result['scores'].items():
            if player not in all_scores:
                all_scores[player] = []
            all_scores[player].append(score)
            
    # Print statistics
    print(f"\nTotal Games: {len(results)}")
    print("\nWin Rates:")
    # Include all players, even those who never won
    all_players = sorted(set(all_scores.keys()))
    for player in all_players:
        wins = win_counts.get(player, 0)
        rate = wins / len(results) * 100
        print(f"  {player}: {wins} wins ({rate:.1f}%)")
        
    print("\nAverage Scores:")
    for player in sorted(all_scores.keys()):
        scores = all_scores[player]
        avg = sum(scores) / len(scores)
        print(f"  {player}: {avg:.1f} (min: {min(scores)}, max: {max(scores)})")
        
    # Round statistics
    total_rounds = sum(r['rounds'] for r in results)
    avg_rounds = total_rounds / len(results)
    print(f"\nAverage Rounds per Game: {avg_rounds:.1f}")
    

if __name__ == "__main__":
    main()