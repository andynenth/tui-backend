#!/usr/bin/env python3
"""Parse game events to create play history markdown"""

import json
import sys
from datetime import datetime
from typing import Dict, List, Any

def parse_timestamp(ts_str: str) -> str:
    """Convert timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return dt.strftime('%H:%M:%S')
    except:
        return ts_str

def extract_play_history(events: List[Dict]) -> Dict:
    """Extract structured play history from events"""
    game_data = {
        'rounds': [],
        'current_round': None,
        'players': {},
        'game_start': None
    }
    
    current_round = None
    
    for event in events:
        event_type = event.get('event_type')
        payload = event.get('payload', {})
        timestamp = event.get('created_at', '')
        
        # Track game start
        if event_type == 'phase_change' and payload.get('phase') == 'preparation' and not game_data['game_start']:
            game_data['game_start'] = parse_timestamp(timestamp)
            players = payload.get('players', {})
            for name, data in players.items():
                game_data['players'][name] = {
                    'is_bot': data.get('is_bot', False),
                    'avatar_color': data.get('avatar_color'),
                    'total_score': 0
                }
        
        # Track round starts
        if event_type == 'phase_change' and payload.get('phase') == 'round_start':
            round_num = payload.get('phase_data', {}).get('round_number')
            if round_num:
                current_round = {
                    'round_number': round_num,
                    'starter': payload.get('phase_data', {}).get('current_starter'),
                    'starter_reason': payload.get('phase_data', {}).get('starter_reason'),
                    'declarations': {},
                    'turns': [],
                    'scores': {},
                    'winner': None,
                    'timestamp': parse_timestamp(timestamp),
                    'initial_hands': {}
                }
                
                # Extract initial hands
                players = payload.get('players', {})
                for name, data in players.items():
                    current_round['initial_hands'][name] = data.get('hand', [])
                
                game_data['rounds'].append(current_round)
        
        # Track declarations
        if event_type == 'action_processed' and payload.get('action_type') == 'declare' and current_round:
            player_name = payload.get('player_name')
            value = payload.get('payload', {}).get('value')
            if player_name and value is not None:
                current_round['declarations'][player_name] = value
        
        # Track turn plays
        if event_type == 'phase_data_update' and payload.get('phase') == 'turn' and current_round:
            turn_plays = payload.get('updates', {}).get('turn_plays', {})
            turn_number = payload.get('updates', {}).get('current_turn_number')
            
            if turn_plays and turn_number:
                # Find or create turn
                turn_data = None
                for turn in current_round['turns']:
                    if turn['turn_number'] == turn_number:
                        turn_data = turn
                        break
                
                if not turn_data:
                    turn_data = {
                        'turn_number': turn_number,
                        'plays': {},
                        'winner': None,
                        'timestamp': parse_timestamp(timestamp)
                    }
                    current_round['turns'].append(turn_data)
                
                # Update plays
                turn_data['plays'].update(turn_plays)
        
        # Track turn winners and pile captures
        if event_type == 'phase_data_update' and 'pile_counts' in payload.get('updates', {}) and current_round:
            pile_counts = payload.get('updates', {}).get('pile_counts', {})
            
            # Find the turn that just completed
            if current_round['turns']:
                last_turn = current_round['turns'][-1]
                if 'winner' not in last_turn or not last_turn['winner']:
                    # Determine winner by comparing current to previous pile counts
                    for player, count in pile_counts.items():
                        prev_count = current_round.get('prev_pile_counts', {}).get(player, 0)
                        if count > prev_count:
                            last_turn['winner'] = player
                            break
            
            current_round['prev_pile_counts'] = pile_counts.copy()
        
        # Track round scoring
        if event_type == 'phase_change' and payload.get('phase') == 'scoring' and current_round:
            players = payload.get('players', {})
            for name, data in players.items():
                current_round['scores'][name] = {
                    'declared': data.get('declared', 0),
                    'captured': data.get('captured_piles', 0),
                    'score': data.get('score', 0)
                }
                # Update total score
                if name in game_data['players']:
                    game_data['players'][name]['total_score'] = data.get('score', 0)
        
        # Track round winner
        if event_type == 'phase_data_update' and payload.get('phase') == 'scoring' and current_round:
            reason = payload.get('reason', '')
            if 'wins the round' in reason:
                winner_name = reason.split(' wins the round')[0].split('Player ')[-1]
                current_round['winner'] = winner_name
    
    return game_data

def format_pieces(pieces: List) -> str:
    """Format pieces list for display"""
    if not pieces:
        return "[]"
    
    piece_names = []
    for piece in pieces:
        if isinstance(piece, dict):
            name = piece.get('name', piece.get('kind', 'UNKNOWN'))
            point = piece.get('point', 0)
            piece_names.append(f"{name}({point})")
        elif isinstance(piece, str):
            # Handle string format like "GENERAL_RED(14)"
            piece_names.append(piece)
        else:
            piece_names.append(str(piece))
    
    return f"[{', '.join(piece_names)}]"

def generate_markdown(game_data: Dict) -> str:
    """Generate markdown play history"""
    md = []
    
    # Header
    md.append("# Liap Tui Game Play History")
    md.append(f"\n**Game Started:** {game_data.get('game_start', 'Unknown')}")
    md.append(f"**Room ID:** 8F4886")
    
    # Players
    md.append("\n## Players")
    md.append("| Player | Type | Avatar | Total Score |")
    md.append("|--------|------|--------|-------------|")
    
    for name, data in game_data['players'].items():
        player_type = "🤖 Bot" if data['is_bot'] else "👤 Human"
        avatar = data['avatar_color'] or "Default"
        score = data['total_score']
        md.append(f"| {name} | {player_type} | {avatar} | {score} |")
    
    # Rounds
    for round_data in game_data['rounds']:
        round_num = round_data['round_number']
        md.append(f"\n## Round {round_num}")
        md.append(f"**Started:** {round_data['timestamp']} | **Starter:** {round_data['starter']} ({round_data.get('starter_reason', 'unknown reason')})")
        
        # Initial Hands
        md.append("\n### Initial Hands")
        for player, hand in round_data['initial_hands'].items():
            formatted_hand = format_pieces(hand)
            md.append(f"- **{player}:** {formatted_hand}")
        
        # Declarations
        if round_data['declarations']:
            md.append("\n### Declarations")
            md.append("| Player | Declared Piles |")
            md.append("|--------|----------------|")
            
            for player, declared in round_data['declarations'].items():
                md.append(f"| {player} | {declared} |")
            
            total_declared = sum(round_data['declarations'].values())
            md.append(f"\n**Total Declared:** {total_declared} piles")
        
        # Turns
        if round_data['turns']:
            md.append("\n### Turn Plays")
            
            for turn in round_data['turns']:
                turn_num = turn['turn_number']
                md.append(f"\n#### Turn {turn_num}")
                md.append(f"**Time:** {turn['timestamp']}")
                
                if turn['plays']:
                    md.append("| Player | Pieces | Play Type | Value | Valid |")
                    md.append("|--------|--------|-----------|-------|-------|")
                    
                    for player, play_data in turn['plays'].items():
                        pieces = format_pieces(play_data.get('pieces', []))
                        play_type = play_data.get('play_type', 'UNKNOWN')
                        play_value = play_data.get('play_value', 0)
                        is_valid = "✅" if play_data.get('is_valid', False) else "❌"
                        md.append(f"| {player} | {pieces} | {play_type} | {play_value} | {is_valid} |")
                
                if turn.get('winner'):
                    md.append(f"\n**👑 Turn Winner:** {turn['winner']}")
        
        # Round Results
        if round_data['scores']:
            md.append("\n### Round Results")
            md.append("| Player | Declared | Captured | Score |")
            md.append("|--------|----------|----------|-------|")
            
            for player, score_data in round_data['scores'].items():
                declared = score_data['declared']
                captured = score_data['captured']
                score = score_data['score']
                md.append(f"| {player} | {declared} | {captured} | {score} |")
        
        if round_data.get('winner'):
            md.append(f"\n**🏆 Round Winner:** {round_data['winner']}")
        
        md.append("\n---")
    
    return "\n".join(md)

def main():
    """Main function"""
    try:
        with open('game_events_raw.json', 'r') as f:
            data = json.load(f)
        
        events = data.get('events', [])
        print(f"Processing {len(events)} events...")
        
        game_data = extract_play_history(events)
        markdown = generate_markdown(game_data)
        
        with open('game_play_history.md', 'w') as f:
            f.write(markdown)
        
        print(f"✅ Generated play history with {len(game_data['rounds'])} rounds")
        print(f"📝 Saved to: game_play_history.md")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())