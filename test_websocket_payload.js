const { chromium } = require('playwright');

async function testWebSocketPayload() {
  console.log('🔍 Testing WebSocket Payload Structure\n');
  
  const browser = await chromium.launch({ headless: false, devtools: false });
  const page = await browser.newPage();
  
  // Capture raw WebSocket messages
  page.on('websocket', ws => {
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        if (data.event === 'room_list_update') {
          console.log('🔍 RAW room_list_update payload:');
          console.log(JSON.stringify(data, null, 2));
          console.log('\\n📊 Data structure analysis:');
          console.log('- event:', data.event);
          console.log('- data:', typeof data.data);
          console.log('- data.rooms:', data.data?.rooms);
          console.log('- data.rooms type:', Array.isArray(data.data?.rooms) ? 'Array' : typeof data.data?.rooms);
          console.log('- data.rooms length:', data.data?.rooms?.length);
          if (data.data?.rooms?.length > 0) {
            console.log('\\n🏠 First room structure:');
            console.log(JSON.stringify(data.data.rooms[0], null, 2));
          }
        }
      } catch (e) {
        console.log('Failed to parse WebSocket message:', e.message);
      }
    });
  });
  
  try {
    console.log('🟢 Connecting to lobby...');
    await page.goto('http://localhost:5050');
    await page.fill('input[type="text"]', 'TestPlayer');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(2000);
    
    console.log('\\n🏠 Creating room to trigger room_list_update...');
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(3000);
    
    console.log('\\n✅ WebSocket payload analysis complete');
    
    setTimeout(async () => {
      await browser.close();
    }, 2000);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    await browser.close();
  }
}

testWebSocketPayload();