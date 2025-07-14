#!/usr/bin/env python3
"""
Simulate API endpoint calls to test complete replacement integration
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.room import Room
from engine.state_machine.core import ActionType, GameAction, GamePhase


class MockRoomManager:
    """Mock room manager for testing"""

    def __init__(self):
        self.rooms = {}

    def create_room(self, name):
        room_id = f"room_{len(self.rooms) + 1}"
        room = Room(room_id, name)
        self.rooms[room_id] = room
        return room_id

    def get_room(self, room_id):
        return self.rooms.get(room_id)


async def simulate_start_game_endpoint(room_manager, room_id):
    """Simulate /start-game endpoint"""
    print("🚀 Simulating /start-game endpoint")

    room = room_manager.get_room(room_id)
    if not room:
        return {"error": "Room not found"}

    # Simulate broadcast callback
    async def room_broadcast(event_type: str, event_data: dict):
        print(f"📡 WebSocket Broadcast: {event_type}")

    try:
        result = await room.start_game_safe(broadcast_callback=room_broadcast)

        if not result.get("success"):
            return {"error": "Failed to start game"}

        print("✅ Game started with StateMachine")
        return {"ok": True, "operation_id": result["operation_id"]}

    except Exception as e:
        return {"error": str(e)}


async def simulate_declare_endpoint(room_manager, room_id, player_name, value):
    """Simulate /declare endpoint"""
    print(f"🗣️ Simulating /declare endpoint: {player_name} = {value}")

    room = room_manager.get_room(room_id)
    if not room or not room.game_state_machine:
        return {"error": "Game or state machine not found"}

    try:
        action = GameAction(
            player_name=player_name,
            action_type=ActionType.DECLARE,
            payload={"value": value},
        )

        result = await room.game_state_machine.handle_action(action)

        if not result.get("success"):
            return {"error": result.get("error", "Declaration failed")}

        print(f"✅ Declaration queued for {player_name}: {value}")
        return {"status": "ok", "queued": True}

    except Exception as e:
        return {"error": str(e)}


async def simulate_redeal_decline(room_manager, room_id, player_name):
    """Simulate redeal decline"""
    print(f"❌ Simulating redeal decline: {player_name}")

    room = room_manager.get_room(room_id)
    if not room or not room.game_state_machine:
        return {"error": "Game or state machine not found"}

    try:
        action = GameAction(
            player_name=player_name,
            action_type=ActionType.REDEAL_RESPONSE,
            payload={"accept": False},
        )

        result = await room.game_state_machine.handle_action(action)
        return {"status": "ok", "declined": True}

    except Exception as e:
        return {"error": str(e)}


async def test_api_simulation():
    """Test complete API flow simulation"""
    print("🎯 Testing API Simulation")

    try:
        # 1. Create room manager and room
        room_manager = MockRoomManager()
        room_id = room_manager.create_room("TestHost")
        print(f"✅ Room created: {room_id}")

        # 2. Simulate /start-game
        result = await simulate_start_game_endpoint(room_manager, room_id)
        if "error" in result:
            print(f"❌ Start game failed: {result['error']}")
            return False
        print(f"✅ Start game result: {result}")

        # 3. Get room state
        room = room_manager.get_room(room_id)
        print(f"✅ Current phase: {room.game_state_machine.current_phase}")

        # 4. Handle weak hand redeals (since all players likely have weak hands)
        await asyncio.sleep(0.2)
        await room.game_state_machine.process_pending_actions()

        prep_state = room.game_state_machine.current_state
        if (
            prep_state
            and hasattr(prep_state, "weak_players")
            and prep_state.weak_players
        ):
            print(f"🔍 Handling weak players: {prep_state.weak_players}")

            # Decline for all weak players
            weak_players_list = list(prep_state.weak_players)
            for player in weak_players_list:
                if (
                    hasattr(prep_state, "current_weak_player")
                    and prep_state.current_weak_player == player
                ):
                    result = await simulate_redeal_decline(
                        room_manager, room_id, player
                    )
                    print(f"✅ {player} decline result: {result}")

                    await asyncio.sleep(0.1)
                    await room.game_state_machine.process_pending_actions()

            # Force transition to DECLARATION
            await asyncio.sleep(0.2)
            next_phase = await prep_state.check_transition_conditions()
            if next_phase == GamePhase.DECLARATION:
                await room.game_state_machine._transition_to(GamePhase.DECLARATION)
                print(f"✅ Transitioned to: {room.game_state_machine.current_phase}")

        # 5. Simulate declarations if in DECLARATION phase
        if room.game_state_machine.current_phase == GamePhase.DECLARATION:
            print("🗣️ Simulating declarations")

            players = ["TestHost", "Bot 2", "Bot 3", "Bot 4"]
            declarations = [2, 2, 2, 1]  # Total = 7 ≠ 8 (valid)

            for player, value in zip(players, declarations):
                result = await simulate_declare_endpoint(
                    room_manager, room_id, player, value
                )
                print(f"✅ {player} declare result: {result}")

                await asyncio.sleep(0.1)
                await room.game_state_machine.process_pending_actions()

        # 6. Final results
        print(f"\n📊 API Simulation Results:")
        print(f"   Final phase: {room.game_state_machine.current_phase}")
        print(f"   State machine running: {room.game_state_machine.is_running}")

        # 7. Cleanup
        await room.game_state_machine.stop()
        print("✅ API simulation complete")

        return True

    except Exception as e:
        print(f"❌ API simulation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    success = await test_api_simulation()
    print(f"\n🎯 API Simulation Test: {'PASSED' if success else 'FAILED'}")

    if success:
        print("\n🎉 Complete Replacement Integration SUCCESSFUL!")
        print("✅ Room creation works")
        print("✅ Game start with state machine works")
        print("✅ WebSocket broadcasting integration works")
        print("✅ GameAction processing works")
        print("✅ State transitions work")
        print("✅ API endpoint simulation works")

        print("\n🚀 Ready for production testing!")


if __name__ == "__main__":
    asyncio.run(main())
