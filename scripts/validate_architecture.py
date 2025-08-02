#!/usr/bin/env python3
"""
Architecture Boundary Validation Script

This script validates that Clean Architecture and Engine Layer boundaries
are maintained and no architectural violations exist.
"""

import os
import sys
import ast
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass


@dataclass
class ArchitectureViolation:
    """Represents an architectural boundary violation."""
    file_path: str
    line_number: int
    violation_type: str
    description: str
    severity: str  # 'error', 'warning', 'info'


class ArchitectureValidator:
    """Validates architectural boundaries and dependencies."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.violations: List[ArchitectureViolation] = []
        
        # Define architectural boundaries
        self.clean_architecture_paths = {
            'domain': 'backend/domain',
            'application': 'backend/application', 
            'infrastructure': 'backend/infrastructure',
            'api': 'backend/api'
        }
        
        self.engine_layer_paths = {
            'engine': 'backend/engine'
        }
        
        # Define forbidden imports
        self.forbidden_imports = {
            # Clean Architecture cannot import Engine Layer
            'backend/domain': ['backend.engine'],
            'backend/application': ['backend.engine'],
            'backend/infrastructure': ['backend.engine'],
            'backend/api': ['backend.engine'],
            
            # Engine Layer should minimize Clean Architecture imports
            'backend/engine': [
                'backend.application.use_cases',  # Engine shouldn't use use cases
                'backend.infrastructure.persistence',  # Engine shouldn't do persistence
                'backend.api'  # Engine shouldn't handle APIs
            ]
        }
        
        # Required patterns for proper architecture
        self.required_patterns = {
            'use_cases': {
                'pattern': r'class\s+\w+UseCase\s*\(',
                'description': 'Use cases should follow naming convention'
            },
            'adapters': {
                'pattern': r'class\s+\w+Adapter\s*\(',
                'description': 'Adapters should follow naming convention'
            }
        }
    
    def validate(self) -> bool:
        """Run all architecture validations."""
        print("🔍 Running Architecture Boundary Validation...")
        print("=" * 50)
        
        self._validate_import_dependencies()
        self._validate_directory_structure()
        self._validate_naming_conventions()
        self._validate_feature_flag_usage()
        self._validate_clean_architecture_layers()
        
        return self._report_results()
    
    def _validate_import_dependencies(self):
        """Check for forbidden imports between architectural layers."""
        print("📦 Checking import dependencies...")
        
        for root, dirs, files in os.walk(self.project_root / 'backend'):
            for file in files:
                if not file.endswith('.py'):
                    continue
                    
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.project_root)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    self._check_file_imports(str(relative_path), content)
                    
                except (UnicodeDecodeError, FileNotFoundError):
                    continue
    
    def _check_file_imports(self, file_path: str, content: str):
        """Check imports in a specific file."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return
            
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                self._validate_import_node(file_path, node)
    
    def _validate_import_node(self, file_path: str, node: ast.AST):
        """Validate a specific import node."""
        if isinstance(node, ast.ImportFrom):
            module = node.module or ''
        elif isinstance(node, ast.Import):
            module = node.names[0].name if node.names else ''
        else:
            return
            
        # Check if this file's directory has forbidden imports
        file_dir = str(Path(file_path).parent)
        
        for forbidden_dir, forbidden_modules in self.forbidden_imports.items():
            if file_path.startswith(forbidden_dir):
                for forbidden_module in forbidden_modules:
                    if module.startswith(forbidden_module):
                        self.violations.append(ArchitectureViolation(
                            file_path=file_path,
                            line_number=getattr(node, 'lineno', 0),
                            violation_type='forbidden_import',
                            description=f"Forbidden import '{module}' in {forbidden_dir}",
                            severity='error'
                        ))
    
    def _validate_directory_structure(self):
        """Validate that the expected directory structure exists."""
        print("📁 Checking directory structure...")
        
        required_dirs = [
            'backend/domain/entities',
            'backend/domain/value_objects', 
            'backend/domain/events',
            'backend/application/use_cases',
            'backend/application/adapters',
            'backend/infrastructure/persistence',
            'backend/infrastructure/state_persistence',
            'backend/api',
            'backend/engine/state_machine'
        ]
        
        for required_dir in required_dirs:
            full_path = self.project_root / required_dir
            if not full_path.exists():
                self.violations.append(ArchitectureViolation(
                    file_path=required_dir,
                    line_number=0,
                    violation_type='missing_directory',
                    description=f"Required directory missing: {required_dir}",
                    severity='warning'
                ))
    
    def _validate_naming_conventions(self):
        """Validate that components follow naming conventions."""
        print("📝 Checking naming conventions...")
        
        # Check use cases
        use_case_dir = self.project_root / 'backend/application/use_cases'
        if use_case_dir.exists():
            self._check_use_case_naming(use_case_dir)
        
        # Check adapters
        adapter_dir = self.project_root / 'backend/application/adapters'
        if adapter_dir.exists():
            self._check_adapter_naming(adapter_dir)
    
    def _check_use_case_naming(self, use_case_dir: Path):
        """Check use case naming conventions."""
        for root, dirs, files in os.walk(use_case_dir):
            for file in files:
                if not file.endswith('.py') or file.startswith('__'):
                    continue
                    
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.project_root)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for UseCase class naming
                    if 'class ' in content and 'UseCase' in content:
                        if not re.search(r'class\s+\w+UseCase\s*\(', content):
                            self.violations.append(ArchitectureViolation(
                                file_path=str(relative_path),
                                line_number=0,
                                violation_type='naming_convention',
                                description="Use case class should end with 'UseCase'",
                                severity='warning'
                            ))
                except (UnicodeDecodeError, FileNotFoundError):
                    continue
    
    def _check_adapter_naming(self, adapter_dir: Path):
        """Check adapter naming conventions."""
        for root, dirs, files in os.walk(adapter_dir):
            for file in files:
                if not file.endswith('.py') or file.startswith('__'):
                    continue
                    
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.project_root)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for Adapter class naming
                    if 'class ' in content and 'Adapter' in content:
                        if not re.search(r'class\s+\w+Adapter\s*\(', content):
                            self.violations.append(ArchitectureViolation(
                                file_path=str(relative_path),
                                line_number=0,
                                violation_type='naming_convention',
                                description="Adapter class should end with 'Adapter'",
                                severity='warning'
                            ))
                except (UnicodeDecodeError, FileNotFoundError):
                    continue
    
    def _validate_feature_flag_usage(self):
        """Validate proper feature flag usage."""
        print("🚩 Checking feature flag usage...")
        
        # Look for state management without feature flag checks
        for root, dirs, files in os.walk(self.project_root / 'backend'):
            for file in files:
                if not file.endswith('.py'):
                    continue
                    
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.project_root)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    self._check_feature_flag_usage(str(relative_path), content)
                    
                except (UnicodeDecodeError, FileNotFoundError):
                    continue
    
    def _check_feature_flag_usage(self, file_path: str, content: str):
        """Check feature flag usage in a file."""
        # Check for StateManagementAdapter usage without feature flag
        if 'StateManagementAdapter' in content and 'USE_STATE_PERSISTENCE' not in content:
            # Allow if it's the adapter itself or test files
            if not any(x in file_path for x in ['state_management_adapter.py', 'test_', '/tests/']):
                self.violations.append(ArchitectureViolation(
                    file_path=file_path,
                    line_number=0,
                    violation_type='missing_feature_flag',
                    description="StateManagementAdapter used without USE_STATE_PERSISTENCE check",
                    severity='warning'
                ))
    
    def _validate_clean_architecture_layers(self):
        """Validate Clean Architecture dependency direction."""
        print("🏗️ Checking Clean Architecture layers...")
        
        # Domain layer should have no dependencies on other layers
        domain_dir = self.project_root / 'backend/domain'
        if domain_dir.exists():
            self._check_domain_layer_purity(domain_dir)
    
    def _check_domain_layer_purity(self, domain_dir: Path):
        """Check that domain layer has no outward dependencies."""
        for root, dirs, files in os.walk(domain_dir):
            for file in files:
                if not file.endswith('.py'):
                    continue
                    
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.project_root)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for imports that violate domain layer purity
                    forbidden_domain_imports = [
                        'backend.application',
                        'backend.infrastructure', 
                        'backend.api',
                        'backend.engine'
                    ]
                    
                    for forbidden in forbidden_domain_imports:
                        if f'from {forbidden}' in content or f'import {forbidden}' in content:
                            self.violations.append(ArchitectureViolation(
                                file_path=str(relative_path),
                                line_number=0,
                                violation_type='domain_layer_violation',
                                description=f"Domain layer importing {forbidden}",
                                severity='error'
                            ))
                            
                except (UnicodeDecodeError, FileNotFoundError):
                    continue
    
    def _report_results(self) -> bool:
        """Report validation results."""
        print("\n" + "=" * 50)
        print("📊 ARCHITECTURE VALIDATION RESULTS")
        print("=" * 50)
        
        if not self.violations:
            print("✅ No architectural violations found!")
            print("🎉 All boundaries are properly maintained.")
            return True
        
        # Group violations by severity
        errors = [v for v in self.violations if v.severity == 'error']
        warnings = [v for v in self.violations if v.severity == 'warning']
        info = [v for v in self.violations if v.severity == 'info']
        
        if errors:
            print(f"❌ {len(errors)} ERRORS found:")
            for violation in errors:
                print(f"  • {violation.file_path}:{violation.line_number}")
                print(f"    {violation.description}")
                print()
        
        if warnings:
            print(f"⚠️  {len(warnings)} WARNINGS found:")
            for violation in warnings:
                print(f"  • {violation.file_path}:{violation.line_number}")
                print(f"    {violation.description}")
                print()
        
        if info:
            print(f"ℹ️  {len(info)} INFO items:")
            for violation in info:
                print(f"  • {violation.file_path}:{violation.line_number}")
                print(f"    {violation.description}")
                print()
        
        print("📚 REMEDIATION GUIDANCE:")
        print("  - Review docs/architecture/QUICK_ARCHITECTURE_REFERENCE.md")
        print("  - Check docs/architecture/ADR-001-Clean-Architecture-vs-Engine-Layer.md") 
        print("  - Follow docs/architecture/CHANGE_PROTOCOLS.md")
        
        # Return False if there are errors
        return len(errors) == 0


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
    
    validator = ArchitectureValidator(str(project_root))
    success = validator.validate()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()