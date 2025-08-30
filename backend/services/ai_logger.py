"""
AI Logger for Debug Mode
Provides structured logging for AI decision analysis
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from .ai_bug_detector import AIBugDetector, BugSeverity
except ImportError:
    # Running as script, use absolute import
    from backend.services.ai_bug_detector import AIBugDetector, BugSeverity

logger = logging.getLogger(__name__)

class AILogger:
    """Structured logger for AI decisions and game events"""
    
    def __init__(self, log_level: str = 'summary', output_file: Optional[str] = None):
        self.log_level = log_level
        self.current_game_id = None
        self.events = []
        self.bug_detector = AIBugDetector()
        
        # Setup output file
        if output_file:
            self.output_path = Path(output_file)
        else:
            # Default path with timestamp
            log_dir = Path("logs/ai_debug")
            log_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Add microseconds to ensure uniqueness when games run fast
            microseconds = datetime.now().microsecond
            self.output_path = log_dir / f"game_{timestamp}_{microseconds:06d}.json"
            
        # Log levels
        self.LOG_LEVELS = {
            'summary': 1,    # Just game outcomes
            'decision': 2,   # + AI decisions
            'detailed': 3    # + full context
        }
        
        self.current_level = self.LOG_LEVELS.get(log_level, 1)
        
    def should_log(self, level: str) -> bool:
        """Check if event should be logged at current verbosity"""
        return self.LOG_LEVELS.get(level, 1) <= self.current_level
        
    def log_event(self, event_data: Dict[str, Any]):
        """Log a generic event"""
        event_data['timestamp'] = datetime.utcnow().isoformat()
        event_data['game_id'] = self.current_game_id
        
        self.events.append(event_data)
        
        # Write to file if detailed logging
        if self.current_level >= 3:
            self._append_to_file(event_data)
            
    def log_game_start(self, game_id: str, game):
        """Log game initialization"""
        self.current_game_id = game_id
        
        if self.should_log('summary'):
            # Get initial hands for each player
            initial_hands = {}
            for player in game.players:
                initial_hands[player.name] = [
                    f"{p.name}_{p.color}" for p in player.hand
                ]
                
            event = {
                'event': 'game_start',
                'game_id': game_id,
                'players': [p.name for p in game.players],
                'round_starter': game.round_starter,
                'initial_hands': initial_hands if self.should_log('detailed') else None
            }
            
            self.log_event(event)
            
    def log_declaration(self, player_name: str, declaration_data: Dict):
        """Log AI declaration decision"""
        if not self.should_log('decision'):
            return
            
        event = {
            'event': 'declaration',
            'player': player_name,
            'phase_data': {
                'position': declaration_data.get('position_in_order'),
                'previous_declarations': declaration_data.get('previous_declarations'),
                'is_starter': declaration_data.get('is_starter'),
                'zero_streak': declaration_data.get('zero_streak', 0)
            },
            'hand_analysis': declaration_data.get('hand_analysis') if self.should_log('detailed') else None,
            'decision_factors': declaration_data.get('decision_factors'),
            'decision': {
                'declared_value': declaration_data.get('final_declaration'),
                'reasoning': declaration_data.get('reasoning'),
                'confidence': declaration_data.get('confidence', 0)
            }
        }
        
        # Check for bugs
        bugs = self.bug_detector.check_declaration_bugs(player_name, declaration_data)
        if bugs:
            event['bugs_detected'] = [bug.to_dict() for bug in bugs]
            for bug in bugs:
                self.log_bug_detected(bug.bug_type, bug.to_dict())
        
        self.log_event(event)
        
    def log_turn_play(self, player_name: str, play_data: Dict):
        """Log AI turn play decision"""
        if not self.should_log('decision'):
            return
            
        event = {
            'event': 'turn_play',
            'player': player_name,
            'turn_context': {
                'turn_number': play_data.get('turn_number'),
                'required_pieces': play_data.get('required_piece_count'),
                'current_winner': play_data.get('current_winner'),
                'am_starter': play_data.get('am_i_starter', False)
            },
            'my_situation': {
                'captured_piles': play_data.get('my_captured'),
                'declared_target': play_data.get('my_declared'),
                'piles_needed': play_data.get('piles_needed'),
                'pieces_remaining': play_data.get('pieces_remaining')
            },
            'play_decision': {
                'selected_play': play_data.get('selected_play'),
                'play_type': play_data.get('play_type'),
                'pieces': play_data.get('pieces_played'),
                'reasoning': play_data.get('reasoning')
            }
        }
        
        # Add detailed info if enabled
        if self.should_log('detailed'):
            event['available_plays'] = play_data.get('available_plays', [])
            event['hand_before'] = play_data.get('hand_before', [])
            
        self.log_event(event)
        
    def log_round_end(self, round_number: int, round_summary: Dict):
        """Log round completion"""
        if not self.should_log('summary'):
            return
            
        event = {
            'event': 'round_end',
            'round_number': round_number,
            'round_summary': round_summary,
            'player_performance': {}
        }
        
        # Add performance metrics
        for player_name, stats in round_summary.get('player_stats', {}).items():
            event['player_performance'][player_name] = {
                'declared': stats.get('declared'),
                'captured': stats.get('captured'),
                'accuracy': stats.get('accuracy'),
                'score_gained': stats.get('score_gained')
            }
            
        self.log_event(event)
        
    def log_game_end(self, game_id: str, winners: List[str], final_scores: Dict[str, int], 
                     rounds_played: int, duration: float):
        """Log game completion"""
        if not self.should_log('summary'):
            return
            
        event = {
            'event': 'game_end',
            'game_id': game_id,
            'winner': winners[0] if winners else None,
            'final_scores': final_scores,
            'rounds_played': rounds_played,
            'duration_seconds': duration,
            'game_summary': self._generate_game_summary()
        }
        
        self.log_event(event)
        
        # Generate and log bug report if any bugs found
        if self.bug_detector.bugs_detected:
            bug_report = self.bug_detector.generate_bug_report()
            logger.info(f"\n{bug_report}")
            
        # Save all events to file
        self._save_to_file()
        
    def log_bug_detected(self, bug_type: str, details: Dict):
        """Log detected bug or anomaly"""
        event = {
            'event': 'bug_detected',
            'bug_type': bug_type,
            'severity': details.get('severity', 'medium'),
            'player': details.get('player'),
            'phase': details.get('phase'),
            'description': details.get('description'),
            'context': details.get('context') if self.should_log('detailed') else None
        }
        
        self.log_event(event)
        logger.warning(f"BUG DETECTED: {bug_type} - {details.get('description')}")
        
    def _generate_game_summary(self) -> Dict:
        """Generate summary statistics for the game"""
        if not self.events:
            return {}
            
        # Calculate declaration accuracy
        declarations = [e for e in self.events if e.get('event') == 'declaration']
        round_ends = [e for e in self.events if e.get('event') == 'round_end']
        
        player_stats = {}
        
        # Process each player
        for round_end in round_ends:
            for player, perf in round_end.get('player_performance', {}).items():
                if player not in player_stats:
                    player_stats[player] = {
                        'total_declared': 0,
                        'total_captured': 0,
                        'perfect_rounds': 0,
                        'rounds_played': 0
                    }
                    
                stats = player_stats[player]
                stats['total_declared'] += perf.get('declared', 0)
                stats['total_captured'] += perf.get('captured', 0)
                stats['rounds_played'] += 1
                
                if perf.get('declared') == perf.get('captured'):
                    stats['perfect_rounds'] += 1
                    
        # Calculate accuracy
        for player, stats in player_stats.items():
            if stats['total_declared'] > 0:
                stats['declaration_accuracy'] = stats['total_captured'] / stats['total_declared']
            else:
                stats['declaration_accuracy'] = 0
                
        # Add bug summary
        bug_summary = self.bug_detector.get_bug_summary()
        performance_analysis = self.bug_detector.analyze_game_performance({
            'player_statistics': player_stats
        })
        
        return {
            'player_statistics': player_stats,
            'total_events': len(self.events),
            'bugs_detected': len([e for e in self.events if e.get('event') == 'bug_detected']),
            'bug_summary': bug_summary,
            'performance_analysis': performance_analysis
        }
        
    def _append_to_file(self, event_data: Dict):
        """Append event to file immediately (for detailed logging)"""
        try:
            with open(self.output_path, 'a') as f:
                f.write(json.dumps(event_data) + '\n')
        except Exception as e:
            logger.error(f"Failed to write event to file: {e}")
            
    def _save_to_file(self):
        """Save all events to output file"""
        try:
            # Create output directory if needed
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save as pretty-printed JSON
            output_data = {
                'game_id': self.current_game_id,
                'timestamp': datetime.utcnow().isoformat(),
                'log_level': self.log_level,
                'events': self.events
            }
            
            with open(self.output_path, 'w') as f:
                json.dump(output_data, f, indent=2)
                
            logger.info(f"Game log saved to: {self.output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save game log: {e}")