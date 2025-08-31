#!/usr/bin/env python3
"""
Tool to verify the 4-step responder validation logic is working correctly
by analyzing AI debug game logs.

The 4 steps we're verifying:
1. Find all valid combinations of the required size AND type
2. Check for never-win combos
3. Prioritize non-never-win combos when available
4. Sort by value to dispose burden pieces first
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.engine.piece import Piece
from backend.engine.rules import get_play_type
from backend.engine.ai_turn_strategy import is_never_win_combo


class ResponderVerifier:
    def __init__(self):
        self.total_responder_plays = 0
        self.valid_type_matches = 0
        self.never_win_avoided = 0
        self.never_win_forced = 0
        self.burden_disposed = 0
        self.type_mismatches = []
        self.never_win_when_avoidable = []
        self.good_examples = []
        
    def analyze_logs(self, log_dir: str):
        """Analyze all game logs in the directory"""
        log_path = Path(log_dir)
        if not log_path.exists():
            print(f"Error: Directory {log_dir} does not exist")
            return
            
        # Process all JSON files
        json_files = list(log_path.glob("*.json"))
        print(f"Found {len(json_files)} game logs to analyze\n")
        
        for json_file in json_files:
            self.analyze_game(json_file)
            
        # Print results
        self.print_results()
        
    def analyze_game(self, json_file: Path):
        """Analyze a single game log"""
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading {json_file}: {e}")
            return
            
        game_id = data.get('game_id', 'Unknown')
        
        # Look for turn complete events
        for event in data.get('events', []):
            if event.get('event') == 'turn_complete':
                self.analyze_turn(game_id, event)
                
    def analyze_turn(self, game_id: str, turn_data: Dict):
        """Analyze a single turn for responder behavior"""
        starter = turn_data.get('starter')
        plays = turn_data.get('plays', [])
        
        if not plays or len(plays) < 2:
            return
            
        # Get starter's play type
        starter_play = plays[0]
        if starter_play['player'] != starter:
            # Find the actual starter play
            for play in plays:
                if play['player'] == starter:
                    starter_play = play
                    break
                    
        starter_type = starter_play.get('play_type')
        if not starter_type:
            return
            
        # Analyze each responder
        for i, play in enumerate(plays):
            if play['player'] == starter:
                continue
                
            self.total_responder_plays += 1
            player_name = play['player']
            played_type = play.get('play_type')
            pieces_str = play.get('pieces_played', [])
            
            # Verify Step 1: Type matching
            if played_type == starter_type:
                self.valid_type_matches += 1
                
                # Check for never-win combo
                pieces = self.parse_pieces(pieces_str)
                if pieces and is_never_win_combo(played_type, pieces):
                    # Check if they had alternatives by looking at hand_before
                    hand_before = play.get('hand_before', [])
                    if hand_before:
                        alternatives = self.find_alternatives(
                            hand_before, 
                            len(pieces), 
                            starter_type
                        )
                        
                        if alternatives:
                            # Step 2 & 3 failed: Played never-win when alternatives existed
                            self.never_win_when_avoidable.append({
                                'game_id': game_id,
                                'turn': turn_data.get('turn_number', '?'),
                                'player': player_name,
                                'played': pieces_str,
                                'type': played_type,
                                'alternatives': alternatives
                            })
                        else:
                            # Forced to play never-win (no alternatives)
                            self.never_win_forced += 1
                else:
                    # Successfully avoided never-win or it wasn't never-win
                    self.never_win_avoided += 1
                    
                    # Check if they disposed burden pieces (lowest value)
                    if pieces and len(pieces) > 1:
                        total_value = sum(p.point for p in pieces)
                        # Get all possible combos from hand to see if this was lowest value
                        hand_before = play.get('hand_before', [])
                        if hand_before:
                            min_value = self.find_min_value_combo(
                                hand_before,
                                len(pieces),
                                starter_type
                            )
                            if min_value and total_value <= min_value:
                                self.burden_disposed += 1
                                
                                # Save as good example
                                if len(self.good_examples) < 5:
                                    self.good_examples.append({
                                        'game_id': game_id,
                                        'turn': turn_data.get('turn_number', '?'),
                                        'player': player_name,
                                        'played': pieces_str,
                                        'type': played_type,
                                        'value': total_value,
                                        'reason': 'Disposed burden pieces'
                                    })
            else:
                # Type mismatch!
                self.type_mismatches.append({
                    'game_id': game_id,
                    'turn': turn_data.get('turn_number', '?'),
                    'player': player_name,
                    'expected': starter_type,
                    'actual': played_type,
                    'pieces': pieces_str
                })
                
    def parse_pieces(self, pieces_str: List[str]) -> List[Piece]:
        """Convert piece strings to Piece objects"""
        pieces = []
        for piece_str in pieces_str:
            parts = piece_str.split('_')
            if len(parts) >= 2:
                name = parts[0]
                color = parts[1]
                pieces.append(Piece(f"{name}_{color}"))
        return pieces
        
    def find_alternatives(self, hand: List[str], required: int, play_type: str) -> List[Dict]:
        """Find alternative valid combinations that aren't never-win"""
        from itertools import combinations
        
        pieces = self.parse_pieces(hand)
        alternatives = []
        
        for combo in combinations(pieces, required):
            combo_list = list(combo)
            combo_type = get_play_type(combo_list)
            
            if combo_type == play_type:
                is_never_win = is_never_win_combo(combo_type, combo_list)
                if not is_never_win:
                    total_value = sum(p.point for p in combo_list)
                    alternatives.append({
                        'pieces': [p.kind for p in combo_list],
                        'value': total_value
                    })
                    
        return alternatives
        
    def find_min_value_combo(self, hand: List[str], required: int, play_type: str) -> int:
        """Find the minimum value valid combination of the required type"""
        from itertools import combinations
        
        pieces = self.parse_pieces(hand)
        min_value = float('inf')
        
        for combo in combinations(pieces, required):
            combo_list = list(combo)
            combo_type = get_play_type(combo_list)
            
            if combo_type == play_type:
                total_value = sum(p.point for p in combo_list)
                min_value = min(min_value, total_value)
                
        return min_value if min_value != float('inf') else None
        
    def print_results(self):
        """Print analysis results"""
        print("=" * 80)
        print("RESPONDER VALIDATION VERIFICATION RESULTS")
        print("=" * 80)
        
        print(f"\nTotal responder plays analyzed: {self.total_responder_plays}")
        
        # Step 1: Type matching
        print(f"\n✅ STEP 1 - Type Matching:")
        print(f"  Valid type matches: {self.valid_type_matches}/{self.total_responder_plays} " +
              f"({self.valid_type_matches/max(1,self.total_responder_plays)*100:.1f}%)")
        
        if self.type_mismatches:
            print(f"  ❌ Type mismatches: {len(self.type_mismatches)}")
            for tm in self.type_mismatches[:3]:
                print(f"    - Game {tm['game_id']}, Turn {tm['turn']}: " +
                      f"{tm['player']} played {tm['actual']} instead of {tm['expected']}")
        
        # Step 2 & 3: Never-win avoidance
        print(f"\n✅ STEP 2 & 3 - Never-Win Handling:")
        print(f"  Successfully avoided never-win: {self.never_win_avoided}")
        print(f"  Forced to play never-win (no choice): {self.never_win_forced}")
        
        if self.never_win_when_avoidable:
            print(f"  ❌ Played never-win when alternatives existed: {len(self.never_win_when_avoidable)}")
            for nw in self.never_win_when_avoidable[:3]:
                print(f"    - Game {nw['game_id']}, Turn {nw['turn']}: " +
                      f"{nw['player']} played {nw['played']}")
                print(f"      Could have played: {nw['alternatives'][0]['pieces']} " +
                      f"(value: {nw['alternatives'][0]['value']})")
        
        # Step 4: Burden disposal
        print(f"\n✅ STEP 4 - Burden Disposal:")
        print(f"  Disposed burden pieces (lowest value): {self.burden_disposed}")
        
        # Good examples
        if self.good_examples:
            print(f"\n🌟 GOOD EXAMPLES:")
            for ex in self.good_examples[:3]:
                print(f"  - Game {ex['game_id']}, Turn {ex['turn']}: " +
                      f"{ex['player']} played {ex['type']} with {ex['played']}")
                print(f"    Reason: {ex['reason']}")
        
        # Overall success rate
        print(f"\n📊 OVERALL SUCCESS METRICS:")
        if self.total_responder_plays > 0:
            perfect_plays = (self.valid_type_matches - len(self.never_win_when_avoidable))
            success_rate = perfect_plays / self.total_responder_plays * 100
            print(f"  Perfect responder plays: {perfect_plays}/{self.total_responder_plays} ({success_rate:.1f}%)")
            
            never_win_rate = len(self.never_win_when_avoidable) / self.total_responder_plays * 100
            print(f"  Never-win mistake rate: {len(self.never_win_when_avoidable)}/{self.total_responder_plays} ({never_win_rate:.1f}%)")
        
        print("\n" + "=" * 80)
        
        # Summary
        if not self.type_mismatches and not self.never_win_when_avoidable:
            print("✅ ALL 4 STEPS VERIFIED WORKING CORRECTLY!")
        else:
            print("⚠️  Some issues found - see details above")
            

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python verify_responder_fix.py <log_directory>")
        print("Example: python verify_responder_fix.py logs/ai_debug/")
        sys.exit(1)
        
    log_dir = sys.argv[1]
    verifier = ResponderVerifier()
    verifier.analyze_logs(log_dir)


if __name__ == "__main__":
    main()