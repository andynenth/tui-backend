const { chromium } = require('playwright');

async function testPhaseChangeAndPieces() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Track all events
  const websocketEvents = [];
  const phaseChangeEvents = [];
  let gameStartedReceived = false;
  let phaseChangeReceived = false;
  
  // Enable comprehensive console logging
  page.on('console', msg => {
    const text = msg.text();
    console.log('📋 Console:', text);
  });
  
  // Monitor WebSocket frames
  const cdpSession = await page.context().newCDPSession(page);
  await cdpSession.send('Network.enable');
  
  cdpSession.on('Network.webSocketFrameReceived', frame => {
    try {
      const data = JSON.parse(frame.response.payloadData);
      websocketEvents.push({
        timestamp: new Date().toISOString(),
        event: data.event || data.type || 'unknown',
        data: data
      });
      
      console.log('📥 WS Received:', data.event || data.type || 'unknown', {
        event: data.event,
        hasData: !!data.data,
        dataKeys: data.data ? Object.keys(data.data) : []
      });
      
      // Track specific events
      if (data.event === 'game_started') {
        gameStartedReceived = true;
        console.log('🎮 GAME_STARTED event received:', {
          round_number: data.data?.round_number,
          players: data.data?.players
        });
      }
      
      if (data.event === 'phase_change') {
        phaseChangeReceived = true;
        phaseChangeEvents.push(data);
        console.log('🔄 PHASE_CHANGE event received:', {
          phase: data.data?.phase,
          hasPlayers: !!data.data?.players,
          playerCount: data.data?.players ? Object.keys(data.data.players).length : 0,
          hasPhaseData: !!data.data?.phase_data
        });
        
        // Log the phase_data in detail
        if (data.data?.phase_data) {
          console.log('📊 phase_data structure:', {
            hasPlayers: !!data.data.phase_data.players,
            playerNames: data.data.phase_data.players ? Object.keys(data.data.phase_data.players) : []
          });
          
          if (data.data.phase_data.players) {
            console.log('🎴 Player hands from phase_data:');
            Object.entries(data.data.phase_data.players).forEach(([playerName, playerData]) => {
              const hand = playerData?.hand;
              console.log(`   ${playerName}: ${hand ? `${hand.length} pieces` : 'NO HAND'} - ${JSON.stringify(hand || []).substring(0, 100)}...`);
            });
          }
        }
        
        // Check if hand data exists
        if (data.data?.players) {
          console.log('👥 Players data in phase_change:');
          Object.entries(data.data.players).forEach(([playerName, playerData]) => {
            console.log(`   ${playerName}:`, {
              hasHand: !!playerData.hand,
              handLength: playerData.hand?.length || 0,
              handSample: playerData.hand?.slice(0, 2)
            });
          });
        }
      }
    } catch (e) {
      console.log('📥 WS Received (raw):', frame.response.payloadData);
    }
  });
  
  cdpSession.on('Network.webSocketFrameSent', frame => {
    try {
      const data = JSON.parse(frame.response.payloadData);
      console.log('📤 WS Sent:', data.event || data.type || 'unknown', {
        event: data.event,
        data: data.data
      });
    } catch (e) {
      console.log('📤 WS Sent (raw):', frame.response.payloadData);
    }
  });
  
  try {
    console.log('🚀 Testing phase_change events and piece display...\n');
    console.log('📍 Test objectives:');
    console.log('   1. Verify backend sends phase_change events');
    console.log('   2. Check if phase_change contains hand data');
    console.log('   3. Monitor how frontend processes the event');
    console.log('   4. Verify pieces are rendered in UI\n');
    
    // Navigate and enter name
    await page.goto('http://localhost:5050');
    await page.waitForTimeout(1000);
    
    // Check initial game service state
    const initialState = await page.evaluate(() => {
      return {
        hasGameService: !!window.gameService,
        hasNetworkService: !!window.networkService,
        gameServiceType: typeof window.gameService
      };
    });
    console.log('🔍 Initial page state:', initialState);
    
    // Enter name
    const nameInput = await page.waitForSelector('input[type="text"]');
    await nameInput.fill('TestPlayer');
    console.log('✅ Entered player name');
    
    // Enter lobby
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(1000);
    console.log('✅ Entered lobby');
    
    // Create room
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(1000);
    console.log('✅ Created room');
    
    // Check game service before starting
    const preGameState = await page.evaluate(() => {
      const gs = window.gameService;
      if (gs && gs.getState) {
        const state = gs.getState();
        return {
          phase: state.phase,
          myHandLength: state.myHand?.length || 0,
          playerName: state.playerName,
          roomId: state.roomId
        };
      }
      return { error: 'gameService not available' };
    });
    console.log('🎮 Pre-game state:', preGameState);
    
    // Start game
    console.log('\n🎮 Starting game...\n');
    await page.click('button:has-text("Start Game")');
    
    // Wait for navigation to game page
    try {
      await page.waitForURL('**/game/**', { timeout: 5000 });
      console.log('✅ Navigated to game page');
    } catch (e) {
      console.log('⚠️ Navigation timeout - checking current URL:', page.url());
    }
    
    // Wait a bit for events to process
    await page.waitForTimeout(3000);
    
    // Check game service state after navigation
    const postNavState = await page.evaluate(() => {
      const gs = window.gameService;
      if (gs && gs.getState) {
        const state = gs.getState();
        return {
          phase: state.phase,
          myHandLength: state.myHand?.length || 0,
          myHand: state.myHand,
          playerName: state.playerName,
          roomId: state.roomId,
          players: state.players
        };
      }
      return { error: 'gameService not available after navigation' };
    });
    console.log('🎮 Post-navigation state:', JSON.stringify(postNavState, null, 2));
    
    // Wait for preparation phase UI
    console.log('\n⏳ Waiting for preparation phase UI...');
    let preparationFound = false;
    try {
      await page.waitForSelector('.preparation-content', { timeout: 5000 });
      preparationFound = true;
      console.log('✅ Preparation phase UI detected');
    } catch (e) {
      console.log('❌ Preparation phase UI not found within 5 seconds');
    }
    
    // Additional wait for any animations
    await page.waitForTimeout(2000);
    
    // Comprehensive UI check
    console.log('\n🔍 Checking UI elements...');
    const uiElements = await page.evaluate(() => {
      return {
        hasPreparationContent: !!document.querySelector('.preparation-content'),
        hasPieceTray: !!document.querySelector('.piece-tray'),
        hasPieceTrayGrid: !!document.querySelector('.piece-tray__grid'),
        hasGameLayout: !!document.querySelector('.game-layout'),
        gameLayoutPhase: document.querySelector('.game-layout')?.getAttribute('data-phase'),
        hasWaitingUI: !!document.querySelector('.waiting-container'),
        pieceTrayHTML: document.querySelector('.piece-tray')?.innerHTML?.substring(0, 200)
      };
    });
    console.log('📄 UI Elements:', JSON.stringify(uiElements, null, 2));
    
    // Count pieces
    const piecesByClass = await page.locator('.game-piece').count();
    const piecesInTray = await page.locator('.piece-tray .game-piece').count();
    const pieceCharacters = await page.locator('.game-piece__character').count();
    
    console.log('\n📊 Pieces found in UI:');
    console.log(`   By .game-piece class: ${piecesByClass}`);
    console.log(`   In .piece-tray: ${piecesInTray}`);
    console.log(`   By .game-piece__character: ${pieceCharacters}`);
    
    // Final game state check
    const finalState = await page.evaluate(() => {
      const gs = window.gameService;
      if (gs && gs.getState) {
        const state = gs.getState();
        return {
          phase: state.phase,
          myHandLength: state.myHand?.length || 0,
          myHand: state.myHand,
          playerName: state.playerName,
          hasHandData: !!state.myHand && state.myHand.length > 0
        };
      }
      return { error: 'gameService not available' };
    });
    console.log('\n🎮 Final game state:', JSON.stringify(finalState, null, 2));
    
    // Summary of findings
    console.log('\n📊 SUMMARY OF FINDINGS:');
    console.log('===========================');
    console.log(`1. WebSocket events received: ${websocketEvents.length}`);
    console.log(`2. game_started event: ${gameStartedReceived ? '✅ Received' : '❌ NOT received'}`);
    console.log(`3. phase_change event: ${phaseChangeReceived ? '✅ Received' : '❌ NOT received'}`);
    console.log(`4. phase_change events count: ${phaseChangeEvents.length}`);
    
    if (phaseChangeEvents.length > 0) {
      console.log('\n📍 Phase change event details:');
      phaseChangeEvents.forEach((event, i) => {
        console.log(`   Event ${i + 1}:`, {
          phase: event.data?.phase,
          hasPlayers: !!event.data?.players,
          hasPhaseData: !!event.data?.phase_data
        });
      });
    }
    
    console.log(`\n5. Preparation UI found: ${preparationFound ? '✅ Yes' : '❌ No'}`);
    console.log(`6. Pieces in UI: ${piecesByClass > 0 ? `✅ ${piecesByClass} pieces` : '❌ No pieces'}`);
    console.log(`7. Game state has hand: ${finalState.hasHandData ? '✅ Yes' : '❌ No'}`);
    
    // Diagnosis
    console.log('\n🔍 DIAGNOSIS:');
    if (!gameStartedReceived) {
      console.log('❌ Backend is not sending game_started events');
    }
    if (!phaseChangeReceived) {
      console.log('❌ Backend is not sending phase_change events');
      console.log('   This is why pieces are not displaying!');
    } else if (phaseChangeEvents.length > 0) {
      const hasHandData = phaseChangeEvents.some(e => 
        e.data?.players && Object.values(e.data.players).some(p => p.hand?.length > 0)
      );
      if (!hasHandData) {
        console.log('❌ phase_change events are sent but do NOT contain hand data');
      } else {
        console.log('✅ phase_change events contain hand data');
        if (piecesByClass === 0) {
          console.log('❌ Frontend receives hand data but fails to render pieces');
        }
      }
    }
    
    // Take screenshot
    await page.screenshot({ path: 'phase-change-test.png', fullPage: true });
    console.log('\n📸 Screenshot saved as phase-change-test.png');
    
    // Log all WebSocket events for analysis
    console.log('\n📜 All WebSocket events timeline:');
    websocketEvents.forEach(event => {
      console.log(`   ${event.timestamp}: ${event.event}`);
    });
    
  } catch (error) {
    console.error('❌ Test error:', error);
    console.error('Stack:', error.stack);
  } finally {
    await page.waitForTimeout(3000);
    await browser.close();
    console.log('\n🏁 Test completed');
  }
}

// Run the test
testPhaseChangeAndPieces();