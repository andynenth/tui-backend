#!/usr/bin/env python3
"""
Architecture Status Dashboard

Real-time dashboard showing architecture status with color-coded indicators.
Provides continuous monitoring of clean architecture vs legacy status.
"""

import asyncio
import sys
import time
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional
import subprocess

def clear_screen():
    """Clear the terminal screen."""
    subprocess.run(['clear'], shell=True)

def get_status_color(status: str) -> str:
    """Get ANSI color code for status."""
    colors = {
        "clean_architecture": "\033[92m",  # Green
        "partial_migration": "\033[93m",   # Yellow  
        "legacy_code": "\033[91m",         # Red
        "unknown": "\033[94m",             # Blue
        "error": "\033[95m"                # Magenta
    }
    return colors.get(status, "\033[0m")

def reset_color() -> str:
    """Reset ANSI color."""
    return "\033[0m"

class ArchitectureDashboard:
    """Real-time architecture status dashboard."""
    
    def __init__(self, server_url: str = "http://localhost:8000", refresh_interval: int = 10):
        self.server_url = server_url
        self.refresh_interval = refresh_interval
        self.last_status = None
        self.status_history = []
        self.error_count = 0
        
    def fetch_architecture_status(self) -> Optional[Dict[str, Any]]:
        """Fetch current architecture status from server."""
        try:
            url = f"{self.server_url}/api/health/architecture-status"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                self.error_count = 0
                return response.json()
            else:
                self.error_count += 1
                return {
                    "architecture_status": "error",
                    "message": f"HTTP {response.status_code}",
                    "confidence_percentage": 0,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.error_count += 1
            return {
                "architecture_status": "error", 
                "message": f"Connection error: {str(e)}",
                "confidence_percentage": 0,
                "timestamp": datetime.now().isoformat()
            }
    
    def fetch_health_status(self) -> Optional[Dict[str, Any]]:
        """Fetch basic health status."""
        try:
            url = f"{self.server_url}/api/health"
            response = requests.get(url, timeout=3)
            return response.json() if response.status_code == 200 else None
        except:
            return None
    
    def render_header(self):
        """Render dashboard header."""
        print("="*80)
        print("🏗️  ARCHITECTURE STATUS DASHBOARD")
        print("="*80)
        print(f"Server: {self.server_url}")
        print(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Refresh Interval: {self.refresh_interval}s")
        print("-"*80)
    
    def render_architecture_status(self, status_data: Dict[str, Any]):
        """Render main architecture status."""
        arch_status = status_data.get("architecture_status", "unknown")
        message = status_data.get("message", "No message")
        confidence = status_data.get("confidence_percentage", 0)
        
        color = get_status_color(arch_status)
        reset = reset_color()
        
        print(f"\\n🎯 ARCHITECTURE STATUS:")
        print(f"   Status: {color}{arch_status.upper().replace('_', ' ')}{reset}")
        print(f"   Message: {message}")
        print(f"   Confidence: {confidence}%")
        
        # Show confidence bar
        bar_length = 40
        filled_length = int(bar_length * confidence / 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        print(f"   Progress: [{color}{bar}{reset}] {confidence}%")
    
    def render_feature_flags(self, status_data: Dict[str, Any]):
        """Render feature flag status."""
        feature_flags = status_data.get("feature_flags", {})
        
        print(f"\\n🏁 FEATURE FLAGS:")
        
        # Clean architecture flags
        clean_flags = feature_flags.get("clean_architecture", {})
        print(f"   Clean Architecture:")
        for flag, enabled in clean_flags.items():
            icon = "✅" if enabled else "❌"
            print(f"     {icon} {flag}: {enabled}")
        
        # Adapter flags
        adapter_flags = feature_flags.get("adapters", {})
        print(f"   Adapters:")
        for flag, enabled in adapter_flags.items():
            icon = "✅" if enabled else "❌"
            print(f"     {icon} {flag}: {enabled}")
        
        # Summary
        summary = feature_flags.get("summary", {})
        if summary:
            total = summary.get("total_flags", 0)
            enabled = summary.get("enabled_flags", 0) 
            percentage = summary.get("enabled_percentage", 0)
            print(f"   Summary: {enabled}/{total} flags enabled ({percentage:.1f}%)")
    
    def render_migration_evidence(self, status_data: Dict[str, Any]):
        """Render migration evidence."""
        evidence = status_data.get("migration_evidence", [])
        
        print(f"\\n📋 MIGRATION EVIDENCE:")
        if evidence:
            for item in evidence:
                print(f"   ✅ {item}")
        else:
            print(f"   ❌ No migration evidence found")
    
    def render_recommendations(self, status_data: Dict[str, Any]):
        """Render recommendations."""
        recommendations = status_data.get("recommendations", {})
        arch_status = status_data.get("architecture_status", "unknown")
        
        print(f"\\n💡 RECOMMENDATIONS:")
        current_recs = recommendations.get(arch_status, [])
        if current_recs:
            for rec in current_recs:
                print(f"   {rec}")
        else:
            print(f"   ℹ️ No specific recommendations available")
    
    def render_health_info(self, health_data: Optional[Dict[str, Any]]):
        """Render basic health information."""
        print(f"\\n💚 SYSTEM HEALTH:")
        if health_data:
            status = health_data.get("status", "unknown")
            uptime = health_data.get("uptime_formatted", "unknown")
            color = get_status_color("clean_architecture" if status == "healthy" else "error")
            reset = reset_color()
            
            print(f"   Status: {color}{status.upper()}{reset}")
            print(f"   Uptime: {uptime}")
            print(f"   Service: {health_data.get('service', 'unknown')}")
        else:
            print(f"   ❌ Health data unavailable")
    
    def render_status_history(self):
        """Render recent status changes."""
        print(f"\\n📊 STATUS HISTORY:")
        if len(self.status_history) > 1:
            recent_history = self.status_history[-5:]  # Last 5 entries
            for entry in recent_history:
                timestamp = entry["timestamp"][:19]  # Remove microseconds
                status = entry["status"] 
                color = get_status_color(status)
                reset = reset_color()
                print(f"   {timestamp}: {color}{status.replace('_', ' ')}{reset}")
        else:
            print(f"   ℹ️ Collecting status history...")
    
    def render_footer(self):
        """Render dashboard footer."""
        print("-"*80)
        print(f"Error Count: {self.error_count}")
        print(f"Press Ctrl+C to exit")
        print("="*80)
    
    def update_status_history(self, status_data: Dict[str, Any]):
        """Update status history."""
        current_status = status_data.get("architecture_status", "unknown")
        timestamp = status_data.get("timestamp", datetime.now().isoformat())
        
        # Only add to history if status changed
        if not self.status_history or self.status_history[-1]["status"] != current_status:
            self.status_history.append({
                "status": current_status,
                "timestamp": timestamp
            })
            
            # Keep only last 20 entries
            if len(self.status_history) > 20:
                self.status_history = self.status_history[-20:]
    
    def render_dashboard(self, status_data: Dict[str, Any], health_data: Optional[Dict[str, Any]]):
        """Render complete dashboard."""
        clear_screen()
        
        self.render_header()
        self.render_architecture_status(status_data)
        self.render_feature_flags(status_data)
        self.render_migration_evidence(status_data)
        self.render_recommendations(status_data)
        self.render_health_info(health_data)
        self.render_status_history()
        self.render_footer()
    
    async def run_dashboard(self):
        """Run the real-time dashboard."""
        print("🚀 Starting Architecture Status Dashboard...")
        print("   Connecting to server...")
        
        try:
            while True:
                # Fetch current status
                status_data = self.fetch_architecture_status()
                health_data = self.fetch_health_status()
                
                if status_data:
                    self.update_status_history(status_data)
                    self.render_dashboard(status_data, health_data)
                    self.last_status = status_data
                else:
                    clear_screen()
                    print("❌ Unable to fetch architecture status")
                    print(f"   Server: {self.server_url}")
                    print(f"   Error Count: {self.error_count}")
                    print("   Retrying...")
                
                # Wait for next refresh
                await asyncio.sleep(self.refresh_interval)
                
        except KeyboardInterrupt:
            clear_screen()
            print("\\n👋 Architecture Status Dashboard stopped")
            
            # Show final status
            if self.last_status:
                arch_status = self.last_status.get("architecture_status", "unknown")
                color = get_status_color(arch_status)
                reset = reset_color()
                print(f"Final Status: {color}{arch_status.upper().replace('_', ' ')}{reset}")
            
            sys.exit(0)
        except Exception as e:
            clear_screen()
            print(f"❌ Dashboard error: {e}")
            sys.exit(1)


async def main():
    """Main dashboard function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Architecture Status Dashboard")
    parser.add_argument("--server-url", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--refresh-interval", type=int, default=10, help="Refresh interval in seconds")
    
    args = parser.parse_args()
    
    dashboard = ArchitectureDashboard(args.server_url, args.refresh_interval)
    await dashboard.run_dashboard()


if __name__ == "__main__":
    asyncio.run(main())