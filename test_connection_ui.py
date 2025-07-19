#!/usr/bin/env python3
"""
Test script for Task 1.4: Connection Status UI Components

This script tests the frontend components by checking:
1. File existence and basic syntax
2. Import dependencies
3. Component structure
"""

import os
import sys
import subprocess
import json

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✓ {description} exists at {filepath}")
        return True
    else:
        print(f"✗ {description} NOT FOUND at {filepath}")
        return False

def check_imports_in_file(filepath, imports, description):
    """Check if specific imports exist in a file"""
    if not os.path.exists(filepath):
        print(f"✗ Cannot check imports - {filepath} not found")
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    all_found = True
    for imp in imports:
        if imp in content:
            print(f"  ✓ Found import: {imp}")
        else:
            print(f"  ✗ Missing import: {imp}")
            all_found = False
    
    return all_found

def run_npm_commands():
    """Run npm commands to check for syntax errors"""
    print("\n" + "="*60)
    print("Running npm type-check and lint...")
    print("="*60)
    
    os.chdir('frontend')
    
    # Run type-check
    print("\n1. Running type-check...")
    try:
        result = subprocess.run(['npm', 'run', 'type-check'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✓ Type check passed")
        else:
            print("✗ Type check failed:")
            print(result.stdout)
            print(result.stderr)
    except Exception as e:
        print(f"✗ Could not run type-check: {e}")
    
    # Run lint
    print("\n2. Running lint...")
    try:
        result = subprocess.run(['npm', 'run', 'lint'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✓ Lint check passed")
        else:
            print("✗ Lint check failed:")
            print(result.stdout)
            print(result.stderr)
    except Exception as e:
        print(f"✗ Could not run lint: {e}")
    
    os.chdir('..')

def test_connection_ui_components():
    """Test all connection UI components"""
    print("="*60)
    print("Testing Connection Status UI Components (Task 1.4)")
    print("="*60)
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Test 1: Check all files exist
    print("\n1. Checking file existence:")
    files_to_check = [
        ("frontend/src/types/connection.ts", "TypeScript connection interfaces"),
        ("frontend/src/components/ConnectionStatusBadge.jsx", "ConnectionStatusBadge component"),
        ("frontend/src/components/DisconnectOverlay.jsx", "DisconnectOverlay component"),
        ("frontend/src/hooks/useDisconnectStatus.js", "useDisconnectStatus hook"),
        ("frontend/src/styles/connection-badges.css", "Connection badges CSS"),
        ("frontend/src/styles/disconnect-overlay.css", "Disconnect overlay CSS"),
    ]
    
    all_exist = True
    for filepath, desc in files_to_check:
        full_path = os.path.join(base_path, filepath)
        if not check_file_exists(full_path, desc):
            all_exist = False
    
    # Test 2: Check PlayerAvatar modifications
    print("\n2. Checking PlayerAvatar enhancements:")
    avatar_path = os.path.join(base_path, "frontend/src/components/game/shared/PlayerAvatar.jsx")
    
    avatar_imports = [
        "import ConnectionStatusBadge from '../../ConnectionStatusBadge'",
        "import DisconnectOverlay from '../../DisconnectOverlay'",
        "import useDisconnectStatus from '../../../hooks/useDisconnectStatus'"
    ]
    
    check_imports_in_file(avatar_path, avatar_imports, "PlayerAvatar imports")
    
    # Check for new props
    with open(avatar_path, 'r') as f:
        avatar_content = f.read()
        
    new_props = ['isDisconnected', 'connectionStatus', 'showConnectionStatus', 'showDisconnectOverlay']
    print("\n  Checking new props:")
    for prop in new_props:
        if prop in avatar_content:
            print(f"  ✓ Found prop: {prop}")
        else:
            print(f"  ✗ Missing prop: {prop}")
    
    # Test 3: Check ConnectionIndicator enhancements
    print("\n3. Checking ConnectionIndicator enhancements:")
    indicator_path = os.path.join(base_path, "frontend/src/components/ConnectionIndicator.jsx")
    
    with open(indicator_path, 'r') as f:
        indicator_content = f.read()
    
    if "disconnectedPlayers" in indicator_content and "AI Playing" in indicator_content:
        print("✓ ConnectionIndicator has AI playing status")
    else:
        print("✗ ConnectionIndicator missing AI playing status")
    
    # Test 4: Check CSS files content
    print("\n4. Checking CSS files have content:")
    css_files = [
        "frontend/src/styles/connection-badges.css",
        "frontend/src/styles/disconnect-overlay.css",
    ]
    
    for css_file in css_files:
        full_path = os.path.join(base_path, css_file)
        if os.path.exists(full_path):
            with open(full_path, 'r') as f:
                content = f.read().strip()
            if len(content) > 100:  # Should have substantial content
                print(f"✓ {css_file} has content ({len(content)} chars)")
            else:
                print(f"✗ {css_file} seems empty or too small")
    
    # Test 5: Check TypeScript interfaces
    print("\n5. Checking TypeScript interfaces:")
    ts_path = os.path.join(base_path, "frontend/src/types/connection.ts")
    
    if os.path.exists(ts_path):
        with open(ts_path, 'r') as f:
            ts_content = f.read()
        
        interfaces = ['ConnectionStatus', 'PlayerStatus', 'DisconnectEvent', 'ReconnectEvent']
        for interface in interfaces:
            if interface in ts_content:
                print(f"✓ Found interface: {interface}")
            else:
                print(f"✗ Missing interface: {interface}")
    
    # Test 6: Check hook implementation
    print("\n6. Checking useDisconnectStatus hook:")
    hook_path = os.path.join(base_path, "frontend/src/hooks/useDisconnectStatus.js")
    
    if os.path.exists(hook_path):
        with open(hook_path, 'r') as f:
            hook_content = f.read()
        
        hook_features = [
            "useState",
            "useEffect", 
            "NetworkService",
            "player_disconnected",
            "player_reconnected",
            "full_state_sync"
        ]
        
        for feature in hook_features:
            if feature in hook_content:
                print(f"✓ Hook uses: {feature}")
            else:
                print(f"✗ Hook missing: {feature}")
    
    # Run npm commands
    run_npm_commands()
    
    print("\n" + "="*60)
    print("Connection UI Components Test Complete")
    print("="*60)

if __name__ == "__main__":
    test_connection_ui_components()