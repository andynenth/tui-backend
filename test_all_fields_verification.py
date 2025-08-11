#!/usr/bin/env python3
"""
Comprehensive test to verify ALL fields in Play History API
"""

import requests
import json

def check_field(field_name, value, expected_type=None, should_not_be_empty=True):
    """Helper to check if a field is properly populated"""
    if value is None:
        print(f"  ❌ {field_name}: null")
        return False
    elif isinstance(value, (list, dict, str)) and len(value) == 0 and should_not_be_empty:
        print(f"  ❌ {field_name}: empty {type(value).__name__}")
        return False
    elif expected_type and not isinstance(value, expected_type):
        print(f"  ❌ {field_name}: wrong type (expected {expected_type}, got {type(value)})")
        return False
    else:
        if isinstance(value, dict):
            print(f"  ✅ {field_name}: {len(value)} items")
        elif isinstance(value, list):
            print(f"  ✅ {field_name}: {len(value)} items") 
        else:
            print(f"  ✅ {field_name}: {value}")
        return True

def test_all_fields():
    """Test all fields in Play History API"""
    
    room_id = "C5E645"
    url = f"http://localhost:5050/api/rooms/{room_id}/play-history"
    
    print(f"🧪 Testing ALL fields for room {room_id}...\n")
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            return
            
        data = response.json()
        
        # Check top level
        print("📋 Top Level:")
        check_field("room_id", data.get("room_id"))
        check_field("total_rounds", data.get("total_rounds"))
        check_field("players", data.get("players"), dict)
        
        if not data.get("rounds"):
            print("\n❌ No rounds found!")
            return
            
        # Check Round 1
        round1 = data["rounds"][0]
        print("\n📋 Round 1 - Initial State:")
        check_field("starter", round1["initial_state"].get("starter"), dict)
        check_field("player_order", round1["initial_state"].get("player_order"), list)
        
        print("\n📋 Round 1 - Hands Dealt:")
        check_field("hands_dealt", round1.get("hands_dealt"), dict, should_not_be_empty=False)  # This might be empty for old games
        
        print("\n📋 Round 1 - Declaration Phase:")
        check_field("declarations", round1["declaration_phase"].get("declarations"), list)
        check_field("total_declared", round1["declaration_phase"].get("total_declared"))
        check_field("pile_room_calculation", round1["declaration_phase"].get("pile_room_calculation"), dict)
        
        # Check Turn 1
        if round1.get("turn_history") and len(round1["turn_history"]) > 0:
            turn1 = round1["turn_history"][0]
            print("\n📋 Round 1 - Turn 1:")
            check_field("turn_number", turn1.get("turn_number"))
            check_field("winner", turn1.get("winner"), dict, should_not_be_empty=False)  # Can be null
            check_field("next_starter", turn1.get("next_starter"), str)
            check_field("game_state_after", turn1.get("game_state_after"), dict)
            
            # Check first play
            if turn1.get("plays") and len(turn1["plays"]) > 0:
                play1 = turn1["plays"][0]
                print(f"\n📋 Round 1 - Turn 1 - First Play ({play1.get('player_name')}):")
                check_field("pieces_played", play1.get("pieces_played"), list)
                check_field("play_type", play1.get("play_type"))
                check_field("hand_before", play1.get("hand_before"), list, should_not_be_empty=False)
                check_field("hand_after", play1.get("hand_after"), list, should_not_be_empty=False)
                
                # Check the critical fields that are always 0
                captured = play1.get("captured_count", -1)
                declared = play1.get("declared_count", -1)
                print(f"\n  🔍 captured_count: {captured} (should not always be 0)")
                print(f"  🔍 declared_count: {declared} (should match declaration)")
                
                # Check all plays for these values
                print("\n📋 All plays captured/declared counts:")
                for i, play in enumerate(turn1["plays"]):
                    print(f"  Play {i+1} - {play['player_name']}: captured={play.get('captured_count')}, declared={play.get('declared_count')}")
        
        # Check Round Summary
        print("\n📋 Round 1 - Summary:")
        summary = round1.get("round_summary", {})
        check_field("total_turns", summary.get("total_turns"))
        check_field("final_captures", summary.get("final_captures"), dict)
        check_field("scoring", summary.get("scoring"), dict)
        check_field("cumulative_scores", summary.get("cumulative_scores"), dict)
        
        # Show actual values for debugging
        if summary.get("final_captures"):
            print("\n  Final Captures Details:")
            for player, capture in summary["final_captures"].items():
                print(f"    {player}: captured={capture['captured']}, declared={capture['declared']}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_all_fields()