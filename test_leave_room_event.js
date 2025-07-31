const { chromium } = require('playwright');

async function testLeaveRoomEvent() {
  console.log('🔍 Testing Leave Room WebSocket Event\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Monitor ALL WebSocket messages
  page.on('websocket', ws => {
    ws.on('framesent', event => {
      try {
        const data = JSON.parse(event.payload);
        console.log(`📤 SENT: ${data.event}`, data.data);
      } catch (e) {}
    });
    
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        console.log(`📥 RECEIVED: ${data.event}`, data.data);
      } catch (e) {}
    });
  });

  try {
    console.log('Setting up test...');
    await page.goto('http://localhost:5050');
    await page.fill('input[type="text"]', 'TestPlayer');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(1000);
    
    console.log('\n🏠 Creating room...');
    await page.click('button:has-text("Create Room")');
    await page.waitForSelector('button:has-text("Leave Room")', { timeout: 5000 });
    
    console.log('\n🚪 Clicking Leave Room button...');
    console.log('📋 Monitoring WebSocket messages for leave_room event:');
    
    await page.click('button:has-text("Leave Room")');
    await page.waitForURL('**/lobby', { timeout: 5000 });
    
    console.log('\n✅ Left room - check messages above for leave_room event');
    
    setTimeout(async () => {
      await browser.close();
    }, 3000);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    await browser.close();
  }
}

testLeaveRoomEvent();