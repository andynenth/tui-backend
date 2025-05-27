# win_conditions.py

from enum import Enum

class WinConditionType(Enum):
    FIRST_TO_REACH_50 = "first_to_50"
    AFTER_20_ROUNDS = "after_20_rounds"
    EXACTLY_50_POINTS = "exactly_50_points"              # Only a score of exactly 50 wins

# -----------------------------------------------
# Check if the game should end
# -----------------------------------------------

def is_game_over(game):
    condition = game.win_condition_type

    if condition == WinConditionType.FIRST_TO_REACH_50:
        return any(p.score >= game.max_score for p in game.players)

    if condition == WinConditionType.MOST_POINTS_AFTER_20_ROUNDS:
        return game.round_number >= game.max_rounds

    if condition == WinConditionType.EXACTLY_50_POINTS:
        return any(p.score == game.max_score for p in game.players)

    return False

# -----------------------------------------------
# Determine the winner(s) based on win condition
# -----------------------------------------------

def get_winners(game):
    condition = game.win_condition_type

    if condition == WinConditionType.EXACTLY_50_POINTS:
        qualified = [p for p in game.players if p.score == game.max_score]

    elif condition == WinConditionType.FIRST_TO_REACH_50:
        qualified = [p for p in game.players if p.score >= game.max_score]

    elif condition == WinConditionType.MOST_POINTS_AFTER_20_ROUNDS:
        if game.round_number < game.max_rounds:
            return []  # Game not finished yet
        max_score = max(p.score for p in game.players)
        qualified = [p for p in game.players if p.score == max_score]

    else:
        return []

    if not qualified:
        return []

    # If multiple players qualify, only return those with the highest score
    highest = max(p.score for p in qualified)
    return [p for p in qualified if p.score == highest]
