/**
 * Debug script to check game_started event handling
 */

console.log('🔍 Debugging GameService event handling...');

// Check if GameService is properly set up
if (window.gameService) {
    console.log('✅ GameService found on window');
    
    // Add a listener to see all events
    window.gameService.addEventListener('stateChange', (event) => {
        console.log('🎮 GameService state change:', event.detail.state.phase);
    });
    
    // Check current state
    const state = window.gameService.getState();
    console.log('📊 Current GameService state:', {
        phase: state.phase,
        roomId: state.roomId,
        playerName: state.playerName,
        isConnected: state.isConnected
    });
} else {
    console.log('❌ GameService not found on window');
}

// Check NetworkService
if (window.networkService) {
    console.log('✅ NetworkService found on window');
    
    // Add listener for game_started events specifically
    window.networkService.addEventListener('game_started', (event) => {
        console.log('🚀 RAW game_started event received:', event.detail);
        console.log('🚀 Event data structure:', JSON.stringify(event.detail.data, null, 2));
    });
    
    // Add listener for all events to see what's coming through
    window.networkService.addEventListener('message', (event) => {
        if (event.detail.message.event === 'game_started') {
            console.log('📨 NetworkService message event - game_started:', event.detail);
        }
    });
    
    const status = window.networkService.getStatus();
    console.log('📡 NetworkService status:', status);
} else {
    console.log('❌ NetworkService not found on window');
}

// Make services available globally for debugging
if (typeof window !== 'undefined') {
    // Import and expose services
    import('./frontend/src/services/GameService.js').then(module => {
        window.GameServiceClass = module.default;
        window.gameService = module.gameService;
        console.log('✅ GameService loaded and exposed');
    }).catch(err => {
        console.log('❌ Failed to load GameService:', err);
    });
    
    import('./frontend/src/services/NetworkService.js').then(module => {
        window.NetworkServiceClass = module.default;
        window.networkService = module.networkService;
        console.log('✅ NetworkService loaded and exposed');
    }).catch(err => {
        console.log('❌ Failed to load NetworkService:', err);
    });
}

console.log('🔍 Debug script loaded. Check console for service availability.');