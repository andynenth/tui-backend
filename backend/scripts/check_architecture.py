#!/usr/bin/env python3
# backend/scripts/check_architecture.py
"""
Automated Architecture Boundary Enforcement

Validates that clean architecture layers respect dependency rules:
- Domain: Zero external dependencies (pure business logic)
- Application: Can only import from domain
- Infrastructure: Can import domain interfaces only
- Presentation: Can import application and domain DTOs only

Usage: python backend/scripts/check_architecture.py
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Set


class ArchitectureChecker:
    """Validates clean architecture boundaries"""
    
    def __init__(self, backend_path: Path = Path('backend')):
        self.backend_path = backend_path
        self.violations: List[str] = []
    
    def check_all_layers(self) -> bool:
        """Check all architectural boundaries"""
        print("🔍 Checking clean architecture boundaries...\n")
        
        # Check each layer
        self.check_domain_purity()
        self.check_application_layer()
        self.check_infrastructure_layer() 
        self.check_presentation_layer()
        
        # Report results
        if self.violations:
            print("❌ Architecture violations found:")
            for violation in self.violations:
                print(f"  - {violation}")
            print(f"\nTotal violations: {len(self.violations)}")
            return False
        else:
            print("✅ Architecture is clean!")
            print("✅ All layer boundaries respected")
            print("✅ Zero dependency violations")
            return True
    
    def check_domain_purity(self) -> None:
        """Ensure domain layer has ZERO external dependencies"""
        print("📦 Checking Domain Layer Purity...")
        
        domain_path = self.backend_path / 'domain'
        if not domain_path.exists():
            print("   📁 Domain layer not found yet")
            return
        
        # Forbidden imports for domain layer
        forbidden_imports = {
            # Other layers
            'application', 'infrastructure', 'presentation',
            # Frameworks
            'fastapi', 'flask', 'django', 'starlette',
            # Databases
            'sqlalchemy', 'pymongo', 'redis', 'psycopg2',
            # External services
            'requests', 'httpx', 'aiohttp',
            # WebSockets
            'websockets', 'socketio',
            # Any external dependency
            'pydantic', 'pytest', 'numpy', 'pandas'
        }
        
        violations = self._check_layer_imports(
            domain_path, 
            forbidden_imports, 
            "Domain"
        )
        
        if violations:
            self.violations.extend(violations)
        else:
            print("   ✅ Domain layer is pure (zero external dependencies)")
    
    def check_application_layer(self) -> None:
        """Ensure application layer only imports from domain"""
        print("🎯 Checking Application Layer...")
        
        app_path = self.backend_path / 'application'
        if not app_path.exists():
            print("   📁 Application layer not found yet")
            return
        
        # Application can only import domain, not infrastructure/presentation
        forbidden_imports = {
            'infrastructure', 'presentation',
            # Frameworks (application should be framework-agnostic)
            'fastapi', 'flask', 'django', 'starlette',
            'websockets', 'socketio'
        }
        
        violations = self._check_layer_imports(
            app_path,
            forbidden_imports,
            "Application"
        )
        
        if violations:
            self.violations.extend(violations)
        else:
            print("   ✅ Application layer dependencies are correct")
    
    def check_infrastructure_layer(self) -> None:
        """Ensure infrastructure only imports domain interfaces"""
        print("🔧 Checking Infrastructure Layer...")
        
        infra_path = self.backend_path / 'infrastructure'
        if not infra_path.exists():
            print("   📁 Infrastructure layer not found yet")
            return
        
        # Infrastructure should not import application or presentation
        forbidden_imports = {
            'application', 'presentation'
        }
        
        violations = self._check_layer_imports(
            infra_path,
            forbidden_imports,
            "Infrastructure"
        )
        
        if violations:
            self.violations.extend(violations)
        else:
            print("   ✅ Infrastructure layer dependencies are correct")
    
    def check_presentation_layer(self) -> None:
        """Ensure presentation layer only calls application use cases"""
        print("🎨 Checking Presentation Layer...")
        
        pres_path = self.backend_path / 'presentation'
        if not pres_path.exists():
            print("   📁 Presentation layer not found yet")
            return
        
        # Presentation should not import infrastructure
        forbidden_imports = {
            'infrastructure'
        }
        
        violations = self._check_layer_imports(
            pres_path,
            forbidden_imports,
            "Presentation"
        )
        
        # Also check for business logic in presentation
        business_logic_violations = self._check_for_business_logic(pres_path)
        
        if violations:
            self.violations.extend(violations)
        if business_logic_violations:
            self.violations.extend(business_logic_violations)
        
        if not violations and not business_logic_violations:
            print("   ✅ Presentation layer dependencies are correct")
    
    def _check_layer_imports(
        self, 
        layer_path: Path, 
        forbidden_imports: Set[str], 
        layer_name: str
    ) -> List[str]:
        """Check for forbidden imports in a layer"""
        violations = []
        
        for py_file in layer_path.rglob('*.py'):
            # Skip __pycache__ and test files for forbidden import check
            if '__pycache__' in str(py_file) or py_file.name.startswith('__'):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                file_violations = self._find_import_violations(
                    py_file, content, forbidden_imports, layer_name
                )
                violations.extend(file_violations)
            except Exception as e:
                print(f"   ⚠️  Warning: Could not read {py_file}: {e}")
        
        return violations
    
    def _find_import_violations(
        self,
        file_path: Path,
        content: str,
        forbidden_imports: Set[str],
        layer_name: str
    ) -> List[str]:
        """Find specific import violations in file content"""
        violations = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Check for direct imports: "import forbidden_module"
            import_match = re.match(r'^import\s+(\w+)', line)
            if import_match:
                module = import_match.group(1)
                if module in forbidden_imports:
                    rel_path = file_path.relative_to(self.backend_path)
                    violations.append(
                        f"{layer_name} violation: {rel_path}:{line_num} "
                        f"imports '{module}' (line: {line})"
                    )
            
            # Check for from imports: "from forbidden_module import ..."
            from_match = re.match(r'^from\s+(\w+)', line)
            if from_match:
                module = from_match.group(1)
                if module in forbidden_imports:
                    rel_path = file_path.relative_to(self.backend_path)
                    violations.append(
                        f"{layer_name} violation: {rel_path}:{line_num} "
                        f"imports from '{module}' (line: {line})"
                    )
        
        return violations
    
    def _check_for_business_logic(self, pres_path: Path) -> List[str]:
        """Check for business logic in presentation layer"""
        violations = []
        
        # Common business logic indicators
        business_patterns = [
            r'def calculate_',
            r'def validate_',
            r'def process_',
            r'if.*score.*>',
            r'if.*game.*state',
            r'\.add_to_score\(',
            r'\.can_beat\(',
        ]
        
        for py_file in pres_path.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                for line_num, line in enumerate(content.split('\n'), 1):
                    for pattern in business_patterns:
                        if re.search(pattern, line):
                            rel_path = py_file.relative_to(self.backend_path)
                            violations.append(
                                f"Business logic in presentation: {rel_path}:{line_num} "
                                f"contains business logic (line: {line.strip()})"
                            )
                            break
            except Exception:
                continue
        
        return violations


def print_architecture_rules():
    """Print the clean architecture rules being enforced"""
    print("""
🏗️  Clean Architecture Rules Being Enforced:

📦 DOMAIN LAYER (backend/domain/):
   ✅ Can import: typing, dataclasses, enum, abc, datetime, uuid
   ❌ Cannot import: application, infrastructure, presentation
   ❌ Cannot import: frameworks (fastapi, flask, etc.)
   ❌ Cannot import: external libraries (requests, sqlalchemy, etc.)
   🎯 Purpose: Pure business logic with zero external dependencies

🎯 APPLICATION LAYER (backend/application/):
   ✅ Can import: domain layer only
   ❌ Cannot import: infrastructure, presentation
   ❌ Cannot import: frameworks directly
   🎯 Purpose: Use case orchestration and business workflows

🔧 INFRASTRUCTURE LAYER (backend/infrastructure/):
   ✅ Can import: domain interfaces only
   ✅ Can import: any external frameworks/libraries
   ❌ Cannot import: application, presentation
   🎯 Purpose: Technical implementations of domain interfaces

🎨 PRESENTATION LAYER (backend/presentation/):
   ✅ Can import: application layer (use cases)
   ✅ Can import: domain layer (DTOs only)
   ✅ Can import: web frameworks
   ❌ Cannot import: infrastructure
   ❌ Cannot contain: business logic
   🎯 Purpose: User interface and API endpoints only

Dependency flow: Presentation → Application → Domain ← Infrastructure
""")


def main():
    """Main entry point"""
    print("🏗️  Clean Architecture Boundary Checker")
    print("=" * 50)
    
    # Change to backend directory if script run from root
    if not Path('backend').exists() and Path('../backend').exists():
        os.chdir('..')
    
    checker = ArchitectureChecker()
    is_clean = checker.check_all_layers()
    
    if not is_clean:
        print("\n📚 To fix violations, review the architecture rules:")
        print_architecture_rules()
        sys.exit(1)
    else:
        print("\n🎉 Architecture is compliant! Great work!")
        sys.exit(0)


if __name__ == "__main__":
    main()