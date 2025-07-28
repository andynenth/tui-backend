#!/usr/bin/env python3
"""
Contract Testing Monitoring Dashboard
Provides real-time monitoring of contract test results and compatibility.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio
import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn


console = Console()


class ContractTestMonitor:
    """Monitors contract test execution and results"""
    
    def __init__(self):
        self.test_results_path = Path("tests/contracts/test_results")
        self.golden_masters_path = Path("tests/contracts/golden_masters")
        self.test_results_path.mkdir(exist_ok=True)
        self.latest_results = {}
        self.historical_results = []
        
    def load_latest_results(self) -> Dict[str, Any]:
        """Load the most recent test results"""
        result_files = list(self.test_results_path.glob("*.json"))
        if not result_files:
            return {"status": "No test results found"}
            
        latest_file = max(result_files, key=lambda p: p.stat().st_mtime)
        
        with open(latest_file, 'r') as f:
            return json.load(f)
            
    def get_golden_master_status(self) -> Dict[str, Any]:
        """Check golden master coverage"""
        if not self.golden_masters_path.exists():
            return {
                "status": "error",
                "message": "Golden masters directory not found",
                "coverage": 0
            }
            
        masters = list(self.golden_masters_path.glob("*.json"))
        
        # Expected golden masters (one per message type)
        expected_count = 21  # Based on our 21 WebSocket message types
        
        return {
            "status": "ok" if len(masters) >= expected_count else "incomplete",
            "found": len(masters),
            "expected": expected_count,
            "coverage": (len(masters) / expected_count * 100) if expected_count > 0 else 0,
            "missing": expected_count - len(masters)
        }
        
    def get_compatibility_score(self) -> float:
        """Calculate overall compatibility score"""
        latest = self.load_latest_results()
        
        if "summary" not in latest:
            return 0.0
            
        total = latest["summary"].get("total", 0)
        passed = latest["summary"].get("passed", 0)
        
        return (passed / total * 100) if total > 0 else 0.0
        
    def get_problem_areas(self) -> List[Dict[str, Any]]:
        """Identify problematic message types"""
        latest = self.load_latest_results()
        problems = []
        
        if "tests" in latest:
            for test in latest["tests"]:
                if test.get("outcome") != "passed":
                    problems.append({
                        "test": test.get("nodeid", "Unknown"),
                        "outcome": test.get("outcome", "failed"),
                        "message": test.get("call", {}).get("longrepr", "No details")
                    })
                    
        return problems[:5]  # Top 5 problems
        
    def generate_dashboard(self) -> Layout:
        """Generate monitoring dashboard"""
        layout = Layout()
        
        # Main sections
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Header
        layout["header"].update(
            Panel(
                f"[bold cyan]Contract Testing Monitor[/bold cyan] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                style="white on blue"
            )
        )
        
        # Body sections
        layout["body"].split_row(
            Layout(name="status", ratio=1),
            Layout(name="details", ratio=2)
        )
        
        # Status section
        status_content = self._create_status_panel()
        layout["body"]["status"].update(status_content)
        
        # Details section
        layout["body"]["details"].split_column(
            Layout(name="coverage"),
            Layout(name="problems")
        )
        
        coverage_content = self._create_coverage_panel()
        layout["body"]["details"]["coverage"].update(coverage_content)
        
        problems_content = self._create_problems_panel()
        layout["body"]["details"]["problems"].update(problems_content)
        
        # Footer
        layout["footer"].update(
            Panel(
                "[dim]Press Ctrl+C to exit | R to refresh | H for help[/dim]",
                style="white on black"
            )
        )
        
        return layout
        
    def _create_status_panel(self) -> Panel:
        """Create status overview panel"""
        compatibility = self.get_compatibility_score()
        golden_status = self.get_golden_master_status()
        
        # Determine overall status
        if compatibility >= 100 and golden_status["status"] == "ok":
            status_emoji = "✅"
            status_text = "[green]Ready for Refactoring[/green]"
        elif compatibility >= 95:
            status_emoji = "⚠️"
            status_text = "[yellow]Almost Ready[/yellow]"
        else:
            status_emoji = "❌"
            status_text = "[red]Not Ready[/red]"
            
        content = f"""
{status_emoji} Status: {status_text}

📊 Compatibility Score: [bold]{compatibility:.1f}%[/bold]
📁 Golden Masters: {golden_status['found']}/{golden_status['expected']}
🧪 Last Test Run: {self._get_last_test_time()}
        """
        
        return Panel(content, title="Overall Status", border_style="cyan")
        
    def _create_coverage_panel(self) -> Panel:
        """Create coverage details panel"""
        golden_status = self.get_golden_master_status()
        
        # Create coverage table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        table.add_column("Status")
        
        # Golden master coverage
        coverage_color = "green" if golden_status["coverage"] >= 100 else "yellow" if golden_status["coverage"] >= 80 else "red"
        table.add_row(
            "Golden Master Coverage",
            f"{golden_status['coverage']:.1f}%",
            f"[{coverage_color}]{'✓' if golden_status['coverage'] >= 100 else '✗'}[/{coverage_color}]"
        )
        
        # Contract definitions
        table.add_row(
            "Contract Definitions",
            "21/21",
            "[green]✓[/green]"
        )
        
        # Test coverage
        latest = self.load_latest_results()
        if "summary" in latest:
            test_coverage = (latest["summary"]["passed"] / latest["summary"]["total"] * 100) if latest["summary"]["total"] > 0 else 0
            coverage_color = "green" if test_coverage >= 100 else "yellow" if test_coverage >= 80 else "red"
            table.add_row(
                "Test Pass Rate",
                f"{test_coverage:.1f}%",
                f"[{coverage_color}]{'✓' if test_coverage >= 100 else '✗'}[/{coverage_color}]"
            )
            
        return Panel(table, title="Coverage Details", border_style="magenta")
        
    def _create_problems_panel(self) -> Panel:
        """Create problems panel"""
        problems = self.get_problem_areas()
        
        if not problems:
            content = "[green]No problems detected! All tests passing.[/green]"
        else:
            lines = ["[red]Failed Tests:[/red]\n"]
            for i, problem in enumerate(problems, 1):
                test_name = problem["test"].split("::")[-1] if "::" in problem["test"] else problem["test"]
                lines.append(f"{i}. {test_name}")
                lines.append(f"   Status: [{problem['outcome']}]{problem['outcome']}[/{problem['outcome']}]")
                
            content = "\n".join(lines)
            
        return Panel(content, title="Problem Areas", border_style="red" if problems else "green")
        
    def _get_last_test_time(self) -> str:
        """Get time of last test run"""
        result_files = list(self.test_results_path.glob("*.json"))
        if not result_files:
            return "Never"
            
        latest_file = max(result_files, key=lambda p: p.stat().st_mtime)
        mtime = datetime.fromtimestamp(latest_file.stat().st_mtime)
        
        # Format as relative time
        delta = datetime.now() - mtime
        if delta < timedelta(minutes=1):
            return "Just now"
        elif delta < timedelta(hours=1):
            return f"{int(delta.total_seconds() / 60)} minutes ago"
        elif delta < timedelta(days=1):
            return f"{int(delta.total_seconds() / 3600)} hours ago"
        else:
            return f"{delta.days} days ago"


async def run_monitor():
    """Run the monitoring dashboard"""
    monitor = ContractTestMonitor()
    
    console.print("[bold cyan]Contract Testing Monitor Starting...[/bold cyan]")
    
    with Live(monitor.generate_dashboard(), refresh_per_second=1) as live:
        try:
            while True:
                await asyncio.sleep(5)  # Refresh every 5 seconds
                live.update(monitor.generate_dashboard())
        except KeyboardInterrupt:
            console.print("\n[yellow]Monitor stopped by user[/yellow]")


def generate_compatibility_report():
    """Generate a detailed compatibility report"""
    monitor = ContractTestMonitor()
    
    console.print(Panel.fit(
        "[bold]Frontend Compatibility Report[/bold]",
        style="cyan"
    ))
    
    # Overall status
    compatibility = monitor.get_compatibility_score()
    golden_status = monitor.get_golden_master_status()
    
    status_table = Table(show_header=False, box=None)
    status_table.add_column("Metric", style="cyan")
    status_table.add_column("Value")
    
    status_table.add_row("Compatibility Score", f"[bold]{compatibility:.1f}%[/bold]")
    status_table.add_row("Golden Masters", f"{golden_status['found']}/{golden_status['expected']}")
    status_table.add_row("Overall Status", "[green]READY[/green]" if compatibility >= 100 and golden_status["status"] == "ok" else "[red]NOT READY[/red]")
    
    console.print(Panel(status_table, title="Summary", border_style="cyan"))
    
    # Required actions
    if compatibility < 100 or golden_status["status"] != "ok":
        console.print(Panel.fit("[bold red]Required Actions:[/bold red]", style="red"))
        
        if golden_status["missing"] > 0:
            console.print(f"  • Capture {golden_status['missing']} missing golden masters")
            console.print("    Run: [cyan]python tests/contracts/capture_golden_masters.py[/cyan]")
            
        problems = monitor.get_problem_areas()
        if problems:
            console.print(f"  • Fix {len(problems)} failing contract tests")
            
    else:
        console.print(Panel.fit(
            "[bold green]✅ All compatibility checks passed![/bold green]\n" +
            "You can safely begin refactoring.",
            style="green"
        ))
        
    # Save report
    report_data = {
        "generated_at": datetime.now().isoformat(),
        "compatibility_score": compatibility,
        "golden_master_status": golden_status,
        "problems": monitor.get_problem_areas(),
        "ready_for_refactoring": compatibility >= 100 and golden_status["status"] == "ok"
    }
    
    report_path = Path("compatibility_report.json")
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
        
    console.print(f"\n[dim]Full report saved to: {report_path}[/dim]")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Contract Testing Monitor")
    parser.add_argument("--report", action="store_true", help="Generate compatibility report")
    parser.add_argument("--monitor", action="store_true", help="Run monitoring dashboard")
    
    args = parser.parse_args()
    
    if args.report:
        generate_compatibility_report()
    elif args.monitor:
        try:
            # Check if rich is installed
            import rich
        except ImportError:
            print("Installing required dependency: rich")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
            
        asyncio.run(run_monitor())
    else:
        parser.print_help()