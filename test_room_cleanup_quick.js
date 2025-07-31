const { chromium } = require('playwright');

async function testRoomCleanupQuick() {
  console.log('🔍 Quick Room Cleanup Test\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: false
  });

  const context1 = await browser.newContext();
  const context2 = await browser.newContext();
  
  const player1 = await context1.newPage();
  const player2 = await context2.newPage();
  
  let player1Rooms = [];
  let player2Rooms = [];
  
  function setupWebSocketMonitoring(page, playerName) {
    page.on('websocket', ws => {
      ws.on('framereceived', event => {
        try {
          const data = JSON.parse(event.payload);
          if (data.event === 'room_list_update') {
            const rooms = data.data.rooms || [];
            if (playerName === 'Player1') {
              player1Rooms = [...rooms];
            } else {
              player2Rooms = [...rooms];
            }
            console.log(`📋 ${playerName}: ${rooms.length} rooms`);
          }
        } catch (e) {}
      });
    });
  }
  
  setupWebSocketMonitoring(player1, 'Player1');
  setupWebSocketMonitoring(player2, 'Player2');

  try {
    // Quick setup
    console.log('Setting up players...');
    await player1.goto('http://localhost:5050');
    await player1.fill('input[type="text"]', 'Player1');
    await player1.click('button:has-text("Enter Lobby")');
    await player1.waitForTimeout(1000);
    
    await player2.goto('http://localhost:5050');
    await player2.fill('input[type="text"]', 'Player2');
    await player2.click('button:has-text("Enter Lobby")');
    await player2.waitForTimeout(1000);
    
    // Test 1: Create and leave room
    console.log('\n🧪 Test: Create room and leave');
    await player1.click('button:has-text("Create Room")');
    await player1.waitForSelector('button:has-text("Leave Room")', { timeout: 5000 });
    
    await player1.waitForTimeout(1000);
    const roomsBeforeLeave = player1Rooms.length;
    console.log(`  Rooms before leave: ${roomsBeforeLeave}`);
    
    // Leave room
    await player1.click('button:has-text("Leave Room")');
    await player1.waitForURL('**/lobby', { timeout: 5000 });
    
    // Wait for cleanup
    await player1.waitForTimeout(2000);
    await player2.waitForTimeout(2000);
    
    const roomsAfterLeave = player1Rooms.length;
    console.log(`  Rooms after leave: ${roomsAfterLeave}`);
    
    if (roomsAfterLeave < roomsBeforeLeave) {
      console.log('  ✅ Room cleanup working!');
    } else {
      console.log('  ❌ Room not cleaned up');
    }
    
    console.log('\n📊 Final Status:');
    console.log(`  Player 1 sees: ${player1Rooms.length} rooms`);
    console.log(`  Player 2 sees: ${player2Rooms.length} rooms`);
    
    setTimeout(async () => {
      await browser.close();
    }, 5000);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    await browser.close();
  }
}

testRoomCleanupQuick();