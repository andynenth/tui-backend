# engine/ai.py

from itertools import combinations
from engine.rules import is_valid_play, get_play_type

def find_valid_plays(hand):
    """คืนชุด play ที่ valid ทั้งหมดจากมือ"""
    valid_plays = []

    for r in range(1, 7):  # เล่นได้ตั้งแต่ 1–6 ตัว
        for combo in combinations(hand, r):
            if is_valid_play(combo):
                valid_plays.append(list(combo))

    return valid_plays

def choose_best_play(hand):
    """เลือกชุดหมากที่ valid และมีแต้มรวมมากที่สุด"""
    valid_plays = find_valid_plays(hand)
    if not valid_plays:
        return []

    return max(valid_plays, key=lambda p: sum(piece.point for piece in p))
