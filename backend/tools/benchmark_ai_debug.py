#!/usr/bin/env python3
"""
Benchmark AI Debug Mode Performance
Tests speed, memory usage, and scalability
"""

import argparse
import time
import psutil
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.ai_debug_simple import SimpleAIGame
from backend.services.ai_logger import AILogger


def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def benchmark_games(num_games: int, log_level: str = "summary"):
    """Run games and measure performance"""
    start_time = time.time()
    start_memory = get_memory_usage()

    results = []
    game_times = []

    print(f"Running {num_games} games with log level: {log_level}")
    print(f"Initial memory usage: {start_memory:.1f} MB")

    for i in range(num_games):
        game_start = time.time()

        # Create logger (no file output for speed)
        ai_logger = AILogger(log_level, None)

        # Run game
        game = SimpleAIGame(ai_logger, verbose=False)
        result = game.run_game()

        game_time = time.time() - game_start
        game_times.append(game_time)
        results.append(result)

        # Progress update every 10 games
        if (i + 1) % 10 == 0:
            current_memory = get_memory_usage()
            avg_time = sum(game_times) / len(game_times)
            print(
                f"  Games: {i+1}/{num_games}, "
                f"Avg time: {avg_time:.3f}s, "
                f"Memory: {current_memory:.1f} MB"
            )

    # Final statistics
    total_time = time.time() - start_time
    final_memory = get_memory_usage()
    memory_increase = final_memory - start_memory

    avg_game_time = sum(game_times) / len(game_times)
    min_game_time = min(game_times)
    max_game_time = max(game_times)
    games_per_second = num_games / total_time

    # Game statistics
    total_rounds = sum(r["rounds"] for r in results)
    avg_rounds = total_rounds / num_games

    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"Total games: {num_games}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Games per second: {games_per_second:.2f}")
    print(f"\nGame timing:")
    print(f"  Average: {avg_game_time:.3f}s")
    print(f"  Min: {min_game_time:.3f}s")
    print(f"  Max: {max_game_time:.3f}s")
    print(f"\nMemory usage:")
    print(f"  Start: {start_memory:.1f} MB")
    print(f"  End: {final_memory:.1f} MB")
    print(f"  Increase: {memory_increase:.1f} MB")
    print(f"  Per game: {memory_increase/num_games:.3f} MB")
    print(f"\nGame statistics:")
    print(f"  Avg rounds per game: {avg_rounds:.1f}")
    print(f"  Total rounds played: {total_rounds}")

    return {
        "total_games": num_games,
        "total_time": total_time,
        "games_per_second": games_per_second,
        "avg_game_time": avg_game_time,
        "memory_increase": memory_increase,
        "avg_rounds": avg_rounds,
    }


def benchmark_log_levels():
    """Compare performance across different log levels"""
    print("\nBENCHMARKING LOG LEVELS")
    print("=" * 60)

    levels = ["summary", "decision", "detailed"]
    results = {}

    for level in levels:
        print(f"\nTesting {level} level...")
        result = benchmark_games(50, level)
        results[level] = result

    # Compare results
    print("\n\nLOG LEVEL COMPARISON")
    print("-" * 40)
    print(f"{'Level':<10} {'Games/sec':<12} {'Avg Time':<10} {'Memory':<10}")
    print("-" * 40)

    for level in levels:
        r = results[level]
        print(
            f"{level:<10} {r['games_per_second']:<12.2f} "
            f"{r['avg_game_time']:<10.3f} {r['memory_increase']:<10.1f}"
        )


def stress_test(max_games: int = 1000):
    """Run increasing numbers of games to find limits"""
    print("\nSTRESS TEST")
    print("=" * 60)

    test_sizes = [10, 50, 100, 250, 500, max_games]

    for size in test_sizes:
        print(f"\nTesting {size} games...")
        try:
            result = benchmark_games(size, "summary")

            # Check if performance is degrading
            if result["games_per_second"] < 1.0:
                print(
                    f"WARNING: Performance degraded to {result['games_per_second']:.2f} games/sec"
                )

            # Check memory usage
            if result["memory_increase"] > 1000:  # 1GB
                print(f"WARNING: High memory usage: {result['memory_increase']:.1f} MB")

        except Exception as e:
            print(f"ERROR at {size} games: {e}")
            break


def main():
    parser = argparse.ArgumentParser(description="Benchmark AI Debug Mode performance")

    parser.add_argument(
        "--games",
        type=int,
        default=100,
        help="Number of games to benchmark (default: 100)",
    )

    parser.add_argument(
        "--mode",
        choices=["basic", "levels", "stress"],
        default="basic",
        help="Benchmark mode (default: basic)",
    )

    parser.add_argument(
        "--log-level",
        choices=["summary", "decision", "detailed"],
        default="summary",
        help="Log level for basic mode (default: summary)",
    )

    args = parser.parse_args()

    if args.mode == "basic":
        benchmark_games(args.games, args.log_level)
    elif args.mode == "levels":
        benchmark_log_levels()
    elif args.mode == "stress":
        stress_test(args.games)


if __name__ == "__main__":
    main()
