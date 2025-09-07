#!/usr/bin/env python3
"""Extract game data for a specific room from the database"""

import sys
import json
import sqlite3
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.services.play_history_simple import PlayHistorySimpleService
from backend.services.event_store_v2 import EventStoreV2

def extract_room_data(room_id: str):
    """Extract and save game data for a specific room"""

    # Get the database path (project root)
    db_path = Path(__file__).parent / "game_events.db"
    print(f"Looking for database at: {db_path}")

    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    # Create event store and play history service
    event_store = EventStoreV2(str(db_path))
    play_history_service = PlayHistorySimpleService(event_store)

    try:
        # Get play history for the room
        print(f"\nExtracting play history for room {room_id}...")
        play_history = play_history_service.get_play_history(room_id, include_ai_analysis=True)

        if play_history is None:
            print(f"No play history found for room {room_id}")
            return

        # Create output directory
        output_dir = Path(f"game-data/room-{room_id}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save full play history
        full_path = output_dir / "full_play_history.json"
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(play_history.dict(), f, indent=2)
        print(f"Saved full play history to: {full_path}")

        # Extract and save each round
        if play_history.rounds:
            for round_data in play_history.rounds:
                round_num = round_data['round_number']
                round_dir = output_dir / f"round{round_num}"
                round_dir.mkdir(exist_ok=True)

                # Save round data
                round_path = round_dir / f"round{round_num}_data.json"
                with open(round_path, 'w', encoding='utf-8') as f:
                    json.dump(round_data, f, indent=2)
                print(f"Saved round {round_num} data to: {round_path}")

                # Extract key info for analysis
                if round_num == 1:
                    extract_round1_data(round_data, round_dir)

    except Exception as e:
        print(f"Error extracting data: {e}")
        import traceback
        traceback.print_exc()

def extract_round1_data(round_data, output_dir):
    """Extract specific data from round 1 for analysis"""

    extracted = {
        "declarations": {},
        "initial_hands": {},
        "turns": []
    }

    # Get declarations and initial hands
    if 'declaration' in round_data:
        for player_data in round_data['declaration'].get('player_declarations', []):
            player_name = player_data['player_name']
            extracted['declarations'][player_name] = player_data['declared']

            # Get initial hand from ai_analysis if available
            if 'ai_analysis' in player_data:
                ai_data = player_data['ai_analysis']
                if 'initial_hand' in ai_data:
                    hand_info = []
                    for piece in ai_data['initial_hand']:
                        hand_info.append({
                            'type': piece.get('type', piece.get('kind', 'UNKNOWN')),
                            'point': piece.get('point', 0)
                        })
                    extracted['initial_hands'][player_name] = sorted(hand_info, key=lambda x: x['point'], reverse=True)

    # Get turns
    if 'turns' in round_data:
        for turn in round_data['turns']:
            turn_num = turn.get('turn_number', 0)
            turn_data = {
                'turn_number': turn_num,
                'plays': []
            }

            for play in turn.get('plays', []):
                player_name = play['player_name']
                pieces_played = []
                for piece in play['pieces']:
                    pieces_played.append({
                        'type': piece.get('type', piece.get('kind', 'UNKNOWN')),
                        'point': piece.get('point', 0)
                    })

                play_data = {
                    'player': player_name,
                    'pieces': pieces_played,
                    'total_points': play.get('points', sum(p['point'] for p in pieces_played)),
                    'play_type': play.get('play_type', '')
                }

                # Add AI reasoning if available
                if 'ai_reasoning' in play:
                    play_data['ai_reasoning'] = play['ai_reasoning']

                turn_data['plays'].append(play_data)

            # Add winner
            if 'winner' in turn:
                turn_data['winner'] = turn['winner']

            extracted['turns'].append(turn_data)

    # Save extracted data
    extracted_path = output_dir / "round1_extracted.json"
    with open(extracted_path, 'w', encoding='utf-8') as f:
        json.dump(extracted, f, indent=2)
    print(f"Saved extracted round 1 data to: {extracted_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_room_data.py <room_id>")
        sys.exit(1)

    room_id = sys.argv[1]
    extract_room_data(room_id)