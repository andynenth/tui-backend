#!/usr/bin/env python3
"""
Analyze dependencies between legacy components for Phase 7.1.3
"""

import ast
import json
import os
from collections import defaultdict
from typing import Dict, Set, List


def find_imports(file_path: str) -> Set[str]:
    """Extract all imports from a Python file"""
    imports = set()
    
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read(), filename=file_path)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                    for alias in node.names:
                        imports.add(f"{node.module}.{alias.name}")
    except Exception as e:
        print(f"  ⚠️  Error parsing {file_path}: {e}")
    
    return imports


def analyze_legacy_dependencies():
    """Analyze dependencies between legacy files"""
    
    print("=== Phase 7.1.3: Legacy Dependency Analysis ===\n")
    
    # Load the registry
    with open('legacy_registry.json', 'r') as f:
        registry = json.load(f)
    
    # Load architecture analysis
    with open('phase7_architecture_analysis.json', 'r') as f:
        arch_analysis = json.load(f)
    
    legacy_files = arch_analysis['summary']['files_by_type']['legacy']
    
    # Build dependency graph
    dependencies = defaultdict(set)
    reverse_deps = defaultdict(set)  # What depends on this file
    
    print(f"Analyzing {len(legacy_files)} legacy files...\n")
    
    for file_path in legacy_files:
        if not file_path.endswith('.py'):
            continue
            
        if not os.path.exists(file_path):
            continue
            
        imports = find_imports(file_path)
        
        # Check which imports are from legacy files
        for imp in imports:
            # Convert import to potential file paths
            potential_paths = [
                imp.replace('.', '/') + '.py',
                imp.replace('.', '/') + '/__init__.py',
                imp + '.py'
            ]
            
            for potential_path in potential_paths:
                if potential_path in legacy_files:
                    dependencies[file_path].add(potential_path)
                    reverse_deps[potential_path].add(file_path)
    
    # Find circular dependencies
    print("=== Circular Dependencies ===")
    circular_deps = []
    for file_a in dependencies:
        for file_b in dependencies.get(file_a, []):
            if file_a in dependencies.get(file_b, []):
                pair = tuple(sorted([file_a, file_b]))
                if pair not in circular_deps:
                    circular_deps.append(pair)
                    print(f"  ⚠️  {pair[0]} <-> {pair[1]}")
    
    if not circular_deps:
        print("  ✅ No circular dependencies found")
    
    # Find removal order (files with no dependencies on other legacy files first)
    print("\n=== Suggested Removal Order ===")
    
    # Group files by dependency count
    dep_counts = {}
    for file_path in legacy_files:
        if file_path.endswith('.py'):
            # Count only dependencies on other legacy files
            legacy_dep_count = len([d for d in dependencies.get(file_path, []) if d in legacy_files])
            dep_counts[file_path] = legacy_dep_count
    
    # Sort by dependency count
    sorted_files = sorted(dep_counts.items(), key=lambda x: x[1])
    
    print("\nPhase 7.2.1 - No legacy dependencies (can remove first):")
    phase_1_files = [f for f, count in sorted_files if count == 0][:10]
    for f in phase_1_files:
        print(f"  - {f}")
    
    print(f"\n  ... and {len([f for f, c in sorted_files if c == 0]) - 10} more")
    
    print("\nPhase 7.2.2 - Few legacy dependencies:")
    phase_2_files = [f for f, count in sorted_files if 0 < count <= 2][:5]
    for f in phase_2_files:
        print(f"  - {f} (depends on: {', '.join(list(dependencies[f])[:2])})")
    
    print("\nPhase 7.2.3 - Core legacy components (remove last):")
    high_dep_files = sorted(reverse_deps.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    for f, deps in high_dep_files:
        print(f"  - {f} (used by {len(deps)} files)")
    
    # Check clean files with legacy dependencies
    print("\n=== Clean Files with Legacy Dependencies ===")
    clean_with_legacy = arch_analysis.get('recommendations', {}).get('clean_with_legacy_deps', [])
    
    if clean_with_legacy:
        print(f"Found {len(clean_with_legacy)} clean files importing legacy code:")
        for item in clean_with_legacy[:5]:
            print(f"  ⚠️  {item['file']} imports {', '.join(item['legacy_imports'][:2])}")
    else:
        print("  ✅ No clean files with legacy dependencies")
    
    # Save detailed analysis
    analysis_report = {
        "analysis_date": "2025-07-27",
        "circular_dependencies": circular_deps,
        "removal_phases": {
            "phase_7.2.1": phase_1_files,
            "phase_7.2.2": phase_2_files,
            "phase_7.2.3": [f for f, _ in high_dep_files]
        },
        "clean_with_legacy_deps": clean_with_legacy,
        "total_legacy_files": len(legacy_files),
        "dependency_graph": {k: list(v) for k, v in dependencies.items()},
        "reverse_dependency_graph": {k: list(v) for k, v in reverse_deps.items()}
    }
    
    with open('legacy_dependency_analysis.json', 'w') as f:
        json.dump(analysis_report, f, indent=2)
    
    print("\n✅ Dependency analysis saved to legacy_dependency_analysis.json")
    print("\n✅ Phase 7.1.3: Dependency Analysis Complete!")


if __name__ == '__main__':
    analyze_legacy_dependencies()