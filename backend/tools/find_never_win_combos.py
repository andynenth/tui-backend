#!/usr/bin/env python3
"""
Find evidence of never-win combos being played in AI game logs
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def is_never_win_combo(play_type, pieces):
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

def analyze_game_log(filepath):
    """Analyze a single game log for never-win combos"""
    never_win_plays = []
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        game_id = data.get('game_id', 'Unknown')
        
        # Look for play events in the log
        for event in data.get('events', []):
            if event.get('event') == 'turn_play':
                player = event.get('player')
                play_type = event.get('play_type')
                pieces = event.get('pieces', [])
                
                if is_never_win_combo(play_type, pieces):
                    never_win_plays.append({
                        'game_id': game_id,
                        'player': player,
                        'play_type': play_type,
                        'pieces': pieces,
                        'turn': event.get('turn_number', 'Unknown'),
                        'round': event.get('round_number', 'Unknown')
                    })
                    
            # Also check turn_plays within turn_complete events
            elif event.get('event') == 'turn_complete':
                for play in event.get('turn_plays', []):
                    player = play.get('player')
                    play_type = play.get('play_type')
                    pieces = play.get('pieces', [])
                    
                    if is_never_win_combo(play_type, pieces):
                        never_win_plays.append({
                            'game_id': game_id,
                            'player': player,
                            'play_type': play_type,
                            'pieces': pieces,
                            'turn': event.get('turn_number', 'Unknown'),
                            'round': event.get('round_number', 'Unknown')
                        })
                        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        
    return never_win_plays

def main():
    # Find all game log files
    log_dir = Path('logs/ai_debug')
    game_files = list(log_dir.glob('game_*.json'))
    
    print(f"Scanning {len(game_files)} game files for never-win combos...")
    
    all_never_wins = []
    
    for filepath in game_files:
        never_wins = analyze_game_log(filepath)
        all_never_wins.extend(never_wins)
        
    # Report findings
    print(f"\nFound {len(all_never_wins)} never-win combo plays!")
    
    if all_never_wins:
        # Group by type
        by_type = defaultdict(list)
        for play in all_never_wins:
            by_type[play['play_type']].append(play)
            
        print("\nBreakdown by combo type:")
        for play_type, plays in by_type.items():
            print(f"  {play_type}: {len(plays)} occurrences")
            
        # Show some examples
        print("\nExample never-win plays:")
        for i, play in enumerate(all_never_wins[:10]):
            pieces_str = ', '.join([f"{p.get('type', 'Unknown')}({p.get('point', '?')})" for p in play['pieces']])
            print(f"  {i+1}. Game {play['game_id']}, {play['player']} played {play['play_type']}: [{pieces_str}]")
            
        # Group by player
        by_player = defaultdict(int)
        for play in all_never_wins:
            by_player[play['player']] += 1
            
        print("\nNever-win plays by player:")
        for player, count in sorted(by_player.items()):
            print(f"  {player}: {count}")
    else:
        print("\nNo never-win combos found in the logs.")
        print("This could mean:")
        print("1. The AI is already avoiding these combos somehow")
        print("2. The game logs don't contain detailed play information")
        print("3. These specific combinations haven't occurred by chance")

if __name__ == "__main__":
    main()