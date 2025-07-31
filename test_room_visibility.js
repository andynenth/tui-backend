const { chromium } = require('playwright');

async function testRoomVisibility() {
  console.log('🔍 Testing Room Visibility Between Players\n');
  
  const browser1 = await chromium.launch({ headless: false, devtools: false });
  const browser2 = await chromium.launch({ headless: false, devtools: false });
  
  const page1 = await browser1.newPage();
  const page2 = await browser2.newPage();
  
  // Monitor room list updates
  page1.on('websocket', ws => {
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        if (data.event === 'room_list_update') {
          console.log(`👤 P1 room_list_update: ${data.data.rooms.length} rooms`);
        }
      } catch (e) {}
    });
  });
  
  page2.on('websocket', ws => {
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        if (data.event === 'room_list_update') {
          console.log(`👥 P2 room_list_update: ${data.data.rooms.length} rooms`);
        }
      } catch (e) {}
    });
  });
  
  try {
    // Player 1: Enter Lobby
    console.log('🟢 Player 1: Entering lobby...');
    await page1.goto('http://localhost:5050');
    await page1.fill('input[type="text"]', 'Player1');
    await page1.click('button:has-text("Enter Lobby")');
    await page1.waitForTimeout(2000);
    
    // Player 2: Enter Lobby  
    console.log('🟢 Player 2: Entering lobby...');
    await page2.goto('http://localhost:5050');
    await page2.fill('input[type="text"]', 'Player2');
    await page2.click('button:has-text("Enter Lobby")');
    await page2.waitForTimeout(2000);
    
    console.log('\\n📊 Initial lobby state:');
    const p1Rooms = await page1.$$('[data-testid="room-card"], .room-card, .room-item').then(els => els.length);
    const p2Rooms = await page2.$$('[data-testid="room-card"], .room-card, .room-item').then(els => els.length);
    console.log(`Player 1 sees: ${p1Rooms} rooms`);
    console.log(`Player 2 sees: ${p2Rooms} rooms`);
    
    // Player 1: Create Room
    console.log('\\n🏠 Player 1: Creating room...');
    await page1.click('button:has-text("Create Room")');
    await page1.waitForSelector('button:has-text("Leave Room")', { timeout: 5000 });
    console.log('✅ Player 1 created room and is now in room');
    
    // Wait for room list updates
    await page2.waitForTimeout(3000);
    
    console.log('\\n📊 After room creation:');
    
    // Player 1 should be in room now, let's go back to lobby to check
    await page1.click('button:has-text("Leave Room")');
    await page1.waitForURL('**/lobby', { timeout: 5000 });
    await page1.waitForTimeout(2000);
    
    const p1RoomsAfter = await page1.$$('[data-testid="room-card"], .room-card, .room-item').then(els => els.length);
    const p2RoomsAfter = await page2.$$('[data-testid="room-card"], .room-card, .room-item').then(els => els.length);
    console.log(`Player 1 sees: ${p1RoomsAfter} rooms`);
    console.log(`Player 2 sees: ${p2RoomsAfter} rooms`);
    
    if (p1RoomsAfter === 0 && p2RoomsAfter === 0) {
      console.log('\\n🚨 Room was immediately cleaned up after host left');
    } else if (p1RoomsAfter > 0 || p2RoomsAfter > 0) {
      console.log('\\n✅ Rooms are visible after creation');
    }
    
    setTimeout(async () => {
      await browser1.close();
      await browser2.close();
    }, 3000);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    await browser1.close();
    await browser2.close();
  }
}

testRoomVisibility();