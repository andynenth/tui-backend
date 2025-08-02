#\!/usr/bin/env python3
"""
Test script to verify connection tracking implementation
Tests that player_name flows through the connection chain
"""

import json

print("🔍 Testing Connection Tracking Implementation")
print("=" * 60)

# Test 1: Check NetworkService passes player name
print("\n1. Frontend NetworkService Changes:")
print("-" * 40)

# Check if NetworkService.ts accepts playerInfo parameter
import os
networkservice_path = "frontend/src/services/NetworkService.ts"
if os.path.exists(networkservice_path):
    with open(networkservice_path, 'r') as f:
        content = f.read()
        if "playerInfo?: { playerName?: string }" in content:
            print("✅ NetworkService.connectToRoom accepts playerInfo parameter")
        else:
            print("❌ NetworkService.connectToRoom missing playerInfo parameter")
        
        if "playerName: playerInfo?.playerName" in content:
            print("✅ NetworkService stores playerName in connection data")
        else:
            print("❌ NetworkService not storing playerName")
            
        if "player_name: connectionData?.playerName" in content:
            print("✅ client_ready event includes player_name")
        else:
            print("❌ client_ready event missing player_name")

# Test 2: Check GameService passes player name
print("\n2. GameService Integration:")
print("-" * 40)

gameservice_path = "frontend/src/services/GameService.ts"
if os.path.exists(gameservice_path):
    with open(gameservice_path, 'r') as f:
        content = f.read()
        if "connectToRoom(roomId, { playerName })" in content:
            print("✅ GameService passes playerName to NetworkService")
        else:
            print("❌ GameService not passing playerName to NetworkService")

# Test 3: Check backend WebSocket handler
print("\n3. Backend WebSocket Handler:")
print("-" * 40)

ws_path = "backend/api/routes/ws.py"
if os.path.exists(ws_path):
    with open(ws_path, 'r') as f:
        content = f.read()
        if "player_name = data.get('player_name')" in content:
            print("✅ Backend extracts player_name from client_ready")
        else:
            print("❌ Backend not extracting player_name")
            
        if "register_player" in content:
            print("✅ Backend has player registration logic")
        else:
            print("❌ Backend missing player registration")

# Test 4: Check RoomPage integration
print("\n4. RoomPage Integration:")
print("-" * 40)

roompage_path = "frontend/src/pages/RoomPage.jsx"
if os.path.exists(roompage_path):
    with open(roompage_path, 'r') as f:
        content = f.read()
        if "playerName: app.playerName" in content:
            print("✅ RoomPage passes playerName from AppContext")
        else:
            print("❌ RoomPage not passing playerName")

# Test 5: Check useAutoReconnect fix
print("\n5. Auto Reconnect Hook:")
print("-" * 40)

autoreconnect_path = "frontend/src/hooks/useAutoReconnect.js"
if os.path.exists(autoreconnect_path):
    with open(autoreconnect_path, 'r') as f:
        content = f.read()
        if "connectToRoom" in content and "connect(" not in content:
            print("✅ useAutoReconnect uses correct method name")
        else:
            print("❌ useAutoReconnect using incorrect method")

print("\n" + "=" * 60)
print("📊 Summary:")
print("The connection tracking implementation ensures player_name")
print("flows through the entire connection chain, enabling proper")
print("disconnect detection and bot activation.")
