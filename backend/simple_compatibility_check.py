#!/usr/bin/env python3
"""
Simple compatibility check without external dependencies
"""

from pathlib import Path
import json
from datetime import datetime

def check_compatibility():
    """Check if we're ready for refactoring"""
    print("Frontend Compatibility Check")
    print("=" * 50)
    
    # Check golden masters
    golden_masters_dir = Path("tests/contracts/golden_masters")
    masters = list(golden_masters_dir.glob("*.json")) if golden_masters_dir.exists() else []
    
    print(f"\n1. Golden Masters:")
    print(f"   Found: {len(masters)} files")
    print(f"   Expected: ~22 (one per test scenario)")
    
    if len(masters) >= 20:
        print("   ✅ Status: READY")
    else:
        print("   ❌ Status: NOT READY - capture golden masters first")
    
    # Check contract definitions
    try:
        from tests.contracts.websocket_contracts import get_all_contracts
        contracts = get_all_contracts()
        print(f"\n2. Contract Definitions:")
        print(f"   Found: {len(contracts)} contracts")
        print("   ✅ Status: ALL DEFINED")
    except Exception as e:
        print(f"\n2. Contract Definitions:")
        print(f"   ❌ Error: {e}")
    
    # Check directories
    print(f"\n3. Directory Structure:")
    dirs = ["tests/contracts", "tests/behavioral", "shadow_mode_data"]
    all_exist = True
    for d in dirs:
        exists = Path(d).exists()
        status = "✅" if exists else "❌"
        print(f"   {status} {d}")
        if not exists:
            all_exist = False
    
    # Overall status
    print(f"\n" + "=" * 50)
    if len(masters) >= 20 and all_exist:
        print("✅ READY FOR REFACTORING!")
        print("\nYou can now:")
        print("1. Create a new branch: git checkout -b phase-1-clean-api-layer")
        print("2. Start implementing adapters")
        print("3. Run contract tests after each adapter")
    else:
        print("❌ NOT READY YET")
        print("\nRequired actions:")
        if len(masters) < 20:
            print("- Run: python3 tests/contracts/capture_golden_masters.py")
        if not all_exist:
            print("- Create missing directories")
    
    # Save report
    report = {
        "generated_at": datetime.now().isoformat(),
        "golden_masters_count": len(masters),
        "contracts_count": len(contracts) if 'contracts' in locals() else 0,
        "ready_for_refactoring": len(masters) >= 20 and all_exist
    }
    
    with open("compatibility_report.json", 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to: compatibility_report.json")

if __name__ == "__main__":
    check_compatibility()