const { chromium } = require('playwright');

async function testRoomCreation() {
  console.log('🔍 Testing Basic Room Creation\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Monitor all WebSocket events
  page.on('websocket', ws => {
    console.log('🔌 WebSocket connection established');
    
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        console.log('📨 WebSocket received:', JSON.stringify(data, null, 2));
      } catch (e) {
        console.log('📨 WebSocket received (non-JSON):', event.payload);
      }
    });
    
    ws.on('framesent', event => {
      try {
        const data = JSON.parse(event.payload);
        console.log('📤 WebSocket sent:', JSON.stringify(data, null, 2));
      } catch (e) {
        console.log('📤 WebSocket sent (non-JSON):', event.payload);
      }
    });
  });

  // Monitor console logs
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    if (type === 'error') {
      console.log('❌ Console Error:', text);
    } else if (text.includes('ERROR') || text.includes('error')) {
      console.log('⚠️ Console:', text);
    }
  });

  try {
    console.log('📍 Step 1: Navigate to application');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    console.log('  ✓ Page loaded');
    
    console.log('\n📍 Step 2: Enter player name');
    await page.fill('input[type="text"]', 'TestPlayer');
    console.log('  ✓ Filled player name: TestPlayer');
    
    console.log('\n📍 Step 3: Click Enter Lobby');
    await page.click('button:has-text("Enter Lobby")');
    console.log('  ✓ Clicked Enter Lobby button');
    
    // Wait and check URL
    await page.waitForTimeout(3000);
    
    let currentUrl = page.url();
    console.log(`  Current URL: ${currentUrl}`);
    
    let pageText = await page.textContent('body');
    console.log(`  Page contains "Lobby": ${pageText.includes('Lobby')}`);
    console.log(`  Page contains "Create Room": ${pageText.includes('Create Room')}`);
    
    if (currentUrl.includes('/lobby') && pageText.includes('Create Room')) {
      console.log('  ✅ Successfully entered lobby');
      
      console.log('\n📍 Step 4: Click Create Room');
      await page.click('button:has-text("Create Room")');
      console.log('  ✓ Clicked Create Room button');
      
      // Wait longer for room creation
      console.log('  ⏳ Waiting 8 seconds for room creation...');
      await page.waitForTimeout(8000);
      
      currentUrl = page.url();
      pageText = await page.textContent('body');
      
      console.log(`  Final URL: ${currentUrl}`);
      console.log(`  URL includes /room/: ${currentUrl.includes('/room/')}`);
      console.log(`  Page contains "Start": ${pageText.includes('Start')}`);
      console.log(`  Page contains "HOST": ${pageText.includes('HOST')}`);
      
      if (currentUrl.includes('/room/')) {
        console.log('  ✅ Successfully created room and navigated to room page');
        
        // Extract room code
        const roomCode = currentUrl.split('/room/')[1];
        console.log(`  🎯 Room Code: ${roomCode}`);
        
        if (pageText.includes('Start')) {
          console.log('  ✅ Start button is available');
        } else {
          console.log('  ❌ Start button not found');
          console.log('  📝 Page content preview:', pageText.substring(0, 300));
        }
      } else {
        console.log('  ❌ Room creation failed - did not navigate to room page');
        console.log('  📝 Current page content:', pageText.substring(0, 500));
      }
      
    } else {
      console.log('  ❌ Failed to enter lobby');
      console.log('  📝 Current page content:', pageText.substring(0, 300));
    }
    
    console.log('\n✅ Test complete. Keeping browser open for 30 seconds for inspection...');
    await page.waitForTimeout(30000);
    await browser.close();
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
    console.error('Stack:', error.stack);
    await browser.close();
  }
}

testRoomCreation();