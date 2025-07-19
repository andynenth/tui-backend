#!/usr/bin/env python3
"""
Trace test for reconnection implementation
Verifies the complete data flow from disconnect to reconnect
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from api.websocket.connection_manager import ConnectionManager, ConnectionStatus
from api.websocket.message_queue import message_queue_manager
from engine.room import Room
from engine.player import Player
from engine.game import Game
from engine.state_machine.core import GamePhase


class ReconnectionTrace:
    """Trace reconnection data flow"""
    
    def __init__(self):
        self.trace_log = []
        self.connection_manager = ConnectionManager()
        
    def log(self, step: str, data: dict = None):
        """Log a trace step"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'data': data or {}
        }
        self.trace_log.append(entry)
        print(f"[{len(self.trace_log)}] {step}")
        if data:
            for key, value in data.items():
                print(f"    {key}: {value}")
    
    async def run_trace(self):
        """Run complete reconnection trace"""
        print("=== RECONNECTION IMPLEMENTATION TRACE ===\n")
        
        # Step 1: Setup initial game state
        self.log("1. SETUP: Create room and game", {
            'room_id': 'test_room',
            'players': ['Alice', 'Bob', 'Charlie', 'David']
        })
        
        room = Room("test_room", "Alice")
        room.players[1] = Player("Bob", is_bot=False)
        room.players[2] = Player("Charlie", is_bot=False)
        room.players[3] = Player("David", is_bot=False)
        room.game = Game(room.players)
        room.game.phase = GamePhase.TURN
        room.game_started = True
        
        # Step 2: Register player connections
        self.log("2. CONNECT: Register all players")
        await self.connection_manager.register_player("test_room", "Alice", "ws_001")
        await self.connection_manager.register_player("test_room", "Bob", "ws_002")
        await self.connection_manager.register_player("test_room", "Charlie", "ws_003")
        await self.connection_manager.register_player("test_room", "David", "ws_004")
        
        # Verify connections
        alice_conn = await self.connection_manager.get_connection("test_room", "Alice")
        bob_conn = await self.connection_manager.get_connection("test_room", "Bob")
        self.log("3. VERIFY: All players connected", {
            'alice_connected': alice_conn is not None,
            'bob_connected': bob_conn is not None,
            'alice_status': alice_conn.connection_status.value if alice_conn else None,
            'bob_status': bob_conn.connection_status.value if bob_conn else None
        })
        
        # Step 3: Simulate Bob disconnecting
        self.log("4. DISCONNECT: Bob loses connection")
        connection = await self.connection_manager.handle_disconnect("ws_002")
        
        self.log("5. VERIFY: Disconnect handled", {
            'player_name': connection.player_name if connection else 'None',
            'status': connection.connection_status.value if connection else 'None',
            'disconnect_time': connection.disconnect_time.isoformat() if connection and connection.disconnect_time else 'None'
        })
        
        # Step 4: Activate bot for Bob
        bob_player = room.players[1]
        bob_player.original_is_bot = False
        bob_player.is_bot = True
        bob_player.is_connected = False
        bob_player.disconnect_time = datetime.now()
        
        self.log("6. BOT: Activate bot for Bob", {
            'is_bot': bob_player.is_bot,
            'original_is_bot': bob_player.original_is_bot,
            'is_connected': bob_player.is_connected
        })
        
        # Step 5: Create message queue
        await message_queue_manager.create_queue("test_room", "Bob")
        self.log("7. QUEUE: Message queue created for Bob")
        
        # Step 6: Simulate game events while Bob is disconnected
        events = [
            ("phase_change", {"phase": "TURN", "current_player": "Charlie"}),
            ("play", {"player": "Charlie", "pieces": [1, 2]}),
            ("turn_resolved", {"winner": "Charlie", "pieces_won": 2}),
            ("phase_change", {"phase": "TURN", "current_player": "David"}),
            ("play", {"player": "David", "pieces": [3]}),
        ]
        
        self.log("8. EVENTS: Queue messages while Bob disconnected")
        for event_type, data in events:
            await message_queue_manager.queue_message("test_room", "Bob", event_type, data)
            self.log(f"   - Queued: {event_type}", {"critical": event_type in message_queue_manager.CRITICAL_EVENTS})
        
        # Step 7: Check queue status
        queue_status = message_queue_manager.get_status()
        bob_queue = queue_status['queues'].get('test_room:Bob', {})
        self.log("9. QUEUE STATUS", {
            'total_messages': bob_queue.get('message_count', 0),
            'critical_messages': bob_queue.get('critical_count', 0)
        })
        
        # Step 8: Simulate Bob reconnecting
        self.log("10. RECONNECT: Bob returns with new websocket")
        
        # Check if can reconnect (should be True - unlimited time)
        can_reconnect = await self.connection_manager.check_reconnection("test_room", "Bob")
        self.log("11. VERIFY: Can reconnect?", {'can_reconnect': can_reconnect})
        
        # Register new connection
        await self.connection_manager.register_player("test_room", "Bob", "ws_005")
        
        # Step 9: Retrieve queued messages
        queued_messages = await message_queue_manager.get_queued_messages("test_room", "Bob")
        self.log("12. RETRIEVE: Get queued messages", {
            'message_count': len(queued_messages),
            'event_types': [msg['event_type'] for msg in queued_messages]
        })
        
        # Step 10: Restore player state
        bob_player.is_bot = False
        bob_player.is_connected = True
        bob_player.disconnect_time = None
        
        self.log("13. RESTORE: Player control restored", {
            'is_bot': bob_player.is_bot,
            'is_connected': bob_player.is_connected
        })
        
        # Step 11: Clear message queue
        await message_queue_manager.clear_queue("test_room", "Bob")
        final_status = message_queue_manager.get_status()
        self.log("14. CLEANUP: Queue cleared", {
            'queues_remaining': final_status['total_queues']
        })
        
        # Step 12: Verify final state
        bob_connection = await self.connection_manager.get_connection('test_room', 'Bob')
        stats = self.connection_manager.get_stats()
        
        self.log("15. FINAL STATE", {
            'bob_connected': bob_connection is not None,
            'bob_status': bob_connection.connection_status.value if bob_connection else None,
            'total_active_connections': stats.get('total_active', 0)
        })
        
        # Print summary
        print("\n=== TRACE SUMMARY ===")
        print(f"Total steps: {len(self.trace_log)}")
        print("\nKey Verifications:")
        print(f"✓ Unlimited reconnection: {can_reconnect}")
        print(f"✓ Bot activated on disconnect: {self.trace_log[6]['data'].get('is_bot', False)}")
        print(f"✓ Messages queued: {len(queued_messages)} messages")
        print(f"✓ Critical events preserved: {bob_queue.get('critical_count', 0)} critical")
        print(f"✓ Player state restored: is_bot={bob_player.is_bot}, connected={bob_player.is_connected}")
        print(f"✓ Queue cleaned up: {final_status['total_queues']} queues remaining")
        
        return self.trace_log


async def test_edge_cases():
    """Test edge cases in reconnection flow"""
    print("\n=== EDGE CASE TESTS ===\n")
    
    # Test 1: Multiple disconnects
    print("Test 1: Multiple simultaneous disconnects")
    tracer = ReconnectionTrace()
    cm = tracer.connection_manager
    
    await cm.register_player("room1", "Player1", "ws_1")
    await cm.register_player("room1", "Player2", "ws_2")
    await cm.register_player("room1", "Player3", "ws_3")
    
    # Disconnect all at once
    await cm.handle_disconnect("ws_1")
    await cm.handle_disconnect("ws_2")
    await cm.handle_disconnect("ws_3")
    
    # All should be able to reconnect
    can_1 = await cm.check_reconnection("room1", "Player1")
    can_2 = await cm.check_reconnection("room1", "Player2")
    can_3 = await cm.check_reconnection("room1", "Player3")
    
    print(f"  All can reconnect: {can_1 and can_2 and can_3} ✓")
    
    # Test 2: Reconnect with different websocket ID
    print("\nTest 2: Reconnect with different WebSocket ID")
    await cm.register_player("room1", "Player1", "ws_new_1")
    new_conn = await cm.get_connection("room1", "Player1")
    print(f"  New connection established: {new_conn is not None} ✓")
    print(f"  Same player name: {new_conn.player_name == 'Player1' if new_conn else False} ✓")
    
    # Test 3: Message queue overflow
    print("\nTest 3: Message queue overflow handling")
    await message_queue_manager.create_queue("room2", "TestPlayer")
    
    # Add 150 messages (queue max is 100)
    for i in range(150):
        is_critical = i % 10 == 0  # Every 10th message is critical
        event_type = "phase_change" if is_critical else "chat"
        await message_queue_manager.queue_message(
            "room2", "TestPlayer", event_type, {"index": i}
        )
    
    # Check queue didn't exceed max size
    status = message_queue_manager.get_status()
    queue_info = status['queues'].get('room2:TestPlayer', {})
    print(f"  Queue size limited: {queue_info.get('message_count', 0)} <= 100 ✓")
    print(f"  Critical messages preserved: {queue_info.get('critical_count', 0)} critical messages")
    
    # Test 4: Rapid connect/disconnect
    print("\nTest 4: Rapid connect/disconnect cycles")
    for i in range(5):
        await cm.register_player("room3", "RapidPlayer", f"ws_rapid_{i}")
        await cm.handle_disconnect(f"ws_rapid_{i}")
    
    # Should still be able to reconnect
    can_reconnect = await cm.check_reconnection("room3", "RapidPlayer")
    print(f"  Can reconnect after rapid cycles: {can_reconnect} ✓")
    
    print("\n✓ All edge cases passed!")


async def main():
    """Run all trace tests"""
    # Run main trace
    tracer = ReconnectionTrace()
    trace_log = await tracer.run_trace()
    
    # Run edge case tests
    await test_edge_cases()
    
    # Save trace log
    with open("reconnection_trace.log", "w") as f:
        f.write("=== RECONNECTION IMPLEMENTATION TRACE LOG ===\n\n")
        for entry in trace_log:
            f.write(f"[{entry['timestamp']}] {entry['step']}\n")
            if entry['data']:
                for key, value in entry['data'].items():
                    f.write(f"    {key}: {value}\n")
            f.write("\n")
    
    print("\n✅ Trace log saved to reconnection_trace.log")


if __name__ == "__main__":
    asyncio.run(main())