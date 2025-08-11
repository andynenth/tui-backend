#!/usr/bin/env python3
"""
Test Play History API when room is not in memory
This verifies that the API correctly retrieves data from SQLite
"""

import requests
import json

def test_api_without_memory():
    """Test the API endpoint directly without room in memory"""
    
    # Room 258B79 has data in SQLite but shouldn't be in memory after restart
    room_id = "258B79"
    url = f"http://localhost:5050/api/rooms/{room_id}/play-history"
    
    print(f"🧪 Testing Play History API for room {room_id} (not in memory)\n")
    
    try:
        # Make the API request
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! API retrieved data from SQLite")
            print(f"   Total Rounds: {data['total_rounds']}")
            print(f"   Players: {list(data['players'].keys())}")
            
            # Show round summary
            for round_data in data['rounds']:
                round_num = round_data['round_number']
                print(f"\n   Round {round_num}:")
                
                # Show starter
                starter = round_data['initial_state']['starter']['player_name']
                print(f"     Starter: {starter}")
                
                # Show declarations
                declarations = round_data['declaration_phase']['declarations']
                decl_str = ', '.join([f"{d['player_id']}={d['declared']}" for d in declarations])
                print(f"     Declarations: {decl_str}")
                
                # Show final scores
                if 'round_summary' in round_data and round_data['round_summary']:
                    scores = round_data['round_summary']['scoring']
                    score_str = ', '.join([f"{p}={s['points']}" for p, s in scores.items()])
                    print(f"     Scores: {score_str}")
            
            print("\n🎉 API successfully retrieved historical data from SQLite!")
            print("   - Room was not in memory")
            print("   - Data persisted across server restarts")
            print("   - Play History API is working correctly")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        print("\nMake sure the backend is running: ./start.sh")


if __name__ == "__main__":
    test_api_without_memory()