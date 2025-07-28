#!/usr/bin/env python3
"""
Analyze Golden Master Mismatches
Helps identify what differences exist between adapter and legacy responses.
"""

import json
import os
from typing import Dict, Any, List
from collections import defaultdict


def load_golden_masters(directory: str) -> Dict[str, Any]:
    """Load all golden master files"""
    masters = {}
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            with open(os.path.join(directory, filename), 'r') as f:
                data = json.load(f)
                masters[filename.replace('.json', '')] = data
    return masters


def analyze_mismatches():
    """Analyze golden master mismatches"""
    golden_dir = "tests/contracts/golden_masters"
    
    if not os.path.exists(golden_dir):
        print("❌ Golden masters directory not found")
        return
    
    masters = load_golden_masters(golden_dir)
    
    print("🔍 Analyzing Golden Master Mismatches")
    print("=" * 60)
    
    # Group by action type
    by_action = defaultdict(list)
    for name, data in masters.items():
        action = data.get('name', 'unknown')
        by_action[action].append(name)
    
    print("\n📊 Golden Masters by Action:")
    print("-" * 40)
    for action, files in sorted(by_action.items()):
        print(f"{action:<20} {len(files)} variants")
    
    # Sample analysis of specific mismatches
    print("\n🔍 Sample Mismatch Analysis:")
    print("-" * 40)
    
    # Look at a few specific examples
    sample_actions = ['ping', 'create_room', 'join_room']
    
    for action in sample_actions:
        action_files = by_action.get(action, [])
        if action_files:
            print(f"\n{action.upper()} variants:")
            for file_id in action_files[:3]:  # Show first 3
                data = masters[file_id]
                request = data.get('request', {})
                response = data.get('response', {})
                print(f"  {file_id}:")
                print(f"    Request: {json.dumps(request, separators=(',', ':'))}")
                print(f"    Response event: {response.get('event', 'N/A')}")
                if 'data' in response:
                    print(f"    Response data keys: {list(response['data'].keys())}")


def compare_adapter_with_legacy():
    """
    Run a specific comparison to understand differences
    """
    print("\n\n🔬 Detailed Comparison Example")
    print("=" * 60)
    
    # We'll need to actually run the adapter and compare
    # For now, let's just show what fields might differ
    
    print("\nCommon differences to check:")
    print("1. Field presence - adapter might include/exclude fields")
    print("2. Field names - slightly different naming conventions")
    print("3. Field types - string vs number, etc.")
    print("4. Default values - null vs empty string vs missing")
    print("5. Timestamps - server_time, timestamps might differ")
    print("6. IDs - room_id, player_id generation might differ")
    
    print("\n📋 Next Steps:")
    print("1. Run adapters in shadow mode to capture actual differences")
    print("2. Update adapters to match legacy behavior exactly")
    print("3. Or update golden masters if adapter behavior is preferred")
    print("4. Document any intentional differences")


if __name__ == "__main__":
    analyze_mismatches()
    compare_adapter_with_legacy()