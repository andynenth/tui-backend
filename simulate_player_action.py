#!/usr/bin/env python3
"""
Simulate a player action for testing
"""
import requests
import json
import sys

def simulate_play(room_id, player_name, piece_to_play):
    """Simulate a player playing a piece via WebSocket message"""
    
    # This would normally go through WebSocket, but for testing we can use the API
    print(f"\nSimulating {player_name} playing {piece_to_play}...")
    
    # Note: In a real game, this would be sent via WebSocket
    # The game uses WebSocket for all game actions
    print("⚠️  Note: Game actions should be sent via WebSocket, not REST API")
    print("This is just for diagnostic purposes")
    
    # Get current game state to find the piece
    state_response = requests.get(f"http://localhost:5050/api/rooms/{room_id}/state")
    if state_response.status_code != 200:
        print(f"Failed to get room state: {state_response.status_code}")
        return
    
    state_data = state_response.json()
    players = state_data.get('state', {}).get('players', [])
    
    # Find player's hand
    player_hand = None
    for player in players:
        if player['name'] == player_name:
            player_hand = player.get('hand', [])
            break
    
    if not player_hand:
        print(f"Player {player_name} not found")
        return
    
    print(f"\n{player_name}'s hand: {player_hand}")
    
    # Find the piece to play
    piece_obj = None
    for piece in player_hand:
        if piece_to_play in piece:
            piece_obj = piece
            break
    
    if not piece_obj:
        print(f"Piece {piece_to_play} not found in hand")
        print("Available pieces:")
        for p in player_hand:
            print(f"  - {p}")
        return
    
    print(f"\nTo play {piece_obj}, send this WebSocket message:")
    message = {
        "action": "play",
        "payload": {
            "pieces": [piece_obj]
        }
    }
    print(json.dumps(message, indent=2))

if __name__ == "__main__":
    room_id = "1A8F34"
    player_name = "Alexanderium"
    piece_to_play = sys.argv[1] if len(sys.argv) > 1 else "SOLDIER_BLACK"
    
    simulate_play(room_id, player_name, piece_to_play)