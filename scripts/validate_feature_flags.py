#!/usr/bin/env python3
"""
Feature Flag Validation Script

This script validates that feature flags are properly used throughout
the codebase and that architectural components respect flag settings.
"""

import os
import sys
import ast
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass


@dataclass
class FeatureFlagViolation:
    """A feature flag usage violation."""
    file_path: str
    line_number: int
    violation_type: str
    description: str
    severity: str
    flag_name: Optional[str] = None


class FeatureFlagValidator:
    """Validates feature flag usage and consistency."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.violations: List[FeatureFlagViolation] = []
        
        # Define expected feature flags and their usage patterns
        self.feature_flags = {
            'USE_STATE_PERSISTENCE': {
                'description': 'Controls state management adapter usage',
                'components': ['StateManagementAdapter'],
                'files': ['state_management_adapter.py'],
                'required_checks': [
                    'track_game_start',
                    'track_phase_change', 
                    'track_player_action'
                ]
            },
            'USE_EVENT_SOURCING': {
                'description': 'Controls event persistence',
                'components': ['EventStore', 'CompositeEventPublisher'],
                'files': ['event_store.py', 'composite_event_publisher.py'],
                'required_checks': ['publish']
            },
            'USE_CLEAN_ARCHITECTURE': {
                'description': 'Controls Clean Architecture features',
                'components': ['UseCase', 'Repository'],
                'files': ['use_case', 'repository'],
                'required_checks': []
            }
        }
        
        # Components that should always check feature flags
        self.flag_dependent_components = {
            'StateManagementAdapter': 'USE_STATE_PERSISTENCE',
            'StatePersistenceManager': 'USE_STATE_PERSISTENCE',
            'EventStore': 'USE_EVENT_SOURCING',
            'CompositeEventPublisher': 'USE_EVENT_SOURCING'
        }
        
        # Methods that should check flags before operation
        self.flag_dependent_methods = {
            'track_game_start': 'USE_STATE_PERSISTENCE',
            'track_phase_change': 'USE_STATE_PERSISTENCE',
            'track_player_action': 'USE_STATE_PERSISTENCE',
            'create_snapshot': 'USE_STATE_PERSISTENCE',
            'recover_game_state': 'USE_STATE_PERSISTENCE'
        }
    
    def validate(self) -> bool:
        """Run feature flag validation."""
        print("🚩 Running Feature Flag Validation...")
        print("=" * 50)
        
        self._validate_flag_definitions()
        self._validate_flag_usage()
        self._validate_component_integration()
        self._validate_consistency()
        
        return self._report_results()
    
    def _validate_flag_definitions(self):
        """Validate that expected feature flags are defined."""
        print("📝 Validating flag definitions...")
        
        feature_flags_file = self.project_root / 'backend/infrastructure/feature_flags.py'
        
        if not feature_flags_file.exists():
            self.violations.append(FeatureFlagViolation(
                file_path='backend/infrastructure/feature_flags.py',
                line_number=0,
                violation_type='missing_flag_file',
                description="Feature flags file is missing",
                severity='error'
            ))
            return
        
        try:
            with open(feature_flags_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for each expected flag
            for flag_name, flag_info in self.feature_flags.items():
                if flag_name not in content:
                    self.violations.append(FeatureFlagViolation(
                        file_path='backend/infrastructure/feature_flags.py',
                        line_number=0,
                        violation_type='missing_flag_definition',
                        description=f"Feature flag '{flag_name}' is not defined",
                        severity='error',
                        flag_name=flag_name
                    ))
                
                # Check for default value setting
                if f'{flag_name}: False' not in content and f'{flag_name}: True' not in content:
                    self.violations.append(FeatureFlagViolation(
                        file_path='backend/infrastructure/feature_flags.py',
                        line_number=0,
                        violation_type='missing_flag_default',
                        description=f"Feature flag '{flag_name}' has no default value",
                        severity='warning',
                        flag_name=flag_name
                    ))
        
        except (UnicodeDecodeError, FileNotFoundError):
            self.violations.append(FeatureFlagViolation(
                file_path='backend/infrastructure/feature_flags.py',
                line_number=0,
                violation_type='unreadable_flag_file',
                description="Cannot read feature flags file",
                severity='error'
            ))
    
    def _validate_flag_usage(self):
        """Validate that components properly check feature flags."""
        print("🔍 Validating flag usage...")
        
        for root, dirs, files in os.walk(self.project_root / 'backend'):
            for file in files:
                if not file.endswith('.py'):
                    continue
                    
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.project_root)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    self._check_file_flag_usage(str(relative_path), content)
                    
                except (UnicodeDecodeError, FileNotFoundError):
                    continue
    
    def _check_file_flag_usage(self, file_path: str, content: str):
        """Check feature flag usage in a specific file."""
        lines = content.split('\n')
        
        # Check for components that should use feature flags
        for component, required_flag in self.flag_dependent_components.items():
            if component in content:
                # Allow the component definition file itself
                if component.lower() in file_path.lower():
                    continue
                    
                # Check if the required flag is checked
                if required_flag not in content:
                    # Find line number for better reporting
                    line_num = 0
                    for i, line in enumerate(lines):
                        if component in line:
                            line_num = i + 1
                            break
                    
                    self.violations.append(FeatureFlagViolation(
                        file_path=file_path,
                        line_number=line_num,
                        violation_type='missing_flag_check',
                        description=f"Component '{component}' used without checking '{required_flag}'",
                        severity='warning',
                        flag_name=required_flag
                    ))
        
        # Check for methods that should check flags
        for method, required_flag in self.flag_dependent_methods.items():
            if f'def {method}(' in content or f'.{method}(' in content:
                # Find the method definition or call
                method_line = 0
                for i, line in enumerate(lines):
                    if method in line:
                        method_line = i + 1
                        break
                
                # Check if flag is checked in reasonable proximity
                context_lines = 20  # Check within 20 lines
                start_line = max(0, method_line - context_lines)
                end_line = min(len(lines), method_line + context_lines)
                context = '\n'.join(lines[start_line:end_line])
                
                if required_flag not in context and 'self.enabled' not in context:
                    self.violations.append(FeatureFlagViolation(
                        file_path=file_path,
                        line_number=method_line,
                        violation_type='method_missing_flag_check',
                        description=f"Method '{method}' should check '{required_flag}' before execution",
                        severity='warning',
                        flag_name=required_flag
                    ))
    
    def _validate_component_integration(self):
        """Validate that components properly integrate with feature flags."""
        print("🔗 Validating component integration...")
        
        # Check StateManagementAdapter specifically
        adapter_file = self.project_root / 'backend/application/adapters/state_management_adapter.py'
        if adapter_file.exists():
            self._validate_state_adapter_integration(adapter_file)
        
        # Check use cases that use adapters
        use_cases_dir = self.project_root / 'backend/application/use_cases'
        if use_cases_dir.exists():
            self._validate_use_case_integration(use_cases_dir)
    
    def _validate_state_adapter_integration(self, adapter_file: Path):
        """Validate StateManagementAdapter integration."""
        try:
            with open(adapter_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            relative_path = adapter_file.relative_to(self.project_root)
            
            # Check for enabled property
            if 'def enabled(self)' not in content and '@property' not in content:
                self.violations.append(FeatureFlagViolation(
                    file_path=str(relative_path),
                    line_number=0,
                    violation_type='missing_enabled_property',
                    description="StateManagementAdapter should have 'enabled' property",
                    severity='error'
                ))
            
            # Check for feature flag import
            if 'get_feature_flags' not in content and 'feature_flags' not in content:
                self.violations.append(FeatureFlagViolation(
                    file_path=str(relative_path),
                    line_number=0,
                    violation_type='missing_flag_import',
                    description="StateManagementAdapter should import feature flags",
                    severity='error'
                ))
            
            # Check for disabled state handling
            if 'if not self.enabled' not in content:
                self.violations.append(FeatureFlagViolation(
                    file_path=str(relative_path),
                    line_number=0,
                    violation_type='missing_disabled_handling',
                    description="StateManagementAdapter should handle disabled state",
                    severity='warning'
                ))
        
        except (UnicodeDecodeError, FileNotFoundError):
            pass
    
    def _validate_use_case_integration(self, use_cases_dir: Path):
        """Validate use case integration with feature flags."""
        for root, dirs, files in os.walk(use_cases_dir):
            for file in files:
                if not file.endswith('.py') or file.startswith('__'):
                    continue
                    
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.project_root)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for StateManagementAdapter usage
                    if 'StateManagementAdapter' in content:
                        # Should handle adapter being None or disabled
                        if 'if self._state_adapter' not in content and 'if state_adapter' not in content:
                            self.violations.append(FeatureFlagViolation(
                                file_path=str(relative_path),
                                line_number=0,
                                violation_type='missing_adapter_null_check',
                                description="Use case should handle StateManagementAdapter being None",
                                severity='warning'
                            ))
                
                except (UnicodeDecodeError, FileNotFoundError):
                    continue
    
    def _validate_consistency(self):
        """Validate feature flag consistency across the codebase."""
        print("⚖️ Validating flag consistency...")
        
        # Check that flags are consistently named
        flag_references = {}
        
        for root, dirs, files in os.walk(self.project_root / 'backend'):
            for file in files:
                if not file.endswith('.py'):
                    continue
                    
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.project_root)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Find flag references
                    for flag_name in self.feature_flags.keys():
                        if flag_name in content:
                            if flag_name not in flag_references:
                                flag_references[flag_name] = []
                            flag_references[flag_name].append(str(relative_path))
                
                except (UnicodeDecodeError, FileNotFoundError):
                    continue
        
        # Check for unused flags
        for flag_name, flag_info in self.feature_flags.items():
            if flag_name not in flag_references:
                self.violations.append(FeatureFlagViolation(
                    file_path='',
                    line_number=0,
                    violation_type='unused_flag',
                    description=f"Feature flag '{flag_name}' is defined but never used",
                    severity='info',
                    flag_name=flag_name
                ))
            elif len(flag_references[flag_name]) == 1:
                # Only referenced in feature_flags.py
                if 'feature_flags.py' in flag_references[flag_name][0]:
                    self.violations.append(FeatureFlagViolation(
                        file_path='',
                        line_number=0,
                        violation_type='underused_flag',
                        description=f"Feature flag '{flag_name}' is only defined but not used elsewhere",
                        severity='info',
                        flag_name=flag_name
                    ))
    
    def _report_results(self) -> bool:
        """Report validation results."""
        print("\n" + "=" * 50)
        print("📊 FEATURE FLAG VALIDATION RESULTS")
        print("=" * 50)
        
        if not self.violations:
            print("✅ No feature flag violations found!")
            print("🎉 All flags are properly defined and used.")
            return True
        
        # Group by severity
        errors = [v for v in self.violations if v.severity == 'error']
        warnings = [v for v in self.violations if v.severity == 'warning']
        info = [v for v in self.violations if v.severity == 'info']
        
        if errors:
            print(f"❌ {len(errors)} ERRORS found:")
            for violation in errors:
                print(f"  • {violation.file_path}:{violation.line_number}")
                print(f"    {violation.description}")
                if violation.flag_name:
                    print(f"    Flag: {violation.flag_name}")
                print()
        
        if warnings:
            print(f"⚠️  {len(warnings)} WARNINGS found:")
            for violation in warnings:
                print(f"  • {violation.file_path}:{violation.line_number}")
                print(f"    {violation.description}")
                if violation.flag_name:
                    print(f"    Flag: {violation.flag_name}")
                print()
        
        if info:
            print(f"ℹ️  {len(info)} INFO items:")
            for violation in info:
                print(f"  • {violation.description}")
                if violation.flag_name:
                    print(f"    Flag: {violation.flag_name}")
                print()
        
        # Show flag usage summary
        self._show_flag_summary()
        
        print("📚 REMEDIATION GUIDANCE:")
        print("  - Add missing feature flag checks before component usage")
        print("  - Ensure components handle disabled state gracefully")
        print("  - Update feature flag definitions if needed")
        print("  - Review architectural boundaries and flag requirements")
        
        return len(errors) == 0
    
    def _show_flag_summary(self):
        """Show summary of feature flag usage."""
        print("\n📈 FEATURE FLAG SUMMARY:")
        
        for flag_name, flag_info in self.feature_flags.items():
            print(f"  🚩 {flag_name}")
            print(f"     Description: {flag_info['description']}")
            print(f"     Components: {', '.join(flag_info['components'])}")
            
            # Check current violations for this flag
            flag_violations = [v for v in self.violations if v.flag_name == flag_name]
            if flag_violations:
                error_count = len([v for v in flag_violations if v.severity == 'error'])
                warning_count = len([v for v in flag_violations if v.severity == 'warning'])
                print(f"     Issues: {error_count} errors, {warning_count} warnings")
            else:
                print(f"     Status: ✅ No issues")
            print()


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        # Detect project root
        current = Path.cwd()
        while current != current.parent:
            if (current / 'backend').exists():
                project_root = current
                break
            current = current.parent
        else:
            print("❌ Could not find project root (looking for 'backend' directory)")
            sys.exit(1)
    
    validator = FeatureFlagValidator(str(project_root))
    success = validator.validate()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()