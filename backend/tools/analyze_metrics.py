#!/usr/bin/env python3
"""
Extended Metrics Analysis for AI Debug Mode
Analyzes winning scores and game length distributions
"""

import argparse
import json
import sys
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Any
import statistics

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class MetricsAnalyzer:
    """Analyzes extended metrics from AI game logs"""

    def __init__(self):
        self.games = []
        self.winning_scores = []
        self.game_lengths = []
        self.score_by_position = defaultdict(list)  # position -> [final_scores]

    def load_log_file(self, filepath: Path):
        """Load and parse a single log file"""
        try:
            with open(filepath, "r") as f:
                content = f.read()

            # Try to parse as JSON
            try:
                data = json.loads(content)
                if isinstance(data, dict) and "events" in data:
                    self.process_game_log(data)
                elif isinstance(data, list):
                    self.process_events_list(data)
            except json.JSONDecodeError:
                # Try line-by-line JSON
                current_game = None
                for line in content.strip().split("\n"):
                    if line:
                        try:
                            event = json.loads(line)
                            if event["event"] == "game_start":
                                if current_game:
                                    self.process_game_data(current_game)
                                current_game = {
                                    "events": [event],
                                    "game_id": event.get("game_id"),
                                }
                            elif current_game:
                                current_game["events"].append(event)
                                if event["event"] == "game_end":
                                    self.process_game_data(current_game)
                                    current_game = None
                        except:
                            pass

        except Exception as e:
            print(f"Error loading {filepath}: {e}")

    def process_game_log(self, game_data: Dict):
        """Process a complete game log"""
        self.process_game_data(game_data)

    def process_events_list(self, events: List[Dict]):
        """Process a list of events"""
        current_game = None

        for event in events:
            if event["event"] == "game_start":
                if current_game:
                    self.process_game_data(current_game)

                current_game = {
                    "events": [event],
                    "game_id": event.get("game_id"),
                }
            elif current_game:
                current_game["events"].append(event)

                if event["event"] == "game_end":
                    self.process_game_data(current_game)
                    current_game = None

        if current_game:
            self.process_game_data(current_game)

    def process_game_data(self, game_data: Dict):
        """Extract metrics from a single game"""
        events = game_data.get("events", [])
        game_info = {
            "game_id": None,
            "winner": None,
            "final_scores": {},
            "rounds_played": 0,
            "winner_score": 0,
            "positions": {},  # player -> position mapping
        }

        # Track player positions
        player_order = []

        for event in events:
            if event["event"] == "game_start":
                game_info["game_id"] = event.get("game_id")
                player_order = event.get("players", [])
                # Map players to positions (0-based)
                for i, player in enumerate(player_order):
                    game_info["positions"][player] = i

            elif event["event"] == "game_end":
                game_info["winner"] = event.get("winner")
                game_info["final_scores"] = event.get("final_scores", {})
                game_info["rounds_played"] = event.get("rounds_played", 0)

                # Extract winner score
                if game_info["winner"] and game_info["final_scores"]:
                    winner_score = game_info["final_scores"].get(game_info["winner"], 0)
                    game_info["winner_score"] = winner_score
                    self.winning_scores.append(winner_score)

                # Track scores by position
                for player, score in game_info["final_scores"].items():
                    position = game_info["positions"].get(player, -1)
                    if position >= 0:
                        self.score_by_position[position].append(score)

                # Track game length
                if game_info["rounds_played"] > 0:
                    self.game_lengths.append(game_info["rounds_played"])

        self.games.append(game_info)

    def generate_metrics_report(self) -> str:
        """Generate comprehensive metrics report"""
        report = []

        report.append("=" * 60)
        report.append("EXTENDED AI GAME METRICS ANALYSIS")
        report.append("=" * 60)
        report.append(f"\nTotal Games Analyzed: {len(self.games)}")

        # Winning Score Analysis
        if self.winning_scores:
            report.append("\n\nWINNING SCORE DISTRIBUTION")
            report.append("-" * 30)
            report.append(f"Total Winners: {len(self.winning_scores)}")
            report.append(
                f"Average Winning Score: {statistics.mean(self.winning_scores):.1f}"
            )
            report.append(
                f"Median Winning Score: {statistics.median(self.winning_scores):.1f}"
            )
            report.append(
                f"Min/Max Winning Scores: {min(self.winning_scores)}/{max(self.winning_scores)}"
            )

            # Score ranges
            score_ranges = {"0-25": 0, "26-50": 0, "51-75": 0, "76-100": 0, "100+": 0}

            for score in self.winning_scores:
                if score <= 25:
                    score_ranges["0-25"] += 1
                elif score <= 50:
                    score_ranges["26-50"] += 1
                elif score <= 75:
                    score_ranges["51-75"] += 1
                elif score <= 100:
                    score_ranges["76-100"] += 1
                else:
                    score_ranges["100+"] += 1

            report.append("\nWinning Score Ranges:")
            for range_name, count in score_ranges.items():
                percentage = (
                    (count / len(self.winning_scores)) * 100
                    if self.winning_scores
                    else 0
                )
                report.append(f"  {range_name}: {count} games ({percentage:.1f}%)")

            # Most common winning scores
            score_counter = Counter(self.winning_scores)
            report.append("\nMost Common Winning Scores:")
            for score, count in score_counter.most_common(10):
                report.append(f"  {score} points: {count} times")

        # Game Length Analysis
        if self.game_lengths:
            report.append("\n\nGAME LENGTH DISTRIBUTION")
            report.append("-" * 30)
            report.append(
                f"Average Game Length: {statistics.mean(self.game_lengths):.1f} rounds"
            )
            report.append(
                f"Median Game Length: {statistics.median(self.game_lengths)} rounds"
            )
            report.append(
                f"Min/Max Rounds: {min(self.game_lengths)}/{max(self.game_lengths)}"
            )

            # Round distribution
            round_counter = Counter(self.game_lengths)
            report.append("\nRounds Distribution:")
            for rounds in sorted(round_counter.keys()):
                count = round_counter[rounds]
                percentage = (count / len(self.game_lengths)) * 100
                bar = "█" * int(percentage / 2)  # Visual bar
                report.append(
                    f"  {rounds} rounds: {count} games ({percentage:.1f}%) {bar}"
                )

        # Position-based Score Analysis
        if self.score_by_position:
            report.append("\n\nSCORE ANALYSIS BY POSITION")
            report.append("-" * 30)

            for position in sorted(self.score_by_position.keys()):
                scores = self.score_by_position[position]
                if scores:
                    report.append(f"\nPosition {position + 1}:")
                    report.append(f"  Average Score: {statistics.mean(scores):.1f}")
                    report.append(f"  Score Range: {min(scores)} to {max(scores)}")
                    winning_scores = [s for s in scores if s == max(scores)]
                    report.append(
                        f"  Times Won: {len([g for g in self.games if g['positions'].get(g['winner']) == position])}"
                    )

        # Game Patterns
        report.append("\n\nGAME PATTERNS")
        report.append("-" * 30)

        # Quick wins vs long games
        quick_wins = [g for g in self.games if g["rounds_played"] <= 2]
        long_games = [g for g in self.games if g["rounds_played"] >= 5]

        report.append(
            f"Quick Wins (≤2 rounds): {len(quick_wins)} ({len(quick_wins)/len(self.games)*100:.1f}%)"
        )
        report.append(
            f"Long Games (≥5 rounds): {len(long_games)} ({len(long_games)/len(self.games)*100:.1f}%)"
        )

        # Score correlations
        if quick_wins:
            quick_win_scores = [
                g["winner_score"] for g in quick_wins if g["winner_score"] > 0
            ]
            if quick_win_scores:
                report.append(
                    f"Average Quick Win Score: {statistics.mean(quick_win_scores):.1f}"
                )

        if long_games:
            long_game_scores = [
                g["winner_score"] for g in long_games if g["winner_score"] > 0
            ]
            if long_game_scores:
                report.append(
                    f"Average Long Game Score: {statistics.mean(long_game_scores):.1f}"
                )

        return "\n".join(report)

    def export_metrics(self, output_file: str):
        """Export detailed metrics to JSON"""
        metrics = {
            "summary": {
                "total_games": len(self.games),
                "avg_winning_score": statistics.mean(self.winning_scores)
                if self.winning_scores
                else 0,
                "avg_game_length": statistics.mean(self.game_lengths)
                if self.game_lengths
                else 0,
            },
            "winning_scores": {
                "all_scores": self.winning_scores,
                "distribution": Counter(self.winning_scores),
                "statistics": {
                    "mean": statistics.mean(self.winning_scores)
                    if self.winning_scores
                    else 0,
                    "median": statistics.median(self.winning_scores)
                    if self.winning_scores
                    else 0,
                    "min": min(self.winning_scores) if self.winning_scores else 0,
                    "max": max(self.winning_scores) if self.winning_scores else 0,
                },
            },
            "game_lengths": {
                "all_lengths": self.game_lengths,
                "distribution": Counter(self.game_lengths),
                "statistics": {
                    "mean": statistics.mean(self.game_lengths)
                    if self.game_lengths
                    else 0,
                    "median": statistics.median(self.game_lengths)
                    if self.game_lengths
                    else 0,
                    "min": min(self.game_lengths) if self.game_lengths else 0,
                    "max": max(self.game_lengths) if self.game_lengths else 0,
                },
            },
        }

        with open(output_file, "w") as f:
            json.dump(metrics, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze extended metrics from AI game logs"
    )

    parser.add_argument("files", nargs="+", help="Log files to analyze (JSON format)")

    parser.add_argument(
        "--export-metrics", type=str, help="Export detailed metrics to JSON file"
    )

    parser.add_argument(
        "--output", type=str, help="Save report to file instead of printing"
    )

    args = parser.parse_args()

    # Create analyzer
    analyzer = MetricsAnalyzer()

    # Load all log files
    for filepath in args.files:
        path = Path(filepath)
        if path.exists():
            print(f"Loading {path}...")
            analyzer.load_log_file(path)
        else:
            print(f"Warning: {path} not found")

    # Generate report
    report = analyzer.generate_metrics_report()

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)

    # Export metrics if requested
    if args.export_metrics:
        analyzer.export_metrics(args.export_metrics)
        print(f"\nDetailed metrics exported to {args.export_metrics}")


if __name__ == "__main__":
    main()
