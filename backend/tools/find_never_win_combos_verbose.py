#!/usr/bin/env python3
"""
Find evidence of never-win combos being played in AI game logs - with detailed diagnostics
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import constants for piece values
from backend.engine.constants import PIECE_POINTS


def is_never_win_combo(play_type, pieces):
    """Check if a play is a never-win combo"""

    if play_type == "STRAIGHT":
        # Check if all pieces are BLACK (odd points)
        all_black = all(p["point"] % 2 == 1 for p in pieces)
        if all_black and len(pieces) >= 3:
            # Check if it's the minimum straight (3,5,7)
            points = sorted([p["point"] for p in pieces])
            if points[:3] == [3, 5, 7]:
                return True

    elif play_type == "PAIR":
        # Check if it's SOLDIER_BLACK pair (1+1=2)
        if len(pieces) == 2 and all(p["point"] == 1 for p in pieces):
            return True

    elif play_type in ["THREE_OF_A_KIND", "FOUR_OF_A_KIND", "FIVE_OF_A_KIND"]:
        # Check if all are SOLDIER_BLACK (point value 1)
        if all(p["point"] == 1 for p in pieces):
            return True

    return False


def analyze_game_log(filepath, verbose=True):
    """Analyze a single game log for never-win combos"""
    never_win_plays = []
    stats = {
        "rounds_found": 0,
        "turns_found": 0,
        "plays_found": 0,
        "events_checked": 0,
        "turn_play_events": 0,
        "turn_complete_events": 0,
        "has_piece_details": False,
    }

    current_round = 1  # Track current round number

    try:
        with open(filepath, "r") as f:
            data = json.load(f)

        game_id = data.get("game_id", "Unknown")

        # Look for play events in the log
        for event in data.get("events", []):
            stats["events_checked"] += 1

            # Track round changes
            if event.get("event") == "round_end":
                stats["rounds_found"] += 1
                current_round += 1

            # Check turn_complete events which contain plays
            elif event.get("event") == "turn_complete":
                stats["turn_complete_events"] += 1
                stats["turns_found"] += 1
                turn_number = event.get("turn_number", "Unknown")
                required_pieces = event.get("required_pieces", "Unknown")
                starter = event.get("starter", "Unknown")

                # Check each player's play in this turn
                for play in event.get("plays", []):
                    player = play.get("player")
                    play_type = play.get("play_type")
                    pieces_played = play.get("pieces_played", [])

                    # Skip invalid plays
                    if not play.get("is_valid", False):
                        continue

                    # Convert piece names to piece objects with point values
                    if pieces_played and len(pieces_played) > 0:
                        stats["has_piece_details"] = True
                        stats["plays_found"] += 1

                        # Create piece objects with point values
                        pieces = []
                        for piece_name in pieces_played:
                            if piece_name in PIECE_POINTS:
                                pieces.append(
                                    {
                                        "name": piece_name,
                                        "point": PIECE_POINTS[piece_name],
                                    }
                                )

                        if is_never_win_combo(play_type, pieces):
                            never_win_plays.append(
                                {
                                    "game_id": game_id,
                                    "player": player,
                                    "play_type": play_type,
                                    "pieces": pieces,
                                    "turn": turn_number,
                                    "round": current_round,
                                    "required_pieces": required_pieces,
                                    "starter": starter,
                                    "is_starter": player == starter,
                                }
                            )

    except Exception as e:
        print(f"Error processing {filepath}: {e}")

    return never_win_plays, stats


def main():
    # Find all game log files
    log_dir = Path("logs/ai_debug")

    if not log_dir.exists():
        print(f"❌ Log directory '{log_dir}' does not exist!")
        return

    game_files = list(log_dir.glob("game_*.json"))

    print(f"📁 Log directory: {log_dir.absolute()}")
    print(f"📄 Found {len(game_files)} game log files")
    print("=" * 70)

    if not game_files:
        print("❌ No game log files found!")
        return

    all_never_wins = []
    total_stats = {
        "files_with_details": 0,
        "files_without_details": 0,
        "total_rounds": 0,
        "total_turns": 0,
        "total_plays": 0,
        "total_events": 0,
        "files_with_errors": 0,
    }

    # Analyze each file
    for i, filepath in enumerate(game_files):
        print(f"\r⏳ Processing file {i+1}/{len(game_files)}...", end="", flush=True)

        try:
            never_wins, stats = analyze_game_log(filepath)
            all_never_wins.extend(never_wins)

            # Update totals
            total_stats["total_rounds"] += stats["rounds_found"]
            total_stats["total_turns"] += stats["turns_found"]
            total_stats["total_plays"] += stats["plays_found"]
            total_stats["total_events"] += stats["events_checked"]

            if stats["has_piece_details"]:
                total_stats["files_with_details"] += 1
            else:
                total_stats["files_without_details"] += 1

        except Exception as e:
            total_stats["files_with_errors"] += 1

    print("\n" + "=" * 70)

    # Report detailed statistics
    print("\n📊 SCANNING SUMMARY:")
    print(f"  Total files processed: {len(game_files)}")
    print(f"  Files with play details: {total_stats['files_with_details']}")
    print(f"  Files without play details: {total_stats['files_without_details']}")
    print(f"  Files with errors: {total_stats['files_with_errors']}")
    print(f"\n  Total rounds analyzed: {total_stats['total_rounds']}")
    print(f"  Total turns analyzed: {total_stats['total_turns']}")
    print(f"  Total plays analyzed: {total_stats['total_plays']}")
    print(f"  Total events checked: {total_stats['total_events']}")

    # Check if we actually have the data we need
    if total_stats["files_with_details"] == 0:
        print("\n⚠️  WARNING: No files contain detailed play information!")
        print("  The logs appear to be in summary format only.")
        print(
            "  To detect never-win combos, you need detailed game logs with piece information."
        )
        print("\n  To enable detailed logging, ensure the game is run with:")
        print("  - Detailed logging mode enabled")
        print("  - Play events include piece details (point values)")
        return

    # Report findings
    print(f"\n🎯 NEVER-WIN COMBO RESULTS:")
    print(f"  Found {len(all_never_wins)} never-win combo plays")

    if all_never_wins:
        # Group by type
        by_type = defaultdict(list)
        for play in all_never_wins:
            by_type[play["play_type"]].append(play)

        print("\n📋 Breakdown by combo type:")
        for play_type, plays in by_type.items():
            print(f"  {play_type}: {len(plays)} occurrences")

        # Show some examples
        print("\n📌 Example never-win plays (with round/turn details):")
        for i, play in enumerate(all_never_wins[:20]):
            pieces_str = ", ".join(
                [
                    f"{p.get('name', 'Unknown')}({p.get('point', '?')})"
                    for p in play["pieces"]
                ]
            )
            starter_info = " (STARTER)" if play.get("is_starter", False) else ""
            print(
                f"  {i+1}. Game {play['game_id']}, Round {play['round']}, Turn {play['turn']} (req: {play.get('required_pieces', '?')} pieces)"
            )
            print(
                f"      {play['player']}{starter_info} played {play['play_type']}: [{pieces_str}]"
            )

        # Group by player
        by_player = defaultdict(int)
        for play in all_never_wins:
            by_player[play["player"]] += 1

        print("\n👥 Never-win plays by player:")
        for player, count in sorted(by_player.items()):
            print(f"  {player}: {count}")

        # Calculate percentage
        if total_stats["total_plays"] > 0:
            percentage = (len(all_never_wins) / total_stats["total_plays"]) * 100
            print(f"\n📈 Never-win combo rate: {percentage:.2f}% of all plays")

        # Analyze by round
        by_round = defaultdict(int)
        for play in all_never_wins:
            by_round[play["round"]] += 1

        print("\n📅 Never-win plays by round:")
        for round_num in sorted(by_round.keys()):
            print(f"  Round {round_num}: {by_round[round_num]} occurrences")

        # Analyze starter vs non-starter
        starter_plays = sum(
            1 for play in all_never_wins if play.get("is_starter", False)
        )
        non_starter_plays = len(all_never_wins) - starter_plays
        print(f"\n🎯 Starter vs Non-starter:")
        print(
            f"  Starter plays: {starter_plays} ({starter_plays/len(all_never_wins)*100:.1f}%)"
        )
        print(
            f"  Non-starter plays: {non_starter_plays} ({non_starter_plays/len(all_never_wins)*100:.1f}%)"
        )
    else:
        if total_stats["total_plays"] > 0:
            print("\n✅ Good news! No never-win combos found in analyzed plays.")
            print(f"  This suggests the AI is successfully avoiding these combos.")
        else:
            print(
                "\n⚠️  No plays were analyzed - unable to determine if never-win combos exist."
            )


if __name__ == "__main__":
    main()
