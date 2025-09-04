#!/usr/bin/env python3
"""Test bot takeover data collection functionality"""
import asyncio
import json
import time
from websockets import connect

async def test_bot_takeover():
    room_id = "65E832"
    player_name = "TestPlayer"
    ws_url = f"ws://localhost:5050/ws/{room_id}"
    
    print(f"Testing bot takeover for room {room_id}...")
    
    # First, let's check current events
    import requests
    
    # Check connection timeline before test
    print("\n--- Connection Timeline Before Test ---")
    response = requests.get(f"http://localhost:5050/api/debug/connection-timeline/{room_id}")
    timeline = response.json()
    print(f"Total timeline events: {timeline['timeline_events']}")
    
    # Now test disconnection scenario
    print(f"\n--- Starting Disconnection Test ---")
    print(f"1. Connecting to WebSocket...")
    
    try:
        async with connect(ws_url) as websocket:
            # Send client ready
            await websocket.send(json.dumps({
                "type": "client_ready",
                "room_id": room_id,
                "player_name": player_name,
                "is_reconnection": False
            }))
            
            # Wait for response
            response = await websocket.recv()
            print(f"2. Received: {json.loads(response)['type']}")
            
            # Send declaration
            print(f"3. Sending declaration...")
            await websocket.send(json.dumps({
                "type": "action",
                "action": "declare",
                "value": 2
            }))
            
            await asyncio.sleep(1)
            
            print(f"4. Disconnecting...")
            # Disconnect will happen when we exit the context
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    
    print(f"5. Waiting 7 seconds for bot takeover to activate...")
    await asyncio.sleep(7)
    
    # Check events after disconnection
    print("\n--- Checking Events After Disconnection ---")
    
    # Get connection timeline
    response = requests.get(f"http://localhost:5050/api/debug/connection-timeline/{room_id}?player_name={player_name}")
    timeline = response.json()
    print(f"\nConnection Timeline Events: {timeline['timeline_events']}")
    
    if timeline['timeline']:
        print("\nRecent Events:")
        for event in timeline['timeline'][-5:]:
            print(f"- {event['event_type']} at {event['human_time']} for player {event['player']}")
    
    # Get bot control analysis
    response = requests.get(f"http://localhost:5050/api/debug/bot-control-analysis/{room_id}")
    analysis = response.json()
    print(f"\n--- Bot Control Analysis ---")
    print(f"Total disconnections: {analysis['summary']['total_disconnections']}")
    print(f"Total takeovers: {analysis['summary']['total_takeovers']}")
    print(f"Has issues: {analysis['has_issues']}")
    
    # Check for specific event types
    print("\n--- Checking Specific Events ---")
    event_types = ["player_disconnected", "bot_takeover_scheduled", "bot_takeover_activated"]
    for event_type in event_types:
        response = requests.get(f"http://localhost:5050/api/debug/events/{room_id}?event_type={event_type}")
        events = response.json()
        print(f"{event_type}: {events['total_events']} events")
        if events['events']:
            latest = events['events'][-1]
            print(f"  Latest: player_id={latest['player_id']}, payload={latest['payload']}")

if __name__ == "__main__":
    asyncio.run(test_bot_takeover())