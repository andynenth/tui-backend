#!/usr/bin/env python3
"""Test bot takeover data collection after fixing payload storage"""
import asyncio
import json
import random
import string
import time
from websockets import connect

async def test_bot_takeover_with_payload():
    # Generate a new room ID
    room_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    player_name = "TestPlayer"
    ws_url = f"ws://localhost:5050/ws/lobby"
    
    print(f"🧪 Testing bot takeover with payload storage fix...")
    print(f"📍 Creating new room: {room_id}")
    
    # First create a room
    try:
        async with connect(ws_url) as websocket:
            # Send create room request
            await websocket.send(json.dumps({
                "type": "create_room",
                "player_name": player_name
            }))
            
            # Wait for room created response
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                if data.get("type") == "room_created":
                    actual_room_id = data.get("room_id")
                    print(f"✅ Room created: {actual_room_id}")
                    room_id = actual_room_id
                    break
    except Exception as e:
        print(f"❌ Error creating room: {e}")
        return
    
    # Now connect to the room
    room_ws_url = f"ws://localhost:5050/ws/{room_id}"
    print(f"\n📍 Connecting to room {room_id}...")
    
    try:
        async with connect(room_ws_url) as websocket:
            # Send client ready
            await websocket.send(json.dumps({
                "type": "client_ready",
                "room_id": room_id,
                "player_name": player_name,
                "is_reconnection": False
            }))
            
            # Wait for initial state
            await asyncio.sleep(1)
            
            # Start the game
            print(f"🎮 Starting game...")
            await websocket.send(json.dumps({
                "type": "start_game"
            }))
            
            await asyncio.sleep(2)
            
            print(f"🔌 Disconnecting to trigger bot takeover...")
            # Disconnect will happen when we exit the context
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    
    print(f"⏳ Waiting 7 seconds for bot takeover to activate...")
    await asyncio.sleep(7)
    
    # Check events after disconnection
    print("\n🔍 Checking Events After Disconnection")
    print("=" * 50)
    
    import requests
    
    # Get specific events
    event_types = ["player_disconnected", "bot_takeover_scheduled", "bot_takeover_activated", "bot_action"]
    for event_type in event_types:
        response = requests.get(f"http://localhost:5050/api/debug/events/{room_id}?event_type={event_type}")
        events = response.json()
        print(f"\n📋 {event_type}: {events['total_events']} events")
        
        if events['events']:
            for i, event in enumerate(events['events']):
                print(f"\n  Event {i+1}:")
                print(f"    player_id: {event['player_id']}")
                print(f"    timestamp: {event['timestamp']}")
                
                # Check if payload has data now
                payload = event['payload']
                if payload and len(payload) > 1:  # More than just round_number
                    print(f"    ✅ Payload has data: {len(payload)} keys")
                    for key in sorted(payload.keys())[:5]:  # Show first 5 keys
                        value = payload[key]
                        if isinstance(value, dict):
                            print(f"      - {key}: <dict with {len(value)} keys>")
                        elif isinstance(value, str) and len(value) > 50:
                            print(f"      - {key}: {value[:50]}...")
                        else:
                            print(f"      - {key}: {value}")
                else:
                    print(f"    ❌ Payload empty or minimal")
    
    # Get connection timeline
    print(f"\n\n📊 Connection Timeline Analysis")
    print("=" * 50)
    response = requests.get(f"http://localhost:5050/api/debug/connection-timeline/{room_id}?player_name={player_name}")
    timeline = response.json()
    print(f"Timeline events: {timeline['timeline_events']}")
    
    if timeline['timeline']:
        print("\nRecent Timeline:")
        for event in timeline['timeline'][-5:]:
            player_info = f" [{event['player']}]" if event['player'] != 'null' else ""
            print(f"  {event['human_time']} - {event['event_type']}{player_info}")
    
    # Get bot control analysis
    print(f"\n\n🤖 Bot Control Analysis")
    print("=" * 50)
    response = requests.get(f"http://localhost:5050/api/debug/bot-control-analysis/{room_id}")
    analysis = response.json()
    print(f"Summary:")
    print(f"  - Total players analyzed: {analysis['summary']['total_players']}")
    print(f"  - Total disconnections: {analysis['summary']['total_disconnections']}")
    print(f"  - Total takeovers: {analysis['summary']['total_takeovers']}")
    print(f"  - Issues detected: {analysis['has_issues']}")
    
    # Check player-specific analysis
    if analysis['player_analysis']:
        print(f"\nPlayer Analysis:")
        for player, stats in analysis['player_analysis'].items():
            if player and player != 'null':
                print(f"  Player {player}:")
                print(f"    - Disconnects: {stats['total_disconnects']}")
                print(f"    - Bot takeovers: {stats['total_takeovers']}")
                print(f"    - Bot actions: {stats['bot_actions']}")

if __name__ == "__main__":
    asyncio.run(test_bot_takeover_with_payload())