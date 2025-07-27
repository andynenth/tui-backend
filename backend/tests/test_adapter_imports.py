#!/usr/bin/env python3
"""
Test suite for validating adapter imports.

This test ensures all adapters and their dependencies can be imported
without errors, catching issues like missing events or circular imports.
"""

import unittest
import importlib
import sys
from typing import List, Tuple


class TestAdapterImports(unittest.TestCase):
    """Test that all adapter modules can be imported successfully."""
    
    def setUp(self):
        """Set up test environment."""
        self.failed_imports: List[Tuple[str, Exception]] = []
    
    def test_room_adapters_import(self):
        """Test room adapters can be imported."""
        try:
            import api.adapters.room_adapters
            self.assertTrue(True, "room_adapters imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import room_adapters: {e}")
    
    def test_game_adapters_import(self):
        """Test game adapters can be imported."""
        try:
            import api.adapters.game_adapters
            self.assertTrue(True, "game_adapters imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import game_adapters: {e}")
    
    def test_connection_adapters_import(self):
        """Test connection adapters can be imported."""
        try:
            import api.adapters.connection_adapters
            self.assertTrue(True, "connection_adapters imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import connection_adapters: {e}")
    
    def test_legacy_repository_bridge_import(self):
        """Test legacy repository bridge can be imported."""
        try:
            import infrastructure.adapters.legacy_repository_bridge
            self.assertTrue(True, "legacy_repository_bridge imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import legacy_repository_bridge: {e}")
    
    def test_clean_architecture_adapter_import(self):
        """Test clean architecture adapter can be imported."""
        try:
            import infrastructure.adapters.clean_architecture_adapter
            self.assertTrue(True, "clean_architecture_adapter imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import clean_architecture_adapter: {e}")
    
    def test_integrated_adapter_system_import(self):
        """Test integrated adapter system can be imported."""
        try:
            import api.adapters.integrated_adapter_system
            self.assertTrue(True, "integrated_adapter_system imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import integrated_adapter_system: {e}")
    
    def test_all_use_cases_import(self):
        """Test that all use cases can be imported."""
        use_case_modules = [
            # Room management
            "application.use_cases.room_management.create_room",
            "application.use_cases.room_management.join_room",
            "application.use_cases.room_management.leave_room",
            "application.use_cases.room_management.get_room_state",
            
            # Game use cases
            "application.use_cases.game.start_game",
            "application.use_cases.game.play",
            "application.use_cases.game.declare",
            "application.use_cases.game.request_redeal",
            "application.use_cases.game.accept_redeal",
            "application.use_cases.game.decline_redeal",
            
            # Connection use cases
            "application.use_cases.connection.handle_player_disconnect",
            "application.use_cases.connection.handle_player_reconnect",
        ]
        
        for module_name in use_case_modules:
            with self.subTest(module=module_name):
                try:
                    importlib.import_module(module_name)
                except ImportError as e:
                    self.fail(f"Failed to import {module_name}: {e}")
    
    def test_domain_events_import(self):
        """Test that all domain events can be imported."""
        event_modules = [
            "domain.events.base",
            "domain.events.game_events",
            "domain.events.player_events",
            "domain.events.room_events",
            "domain.events.connection_events",
            "domain.events.all_events",
        ]
        
        for module_name in event_modules:
            with self.subTest(module=module_name):
                try:
                    importlib.import_module(module_name)
                except ImportError as e:
                    self.fail(f"Failed to import {module_name}: {e}")
    
    def test_specific_event_imports(self):
        """Test specific event imports that have caused issues."""
        test_cases = [
            # (module, event_name, should_exist)
            ("domain.events.game_events", "PiecesPlayed", True),
            ("domain.events.player_events", "PlayerPlayedPieces", False),  # This should NOT exist
            ("domain.events.game_events", "RedealVoteStarted", False),  # This should NOT exist
            ("domain.events.game_events", "RedealRequested", True),
            ("domain.events.game_events", "RedealDecisionMade", True),
            ("domain.events.game_events", "RedealExecuted", True),
        ]
        
        for module_name, event_name, should_exist in test_cases:
            with self.subTest(event=event_name):
                try:
                    module = importlib.import_module(module_name)
                    has_event = hasattr(module, event_name)
                    
                    if should_exist and not has_event:
                        self.fail(f"Expected event {event_name} not found in {module_name}")
                    elif not should_exist and has_event:
                        self.fail(f"Unexpected event {event_name} found in {module_name} (should not exist)")
                    else:
                        self.assertTrue(True, f"Event {event_name} existence check passed")
                        
                except ImportError as e:
                    self.fail(f"Failed to import {module_name}: {e}")


def run_import_diagnostics():
    """Run comprehensive import diagnostics and print results."""
    print("=" * 60)
    print("ADAPTER IMPORT DIAGNOSTICS")
    print("=" * 60)
    
    modules_to_test = [
        # Core adapters
        "api.adapters.room_adapters",
        "api.adapters.game_adapters",
        "api.adapters.connection_adapters",
        "api.adapters.integrated_adapter_system",
        
        # Infrastructure adapters
        "infrastructure.adapters.legacy_repository_bridge",
        "infrastructure.adapters.clean_architecture_adapter",
        
        # Problematic use cases
        "application.use_cases.game.play",
        "application.use_cases.game.request_redeal",
    ]
    
    failed_imports = []
    
    for module_name in modules_to_test:
        try:
            importlib.import_module(module_name)
            print(f"✓ {module_name}")
        except ImportError as e:
            print(f"✗ {module_name}")
            print(f"  Error: {e}")
            failed_imports.append((module_name, str(e)))
        except Exception as e:
            print(f"✗ {module_name}")
            print(f"  Unexpected error: {type(e).__name__}: {e}")
            failed_imports.append((module_name, f"{type(e).__name__}: {e}"))
    
    if failed_imports:
        print("\n" + "=" * 60)
        print("IMPORT FAILURE SUMMARY")
        print("=" * 60)
        for module, error in failed_imports:
            print(f"\n{module}:")
            print(f"  {error}")
        
        # Try to find root cause
        print("\n" + "=" * 60)
        print("ROOT CAUSE ANALYSIS")
        print("=" * 60)
        
        if any("PlayerPlayedPieces" in error for _, error in failed_imports):
            print("\n- PlayerPlayedPieces import issue detected")
            print("  Fix: Change 'PlayerPlayedPieces' to 'PiecesPlayed' in play.py")
        
        if any("RedealVoteStarted" in error for _, error in failed_imports):
            print("\n- RedealVoteStarted import issue detected")
            print("  Fix: Remove 'RedealVoteStarted' import from request_redeal.py")
    
    print("\n" + "=" * 60)
    print(f"Total modules tested: {len(modules_to_test)}")
    print(f"Failed imports: {len(failed_imports)}")
    print("=" * 60)
    
    return len(failed_imports) == 0


if __name__ == "__main__":
    # Run diagnostics first
    success = run_import_diagnostics()
    
    if not success:
        print("\n⚠️  Fix the import errors above before running unit tests")
        sys.exit(1)
    
    # Run unit tests if imports are OK
    print("\nRunning unit tests...")
    unittest.main()