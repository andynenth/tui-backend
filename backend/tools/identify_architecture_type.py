#!/usr/bin/env python3
"""
Architecture Type Identification Tool

Analyzes Python files to determine if they belong to legacy or clean architecture.
Generates comprehensive reports for migration planning.

Usage:
    python identify_architecture_type.py [--file FILE] [--directory DIR] [--output OUTPUT]
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class FileAnalysis:
    """Analysis result for a single file"""

    file_path: str
    architecture_type: str  # 'legacy', 'clean', 'hybrid', 'bridge'
    confidence: float  # 0.0 to 1.0
    indicators: List[str]
    imports: List[str]
    dependencies: List[str]
    recommendation: str


class ArchitectureAnalyzer:
    """Analyzes files to determine architecture type"""

    # Clean architecture directory patterns
    CLEAN_DIRS = [
        "domain/",
        "application/",
        "infrastructure/",
        "api/adapters/",
        "api/dto/",
        "api/interfaces/",
    ]

    # Legacy directory patterns
    LEGACY_DIRS = ["engine/", "models/", "backend/engine/", "backend/models/"]

    # Special cases
    SPECIAL_CASES = {
        "engine/state_machine/": "enterprise",
        "api/routes/ws.py": "hybrid",
        "api/routes/ws_adapter_wrapper.py": "bridge",
        "socket_manager.py": "legacy",
        "shared_instances.py": "legacy",
    }

    # Legacy import patterns
    LEGACY_IMPORTS = [
        r"from backend\.socket_manager",
        r"from socket_manager",
        r"import backend\.socket_manager",
        r"from shared_instances",
        r"from engine\.(?!state_machine)",
        r"from backend\.engine\.(?!state_machine)",
        r"shared_room_manager",
        r"shared_bot_manager",
    ]

    # Clean architecture import patterns
    CLEAN_IMPORTS = [
        r"from domain\.",
        r"from application\.",
        r"from infrastructure\.",
        r"from api\.adapters\.",
        r"from \.\.domain",
        r"from \.\.application",
        r"from \.\.infrastructure",
    ]

    # Pattern indicators
    LEGACY_PATTERNS = [
        r"await broadcast\(",  # Direct broadcasting
        r"shared_.*_manager",  # Shared global state
        r"class.*Manager.*:.*\n.*async def.*broadcast",  # Manager with broadcast
        r"backend\.socket_manager",  # Direct socket manager usage
        r"LEGACY|legacy",  # Explicit legacy markers
    ]

    CLEAN_PATTERNS = [
        r"def __init__.*Repository.*:",  # Repository injection
        r"def __init__.*Service.*:",  # Service injection
        r"def __init__.*Publisher.*:",  # Publisher injection
        r"@inject",  # Dependency injection decorator
        r"async def publish.*Event",  # Event publishing
        r"class.*UseCase",  # Use case pattern
        r"class.*Repository\(",  # Repository interface
        r"class.*DTO\(",  # DTO pattern
        r"raise.*DomainException",  # Domain exceptions
    ]

    def __init__(self):
        self.results: List[FileAnalysis] = []

    def analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analyze a single file to determine its architecture type"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return FileAnalysis(
                file_path=str(file_path),
                architecture_type="error",
                confidence=0.0,
                indicators=[f"Error reading file: {str(e)}"],
                imports=[],
                dependencies=[],
                recommendation="Fix file access issues",
            )

        # Check special cases first
        relative_path = str(file_path).replace(str(Path.cwd()) + "/", "")
        for pattern, arch_type in self.SPECIAL_CASES.items():
            if pattern in relative_path:
                return FileAnalysis(
                    file_path=relative_path,
                    architecture_type=arch_type,
                    confidence=1.0,
                    indicators=[f"Special case: {pattern}"],
                    imports=self._extract_imports(content),
                    dependencies=self._extract_dependencies(content),
                    recommendation=self._get_recommendation(arch_type),
                )

        # Analyze based on directory structure
        dir_score = self._analyze_directory(relative_path)

        # Analyze imports
        imports = self._extract_imports(content)
        import_score = self._analyze_imports(imports)

        # Analyze patterns
        pattern_score = self._analyze_patterns(content)

        # Calculate final score and type
        arch_type, confidence = self._calculate_type(
            dir_score, import_score, pattern_score
        )

        # Get indicators
        indicators = self._get_indicators(relative_path, imports, content, arch_type)

        return FileAnalysis(
            file_path=relative_path,
            architecture_type=arch_type,
            confidence=confidence,
            indicators=indicators,
            imports=imports,
            dependencies=self._extract_dependencies(content),
            recommendation=self._get_recommendation(arch_type),
        )

    def _analyze_directory(self, file_path: str) -> Dict[str, float]:
        """Analyze directory structure"""
        scores = {"clean": 0.0, "legacy": 0.0}

        for clean_dir in self.CLEAN_DIRS:
            if clean_dir in file_path:
                scores["clean"] = 1.0
                break

        for legacy_dir in self.LEGACY_DIRS:
            if legacy_dir in file_path and "state_machine" not in file_path:
                scores["legacy"] = 1.0
                break

        return scores

    def _analyze_imports(self, imports: List[str]) -> Dict[str, float]:
        """Analyze import statements"""
        clean_count = 0
        legacy_count = 0

        for imp in imports:
            for pattern in self.LEGACY_IMPORTS:
                if re.search(pattern, imp):
                    legacy_count += 1
                    break

            for pattern in self.CLEAN_IMPORTS:
                if re.search(pattern, imp):
                    clean_count += 1
                    break

        total = max(clean_count + legacy_count, 1)
        return {"clean": clean_count / total, "legacy": legacy_count / total}

    def _analyze_patterns(self, content: str) -> Dict[str, float]:
        """Analyze code patterns"""
        clean_matches = 0
        legacy_matches = 0

        for pattern in self.LEGACY_PATTERNS:
            legacy_matches += len(re.findall(pattern, content, re.MULTILINE))

        for pattern in self.CLEAN_PATTERNS:
            clean_matches += len(re.findall(pattern, content, re.MULTILINE))

        total = max(clean_matches + legacy_matches, 1)
        return {"clean": clean_matches / total, "legacy": legacy_matches / total}

    def _calculate_type(
        self,
        dir_score: Dict[str, float],
        import_score: Dict[str, float],
        pattern_score: Dict[str, float],
    ) -> Tuple[str, float]:
        """Calculate final architecture type and confidence"""
        # Weight the different scores
        clean_score = (
            dir_score["clean"] * 0.4
            + import_score["clean"] * 0.4
            + pattern_score["clean"] * 0.2
        )

        legacy_score = (
            dir_score["legacy"] * 0.4
            + import_score["legacy"] * 0.4
            + pattern_score["legacy"] * 0.2
        )

        # Determine type
        if clean_score > 0.7:
            return "clean", clean_score
        elif legacy_score > 0.7:
            return "legacy", legacy_score
        elif clean_score > legacy_score:
            if legacy_score > 0.3:
                return "hybrid", 0.6
            return "clean", clean_score
        else:
            if clean_score > 0.3:
                return "hybrid", 0.6
            return "legacy", legacy_score

    def _extract_imports(self, content: str) -> List[str]:
        """Extract all import statements"""
        import_pattern = r"^\s*(from\s+[\w\.]+\s+import|import\s+[\w\.]+)"
        return re.findall(import_pattern, content, re.MULTILINE)

    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract file dependencies"""
        deps = set()

        # Extract from imports
        for imp in self._extract_imports(content):
            if "from" in imp:
                module = re.search(r"from\s+([\w\.]+)", imp)
                if module:
                    deps.add(module.group(1))
            else:
                module = re.search(r"import\s+([\w\.]+)", imp)
                if module:
                    deps.add(module.group(1))

        return sorted(list(deps))

    def _get_indicators(
        self, file_path: str, imports: List[str], content: str, arch_type: str
    ) -> List[str]:
        """Get indicators that led to the classification"""
        indicators = []

        # Directory indicators
        for clean_dir in self.CLEAN_DIRS:
            if clean_dir in file_path:
                indicators.append(f"Located in clean directory: {clean_dir}")

        for legacy_dir in self.LEGACY_DIRS:
            if legacy_dir in file_path and "state_machine" not in file_path:
                indicators.append(f"Located in legacy directory: {legacy_dir}")

        # Import indicators
        for imp in imports:
            for pattern in self.LEGACY_IMPORTS:
                if re.search(pattern, imp):
                    indicators.append(f"Legacy import: {imp}")
                    break

        # Pattern indicators
        if "await broadcast(" in content:
            indicators.append("Uses direct broadcasting (legacy pattern)")
        if "dependency injection" in content.lower() or "__init__" in content:
            if "Repository" in content or "Service" in content:
                indicators.append("Uses dependency injection (clean pattern)")

        return indicators[:5]  # Limit to top 5 indicators

    def _get_recommendation(self, arch_type: str) -> str:
        """Get recommendation based on architecture type"""
        recommendations = {
            "clean": "Ready for production. No migration needed.",
            "legacy": "Schedule for Phase 7 removal. Ensure clean architecture replacement exists.",
            "hybrid": "Review for cleanup. May need partial refactoring in Phase 7.",
            "bridge": "Keep as integration point. Review after Phase 7 for optimization.",
            "enterprise": "Modern implementation. Maintain current patterns.",
            "error": "Fix file access issues before analysis.",
        }
        return recommendations.get(arch_type, "Manual review recommended.")

    def analyze_directory(self, directory: Path) -> None:
        """Analyze all Python files in a directory"""
        for file_path in directory.rglob("*.py"):
            if "venv" not in str(file_path) and "__pycache__" not in str(file_path):
                result = self.analyze_file(file_path)
                self.results.append(result)

    def generate_report(self) -> Dict:
        """Generate comprehensive analysis report"""
        # Count by type
        type_counts = {}
        for result in self.results:
            type_counts[result.architecture_type] = (
                type_counts.get(result.architecture_type, 0) + 1
            )

        # Group files by type
        files_by_type = {}
        for result in self.results:
            if result.architecture_type not in files_by_type:
                files_by_type[result.architecture_type] = []
            files_by_type[result.architecture_type].append(result.file_path)

        # Find cross-dependencies
        cross_deps = []
        for result in self.results:
            if result.architecture_type == "clean":
                for dep in result.dependencies:
                    if any(
                        legacy in dep
                        for legacy in ["engine", "socket_manager", "shared_instances"]
                    ):
                        cross_deps.append(
                            {"clean_file": result.file_path, "legacy_dependency": dep}
                        )

        return {
            "analysis_date": datetime.now().isoformat(),
            "total_files": len(self.results),
            "type_distribution": type_counts,
            "files_by_type": files_by_type,
            "cross_dependencies": cross_deps,
            "recommendations": {
                "immediate_action": len(
                    [r for r in self.results if r.architecture_type == "error"]
                ),
                "phase_7_removal": len(
                    [r for r in self.results if r.architecture_type == "legacy"]
                ),
                "review_needed": len(
                    [r for r in self.results if r.architecture_type == "hybrid"]
                ),
            },
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Identify architecture type of Python files"
    )
    parser.add_argument("--file", "-f", type=Path, help="Analyze a single file")
    parser.add_argument(
        "--directory",
        "-d",
        type=Path,
        default=Path("backend"),
        help="Analyze all files in directory (default: backend)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file for detailed results (JSON format)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed analysis for each file",
    )

    args = parser.parse_args()
    analyzer = ArchitectureAnalyzer()

    if args.file:
        # Analyze single file
        result = analyzer.analyze_file(args.file)
        print(f"\nFile: {result.file_path}")
        print(f"Architecture Type: {result.architecture_type.upper()}")
        print(f"Confidence: {result.confidence:.1%}")
        print(f"Recommendation: {result.recommendation}")

        if result.indicators:
            print("\nIndicators:")
            for indicator in result.indicators:
                print(f"  - {indicator}")

        if args.verbose and result.dependencies:
            print("\nDependencies:")
            for dep in result.dependencies:
                print(f"  - {dep}")
    else:
        # Analyze directory
        print(f"Analyzing directory: {args.directory}")
        analyzer.analyze_directory(args.directory)

        # Generate report
        report = analyzer.generate_report()

        # Print summary
        print(f"\nAnalysis Summary:")
        print(f"Total files analyzed: {report['total_files']}")
        print(f"\nArchitecture Type Distribution:")
        for arch_type, count in report["type_distribution"].items():
            percentage = (count / report["total_files"]) * 100
            print(f"  {arch_type.upper()}: {count} files ({percentage:.1f}%)")

        print(f"\nRecommendations:")
        print(
            f"  Files needing immediate attention: {report['recommendations']['immediate_action']}"
        )
        print(
            f"  Files for Phase 7 removal: {report['recommendations']['phase_7_removal']}"
        )
        print(f"  Files needing review: {report['recommendations']['review_needed']}")

        if report["cross_dependencies"]:
            print(
                f"\n⚠️  WARNING: Found {len(report['cross_dependencies'])} clean files with legacy dependencies!"
            )
            if args.verbose:
                for dep in report["cross_dependencies"][:5]:
                    print(f"  - {dep['clean_file']} → {dep['legacy_dependency']}")

        # Save detailed results if requested
        if args.output:
            # Include full analysis details
            detailed_results = {
                "summary": report,
                "file_analyses": [asdict(r) for r in analyzer.results],
            }

            with open(args.output, "w") as f:
                json.dump(detailed_results, f, indent=2)
            print(f"\nDetailed results saved to: {args.output}")

        # Show files needing attention if verbose
        if args.verbose:
            legacy_files = [
                r for r in analyzer.results if r.architecture_type == "legacy"
            ]
            if legacy_files:
                print(f"\nLegacy files (first 10):")
                for result in legacy_files[:10]:
                    print(f"  - {result.file_path}")

            hybrid_files = [
                r for r in analyzer.results if r.architecture_type == "hybrid"
            ]
            if hybrid_files:
                print(f"\nHybrid files needing review:")
                for result in hybrid_files:
                    print(f"  - {result.file_path}")


if __name__ == "__main__":
    main()
