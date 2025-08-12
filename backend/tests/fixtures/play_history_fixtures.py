# backend/tests/fixtures/play_history_fixtures.py

from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece
from typing import List, Dict, Any


def create_test_players(with_human: bool = False) -> List[Player]:
    """Create test players for fixtures."""
    players = [
        Player("Bot 1", is_bot=True),
        Player("Bot 2", is_bot=True),
        Player("Bot 3", is_bot=True),
    ]

    if with_human:
        players.append(Player("Alice", is_bot=False))
    else:
        players.append(Player("Bot 4", is_bot=True))

    return players


def create_known_hands() -> Dict[str, List[Piece]]:
    """Create known hands for testing."""
    return {
        "bot_1": [
            Piece("GENERAL_RED"),  # 14
            Piece("ADVISOR_RED"),  # 12
            Piece("ELEPHANT_BLACK"),  # 9
            Piece("HORSE_BLACK"),  # 5
            Piece("CANNON_BLACK"),  # 3
            Piece("CANNON_BLACK"),  # 3
            Piece("SOLDIER_RED"),  # 2
            Piece("SOLDIER_BLACK"),  # 1
        ],
        "bot_2": [
            Piece("GENERAL_BLACK"),  # 13
            Piece("ADVISOR_BLACK"),  # 11
            Piece("ELEPHANT_RED"),  # 10
            Piece("CHARIOT_RED"),  # 8
            Piece("HORSE_RED"),  # 6
            Piece("CANNON_RED"),  # 4
            Piece("SOLDIER_RED"),  # 2
            Piece("SOLDIER_BLACK"),  # 1
        ],
        "bot_3": [
            Piece("ADVISOR_RED"),  # 12
            Piece("ADVISOR_BLACK"),  # 11
            Piece("ELEPHANT_RED"),  # 10
            Piece("CHARIOT_BLACK"),  # 7
            Piece("HORSE_RED"),  # 6
            Piece("HORSE_BLACK"),  # 5
            Piece("CANNON_RED"),  # 4
            Piece("SOLDIER_BLACK"),  # 1
        ],
        "bot_4": [
            Piece("ELEPHANT_BLACK"),  # 9
            Piece("CHARIOT_RED"),  # 8
            Piece("CHARIOT_BLACK"),  # 7
            Piece("HORSE_BLACK"),  # 5
            Piece("CANNON_BLACK"),  # 3
            Piece("SOLDIER_RED"),  # 2
            Piece("SOLDIER_RED"),  # 2
            Piece("SOLDIER_BLACK"),  # 1
        ],
    }


def create_completed_game_fixture() -> Game:
    """Create a completed 2-round game for testing."""
    players = create_test_players()
    game = Game(players)

    # TODO: Set up game state with 2 completed rounds
    # This will involve:
    # 1. Dealing specific hands
    # 2. Making declarations
    # 3. Playing turns
    # 4. Completing rounds with known outcomes

    return game


def create_single_round_game_fixture() -> Game:
    """Create a game with single completed round."""
    players = create_test_players()
    game = Game(players)

    # TODO: Set up single round with known state

    return game


def create_mixed_players_game_fixture() -> Game:
    """Create a game with both AI and human players."""
    players = create_test_players(with_human=True)
    game = Game(players)

    # TODO: Set up game with mixed player types

    return game


def create_abandoned_game_fixture() -> Game:
    """Create a game that was abandoned mid-round."""
    players = create_test_players()
    game = Game(players)

    # TODO: Set up game with incomplete round

    return game


def create_test_game_with_known_state() -> Game:
    """Create a game with fully known state for testing."""
    players = create_test_players()
    game = Game(players)

    # TODO: Set up complete known game state

    return game


def create_mock_round_data() -> Dict[str, Any]:
    """Create mock round data for testing."""
    return {
        "round_number": 1,
        "starter": "bot_1",
        "hands": create_known_hands(),
        "declarations": {
            "bot_1": 4,
            "bot_2": 2,
            "bot_3": 2,
            "bot_4": 0,
        },
        "turns": [
            {
                "turn_number": 1,
                "starter": "bot_1",
                "plays": {
                    "bot_1": [Piece("SOLDIER_BLACK")],
                    "bot_2": [Piece("SOLDIER_BLACK")],
                    "bot_3": [Piece("GENERAL_RED")],
                    "bot_4": [Piece("SOLDIER_BLACK")],
                },
                "winner": "bot_3",
            },
            # More turns...
        ],
        "final_captures": {
            "bot_1": 2,
            "bot_2": 3,
            "bot_3": 2,
            "bot_4": 1,
        },
    }
