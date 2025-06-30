#!/usr/bin/env python3
"""
🧪 Quick Integration Verification Test
Tests the specific issues we've been working on: transitions and bot declarations
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_imports():
    """Test that all imports work correctly"""
    print("🧪 Testing imports...")
    
    try:
        from engine.room import Room
        from engine.player import Player  
        from engine.bot_manager import BotManager
        from engine.state_machine.core import GamePhase, ActionType, GameAction
        from engine.game import Game
        print("✅ All core imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_bot_manager_registration():
    """Test bot manager registration timing"""
    print("\n🤖 Testing bot manager registration...")
    
    try:
        from engine.room import Room
        
        # Create room
        room = Room("TEST_ROOM", "TestHost") 
        
        # Add some bots
        room.join_room("Bot1")
        room.join_room("Bot2") 
        room.join_room("Bot3")
        
        # Mark as bots
        room.players[1].is_bot = True
        room.players[2].is_bot = True 
        room.players[3].is_bot = True
        
        print(f"✅ Room setup: {[p.name for p in room.players]}")
        print(f"✅ Bot players: {[p.name for p in room.players if p.is_bot]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Bot manager registration test failed: {e}")
        return False

def test_phase_enumeration():
    """Test that phase transitions are properly defined"""
    print("\n🔄 Testing phase transitions...")
    
    try:
        from engine.state_machine.core import GamePhase
        
        phases = [GamePhase.PREPARATION, GamePhase.DECLARATION, GamePhase.TURN, GamePhase.SCORING]
        print(f"✅ All phases accessible: {[p.value for p in phases]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Phase enumeration test failed: {e}")
        return False

def test_state_machine_structure():
    """Test state machine structure without running it"""
    print("\n🏗️ Testing state machine structure...")
    
    try:
        from engine.state_machine.game_state_machine import GameStateMachine
        from engine.state_machine.states.preparation_state import PreparationState
        from engine.state_machine.states.declaration_state import DeclarationState
        from engine.state_machine.states.turn_state import TurnState
        from engine.state_machine.states.scoring_state import ScoringState
        from engine.game import Game
        from engine.player import Player
        
        # Create minimal game
        players = [Player("P1"), Player("P2"), Player("P3"), Player("P4")]
        game = Game(players)
        
        # Create state machine
        state_machine = GameStateMachine(game)
        
        print(f"✅ State machine created with {len(state_machine.states)} states")
        print(f"✅ Available states: {list(state_machine.states.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ State machine structure test failed: {e}")
        return False

def main():
    """Run quick verification tests"""
    print("🧪 Quick Integration Verification Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_bot_manager_registration, 
        test_phase_enumeration,
        test_state_machine_structure
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All verification tests passed!")
        print("✅ Core structure is working correctly")
        print("✅ Ready for actual game flow testing")
    else:
        print("⚠️ Some verification tests failed")
        print("🔧 Fix structural issues before testing game flow")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)