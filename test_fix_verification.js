const { chromium } = require('playwright');

async function testFixVerification() {
  console.log('🔍 Testing Room Deletion Fix\n');
  
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
    // Enter lobby
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    await page.fill('input[type="text"]', 'TestPlayer');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(2000);
    
    // Create room
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(2000);
    
    // Start game
    const startButton = await page.$('button:has-text("Start")');
    if (startButton) {
      await startButton.click();
      console.log('🎯 Start game button clicked');
      
      // Wait for 10 seconds to see the result
      await page.waitForTimeout(10000);
      
      const pageText = await page.textContent('body');
      
      if (roomNotFoundReceived) {
        console.log('❌ ISSUE STILL EXISTS: Room was deleted after game start');
        console.log('The fix did not work correctly');
      } else if (gameStartedReceived && !pageText.includes('room no longer exists')) {
        console.log('✅ SUCCESS: Game started and room persisted!');
        console.log('The fix appears to be working');
      } else {
        console.log('⚠️ INCONCLUSIVE: Need to investigate further');
        console.log(`Game started: ${gameStartedReceived}`);
        console.log(`Room error: ${roomNotFoundReceived}`);
      }
    } else {
      console.log('❌ Start button not found');
    }
    
    await browser.close();
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
    await browser.close();
  }
}

testFixVerification();