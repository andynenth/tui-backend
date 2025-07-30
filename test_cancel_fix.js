const { chromium } = require('playwright');

async function testCancelFix() {
  console.log('✅ Testing Cancel Button Fix\n');
  console.log('Expected: Cancel should redirect to lobby without 404 error\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Monitor WebSocket messages
  const wsMessages = [];
  page.on('websocket', ws => {
    console.log('🔌 WebSocket connected');
    
    ws.on('framesent', event => {
      try {
        const data = JSON.parse(event.payload);
        console.log(`📤 WS Send: ${data.type}`);
        wsMessages.push({ direction: 'sent', type: data.type, data });
        
        // Check for leave_room message
        if (data.type === 'leave_room') {
          console.log('  ✅ leave_room message sent!');
          console.log(`  Player: ${data.payload?.player_name}`);
        }
      } catch (e) {}
    });
    
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        console.log(`📥 WS Receive: ${data.type}`);
        wsMessages.push({ direction: 'received', type: data.type, data });
      } catch (e) {}
    });
  });

  // Monitor navigation
  page.on('framenavigated', frame => {
    if (frame === page.mainFrame()) {
      console.log(`🧭 Navigated to: ${frame.url()}`);
    }
  });

  // Monitor 404 errors
  page.on('response', response => {
    if (response.status() === 404) {
      console.log(`❌ 404 Error: ${response.url()}`);
      response.text().then(text => {
        console.log(`   Body: ${text}`);
      });
    }
  });

  try {
    // Navigate to start page
    console.log('📍 Starting test flow');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    // Enter lobby
    await page.fill('input[type="text"]', 'TestPlayer');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(1500);
    console.log('  ✓ Entered lobby');
    
    // Create room
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(2000);
    
    const roomCode = await page.$eval('body', body => {
      const text = body.innerText;
      const match = text.match(/[A-Z]{4}/);
      return match ? match[0] : null;
    });
    console.log(`  ✓ Room created: ${roomCode}`);
    
    // Start game
    await page.click('button:has-text("Start")');
    console.log('  ✓ Clicked Start Game');
    await page.waitForTimeout(3000);
    
    // Check if we're on waiting page
    const pageText = await page.textContent('body');
    
    if (pageText.includes('room no longer exists')) {
      console.log('  ⚠️  Got room error, waiting for redirect...');
      await page.waitForURL('http://localhost:5050/', { timeout: 15000 });
      console.log('  ✓ Redirected to start, trying again...\n');
      
      // Try again
      await page.fill('input[type="text"]', 'TestPlayer2');
      await page.click('button:has-text("Enter Lobby")');
      await page.waitForTimeout(1500);
      await page.click('button:has-text("Create Room")');
      await page.waitForTimeout(2000);
      await page.click('button:has-text("Start")');
      await page.waitForTimeout(3000);
    }
    
    // Clear WebSocket messages to focus on cancel action
    wsMessages.length = 0;
    
    // Now test cancel button
    console.log('\n📍 Testing Cancel Button');
    const cancelButton = await page.$('button:has-text("Cancel")');
    
    if (cancelButton) {
      console.log('  ✓ Found Cancel button');
      
      const beforeUrl = page.url();
      console.log(`  Current URL: ${beforeUrl}`);
      
      // Click cancel
      await cancelButton.click();
      console.log('  ✓ Clicked Cancel button');
      
      // Wait for navigation
      await page.waitForTimeout(2000);
      
      const afterUrl = page.url();
      const afterText = await page.textContent('body');
      
      console.log(`\n📊 Results:`);
      console.log(`  After URL: ${afterUrl}`);
      
      // Check if leave_room was sent
      const leaveRoomSent = wsMessages.some(msg => 
        msg.direction === 'sent' && msg.type === 'leave_room'
      );
      console.log(`  leave_room sent: ${leaveRoomSent ? '✅ Yes' : '❌ No'}`);
      
      // Check if we got 404 error
      const has404Error = afterText.includes('"detail":"Not Found"') || 
                          afterText.includes('{"detail":"Not Found"}');
      console.log(`  404 error: ${has404Error ? '❌ Yes (BUG)' : '✅ No'}`);
      
      // Check if we're in lobby
      const inLobby = afterUrl.includes('/lobby') || 
                      afterText.includes('Create Room') || 
                      afterText.includes('Join Room');
      console.log(`  In lobby: ${inLobby ? '✅ Yes' : '❌ No'}`);
      
      if (!has404Error && inLobby && leaveRoomSent) {
        console.log('\n✅ FIX CONFIRMED: Cancel button works correctly!');
        console.log('  - Sent leave_room WebSocket message');
        console.log('  - No 404 error');
        console.log('  - Successfully redirected to lobby');
      } else {
        console.log('\n❌ Issue still present:');
        if (!leaveRoomSent) console.log('  - leave_room message not sent');
        if (has404Error) console.log('  - Still getting 404 error');
        if (!inLobby) console.log('  - Not redirected to lobby');
      }
      
    } else {
      console.log('  ❌ Cancel button not found');
    }
    
    console.log('\n✅ Test complete. Browser remains open.');
    
    await new Promise(() => {});
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
  }
}

testCancelFix().catch(console.error);