const { chromium } = require('playwright');

async function testBackendLogs() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Enable all console logging
  page.on('console', msg => {
    console.log('📋 Console:', msg.text());
  });
  
  // Also log network activity
  page.on('response', response => {
    if (response.url().includes('/ws') || response.url().includes('websocket')) {
      console.log('🌐 WebSocket Response:', response.url(), response.status());
    }
  });
  
  // Monitor WebSocket frames
  const cdpSession = await page.context().newCDPSession(page);
  await cdpSession.send('Network.enable');
  
  cdpSession.on('Network.webSocketFrameReceived', frame => {
    try {
      const data = JSON.parse(frame.response.payloadData);
      console.log('📥 WS Received:', data.event || data.type || 'unknown', data);
    } catch (e) {
      console.log('📥 WS Received (raw):', frame.response.payloadData);
    }
  });
  
  cdpSession.on('Network.webSocketFrameSent', frame => {
    try {
      const data = JSON.parse(frame.response.payloadData);
      console.log('📤 WS Sent:', data.event || data.type || 'unknown', data);
    } catch (e) {
      console.log('📤 WS Sent (raw):', frame.response.payloadData);
    }
  });
  
  try {
    console.log('🚀 Testing WebSocket communication...\n');
    
    // Navigate and enter name
    await page.goto('http://localhost:5050');
    await page.waitForTimeout(1000);
    
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
    
    // Start game
    console.log('\n🎮 Starting game...\n');
    await page.click('button:has-text("Start Game")');
    
    // Wait longer to capture all events
    await page.waitForTimeout(10000);
    
    console.log('\n🏁 Test completed');
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
  } finally {
    await page.waitForTimeout(3000);
    await browser.close();
  }
}

// Run the test
testBackendLogs();