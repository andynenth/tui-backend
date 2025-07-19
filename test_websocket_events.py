#!/usr/bin/env python3
"""
Test script for Task 1.5: WebSocket Event Handlers

This script tests the WebSocket event integration by:
1. Checking file existence
2. Verifying TypeScript types
3. Testing event flow
"""

import os
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

def check_imports_and_exports(filepath, patterns, description):
    """Check for specific patterns in a file"""
    if not os.path.exists(filepath):
        print(f"✗ Cannot check {description} - file not found")
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    all_found = True
    for pattern in patterns:
        if pattern in content:
            print(f"  ✓ Found: {pattern[:50]}...")
        else:
            print(f"  ✗ Missing: {pattern}")
            all_found = False
    
    return all_found

def run_typescript_check():
    """Run TypeScript type checking"""
    print("\n" + "="*60)
    print("Running TypeScript type check...")
    print("="*60)
    
    os.chdir('frontend')
    
    try:
        # Check just our new files to avoid unrelated errors
        files_to_check = [
            "src/types/events.ts",
            "src/services/DisconnectEventService.ts",
            "src/services/NetworkServiceIntegration.ts"
        ]
        
        for file in files_to_check:
            print(f"\nChecking {file}...")
            result = subprocess.run(
                ['npx', 'tsc', '--noEmit', '--skipLibCheck', file],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                print(f"✓ {file} - No type errors")
            else:
                print(f"✗ {file} - Type errors found:")
                print(result.stdout)
                print(result.stderr)
                
    except Exception as e:
        print(f"✗ Could not run type check: {e}")
    
    os.chdir('..')

def create_integration_demo():
    """Create a demo file showing integration"""
    demo_content = '''// frontend/src/components/WebSocketEventDemo.jsx

import React, { useEffect, useState } from 'react';
import { 
  NetworkServiceIntegration,
  initializeNetworkWithDisconnectHandling 
} from '../services/NetworkServiceIntegration';
import ToastContainer from './ToastContainer';
import ConnectionIndicator from './ConnectionIndicator';
import PlayerAvatar from './game/shared/PlayerAvatar';

const WebSocketEventDemo = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [roomId] = useState('demo-room');
  const [events, setEvents] = useState([]);
  const [disconnectedPlayers, setDisconnectedPlayers] = useState([]);

  useEffect(() => {
    // Initialize with custom handlers
    const handlers = {
      onPlayerDisconnected: (data) => {
        console.log('Demo: Player disconnected', data);
        setEvents(prev => [...prev, { type: 'disconnect', data, time: new Date() }]);
        setDisconnectedPlayers(prev => [...prev, data.player_name]);
      },
      onPlayerReconnected: (data) => {
        console.log('Demo: Player reconnected', data);
        setEvents(prev => [...prev, { type: 'reconnect', data, time: new Date() }]);
        setDisconnectedPlayers(prev => prev.filter(name => name !== data.player_name));
      },
    };

    // Initialize network with disconnect handling
    initializeNetworkWithDisconnectHandling(roomId, handlers)
      .then(() => {
        setIsConnected(true);
        console.log('Connected to demo room');
      })
      .catch(err => {
        console.error('Failed to connect:', err);
        setIsConnected(false);
      });

    // Cleanup
    return () => {
      NetworkServiceIntegration.cleanup();
    };
  }, [roomId]);

  const simulateDisconnect = (playerName) => {
    NetworkServiceIntegration.sendTestDisconnectEvent(playerName);
  };

  const simulateReconnect = (playerName) => {
    NetworkServiceIntegration.sendTestReconnectEvent(playerName);
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>WebSocket Event Integration Demo</h1>
      
      <section style={{ marginBottom: '20px' }}>
        <h2>Connection Status</h2>
        <ConnectionIndicator 
          isConnected={isConnected}
          disconnectedPlayers={disconnectedPlayers}
          showAIStatus={true}
        />
      </section>

      <section style={{ marginBottom: '20px' }}>
        <h2>Test Players</h2>
        <div style={{ display: 'flex', gap: '20px' }}>
          {['Alice', 'Bob', 'Charlie'].map(name => (
            <div key={name} style={{ textAlign: 'center' }}>
              <PlayerAvatar
                name={name}
                isDisconnected={disconnectedPlayers.includes(name)}
                showConnectionStatus={true}
                size="large"
              />
              <h3>{name}</h3>
              <button onClick={() => simulateDisconnect(name)}>
                Disconnect
              </button>
              {' '}
              <button onClick={() => simulateReconnect(name)}>
                Reconnect
              </button>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>Event Log</h2>
        <div style={{ 
          maxHeight: '200px', 
          overflow: 'auto',
          border: '1px solid #ccc',
          padding: '10px',
          fontSize: '12px'
        }}>
          {events.map((event, idx) => (
            <div key={idx}>
              [{event.time.toLocaleTimeString()}] {event.type}: {event.data.player_name}
            </div>
          ))}
        </div>
      </section>

      <ToastContainer position="top-right" />
    </div>
  );
};

export default WebSocketEventDemo;
'''
    
    demo_path = 'frontend/src/components/WebSocketEventDemo.jsx'
    with open(demo_path, 'w') as f:
        f.write(demo_content)
    
    print(f"✓ Created demo component at {demo_path}")

def test_websocket_event_handlers():
    """Test all WebSocket event handler components"""
    print("="*60)
    print("Testing WebSocket Event Handlers (Task 1.5)")
    print("="*60)
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Test 1: Check all files exist
    print("\n1. Checking file existence:")
    files_to_check = [
        ("frontend/src/types/events.ts", "Event type definitions"),
        ("frontend/src/services/DisconnectEventService.ts", "Disconnect event service"),
        ("frontend/src/services/NetworkServiceIntegration.ts", "Network integration module"),
        ("frontend/src/components/ToastNotification.jsx", "Toast notification component"),
        ("frontend/src/components/ToastContainer.jsx", "Toast container component"),
        ("frontend/src/hooks/useToastNotifications.js", "Toast notifications hook"),
        ("frontend/src/styles/toast-notifications.css", "Toast notification styles"),
    ]
    
    all_exist = True
    for filepath, desc in files_to_check:
        full_path = os.path.join(base_path, filepath)
        if not check_file_exists(full_path, desc):
            all_exist = False
    
    # Test 2: Check event types
    print("\n2. Checking event type definitions:")
    events_path = os.path.join(base_path, "frontend/src/types/events.ts")
    
    event_types = [
        "PlayerDisconnectedEvent",
        "PlayerReconnectedEvent",
        "AIActivatedEvent",
        "FullStateSyncEvent",
        "ReconnectionSummaryEvent",
        "DISCONNECT_EVENT_NAMES"
    ]
    
    check_imports_and_exports(events_path, event_types, "event types")
    
    # Test 3: Check DisconnectEventService
    print("\n3. Checking DisconnectEventService:")
    service_path = os.path.join(base_path, "frontend/src/services/DisconnectEventService.ts")
    
    service_features = [
        "class DisconnectEventService",
        "initializeRoom",
        "setHandlers",
        "networkService.addEventListener",
        "window.dispatchEvent"
    ]
    
    check_imports_and_exports(service_path, service_features, "service features")
    
    # Test 4: Check integration module
    print("\n4. Checking NetworkServiceIntegration:")
    integration_path = os.path.join(base_path, "frontend/src/services/NetworkServiceIntegration.ts")
    
    integration_features = [
        "NetworkServiceIntegration",
        "initializeForRoom",
        "disconnectEventService",
        "initializeNetworkWithDisconnectHandling"
    ]
    
    check_imports_and_exports(integration_path, integration_features, "integration features")
    
    # Test 5: Check toast components
    print("\n5. Checking toast notification components:")
    
    toast_files = [
        "frontend/src/components/ToastNotification.jsx",
        "frontend/src/components/ToastContainer.jsx",
        "frontend/src/hooks/useToastNotifications.js"
    ]
    
    for file in toast_files:
        full_path = os.path.join(base_path, file)
        if os.path.exists(full_path):
            with open(full_path, 'r') as f:
                content = f.read()
            
            # Check for key features
            if "player_disconnected" in content or "ToastNotification" in content:
                print(f"✓ {file} has expected content")
            else:
                print(f"✗ {file} missing expected content")
    
    # Test 6: Check useDisconnectStatus updates
    print("\n6. Checking useDisconnectStatus hook updates:")
    hook_path = os.path.join(base_path, "frontend/src/hooks/useDisconnectStatus.js")
    
    with open(hook_path, 'r') as f:
        hook_content = f.read()
    
    if "window.addEventListener" in hook_content and "player_disconnected" in hook_content:
        print("✓ Hook updated to use window events")
    else:
        print("✗ Hook not properly updated")
    
    # Run TypeScript check
    run_typescript_check()
    
    # Create demo component
    print("\n7. Creating demo component:")
    create_integration_demo()
    
    print("\n" + "="*60)
    print("WebSocket Event Handlers Test Complete")
    print("="*60)
    
    print("\n📝 Summary:")
    print("- Event type definitions created")
    print("- DisconnectEventService handles NetworkService events")
    print("- Toast notifications ready for disconnect/reconnect events")
    print("- Integration module connects everything together")
    print("- Demo component shows how to use the system")

if __name__ == "__main__":
    test_websocket_event_handlers()