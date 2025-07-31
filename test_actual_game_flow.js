const { chromium } = require('playwright');

async function testActualGameFlow() {
  console.log('🔍 Testing Complete Game Flow - UI State Verification\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: false
  });

  const page = await browser.newPage();
  
  let gameStartedReceived = false;
  let roomNotFoundReceived = false;
  
  // Monitor WebSocket events
  page.on('websocket', ws => {
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        const eventType = data.event || data.type || 'unknown';
        
        if (eventType === 'game_started') {
          gameStartedReceived = true;
          console.log('✅ game_started event received');
        }
        
        if (eventType === 'room_not_found') {
          roomNotFoundReceived = true;
          console.log('❌ room_not_found event received');
        }
      } catch (e) {}
    });
  });

  try {
    console.log('📍 Step 1: Enter lobby');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    await page.fill('input[type="text"]', 'FlowTestPlayer');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(2000);
    console.log('  ✓ Entered lobby');
    
    console.log('\n📍 Step 2: Create room');
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(3000);
    
    const roomCode = await page.$eval('body', body => {
      const text = body.innerText;
      const match = text.match(/([A-Z]{4})/);
      return match ? match[1] : null;
    });
    console.log(`  ✓ Room created: ${roomCode}`);
    
    console.log('\n📍 Step 3: Start game');
    const startButton = await page.$('button:has-text("Start")');
    if (startButton) {
      await startButton.click();
      console.log('  ✓ Clicked Start Game button');
      
      // Wait for initial response
      await page.waitForTimeout(3000);
      
      console.log('\n📍 Step 4: Monitor game state progression');
      
      let finalState = 'unknown';
      let progressDetected = false;
      
      // Monitor for 15 seconds to see the actual progression
      for (let i = 0; i < 15; i++) {
        const pageText = await page.textContent('body');
        const currentUrl = page.url();
        
        console.log(`  ${i + 1}s: URL=${new URL(currentUrl).pathname}`);
        
        if (pageText.includes('room no longer exists')) {
          console.log(`  ${i + 1}s: ❌ Room error appeared`);
          finalState = 'room_error';
          break;
        } else if (pageText.includes('Waiting for game to start')) {
          console.log(`  ${i + 1}s: ⏳ Still on "Waiting for game to start..." page`);
          finalState = 'waiting_stuck';
        } else if (pageText.includes('Declaration') || pageText.includes('Choose') || pageText.includes('declare')) {
          console.log(`  ${i + 1}s: ✅ Game progressed to Declaration phase!`);
          finalState = 'success';
          progressDetected = true;
          break;
        } else if (pageText.includes('Turn') || pageText.includes('play') || pageText.includes('pieces')) {
          console.log(`  ${i + 1}s: ✅ Game progressed to gameplay!`);
          finalState = 'success';
          progressDetected = true;
          break;
        } else if (currentUrl.includes('/game/')) {
          console.log(`  ${i + 1}s: 🔄 On game page, checking content...`);
          // Take a screenshot for debugging
          if (i === 10) {
            await page.screenshot({ path: `game-state-debug-${Date.now()}.png` });
            console.log(`    📸 Screenshot saved for debugging`);
          }
        } else {
          console.log(`  ${i + 1}s: 🤔 Unknown state`);
          console.log(`    Content preview: ${pageText.substring(0, 100)}...`);
        }
        
        await page.waitForTimeout(1000);
      }
      
      console.log('\n📊 FINAL TEST RESULTS:');
      console.log(`Final State: ${finalState}`);
      console.log(`WebSocket game_started received: ${gameStartedReceived}`);
      console.log(`WebSocket room_not_found received: ${roomNotFoundReceived}`);
      
      if (finalState === 'success') {
        console.log('🎉 SUCCESS: Game flow works completely!');
        console.log('✅ Game progressed beyond waiting page to actual gameplay');
      } else if (finalState === 'waiting_stuck') {
        console.log('❌ ISSUE CONFIRMED: Game stuck on "Waiting for game to start..."');
        console.log('🔍 This means the frontend is not receiving the proper game state');
        console.log('📝 Next steps: Check WebSocket game state events and frontend handling');
      } else if (finalState === 'room_error') {
        console.log('❌ ISSUE: Room was deleted after game start');
        console.log('🔍 The room status fix may not be working properly');
      } else {
        console.log('⚠️ INCONCLUSIVE: Unknown final state');
      }
      
    } else {
      console.log('❌ Start Game button not found');
    }
    
    console.log('\n✅ Test complete. Leaving browser open for inspection...');
    // Keep browser open for 30 seconds for manual inspection
    await page.waitForTimeout(30000);
    await browser.close();
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
    await browser.close();
  }
}

testActualGameFlow();