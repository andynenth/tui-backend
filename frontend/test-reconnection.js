/**
 * Test script to reproduce disconnection/reconnection scenarios
 * Run this in the browser console while a game is active
 */

const testReconnection = {
  // Store original WebSocket
  originalWebSocket: null,
  
  // Get NetworkService instance
  getNetworkService() {
    // Access the singleton instance through window (for debugging)
    return window.__networkService || 
           require('./src/services/NetworkService').networkService;
  },
  
  // Get current WebSocket connection
  getCurrentWebSocket() {
    const networkService = this.getNetworkService();
    const connections = networkService.connections;
    if (connections && connections.size > 0) {
      const firstConnection = connections.values().next().value;
      return firstConnection?.websocket;
    }
    return null;
  },
  
  // Force disconnect
  async forceDisconnect() {
    console.log('🔴 Forcing disconnection...');
    const ws = this.getCurrentWebSocket();
    if (ws) {
      // Close with abnormal closure code (not 1000)
      ws.close(1006, 'Test disconnection');
      console.log('✅ WebSocket closed');
    } else {
      console.error('❌ No active WebSocket found');
    }
  },
  
  // Test quick disconnect/reconnect
  async testQuickReconnect(delayMs = 1000) {
    console.log(`🧪 Testing quick reconnection (${delayMs}ms delay)...`);
    
    // Log initial state
    const gameState = window.__gameService?.getState() || {};
    console.log('📊 Initial state:', {
      round: gameState.currentRound,
      phase: gameState.phase,
      connected: gameState.isConnected
    });
    
    // Force disconnect
    await this.forceDisconnect();
    
    // Wait specified time
    await new Promise(resolve => setTimeout(resolve, delayMs));
    
    // Connection should auto-reconnect
    console.log('⏳ Waiting for auto-reconnection...');
    
    // Monitor state changes
    setTimeout(() => {
      const newState = window.__gameService?.getState() || {};
      console.log('📊 State after reconnection:', {
        round: newState.currentRound,
        phase: newState.phase,
        connected: newState.isConnected
      });
      
      // Check for issues
      if (newState.currentRound !== gameState.currentRound) {
        console.warn('⚠️ Round number changed after reconnection!');
      }
      if (newState.phase !== gameState.phase) {
        console.warn('⚠️ Phase changed after reconnection!');
      }
    }, delayMs + 3000); // Give time for reconnection
  },
  
  // Test medium disconnect
  async testMediumDisconnect() {
    return this.testQuickReconnect(5000);
  },
  
  // Test long disconnect
  async testLongDisconnect() {
    return this.testQuickReconnect(15000);
  },
  
  // Test multiple rapid disconnects
  async testRapidDisconnects(count = 3) {
    console.log(`🧪 Testing ${count} rapid disconnections...`);
    
    for (let i = 0; i < count; i++) {
      console.log(`\n📍 Disconnection ${i + 1}/${count}`);
      await this.forceDisconnect();
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    // Check final state
    setTimeout(() => {
      const state = window.__gameService?.getState() || {};
      console.log('📊 Final state after rapid disconnects:', {
        round: state.currentRound,
        phase: state.phase,
        connected: state.isConnected
      });
    }, 5000);
  },
  
  // Log all WebSocket messages
  monitorMessages() {
    console.log('👁️ Starting WebSocket message monitoring...');
    
    const networkService = this.getNetworkService();
    
    // Listen for phase_change events
    networkService.addEventListener('phase_change', (event) => {
      console.log('📨 phase_change event:', event.detail);
    });
    
    // Listen for all messages
    networkService.addEventListener('message', (event) => {
      const msg = event.detail.message;
      if (msg.event === 'phase_change' || msg.event === 'reconnected') {
        console.log(`📨 ${msg.event}:`, msg);
      }
    });
    
    console.log('✅ Monitoring started. Messages will be logged to console.');
  }
};

// Make it available globally for testing
window.testReconnection = testReconnection;

// Instructions
console.log(`
🧪 Reconnection Test Script Loaded!

Available commands:
- testReconnection.monitorMessages() - Start monitoring WebSocket messages
- testReconnection.forceDisconnect() - Force immediate disconnection
- testReconnection.testQuickReconnect() - Test 1 second disconnect
- testReconnection.testMediumDisconnect() - Test 5 second disconnect
- testReconnection.testLongDisconnect() - Test 15 second disconnect
- testReconnection.testRapidDisconnects() - Test multiple rapid disconnects

Make sure to start monitoring before testing!
`);

// Auto-start monitoring
testReconnection.monitorMessages();