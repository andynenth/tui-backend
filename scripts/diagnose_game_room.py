#!/usr/bin/env python3
"""
Diagnostic tool for analyzing game room state and identifying issues.

Usage: python scripts/diagnose_game_room.py [ROOM_ID]
"""
import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional


class GameRoomDiagnostics:
    def __init__(self, base_url: str = "http://localhost:5050"):
        self.base_url = base_url
        
    def diagnose_room(self, room_id: str) -> None:
        """Run complete diagnostics on a game room."""
        print(f"\n{'='*60}")
        print(f"GAME ROOM DIAGNOSTICS - Room: {room_id}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"{'='*60}\n")
        
        # Get room state
        state_data = self._get_room_state(room_id)
        if not state_data:
            return
            
        # Get event history
        events = self._get_room_events(room_id)
        if not events:
            return
            
        # Run diagnostics
        self._analyze_basic_state(state_data)
        self._analyze_turn_state(events)
        self._analyze_player_status(state_data, events)
        self._analyze_declarations(events)
        self._identify_issues(state_data, events)
        self._provide_recommendations(state_data, events)
        
    def _get_room_state(self, room_id: str) -> Optional[Dict]:
        """Fetch room state from API."""
        try:
            response = requests.get(f"{self.base_url}/api/rooms/{room_id}/state")
            if response.status_code != 200:
                print(f"❌ Failed to get room state: HTTP {response.status_code}")
                return None
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching room state: {e}")
            return None
            
    def _get_room_events(self, room_id: str) -> Optional[List[Dict]]:
        """Fetch room events from API."""
        try:
            response = requests.get(f"{self.base_url}/api/rooms/{room_id}/events")
            if response.status_code != 200:
                print(f"❌ Failed to get events: HTTP {response.status_code}")
                return None
            return response.json().get('events', [])
        except Exception as e:
            print(f"❌ Error fetching events: {e}")
            return None
            
    def _analyze_basic_state(self, state_data: Dict) -> None:
        """Analyze basic room state."""
        print("📊 BASIC STATE ANALYSIS")
        print("-" * 40)
        
        state = state_data.get('state', {})
        print(f"State Source: {state_data.get('state_source', 'unknown')}")
        print(f"Phase: {state.get('phase', 'UNKNOWN')}")
        print(f"Round Number: {state.get('round_number', 'N/A')}")
        print(f"Game Active: {state.get('game_active', False)}")
        print(f"Game Ended: {state.get('game_ended', False)}")
        
        if state_data.get('state_source') == 'reconstructed':
            print("\n⚠️  State is RECONSTRUCTED (not live)")
            
        print()
        
    def _analyze_turn_state(self, events: List[Dict]) -> None:
        """Analyze current turn state."""
        print("🎮 TURN STATE ANALYSIS")
        print("-" * 40)
        
        # Find latest turn phase data
        turn_data = None
        for event in reversed(events):
            if (event['event_type'] == 'phase_data_update' and 
                event['payload'].get('phase') == 'turn'):
                turn_data = event['payload'].get('updates', {})
                break
                
        if not turn_data:
            print("No turn data found")
            return
            
        print(f"Current Player: {turn_data.get('current_player', 'UNKNOWN')}")
        print(f"Turn Starter: {turn_data.get('current_turn_starter', 'UNKNOWN')}")
        print(f"Turn Number: {turn_data.get('current_turn_number', 0)}")
        print(f"Required Pieces: {turn_data.get('required_piece_count', 'Not set')}")
        print(f"Turn Complete: {turn_data.get('turn_complete', False)}")
        
        turn_order = turn_data.get('turn_order', [])
        if turn_order:
            print(f"\nTurn Order: {' → '.join(turn_order)}")
            
        # Find who has played this turn
        self._analyze_current_turn_plays(events, turn_order)
        print()
        
    def _analyze_current_turn_plays(self, events: List[Dict], turn_order: List[str]) -> None:
        """Analyze who has played in current turn."""
        print("\n🎯 Current Turn Plays:")
        
        # Find last turn start
        last_turn_start_idx = None
        for i, event in enumerate(reversed(events)):
            if (event['event_type'] == 'phase_data_update' and 
                'New turn' in event['payload'].get('reason', '')):
                last_turn_start_idx = len(events) - i - 1
                break
                
        if last_turn_start_idx is None:
            print("Could not find turn start")
            return
            
        # Collect plays since turn start
        plays = []
        for event in events[last_turn_start_idx:]:
            if (event['event_type'] == 'action_processed' and 
                event['payload'].get('action_type') == 'play_pieces'):
                player = event['payload'].get('player_name')
                pieces = event['payload'].get('payload', {}).get('pieces', [])
                if pieces:
                    piece_names = [p.get('kind', 'UNKNOWN') for p in pieces]
                    plays.append((player, piece_names))
                    
        # Display plays
        players_who_played = []
        for player, pieces in plays:
            print(f"  ✓ {player}: {', '.join(pieces)}")
            players_who_played.append(player)
            
        # Check who hasn't played
        if turn_order:
            waiting_for = [p for p in turn_order if p not in players_who_played]
            if waiting_for:
                print(f"\n⏳ Waiting for: {', '.join(waiting_for)}")
                
        print(f"\nTotal plays this turn: {len(plays)}/{len(turn_order)}")
        
    def _analyze_player_status(self, state_data: Dict, events: List[Dict]) -> None:
        """Analyze player status and hands."""
        print("👥 PLAYER STATUS")
        print("-" * 40)
        
        # Try to get player info from state
        state = state_data.get('state', {})
        players = state.get('players', [])
        
        if isinstance(players, dict):
            # Sometimes players is a dict
            print("Player data format: dict")
        elif isinstance(players, list) and players:
            # Normal player list
            for player in players:
                name = player.get('name', 'Unknown')
                hand_size = len(player.get('hand', []))
                print(f"{name}: {hand_size} pieces in hand")
        else:
            print("No player data available in state")
            
        print()
        
    def _analyze_declarations(self, events: List[Dict]) -> None:
        """Analyze player declarations."""
        print("📋 DECLARATIONS ANALYSIS")
        print("-" * 40)
        
        # Find most recent declarations
        declarations = {}
        for event in reversed(events):
            if (event['event_type'] == 'phase_data_update' and
                event['payload'].get('phase') == 'declaration'):
                decl_data = event['payload'].get('updates', {})
                declarations = decl_data.get('declarations', {})
                if declarations:
                    break
                    
        if not declarations:
            print("No declarations found")
            return
            
        print("Player Declarations:")
        for player, declared in declarations.items():
            print(f"  {player}: {declared} piles")
            if declared == 0:
                print(f"    → Must play weak pieces to avoid winning!")
                
        total = sum(declarations.values())
        print(f"\nTotal declared: {total}/8 piles")
        print()
        
    def _identify_issues(self, state_data: Dict, events: List[Dict]) -> None:
        """Identify potential issues."""
        print("🔍 ISSUE DETECTION")
        print("-" * 40)
        
        issues = []
        
        # Check state source
        if state_data.get('state_source') == 'reconstructed':
            issues.append("State is reconstructed (live game object unavailable)")
            
        # Check phase
        state = state_data.get('state', {})
        if state.get('phase') is None:
            issues.append("Phase is null (check state machine)")
            
        # Check game active
        if not state.get('game_active', False) and not state.get('game_ended', False):
            issues.append("Game marked inactive but not ended")
            
        # Check for stuck turn
        for event in reversed(events[-50:]):
            if (event['event_type'] == 'phase_data_update' and
                event['payload'].get('phase') == 'turn'):
                turn_data = event['payload'].get('updates', {})
                if (not turn_data.get('turn_complete', False) and
                    turn_data.get('current_turn_number', 0) > 0):
                    # Check if waiting for player
                    current = turn_data.get('current_player')
                    if current:
                        issues.append(f"Turn incomplete - check if waiting for {current}")
                break
                
        if issues:
            for issue in issues:
                print(f"⚠️  {issue}")
        else:
            print("✅ No obvious issues detected")
            
        print()
        
    def _provide_recommendations(self, state_data: Dict, events: List[Dict]) -> None:
        """Provide recommendations based on analysis."""
        print("💡 RECOMMENDATIONS")
        print("-" * 40)
        
        state = state_data.get('state', {})
        
        # Check if waiting for human
        for event in reversed(events[-20:]):
            if (event['event_type'] == 'phase_data_update' and
                'Waiting for' in str(event)):
                print("1. Game appears to be waiting for human player input")
                print("   → Check the game UI for the waiting player")
                break
                
        # Check if reconstructed
        if state_data.get('state_source') == 'reconstructed':
            print("2. State is reconstructed:")
            print("   → Check if game room still has active connections")
            print("   → May need to refresh or reconnect")
            
        # Check declarations
        has_zero_declaration = False
        for event in reversed(events):
            if event['event_type'] == 'phase_data_update':
                declarations = event['payload'].get('updates', {}).get('declarations', {})
                if any(d == 0 for d in declarations.values()):
                    has_zero_declaration = True
                    break
                    
        if has_zero_declaration:
            print("3. Player(s) declared 0:")
            print("   → Expect them to play weak pieces (this is correct!)")
            print("   → Not a bug if bots play SOLDIER pieces")
            
        print("\n📌 Quick Actions:")
        print("- Check game UI for waiting player")
        print("- Verify all players are connected")
        print("- Use WebSocket for game actions (not REST)")


def main():
    """Main entry point."""
    room_id = sys.argv[1] if len(sys.argv) > 1 else "1A8F34"
    
    diagnostics = GameRoomDiagnostics()
    diagnostics.diagnose_room(room_id)
    

if __name__ == "__main__":
    main()