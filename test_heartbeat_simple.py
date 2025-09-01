#!/usr/bin/env python3
"""
Simple test for enhanced heartbeat functionality
"""

import asyncio
import json
import requests

BASE_URL = "http://localhost:5050"


def test_heartbeat_via_rest():
    """Test heartbeat recording via REST API"""
    print("\n=== Testing Heartbeat Recording ===")
    
    # First check if any debug endpoints are available
    try:
        response = requests.get(f"{BASE_URL}/api/debug/player-activity/test_room")
        print(f"Player activity endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error accessing debug endpoint: {e}")
    
    # Check hang diagnostics
    try:
        response = requests.get(f"{BASE_URL}/api/debug/hang-diagnostics")
        print(f"\nHang diagnostics endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error accessing hang diagnostics: {e}")


def main():
    """Run simple tests"""
    print("🧪 Testing Player Activity Monitor - Simple Test")
    print("=" * 50)
    
    test_heartbeat_via_rest()
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    main()