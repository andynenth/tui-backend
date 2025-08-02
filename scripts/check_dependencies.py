#!/usr/bin/env python3
"""
Dependency Analysis Script

This script analyzes import dependencies to detect architectural violations
and circular dependencies between Clean Architecture and Engine Layer.
"""

import os
import sys
import ast
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict, deque


@dataclass
class ImportInfo:
    """Information about an import statement."""
    source_file: str
    target_module: str
    line_number: int
    import_type: str  # 'direct', 'from', 'relative'


@dataclass 
class DependencyViolation:
    """A dependency rule violation."""
    source_file: str
    target_module: str
    line_number: int
    violation_type: str
    description: str
    severity: str


class DependencyAnalyzer:
    """Analyzes import dependencies and detects violations."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.imports: List[ImportInfo] = []
        self.violations: List[DependencyViolation] = []
        
        # Define architectural layers
        self.layers = {
            'domain': 'backend/domain',
            'application': 'backend/application',
            'infrastructure': 'backend/infrastructure', 
            'api': 'backend/api',
            'engine': 'backend/engine'
        }
        
        # Define allowed dependencies (who can import whom)
        self.allowed_dependencies = {
            'domain': [],  # Domain depends on nothing
            'application': ['domain'],  # Application can use domain
            'infrastructure': ['domain', 'application'],  # Infrastructure can use domain and application
            'api': ['domain', 'application', 'infrastructure'],  # API can use all Clean Architecture
            'engine': ['domain']  # Engine can only use domain (minimally)
        }
        
        # Critical violations that should fail builds
        self.critical_violations = {
            'domain_violation',  # Domain importing other layers
            'engine_in_clean_arch',  # Clean Architecture importing Engine
            'circular_dependency'  # Circular dependencies
        }
    
    def analyze(self) -> bool:
        """Run dependency analysis."""
        print("🔍 Running Dependency Analysis...")
        print("=" * 50)
        
        self._collect_imports()
        self._analyze_layer_dependencies()
        self._detect_circular_dependencies()
        self._check_critical_patterns()
        
        return self._report_results()
    
    def _collect_imports(self):
        """Collect all import statements from Python files."""
        print("📦 Collecting import statements...")
        
        for root, dirs, files in os.walk(self.project_root / 'backend'):
            # Skip __pycache__ and other non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('__pycache__')]
            
            for file in files:
                if not file.endswith('.py') or file.startswith('.'):
                    continue
                    
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.project_root)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    self._extract_imports_from_file(str(relative_path), content)
                    
                except (UnicodeDecodeError, FileNotFoundError, PermissionError):
                    continue
        
        print(f"  Found {len(self.imports)} import statements")
    
    def _extract_imports_from_file(self, file_path: str, content: str):
        """Extract imports from a single file."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return
            
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ''
                if module:  # Skip relative imports without module
                    self.imports.append(ImportInfo(
                        source_file=file_path,
                        target_module=module,
                        line_number=getattr(node, 'lineno', 0),
                        import_type='from'
                    ))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports.append(ImportInfo(
                        source_file=file_path,
                        target_module=alias.name,
                        line_number=getattr(node, 'lineno', 0),
                        import_type='direct'
                    ))
    
    def _analyze_layer_dependencies(self):
        """Analyze dependencies between architectural layers."""
        print("🏗️ Analyzing layer dependencies...")
        
        for import_info in self.imports:
            source_layer = self._get_layer_for_file(import_info.source_file)
            target_layer = self._get_layer_for_module(import_info.target_module)
            
            if source_layer and target_layer and source_layer != target_layer:
                self._check_layer_dependency(import_info, source_layer, target_layer)
    
    def _get_layer_for_file(self, file_path: str) -> Optional[str]:
        """Determine which architectural layer a file belongs to."""
        for layer_name, layer_path in self.layers.items():
            if file_path.startswith(layer_path):
                return layer_name
        return None
    
    def _get_layer_for_module(self, module_name: str) -> Optional[str]:
        """Determine which architectural layer a module belongs to."""
        # Convert module name to path-like format
        module_path = module_name.replace('.', '/')
        
        # Check against backend paths
        if module_path.startswith('backend/'):
            for layer_name, layer_path in self.layers.items():
                if module_path.startswith(layer_path):
                    return layer_name
        else:
            # Handle relative imports
            for layer_name, layer_path in self.layers.items():
                layer_relative = layer_path.replace('backend/', '')
                if module_path.startswith(layer_relative):
                    return layer_name
        
        return None
    
    def _check_layer_dependency(self, import_info: ImportInfo, source_layer: str, target_layer: str):
        """Check if a layer dependency is allowed."""
        allowed_targets = self.allowed_dependencies.get(source_layer, [])
        
        if target_layer not in allowed_targets:
            # Determine violation type and severity
            violation_type = 'layer_violation'
            severity = 'error'
            
            # Special cases for critical violations
            if source_layer == 'domain':
                violation_type = 'domain_violation'
                severity = 'error'
            elif source_layer in ['application', 'infrastructure', 'api'] and target_layer == 'engine':
                violation_type = 'engine_in_clean_arch'
                severity = 'error'
            elif source_layer == 'engine' and target_layer in ['application', 'infrastructure', 'api']:
                violation_type = 'engine_dependency'
                severity = 'warning'  # Warning because engine might need some adapters
            
            self.violations.append(DependencyViolation(
                source_file=import_info.source_file,
                target_module=import_info.target_module,
                line_number=import_info.line_number,
                violation_type=violation_type,
                description=f"Layer '{source_layer}' cannot import from layer '{target_layer}'",
                severity=severity
            ))
    
    def _detect_circular_dependencies(self):
        """Detect circular dependencies between modules."""
        print("🔄 Detecting circular dependencies...")
        
        # Build dependency graph
        graph = defaultdict(set)
        
        for import_info in self.imports:
            source_module = self._file_to_module(import_info.source_file)
            target_module = import_info.target_module
            
            # Only consider internal modules
            if source_module.startswith('backend') and target_module.startswith('backend'):
                graph[source_module].add(target_module)
        
        # Detect cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str, path: List[str]) -> Optional[List[str]]:
            if node in rec_stack:
                # Found cycle - return the cycle path
                cycle_start = path.index(node)
                return path[cycle_start:] + [node]
            
            if node in visited:
                return None
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                cycle = has_cycle(neighbor, path + [node])
                if cycle:
                    return cycle
            
            rec_stack.remove(node)
            return None
        
        # Check each node for cycles
        for node in graph:
            if node not in visited:
                cycle = has_cycle(node, [])
                if cycle:
                    self._report_circular_dependency(cycle)
    
    def _file_to_module(self, file_path: str) -> str:
        """Convert file path to module name."""
        # Remove .py extension and convert slashes to dots
        module = file_path.replace('.py', '').replace('/', '.')
        
        # Remove __init__ from module names
        if module.endswith('.__init__'):
            module = module[:-9]
        
        return module
    
    def _report_circular_dependency(self, cycle: List[str]):
        """Report a circular dependency."""
        cycle_str = ' -> '.join(cycle)
        
        # Find a file in the cycle to report against
        for import_info in self.imports:
            source_module = self._file_to_module(import_info.source_file)
            if source_module in cycle:
                self.violations.append(DependencyViolation(
                    source_file=import_info.source_file,
                    target_module='',
                    line_number=0,
                    violation_type='circular_dependency',
                    description=f"Circular dependency detected: {cycle_str}",
                    severity='error'
                ))
                break
    
    def _check_critical_patterns(self):
        """Check for critical anti-patterns."""
        print("⚠️ Checking for critical patterns...")
        
        # Check for State Machine in Clean Architecture
        clean_arch_files = [
            imp.source_file for imp in self.imports 
            if any(imp.source_file.startswith(layer) for layer in 
                   ['backend/domain', 'backend/application', 'backend/infrastructure', 'backend/api'])
        ]
        
        for import_info in self.imports:
            if import_info.source_file in clean_arch_files:
                # Check for GameStateMachine imports
                if 'game_state_machine' in import_info.target_module.lower():
                    self.violations.append(DependencyViolation(
                        source_file=import_info.source_file,
                        target_module=import_info.target_module,
                        line_number=import_info.line_number,
                        violation_type='state_machine_in_clean_arch',
                        description="Clean Architecture should not import GameStateMachine directly",
                        severity='error'
                    ))
                
                # Check for direct Engine imports
                if 'backend.engine' in import_info.target_module:
                    self.violations.append(DependencyViolation(
                        source_file=import_info.source_file,
                        target_module=import_info.target_module,
                        line_number=import_info.line_number,
                        violation_type='direct_engine_import',
                        description="Clean Architecture should not import Engine Layer directly",
                        severity='error'
                    ))
    
    def _report_results(self) -> bool:
        """Report analysis results."""
        print("\n" + "=" * 50)
        print("📊 DEPENDENCY ANALYSIS RESULTS")
        print("=" * 50)
        
        if not self.violations:
            print("✅ No dependency violations found!")
            print("🎉 All architectural boundaries are respected.")
            return True
        
        # Group by severity
        errors = [v for v in self.violations if v.severity == 'error']
        warnings = [v for v in self.violations if v.severity == 'warning']
        
        if errors:
            print(f"❌ {len(errors)} CRITICAL ERRORS found:")
            for violation in errors:
                print(f"  • {violation.source_file}:{violation.line_number}")
                print(f"    {violation.description}")
                print(f"    Import: {violation.target_module}")
                print()
        
        if warnings:
            print(f"⚠️  {len(warnings)} WARNINGS found:")
            for violation in warnings:
                print(f"  • {violation.source_file}:{violation.line_number}")
                print(f"    {violation.description}")
                print(f"    Import: {violation.target_module}")
                print()
        
        # Show dependency summary
        self._show_dependency_summary()
        
        print("📚 REMEDIATION GUIDANCE:")
        print("  - Remove forbidden imports")
        print("  - Use adapter patterns for cross-system communication")
        print("  - Review architectural boundaries in documentation")
        print("  - Consider dependency injection for loose coupling")
        
        # Check for critical violations
        has_critical = any(v.violation_type in self.critical_violations for v in self.violations)
        return not has_critical
    
    def _show_dependency_summary(self):
        """Show a summary of dependencies by layer."""
        print("\n📈 DEPENDENCY SUMMARY BY LAYER:")
        
        layer_imports = defaultdict(lambda: defaultdict(int))
        
        for import_info in self.imports:
            source_layer = self._get_layer_for_file(import_info.source_file)
            target_layer = self._get_layer_for_module(import_info.target_module)
            
            if source_layer and target_layer:
                layer_imports[source_layer][target_layer] += 1
        
        for source_layer in sorted(layer_imports.keys()):
            targets = layer_imports[source_layer]
            if targets:
                print(f"  {source_layer}:")
                for target_layer, count in sorted(targets.items()):
                    status = "✅" if target_layer in self.allowed_dependencies.get(source_layer, []) else "❌"
                    print(f"    {status} {target_layer}: {count} imports")


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
    
    analyzer = DependencyAnalyzer(str(project_root))
    success = analyzer.analyze()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()