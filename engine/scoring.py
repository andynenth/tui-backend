# engine/scoring.py
# ------------------------------------------------------------------------
# Calculate the player's score based on their declared and actual result.
# ------------------------------------------------------------------------
#     - If the player declares 0 and gets 0: +3 bonus points.
#     - If the player declares 0 but captures something: penalty = -actual.
#     - If declared equals actual (non-zero): score = declared + 5 bonus.
#     - Otherwise: penalty = -abs(declared - actual).


def calculate_score(declared: int, actual: int) -> int:

    if declared == 0:
        if actual == 0:
            return 3  # Success: declared 0 and captured nothing → +3 bonus
        else:
            return -actual  # Fail: declared 0 but captured something → -actual
    else:
        if actual == declared:
            return declared + 5  # Exact match → declared + 5 bonus
        else:
            return -abs(declared - actual)  # Off target → penalty by difference


def calculate_round_scores(players, pile_counts, redeal_multiplier):
    score_data = []
    for player in players:
        actual = pile_counts[player.name]
        declared = player.declared
        delta = calculate_score(declared, actual) * redeal_multiplier
        player.score += delta
        score_data.append({
            "player": player,
            "declared": declared,
            "actual": actual,
            "delta": delta,
            "multiplier": redeal_multiplier,
            "total": player.score
        })
    return score_data
