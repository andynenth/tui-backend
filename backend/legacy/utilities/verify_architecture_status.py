#!/usr/bin/env python3
"""
Architecture Status Verification Tool

Comprehensive tool to verify whether the project is running on clean architecture or legacy code.
Provides definitive evidence of the current architecture state through multiple verification methods.
"""

import asyncio
import sys
import os
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ArchitectureVerifier:
    """Comprehensive architecture status verification system."""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.verification_results = {}
        self.evidence = []
        self.confidence_score = 0
        
    def add_evidence(self, category: str, evidence: str, confidence: int, status: str):
        """Add evidence for architecture determination."""
        self.evidence.append({
            "category": category,
            "evidence": evidence,
            "confidence": confidence,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
        
    async def verify_feature_flags(self) -> Dict[str, Any]:
        """Verify feature flag status from the application."""
        logger.info("🏁 Checking feature flag status...")
        
        results = {
            "method": "feature_flags",
            "status": "unknown",
            "flags": {},
            "architecture": "unknown",
            "confidence": 0
        }
        
        try:
            # Try to import and check feature flags directly
            from infrastructure.feature_flags import get_feature_flags
            
            flags = get_feature_flags()
            flag_values = flags.get_all_flags()
            
            results["flags"] = flag_values
            
            # Check critical architecture flags
            clean_architecture_flags = [
                "use_clean_architecture",
                "use_domain_events", 
                "use_application_layer",
                "use_new_repositories"
            ]
            
            adapter_flags = [
                "use_connection_adapters",
                "use_room_adapters", 
                "use_game_adapters",
                "use_lobby_adapters"
            ]
            
            # Count enabled clean architecture flags
            clean_enabled = sum(1 for flag in clean_architecture_flags if flag_values.get(flag, False))
            adapter_enabled = sum(1 for flag in adapter_flags if flag_values.get(flag, False))
            
            total_flags = len(clean_architecture_flags) + len(adapter_flags)
            enabled_flags = clean_enabled + adapter_enabled
            
            # Determine architecture based on flags
            if enabled_flags >= total_flags * 0.8:  # 80% or more enabled
                results["architecture"] = "clean"
                results["status"] = "clean_architecture"
                results["confidence"] = 90
                self.add_evidence(
                    "Feature Flags",
                    f"{enabled_flags}/{total_flags} clean architecture flags enabled",
                    90,
                    "clean"
                )
            elif enabled_flags > 0:
                results["architecture"] = "hybrid"
                results["status"] = "partial_migration"
                results["confidence"] = 60
                self.add_evidence(
                    "Feature Flags", 
                    f"{enabled_flags}/{total_flags} clean architecture flags enabled (partial)",
                    60,
                    "hybrid"
                )
            else:
                results["architecture"] = "legacy"
                results["status"] = "legacy_code"
                results["confidence"] = 85
                self.add_evidence(
                    "Feature Flags",
                    f"No clean architecture flags enabled ({enabled_flags}/{total_flags})",
                    85,
                    "legacy"
                )
                
        except Exception as e:
            results["error"] = str(e)
            results["confidence"] = 0
            self.add_evidence(
                "Feature Flags",
                f"Could not access feature flags: {e}",
                0,
                "error"
            )
            
        return results
    
    def verify_environment_variables(self) -> Dict[str, Any]:
        """Check environment variables for architecture settings."""
        logger.info("🌍 Checking environment variables...")
        
        results = {
            "method": "environment_variables",
            "variables": {},
            "architecture": "unknown",
            "confidence": 0
        }
        
        # Check feature flag environment variables
        flag_env_vars = [
            "FF_USE_CLEAN_ARCHITECTURE",
            "FF_USE_DOMAIN_EVENTS",
            "FF_USE_APPLICATION_LAYER", 
            "FF_USE_NEW_REPOSITORIES",
            "FF_USE_CONNECTION_ADAPTERS",
            "FF_USE_ROOM_ADAPTERS",
            "FF_USE_GAME_ADAPTERS",
            "FF_USE_LOBBY_ADAPTERS"
        ]
        
        # Check general architecture variables
        arch_env_vars = [
            "ENABLE_CLEAN_ARCHITECTURE",
            "CLEAN_ARCHITECTURE_ENABLED",
            "ADAPTER_ENABLED",
            "ARCHITECTURE_MODE"
        ]
        
        all_vars = flag_env_vars + arch_env_vars
        found_vars = {}
        clean_indicators = 0
        
        for var in all_vars:
            value = os.environ.get(var)
            if value is not None:
                found_vars[var] = value
                
                # Check if variable indicates clean architecture
                if value.lower() in ['true', '1', 'yes', 'on', 'enabled']:
                    clean_indicators += 1
                elif value.lower() in ['100', 'clean', 'new']:
                    clean_indicators += 1
                    
        results["variables"] = found_vars
        
        if clean_indicators >= 4:  # Strong indication of clean architecture
            results["architecture"] = "clean"
            results["confidence"] = 75
            self.add_evidence(
                "Environment Variables",
                f"{clean_indicators} environment variables indicate clean architecture",
                75,
                "clean"
            )
        elif clean_indicators > 0:
            results["architecture"] = "hybrid"
            results["confidence"] = 50
            self.add_evidence(
                "Environment Variables",
                f"{clean_indicators} environment variables indicate partial clean architecture",
                50,
                "hybrid"
            )
        elif found_vars:
            results["architecture"] = "legacy"
            results["confidence"] = 30
            self.add_evidence(
                "Environment Variables",
                f"Found {len(found_vars)} architecture variables but no clean architecture indicators",
                30,
                "legacy"
            )
        else:
            results["confidence"] = 0
            self.add_evidence(
                "Environment Variables",
                "No architecture-related environment variables found",
                0,
                "unknown"
            )
            
        return results
    
    async def verify_health_endpoints(self) -> Dict[str, Any]:
        """Check health endpoints for architecture status."""
        logger.info("🏥 Checking health endpoints...")
        
        results = {
            "method": "health_endpoints",
            "endpoints": {},
            "architecture": "unknown",
            "confidence": 0
        }
        
        # Test health endpoints
        endpoints_to_check = [
            "/api/health",
            "/api/health/detailed", 
            "/api/health/metrics"
        ]
        
        architecture_indicators = []
        
        for endpoint in endpoints_to_check:
            try:
                url = f"{self.server_url}{endpoint}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    results["endpoints"][endpoint] = {
                        "status": "success",
                        "data": data
                    }
                    
                    # Look for architecture indicators in response
                    if "components" in data:
                        components = data["components"]
                        clean_components = [
                            "application_layer", "domain_events", "clean_adapters",
                            "new_repositories", "event_store"
                        ]
                        
                        for component in clean_components:
                            if component in components:
                                architecture_indicators.append(f"Component {component} present")
                                
                    # Check for feature flags in response
                    if "feature_flags" in data:
                        flag_data = data["feature_flags"]
                        if isinstance(flag_data, dict):
                            clean_flags = [k for k, v in flag_data.items() 
                                         if "clean" in k.lower() and v]
                            if clean_flags:
                                architecture_indicators.append(f"Clean flags active: {clean_flags}")
                else:
                    results["endpoints"][endpoint] = {
                        "status": "error",
                        "status_code": response.status_code
                    }
                    
            except Exception as e:
                results["endpoints"][endpoint] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Determine architecture from health endpoint data
        if len(architecture_indicators) >= 2:
            results["architecture"] = "clean"
            results["confidence"] = 70
            self.add_evidence(
                "Health Endpoints",
                f"Clean architecture indicators found: {architecture_indicators}",
                70,
                "clean"
            )
        elif len(architecture_indicators) > 0:
            results["architecture"] = "hybrid"
            results["confidence"] = 40
            self.add_evidence(
                "Health Endpoints",
                f"Some clean architecture indicators: {architecture_indicators}",
                40,
                "hybrid"
            )
        else:
            results["confidence"] = 20
            self.add_evidence(
                "Health Endpoints",
                "No clean architecture indicators found in health endpoints",
                20,
                "legacy"
            )
            
        return results
    
    async def verify_migration_reports(self) -> Dict[str, Any]:
        """Check migration completion reports."""
        logger.info("📋 Checking migration reports...")
        
        results = {
            "method": "migration_reports",
            "reports": {},
            "architecture": "unknown",
            "confidence": 0
        }
        
        # Check for Phase 6 completion report
        report_files = [
            "PHASE_6_COMPLETION_REPORT.md",
            "tests/phase6/reports/final_performance_validation_report.json",
            "tests/phase6/reports/regression_test_report.json"
        ]
        
        completion_indicators = []
        
        for report_file in report_files:
            report_path = Path(report_file)
            if report_path.exists():
                try:
                    if report_file.endswith('.json'):
                        with open(report_path, 'r') as f:
                            data = json.load(f)
                            results["reports"][report_file] = data
                            
                            # Look for completion indicators
                            if "summary" in data:
                                summary = data["summary"]
                                if summary.get("all_requirements_met", False):
                                    completion_indicators.append(f"{report_file}: All requirements met")
                                if summary.get("ready_for_legacy_removal", False):
                                    completion_indicators.append(f"{report_file}: Ready for legacy removal")
                                    
                    else:  # Markdown file
                        with open(report_path, 'r') as f:
                            content = f.read()
                            results["reports"][report_file] = {"content_length": len(content)}
                            
                            # Look for completion keywords
                            if "✅ COMPLETE" in content:
                                completion_indicators.append(f"{report_file}: Marked as complete")
                            if "PRODUCTION READY" in content:
                                completion_indicators.append(f"{report_file}: Production ready")
                                
                except Exception as e:
                    results["reports"][report_file] = {"error": str(e)}
            else:
                results["reports"][report_file] = {"status": "not_found"}
        
        # Determine architecture from migration reports
        if len(completion_indicators) >= 3:
            results["architecture"] = "clean"
            results["confidence"] = 95
            self.add_evidence(
                "Migration Reports",
                f"Strong migration completion evidence: {completion_indicators}",
                95,
                "clean"
            )
        elif len(completion_indicators) > 0:
            results["architecture"] = "hybrid"
            results["confidence"] = 60
            self.add_evidence(
                "Migration Reports", 
                f"Some migration completion evidence: {completion_indicators}",
                60,
                "hybrid"
            )
        else:
            results["confidence"] = 10
            self.add_evidence(
                "Migration Reports",
                "No migration completion evidence found",
                10,
                "legacy"
            )
            
        return results
    
    async def verify_code_structure(self) -> Dict[str, Any]:
        """Verify the presence of clean architecture code structure."""
        logger.info("🏗️ Checking code structure...")
        
        results = {
            "method": "code_structure",
            "structure": {},
            "architecture": "unknown", 
            "confidence": 0
        }
        
        # Check for clean architecture directories
        clean_arch_paths = [
            "domain/",
            "application/",
            "infrastructure/",
            "infrastructure/adapters/",
            "infrastructure/repositories/",
            "application/use_cases/",
            "domain/entities/",
            "domain/services/"
        ]
        
        legacy_paths = [
            "legacy/",
            "old/", 
            "deprecated/"
        ]
        
        clean_indicators = 0
        legacy_indicators = 0
        
        for path in clean_arch_paths:
            if Path(path).exists():
                file_count = len(list(Path(path).rglob("*.py")))
                results["structure"][path] = {"exists": True, "files": file_count}
                if file_count > 0:
                    clean_indicators += 1
            else:
                results["structure"][path] = {"exists": False}
                
        for path in legacy_paths:
            if Path(path).exists():
                file_count = len(list(Path(path).rglob("*.py")))
                results["structure"][path] = {"exists": True, "files": file_count}
                if file_count > 0:
                    legacy_indicators += 1
            else:
                results["structure"][path] = {"exists": False}
        
        # Determine architecture from code structure
        if clean_indicators >= 6:  # Most clean architecture directories present
            results["architecture"] = "clean"
            results["confidence"] = 80
            self.add_evidence(
                "Code Structure",
                f"{clean_indicators}/{len(clean_arch_paths)} clean architecture directories present",
                80,
                "clean"
            )
        elif clean_indicators >= 3:
            results["architecture"] = "hybrid"
            results["confidence"] = 50
            self.add_evidence(
                "Code Structure",
                f"{clean_indicators}/{len(clean_arch_paths)} clean architecture directories present (partial)",
                50,
                "hybrid"
            )
        else:
            results["architecture"] = "legacy"
            results["confidence"] = 30
            self.add_evidence(
                "Code Structure",
                f"Only {clean_indicators}/{len(clean_arch_paths)} clean architecture directories present",
                30,
                "legacy"
            )
            
        return results
    
    def calculate_final_determination(self) -> Dict[str, Any]:
        """Calculate final architecture determination based on all evidence."""
        logger.info("🧮 Calculating final determination...")
        
        # Weight different verification methods
        method_weights = {
            "feature_flags": 0.3,      # Most reliable indicator
            "migration_reports": 0.25,  # Strong evidence of completion
            "environment_variables": 0.2,  # Configuration evidence
            "health_endpoints": 0.15,   # Runtime evidence
            "code_structure": 0.1       # Static evidence
        }
        
        architecture_scores = {
            "clean": 0,
            "hybrid": 0,
            "legacy": 0
        }
        
        total_confidence = 0
        verification_count = 0
        
        # Calculate weighted scores
        for result in self.verification_results.values():
            method = result["method"]
            architecture = result.get("architecture", "unknown")
            confidence = result.get("confidence", 0)
            weight = method_weights.get(method, 0.1)
            
            if architecture in architecture_scores:
                weighted_score = (confidence / 100) * weight
                architecture_scores[architecture] += weighted_score
                total_confidence += confidence * weight
                verification_count += 1
        
        # Determine final architecture
        final_architecture = max(architecture_scores, key=architecture_scores.get)
        final_confidence = total_confidence / max(verification_count, 1)
        
        # Determine status
        if final_architecture == "clean" and final_confidence >= 70:
            status = "CLEAN_ARCHITECTURE"
            message = "System is definitively running on clean architecture"
        elif final_architecture == "clean" and final_confidence >= 50:
            status = "LIKELY_CLEAN"
            message = "System is likely running on clean architecture"
        elif final_architecture == "hybrid":
            status = "PARTIAL_MIGRATION"
            message = "System is in partial migration state (hybrid)"
        elif final_architecture == "legacy" and final_confidence >= 70:
            status = "LEGACY_CODE"
            message = "System is definitively running on legacy code"
        elif final_architecture == "legacy" and final_confidence >= 50:
            status = "LIKELY_LEGACY"
            message = "System is likely running on legacy code"
        else:
            status = "UNKNOWN"
            message = "Cannot determine architecture status with confidence"
        
        return {
            "final_determination": {
                "architecture": final_architecture,
                "status": status,
                "confidence": final_confidence,
                "message": message,
                "scores": architecture_scores
            },
            "evidence_summary": {
                "total_evidence_points": len(self.evidence),
                "verification_methods": len(self.verification_results),
                "high_confidence_evidence": len([e for e in self.evidence if e["confidence"] >= 70]),
                "clean_evidence": len([e for e in self.evidence if e["status"] == "clean"]),
                "legacy_evidence": len([e for e in self.evidence if e["status"] == "legacy"]),
                "hybrid_evidence": len([e for e in self.evidence if e["status"] == "hybrid"])
            }
        }
    
    async def run_full_verification(self) -> Dict[str, Any]:
        """Run complete architecture verification."""
        logger.info("🔍 Starting complete architecture verification...")
        
        # Run all verification methods
        self.verification_results["feature_flags"] = await self.verify_feature_flags()
        self.verification_results["environment_variables"] = self.verify_environment_variables() 
        self.verification_results["health_endpoints"] = await self.verify_health_endpoints()
        self.verification_results["migration_reports"] = await self.verify_migration_reports()
        self.verification_results["code_structure"] = await self.verify_code_structure()
        
        # Calculate final determination
        final_results = self.calculate_final_determination()
        
        # Compile complete report
        complete_report = {
            "timestamp": time.time(),
            "verification_methods": self.verification_results,
            "evidence": self.evidence,
            **final_results
        }
        
        return complete_report
    
    def print_results(self, results: Dict[str, Any]):
        """Print human-readable verification results."""
        final = results["final_determination"]
        evidence_summary = results["evidence_summary"]
        
        print("\\n" + "="*60)
        print("🏗️  ARCHITECTURE STATUS VERIFICATION REPORT")
        print("="*60)
        
        print(f"\\n📊 FINAL DETERMINATION:")
        print(f"   Architecture: {final['architecture'].upper()}")
        print(f"   Status: {final['status']}")
        print(f"   Confidence: {final['confidence']:.1f}%")
        print(f"   Message: {final['message']}")
        
        print(f"\\n📈 EVIDENCE SUMMARY:")
        print(f"   Total Evidence Points: {evidence_summary['total_evidence_points']}")
        print(f"   Verification Methods: {evidence_summary['verification_methods']}")
        print(f"   High Confidence Evidence: {evidence_summary['high_confidence_evidence']}")
        print(f"   Clean Architecture Evidence: {evidence_summary['clean_evidence']}")
        print(f"   Legacy Code Evidence: {evidence_summary['legacy_evidence']}")
        print(f"   Hybrid Evidence: {evidence_summary['hybrid_evidence']}")
        
        print(f"\\n🔍 VERIFICATION METHODS:")
        for method, result in results["verification_methods"].items():
            status_icon = "✅" if result.get("confidence", 0) >= 70 else "⚠️" if result.get("confidence", 0) >= 40 else "❌"
            print(f"   {status_icon} {method}: {result.get('architecture', 'unknown')} ({result.get('confidence', 0):.0f}% confidence)")
        
        print(f"\\n📝 DETAILED EVIDENCE:")
        for evidence in results["evidence"]:
            confidence_icon = "🔴" if evidence["confidence"] >= 80 else "🟡" if evidence["confidence"] >= 50 else "⚪"
            status_icon = "🟢" if evidence["status"] == "clean" else "🔴" if evidence["status"] == "legacy" else "🟡"
            print(f"   {confidence_icon}{status_icon} [{evidence['category']}] {evidence['evidence']} ({evidence['confidence']}%)")
        
        print("\\n" + "="*60)
        
        # Print recommendation
        if final["status"] == "CLEAN_ARCHITECTURE":
            print("✅ RESULT: Your project is running on CLEAN ARCHITECTURE!")
        elif final["status"] in ["LIKELY_CLEAN"]:
            print("✅ RESULT: Your project is likely running on CLEAN ARCHITECTURE")
        elif final["status"] == "PARTIAL_MIGRATION":
            print("⚠️ RESULT: Your project is in PARTIAL MIGRATION state (hybrid)")
        elif final["status"] in ["LEGACY_CODE", "LIKELY_LEGACY"]:
            print("❌ RESULT: Your project is running on LEGACY CODE")
        else:
            print("❓ RESULT: Cannot determine architecture status with confidence")
            
        print("="*60 + "\\n")


async def main():
    """Main verification function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Architecture Status Verification Tool")
    parser.add_argument("--server-url", default="http://localhost:8000", help="Server URL for health checks")
    parser.add_argument("--output-file", help="Save results to JSON file")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    
    args = parser.parse_args()
    
    try:
        verifier = ArchitectureVerifier(args.server_url)
        results = await verifier.run_full_verification()
        
        if not args.quiet:
            verifier.print_results(results)
        
        if args.output_file:
            with open(args.output_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {args.output_file}")
        
        # Exit with appropriate code
        final_status = results["final_determination"]["status"]
        if final_status in ["CLEAN_ARCHITECTURE", "LIKELY_CLEAN"]:
            sys.exit(0)  # Clean architecture
        elif final_status == "PARTIAL_MIGRATION":
            sys.exit(1)  # Partial migration
        elif final_status in ["LEGACY_CODE", "LIKELY_LEGACY"]:
            sys.exit(2)  # Legacy code
        else:
            sys.exit(3)  # Unknown
            
    except Exception as e:
        logger.error(f"Verification error: {e}")
        print(f"❌ Error during verification: {e}")
        sys.exit(4)


if __name__ == "__main__":
    asyncio.run(main())