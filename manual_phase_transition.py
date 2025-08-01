#!/usr/bin/env python3

"""
Manual Phase Transition Tool for Room 04CFOJ
Provides direct ways to force phase transitions and inspect game state
"""

import asyncio
import websockets
import json
import time
from typing import Optional, Dict, Any

class ManualPhaseController:
    """Manual control for game phase transitions"""
    
    def __init__(self, room_id: str = "04CFOJ", websocket_url: str = "ws://localhost:8000"):
        self.room_id = room_id
        self.websocket_url = f"{websocket_url}/ws/{room_id}"
        self.websocket = None
    
    async def connect(self):
        """Connect to WebSocket"""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            print(f"✅ Connected to {self.websocket_url}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            print("🔌 Disconnected")
    
    async def send_message(self, event: str, data: Dict[str, Any]):
        """Send a WebSocket message"""
        if not self.websocket:
            print("❌ Not connected")
            return False
        
        message = {
            "event": event,
            "data": data
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            print(f"📤 Sent: {event}")
            return True
        except Exception as e:
            print(f"❌ Failed to send: {e}")
            return False
    
    async def listen_for_responses(self, timeout: float = 5.0):
        """Listen for WebSocket responses"""
        if not self.websocket:
            return []
        
        responses = []
        end_time = time.time() + timeout
        
        try:
            while time.time() < end_time:
                try:
                    response = await asyncio.wait_for(
                        self.websocket.recv(), 
                        timeout=min(1.0, end_time - time.time())
                    )
                    data = json.loads(response)
                    responses.append(data)
                    print(f"📥 Received: {data.get('event', 'unknown')}")
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 Connection closed")
                    break
        except Exception as e:
            print(f"❌ Error listening: {e}")
        
        return responses
    
    async def force_redeal_decline_all(self):
        """Force decline redeal for all weak players"""
        print("🚫 Forcing redeal decline for all players...")
        
        # We'll send multiple decline messages for potential weak players
        for player_name in ["Player1", "Player2", "Player3", "Player4", "Bot1", "Bot2", "Bot3", "Bot4"]:
            await self.send_message("redeal_response", {
                "player_name": player_name,
                "accept": False
            })
            await asyncio.sleep(0.1)  # Small delay between messages
        
        # Listen for responses
        responses = await self.listen_for_responses(10.0)
        return responses
    
    async def force_redeal_accept(self, player_name: str = "Player1"):
        """Force accept redeal for a specific player"""
        print(f"♻️ Forcing redeal accept for {player_name}...")
        
        await self.send_message("redeal_request", {
            "player_name": player_name,
            "accept": True
        })
        
        responses = await self.listen_for_responses(10.0)
        return responses
    
    async def try_direct_phase_transition(self, target_phase: str = "DECLARATION"):
        """Attempt direct phase transition (may not work without proper handlers)"""
        print(f"🔄 Attempting direct transition to {target_phase}...")
        
        await self.send_message("force_phase_transition", {
            "target_phase": target_phase,
            "reason": "manual_debug"
        })
        
        responses = await self.listen_for_responses(5.0)
        return responses
    
    async def send_ping(self):
        """Send a ping to test connection"""
        print("🏓 Sending ping...")
        await self.send_message("ping", {"timestamp": time.time()})
        responses = await self.listen_for_responses(3.0)
        return responses
    
    async def request_game_state(self):
        """Request current game state"""
        print("📊 Requesting game state...")
        await self.send_message("get_game_state", {})
        responses = await self.listen_for_responses(5.0)
        return responses
    
    async def join_as_player(self, player_name: str = "DebugPlayer"):
        """Join room as a player"""
        print(f"👤 Joining as {player_name}...")
        await self.send_message("join_room", {
            "player_name": player_name
        })
        responses = await self.listen_for_responses(5.0)
        return responses

async def interactive_debug_session():
    """Interactive debugging session"""
    controller = ManualPhaseController()
    
    if not await controller.connect():
        return
    
    try:
        while True:
            print("\n🎮 MANUAL PHASE CONTROL")
            print("=" * 40)
            print("1. Send ping")
            print("2. Request game state")
            print("3. Join as debug player")
            print("4. Force decline all redeal")
            print("5. Force accept redeal (Player1)")
            print("6. Direct phase transition")
            print("7. Listen for messages (10s)")
            print("8. Exit")
            
            choice = input("\nSelect option (1-8): ").strip()
            
            if choice == "1":
                await controller.send_ping()
            
            elif choice == "2":
                await controller.request_game_state()
            
            elif choice == "3":
                player_name = input("Enter player name (default: DebugPlayer): ").strip() or "DebugPlayer"
                await controller.join_as_player(player_name)
            
            elif choice == "4":
                await controller.force_redeal_decline_all()
            
            elif choice == "5":
                player_name = input("Enter player name (default: Player1): ").strip() or "Player1"
                await controller.force_redeal_accept(player_name)
            
            elif choice == "6":
                phase = input("Enter target phase (default: DECLARATION): ").strip() or "DECLARATION"
                await controller.try_direct_phase_transition(phase)
            
            elif choice == "7":
                print("👂 Listening for messages...")
                responses = await controller.listen_for_responses(10.0)
                if responses:
                    print(f"Received {len(responses)} messages:")
                    for resp in responses:
                        print(f"  {json.dumps(resp, indent=2)}")
                else:
                    print("No messages received")
            
            elif choice == "8":
                break
            
            else:
                print("❌ Invalid choice")
    
    finally:
        await controller.disconnect()

async def automated_phase_fix():
    """Automated attempt to fix stuck PREPARATION phase"""
    print("🤖 AUTOMATED PHASE FIX")
    print("=" * 40)
    
    controller = ManualPhaseController()
    
    if not await controller.connect():
        return False
    
    try:
        # Step 1: Check current state
        print("1️⃣ Checking current game state...")
        await controller.request_game_state()
        await asyncio.sleep(2)
        
        # Step 2: Force decline all potential redeal decisions
        print("2️⃣ Force declining all redeal decisions...")
        await controller.force_redeal_decline_all()
        await asyncio.sleep(3)
        
        # Step 3: Listen for phase change
        print("3️⃣ Listening for phase change...")
        responses = await controller.listen_for_responses(10.0)
        
        # Check if phase changed
        phase_changed = False
        for response in responses:
            if response.get("event") == "phase_change":
                phase = response.get("data", {}).get("phase")
                if phase != "PREPARATION":
                    phase_changed = True
                    print(f"✅ Phase changed to: {phase}")
                    break
        
        if not phase_changed:
            print("4️⃣ Phase still stuck, trying direct transition...")
            await controller.try_direct_phase_transition("DECLARATION")
            await controller.listen_for_responses(5.0)
        
        return phase_changed
    
    finally:
        await controller.disconnect()

async def main():
    """Main function"""
    print("🛠️ MANUAL PHASE TRANSITION TOOL")
    print("=" * 50)
    print("This tool helps debug and fix stuck game phases")
    print()
    
    mode = input("Select mode:\n1. Interactive session\n2. Automated fix\n3. Quick ping test\nChoice (1-3): ").strip()
    
    if mode == "1":
        await interactive_debug_session()
    
    elif mode == "2":
        success = await automated_phase_fix()
        if success:
            print("✅ Phase transition appears successful!")
        else:
            print("❌ Phase may still be stuck - try interactive mode")
    
    elif mode == "3":
        controller = ManualPhaseController()
        if await controller.connect():
            await controller.send_ping()
            await controller.disconnect()
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    asyncio.run(main())