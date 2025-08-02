#!/usr/bin/env python3
"""
Comprehensive test script for all room management operations.
Tests both lobby and room functionality with AsyncRoomManager.
"""

import asyncio
import websockets
import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared_instances import shared_room_manager

BASE_URL = "ws://127.0.0.1:5050"


class RoomOperationTester:
    def __init__(self):
        self.results = []
        self.room_id = None
        
    def log_result(self, operation: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅" if success else "❌"
        self.results.append({
            "operation": operation,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{status} {operation}: {details}")
    
    async def test_lobby_connection(self):
        """Test 1: Connect to lobby"""
        try:
            async with websockets.connect(f"{BASE_URL}/ws/lobby") as websocket:
                # Send client ready
                await websocket.send(json.dumps({
                    "event": "client_ready",
                    "data": {"player_name": "TestPlayer"}
                }))
                
                response = await websocket.recv()
                data = json.loads(response)
                
                if data.get("event") == "room_list_update":
                    self.log_result("Lobby Connection", True, "Connected and received room list")
                else:
                    self.log_result("Lobby Connection", False, f"Unexpected response: {data.get('event')}")
                    
        except Exception as e:
            self.log_result("Lobby Connection", False, str(e))
    
    async def test_room_creation(self):
        """Test 2: Create a new room"""
        try:
            async with websockets.connect(f"{BASE_URL}/ws/lobby") as websocket:
                # Send client ready
                await websocket.send(json.dumps({
                    "event": "client_ready",
                    "data": {"player_name": "Host"}
                }))
                
                await websocket.recv()  # Ignore initial response
                
                # Create room
                await websocket.send(json.dumps({
                    "event": "create_room",
                    "data": {"player_name": "Host"}
                }))
                
                response = await websocket.recv()
                data = json.loads(response)
                
                if data.get("event") == "room_created":
                    self.room_id = data["data"]["room_id"]
                    self.log_result("Room Creation", True, f"Created room {self.room_id}")
                    
                    # Verify room exists in manager
                    room = await shared_room_manager.get_room(self.room_id)
                    if room:
                        self.log_result("Room Verification", True, "Room exists in AsyncRoomManager")
                    else:
                        self.log_result("Room Verification", False, "Room not found in manager")
                else:
                    self.log_result("Room Creation", False, f"Unexpected response: {data}")
                    
        except Exception as e:
            self.log_result("Room Creation", False, str(e))
    
    async def test_room_join(self):
        """Test 3: Join the created room"""
        if not self.room_id:
            self.log_result("Room Join", False, "No room created to join")
            return
            
        try:
            async with websockets.connect(f"{BASE_URL}/ws/lobby") as websocket:
                # Send client ready
                await websocket.send(json.dumps({
                    "event": "client_ready",
                    "data": {"player_name": "Player2"}
                }))
                
                await websocket.recv()  # Ignore initial response
                
                # Join room
                await websocket.send(json.dumps({
                    "event": "join_room",
                    "data": {"room_id": self.room_id, "player_name": "Player2"}
                }))
                
                response = await websocket.recv()
                data = json.loads(response)
                
                if data.get("event") == "room_joined":
                    self.log_result("Room Join", True, f"Player2 joined room {self.room_id}")
                else:
                    self.log_result("Room Join", False, f"Join failed: {data}")
                    
        except Exception as e:
            self.log_result("Room Join", False, str(e))
    
    async def test_bot_operations(self):
        """Test 4: Add and remove bots"""
        if not self.room_id:
            self.log_result("Bot Operations", False, "No room created")
            return
            
        try:
            async with websockets.connect(f"{BASE_URL}/ws/{self.room_id}") as websocket:
                # Send client ready as host
                await websocket.send(json.dumps({
                    "event": "client_ready",
                    "data": {"player_name": "Host"}
                }))
                
                await websocket.recv()  # Ignore initial response
                
                # Add bot to slot 3
                await websocket.send(json.dumps({
                    "event": "add_bot",
                    "data": {"slot_id": "3"}
                }))
                
                # Wait for response
                await asyncio.sleep(0.5)
                
                # Remove player from slot 3
                await websocket.send(json.dumps({
                    "event": "remove_player",
                    "data": {"slot_id": "3"}
                }))
                
                # Check room state
                room = await shared_room_manager.get_room(self.room_id)
                if room:
                    self.log_result("Bot Operations", True, 
                                  f"Bot operations completed, {room.get_occupied_slots()} players in room")
                else:
                    self.log_result("Bot Operations", False, "Room not found after bot operations")
                    
        except Exception as e:
            self.log_result("Bot Operations", False, str(e))
    
    async def test_game_start(self):
        """Test 5: Start the game"""
        if not self.room_id:
            self.log_result("Game Start", False, "No room created")
            return
            
        try:
            # First, fill the room with bots
            async with websockets.connect(f"{BASE_URL}/ws/{self.room_id}") as websocket:
                # Send client ready as host
                await websocket.send(json.dumps({
                    "event": "client_ready",
                    "data": {"player_name": "Host"}
                }))
                
                await websocket.recv()  # Ignore initial response
                
                # Add bots to fill remaining slots
                for slot in [3, 4]:  # Assuming Host is slot 1, Player2 is slot 2
                    await websocket.send(json.dumps({
                        "event": "add_bot",
                        "data": {"slot_id": str(slot)}
                    }))
                    await asyncio.sleep(0.2)
                
                # Start game
                await websocket.send(json.dumps({
                    "event": "start_game",
                    "data": {}
                }))
                
                # Wait for game started event
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(response)
                
                if data.get("event") == "game_started":
                    self.log_result("Game Start", True, "Game started successfully")
                else:
                    self.log_result("Game Start", False, f"Unexpected response: {data.get('event')}")
                    
        except asyncio.TimeoutError:
            self.log_result("Game Start", False, "Timeout waiting for game start")
        except Exception as e:
            self.log_result("Game Start", False, str(e))
    
    async def test_room_state_methods(self):
        """Test 6: Test AsyncRoom methods"""
        if not self.room_id:
            self.log_result("Room Methods", False, "No room created")
            return
            
        try:
            room = await shared_room_manager.get_room(self.room_id)
            if not room:
                self.log_result("Room Methods", False, "Room not found")
                return
            
            # Test validate_state
            validation = room.validate_state()
            self.log_result("validate_state()", validation["valid"], 
                          f"Errors: {validation['errors']}, Warnings: {validation['warnings']}")
            
            # Test slots property
            slots_count = len([s for s in room.slots if s is not None])
            self.log_result("slots property", True, f"{slots_count} slots occupied")
            
            # Test summary
            summary = await room.summary()
            self.log_result("summary()", True, 
                          f"Room {summary['room_id']}, Host: {summary['host_name']}")
            
            # Test is_full
            is_full = room.is_full()
            self.log_result("is_full()", True, f"Room full: {is_full}")
            
        except Exception as e:
            self.log_result("Room Methods", False, str(e))
    
    async def test_cleanup(self):
        """Test 7: Leave room and verify cleanup"""
        if not self.room_id:
            self.log_result("Room Cleanup", False, "No room created")
            return
            
        try:
            # Host leaves room
            async with websockets.connect(f"{BASE_URL}/ws/{self.room_id}") as websocket:
                await websocket.send(json.dumps({
                    "event": "client_ready",
                    "data": {"player_name": "Host"}
                }))
                
                await websocket.recv()
                
                # Leave room
                await websocket.send(json.dumps({
                    "event": "leave_room",
                    "data": {}
                }))
            
            # Wait a bit
            await asyncio.sleep(0.5)
            
            # Check if room was deleted
            room = await shared_room_manager.get_room(self.room_id)
            if room is None:
                self.log_result("Room Cleanup", True, "Room deleted when host left")
            else:
                self.log_result("Room Cleanup", False, "Room still exists after host left")
                
        except Exception as e:
            self.log_result("Room Cleanup", False, str(e))
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['operation']}: {result['details']}")


async def main():
    """Run all tests"""
    print("🧪 Comprehensive Room Operations Test")
    print("="*60)
    
    tester = RoomOperationTester()
    
    # Run tests in sequence
    await tester.test_lobby_connection()
    await tester.test_room_creation()
    await tester.test_room_join()
    await tester.test_bot_operations()
    await tester.test_game_start()
    await tester.test_room_state_methods()
    await tester.test_cleanup()
    
    # Print summary
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())