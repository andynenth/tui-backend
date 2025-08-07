#!/usr/bin/env python3
"""
Diagnose room state issues
"""
import requests
import json
import sys

def diagnose_room(room_id):
    print(f"\n=== Diagnosing Room {room_id} ===\n")
    
    # Get room state
    state_response = requests.get(f"http://localhost:5050/api/rooms/{room_id}/state")
    if state_response.status_code != 200:
        print(f"Failed to get room state: {state_response.status_code}")
        return
    
    state_data = state_response.json()
    state = state_data.get('state', {})
    
    print(f"Phase: {state.get('phase', 'UNKNOWN')}")
    print(f"Round: {state.get('round_number', 'N/A')}")
    print(f"Game Active: {state.get('game_active', False)}")
    
    # Get recent events
    events_response = requests.get(f"http://localhost:5050/api/rooms/{room_id}/events")
    if events_response.status_code != 200:
        print(f"Failed to get events: {events_response.status_code}")
        return
    
    events_data = events_response.json()
    events = events_data.get('events', [])
    
    # Find current turn state
    print("\n=== Current Turn Analysis ===")
    
    # Find the last phase_data_update for turn phase
    turn_phase_data = None
    for event in reversed(events):
        if event['event_type'] == 'phase_data_update' and event['payload'].get('phase') == 'turn':
            turn_phase_data = event['payload'].get('updates', {})
            break
    
    if turn_phase_data:
        print(f"Current Player: {turn_phase_data.get('current_player', 'UNKNOWN')}")
        print(f"Turn Starter: {turn_phase_data.get('current_turn_starter', 'UNKNOWN')}")
        print(f"Turn Number: {turn_phase_data.get('current_turn_number', 0)}")
        print(f"Required Pieces: {turn_phase_data.get('required_piece_count', 'Not set')}")
        print(f"Turn Complete: {turn_phase_data.get('turn_complete', False)}")
        print(f"\nTurn Order: {turn_phase_data.get('turn_order', [])}")
        
        # Check who has played
        print("\n=== Who Has Played This Turn ===")
        
        # Find play events after the last turn start
        plays_this_turn = []
        last_turn_start = None
        
        for i, event in enumerate(reversed(events)):
            if event['event_type'] == 'phase_data_update' and 'New turn' in event['payload'].get('reason', ''):
                last_turn_start = len(events) - i - 1
                break
        
        if last_turn_start is not None:
            for event in events[last_turn_start:]:
                if event['event_type'] == 'action_processed' and event['payload'].get('action_type') == 'play_pieces':
                    player = event['payload'].get('player_name')
                    pieces = event['payload'].get('payload', {}).get('pieces', [])
                    if pieces:
                        piece_str = pieces[0].get('kind', 'UNKNOWN')
                        plays_this_turn.append(f"{player}: {piece_str}")
        
        for play in plays_this_turn:
            print(f"  - {play}")
        
        print(f"\nTotal plays this turn: {len(plays_this_turn)}")
        
        # Check if all players have played
        turn_order = turn_phase_data.get('turn_order', [])
        if turn_order:
            players_who_played = [p.split(':')[0] for p in plays_this_turn]
            for player in turn_order:
                if player not in players_who_played:
                    print(f"\n⚠️  Waiting for: {player}")
    
    # Check for stuck state
    print("\n=== Diagnosis ===")
    
    if state.get('phase') is None:
        print("❌ CRITICAL: Game phase is None - state machine may have crashed")
    elif turn_phase_data and not turn_phase_data.get('turn_complete', False):
        waiting_for = []
        if turn_order:
            players_who_played = [p.split(':')[0] for p in plays_this_turn]
            waiting_for = [p for p in turn_order if p not in players_who_played]
        
        if waiting_for:
            print(f"⏳ Game is waiting for player(s) to play: {', '.join(waiting_for)}")
        else:
            print("❌ All players have played but turn didn't complete!")
    else:
        print("✅ Game appears to be in normal state")

if __name__ == "__main__":
    room_id = sys.argv[1] if len(sys.argv) > 1 else "1A8F34"
    diagnose_room(room_id)