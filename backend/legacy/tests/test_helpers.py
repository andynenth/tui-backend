# backend/tests/test_helpers.py

"""
Test helper functions for creating realistic test data
"""

from engine.constants import PIECE_POINTS
from engine.piece import Piece


def create_test_hand_realistic():
    """
    Create realistic player hands using actual Piece objects
    Returns a dict with 4 players each having 8 pieces
    """
    # Get all available piece types
    all_pieces = list(PIECE_POINTS.keys())

    # Create realistic hands - each player gets a mix of piece types
    hands = {
        "Player1": [
            Piece("GENERAL_RED"),  # 14 points (strong)
            Piece("ADVISOR_BLACK"),  # 11 points
            Piece("ELEPHANT_RED"),  # 10 points
            Piece("CHARIOT_BLACK"),  # 7 points
            Piece("HORSE_RED"),  # 6 points
            Piece("CANNON_BLACK"),  # 3 points
            Piece("SOLDIER_RED"),  # 2 points
            Piece("SOLDIER_BLACK"),  # 1 point (weak)
        ],
        "Player2": [
            Piece("GENERAL_BLACK"),  # 13 points
            Piece("ADVISOR_RED"),  # 12 points
            Piece("ELEPHANT_BLACK"),  # 9 points
            Piece("CHARIOT_RED"),  # 8 points
            Piece("HORSE_BLACK"),  # 5 points
            Piece("CANNON_RED"),  # 4 points
            Piece("SOLDIER_RED"),  # 2 points
            Piece("SOLDIER_BLACK"),  # 1 point
        ],
        "Player3": [
            Piece("ADVISOR_RED"),  # 12 points
            Piece("ELEPHANT_RED"),  # 10 points
            Piece("CHARIOT_BLACK"),  # 7 points
            Piece("HORSE_RED"),  # 6 points
            Piece("CANNON_BLACK"),  # 3 points
            Piece("SOLDIER_RED"),  # 2 points
            Piece("SOLDIER_BLACK"),  # 1 point
            Piece("SOLDIER_RED"),  # 2 points
        ],
        "Player4": [
            Piece("ADVISOR_BLACK"),  # 11 points
            Piece("ELEPHANT_BLACK"),  # 9 points
            Piece("CHARIOT_RED"),  # 8 points
            Piece("HORSE_BLACK"),  # 5 points
            Piece("CANNON_RED"),  # 4 points
            Piece("SOLDIER_BLACK"),  # 1 point
            Piece("SOLDIER_RED"),  # 2 points
            Piece("SOLDIER_BLACK"),  # 1 point
        ],
    }

    return hands


def create_weak_hand():
    """
    Create a weak hand (no piece > 9 points) for redeal testing
    """
    return [
        Piece("ELEPHANT_BLACK"),  # 9 points (highest allowed for weak hand)
        Piece("CHARIOT_RED"),  # 8 points
        Piece("CHARIOT_BLACK"),  # 7 points
        Piece("HORSE_RED"),  # 6 points
        Piece("HORSE_BLACK"),  # 5 points
        Piece("CANNON_RED"),  # 4 points
        Piece("CANNON_BLACK"),  # 3 points
        Piece("SOLDIER_RED"),  # 2 points
    ]


def create_strong_hand():
    """
    Create a strong hand (has pieces > 9 points) for redeal testing
    """
    return [
        Piece("GENERAL_RED"),  # 14 points (strong)
        Piece("ADVISOR_BLACK"),  # 11 points (strong)
        Piece("ELEPHANT_RED"),  # 10 points (strong)
        Piece("CHARIOT_BLACK"),  # 7 points
        Piece("HORSE_RED"),  # 6 points
        Piece("CANNON_BLACK"),  # 3 points
        Piece("SOLDIER_RED"),  # 2 points
        Piece("SOLDIER_BLACK"),  # 1 point
    ]


def pieces_to_simple_list(pieces):
    """
    Convert list of Piece objects to simple list for easy testing
    Returns list of piece kinds: ["GENERAL_RED", "ADVISOR_BLACK", ...]
    """
    return [piece.kind for piece in pieces]


def create_test_play_data():
    """
    Create realistic play data for turn testing
    """
    return {
        "single_play": {
            "pieces": [Piece("GENERAL_RED")],
            "play_type": "SINGLE",
            "play_value": 14,
            "is_valid": True,
        },
        "pair_play": {
            "pieces": [Piece("SOLDIER_RED"), Piece("SOLDIER_RED")],
            "play_type": "PAIR",
            "play_value": 4,
            "is_valid": True,
        },
        "invalid_play": {
            "pieces": [Piece("GENERAL_RED"), Piece("ADVISOR_BLACK")],
            "play_type": "INVALID",
            "play_value": 0,
            "is_valid": False,
        },
    }
