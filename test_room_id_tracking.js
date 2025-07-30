const { chromium } = require('playwright');

async function testRoomIdTracking() {
  console.log('🔍 Testing Room ID Tracking During Error\n');
  console.log('Goal: Identify which room ID causes "room no longer exists" error');
  console.log('- Track room creation');
  console.log('- Track navigation URLs');
  console.log('- Compare room IDs when error occurs\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Track all room-related data
  let roomCreationData = [];
  let navigationUrls = [];
  let wsEvents = [];
  
  // Monitor WebSocket events with room tracking
  page.on('websocket', ws => {
    console.log('🔌 WebSocket connected');
    
    ws.on('framesent', event => {
      try {
        const data = JSON.parse(event.payload);
        const eventType = data.event || data.type || 'unknown';
        console.log(`📤 WS Send: ${eventType}`);
        wsEvents.push({ 
          direction: 'sent', 
          event: eventType, 
          data: data,
          timestamp: Date.now()
        });
        
        if (eventType === 'start_game') {
          console.log(`🎯 START_GAME sent with data:`, data);
        }
      } catch (e) {}
    });
    
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        const eventType = data.event || data.type || 'unknown';
        console.log(`📥 WS Receive: ${eventType}`);
        wsEvents.push({ 
          direction: 'received', 
          event: eventType, 
          data: data,
          timestamp: Date.now()
        });
        
        if (eventType === 'game_started') {
          console.log(`🎯 GAME_STARTED received with data:`, data);
        }
        
        if (eventType === 'room_not_found') {
          console.log(`❌ ROOM_NOT_FOUND received with data:`, data);
        }
      } catch (e) {}
    });
  });

  // Monitor all navigation
  page.on('framenavigated', frame => {
    if (frame === page.mainFrame()) {
      const url = frame.url();
      const path = new URL(url).pathname;
      navigationUrls.push({ url, path, timestamp: Date.now() });
      console.log(`🧭 Navigation: ${path}`);
      
      // Extract room ID from URL if present
      const roomMatch = path.match(/\/game\/([A-Z0-9-]+)/);
      if (roomMatch) {
        const roomIdFromUrl = roomMatch[1];
        console.log(`🏠 Room ID from URL: ${roomIdFromUrl}`);
      }
    }
  });

  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`❌ Console Error: ${msg.text()}`);
    }
  });

  try {
    // Step 1: Enter Lobby
    console.log('📍 Step 1: Enter Lobby');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    await page.fill('input[type="text"]', 'RoomTracker');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(2000);
    console.log('  ✓ Entered lobby');
    
    // Step 2: Create Room and capture all room data
    console.log('\n📍 Step 2: Create Room');
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(3000);
    
    // Extract room information from page
    const pageText = await page.textContent('body');
    const roomCodeMatch = pageText.match(/([A-Z]{4})/);
    const roomCode = roomCodeMatch ? roomCodeMatch[1] : null;
    
    // Try to find room ID from current URL or page content
    const currentUrl = page.url();
    const roomIdMatch = currentUrl.match(/\/room\/([A-Z0-9-]+)/);
    const roomIdFromUrl = roomIdMatch ? roomIdMatch[1] : null;
    
    // Also check for any room ID patterns in page text
    const roomIdTextMatch = pageText.match(/room[_-]?id[:\s]*([A-Z0-9-]+)/i);
    const roomIdFromText = roomIdTextMatch ? roomIdTextMatch[1] : null;
    
    const roomData = {
      roomCode,
      roomIdFromUrl,
      roomIdFromText,
      currentUrl,
      timestamp: Date.now()
    };
    
    roomCreationData.push(roomData);
    
    console.log('  ✓ Room created with data:');
    console.log(`    Room Code: ${roomCode}`);
    console.log(`    Room ID from URL: ${roomIdFromUrl}`);
    console.log(`    Room ID from text: ${roomIdFromText}`);
    console.log(`    Current URL: ${currentUrl}`);
    
    // Step 3: Start Game and track everything
    console.log('\n📍 Step 3: Start Game (with detailed tracking)');
    const startButton = await page.$('button:has-text("Start")');
    
    if (startButton) {
      // Clear previous events to focus on start game sequence
      const startGameTimestamp = Date.now();
      
      await startButton.click();
      console.log('  ✓ Clicked Start Game button');
      
      // Wait and monitor what happens
      await page.waitForTimeout(8000);
      
      // Analyze what happened
      const finalUrl = page.url();
      const finalPath = new URL(finalUrl).pathname;
      const finalPageText = await page.textContent('body');
      
      console.log('\n📊 DETAILED ANALYSIS:');
      console.log(`Final URL: ${finalPath}`);
      
      // Extract room ID from final URL
      const finalRoomMatch = finalPath.match(/\/game\/([A-Z0-9-]+)/);
      const finalRoomId = finalRoomMatch ? finalRoomMatch[1] : null;
      
      console.log(`Room ID from final URL: ${finalRoomId}`);
      
      // Compare room IDs
      if (roomCode && finalRoomId) {
        console.log('\n🔍 ROOM ID COMPARISON:');
        console.log(`  Created Room Code: ${roomCode}`);
        console.log(`  Final URL Room ID: ${finalRoomId}`);
        console.log(`  Match: ${roomCode === finalRoomId ? '✅ SAME' : '❌ DIFFERENT'}`);
        
        if (roomCode !== finalRoomId) {
          console.log('  ⚠️ MISMATCH DETECTED! System is trying to connect to different room!');
        }
      }
      
      // Check for error message
      if (finalPageText.includes('room no longer exists')) {
        console.log('\n❌ ERROR OCCURRED: "room no longer exists"');
        
        // Analyze which room the error is about
        const errorRoomMatch = finalPageText.match(/room[_\s]?id[:\s]*([A-Z0-9-]+)/i);
        const errorRoomId = errorRoomMatch ? errorRoomMatch[1] : null;
        
        console.log(`Error is about room: ${errorRoomId || 'Not specified'}`);
        
        // Get WebSocket events from start_game onwards
        const relevantEvents = wsEvents.filter(e => e.timestamp >= startGameTimestamp);
        
        console.log('\n📊 WebSocket Events During Start Game:');
        relevantEvents.forEach(event => {
          console.log(`  ${event.direction === 'sent' ? '📤' : '📥'} ${event.event}`);
          if (event.data && (event.data.room_id || event.data.roomId)) {
            console.log(`    Room ID in event: ${event.data.room_id || event.data.roomId}`);
          }
        });
        
        // Check if game_started was received
        const gameStartedEvents = relevantEvents.filter(e => e.event === 'game_started');
        if (gameStartedEvents.length > 0) {
          console.log(`\n✅ game_started events received: ${gameStartedEvents.length}`);
          gameStartedEvents.forEach((event, i) => {
            console.log(`  Event ${i + 1}:`, event.data);
          });
        } else {
          console.log('\n❌ No game_started events received');
        }
        
        // Final conclusion
        console.log('\n🎯 CONCLUSION:');
        if (roomCode && finalRoomId && roomCode === finalRoomId) {
          console.log('  The system IS trying to connect to the SAME room that was just created');
          console.log('  Issue: Room was deleted/lost between creation and game start');
        } else if (roomCode && finalRoomId && roomCode !== finalRoomId) {
          console.log('  The system is trying to connect to a DIFFERENT room!');
          console.log('  Issue: Room ID mismatch during navigation');
        } else {
          console.log('  Cannot determine room ID relationship');
          console.log('  Need more investigation into room tracking');
        }
        
      } else {
        console.log('\n✅ No error occurred - game worked correctly');
      }
      
    } else {
      console.log('  ❌ Start Game button not found');
    }
    
    console.log('\n✅ Test complete. Browser remains open for inspection.');
    await new Promise(() => {});
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
  }
}

testRoomIdTracking().catch(console.error);