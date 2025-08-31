#!/usr/bin/env python3
"""
AI Game Log Reader - Human-readable display of AI debug logs
Shows complete game flow from declarations through turns for each round
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class AIGameLogReader:
    """Reads and displays AI game logs in human-readable format"""
    
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.data = None
        self.load_log()
        
    def load_log(self):
        """Load the JSON log file"""
        try:
            with open(self.log_path, 'r') as f:
                self.data = json.load(f)
        except Exception as e:
            print(f"{Colors.RED}Error loading log file: {e}{Colors.ENDC}")
            sys.exit(1)
            
    def display_game(self):
        """Display the complete game in readable format"""
        if not self.data:
            return
            
        # Game header
        self._print_game_header()
        
        # Process events chronologically
        round_number = 0
        current_round_events = []
        
        for event in self.data['events']:
            event_type = event.get('event')
            
            if event_type == 'game_start':
                self._display_game_start(event)
            elif event_type == 'round_start':
                if current_round_events:
                    self._display_round(round_number, current_round_events)
                round_number = event.get('round_number', round_number + 1)
                current_round_events = [event]
            elif event_type == 'game_end':
                if current_round_events:
                    self._display_round(round_number, current_round_events)
                self._display_game_end(event)
            else:
                current_round_events.append(event)
                
    def _print_game_header(self):
        """Print game header information"""
        game_id = self.data.get('game_id', 'Unknown')
        timestamp = self.data.get('timestamp', '')
        
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}AI GAME LOG - {game_id}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"Timestamp: {timestamp}")
        print(f"Log Level: {self.data.get('log_level', 'Unknown')}")
        
    def _display_game_start(self, event: Dict):
        """Display game start information"""
        print(f"\n{Colors.CYAN}GAME START{Colors.ENDC}")
        print(f"Players: {', '.join(event.get('players', []))}")
        print(f"Round Starter: {event.get('round_starter', 'Unknown')}")
        
        # Display initial hands if available
        if event.get('initial_hands'):
            print(f"\n{Colors.YELLOW}Initial Hands:{Colors.ENDC}")
            for player, hand in event['initial_hands'].items():
                self._display_hand(player, hand)
                
    def _display_round(self, round_number: int, events: List[Dict]):
        """Display a complete round"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}ROUND {round_number}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
        
        # Group events by type
        round_start = None
        declarations = []
        turn_plays = defaultdict(list)  # Group by turn number
        turn_results = {}
        round_end = None
        bugs = []
        
        for event in events:
            event_type = event.get('event')
            if event_type == 'round_start':
                round_start = event
            elif event_type == 'declaration':
                declarations.append(event)
            elif event_type == 'turn_play':
                turn_num = event.get('turn_context', {}).get('turn_number', 0)
                turn_plays[turn_num].append(event)
            elif event_type == 'turn_complete':
                turn_num = event.get('turn_number', 0)
                turn_results[turn_num] = event
            elif event_type == 'round_end':
                round_end = event
            elif event_type == 'bug_detected':
                bugs.append(event)
                
        # Display round start
        if round_start:
            self._display_round_start(round_start)
            
        # Display declaration phase
        if declarations:
            self._display_declaration_phase(declarations)
            
        # Display turns in order
        for turn_num in sorted(turn_plays.keys()):
            self._display_turn(turn_num, turn_plays[turn_num], turn_results.get(turn_num))
            
        # Display round end
        if round_end:
            self._display_round_end(round_end)
            
        # Display bugs if any
        if bugs:
            self._display_bugs(bugs)
            
    def _display_round_start(self, event: Dict):
        """Display round start information"""
        print(f"\n{Colors.GREEN}Round Starter: {event.get('round_starter', 'Unknown')}{Colors.ENDC}")
        
        if event.get('initial_hands'):
            print(f"\n{Colors.YELLOW}Hands Dealt:{Colors.ENDC}")
            for player, hand in event['initial_hands'].items():
                self._display_hand(player, hand)
                
    def _display_declaration_phase(self, declarations: List[Dict]):
        """Display declaration phase"""
        print(f"\n{Colors.CYAN}--- DECLARATION PHASE ---{Colors.ENDC}")
        
        # Sort by position
        sorted_decls = sorted(declarations, key=lambda x: x.get('phase_data', {}).get('position', 0))
        
        for decl in sorted_decls:
            player = decl.get('player', 'Unknown')
            position = decl.get('phase_data', {}).get('position', 0)
            declared = decl.get('decision', {}).get('declared_value', 0)
            reasoning = decl.get('decision', {}).get('reasoning', '')
            
            pos_text = ['1st', '2nd', '3rd', '4th'][position] if position < 4 else f'{position+1}th'
            print(f"{pos_text}: {Colors.BOLD}{player}{Colors.ENDC} declares {Colors.YELLOW}{declared}{Colors.ENDC} - {reasoning}")
            
    def _display_turn(self, turn_num: int, plays: List[Dict], result: Optional[Dict]):
        """Display a single turn"""
        print(f"\n{Colors.CYAN}--- TURN {turn_num} ---{Colors.ENDC}")
        
        # Get turn starter from result (more reliable than am_starter flag)
        starter = result.get('starter', 'Unknown') if result else 'Unknown'
        if starter == 'Unknown' and plays:
            # Fallback to checking am_starter flag
            starter = next((p.get('player') for p in plays 
                          if p.get('turn_context', {}).get('am_starter')), 'Unknown')
        print(f"Starter: {Colors.BOLD}{starter}{Colors.ENDC}")
        
        # Process turn_complete event data if available
        if result and 'plays' in result:
            # Use data from turn_complete event which has all the info
            for play_data in result['plays']:
                player = play_data.get('player', 'Unknown')
                hand_before = play_data.get('hand_before', [])
                pieces_played = play_data.get('pieces_played', [])
                play_type = play_data.get('play_type', 'UNKNOWN')
                is_valid = play_data.get('is_valid', False)
                points = play_data.get('points', 0)
                
                # Find the corresponding turn_play event for additional context
                turn_play_event = next((p for p in plays if p.get('player') == player), {})
                situation = turn_play_event.get('my_situation', {})
                decision = turn_play_event.get('play_decision', {})
                
                # Display hand before play
                if hand_before:
                    hand_str = self._format_pieces(hand_before)
                    print(f"  {Colors.BOLD}{player}'s hand:{Colors.ENDC} {hand_str}")
                
                # Build status line
                captured = situation.get('captured_piles', 0)
                declared = situation.get('declared_target', 0)
                needed = situation.get('piles_needed', 0)
                
                status = f"[{captured}/{declared}]"
                if needed > 0:
                    status = f"{Colors.RED}{status} Need {needed}{Colors.ENDC}"
                else:
                    status = f"{Colors.GREEN}{status} Safe{Colors.ENDC}"
                
                # Format pieces played
                pieces_str = self._format_pieces(pieces_played)
                
                # Color code by play type
                if not is_valid or play_type == 'INVALID':
                    play_color = Colors.RED
                elif play_type in ['STRAIGHT', 'THREE_OF_A_KIND', 'PAIR']:
                    play_color = Colors.GREEN
                else:
                    play_color = Colors.YELLOW
                
                # Get reasoning
                reasoning = decision.get('reasoning', '')
                
                print(f"  {Colors.BOLD}{player}{Colors.ENDC} {status}: {play_color}{play_type}{Colors.ENDC} {pieces_str} - {reasoning}")
        else:
            # Fallback to original display method
            for play in plays:
                self._display_turn_play(play)
        
        # Display turn result
        if result:
            self._display_turn_result(result)
            
    def _display_turn_play(self, play: Dict):
        """Display a single player's turn play"""
        player = play.get('player', 'Unknown')
        context = play.get('turn_context', {})
        situation = play.get('my_situation', {})
        decision = play.get('play_decision', {})
        
        # Build status line
        captured = situation.get('captured_piles', 0)
        declared = situation.get('declared_target', 0)
        needed = situation.get('piles_needed', 0)
        
        status = f"[{captured}/{declared}]"
        if needed > 0:
            status = f"{Colors.RED}{status} Need {needed}{Colors.ENDC}"
        else:
            status = f"{Colors.GREEN}{status} Safe{Colors.ENDC}"
            
        # Display play
        pieces = decision.get('selected_play', [])
        play_type = decision.get('play_type', 'UNKNOWN')
        reasoning = decision.get('reasoning', '')
        
        # Format pieces nicely
        pieces_str = self._format_pieces(pieces)
        
        # Color code by play type
        if play_type == 'INVALID':
            play_color = Colors.RED
        elif play_type in ['STRAIGHT', 'THREE_OF_A_KIND', 'PAIR']:
            play_color = Colors.GREEN
        else:
            play_color = Colors.YELLOW
            
        print(f"  {Colors.BOLD}{player}{Colors.ENDC} {status}: {play_color}{play_type}{Colors.ENDC} {pieces_str} - {reasoning}")
        
    def _display_turn_result(self, result: Dict):
        """Display turn result"""
        winner = result.get('winner')
        if winner:
            winner_name = winner.get('player', 'Unknown')
            winning_type = winner.get('play_type', '')
            points = winner.get('points', 0)
            print(f"  {Colors.GREEN}→ Winner: {Colors.BOLD}{winner_name}{Colors.ENDC} with {winning_type} ({points} points){Colors.ENDC}")
        else:
            print(f"  {Colors.YELLOW}→ No winner (all invalid plays){Colors.ENDC}")
            
        # Show pile counts after turn
        pile_counts = result.get('game_state_after', {}).get('pile_counts', {})
        if pile_counts:
            counts_str = ', '.join(f"{p}: {c}" for p, c in pile_counts.items() if c > 0)
            if counts_str:
                print(f"  Piles: {counts_str}")
                
    def _display_round_end(self, event: Dict):
        """Display round end summary"""
        print(f"\n{Colors.CYAN}--- ROUND SUMMARY ---{Colors.ENDC}")
        
        perfs = event.get('player_performance', {})
        for player, perf in perfs.items():
            declared = perf.get('declared', 0)
            captured = perf.get('captured', 0)
            score = perf.get('score_gained', 0)
            accuracy = perf.get('accuracy', 0)
            
            # Color code score
            if score > 0:
                score_color = Colors.GREEN
                score_str = f"+{score}"
            elif score < 0:
                score_color = Colors.RED
                score_str = str(score)
            else:
                score_color = Colors.YELLOW
                score_str = "0"
                
            # Perfect prediction indicator
            perfect = "✓" if accuracy == 1.0 else "✗"
            
            print(f"  {Colors.BOLD}{player}{Colors.ENDC}: Declared {declared}, Got {captured} {perfect} → {score_color}{score_str}{Colors.ENDC} points")
            
    def _display_game_end(self, event: Dict):
        """Display game end summary"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}GAME OVER{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
        
        winner = event.get('winner', 'Unknown')
        scores = event.get('final_scores', {})
        rounds = event.get('rounds_played', 0)
        duration = event.get('duration_seconds', 0)
        
        print(f"\n{Colors.GREEN}WINNER: {Colors.BOLD}{winner}{Colors.ENDC}")
        print(f"\nFinal Scores:")
        
        # Sort by score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for player, score in sorted_scores:
            if player == winner:
                print(f"  {Colors.GREEN}{Colors.BOLD}{player}: {score}{Colors.ENDC} 👑")
            else:
                print(f"  {player}: {score}")
                
        print(f"\nRounds Played: {rounds}")
        print(f"Duration: {duration:.1f} seconds")
        
        # Display game summary if available
        summary = event.get('game_summary', {})
        if summary.get('bugs_detected'):
            print(f"\n{Colors.RED}Bugs Detected: {summary['bugs_detected']}{Colors.ENDC}")
            
    def _display_bugs(self, bugs: List[Dict]):
        """Display detected bugs"""
        print(f"\n{Colors.RED}--- BUGS DETECTED ---{Colors.ENDC}")
        for bug in bugs:
            bug_type = bug.get('bug_type', 'Unknown')
            player = bug.get('player', 'Unknown')
            desc = bug.get('description', '')
            print(f"  {Colors.RED}• {bug_type}{Colors.ENDC} ({player}): {desc}")
            
    def _display_hand(self, player: str, hand: List[str]):
        """Display a player's hand"""
        formatted = self._format_pieces(hand)
        print(f"  {Colors.BOLD}{player}{Colors.ENDC}: {formatted}")
        
    def _format_pieces(self, pieces: List[str]) -> str:
        """Format pieces list nicely with proper sorting"""
        if not pieces:
            return "[]"
        
        # Define piece values for sorting
        piece_values = {
            'GENERAL': 14,
            'ADVISOR': 11,
            'ELEPHANT': 9,
            'CHARIOT': 7,
            'HORSE': 5,
            'CANNON': 3,
            'SOLDIER': 1
        }
        
        # Parse pieces with their colors and values
        parsed_pieces = []
        for piece in pieces:
            parts = piece.split('_')
            if len(parts) >= 2:
                name = parts[0]
                color = parts[1]
                value = piece_values.get(name, 0)
                # Adjust value for RED pieces (RED is higher value than BLACK for same piece)
                if color == 'RED':
                    value += 1
                parsed_pieces.append((piece, name, color, value))
            else:
                # Handle malformed piece names
                parsed_pieces.append((piece, piece, 'UNKNOWN', 0))
        
        # Sort by color (RED first) then by value (high to low)
        sorted_pieces = sorted(parsed_pieces, 
                              key=lambda x: (0 if x[2] == 'RED' else 1, -x[3]))
        
        # Return the full piece names in sorted order
        return f"[{', '.join(p[0] for p in sorted_pieces)}]"


def find_game_by_id(game_id: str, search_dir: Path = Path("logs/ai_debug")) -> Optional[Path]:
    """Find a game log file by game ID"""
    # Search for files containing the game ID
    for log_file in search_dir.glob("*.json"):
        try:
            with open(log_file, 'r') as f:
                # Quick check - just read first few lines to find game_id
                content = f.read(500)  # Read first 500 chars
                if f'"game_id": "{game_id}"' in content or f'"game_id":"{game_id}"' in content:
                    return log_file
        except:
            continue
    
    # If not found by content, try filename pattern
    for log_file in search_dir.glob(f"*{game_id}*.json"):
        return log_file
        
    return None


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <log_file_or_game_id>")
        print(f"Examples:")
        print(f"  {sys.argv[0]} logs/ai_debug/game_20250830_123456.json")
        print(f"  {sys.argv[0]} AI_393635")
        print(f"  {sys.argv[0]} AI_393635 --dir logs/ai_debug")
        sys.exit(1)
    
    arg = sys.argv[1]
    
    # Check if custom directory is specified
    search_dir = Path("logs/ai_debug")
    if len(sys.argv) > 3 and sys.argv[2] == "--dir":
        search_dir = Path(sys.argv[3])
        if not search_dir.exists():
            print(f"{Colors.RED}Error: Directory not found: {search_dir}{Colors.ENDC}")
            sys.exit(1)
    
    # Check if argument is a file path or game ID
    log_path = Path(arg)
    
    if log_path.exists() and log_path.suffix == '.json':
        # Direct file path provided
        pass
    elif arg.startswith("AI_") or arg.isdigit():
        # Looks like a game ID, search for it
        print(f"Searching for game ID: {arg}...")
        found_path = find_game_by_id(arg, search_dir)
        if found_path:
            print(f"Found: {found_path}")
            log_path = found_path
        else:
            print(f"{Colors.RED}Error: Game ID '{arg}' not found in {search_dir}{Colors.ENDC}")
            sys.exit(1)
    else:
        print(f"{Colors.RED}Error: '{arg}' is not a valid file path or game ID{Colors.ENDC}")
        print(f"Game IDs should start with 'AI_' (e.g., AI_393635)")
        sys.exit(1)
        
    # Create reader and display the game
    reader = AIGameLogReader(log_path)
    reader.display_game()


if __name__ == "__main__":
    main()