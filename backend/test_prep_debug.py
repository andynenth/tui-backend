#!/usr/bin/env python3
"""
Debug preparation phase transition conditions
"""
import asyncio
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GamePhase
from engine.game import Game
from engine.player import Player


async def debug_preparation():
    """Debug preparation phase state"""
    print("🔍 Debugging preparation phase...")

    # Create test players
    players = [Player(f"Player {i+1}", is_bot=(i > 0)) for i in range(4)]

    # Create test game
    game = Game(players)

    async def capture_broadcast(event_type, event_data):
        print(f"📡 {event_type}: {event_data}")

    # Create state machine
    state_machine = GameStateMachine(game, capture_broadcast)

    # Start in preparation phase
    await state_machine.start(GamePhase.PREPARATION)

    # Wait a moment for setup
    await asyncio.sleep(0.2)

    # Check preparation state internal data
    prep_state = state_machine.current_state
    print(f"Current phase: {state_machine.current_phase}")
    print(f"State type: {type(prep_state).__name__}")

    if hasattr(prep_state, "initial_deal_complete"):
        print(f"Initial deal complete: {prep_state.initial_deal_complete}")

    if hasattr(prep_state, "weak_players"):
        print(f"Weak players: {prep_state.weak_players}")

    # Manually check transition conditions
    next_phase = await prep_state.check_transition_conditions()
    print(f"Next phase from transition check: {next_phase}")

    # Check game state
    print(
        f"Game players count: {len(game.players) if hasattr(game, 'players') else 'No players'}"
    )
    if hasattr(game, "players"):
        for i, player in enumerate(game.players):
            if player:
                hand_size = (
                    len(player.hand) if hasattr(player, "hand") and player.hand else 0
                )
                print(f"  Player {player.name}: {hand_size} pieces")

    await state_machine.stop()


if __name__ == "__main__":
    asyncio.run(debug_preparation())
