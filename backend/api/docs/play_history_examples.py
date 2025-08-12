# backend/api/docs/play_history_examples.py
"""
Example responses for play history API documentation.
"""

# Full response example
PLAY_HISTORY_FULL_EXAMPLE = {
    "room_id": "ROOM123",
    "total_rounds": 2,
    "players": {
        "Player 1": {
            "player_id": "player1",
            "player_name": "Player 1",
            "player_type": "human",
            "ai_version": None,
        },
        "Bot 2": {
            "player_id": "bot2",
            "player_name": "Bot 2",
            "player_type": "ai",
            "ai_version": "v2.0",
        },
        "Bot 3": {
            "player_id": "bot3",
            "player_name": "Bot 3",
            "player_type": "ai",
            "ai_version": "v2.0",
        },
        "Bot 4": {
            "player_id": "bot4",
            "player_name": "Bot 4",
            "player_type": "ai",
            "ai_version": "v2.0",
        },
    },
    "rounds": [
        {
            "round_number": 1,
            "initial_state": {
                "starter": {
                    "player_id": "player1",
                    "player_name": "Player 1",
                    "reason": "red_general",
                    "highest_card": "GENERAL_RED",
                },
                "player_order": ["Player 1", "Bot 2", "Bot 3", "Bot 4"],
            },
            "hands_dealt": {
                "Player 1": [
                    {"kind": "GENERAL_RED", "point": 9999},
                    {"kind": "ADVISOR_RED", "point": 60},
                    {"kind": "ELEPHANT_RED", "point": 50},
                    {"kind": "CHARIOT_BLACK", "point": 40},
                    {"kind": "HORSE_BLACK", "point": 30},
                    {"kind": "CANNON_BLACK", "point": 20},
                    {"kind": "SOLDIER_RED", "point": 1},
                    {"kind": "SOLDIER_BLACK", "point": 1},
                ]
            },
            "declaration_phase": {
                "declarations": [
                    {
                        "player_id": "player1",
                        "declared": 2,
                        "position": 0,
                        "strategy_notes": None,
                    },
                    {
                        "player_id": "bot2",
                        "declared": 3,
                        "position": 1,
                        "strategy_notes": "Conservative strategy - manageable target with strong middle cards",
                    },
                    {
                        "player_id": "bot3",
                        "declared": 1,
                        "position": 2,
                        "strategy_notes": "Aggressive low declaration - aiming for exact match",
                    },
                    {
                        "player_id": "bot4",
                        "declared": 2,
                        "position": 3,
                        "strategy_notes": "Balanced approach - moderate risk/reward",
                    },
                ],
                "total_declared": 8,
                "pile_room_calculation": {
                    "Player 1": 6,
                    "Bot 2": 5,
                    "Bot 3": 7,
                    "Bot 4": 6,
                },
            },
            "turn_history": [
                {
                    "turn_number": 1,
                    "plays": [
                        {
                            "player_id": "player1",
                            "player_name": "Player 1",
                            "pieces_played": [{"kind": "SOLDIER_RED", "point": 1}],
                            "play_type": "SINGLE",
                            "hand_before": [
                                {"kind": "GENERAL_RED", "point": 9999},
                                {"kind": "ADVISOR_RED", "point": 60},
                                {"kind": "ELEPHANT_RED", "point": 50},
                                {"kind": "CHARIOT_BLACK", "point": 40},
                                {"kind": "HORSE_BLACK", "point": 30},
                                {"kind": "CANNON_BLACK", "point": 20},
                                {"kind": "SOLDIER_RED", "point": 1},
                                {"kind": "SOLDIER_BLACK", "point": 1},
                            ],
                            "hand_after": [
                                {"kind": "GENERAL_RED", "point": 9999},
                                {"kind": "ADVISOR_RED", "point": 60},
                                {"kind": "ELEPHANT_RED", "point": 50},
                                {"kind": "CHARIOT_BLACK", "point": 40},
                                {"kind": "HORSE_BLACK", "point": 30},
                                {"kind": "CANNON_BLACK", "point": 20},
                                {"kind": "SOLDIER_BLACK", "point": 1},
                            ],
                            "captured_count": 0,
                            "declared_count": 2,
                            "ai_decision_analysis": None,
                        },
                        {
                            "player_id": "bot2",
                            "player_name": "Bot 2",
                            "pieces_played": [{"kind": "SOLDIER_BLACK", "point": 1}],
                            "play_type": "SINGLE",
                            "hand_before": [
                                {"kind": "ADVISOR_BLACK", "point": 60},
                                {"kind": "ELEPHANT_BLACK", "point": 50},
                                {"kind": "CHARIOT_RED", "point": 40},
                                {"kind": "HORSE_RED", "point": 30},
                                {"kind": "CANNON_RED", "point": 20},
                                {"kind": "SOLDIER_BLACK", "point": 1},
                                {"kind": "SOLDIER_BLACK", "point": 1},
                                {"kind": "SOLDIER_RED", "point": 1},
                            ],
                            "hand_after": [
                                {"kind": "ADVISOR_BLACK", "point": 60},
                                {"kind": "ELEPHANT_BLACK", "point": 50},
                                {"kind": "CHARIOT_RED", "point": 40},
                                {"kind": "HORSE_RED", "point": 30},
                                {"kind": "CANNON_RED", "point": 20},
                                {"kind": "SOLDIER_BLACK", "point": 1},
                                {"kind": "SOLDIER_RED", "point": 1},
                            ],
                            "captured_count": 0,
                            "declared_count": 3,
                            "ai_decision_analysis": {
                                "declaration_reasoning": {
                                    "declared_target": 3,
                                    "confidence": 0.75,
                                    "strategy": "conservative",
                                },
                                "turn_play_reasoning": {
                                    "available_plays": ["SINGLE", "PAIR"],
                                    "chosen_play": "SINGLE",
                                    "reasoning": "Matching opponent's single play with lowest card",
                                },
                            },
                        },
                    ],
                    "winner": {
                        "player_id": "bot3",
                        "player_name": "Bot 3",
                        "winning_play": [{"kind": "ELEPHANT_RED", "point": 50}],
                        "pieces_captured": 4,
                    },
                    "next_starter": "Bot 3",
                    "game_state_after": {
                        "Player 1": {"captured": 0, "declared": 2, "hand_size": 7},
                        "Bot 2": {"captured": 0, "declared": 3, "hand_size": 7},
                        "Bot 3": {"captured": 4, "declared": 1, "hand_size": 7},
                        "Bot 4": {"captured": 0, "declared": 2, "hand_size": 7},
                    },
                }
            ],
            "round_summary": {
                "total_turns": 8,
                "final_captures": {
                    "Player 1": {"captured": 7, "declared": 2, "difference": 5},
                    "Bot 2": {"captured": 12, "declared": 3, "difference": 9},
                    "Bot 3": {"captured": 8, "declared": 1, "difference": 7},
                    "Bot 4": {"captured": 5, "declared": 2, "difference": 3},
                },
                "scoring": {
                    "Player 1": {
                        "points": 10,
                        "multiplier": 1,
                        "reason": "overcapture",
                    },
                    "Bot 2": {"points": -6, "multiplier": 1, "reason": "overcapture"},
                    "Bot 3": {"points": 15, "multiplier": 1, "reason": "overcapture"},
                    "Bot 4": {"points": 5, "multiplier": 1, "reason": "overcapture"},
                },
                "cumulative_scores": {
                    "Player 1": 10,
                    "Bot 2": -6,
                    "Bot 3": 15,
                    "Bot 4": 5,
                },
            },
        }
    ],
}

# Compact response example
PLAY_HISTORY_COMPACT_EXAMPLE = {
    "room_id": "ROOM123",
    "total_rounds": 2,
    "players": {
        "Player 1": {
            "player_id": "player1",
            "player_name": "Player 1",
            "player_type": "human",
            "ai_version": None,
        },
        "Bot 2": {
            "player_id": "bot2",
            "player_name": "Bot 2",
            "player_type": "ai",
            "ai_version": "v2.0",
        },
        "Bot 3": {
            "player_id": "bot3",
            "player_name": "Bot 3",
            "player_type": "ai",
            "ai_version": "v2.0",
        },
        "Bot 4": {
            "player_id": "bot4",
            "player_name": "Bot 4",
            "player_type": "ai",
            "ai_version": "v2.0",
        },
    },
    "rounds": [
        {
            "round_number": 1,
            "initial_state": {
                "starter": {
                    "player_id": "player1",
                    "player_name": "Player 1",
                    "reason": "red_general",
                },
                "player_order": ["Player 1", "Bot 2", "Bot 3", "Bot 4"],
            },
            "hands_dealt": {},  # Empty in compact format
            "declaration_phase": {
                "declarations": [
                    {"player_id": "player1", "declared": 2},
                    {"player_id": "bot2", "declared": 3},
                    {"player_id": "bot3", "declared": 1},
                    {"player_id": "bot4", "declared": 2},
                ],
                "total_declared": 8,
            },
            "turn_history": [],  # Minimal in compact format
            "round_summary": {
                "total_turns": 8,
                "final_captures": {
                    "Player 1": {"captured": 7, "declared": 2},
                    "Bot 2": {"captured": 12, "declared": 3},
                    "Bot 3": {"captured": 8, "declared": 1},
                    "Bot 4": {"captured": 5, "declared": 2},
                },
                "scoring": {
                    "Player 1": {"points": 10},
                    "Bot 2": {"points": -6},
                    "Bot 3": {"points": 15},
                    "Bot 4": {"points": 5},
                },
                "cumulative_scores": {
                    "Player 1": 10,
                    "Bot 2": -6,
                    "Bot 3": 15,
                    "Bot 4": 5,
                },
            },
        }
    ],
}

# Error response examples
ERROR_ROOM_NOT_FOUND = {
    "error": {
        "code": "ROOM_NOT_FOUND",
        "message": "Room with ID 'ABC123' not found",
        "status_code": 404,
    },
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-10T10:30:00Z",
    "path": "/api/rooms/ABC123/play-history",
}

ERROR_NO_ACTIVE_GAME = {
    "error": {
        "code": "NO_ACTIVE_GAME",
        "message": "Room 'ABC123' has no active game",
        "status_code": 400,
    },
    "request_id": "550e8400-e29b-41d4-a716-446655440001",
    "timestamp": "2024-01-10T10:30:00Z",
    "path": "/api/rooms/ABC123/play-history",
}

ERROR_INVALID_RANGE = {
    "error": {
        "code": "INVALID_RANGE",
        "message": "'from' must be less than or equal to 'to'",
        "status_code": 400,
        "field": "from",
        "context": {"from": 5, "to": 3},
    },
    "request_id": "550e8400-e29b-41d4-a716-446655440002",
    "timestamp": "2024-01-10T10:30:00Z",
    "path": "/api/rooms/ABC123/play-history/rounds",
}
