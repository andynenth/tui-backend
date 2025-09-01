#!/usr/bin/env python3
"""
Debug script to systematically test WebSocket reconnection and state synchronization
"""
import asyncio
import json
import time
import websockets
from datetime import datetime

class WebSocketDebugger:
    def __init__(self, base_url="ws://localhost:5050/ws"):
        self.base_url = base_url
        self.room_id = None
        self.player_name = None
        self.websocket = None
        self.received_messages = []
        
    async def connect(self, room_id, player_name):
        """Connect to room and track messages"""
        self.room_id = room_id
        self.player_name = player_name
        url = f"{self.base_url}/{room_id}"
        
        print(f"\n🔌 [{datetime.now().isoformat()}] Connecting to {url}")
        self.websocket = await websockets.connect(url)
        
        # Start message receiver
        asyncio.create_task(self.receive_messages())
        
        # Send client_ready
        await self.send_message("client_ready", {
            "room_id": room_id,
            "player_name": player_name,
            "is_reconnection": False,
            "request_full_state": False
        })
        
        print(f"✅ Connected as {player_name}")
        
    async def receive_messages(self):
        """Receive and log all messages"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                timestamp = datetime.now().isoformat()
                
                self.received_messages.append({
                    "timestamp": timestamp,
                    "event": data.get("event"),
                    "data": data.get("data")
                })
                
                # Log key events
                event = data.get("event")
                if event in ["phase_change", "room_update", "game_started"]:
                    print(f"\n📥 [{timestamp}] {event}")
                    if event == "phase_change":
                        phase_data = data.get("data", {})
                        print(f"  Phase: {phase_data.get('phase')}")
                        print(f"  Round: {phase_data.get('round')}")
                        print(f"  Has players data: {bool(phase_data.get('players'))}")
                        if phase_data.get('players'):
                            for player, info in phase_data['players'].items():
                                print(f"    {player}: hand_size={info.get('hand_size', 0)}")
                                
        except websockets.exceptions.ConnectionClosed:
            print(f"\n❌ [{datetime.now().isoformat()}] Connection closed")
            
    async def send_message(self, event, data):
        """Send a message to the server"""
        message = {
            "event": event,
            "data": data
        }
        await self.websocket.send(json.dumps(message))
        print(f"\n📤 [{datetime.now().isoformat()}] Sent: {event}")
        
    async def disconnect(self):
        """Disconnect from server"""
        if self.websocket:
            await self.websocket.close()
            print(f"\n🔌 [{datetime.now().isoformat()}] Disconnected")
            
    async def reconnect(self):
        """Simulate reconnection"""
        print(f"\n🔄 [{datetime.now().isoformat()}] Simulating reconnection...")
        
        # Close existing connection
        if self.websocket:
            await self.websocket.close()
            
        # Clear old messages
        self.received_messages = []
        
        # Wait a bit
        await asyncio.sleep(2)
        
        # Reconnect with request_full_state
        url = f"{self.base_url}/{self.room_id}"
        print(f"🔌 [{datetime.now().isoformat()}] Reconnecting to {url}")
        self.websocket = await websockets.connect(url)
        
        # Start message receiver
        asyncio.create_task(self.receive_messages())
        
        # Send client_ready with reconnection flags
        await self.send_message("client_ready", {
            "room_id": self.room_id,
            "player_name": self.player_name,
            "is_reconnection": True,
            "request_full_state": True
        })
        
        print(f"✅ Reconnected as {self.player_name}")
        
    async def create_room(self):
        """Create a new room"""
        await self.send_message("create_room", {
            "player_name": self.player_name
        })
        
        # Wait for room_created event
        await asyncio.sleep(1)
        
        # Find room_id from messages
        for msg in reversed(self.received_messages):
            if msg["event"] == "room_created":
                room_id = msg["data"].get("room_id")
                print(f"  Found room_created event with room_id: {room_id}")
                return room_id
        print("  No room_created event found in messages")
        return None
        
    async def start_game(self):
        """Start the game"""
        await self.send_message("start_game", {})
        
    async def make_declaration(self, count):
        """Make a declaration"""
        await self.send_message("declare", {
            "declaration": count,
            "player_name": self.player_name
        })
        
    def print_message_summary(self):
        """Print summary of received messages"""
        print(f"\n📊 Message Summary ({len(self.received_messages)} messages):")
        event_counts = {}
        for msg in self.received_messages:
            event = msg["event"]
            event_counts[event] = event_counts.get(event, 0) + 1
            
        for event, count in sorted(event_counts.items()):
            print(f"  {event}: {count}")

async def main():
    """Run the debug test"""
    debugger = WebSocketDebugger()
    
    try:
        # Connect to lobby first
        await debugger.connect("lobby", "DebugPlayer")
        await asyncio.sleep(1)
        
        # Create a room
        room_id = await debugger.create_room()
        if not room_id:
            print("❌ Failed to create room")
            return
            
        print(f"\n🏠 Created room: {room_id}")
        
        # Disconnect from lobby and connect to room
        await debugger.disconnect()
        await asyncio.sleep(1)
        
        # Connect to the room
        await debugger.connect(room_id, "DebugPlayer")
        await asyncio.sleep(1)
        
        # Start the game
        print("\n🎮 Starting game...")
        await debugger.start_game()
        await asyncio.sleep(2)
        
        # Make a declaration if we're in declaration phase
        print("\n📢 Making declaration...")
        await debugger.make_declaration(2)
        await asyncio.sleep(2)
        
        # Print current state
        debugger.print_message_summary()
        
        # Now simulate disconnection and reconnection
        print("\n" + "="*50)
        print("SIMULATING DISCONNECTION/RECONNECTION")
        print("="*50)
        
        await debugger.reconnect()
        
        # Wait for messages
        await asyncio.sleep(3)
        
        # Print final state
        debugger.print_message_summary()
        
        # Check if we received phase_change with player data
        phase_changes = [msg for msg in debugger.received_messages if msg["event"] == "phase_change"]
        if phase_changes:
            last_phase = phase_changes[-1]
            phase_data = last_phase["data"]
            print(f"\n🔍 Last phase_change analysis:")
            print(f"  Phase: {phase_data.get('phase')}")
            print(f"  Has players data: {bool(phase_data.get('players'))}")
            print(f"  Has phase_data: {bool(phase_data.get('phase_data'))}")
            print(f"  All keys: {list(phase_data.keys())}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if debugger.websocket:
            await debugger.disconnect()

if __name__ == "__main__":
    asyncio.run(main())