#!/usr/bin/env python3
"""Extract game data directly from SQLite database"""

import sys
import json
import sqlite3
from pathlib import Path

def extract_room_data(room_id: str):
    """Extract game data for a specific room directly from SQLite"""
    
    # Get the database path (in data directory)
    db_path = Path(__file__).parent / "data" / "game_events.db"
    print(f"Looking for database at: {db_path}")
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Query events for this room
        cursor.execute("""
            SELECT event_type, game_state, metadata, timestamp
            FROM game_events
            WHERE room_id = ?
            ORDER BY sequence_number
        """, (room_id,))
        
        events = cursor.fetchall()
        print(f"Found {len(events)} events for room {room_id}")
        
        if not events:
            print(f"No events found for room {room_id}")
            return
        
        # Create output directory
        output_dir = Path(f"game-data/room-{room_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process events
        all_events = []
        round_events = {}
        current_round = 0
        
        for event_type, game_state_str, metadata_str, timestamp in events:
            # Parse JSON data
            game_state = json.loads(game_state_str) if game_state_str else {}
            metadata = json.loads(metadata_str) if metadata_str else {}
            
            # Track round number
            if 'round_number' in game_state:
                current_round = game_state['round_number']
            
            event_data = {
                'event_type': event_type,
                'timestamp': timestamp,
                'round': current_round,
                'game_state': game_state,
                'metadata': metadata
            }
            
            all_events.append(event_data)
            
            # Group by round
            if current_round not in round_events:
                round_events[current_round] = []
            round_events[current_round].append(event_data)
        
        # Save all events
        all_events_path = output_dir / "all_events.json"
        with open(all_events_path, 'w', encoding='utf-8') as f:
            json.dump(all_events, f, indent=2)
        print(f"Saved all events to: {all_events_path}")
        
        # Extract round 1 data specifically
        if 1 in round_events:
            extract_round1_plays(round_events[1], output_dir)
    
    finally:
        conn.close()

def extract_round1_plays(events, output_dir):
    """Extract play data from round 1 events"""
    
    round1_data = {
        "declarations": {},
        "initial_hands": {},
        "turns": {},
        "plays": []
    }
    
    for event in events:
        event_type = event['event_type']
        game_state = event['game_state']
        metadata = event.get('metadata', {})
        
        # Extract declarations
        if event_type == 'declaration_made':
            player = metadata.get('player_name', 'Unknown')
            declared = metadata.get('declared', 0)
            round1_data['declarations'][player] = declared
            print(f"Found declaration: {player} declared {declared}")
        
        # Extract initial hands from game state
        if event_type == 'round_started' and 'players' in game_state:
            for player_name, player_data in game_state['players'].items():
                if 'hand' in player_data:
                    hand = []
                    for piece in player_data['hand']:
                        hand.append({
                            'type': piece.get('kind', 'UNKNOWN'),
                            'point': piece.get('point', 0)
                        })
                    round1_data['initial_hands'][player_name] = sorted(hand, key=lambda x: x['point'], reverse=True)
                    print(f"Found initial hand for {player_name}: {len(hand)} pieces")
        
        # Extract plays
        if event_type == 'play_made':
            play_data = metadata.copy()
            
            # Get turn number from game state
            turn_num = game_state.get('turn_number', 0)
            if turn_num not in round1_data['turns']:
                round1_data['turns'][turn_num] = []
            
            round1_data['turns'][turn_num].append(play_data)
            round1_data['plays'].append({
                'turn': turn_num,
                **play_data
            })
            
            player = play_data.get('player_name', 'Unknown')
            pieces = play_data.get('pieces', [])
            print(f"Turn {turn_num}: {player} played {len(pieces)} pieces")
    
    # Save round 1 data
    round1_dir = output_dir / "round1"
    round1_dir.mkdir(exist_ok=True)
    
    round1_path = round1_dir / "round1_extracted.json"
    with open(round1_path, 'w', encoding='utf-8') as f:
        json.dump(round1_data, f, indent=2)
    print(f"\nSaved round 1 data to: {round1_path}")
    
    # Print summary
    print(f"\nRound 1 Summary:")
    print(f"Declarations: {round1_data['declarations']}")
    print(f"Total plays: {len(round1_data['plays'])}")
    print(f"Turns: {list(round1_data['turns'].keys())}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_room_data_direct.py <room_id>")
        sys.exit(1)
    
    room_id = sys.argv[1]
    extract_room_data(room_id)