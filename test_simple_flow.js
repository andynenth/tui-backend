const { chromium } = require('playwright');

async function testSimpleFlow() {
  console.log('🔍 Simple Game Flow Test\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: false
  });

  const page = await browser.newPage();
  
  let gameStartedReceived = false;
  
  // Monitor WebSocket events
  page.on('websocket', ws => {
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        const eventType = data.event || data.type || 'unknown';
        
        if (eventType === 'game_started') {
          gameStartedReceived = true;
          console.log('✅ game_started event received:', JSON.stringify(data, null, 2));
        }
      } catch (e) {}
    });
  });

  try {
    console.log('📍 Step 1: Enter lobby');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    await page.fill('input[type="text"]', 'TestPlayer');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(3000);
    console.log('  ✓ Entered lobby');
    
    console.log('\n📍 Step 2: Create room');
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(5000);
    
    // Check if we're in a room now
    const currentUrl = page.url();
    console.log(`  Current URL: ${currentUrl}`);
    
    const pageText = await page.textContent('body');
    console.log(`  Page contains "Start": ${pageText.includes('Start')}`);
    console.log(`  Page contains "HOST": ${pageText.includes('HOST')}`);
    
    const startButton = await page.$('button:has-text("Start")');
    if (startButton) {
      console.log('\n📍 Step 3: Start game');
      await startButton.click();
      console.log('  ✓ Clicked Start Game button');
      
      // Wait for response
      await page.waitForTimeout(5000);
      
      // Check if we navigated to game page
      const finalUrl = page.url();
      console.log(`  Final URL: ${finalUrl}`);
      
      if (finalUrl.includes('/game/')) {
        console.log('✅ Successfully navigated to game page');
        
        // Check page content 
        const gamePageText = await page.textContent('body');
        if (gamePageText.includes('Waiting for game to start')) {
          console.log('⏳ On "Waiting for game to start..." page');
        } else if (gamePageText.includes('Declaration') || gamePageText.includes('Choose')) {
          console.log('🎉 SUCCESS: Game progressed to gameplay!');
        } else {
          console.log('🤔 Unknown game state');
          console.log(`  Content preview: ${gamePageText.substring(0, 200)}...`);
        }
      } else {
        console.log('❌ Did not navigate to game page');
      }
      
    } else {
      console.log('❌ Start Game button not found');
      console.log('  Page content preview:', pageText.substring(0, 300));
    }
    
    console.log(`\n📊 WebSocket game_started events received: ${gameStartedReceived ? 'Yes' : 'No'}`);
    
    // Keep browser open briefly for inspection
    console.log('\n✅ Test complete. Keeping browser open for 10 seconds...');
    await page.waitForTimeout(10000);
    await browser.close();
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
    await browser.close();
  }
}

testSimpleFlow();