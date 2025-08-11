#!/usr/bin/env python3
"""
Test the Event Store Play History Integration
"""

import asyncio
import json
from backend.services.event_store_play_history_service import EventStorePlayHistoryService


async def test_event_store_integration():
    """Test extracting play history from event store"""
    
    service = EventStorePlayHistoryService()
    
    # Test with room 258B79
    room_id = "258B79"
    print(f"Testing play history extraction for room {room_id}...")
    
    try:
        # Get full play history
        play_history = await service.build_play_history_from_events(
            room_id=room_id,
            include_ai_analysis=True,
            format=None
        )
        
        print(f"\n✅ Successfully extracted play history!")
        print(f"Room ID: {play_history.room_id}")
        print(f"Total Rounds: {play_history.total_rounds}")
        print(f"Players: {list(play_history.players.keys())}")
        
        # Show details for each round
        for round_data in play_history.rounds:
            print(f"\n📍 Round {round_data.round_number}:")
            print(f"  Starter: {round_data.initial_state.starter.player_name} ({round_data.initial_state.starter.reason})")
            
            # Show hands dealt
            if round_data.hands_dealt:
                print(f"  Hands Dealt: {len(round_data.hands_dealt)} players")
                for player, hand in round_data.hands_dealt.items():
                    print(f"    {player}: {len(hand)} pieces")
            
            # Show declarations
            if round_data.declaration_phase:
                print(f"  Declarations:")
                for decl in round_data.declaration_phase.declarations:
                    print(f"    {decl.player_id}: {decl.declared}")
            
            # Show turn summary
            print(f"  Turns Played: {len(round_data.turn_history)}")
            
            # Show final scores
            if round_data.round_summary:
                print(f"  Final Captures:")
                for player, capture in round_data.round_summary.final_captures.items():
                    print(f"    {player}: {capture.captured}/{capture.declared} (diff: {capture.difference})")
                print(f"  Scores:")
                for player, score in round_data.round_summary.scoring.items():
                    print(f"    {player}: {score.points} points ({score.reason})")
        
        # Test compact format
        print("\n\nTesting compact format...")
        compact_history = await service.build_play_history_from_events(
            room_id=room_id,
            include_ai_analysis=False,
            format="compact"
        )
        
        print(f"✅ Compact format works! Rounds: {compact_history.total_rounds}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_event_store_integration())