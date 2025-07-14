# backend/engine/scoring.py
# ------------------------------------------------------------------------
# Scoring Logic for Each Round
# ------------------------------------------------------------------------
# Rules:
# - If declared = 0 and actual = 0 → +3 bonus points
# - If declared = 0 but actual > 0 → penalty = -actual
# - If declared == actual (non-zero) → score = declared + 5 bonus
# - Otherwise → penalty = -abs(declared - actual)
# - If this round was triggered by a redeal → score × multiplier
# ------------------------------------------------------------------------


def calculate_score(declared: int, actual: int) -> int:
    """
    Calculate base score based on declared and actual piles captured.

    Args:
        declared (int): The number of piles the player aimed to capture.
        actual (int): The number of piles the player actually captured.

    Returns:
        int: The score before applying any multipliers.
    """
    if declared == 0:
        if actual == 0:
            return 3  # Success: declared 0 and kept it → reward
        else:
            return -actual  # Failure: declared 0 but took some → penalty
    else:
        if actual == declared:
            return declared + 5  # Perfect prediction → bonus
        else:
            return -abs(declared - actual)  # Missed target → penalty


def calculate_round_scores(players, pile_counts, redeal_multiplier):
    """
    Apply score calculation to all players at the end of the round.

    Args:
        players (List[Player]): All players in the game.
        pile_counts (Dict[str, int]): How many pieces (piles) each player captured.
        redeal_multiplier (int): Score multiplier due to redeals (e.g., ×2, ×3...)

    Returns:
        List[Dict]: Score summary for this round, one entry per player.
    """
    score_data = []

    for player in players:
        declared = player.declared  # What they announced they'd capture
        actual = pile_counts[player.name]  # What they actually captured
        delta = calculate_score(declared, actual) * redeal_multiplier

        player.score += delta  # Update total score

        # Check for perfect round (non-zero declaration that was met exactly)
        perfect_round = declared > 0 and declared == actual
        if perfect_round:
            player.perfect_rounds += 1

        score_data.append(
            {
                "player": player,  # Reference to player object
                "declared": declared,  # Declared pile target
                "actual": actual,  # Actual piles captured
                "delta": delta,  # Score gained/lost this round
                "multiplier": redeal_multiplier,  # Score multiplier from redeals
                "total": player.score,  # Updated total score
                "perfect_round": perfect_round,  # Whether this was a perfect round
                "total_perfect_rounds": player.perfect_rounds,  # Cumulative perfect rounds
            }
        )

    return score_data
