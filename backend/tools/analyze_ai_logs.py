#!/usr/bin/env python3
"""
AI Log Analyzer
Parses AI debug logs to generate insights and statistics
"""

import argparse
import json
import sys
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import statistics

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.ai_bug_detector import BugSeverity


class AILogAnalyzer:
    """Analyzes AI game logs for patterns and insights"""
    
    def __init__(self):
        self.games = []
        self.all_events = []
        self.bugs_by_type = Counter()
        self.bugs_by_player = Counter()
        self.player_stats = defaultdict(lambda: {
            'games_played': 0,
            'games_won': 0,
            'total_score': 0,
            'declarations': [],
            'captures': [],
            'perfect_rounds': 0,
            'total_rounds': 0
        })
        
    def load_log_file(self, filepath: Path):
        """Load and parse a single log file"""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                
            # Try to parse as JSON
            try:
                data = json.loads(content)
                if isinstance(data, dict) and 'events' in data:
                    # New format with all events in one object
                    self.process_game_log(data)
                elif isinstance(data, list):
                    # List of events
                    self.process_events_list(data)
            except json.JSONDecodeError:
                # Try line-by-line JSON
                for line in content.strip().split('\n'):
                    if line:
                        try:
                            event = json.loads(line)
                            self.all_events.append(event)
                        except:
                            pass
                            
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            
    def process_game_log(self, game_data: Dict):
        """Process a complete game log"""
        events = game_data.get('events', [])
        game_info = {
            'events': events,
            'game_id': None,
            'winner': None,
            'final_scores': {},
            'rounds_played': 0,
            'bugs_detected': []
        }
        
        for event in events:
            self.all_events.append(event)
            
            if event['event'] == 'game_start':
                game_info['game_id'] = event.get('game_id')
                
            elif event['event'] == 'game_end':
                game_info['winner'] = event.get('winner')
                game_info['final_scores'] = event.get('final_scores', {})
                game_info['rounds_played'] = event.get('rounds_played', 0)
                
            elif event['event'] == 'bug_detected':
                game_info['bugs_detected'].append(event)
                self.bugs_by_type[event.get('bug_type')] += 1
                self.bugs_by_player[event.get('player')] += 1
                
        self.games.append(game_info)
        self._update_player_stats(game_info)
        
    def process_events_list(self, events: List[Dict]):
        """Process a list of events"""
        # Group events by game
        current_game = None
        
        for event in events:
            self.all_events.append(event)
            
            if event['event'] == 'game_start':
                if current_game:
                    self.games.append(current_game)
                    self._update_player_stats(current_game)
                    
                current_game = {
                    'events': [event],
                    'game_id': event.get('game_id'),
                    'winner': None,
                    'final_scores': {},
                    'rounds_played': 0,
                    'bugs_detected': []
                }
            elif current_game:
                current_game['events'].append(event)
                
                if event['event'] == 'game_end':
                    current_game['winner'] = event.get('winner')
                    current_game['final_scores'] = event.get('final_scores', {})
                    current_game['rounds_played'] = event.get('rounds_played', 0)
                    
                elif event['event'] == 'bug_detected':
                    current_game['bugs_detected'].append(event)
                    self.bugs_by_type[event.get('bug_type')] += 1
                    self.bugs_by_player[event.get('player')] += 1
                    
        if current_game:
            self.games.append(current_game)
            self._update_player_stats(current_game)
            
    def _update_player_stats(self, game_info: Dict):
        """Update player statistics from a game"""
        # Update win counts and scores
        for player, score in game_info['final_scores'].items():
            self.player_stats[player]['games_played'] += 1
            self.player_stats[player]['total_score'] += score
            
            if player == game_info['winner']:
                self.player_stats[player]['games_won'] += 1
                
        # Process declarations and captures from events
        for event in game_info['events']:
            if event['event'] == 'declaration':
                player = event.get('player')
                decision = event.get('decision', {})
                declared = decision.get('declared_value', 0)
                if player:
                    self.player_stats[player]['declarations'].append(declared)
                
            elif event['event'] == 'round_end':
                for player, perf in event.get('player_performance', {}).items():
                    self.player_stats[player]['declarations'].append(perf.get('declared', 0))
                    self.player_stats[player]['captures'].append(perf.get('captured', 0))
                    self.player_stats[player]['total_rounds'] += 1
                    if perf.get('declared') == perf.get('captured'):
                        self.player_stats[player]['perfect_rounds'] += 1
                        
    def generate_report(self) -> str:
        """Generate comprehensive analysis report"""
        report = []
        
        report.append("=" * 60)
        report.append("AI GAME ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"\nTotal Games Analyzed: {len(self.games)}")
        report.append(f"Total Events Processed: {len(self.all_events)}")
        
        # Player Performance
        report.append("\n\nPLAYER PERFORMANCE")
        report.append("-" * 30)
        
        for player in sorted(self.player_stats.keys()):
            stats = self.player_stats[player]
            if stats['games_played'] > 0:
                win_rate = (stats['games_won'] / stats['games_played']) * 100
                avg_score = stats['total_score'] / stats['games_played']
                
                report.append(f"\n{player}:")
                report.append(f"  Games: {stats['games_played']}")
                report.append(f"  Wins: {stats['games_won']} ({win_rate:.1f}%)")
                report.append(f"  Avg Score: {avg_score:.1f}")
                
                if stats['declarations']:
                    avg_declared = statistics.mean(stats['declarations'])
                    report.append(f"  Avg Declared: {avg_declared:.1f}")
                    
                if stats['captures']:
                    avg_captured = statistics.mean(stats['captures'])
                    report.append(f"  Avg Captured: {avg_captured:.1f}")
                    
                if stats['total_rounds'] > 0:
                    accuracy = (stats['perfect_rounds'] / stats['total_rounds']) * 100
                    report.append(f"  Declaration Accuracy: {accuracy:.1f}%")
                    
        # Bug Analysis
        if self.bugs_by_type:
            report.append("\n\nBUG ANALYSIS")
            report.append("-" * 30)
            report.append(f"Total Bugs Detected: {sum(self.bugs_by_type.values())}")
            
            report.append("\nBy Type:")
            for bug_type, count in self.bugs_by_type.most_common():
                report.append(f"  {bug_type}: {count}")
                
            report.append("\nBy Player:")
            for player, count in self.bugs_by_player.most_common():
                report.append(f"  {player}: {count}")
                
        # Game Patterns
        report.append("\n\nGAME PATTERNS")
        report.append("-" * 30)
        
        if self.games:
            rounds_per_game = [g['rounds_played'] for g in self.games if g['rounds_played'] > 0]
            if rounds_per_game:
                report.append(f"Avg Rounds per Game: {statistics.mean(rounds_per_game):.1f}")
                report.append(f"Min/Max Rounds: {min(rounds_per_game)}/{max(rounds_per_game)}")
                
            # Score distributions
            all_scores = []
            for game in self.games:
                all_scores.extend(game['final_scores'].values())
                
            if all_scores:
                report.append(f"\nScore Distribution:")
                report.append(f"  Mean: {statistics.mean(all_scores):.1f}")
                report.append(f"  Median: {statistics.median(all_scores):.1f}")
                report.append(f"  Min/Max: {min(all_scores)}/{max(all_scores)}")
                
        # Declaration Patterns
        report.append("\n\nDECLARATION PATTERNS")
        report.append("-" * 30)
        
        declaration_events = [e for e in self.all_events if e['event'] == 'declaration']
        if declaration_events:
            by_position = defaultdict(list)
            
            for event in declaration_events:
                position = event['phase_data'].get('position', 0)
                declared = event['decision'].get('declared_value', 0)
                by_position[position].append(declared)
                
            for pos in sorted(by_position.keys()):
                values = by_position[pos]
                avg = statistics.mean(values)
                report.append(f"Position {pos}: avg {avg:.2f}, range {min(values)}-{max(values)}")
                
        return '\n'.join(report)
        
    def export_stats(self, output_file: str):
        """Export statistics to CSV format"""
        import csv
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['Player', 'Games', 'Wins', 'Win%', 'AvgScore', 
                           'AvgDeclared', 'AvgCaptured', 'Accuracy%'])
            
            # Player data
            for player in sorted(self.player_stats.keys()):
                stats = self.player_stats[player]
                if stats['games_played'] > 0:
                    win_rate = (stats['games_won'] / stats['games_played']) * 100
                    avg_score = stats['total_score'] / stats['games_played']
                    avg_declared = statistics.mean(stats['declarations']) if stats['declarations'] else 0
                    avg_captured = statistics.mean(stats['captures']) if stats['captures'] else 0
                    accuracy = (stats['perfect_rounds'] / stats['total_rounds']) * 100 if stats['total_rounds'] > 0 else 0
                    
                    writer.writerow([
                        player,
                        stats['games_played'],
                        stats['games_won'],
                        f"{win_rate:.1f}",
                        f"{avg_score:.1f}",
                        f"{avg_declared:.1f}",
                        f"{avg_captured:.1f}",
                        f"{accuracy:.1f}"
                    ])


def main():
    parser = argparse.ArgumentParser(
        description='Analyze AI game logs for patterns and insights'
    )
    
    parser.add_argument(
        'files',
        nargs='+',
        help='Log files to analyze (JSON format)'
    )
    
    parser.add_argument(
        '--export-stats',
        type=str,
        help='Export statistics to CSV file'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Save report to file instead of printing'
    )
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = AILogAnalyzer()
    
    # Load all log files
    for filepath in args.files:
        path = Path(filepath)
        if path.exists():
            print(f"Loading {path}...")
            analyzer.load_log_file(path)
        else:
            print(f"Warning: {path} not found")
            
    # Generate report
    report = analyzer.generate_report()
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)
        
    # Export stats if requested
    if args.export_stats:
        analyzer.export_stats(args.export_stats)
        print(f"\nStatistics exported to {args.export_stats}")


if __name__ == "__main__":
    main()