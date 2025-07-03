#!/usr/bin/env python3
"""
Phase 1 Migration Preparation Script

This script validates that the system is ready for the state management migration
and creates backups of all files that will be modified.
"""

import os
import sys
import shutil
import datetime
import json
import subprocess
from pathlib import Path


class MigrationPreparation:
    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = f"migration_backups/phase1_{self.timestamp}"
        self.report = {
            "timestamp": self.timestamp,
            "checks": {},
            "backups": [],
            "warnings": [],
            "errors": []
        }
    
    def run(self):
        """Run all preparation steps"""
        print("🔧 Phase 1 Migration Preparation")
        print(f"📅 Timestamp: {self.timestamp}")
        print("-" * 50)
        
        # Create backup directory
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Run all checks
        self.check_new_components()
        self.check_no_active_games()
        self.check_dependencies()
        self.create_backups()
        self.check_git_status()
        
        # Generate report
        self.generate_report()
        
        # Final summary
        if self.report["errors"]:
            print("\n❌ Migration NOT ready - errors found!")
            return False
        else:
            print("\n✅ Migration ready to proceed!")
            print(f"📁 Backups created in: {self.backup_dir}")
            print("\n⚠️  Remember to:")
            print("   1. Announce maintenance window to players")
            print("   2. Tag current version: git tag pre-phase-1-migration")
            print("   3. Follow WEEKEND_MIGRATION_CHECKLIST.md")
            return True
    
    def check_new_components(self):
        """Verify all new components exist"""
        print("\n🔍 Checking new components...")
        
        components = {
            "Frontend UnifiedGameStore": "../../../frontend/src/stores/UnifiedGameStore.ts",
            "Frontend NetworkIntegration": "../../../frontend/src/stores/NetworkIntegration.ts",
            "Frontend useGameStore hook": "../../../frontend/src/stores/useGameStore.ts",
            "Backend StateManager": "../../engine/state/state_manager.py",
            "Backend StateSnapshot": "../../engine/state/state_snapshot.py",
            "Migration hook": "./state_manager_hook.py"
        }
        
        all_exist = True
        for name, path in components.items():
            full_path = os.path.join(os.path.dirname(__file__), path)
            exists = os.path.exists(full_path)
            status = "✅" if exists else "❌"
            print(f"  {status} {name}: {path}")
            
            self.report["checks"][name] = exists
            if not exists:
                all_exist = False
                self.report["errors"].append(f"Missing component: {name}")
        
        return all_exist
    
    def check_no_active_games(self):
        """Check if any games are currently active"""
        print("\n🎮 Checking for active games...")
        
        try:
            # Try to call health endpoint
            import requests
            response = requests.get("http://localhost:5050/health/detailed", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'health' in data and 'metrics' in data['health']:
                    metrics = data['health']['metrics']
                    active_games = metrics.get('active_games', {}).get('value', 0)
                    
                    if active_games > 0:
                        self.report["warnings"].append(f"Active games detected: {active_games}")
                        print(f"  ⚠️  Active games: {active_games}")
                    else:
                        print("  ✅ No active games")
                        self.report["checks"]["no_active_games"] = True
        except Exception as e:
            print("  ℹ️  Could not check active games (server may be offline)")
            self.report["warnings"].append("Could not verify active games status")
    
    def check_dependencies(self):
        """Verify required dependencies are installed"""
        print("\n📦 Checking dependencies...")
        
        # Python dependencies
        try:
            import fastapi
            print("  ✅ FastAPI installed")
            self.report["checks"]["fastapi"] = True
        except ImportError:
            print("  ❌ FastAPI not installed")
            self.report["errors"].append("FastAPI not installed")
        
        # Check if TypeScript is available for frontend
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print("  ✅ npm installed")
                self.report["checks"]["npm"] = True
            else:
                print("  ❌ npm not installed")
                self.report["errors"].append("npm not installed")
        except FileNotFoundError:
            print("  ❌ npm not found")
            self.report["errors"].append("npm not found")
    
    def create_backups(self):
        """Create backups of files that will be modified"""
        print("\n💾 Creating backups...")
        
        files_to_backup = [
            # Frontend files
            "../../../frontend/src/App.jsx",
            "../../../frontend/src/pages/GamePage.jsx",
            "../../../frontend/src/components/game/GameBoard.jsx",
            "../../../frontend/src/components/game/PlayerHand.jsx",
            
            # Backend files  
            "../../room.py",
            "../../socket_manager.py",
            "../../api/routes/ws.py",
            
            # Files to be deleted (backup before deletion)
            "../../../frontend/src/services/GameService.ts",
            "../../../frontend/src/services/ServiceIntegration.ts",
            "../../../frontend/src/hooks/useGameState.ts",
            "../../../frontend/src/hooks/useGameActions.ts"
        ]
        
        for file_path in files_to_backup:
            full_path = os.path.join(os.path.dirname(__file__), file_path)
            if os.path.exists(full_path):
                # Create backup path
                backup_path = os.path.join(self.backup_dir, os.path.basename(file_path))
                
                # Handle duplicate filenames
                if os.path.exists(backup_path):
                    name, ext = os.path.splitext(backup_path)
                    counter = 1
                    while os.path.exists(f"{name}_{counter}{ext}"):
                        counter += 1
                    backup_path = f"{name}_{counter}{ext}"
                
                # Copy file
                shutil.copy2(full_path, backup_path)
                print(f"  ✅ Backed up: {os.path.basename(file_path)}")
                self.report["backups"].append({
                    "original": file_path,
                    "backup": backup_path
                })
            else:
                print(f"  ℹ️  File not found (ok if new): {file_path}")
    
    def check_git_status(self):
        """Check git status"""
        print("\n📊 Checking git status...")
        
        try:
            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__)
            )
            
            if result.stdout:
                print("  ⚠️  Uncommitted changes detected")
                self.report["warnings"].append("Uncommitted git changes")
            else:
                print("  ✅ Working directory clean")
                self.report["checks"]["git_clean"] = True
            
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__)
            )
            
            current_branch = result.stdout.strip()
            print(f"  ℹ️  Current branch: {current_branch}")
            self.report["checks"]["git_branch"] = current_branch
            
        except Exception as e:
            print(f"  ❌ Git check failed: {e}")
            self.report["errors"].append(f"Git check failed: {e}")
    
    def generate_report(self):
        """Generate migration readiness report"""
        report_path = os.path.join(self.backup_dir, "migration_report.json")
        
        with open(report_path, 'w') as f:
            json.dump(self.report, f, indent=2)
        
        print(f"\n📄 Report saved to: {report_path}")
        
        # Summary
        print("\n📊 Summary:")
        print(f"  ✅ Checks passed: {sum(1 for v in self.report['checks'].values() if v)}")
        print(f"  ⚠️  Warnings: {len(self.report['warnings'])}")
        print(f"  ❌ Errors: {len(self.report['errors'])}")
        print(f"  💾 Files backed up: {len(self.report['backups'])}")


if __name__ == "__main__":
    preparation = MigrationPreparation()
    success = preparation.run()
    sys.exit(0 if success else 1)