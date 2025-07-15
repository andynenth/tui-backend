#!/usr/bin/env python3
"""
Script to analyze the current rate limiting implementation for potential issues.

This script examines the code statically to identify:
1. WebSocket connection handling issues
2. Race conditions
3. Memory leaks
4. Configuration problems
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Dict, Any


class RateLimitAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.suggestions = []
        
    def analyze_websocket_handler(self):
        """Analyze the WebSocket handler for rate limit issues."""
        ws_file = self.project_root / "backend/api/routes/ws.py"
        
        if not ws_file.exists():
            self.issues.append({
                "severity": "ERROR",
                "file": "ws.py",
                "issue": "WebSocket handler file not found"
            })
            return
            
        with open(ws_file, 'r') as f:
            content = f.read()
            
        # Check for proper error handling after rate limit
        if "if not rate_limit_allowed:" in content:
            # Check what happens after rate limit error
            rate_limit_block = content[content.find("if not rate_limit_allowed:"):]
            rate_limit_block = rate_limit_block[:rate_limit_block.find("\n\n")]
            
            if "continue" in rate_limit_block:
                self.suggestions.append({
                    "file": "ws.py",
                    "suggestion": "Good: WebSocket loop continues after rate limit error"
                })
            else:
                self.issues.append({
                    "severity": "HIGH",
                    "file": "ws.py",
                    "issue": "WebSocket might close connection on rate limit",
                    "line": content[:content.find("if not rate_limit_allowed:")].count('\n') + 1
                })
                
        # Check for try-except around rate limit check
        if "check_websocket_rate_limit" in content:
            # Find the context around the rate limit check
            check_context = self._get_context_around(content, "check_websocket_rate_limit", 5)
            if "try:" not in check_context:
                self.issues.append({
                    "severity": "MEDIUM",
                    "file": "ws.py",
                    "issue": "Rate limit check not wrapped in try-except",
                    "suggestion": "Add exception handling to prevent connection drops"
                })
    
    def analyze_rate_limiter_implementation(self):
        """Analyze the core rate limiter for thread safety and memory issues."""
        rate_limit_file = self.project_root / "backend/api/middleware/rate_limit.py"
        
        if not rate_limit_file.exists():
            return
            
        with open(rate_limit_file, 'r') as f:
            content = f.read()
            
        # Check for asyncio.Lock usage
        if "asyncio.Lock" in content:
            self.suggestions.append({
                "file": "rate_limit.py",
                "suggestion": "Good: Using asyncio.Lock for thread safety"
            })
        else:
            self.issues.append({
                "severity": "HIGH",
                "file": "rate_limit.py",
                "issue": "No asyncio.Lock found - potential race conditions",
                "suggestion": "Add asyncio.Lock to protect shared data structures"
            })
            
        # Check for cleanup task
        if "_cleanup_task" in content or "cleanup_loop" in content:
            self.suggestions.append({
                "file": "rate_limit.py",
                "suggestion": "Good: Cleanup task implemented for memory management"
            })
        else:
            self.issues.append({
                "severity": "MEDIUM",
                "file": "rate_limit.py",
                "issue": "No cleanup task found - potential memory leak",
                "suggestion": "Implement periodic cleanup of old rate limit data"
            })
            
        # Check for proper deque usage
        if "defaultdict(deque)" in content:
            self.suggestions.append({
                "file": "rate_limit.py",
                "suggestion": "Good: Using deque for efficient timestamp management"
            })
            
        # Check for burst multiplier handling
        if "burst_multiplier" in content:
            # Look for potential overflow issues
            burst_context = self._get_context_around(content, "burst_multiplier", 3)
            if "int(" in burst_context and "*" in burst_context:
                self.suggestions.append({
                    "file": "rate_limit.py",
                    "suggestion": "Burst multiplier calculation appears safe"
                })
    
    def analyze_websocket_rate_limiter(self):
        """Analyze WebSocket-specific rate limiter."""
        ws_rate_limit_file = self.project_root / "backend/api/middleware/websocket_rate_limit.py"
        
        if not ws_rate_limit_file.exists():
            return
            
        with open(ws_rate_limit_file, 'r') as f:
            content = f.read()
            
        # Check for connection cleanup
        if "cleanup_connection" in content:
            cleanup_method = self._get_method_content(content, "cleanup_connection")
            if "await asyncio.sleep" in cleanup_method:
                delay_match = re.search(r'asyncio\.sleep\((\d+)\)', cleanup_method)
                if delay_match:
                    delay = int(delay_match.group(1))
                    if delay > 60:
                        self.suggestions.append({
                            "file": "websocket_rate_limit.py",
                            "suggestion": f"Connection cleanup delay of {delay}s helps prevent rapid reconnection abuse"
                        })
                        
        # Check rate limit configuration
        if "WEBSOCKET_RATE_LIMITS" in content:
            # Extract rate limits
            limits_section = content[content.find("WEBSOCKET_RATE_LIMITS"):]
            limits_section = limits_section[:limits_section.find("}")  + 1]
            
            # Check for critical events
            critical_events = ["declare", "play", "create_room"]
            for event in critical_events:
                if f'"{event}"' in limits_section:
                    # Extract the limit
                    event_line = [line for line in limits_section.split('\n') if f'"{event}"' in line][0]
                    if "block_duration_seconds" in event_line:
                        self.suggestions.append({
                            "file": "websocket_rate_limit.py",
                            "suggestion": f"Good: {event} has block duration for repeat offenders"
                        })
    
    def analyze_middleware_integration(self):
        """Analyze how rate limiting is integrated into the app."""
        main_file = self.project_root / "backend/api/main.py"
        
        if not main_file.exists():
            return
            
        with open(main_file, 'r') as f:
            content = f.read()
            
        # Check if middleware is added
        if "RateLimitMiddleware" in content:
            self.suggestions.append({
                "file": "main.py",
                "suggestion": "Rate limit middleware is integrated"
            })
            
            # Check middleware order
            middleware_section = self._get_context_around(content, "add_middleware", 10)
            cors_pos = middleware_section.find("CORSMiddleware")
            rate_limit_pos = middleware_section.find("RateLimitMiddleware")
            
            if cors_pos > -1 and rate_limit_pos > -1:
                if cors_pos < rate_limit_pos:
                    self.suggestions.append({
                        "file": "main.py",
                        "suggestion": "Good: CORS middleware is before rate limiting"
                    })
                else:
                    self.issues.append({
                        "severity": "LOW",
                        "file": "main.py",
                        "issue": "Rate limit middleware should be after CORS",
                        "suggestion": "Reorder middleware for proper CORS handling"
                    })
    
    def check_configuration(self):
        """Check for configuration issues."""
        # Check for environment variable usage
        env_example = self.project_root / ".env.example"
        
        if env_example.exists():
            with open(env_example, 'r') as f:
                env_content = f.read()
                
            if "RATE_LIMIT" in env_content:
                self.suggestions.append({
                    "file": ".env.example",
                    "suggestion": "Rate limit configuration documented in .env.example"
                })
        else:
            self.issues.append({
                "severity": "LOW",
                "file": ".env.example",
                "issue": "No rate limit configuration in .env.example",
                "suggestion": "Add rate limit environment variables to .env.example"
            })
    
    def _get_context_around(self, content: str, search_term: str, lines: int) -> str:
        """Get context around a search term."""
        pos = content.find(search_term)
        if pos == -1:
            return ""
            
        start = max(0, content.rfind('\n', 0, pos - lines * 80))
        end = min(len(content), content.find('\n', pos + lines * 80))
        
        return content[start:end]
    
    def _get_method_content(self, content: str, method_name: str) -> str:
        """Extract a method's content."""
        method_start = content.find(f"def {method_name}")
        if method_start == -1:
            method_start = content.find(f"async def {method_name}")
        
        if method_start == -1:
            return ""
            
        # Find the end of the method (next def at same indentation)
        method_content = content[method_start:]
        lines = method_content.split('\n')
        
        # Get indentation of method
        indent = len(lines[0]) - len(lines[0].lstrip())
        
        for i, line in enumerate(lines[1:], 1):
            if line.strip() and not line.startswith(' ' * (indent + 1)):
                return '\n'.join(lines[:i])
                
        return method_content
    
    def generate_report(self):
        """Generate analysis report."""
        print("=" * 60)
        print("Rate Limiting Implementation Analysis")
        print("=" * 60)
        
        if self.issues:
            print("\n🚨 ISSUES FOUND:")
            print("-" * 40)
            
            # Group by severity
            for severity in ["ERROR", "HIGH", "MEDIUM", "LOW"]:
                severity_issues = [i for i in self.issues if i["severity"] == severity]
                if severity_issues:
                    print(f"\n{severity} Priority:")
                    for issue in severity_issues:
                        print(f"  📍 {issue['file']}: {issue['issue']}")
                        if "line" in issue:
                            print(f"     Line: {issue['line']}")
                        if "suggestion" in issue:
                            print(f"     💡 {issue['suggestion']}")
        
        if self.suggestions:
            print("\n✅ POSITIVE FINDINGS:")
            print("-" * 40)
            for suggestion in self.suggestions:
                print(f"  ✓ {suggestion['file']}: {suggestion['suggestion']}")
        
        print("\n" + "=" * 60)
        print("SUMMARY:")
        print(f"  Total Issues: {len(self.issues)}")
        print(f"  High Priority: {len([i for i in self.issues if i['severity'] in ['ERROR', 'HIGH']])}")
        print(f"  Positive Findings: {len(self.suggestions)}")
        
        # Specific recommendations
        print("\n📋 KEY RECOMMENDATIONS:")
        print("-" * 40)
        
        recommendations = [
            "1. Ensure WebSocket connections continue after rate limit errors",
            "2. Add try-except blocks around rate limit checks",
            "3. Test with the manual_rate_limit_test.py script",
            "4. Monitor memory usage during high traffic",
            "5. Add environment variable configuration for rate limits",
            "6. Implement graceful degradation for critical game events"
        ]
        
        for rec in recommendations:
            print(f"  {rec}")
        
        print("\n" + "=" * 60)


def main():
    """Main function."""
    # Get project root (assuming we're in backend/tests/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    analyzer = RateLimitAnalyzer(project_root)
    
    print("Analyzing rate limiting implementation...")
    
    analyzer.analyze_websocket_handler()
    analyzer.analyze_rate_limiter_implementation()
    analyzer.analyze_websocket_rate_limiter()
    analyzer.analyze_middleware_integration()
    analyzer.check_configuration()
    
    analyzer.generate_report()


if __name__ == "__main__":
    main()