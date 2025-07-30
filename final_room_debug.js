const { chromium } = require('playwright');

async function debugRoomDisplay() {
  console.log('🔍 Final Room Display Debug...');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });
  
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Enhanced console monitoring
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('room_list_update') || text.includes('Received') || text.includes('setRooms')) {
        console.log(`[BROWSER] 🎯 ${text}`);
      }
    });
    
    // WebSocket monitoring
    page.on('websocket', ws => {
      console.log(`🔗 WebSocket connected: ${ws.url()}`);
      
      ws.on('framereceived', data => {
        try {
          const message = JSON.parse(data.payload);
          if (message.event === 'room_list_update') {
            console.log(`[WS] 📥 room_list_update:`, message.data);
            console.log(`[WS] 🏠 Rooms count: ${message.data.rooms?.length || 0}`);
          }
        } catch (e) {}
      });
    });
    
    // Enter lobby
    await page.goto('http://localhost:5050');
    await page.fill('input[type="text"]', 'DebugPlayer');
    await page.click('button');
    await page.waitForTimeout(3000);
    
    console.log('📊 Current lobby state:');
    const state = await page.evaluate(() => {
      return {
        url: window.location.href,
        roomCards: document.querySelectorAll('.lp-roomCard').length,
        emptyState: !!document.querySelector('.lp-emptyState'),
        roomList: !!document.querySelector('.lp-roomList'),
        roomCount: document.querySelector('.lp-roomCount')?.textContent,
        connection: document.querySelector('.connection-status')?.textContent
      };
    });
    console.log(state);
    
    // Wait and check for room_list_update events
    console.log('⏳ Waiting 10 seconds for any room_list_update events...');
    await page.waitForTimeout(10000);
    
  } catch (error) {
    console.error('❌ Debug failed:', error);
  } finally {
    await browser.close();
  }
}

if (require.main === module) {
  debugRoomDisplay().catch(console.error);
}

module.exports = { debugRoomDisplay };