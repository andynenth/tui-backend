#!/usr/bin/env python3
"""
Analyze never-win combos with full hand context from detailed logs
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import constants for piece values
from backend.engine.constants import PIECE_POINTS

def parse_piece_string(piece_str: str) -> Tuple[str, int]:
    """Parse a piece string like 'CANNON_RED' into name and point value"""
    if piece_str in PIECE_POINTS:
        return piece_str, PIECE_POINTS[piece_str]
    return piece_str, 0

def is_never_win_combo(play_type: str, pieces: List[Dict]) -> bool:
    """Check if a play is a never-win combo"""
    
    if play_type == "STRAIGHT":
        # Check if all pieces are BLACK (odd points)
        all_black = all(p['point'] % 2 == 1 for p in pieces)
        if all_black and len(pieces) >= 3:
            # Check if it's the minimum straight (3,5,7)
            points = sorted([p['point'] for p in pieces])
            if points[:3] == [3, 5, 7]:
                return True
                
    elif play_type == "PAIR":
        # Check if it's SOLDIER_BLACK pair (1+1=2)
        if len(pieces) == 2 and all(p['point'] == 1 for p in pieces):
            return True
            
    elif play_type in ["THREE_OF_A_KIND", "FOUR_OF_A_KIND", "FIVE_OF_A_KIND"]:
        # Check if all are SOLDIER_BLACK (point value 1)
        if all(p['point'] == 1 for p in pieces):
            return True
            
    return False

def find_better_plays(hand: List[str], required_pieces: int) -> List[Dict]:
    """Find all valid plays from hand that match required piece count"""
    from backend.engine.rules import is_valid_play, get_play_type
    from backend.engine.piece import Piece
    
    # Convert hand strings to Piece objects
    pieces = []
    for piece_str in hand:
        piece_name, point = parse_piece_string(piece_str)
        # Create a simple piece-like object
        piece = type('Piece', (), {
            'name': piece_str.split('_')[0],
            'color': piece_str.split('_')[1],
            'kind': piece_str,
            'point': point
        })()
        pieces.append(piece)
    
    valid_plays = []
    
    # Try all combinations of the required size
    from itertools import combinations
    for combo in combinations(pieces, required_pieces):
        combo_list = list(combo)
        if is_valid_play(combo_list):
            play_type = get_play_type(combo_list)
            total_points = sum(p.point for p in combo_list)
            
            # Check if it's a never-win combo
            pieces_dict = [{'name': p.kind, 'point': p.point} for p in combo_list]
            is_never_win = is_never_win_combo(play_type, pieces_dict)
            
            valid_plays.append({
                'pieces': [p.kind for p in combo_list],
                'type': play_type,
                'points': total_points,
                'is_never_win': is_never_win
            })
    
    # Sort by points (descending)
    valid_plays.sort(key=lambda x: x['points'], reverse=True)
    
    return valid_plays

def analyze_never_win_play(game_data: Dict, event: Dict, play: Dict, 
                          current_round: int, initial_hands: Dict) -> Optional[Dict]:
    """Analyze a never-win play with full context"""
    
    player = play.get('player')
    turn_number = event.get('turn_number')
    pieces_played = play.get('pieces_played', [])
    play_type = play.get('play_type')
    required_pieces = event.get('required_pieces')
    
    # Skip if we don't have hand data
    if not initial_hands or player not in initial_hands:
        return None
    
    # Get the player's initial hand for this round
    round_hands = None
    
    # Find the round_start event for the current round
    for e in game_data.get('events', []):
        if e.get('event') == 'round_start' and e.get('round_number') == current_round:
            round_hands = e.get('initial_hands', {})
            break
    
    # If no round_start, use game_start hands for round 1
    if not round_hands and current_round == 1:
        round_hands = initial_hands
    
    if not round_hands or player not in round_hands:
        return None
    
    # Track what pieces have been played by this player
    pieces_played_so_far = []
    for prev_event in game_data.get('events', []):
        if prev_event.get('event') == 'turn_complete':
            prev_turn = prev_event.get('turn_number', 0)
            if prev_turn >= turn_number:
                break
            
            for prev_play in prev_event.get('plays', []):
                if prev_play.get('player') == player and prev_play.get('is_valid'):
                    pieces_played_so_far.extend(prev_play.get('pieces_played', []))
    
    # Calculate remaining hand
    remaining_hand = round_hands[player].copy()
    for piece in pieces_played_so_far:
        if piece in remaining_hand:
            remaining_hand.remove(piece)
    
    # Find better alternatives
    better_plays = find_better_plays(remaining_hand, required_pieces)
    non_never_win_plays = [p for p in better_plays if not p['is_never_win']]
    
    # Create piece objects for the actual play
    actual_pieces = []
    for piece_name in pieces_played:
        _, point = parse_piece_string(piece_name)
        actual_pieces.append({'name': piece_name, 'point': point})
    
    # Get player's declaration and captured piles info
    player_declared = None
    player_captured = None
    
    # Find declaration info - need to check round_end events for player performance
    for e in game_data.get('events', []):
        if e.get('event') == 'round_end' and e.get('round_number') == current_round:
            player_perf = e.get('player_performance', {}).get(player, {})
            player_declared = player_perf.get('declared')
            break
    
    # Get captured piles from game state after this turn
    pile_counts = event.get('game_state_after', {}).get('pile_counts', {})
    player_captured = pile_counts.get(player, 0)
    
    return {
        'game_id': game_data.get('game_id'),
        'round': current_round,
        'turn': turn_number,
        'player': player,
        'play_type': play_type,
        'pieces': actual_pieces,
        'required_pieces': required_pieces,
        'initial_hand': round_hands[player],
        'remaining_hand': remaining_hand,
        'pieces_played_before': pieces_played_so_far,
        'total_alternatives': len(better_plays),
        'non_never_win_alternatives': len(non_never_win_plays),
        'best_alternative': non_never_win_plays[0] if non_never_win_plays else None,
        'all_alternatives': better_plays[:5],  # Top 5 alternatives
        'declared': player_declared,
        'captured': player_captured,
        'piles_needed': player_declared - player_captured if player_declared is not None else None
    }

def analyze_game_log(filepath: Path) -> Tuple[List[Dict], Dict]:
    """Analyze a single game log for never-win combos with context"""
    never_win_analyses = []
    stats = {
        'rounds': 0,
        'turns': 0,
        'plays': 0,
        'never_win_plays': 0,
        'has_detailed_logs': False
    }
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Check if this is a detailed log
        if data.get('log_level') == 'detailed':
            stats['has_detailed_logs'] = True
        
        # Get initial hands from game start
        initial_hands = {}
        for event in data.get('events', []):
            if event.get('event') == 'game_start':
                initial_hands = event.get('initial_hands', {})
                break
        
        current_round = 1
        
        # Process events
        for event in data.get('events', []):
            if event.get('event') == 'round_end':
                stats['rounds'] += 1
                current_round += 1
                
            elif event.get('event') == 'turn_complete':
                stats['turns'] += 1
                
                # Check each play in the turn
                for play in event.get('plays', []):
                    if not play.get('is_valid'):
                        continue
                        
                    stats['plays'] += 1
                    
                    # Check if it's a never-win combo
                    pieces_played = play.get('pieces_played', [])
                    play_type = play.get('play_type')
                    
                    if pieces_played:
                        # Create piece objects
                        pieces = []
                        for piece_name in pieces_played:
                            if piece_name in PIECE_POINTS:
                                pieces.append({
                                    'name': piece_name,
                                    'point': PIECE_POINTS[piece_name]
                                })
                        
                        if is_never_win_combo(play_type, pieces):
                            stats['never_win_plays'] += 1
                            
                            # Analyze with full context
                            analysis = analyze_never_win_play(
                                data, event, play, current_round, initial_hands
                            )
                            
                            if analysis:
                                never_win_analyses.append(analysis)
                                
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        
    return never_win_analyses, stats

def main():
    """Main analysis function"""
    log_dir = Path('logs/ai_debug')
    
    print("🔍 NEVER-WIN COMBO ANALYSIS WITH HAND CONTEXT")
    print("=" * 70)
    
    # Find all game files
    game_files = list(log_dir.glob('game_*.json'))
    
    # Filter for detailed logs only
    detailed_files = []
    for filepath in game_files:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                if data.get('log_level') == 'detailed':
                    detailed_files.append(filepath)
        except:
            pass
    
    print(f"📁 Found {len(detailed_files)} detailed log files (out of {len(game_files)} total)")
    
    if not detailed_files:
        print("❌ No detailed log files found!")
        print("\nTo generate detailed logs, run:")
        print("  python ai_debug_simple.py --games 10 --log-level detailed")
        return
    
    # Analyze all detailed logs
    all_analyses = []
    total_stats = defaultdict(int)
    
    for filepath in detailed_files:
        analyses, stats = analyze_game_log(filepath)
        all_analyses.extend(analyses)
        
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                total_stats[key] += value
    
    print(f"\n📊 ANALYSIS SUMMARY:")
    print(f"  Total games analyzed: {len(detailed_files)}")
    print(f"  Total rounds: {total_stats['rounds']}")
    print(f"  Total turns: {total_stats['turns']}")
    print(f"  Total valid plays: {total_stats['plays']}")
    print(f"  Never-win plays: {total_stats['never_win_plays']}")
    
    if total_stats['plays'] > 0:
        percentage = (total_stats['never_win_plays'] / total_stats['plays']) * 100
        print(f"  Never-win rate: {percentage:.2f}%")
    
    # Categorize the analyses
    forced_plays = []
    poor_choices = []
    
    for analysis in all_analyses:
        if analysis['non_never_win_alternatives'] == 0:
            forced_plays.append(analysis)
        else:
            poor_choices.append(analysis)
    
    print(f"\n🎯 CATEGORIZATION:")
    print(f"  Forced plays (no alternatives): {len(forced_plays)}")
    print(f"  Poor AI choices (had alternatives): {len(poor_choices)}")
    
    # Show examples of poor choices
    if poor_choices:
        print(f"\n❌ POOR AI CHOICES (had better alternatives):")
        for i, analysis in enumerate(poor_choices[:10]):  # Show up to 10 examples
            print(f"\n{i+1}. Game {analysis['game_id']}, Round {analysis['round']}, Turn {analysis['turn']}")
            print(f"   Player: {analysis['player']}")
            print(f"   Declared: {analysis['declared']}, Captured: {analysis['captured']}, Piles needed: {analysis['piles_needed']}")
            
            pieces_str = ', '.join([f"{p['name']}({p['point']})" for p in analysis['pieces']])
            print(f"   Played: {analysis['play_type']} [{pieces_str}]")
            print(f"   Had {analysis['non_never_win_alternatives']} better alternatives!")
            
            if analysis['best_alternative']:
                alt = analysis['best_alternative']
                alt_str = ', '.join(alt['pieces'])
                print(f"   Best alternative: {alt['type']} [{alt_str}] ({alt['points']} pts)")
            
            print(f"   Remaining hand ({len(analysis['remaining_hand'])} pieces): {', '.join(analysis['remaining_hand'])}")
    
    # Show examples of forced plays
    if forced_plays:
        print(f"\n⚠️  FORCED PLAYS (no alternatives):")
        for i, analysis in enumerate(forced_plays[:3]):
            print(f"\n{i+1}. Game {analysis['game_id']}, Round {analysis['round']}, Turn {analysis['turn']}")
            print(f"   Player: {analysis['player']}")
            pieces_str = ', '.join([f"{p['name']}({p['point']})" for p in analysis['pieces']])
            print(f"   Played: {analysis['play_type']} [{pieces_str}]")
            print(f"   Required pieces: {analysis['required_pieces']}")
            print(f"   Remaining hand: {', '.join(analysis['remaining_hand'])}")
            print(f"   Had {analysis['total_alternatives']} valid plays, ALL were never-win combos")
    
    # Summary recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if poor_choices:
        print(f"  • {len(poor_choices)} never-win plays could have been avoided")
        print(f"  • The AI is not properly checking for never-win combos before playing")
        print(f"  • Fix needed in choose_best_play and strategic play selection")
    
    if forced_plays:
        print(f"  • {len(forced_plays)} plays were forced (no better alternatives)")
        print(f"  • These are acceptable - the AI had no choice")

if __name__ == "__main__":
    main()