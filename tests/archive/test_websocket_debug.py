#!/usr/bin/env python3

"""
Debug WebSocket data flow for simultaneous mode
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket_connection():
    """Test WebSocket connection and data flow"""
    
    print("🔌 Testing WebSocket connection...")
    
    # Connect to the WebSocket endpoint
    try:
        uri = "ws://localhost:8000/ws/2C2507"
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {uri}")
            
            # Send client_ready message
            client_ready = {
                "event": "client_ready",
                "data": {"room_id": "2C2507"}
            }
            await websocket.send(json.dumps(client_ready))
            print("📤 Sent client_ready message")
            
            # Listen for messages
            print("👂 Listening for messages...")
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    print(f"\n📥 Received message at {datetime.now().strftime('%H:%M:%S')}:")
                    print(f"   Event: {data.get('event', 'unknown')}")
                    
                    if data.get('event') == 'phase_change':
                        phase_data = data.get('data', {}).get('phase_data', {})
                        print(f"   Phase: {data.get('data', {}).get('phase', 'unknown')}")
                        print(f"   Simultaneous mode: {phase_data.get('simultaneous_mode', False)}")
                        print(f"   Weak players: {phase_data.get('weak_players', [])}")
                        print(f"   Weak players awaiting: {phase_data.get('weak_players_awaiting', [])}")
                        print(f"   Decisions received: {phase_data.get('decisions_received', 0)}")
                        print(f"   Decisions needed: {phase_data.get('decisions_needed', 0)}")
                        
                        # This is what we're looking for!
                        if phase_data.get('simultaneous_mode'):
                            print("✅ Found simultaneous mode data!")
                            return True
                    
            except asyncio.TimeoutError:
                print("⏱️ No more messages received (timeout)")
                return False
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket_connection())
    if result:
        print("\n🎉 WebSocket data flow test PASSED")
    else:
        print("\n❌ WebSocket data flow test FAILED")