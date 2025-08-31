"""
AI Bug Detector for Liap Tui
Analyzes AI decisions and detects known bug patterns
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class BugSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BugReport:
    """Represents a detected bug in AI behavior"""
    bug_type: str
    severity: BugSeverity
    player: str
    phase: str
    description: str
    context: Dict[str, Any]
    suggested_fix: str
    
    def to_dict(self) -> Dict:
        return {
            'bug_type': self.bug_type,
            'severity': self.severity.value,
            'player': self.player,
            'phase': self.phase,
            'description': self.description,
            'context': self.context,
            'suggested_fix': self.suggested_fix
        }


class AIBugDetector:
    """Detects known bugs in AI decision making"""
    
    def __init__(self):
        self.bugs_detected: List[BugReport] = []
        
    def check_declaration_bugs(self, player_name: str, declaration_data: Dict) -> List[BugReport]:
        """Check for bugs in declaration phase"""
        bugs = []
        
        # Extract data
        hand_analysis = declaration_data.get('hand_analysis', {})
        decision_factors = declaration_data.get('decision_factors', {})
        final_declaration = declaration_data.get('final_declaration', 0)
        position = declaration_data.get('position_in_order', 0)
        pile_room = decision_factors.get('pile_room', 8)
        previous_declarations = declaration_data.get('previous_declarations', [])
        zero_streak = declaration_data.get('zero_streak', 0)
        
        # Count openers and combos
        openers = sum(1 for play in declaration_data.get('play_list', []) 
                     if play.get('type') == 'opener')
        combos = sum(1 for play in declaration_data.get('play_list', []) 
                    if play.get('type') == 'combo')
        
        # Bug 1: Over-aggressive declarations
        if final_declaration >= 6 and openers + combos < 3:
            bugs.append(BugReport(
                bug_type="over_aggressive_declaration",
                severity=BugSeverity.HIGH,
                player=player_name,
                phase="declaration",
                description=f"Declared {final_declaration} with only {openers} openers and {combos} combos",
                context={
                    'declaration': final_declaration,
                    'openers': openers,
                    'combos': combos,
                    'hand_strength': hand_analysis.get('total_hand_value', 0)
                },
                suggested_fix="Check hand strength before high declarations (need 3+ openers/combos for 6+)"
            ))
            
        # Bug 2: Zero declaration with strong hand
        if final_declaration == 0 and openers >= 2:
            # Check if forced by zero streak
            if zero_streak < 2:  # Not forced to declare non-zero
                bugs.append(BugReport(
                    bug_type="zero_declaration_strong_hand",
                    severity=BugSeverity.MEDIUM,
                    player=player_name,
                    phase="declaration",
                    description=f"Declared 0 with {openers} openers available",
                    context={
                        'declaration': final_declaration,
                        'openers': openers,
                        'zero_streak': zero_streak
                    },
                    suggested_fix="Force minimum declaration (1-2) with 2+ openers"
                ))
                
        # Bug 3: Ignoring pile room constraints
        if position >= 2:  # Third or fourth player
            if final_declaration > pile_room:
                bugs.append(BugReport(
                    bug_type="ignoring_pile_room",
                    severity=BugSeverity.CRITICAL,
                    player=player_name,
                    phase="declaration",
                    description=f"Declared {final_declaration} when pile room is only {pile_room}",
                    context={
                        'declaration': final_declaration,
                        'pile_room': pile_room,
                        'position': position,
                        'previous_declarations': declaration_data.get('previous_declarations', [])
                    },
                    suggested_fix="Respect pile room calculations (max declaration = pile room)"
                ))
                
        # Bug 4: Excessive zero declarations (>2 in a row)
        if zero_streak > 2:
            bugs.append(BugReport(
                bug_type="excessive_zero_declarations",
                severity=BugSeverity.CRITICAL,
                player=player_name,
                phase="declaration",
                description=f"Declared 0 for {zero_streak} times in a row (max allowed: 2)",
                context={
                    'zero_streak': zero_streak,
                    'declaration': final_declaration
                },
                suggested_fix="Enforce rule: cannot declare 0 more than 2 times in a row"
            ))
            
        # Bug 5: Last player declaring sum of 8
        if position == 3:  # Last player (0-indexed)
            total_declared = sum(previous_declarations) + final_declaration
            if total_declared == 8:
                bugs.append(BugReport(
                    bug_type="last_player_sum_8",
                    severity=BugSeverity.CRITICAL,
                    player=player_name,
                    phase="declaration",
                    description=f"Last player declared {final_declaration} making total equal to 8",
                    context={
                        'position': position,
                        'declaration': final_declaration,
                        'previous_declarations': previous_declarations,
                        'total': total_declared
                    },
                    suggested_fix="Last player cannot declare a value that makes total equal to 8"
                ))
                
        self.bugs_detected.extend(bugs)
        return bugs
        
    def check_turn_play_bugs(self, player_name: str, turn_data: Dict) -> List[BugReport]:
        """Check for bugs in turn play phase"""
        bugs = []
        
        # Extract data
        my_captured = turn_data.get('my_captured', 0)
        my_declared = turn_data.get('my_declared', 0)
        selected_play = turn_data.get('selected_play', [])
        play_type = turn_data.get('play_type', '')
        pieces_remaining = turn_data.get('pieces_remaining', 0)
        turn_number = turn_data.get('turn_number', 0)
        hand_before = turn_data.get('hand_before', [])  # Get actual hand if available
        required_count = turn_data.get('required_piece_count', 0)
        
        # Calculate if at target
        at_target = my_captured >= my_declared
        needs_to_win = my_captured < my_declared
        
        # Check if played high-value piece
        if selected_play:
            # Assuming piece format like "GENERAL_RED"
            piece_names = [p.split('_')[0] for p in selected_play]
            has_opener = any(name in ['GENERAL', 'ADVISOR'] for name in piece_names)
            
            # Bug 4: Wasting openers when at target
            # Only flag if playing invalidly (strategic disposal is not a bug)
            if at_target and has_opener and pieces_remaining > 2 and play_type != 'INVALID':
                bugs.append(BugReport(
                    bug_type="wasting_opener_at_target",
                    severity=BugSeverity.MEDIUM,
                    player=player_name,
                    phase="turn_play",
                    description=f"Played {piece_names} when already at target ({my_captured}/{my_declared})",
                    context={
                        'played': selected_play,
                        'captured': my_captured,
                        'declared': my_declared,
                        'pieces_remaining': pieces_remaining
                    },
                    suggested_fix="Play weakest possible pieces when at or above target"
                ))
                
            # Bug 5: Not playing to win when needed
            # REMOVED: This detection is disabled because we cannot determine if playing
            # weak pieces is a bug or a strategic choice without full game context.
            # There may be valid strategic reasons to play weak pieces even when
            # holding openers (e.g., baiting, misdirection, or other tactical considerations).
            
            # Bug 6: Playing pieces not in hand
            if hand_before:  # Only check if we have hand data
                for piece in selected_play:
                    if piece not in hand_before:
                        bugs.append(BugReport(
                            bug_type="playing_piece_not_in_hand",
                            severity=BugSeverity.CRITICAL,
                            player=player_name,
                            phase="turn_play",
                            description=f"Played {piece} which was not in hand",
                            context={
                                'played_piece': piece,
                                'hand_before': hand_before,
                                'selected_play': selected_play
                            },
                            suggested_fix="Only play pieces that are actually in the player's hand"
                        ))
                        
            # Bug 7: Playing wrong number of pieces
            if required_count and required_count > 0 and len(selected_play) != required_count:
                bugs.append(BugReport(
                    bug_type="wrong_piece_count",
                    severity=BugSeverity.CRITICAL,
                    player=player_name,
                    phase="turn_play",
                    description=f"Played {len(selected_play)} pieces when {required_count} were required",
                    context={
                        'played_count': len(selected_play),
                        'required_count': required_count,
                        'selected_play': selected_play
                    },
                    suggested_fix=f"Must play exactly {required_count} pieces as required"
                ))
                
        self.bugs_detected.extend(bugs)
        return bugs
        
    def check_combo_management_bugs(self, player_name: str, hand_data: List[str], 
                                   play_data: Dict) -> List[BugReport]:
        """Check for combo mismanagement"""
        bugs = []
        
        # This would require more complex analysis of the hand
        # For now, we'll skip this check
        
        return bugs
        
    def analyze_game_performance(self, game_summary: Dict) -> Dict[str, Any]:
        """Analyze overall game performance metrics"""
        player_stats = game_summary.get('player_statistics', {})
        
        performance = {
            'declaration_accuracy': {},
            'score_distribution': {},
            'red_flags': []
        }
        
        # Calculate declaration accuracy for each player
        for player, stats in player_stats.items():
            total_declared = stats.get('total_declared', 0)
            total_captured = stats.get('total_captured', 0)
            
            if total_declared > 0:
                accuracy = (total_captured / total_declared) * 100
                performance['declaration_accuracy'][player] = round(accuracy, 1)
                
                # Check for red flags
                if accuracy < 40:
                    performance['red_flags'].append(f"{player}: Very low accuracy ({accuracy:.1f}%)")
                elif accuracy > 90:
                    performance['red_flags'].append(f"{player}: Too conservative ({accuracy:.1f}%)")
                    
        return performance
        
    def get_bug_summary(self) -> Dict[str, Any]:
        """Get summary of all detected bugs"""
        summary = {
            'total_bugs': len(self.bugs_detected),
            'by_severity': {},
            'by_type': {},
            'by_player': {},
            'by_phase': {}
        }
        
        for bug in self.bugs_detected:
            # By severity
            severity = bug.severity.value
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
            
            # By type
            bug_type = bug.bug_type
            summary['by_type'][bug_type] = summary['by_type'].get(bug_type, 0) + 1
            
            # By player
            player = bug.player
            summary['by_player'][player] = summary['by_player'].get(player, 0) + 1
            
            # By phase
            phase = bug.phase
            summary['by_phase'][phase] = summary['by_phase'].get(phase, 0) + 1
            
        return summary
        
    def generate_bug_report(self) -> str:
        """Generate a human-readable bug report"""
        if not self.bugs_detected:
            return "No bugs detected!"
            
        report = f"AI BUG REPORT - {len(self.bugs_detected)} bugs found\n"
        report += "=" * 60 + "\n\n"
        
        # Group by severity
        critical = [b for b in self.bugs_detected if b.severity == BugSeverity.CRITICAL]
        high = [b for b in self.bugs_detected if b.severity == BugSeverity.HIGH]
        medium = [b for b in self.bugs_detected if b.severity == BugSeverity.MEDIUM]
        low = [b for b in self.bugs_detected if b.severity == BugSeverity.LOW]
        
        if critical:
            report += f"CRITICAL BUGS ({len(critical)})\n"
            report += "-" * 30 + "\n"
            for bug in critical:
                report += f"• {bug.player} - {bug.description}\n"
                report += f"  Fix: {bug.suggested_fix}\n\n"
                
        if high:
            report += f"\nHIGH SEVERITY BUGS ({len(high)})\n"
            report += "-" * 30 + "\n"
            for bug in high:
                report += f"• {bug.player} - {bug.description}\n"
                report += f"  Fix: {bug.suggested_fix}\n\n"
                
        if medium:
            report += f"\nMEDIUM SEVERITY BUGS ({len(medium)})\n"
            report += "-" * 30 + "\n"
            for bug in medium[:3]:  # Show first 3
                report += f"• {bug.player} - {bug.description}\n"
            if len(medium) > 3:
                report += f"  ... and {len(medium) - 3} more\n"
                
        report += "\nSUMMARY\n"
        report += "-" * 30 + "\n"
        summary = self.get_bug_summary()
        report += f"By Type: {summary['by_type']}\n"
        report += f"By Player: {summary['by_player']}\n"
        
        # Add descriptions for new bug types
        report += "\n\nBUG TYPE DESCRIPTIONS\n"
        report += "-" * 30 + "\n"
        bug_descriptions = {
            'over_aggressive_declaration': "Declaring high values without sufficient strong pieces",
            'zero_declaration_strong_hand': "Declaring 0 with strong opener pieces",
            'ignoring_pile_room': "Declaring more piles than mathematically possible",
            'excessive_zero_declarations': "Declaring 0 more than 2 times in a row (rule violation)",
            'last_player_sum_8': "Last player making total declaration equal to 8 (rule violation)",
            'wasting_opener_at_target': "Playing high-value pieces when already at/above target",
            'playing_piece_not_in_hand': "Playing pieces that are not in the player's hand (rule violation)",
            'wrong_piece_count': "Playing wrong number of pieces than required (rule violation)"
        }
        
        for bug_type in summary['by_type'].keys():
            if bug_type in bug_descriptions:
                report += f"{bug_type}: {bug_descriptions[bug_type]}\n"
        
        return report