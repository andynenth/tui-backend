#!/usr/bin/env python3
"""
Quick Architecture Check

Simple command-line tool for fast architecture status verification.
Provides instant feedback on whether the system is running clean architecture or legacy code.
"""

import sys
import requests
import json
from pathlib import Path

def check_via_endpoint(server_url: str = "http://localhost:8000") -> str:
    """Check architecture status via health endpoint."""
    try:
        url = f"{server_url}/api/health/architecture-status"
        response = requests.get(url, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            arch_status = data.get("architecture_status", "unknown")
            confidence = data.get("confidence_percentage", 0)
            
            if arch_status == "clean_architecture":
                return f"✅ CLEAN ARCHITECTURE ({confidence}% confidence)"
            elif arch_status == "partial_migration":
                return f"⚠️ PARTIAL MIGRATION ({confidence}% confidence)"
            elif arch_status == "legacy_code":
                return f"❌ LEGACY CODE ({confidence}% confidence)"
            else:
                return f"❓ UNKNOWN STATUS ({confidence}% confidence)"
        else:
            return f"❌ SERVER ERROR (HTTP {response.status_code})"
            
    except Exception as e:
        return f"❌ CONNECTION ERROR: {e}"

def check_via_feature_flags() -> str:
    """Check architecture status via feature flags directly."""
    try:
        # Add current directory to Python path for imports
        sys.path.append(str(Path(__file__).parent))
        
        from infrastructure.feature_flags import get_feature_flags
        
        flags = get_feature_flags()
        flag_values = flags.get_all_flags()
        
        # Check critical flags
        critical_flags = [
            "use_clean_architecture",
            "use_domain_events", 
            "use_application_layer",
            "use_new_repositories"
        ]
        
        enabled = sum(1 for flag in critical_flags if flag_values.get(flag, False))
        total = len(critical_flags)
        percentage = (enabled / total) * 100
        
        if percentage >= 80:
            return f"✅ CLEAN ARCHITECTURE ({enabled}/{total} flags enabled)"
        elif percentage > 0:
            return f"⚠️ PARTIAL MIGRATION ({enabled}/{total} flags enabled)" 
        else:
            return f"❌ LEGACY CODE ({enabled}/{total} flags enabled)"
            
    except Exception as e:
        return f"❌ FEATURE FLAG ERROR: {e}"

def check_via_reports() -> str:
    """Check architecture status via migration reports."""
    completion_indicators = 0
    
    # Check for completion reports
    report_files = [
        "PHASE_6_COMPLETION_REPORT.md",
        "tests/phase6/reports/final_performance_validation_report.json",
        "tests/phase6/reports/regression_test_report.json"
    ]
    
    for report_file in report_files:
        if Path(report_file).exists():
            completion_indicators += 1
            
    if completion_indicators >= 3:
        return f"✅ CLEAN ARCHITECTURE (All migration reports present)"
    elif completion_indicators > 0:
        return f"⚠️ PARTIAL MIGRATION ({completion_indicators}/3 reports present)"
    else:
        return f"❌ LEGACY CODE (No migration reports found)"

def main():
    """Main quick check function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Quick Architecture Status Check")
    parser.add_argument("--method", choices=["endpoint", "flags", "reports", "all"], 
                       default="all", help="Check method")
    parser.add_argument("--server-url", default="http://localhost:8000", 
                       help="Server URL for endpoint check")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    args = parser.parse_args()
    
    results = {}
    
    if args.method in ["endpoint", "all"]:
        results["endpoint"] = check_via_endpoint(args.server_url)
        
    if args.method in ["flags", "all"]:
        results["feature_flags"] = check_via_feature_flags()
        
    if args.method in ["reports", "all"]:
        results["migration_reports"] = check_via_reports()
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("🏗️ Architecture Status Check")
        print("=" * 40)
        
        for method, result in results.items():
            print(f"{method.replace('_', ' ').title()}: {result}")
        
        print("=" * 40)
        
        # Determine overall status
        clean_count = sum(1 for result in results.values() if "✅" in result)
        total_count = len(results)
        
        if clean_count == total_count:
            print("🎉 OVERALL: Clean Architecture Confirmed")
            sys.exit(0)
        elif clean_count > 0:
            print("🔄 OVERALL: Mixed Signals (Partial Migration)")
            sys.exit(1) 
        else:
            print("🚨 OVERALL: Legacy Code Detected")
            sys.exit(2)

if __name__ == "__main__":
    main()