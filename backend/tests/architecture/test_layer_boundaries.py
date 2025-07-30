"""
Architectural Boundary Tests

These tests ensure that architectural boundaries are respected
and that layers don't violate dependency rules.
"""

import os
import ast
import pytest
from pathlib import Path
from typing import Set, List, Dict, Any


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to extract imports from Python files"""

    def __init__(self):
        self.imports: Set[str] = set()
        self.from_imports: Set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statements"""
        for alias in node.names:
            self.imports.add(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from...import statements"""
        if node.module:
            self.from_imports.add(node.module)


def get_imports_from_file(file_path: Path) -> Set[str]:
    """Extract all imports from a Python file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        visitor = ImportVisitor()
        visitor.visit(tree)

        return visitor.imports | visitor.from_imports
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return set()


def get_python_files_in_layer(layer_path: str) -> List[Path]:
    """Get all Python files in a layer directory"""
    layer_dir = Path(layer_path)
    if not layer_dir.exists():
        return []

    return list(layer_dir.rglob("*.py"))


class TestLayerBoundaries:
    """Test that layers respect architectural boundaries"""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory"""
        # Assuming tests are run from backend directory
        return Path.cwd()

    def test_infrastructure_no_application_imports(self, project_root):
        """Test that infrastructure layer doesn't import from application layer"""
        infrastructure_files = get_python_files_in_layer(
            project_root / "infrastructure"
        )

        violations = []

        for file_path in infrastructure_files:
            # Skip interface files and test files
            if "interfaces" in str(file_path) or "test" in str(file_path):
                continue

            imports = get_imports_from_file(file_path)

            # Check for application layer imports
            app_imports = [
                imp
                for imp in imports
                if imp.startswith("application.")
                and not imp.startswith("application.interfaces")
            ]

            if app_imports:
                violations.append(
                    {
                        "file": str(file_path.relative_to(project_root)),
                        "imports": app_imports,
                    }
                )

        assert not violations, (
            "Infrastructure layer should not import from application layer:\n"
            + "\n".join(
                f"  {v['file']} imports: {', '.join(v['imports'])}" for v in violations
            )
        )

    def test_application_no_api_imports(self, project_root):
        """Test that application layer doesn't import from API layer"""
        application_files = get_python_files_in_layer(project_root / "application")

        violations = []

        for file_path in application_files:
            # Skip test files
            if "test" in str(file_path):
                continue

            imports = get_imports_from_file(file_path)

            # Check for API layer imports
            api_imports = [imp for imp in imports if imp.startswith("api.")]

            if api_imports:
                violations.append(
                    {
                        "file": str(file_path.relative_to(project_root)),
                        "imports": api_imports,
                    }
                )

        assert (
            not violations
        ), "Application layer should not import from API layer:\n" + "\n".join(
            f"  {v['file']} imports: {', '.join(v['imports'])}" for v in violations
        )

    def test_domain_no_external_imports(self, project_root):
        """Test that domain layer has no external dependencies"""
        domain_files = get_python_files_in_layer(project_root / "domain")

        # Also check engine directory (contains domain logic)
        domain_files.extend(get_python_files_in_layer(project_root / "engine"))

        violations = []
        allowed_stdlib = {
            "abc",
            "dataclasses",
            "enum",
            "typing",
            "datetime",
            "uuid",
            "random",
            "math",
            "collections",
            "itertools",
            "functools",
            "copy",
            "json",
            "re",
            "logging",
            "os",
            "sys",
        }

        for file_path in domain_files:
            # Skip test files
            if "test" in str(file_path):
                continue

            imports = get_imports_from_file(file_path)

            # Check for non-stdlib imports
            external_imports = []
            for imp in imports:
                root_module = imp.split(".")[0]

                # Skip relative imports and stdlib
                if (
                    not imp.startswith(".")
                    and root_module not in allowed_stdlib
                    and not imp.startswith("__")
                ):
                    external_imports.append(imp)

            if external_imports:
                violations.append(
                    {
                        "file": str(file_path.relative_to(project_root)),
                        "imports": external_imports,
                    }
                )

        # Filter out known acceptable imports
        filtered_violations = []
        for v in violations:
            filtered_imports = [
                imp
                for imp in v["imports"]
                if not any(
                    imp.startswith(prefix)
                    for prefix in [
                        "engine.",  # Internal engine imports are OK
                        "domain.",  # Internal domain imports are OK
                        "tests.",  # Test imports
                    ]
                )
            ]
            if filtered_imports:
                v["imports"] = filtered_imports
                filtered_violations.append(v)

        assert (
            not filtered_violations
        ), "Domain layer should have no external dependencies:\n" + "\n".join(
            f"  {v['file']} imports: {', '.join(v['imports'])}"
            for v in filtered_violations
        )

    def test_no_circular_dependencies(self, project_root):
        """Test that there are no circular dependencies between layers"""
        # Define layer dependencies
        layer_deps = {
            "api": ["application", "infrastructure"],
            "application": ["domain", "infrastructure"],
            "infrastructure": ["domain"],
            "domain": [],
        }

        # Check each layer
        for layer, allowed_deps in layer_deps.items():
            layer_files = get_python_files_in_layer(project_root / layer)

            for file_path in layer_files:
                if "test" in str(file_path):
                    continue

                imports = get_imports_from_file(file_path)

                # Check imports against allowed dependencies
                for imp in imports:
                    for other_layer in layer_deps:
                        if other_layer == layer:
                            continue

                        if imp.startswith(f"{other_layer}."):
                            if other_layer not in allowed_deps:
                                pytest.fail(
                                    f"Circular dependency: {layer}/{file_path.name} "
                                    f"imports from {other_layer} layer ({imp})"
                                )


class TestInterfaceUsage:
    """Test that interfaces are used correctly"""

    def test_infrastructure_implements_interfaces(self, project_root):
        """Test that infrastructure implementations follow interfaces"""
        impl_file = (
            project_root
            / "infrastructure"
            / "websocket"
            / "contract_implementations.py"
        )

        if impl_file.exists():
            content = impl_file.read_text()

            # Check that implementations inherit from interfaces
            assert "IWebSocketConnection" in content
            assert "IConnectionManager" in content
            assert "IBroadcaster" in content
            assert "IWebSocketInfrastructure" in content

            # Check that classes implement interfaces
            assert "class FastAPIWebSocketConnection(IWebSocketConnection)" in content
            assert "class WebSocketConnectionManager(IConnectionManager)" in content
            assert "class WebSocketBroadcaster(IBroadcaster)" in content
            assert "class WebSocketInfrastructure(IWebSocketInfrastructure)" in content

    def test_application_implements_interfaces(self, project_root):
        """Test that application implementations follow interfaces"""
        impl_file = (
            project_root / "application" / "websocket" / "contract_implementations.py"
        )

        if impl_file.exists():
            content = impl_file.read_text()

            # Check that implementations inherit from interfaces
            assert "IMessageHandler" in content
            assert "IMessageRouter" in content
            assert "IConnectionContext" in content
            assert "IEventPublisher" in content
            assert "IMessageValidator" in content

            # Check that classes implement interfaces
            assert "class UseCaseMessageHandler(IMessageHandler)" in content
            assert "class ApplicationMessageRouter(IMessageRouter)" in content
            assert "class WebSocketConnectionContext(IConnectionContext)" in content
            assert "class ApplicationEventPublisher(IEventPublisher)" in content
            assert "class ApplicationMessageValidator(IMessageValidator)" in content


class TestPackageStructure:
    """Test that package structure follows architectural guidelines"""

    def test_layer_directories_exist(self, project_root):
        """Test that all architectural layers have directories"""
        expected_layers = ["api", "application", "domain", "infrastructure"]

        for layer in expected_layers:
            layer_dir = project_root / layer
            assert layer_dir.exists(), f"Layer directory '{layer}' should exist"

    def test_interfaces_directories(self, project_root):
        """Test that interface directories exist where needed"""
        interface_locations = ["application/interfaces", "infrastructure/interfaces"]

        for location in interface_locations:
            interface_dir = project_root / location
            assert (
                interface_dir.exists()
            ), f"Interface directory '{location}' should exist"

    def test_no_implementation_in_interfaces(self, project_root):
        """Test that interface directories only contain interfaces"""
        interface_dirs = [
            project_root / "application" / "interfaces",
            project_root / "infrastructure" / "interfaces",
        ]

        for interface_dir in interface_dirs:
            if not interface_dir.exists():
                continue

            for file_path in interface_dir.glob("*.py"):
                if file_path.name == "__init__.py":
                    continue

                content = file_path.read_text()

                # Check that files contain abstract classes
                assert (
                    "ABC" in content or "Protocol" in content
                ), f"Interface file {file_path} should contain abstract classes"

                # Check that there are no concrete implementations
                # (This is a simple check - could be more sophisticated)
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if line.strip().startswith("def ") and not line.strip().startswith(
                        "def __"
                    ):
                        # Check if next lines contain actual implementation
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line and not (
                                next_line.startswith('"""')
                                or next_line.startswith("'''")
                                or next_line == "pass"
                                or next_line.startswith("...")
                            ):
                                # Skip if it's an abstract method
                                if any(
                                    "@abstractmethod" in lines[j]
                                    for j in range(max(0, i - 5), i)
                                ):
                                    continue

                                pytest.fail(
                                    f"Interface file {file_path} appears to contain "
                                    f"concrete implementation at line {i+1}"
                                )
