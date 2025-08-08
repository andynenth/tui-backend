#!/usr/bin/env python3
"""Create focused play history for rounds 1-8"""

import json
from datetime import datetime

def parse_timestamp(ts_str: str) -> str:
    """Convert timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return dt.strftime('%H:%M:%S')
    except:
        return ts_str

def format_pieces(pieces):
    """Format pieces for display"""
    if not pieces:
        return "[]"
    
    formatted = []
    for piece in pieces:
        if isinstance(piece, dict):
            name = piece.get('name', piece.get('kind', 'UNKNOWN'))
            point = piece.get('point', 0)
            formatted.append(f"{name}({point})")
        elif isinstance(piece, str):
            formatted.append(piece)
        else:
            formatted.append(str(piece))
    
    return f"[{', '.join(formatted)}]"

def extract_focused_history():
    """Extract rounds 1-8 from the game events"""
    with open('game_events_raw.json', 'r') as f:
        data = json.load(f)
    
    events = data.get('events', [])
    
    game_info = {
        'game_start': None,
        'room_id': '8F4886',
        'players': {},
        'rounds': []
    }
    
    current_round = None
    
    for event in events:
        event_type = event.get('event_type')
        payload = event.get('payload', {})
        timestamp = event.get('created_at', '')
        
        # Track game start and players
        if event_type == 'phase_change' and payload.get('phase') == 'preparation' and not game_info['game_start']:
            game_info['game_start'] = parse_timestamp(timestamp)
            players = payload.get('players', {})
            for name, data in players.items():
                game_info['players'][name] = {
                    'is_bot': data.get('is_bot', False),
                    'avatar_color': data.get('avatar_color'),
                }
        
        # Track round starts
        if event_type == 'phase_change' and payload.get('phase') == 'round_start':
            round_num = payload.get('phase_data', {}).get('round_number')
            if round_num and round_num <= 8:  # Only process rounds 1-8
                current_round = {
                    'round_number': round_num,
                    'starter': payload.get('phase_data', {}).get('current_starter'),
                    'starter_reason': payload.get('phase_data', {}).get('starter_reason'),
                    'timestamp': parse_timestamp(timestamp),
                    'initial_hands': {},
                    'declarations': {},
                    'turns': [],
                    'scores': {},
                    'winner': None
                }
                
                # Extract initial hands
                players = payload.get('players', {})
                for name, data in players.items():
                    current_round['initial_hands'][name] = data.get('hand', [])
                
                game_info['rounds'].append(current_round)
            elif round_num > 8:
                current_round = None  # Stop processing after round 8
        
        # Only process events for rounds 1-8
        if not current_round or current_round['round_number'] > 8:
            continue
        
        # Track declarations
        if event_type == 'action_processed' and payload.get('action_type') == 'declare':
            player_name = payload.get('player_name')
            value = payload.get('payload', {}).get('value')
            if player_name and value is not None:
                current_round['declarations'][player_name] = value
        
        # Track turn plays
        if event_type == 'phase_data_update' and payload.get('phase') == 'turn':
            turn_plays = payload.get('updates', {}).get('turn_plays', {})
            turn_number = payload.get('updates', {}).get('current_turn_number')
            pile_counts = payload.get('updates', {}).get('pile_counts', {})
            
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
                
                # Determine winner if pile counts changed
                if pile_counts:
                    prev_counts = current_round.get('prev_pile_counts', {})
                    for player, count in pile_counts.items():
                        prev_count = prev_counts.get(player, 0)
                        if count > prev_count:
                            turn_data['winner'] = player
                            break
                    current_round['prev_pile_counts'] = pile_counts
        
        # Track round scoring
        if event_type == 'phase_change' and payload.get('phase') == 'scoring':
            players = payload.get('players', {})
            for name, data in players.items():
                current_round['scores'][name] = {
                    'declared': data.get('declared', 0),
                    'captured': data.get('captured_piles', 0),
                    'score': data.get('score', 0)
                }
        
        # Track round winner
        if event_type == 'phase_data_update' and payload.get('phase') == 'scoring':
            reason = payload.get('reason', '')
            if 'wins the round' in reason:
                winner_name = reason.split(' wins the round')[0].split('Player ')[-1]
                current_round['winner'] = winner_name
    
    return game_info

def generate_markdown(game_info):
    """Generate markdown for rounds 1-8"""
    md = []
    
    # Header
    md.append("# Liap Tui Game Play History - Rounds 1-8")
    md.append(f"\n**Game Started:** {game_info['game_start']}")
    md.append(f"**Room ID:** {game_info['room_id']}")
    
    # Players
    md.append("\n## Players")
    md.append("| Player | Type | Avatar Color |")
    md.append("|--------|------|--------------|")
    
    for name, data in game_info['players'].items():
        player_type = "🤖 Bot" if data['is_bot'] else "👤 Human"
        avatar = data['avatar_color'] or "Default"
        md.append(f"| {name} | {player_type} | {avatar} |")
    
    # Summary table with final scores after round 8
    if len(game_info['rounds']) >= 8:
        md.append("\n## Summary After Round 8")
        md.append("| Player | Total Score | Rounds Won | Performance |")
        md.append("|--------|-------------|------------|-------------|")
        
        # Calculate final scores and performance
        final_scores = {}
        rounds_won = {}
        
        for player in game_info['players'].keys():
            final_scores[player] = 0
            rounds_won[player] = 0
        
        # Sum scores through round 8 and count wins
        for round_data in game_info['rounds']:
            if round_data['scores']:
                for player, score_data in round_data['scores'].items():
                    final_scores[player] = score_data.get('score', 0)
            
            if round_data.get('winner'):
                rounds_won[round_data['winner']] += 1
        
        # Sort by score for display
        sorted_players = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
        
        for player, total_score in sorted_players:
            wins = rounds_won.get(player, 0)
            if total_score >= 50:
                performance = "🏆 Winner!"
            elif total_score >= 30:
                performance = "🥈 Strong"
            elif total_score >= 15:
                performance = "🥉 Good"
            else:
                performance = "😰 Struggling"
            
            md.append(f"| {player} | {total_score} | {wins} | {performance} |")
    
    # Detailed rounds
    md.append("\n---\n")
    
    for round_data in game_info['rounds']:
        round_num = round_data['round_number']
        md.append(f"## Round {round_num}")
        md.append(f"**Started:** {round_data['timestamp']} | **Starter:** {round_data['starter']} ({round_data.get('starter_reason', 'unknown')})")
        
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
            
            total_declared = 0
            for player, declared in round_data['declarations'].items():
                md.append(f"| {player} | {declared} |")
                total_declared += declared
            
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
        
        md.append("\n---\n")
    
    return "\n".join(md)

def main():
    """Main function"""
    print("Extracting rounds 1-8 from room 8F4886...")
    
    game_info = extract_focused_history()
    markdown = generate_markdown(game_info)
    
    with open('game_play_history_rounds_1_8.md', 'w') as f:
        f.write(markdown)
    
    print(f"✅ Generated focused play history with {len(game_info['rounds'])} rounds")
    print(f"📝 Saved to: game_play_history_rounds_1_8.md")

if __name__ == "__main__":
    main()