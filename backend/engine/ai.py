# backend/engine/main.py

from itertools import combinations
from engine.rules import is_valid_play, get_play_type
from collections import Counter

# ------------------------------------------------------------------
# Find all valid combinations from a hand (1 to 6 pieces per combo)
# ------------------------------------------------------------------
def find_all_valid_combos(hand):
    results = []
    for r in range(1, 7):  # Try all combination lengths from 1 to 6
        for combo in combinations(hand, r):
            pieces = list(combo)
            if is_valid_play(pieces):
                play_type = get_play_type(pieces)
                results.append((play_type, pieces))
    return results

# ------------------------------------------------------------------
# Decide how many piles the bot should declare at the start of a round
# ------------------------------------------------------------------
def choose_declare(
    hand,
    is_first_player: bool,
    position_in_order: int,
    previous_declarations: list[int],
    must_declare_nonzero: bool,
    verbose: bool = True
) -> int:
    # Categorize hand pieces
    high_pieces = [p for p in hand if p.point >= 9]
    mid_pieces = [p for p in hand if 7 <= p.point < 9]

    # Search for powerful combinations
    combos = find_all_valid_combos(hand)
    strong_combos = [c for c in combos if c[0] in {
        "THREE_OF_A_KIND", "STRAIGHT", "FOUR_OF_A_KIND",
        "EXTENDED_STRAIGHT", "FIVE_OF_A_KIND", "DOUBLE_STRAIGHT"
    }]

    # Determine if the hand has a strong opener (e.g. GENERAL or high STRAIGHT)
    has_strong_opening = any(p.name.startswith("GENERAL") or p.point >= 13 for p in hand)
    for combo_type, pieces in strong_combos:
        if combo_type in {"STRAIGHT", "EXTENDED_STRAIGHT"}:
            if sum(p.point for p in pieces) >= 20:
                has_strong_opening = True

    # Estimate base declare score
    score = len(strong_combos)
    if has_strong_opening:
        score += 1
    if is_first_player:
        score += 1

    # Adjust score for weak hands
    if not high_pieces and not strong_combos:
        score = 0
    elif score == 0 and mid_pieces:
        score = 1
    score = min(max(score, 1), 7)  # Clamp score to range [1, 7]

    # Debug info for analysis
    if verbose:
        print(f"\n🤖 DEBUG: Evaluating declare for BOT")
        print(f"  Position in order: {position_in_order} (First: {is_first_player})")
        print(f"  Must declare ≥1: {must_declare_nonzero}")
        print(f"  Previous declarations: {previous_declarations}")
        
        # 🔧 Sorting: RED first (reverse lexicographically), then by descending point
        sorted_hand = sorted(
            [(i, piece) for i, piece in enumerate(hand)],
            key=lambda pair: (pair[1].color != "RED", -pair[1].point)
        )
        print(f"  Hand: ") 
        for shown_idx, (real_idx, piece) in enumerate(sorted_hand):
            print(f"    [{real_idx}] {piece}")
        
        print(f"  High pieces (>=9): {[p.name for p in high_pieces]}")
        print(f"  Mid pieces (7–8): {[p.name for p in mid_pieces]}")
        print(f"  Found {len(strong_combos)} strong combo(s):")
        for play_type, pieces in strong_combos:
            summary = ', '.join(p.name for p in pieces)
            print(f"    - {play_type}: {summary}")
        print(f"  Has strong opening: {has_strong_opening}")
        print(f"  Raw declare score (before filtering): {score}")

    # Apply game rules that forbid certain declarations
    forbidden_declares = set()
    if position_in_order == 3:
        # Last player cannot declare the exact value that makes total = 8
        total_so_far = sum(previous_declarations)
        forbidden = 8 - total_so_far
        if 0 <= forbidden <= 8:
            forbidden_declares.add(forbidden)
    if must_declare_nonzero:
        forbidden_declares.add(0)

    # Determine valid declaration options
    valid_range = [d for d in range(0, 8) if d not in forbidden_declares]

    # Select final declare value
    if score in valid_range:
        final = score
    else:
        valid_range.sort()
        final = valid_range[-1] if score > valid_range[-1] else valid_range[0]

    if verbose:
        print(f"  Forbidden declares: {sorted(forbidden_declares)}")
        print(f"  Final declare chosen: {final}")
        
    return final

# ------------------------------------------------------------------
# Utility function to check if all pieces in a play exist in hand
# (helps prevent using pieces not actually in the player's hand)
# ------------------------------------------------------------------
def pieces_exist_in_hand(play, hand):
    play_counts = Counter(play)
    hand_counts = Counter(hand)
    return all(play_counts[p] <= hand_counts[p] for p in play)

# ------------------------------------------------------------------
# Choose the best play (set of 1–6 pieces) based on total point value
# ------------------------------------------------------------------
def choose_best_play(hand: list, required_count: int | None, verbose: bool = True) -> list:
    best_play = None
    best_score = -1
    best_type = None

    # Determine which sizes of combinations to check
    play_sizes = [required_count] if required_count else range(1, 7)

    for r in play_sizes:
        for combo in combinations(hand, r):
            pieces = list(combo)
            if required_count and len(pieces) != required_count:
                continue  # Skip if the size does not match required count
            if is_valid_play(pieces):
                total = sum(p.point for p in pieces)
                if total > best_score:
                    best_score = total
                    best_play = pieces
                    best_type = get_play_type(pieces)

    # Return best found play
    if best_play:
        if verbose:
            summary = ', '.join(p.name for p in best_play)
            print(f"🤖 BOT chooses to play {best_type} ({best_score} pts): {summary}")
        return best_play

    # Fallback: discard lowest-point pieces if no valid play
    fallback = sorted(hand, key=lambda p: p.point)[:required_count or 1]
    if verbose:
        summary = ', '.join(p.name for p in fallback)
        print(f"🤖 BOT has no valid play. Discards lowest pieces: {summary}")
        print(f"    🔍 Final play: {[p.name for p in fallback]}")
        print(f"    🧠 Hand left: {[p.name for p in hand]}")

    return fallback
