#!/usr/bin/env python3
"""
Test script to verify the Play History API now shows all missing data
"""

import asyncio
import json
from backend.services.event_store_play_history_service import EventStorePlayHistoryService

async def test_missing_data():
    """Test that previously missing data is now populated"""
    
    service = EventStorePlayHistoryService()
    
    # Test room C5E645 which has 2 rounds
    room_id = "C5E645"
    print(f"🧪 Testing Play History for room {room_id}...\n")
    
    try:
        play_history = await service.build_play_history_from_events(
            room_id=room_id,
            include_ai_analysis=True,
            format=None
        )
        
        print(f"✅ Total Rounds: {play_history.total_rounds}")
        print(f"✅ Players: {list(play_history.players.keys())}")
        
        # Check Round 1
        if play_history.rounds:
            round1 = play_history.rounds[0]
            
            print(f"\n📋 Round 1 Analysis:")
            
            # Check player order
            print(f"  Player Order: {round1.initial_state.player_order}")
            if round1.initial_state.player_order:
                print("  ✅ Player order is populated!")
            else:
                print("  ❌ Player order is still empty")
            
            # Check declarations with declared counts
            print(f"\n  Declarations:")
            for decl in round1.declaration_phase.declarations:
                print(f"    {decl.player_id}: declared={decl.declared}")
            
            # Check turn history
            if round1.turn_history:
                turn1 = round1.turn_history[0]
                print(f"\n  Turn 1 Analysis:")
                
                # Check if winner is populated
                if turn1.winner:
                    print(f"    ✅ Winner: {turn1.winner.player_name} won {turn1.winner.pieces_captured} piles")
                else:
                    print(f"    ❌ Winner is still null")
                
                # Check next starter
                print(f"    Next Starter: {turn1.next_starter}")
                
                # Check game state after turn
                if turn1.game_state_after:
                    print(f"    ✅ Game State After Turn:")
                    for player, state in turn1.game_state_after.items():
                        print(f"      {player}: captured={state.captured}, declared={state.declared}, hand_size={state.hand_size}")
                else:
                    print(f"    ❌ Game state after turn is empty")
                
                # Check plays for declared counts
                print(f"\n    Player Plays:")
                for play in turn1.plays:
                    print(f"      {play.player_name}: declared_count={play.declared_count}, captured_count={play.captured_count}")
            
            # Check round summary
            print(f"\n  Round Summary:")
            if round1.round_summary.final_captures:
                print(f"    ✅ Final Captures:")
                for player, capture in round1.round_summary.final_captures.items():
                    print(f"      {player}: captured={capture.captured}, declared={capture.declared}, diff={capture.difference}")
            else:
                print(f"    ❌ Final captures is empty")
            
            if round1.round_summary.scoring:
                print(f"    ✅ Scoring:")
                for player, score in round1.round_summary.scoring.items():
                    print(f"      {player}: {score.points} points (multiplier={score.multiplier}, reason={score.reason})")
            else:
                print(f"    ❌ Scoring is empty")
        
        print("\n🎉 Test complete! Check which fields are now populated.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_missing_data())