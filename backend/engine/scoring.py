# backend/engine/scoring.py
# ------------------------------------------------------------------------
# Scoring Logic for Each Round
# ------------------------------------------------------------------------
# Rules:
# - If declared = 0 and actual = 0 → +3 bonus points (no multiplier)
# - If declared = 0 but actual > 0 → penalty = -actual × multiplier
# - If declared == actual (non-zero) → score = (declared × multiplier) + 5
# - Otherwise → penalty = -abs(declared - actual) × multiplier
# - Multipliers apply only to base points (X), not to bonuses (+3 or +5)
# ------------------------------------------------------------------------


def calculate_score(declared: int, actual: int) -> int:
    """
    Calculate base score based on declared and actual piles captured.

    DEPRECATED: This function uses OLD scoring rules where bonuses are included
    in the base score. Use calculate_final_score() for the new rules where
    multipliers only apply to base points.

    Args:
        declared (int): The number of piles the player aimed to capture.
        actual (int): The number of piles the player actually captured.

    Returns:
        int: The score before applying any multipliers (OLD RULES).
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

    DEPRECATED: This function appears to be unused and has a bug where code
    expects it to return a dict but it returns a list. The actual game uses
    ScoringState._calculate_round_scores() instead.

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


# ------------------------------------------------------------------------
# NEW SCORING FUNCTIONS - Implement current rules correctly
# ------------------------------------------------------------------------


def calculate_score_components(declared: int, actual: int) -> dict:
    """
    Calculate scoring components based on declared and actual piles.

    This implements the NEW scoring rules where multipliers only apply
    to base points, not to bonuses.

    Args:
        declared (int): The number of piles the player aimed to capture.
        actual (int): The number of piles the player actually captured.

    Returns:
        dict: {
            'base_points': int,    # The X value (can be positive or negative)
            'bonus': int,          # Fixed bonus (0, 3, or 5)
            'is_perfect': bool,    # Whether it's a perfect prediction
            'hit_type': str        # 'perfect_zero', 'perfect', 'miss', 'failed_zero'
        }
    """
    if declared == 0:
        if actual == 0:
            # Perfect zero prediction
            return {
                "base_points": 0,
                "bonus": 3,
                "is_perfect": True,
                "hit_type": "perfect_zero",
            }
        else:
            # Failed zero declaration
            return {
                "base_points": -actual,
                "bonus": 0,
                "is_perfect": False,
                "hit_type": "failed_zero",
            }
    else:
        if actual == declared:
            # Perfect non-zero prediction
            return {
                "base_points": declared,
                "bonus": 5,
                "is_perfect": True,
                "hit_type": "perfect",
            }
        else:
            # Missed target
            return {
                "base_points": -abs(declared - actual),
                "bonus": 0,
                "is_perfect": False,
                "hit_type": "miss",
            }


def calculate_final_score(declared: int, actual: int, multiplier: int = 1) -> dict:
    """
    Calculate final score with multiplier applied correctly.

    This implements the NEW rules where multipliers only apply to base points,
    not to bonuses (+3 or +5).

    Args:
        declared (int): The number of piles the player aimed to capture.
        actual (int): The number of piles the player actually captured.
        multiplier (int): Score multiplier due to redeals (e.g., ×2, ×3...)

    Returns:
        dict: {
            'final_score': int,     # The final score after multiplier
            'base_points': int,     # Base points (before multiplier)
            'bonus': int,           # Fixed bonus (not multiplied)
            'multiplier': int,      # The multiplier used
            'hit_value': int,       # For UI display (base × multiplier)
            'is_perfect': bool,     # Whether it's a perfect prediction
            'hit_type': str         # Type of result
        }
    """
    components = calculate_score_components(declared, actual)

    # Apply multiplier ONLY to base points
    if components["hit_type"] == "perfect_zero":
        # Special case: +3 bonus with no multiplier
        final_score = components["bonus"]
        hit_value = 0
    else:
        # All other cases: multiply base points, add bonus after
        hit_value = components["base_points"] * multiplier
        final_score = hit_value + components["bonus"]

    return {
        "final_score": final_score,
        "base_points": components["base_points"],
        "bonus": components["bonus"],
        "multiplier": multiplier,
        "hit_value": hit_value,
        "is_perfect": components["is_perfect"],
        "hit_type": components["hit_type"],
    }
