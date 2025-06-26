#!/usr/bin/env python3
"""
Deep test to find any Player objects hiding in phase data structures
"""
import asyncio
import json
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GamePhase, ActionType, GameAction
from engine.game import Game
from engine.player import Player

def deep_inspect_for_objects(obj, path="root"):
    """Recursively inspect object for non-serializable items"""
    issues = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}"
            if hasattr(value, '__dict__') and not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                issues.append(f"Non-serializable object at {current_path}: {type(value)} - {value}")
            else:
                issues.extend(deep_inspect_for_objects(value, current_path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            current_path = f"{path}[{i}]"
            if hasattr(item, '__dict__') and not isinstance(item, (str, int, float, bool, list, dict, type(None))):
                issues.append(f"Non-serializable object at {current_path}: {type(item)} - {item}")
            else:
                issues.extend(deep_inspect_for_objects(item, current_path))
    elif hasattr(obj, '__dict__') and not isinstance(obj, (str, int, float, bool, list, dict, type(None))):
        issues.append(f"Non-serializable object at {path}: {type(obj)} - {obj}")
    
    return issues

async def test_deep_phase_data_inspection():
    """Deep inspection of all phase data structures"""
    print("🔍 Deep inspection for Player objects in phase data...")
    
    # Create test players
    players = [Player(f'Player {i+1}', is_bot=(i>0)) for i in range(4)]
    
    # Create test game
    game = Game(players)
    
    # Track issues
    all_issues = []
    
    async def inspect_broadcast(event_type, event_data):
        print(f"\n📡 Inspecting broadcast: {event_type}")
        
        # Deep inspect the event data
        issues = deep_inspect_for_objects(event_data, f"{event_type}_data")
        if issues:
            print(f"❌ Found {len(issues)} serialization issues in {event_type}:")
            for issue in issues:
                print(f"   {issue}")
            all_issues.extend(issues)
        else:
            print(f"✅ No serialization issues found in {event_type}")
        
        # Try actual JSON serialization
        try:
            json_str = json.dumps(event_data)
            print(f"✅ JSON serialization successful for {event_type}")
        except TypeError as e:
            print(f"❌ JSON serialization failed for {event_type}: {e}")
            all_issues.append(f"JSON serialization failed for {event_type}: {e}")
    
    # Create state machine with inspection callback
    state_machine = GameStateMachine(game, inspect_broadcast)
    
    # Start and let it go through phases
    await state_machine.start(GamePhase.PREPARATION)
    await asyncio.sleep(0.2)
    
    # Force transition to DECLARATION
    print(f"\n🔄 Current phase: {state_machine.current_phase}")
    
    # Check phase data directly
    print(f"\n🔍 Direct inspection of phase data:")
    phase_data = state_machine.get_phase_data()
    direct_issues = deep_inspect_for_objects(phase_data, "phase_data")
    if direct_issues:
        print(f"❌ Found {len(direct_issues)} issues in direct phase data:")
        for issue in direct_issues:
            print(f"   {issue}")
        all_issues.extend(direct_issues)
    else:
        print(f"✅ No issues in direct phase data")
    
    # Check raw phase data (before serialization)
    print(f"\n🔍 Raw phase data inspection:")
    if state_machine.current_state:
        raw_data = state_machine.current_state.phase_data
        raw_issues = deep_inspect_for_objects(raw_data, "raw_phase_data")
        if raw_issues:
            print(f"❌ Found {len(raw_issues)} issues in raw phase data:")
            for issue in raw_issues:
                print(f"   {issue}")
            all_issues.extend(raw_issues)
        else:
            print(f"✅ No issues in raw phase data")
    
    # Add declarations to force TURN transition
    if state_machine.current_phase == GamePhase.DECLARATION:
        print(f"\n📢 Adding declarations to trigger TURN transition...")
        # Properly add declarations
        current_state = state_machine.current_state
        for i, player in enumerate(players):
            # Set player as current declarer for validation
            current_state.phase_data['current_declarer_index'] = i
            current_state.phase_data['current_declarer'] = player.name
            
            action = GameAction(
                player_name=player.name,
                action_type=ActionType.DECLARE,
                payload={"value": 2}
            )
            result = await state_machine.handle_action(action)
            print(f"   Declaration result for {player.name}: {result}")
            await asyncio.sleep(0.1)
    
    # Wait for transitions
    await asyncio.sleep(0.5)
    
    print(f"\n🔄 Final phase: {state_machine.current_phase}")
    
    # Final inspection
    if all_issues:
        print(f"\n❌ TOTAL ISSUES FOUND: {len(all_issues)}")
        for issue in all_issues:
            print(f"   {issue}")
    else:
        print(f"\n✅ NO SERIALIZATION ISSUES FOUND!")
    
    # Stop the state machine
    await state_machine.stop()
    
    return len(all_issues) == 0

if __name__ == "__main__":
    try:
        success = asyncio.run(test_deep_phase_data_inspection())
        if success:
            print("\n🎉 Deep inspection PASSED - no Player objects found in phase data")
        else:
            print("\n💥 Deep inspection FAILED - Player objects found!")
            exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)