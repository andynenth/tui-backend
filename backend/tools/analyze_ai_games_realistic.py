#!/usr/bin/env python3
"""
Realistic AI Game Analyzer
Analyzes AI game logs using ONLY data that is actually available
No assumptions about future capabilities
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict, Counter


class RealisticAIAnalyzer:
    """Analyzes AI games using only currently available data"""

    def __init__(self, log_paths: List[Path]):
        self.games = []
        self.load_games(log_paths)

    def load_games(self, log_paths: List[Path]):
        """Load game logs from files"""
        for path in log_paths:
            try:
                with open(path, "r") as f:
                    game_data = json.load(f)
                    self.games.append(game_data)
            except Exception as e:
                print(f"Error loading {path}: {e}")

    def analyze_all(self) -> Dict[str, Any]:
        """Run all available analyses"""
        if not self.games:
            return {"error": "No games loaded"}

        return {
            "total_games": len(self.games),
            "declaration_analysis": self.analyze_declarations(),
            "play_patterns": self.analyze_play_patterns(),
            "hand_strength": self.analyze_hand_strength(),
            "rule_violations": self.analyze_violations(),
            "performance_metrics": self.calculate_performance(),
        }

    def analyze_declarations(self) -> Dict[str, Any]:
        """Analyze declaration patterns from available data"""
        position_stats = defaultdict(lambda: {"total": 0, "sum_declared": 0})
        zero_streak_usage = Counter()
        accuracy_by_position = defaultdict(list)

        for game in self.games:
            # Get declaration events
            declarations = [e for e in game["events"] if e["event"] == "declaration"]
            round_ends = [e for e in game["events"] if e["event"] == "round_end"]

            # Track position impact
            for decl in declarations:
                position = decl["phase_data"]["position"]
                value = decl["decision"]["declared_value"]
                player = decl["player"]

                position_stats[position]["total"] += 1
                position_stats[position]["sum_declared"] += value

                # Track zero streaks
                zero_streak = decl["phase_data"].get("zero_streak", 0)
                if value == 0:
                    zero_streak_usage[zero_streak] += 1

            # Calculate accuracy by position
            for round_end in round_ends:
                for player, perf in round_end["player_performance"].items():
                    # Find this player's declaration position
                    player_decls = [d for d in declarations if d["player"] == player]
                    if player_decls:
                        position = player_decls[0]["phase_data"]["position"]
                        accuracy = perf["accuracy"]
                        accuracy_by_position[position].append(accuracy)

        # Calculate averages
        position_analysis = {}
        for pos, stats in position_stats.items():
            position_analysis[f"position_{pos}"] = {
                "avg_declared": stats["sum_declared"] / stats["total"]
                if stats["total"] > 0
                else 0,
                "declaration_count": stats["total"],
                "avg_accuracy": sum(accuracy_by_position[pos])
                / len(accuracy_by_position[pos])
                if accuracy_by_position[pos]
                else 0,
            }

        return {
            "position_impact": position_analysis,
            "zero_streak_patterns": dict(zero_streak_usage),
            "starter_advantage": position_analysis.get("position_0", {}).get(
                "avg_accuracy", 0
            ),
        }

    def analyze_play_patterns(self) -> Dict[str, Any]:
        """Analyze play patterns from turn decisions"""
        opener_usage = {"early_game": 0, "mid_game": 0, "late_game": 0}
        play_types = Counter()
        must_win_plays = []
        disposal_plays = []

        # New: Turn-level analysis
        turn_win_rates = Counter()  # Track which play types win turns
        combo_effectiveness = defaultdict(lambda: {"played": 0, "won": 0})

        for game in self.games:
            turn_plays = [e for e in game["events"] if e["event"] == "turn_play"]
            turn_results = [e for e in game["events"] if e["event"] == "turn_complete"]

            # Create turn result lookup
            turn_winners = {}
            for result in turn_results:
                if result.get("winner"):
                    turn_winners[result["turn_number"]] = {
                        "player": result["winner"]["player"],
                        "play_type": result["winner"]["play_type"],
                        "points": result["winner"]["points"],
                    }

            for play in turn_plays:
                # Categorize by game stage
                pieces_remaining = play["my_situation"]["pieces_remaining"]
                play_type = play["play_decision"]["play_type"]
                selected = play["play_decision"]["selected_play"]

                # Track play types
                play_types[play_type] += 1

                # Check for opener usage (pieces worth >10 points)
                if any("GENERAL" in p or "ADVISOR" in p for p in selected):
                    if pieces_remaining >= 6:
                        opener_usage["early_game"] += 1
                    elif pieces_remaining >= 3:
                        opener_usage["mid_game"] += 1
                    else:
                        opener_usage["late_game"] += 1

                # Track must-win situations
                piles_needed = play["my_situation"]["piles_needed"]
                if piles_needed > 0 and pieces_remaining <= piles_needed * 2:
                    must_win_plays.append(
                        {
                            "player": play["player"],
                            "piles_needed": piles_needed,
                            "pieces_left": pieces_remaining,
                            "play_type": play_type,
                        }
                    )

                # Track disposal plays (invalid plays when at target)
                captured = play["my_situation"]["captured_piles"]
                declared = play["my_situation"]["declared_target"]
                if captured >= declared and play_type == "INVALID":
                    disposal_plays.append(
                        {"player": play["player"], "pieces": selected}
                    )

            # Analyze turn results for win rates
            for result in turn_results:
                for play in result.get("plays", []):
                    play_type = play["play_type"]
                    combo_effectiveness[play_type]["played"] += 1

                    # Check if this player won
                    if (
                        result.get("winner")
                        and play["player"] == result["winner"]["player"]
                    ):
                        combo_effectiveness[play_type]["won"] += 1
                        turn_win_rates[play_type] += 1

        # Calculate win rates
        combo_win_rates = {}
        for combo, stats in combo_effectiveness.items():
            if stats["played"] > 0:
                combo_win_rates[combo] = {
                    "win_rate": (stats["won"] / stats["played"]) * 100,
                    "total_played": stats["played"],
                    "total_won": stats["won"],
                }

        return {
            "opener_timing": opener_usage,
            "play_type_distribution": dict(play_types),
            "must_win_situations": len(must_win_plays),
            "disposal_strategies": len(disposal_plays),
            "disposal_rate": len(disposal_plays) / sum(play_types.values())
            if play_types
            else 0,
            "turn_win_rates": dict(turn_win_rates),
            "combo_effectiveness": combo_win_rates,
        }

    def analyze_hand_strength(self) -> Dict[str, Any]:
        """Analyze initial hand quality"""
        weak_hands = []
        hand_strengths = []
        piece_distribution = Counter()

        for game in self.games:
            # Get initial hands from game start or round start
            starts = [
                e for e in game["events"] if e["event"] in ["game_start", "round_start"]
            ]

            for start in starts:
                if "initial_hands" in start and start["initial_hands"]:
                    for player, hand in start["initial_hands"].items():
                        # Calculate hand strength
                        strength = 0
                        has_strong = False

                        for piece in hand:
                            # Extract piece type
                            piece_type = piece.split("_")[0]
                            piece_distribution[piece_type] += 1

                            # Estimate piece value
                            if "GENERAL" in piece:
                                strength += 14
                                has_strong = True
                            elif "ADVISOR" in piece:
                                strength += 11 if "RED" in piece else 12
                                has_strong = True
                            elif "ELEPHANT" in piece:
                                strength += 10 if "RED" in piece else 9
                                has_strong = True
                            elif "CHARIOT" in piece:
                                strength += 8 if "RED" in piece else 7
                            elif "HORSE" in piece:
                                strength += 6 if "RED" in piece else 5
                            elif "CANNON" in piece:
                                strength += 4 if "RED" in piece else 3
                            else:  # SOLDIER
                                strength += 2 if "RED" in piece else 1

                        hand_strengths.append(strength)
                        if not has_strong:
                            weak_hands.append(
                                {
                                    "player": player,
                                    "hand_strength": strength,
                                    "round": start.get("round_number", 1),
                                }
                            )

        avg_strength = (
            sum(hand_strengths) / len(hand_strengths) if hand_strengths else 0
        )

        return {
            "weak_hand_frequency": len(weak_hands),
            "weak_hand_percentage": (len(weak_hands) / len(hand_strengths) * 100)
            if hand_strengths
            else 0,
            "average_hand_strength": avg_strength,
            "piece_distribution": dict(piece_distribution),
            "weakest_hands": sorted(weak_hands, key=lambda x: x["hand_strength"])[:5],
        }

    def analyze_violations(self) -> Dict[str, Any]:
        """Analyze rule violations from bug detection"""
        violations_by_type = Counter()
        violations_by_player = Counter()
        violations_by_phase = Counter()

        for game in self.games:
            bugs = [e for e in game["events"] if e["event"] == "bug_detected"]

            for bug in bugs:
                violations_by_type[bug["bug_type"]] += 1
                violations_by_player[bug["player"]] += 1
                violations_by_phase[bug["phase"]] += 1

        return {
            "total_violations": sum(violations_by_type.values()),
            "by_type": dict(violations_by_type),
            "by_player": dict(violations_by_player),
            "by_phase": dict(violations_by_phase),
        }

    def calculate_performance(self) -> Dict[str, Any]:
        """Calculate performance metrics from available data"""
        player_stats = defaultdict(
            lambda: {
                "games": 0,
                "wins": 0,
                "total_score": 0,
                "perfect_rounds": 0,
                "total_rounds": 0,
            }
        )

        for game in self.games:
            # Get game end event
            game_ends = [e for e in game["events"] if e["event"] == "game_end"]
            if not game_ends:
                continue

            game_end = game_ends[0]
            winner = game_end["winner"]

            # Update stats
            for player, score in game_end["final_scores"].items():
                player_stats[player]["games"] += 1
                player_stats[player]["total_score"] += score
                if player == winner:
                    player_stats[player]["wins"] += 1

            # Get round performance
            round_ends = [e for e in game["events"] if e["event"] == "round_end"]
            for round_end in round_ends:
                for player, perf in round_end["player_performance"].items():
                    player_stats[player]["total_rounds"] += 1
                    if perf["accuracy"] == 1.0:
                        player_stats[player]["perfect_rounds"] += 1

        # Calculate derived metrics
        performance = {}
        for player, stats in player_stats.items():
            performance[player] = {
                "win_rate": (stats["wins"] / stats["games"] * 100)
                if stats["games"] > 0
                else 0,
                "avg_score": stats["total_score"] / stats["games"]
                if stats["games"] > 0
                else 0,
                "perfect_round_rate": (
                    stats["perfect_rounds"] / stats["total_rounds"] * 100
                )
                if stats["total_rounds"] > 0
                else 0,
                "games_played": stats["games"],
            }

        return performance


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python analyze_ai_games_realistic.py <log_file_or_directory>...")
        sys.exit(1)

    # Collect log files
    log_files = []
    for arg in sys.argv[1:]:
        path = Path(arg)
        if path.is_file() and path.suffix == ".json":
            log_files.append(path)
        elif path.is_dir():
            log_files.extend(path.glob("*.json"))

    if not log_files:
        print("No JSON log files found")
        sys.exit(1)

    print(f"Analyzing {len(log_files)} game logs...")

    # Run analysis
    analyzer = RealisticAIAnalyzer(log_files)
    results = analyzer.analyze_all()

    # Print results
    print("\n" + "=" * 60)
    print("AI GAME ANALYSIS RESULTS")
    print("=" * 60)

    print(f"\nTotal Games Analyzed: {results['total_games']}")

    # Declaration Analysis
    print("\n--- DECLARATION PATTERNS ---")
    decl = results["declaration_analysis"]
    for pos_key, stats in decl["position_impact"].items():
        print(
            f"{pos_key}: avg_declared={stats['avg_declared']:.1f}, "
            f"accuracy={stats['avg_accuracy']:.1%}"
        )
    print(f"Zero streak usage: {decl['zero_streak_patterns']}")

    # Play Patterns
    print("\n--- PLAY PATTERNS ---")
    plays = results["play_patterns"]
    print(f"Opener timing: {plays['opener_timing']}")
    print(f"Play types: {plays['play_type_distribution']}")
    print(f"Must-win situations: {plays['must_win_situations']}")
    print(f"Disposal rate: {plays['disposal_rate']:.1%}")

    # New: Turn win rates
    print("\n--- TURN WIN RATES ---")
    if plays.get("combo_effectiveness"):
        for combo, stats in sorted(
            plays["combo_effectiveness"].items(),
            key=lambda x: x[1]["win_rate"],
            reverse=True,
        ):
            print(
                f"{combo}: {stats['win_rate']:.1f}% win rate "
                f"({stats['total_won']}/{stats['total_played']} turns won)"
            )

    # Hand Strength
    print("\n--- HAND STRENGTH ---")
    hands = results["hand_strength"]
    print(
        f"Weak hand frequency: {hands['weak_hand_frequency']} ({hands['weak_hand_percentage']:.1f}%)"
    )
    print(f"Average hand strength: {hands['average_hand_strength']:.1f}")

    # Violations
    print("\n--- RULE VIOLATIONS ---")
    violations = results["rule_violations"]
    print(f"Total violations: {violations['total_violations']}")
    if violations["by_type"]:
        print(f"By type: {violations['by_type']}")

    # Performance
    print("\n--- PERFORMANCE METRICS ---")
    for player, metrics in results["performance_metrics"].items():
        print(
            f"{player}: Win rate={metrics['win_rate']:.1f}%, "
            f"Avg score={metrics['avg_score']:.1f}, "
            f"Perfect rounds={metrics['perfect_round_rate']:.1f}%"
        )


if __name__ == "__main__":
    main()
