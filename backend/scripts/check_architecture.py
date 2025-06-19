#!/usr/bin/env python3
"""Check architectural boundaries are respected"""

import os
import sys
from pathlib import Path

def check_domain_purity():
    """Ensure domain has no external dependencies"""
    violations = []
    domain_path = Path('backend/domain')
    
    if not domain_path.exists():
        print("Domain layer not found yet")
        return []
    
    forbidden_imports = [
        'fastapi', 'websocket', 'infrastructure', 
        'application', 'presentation', 'sqlalchemy'
    ]
    
    for py_file in domain_path.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
            
        with open(py_file, 'r') as f:
            content = f.read()
            
        for forbidden in forbidden_imports:
            if f'from {forbidden}' in content or f'import {forbidden}' in content:
                violations.append(
                    f"{py_file.relative_to('backend')}: imports {forbidden}"
                )
    
    return violations

def main():
    print("🔍 Checking architecture boundaries...\n")
    
    violations = check_domain_purity()
    
    if violations:
        print("❌ Violations found:")
        for v in violations:
            print(f"  - {v}")
        sys.exit(1)
    else:
        print("✅ Architecture is clean!")

if __name__ == "__main__":
    main()
