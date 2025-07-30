#!/usr/bin/env python3
"""
Simple test to verify frontend-backend data connection
Tests the data format and flow between backend and frontend services
"""

import json
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_backend_data_format():
    """Test what data format the backend sends"""
    
    # Simulate a phase_change event from backend
    backend_event = {
        "event": "phase_change",
        "data": {
            "phase": "preparation",
            "allowed_actions": ["accept_redeal", "decline_redeal"],
            "phase_data": {
                "my_hand": [
                    {"name": "GENERAL_RED", "color": "red", "value": 14},
                    {"name": "SOLDIER_BLACK", "color": "black", "value": 1}
                ],
                "players": [
                    {"name": "Alice", "pile_count": 0, "zero_declares_in_a_row": 0},
                    {"name": "Bob", "pile_count": 0, "zero_declares_in_a_row": 1}
                ],
                "round_starter": "Alice",
                "redeal_multiplier": 1,
                "weak_hands": ["Bob"],
                "current_weak_player": "Bob"
            }
        }
    }
    
    print("✅ Backend Event Format:")
    print(json.dumps(backend_event, indent=2))
    print()
    
    # Check what additional fields the UI components expect
    expected_ui_fields = {
        "preparation": [
            "isMyDecision",
            "isMyHandWeak", 
            "handValue",
            "highestCardValue"
        ],
        "declaration": [
            "currentTotal",
            "declarationProgress", 
            "isLastPlayer",
            "estimatedPiles",
            "handStrength"
        ],
        "turn": [
            "canPlayAnyCount",
            "selectedPlayValue"
        ],
        "scoring": [
            "playersWithScores"
        ]
    }
    
    print("❌ Missing UI Fields (need to be calculated by backend):")
    for phase, fields in expected_ui_fields.items():
        print(f"  {phase}: {', '.join(fields)}")
    
    return True

def test_frontend_service_integration():
    """Test if frontend services can process backend data"""
    
    # This would test the GameService processing, but requires browser environment
    # For now, just validate the data structure
    
    print("📋 Frontend Service Requirements:")
    print("  - GameService.handlePhaseChange() must convert snake_case to camelCase")
    print("  - GameService must calculate missing UI fields")
    print("  - UI components should be purely presentational")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Frontend-Backend Data Connection\n")
    
    try:
        test_backend_data_format()
        print()
        test_frontend_service_integration()
        print("\n✅ Connection test completed - Issues identified")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)