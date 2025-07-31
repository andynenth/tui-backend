const { chromium } = require('playwright');

async function testHostLeaveCleanup() {
  console.log('🔍 Testing Host Leave Room Cleanup\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  // Create two browser contexts for two players
  const context1 = await browser.newContext();
  const context2 = await browser.newContext();
  
  const player1 = await context1.newPage();
  const player2 = await context2.newPage();
  
  // Track room lists for both players
  let player1Rooms = [];
  let player2Rooms = [];
  
  // Monitor WebSocket messages for both players
  function setupWebSocketMonitoring(page, playerName) {
    page.on('websocket', ws => {
      ws.on('framereceived', event => {
        try {
          const data = JSON.parse(event.payload);
          if (data.event === 'room_list_update') {
            const rooms = data.data.rooms || [];
            console.log(`📋 ${playerName} sees ${rooms.length} rooms:`, rooms.map(r => `${r.room_code} (${r.host_name})`));
            
            if (playerName === 'Player1') {
              player1Rooms = [...rooms];
            } else {
              player2Rooms = [...rooms];
            }
          }
          
          if (data.event === 'room_closed') {
            console.log(`🚪 ${playerName} received room_closed:`, data.data);
          }
        } catch (e) {}
      });
    });
  }
  
  setupWebSocketMonitoring(player1, 'Player1');
  setupWebSocketMonitoring(player2, 'Player2');

  try {
    console.log('📍 Step 1: Player 1 >> Enter Lobby');
    await player1.goto('http://localhost:5050');
    await player1.waitForLoadState('networkidle');
    await player1.fill('input[type="text"]', 'Player1');
    await player1.click('button:has-text("Enter Lobby")');
    await player1.waitForTimeout(2000);
    console.log('  ✅ Player 1 in lobby');
    
    console.log('\n📍 Step 2: Player 2 >> Enter Lobby');
    await player2.goto('http://localhost:5050');
    await player2.waitForLoadState('networkidle');
    await player2.fill('input[type="text"]', 'Player2');
    await player2.click('button:has-text("Enter Lobby")');
    await player2.waitForTimeout(2000);
    console.log('  ✅ Player 2 in lobby');
    
    // Wait for initial room list sync
    await player1.waitForTimeout(1000);
    await player2.waitForTimeout(1000);
    
    console.log('\n📍 Step 3: Player 1 >> Create Room');
    await player1.click('button:has-text("Create Room")');
    await player1.waitForSelector('button:has-text("Leave Room")', { timeout: 10000 });
    console.log('  ✅ Player 1 created room and is in room page');
    
    // Wait for room list updates
    await player1.waitForTimeout(2000);
    await player2.waitForTimeout(2000);
    
    const room1Code = await player1.evaluate(() => {
      const url = window.location.href;
      const match = url.match(/room\/([A-Z0-9]+)/);
      return match ? match[1] : null;
    });
    
    console.log(`  🏠 Room created: ${room1Code}`);
    console.log(`  📊 Player 1 room list: ${player1Rooms.length} rooms`);
    console.log(`  📊 Player 2 room list: ${player2Rooms.length} rooms`);
    
    console.log('\n📍 Step 4: Player 1 >> Leave Room (Should delete room)');
    await player1.click('button:has-text("Leave Room")');
    await player1.waitForURL('**/lobby', { timeout: 10000 });
    console.log('  ✅ Player 1 returned to lobby');
    
    // Wait for room cleanup
    await player1.waitForTimeout(3000);
    await player2.waitForTimeout(3000);
    
    console.log(`  📊 After leave - Player 1 room list: ${player1Rooms.length} rooms`);
    console.log(`  📊 After leave - Player 2 room list: ${player2Rooms.length} rooms`);
    
    if (player1Rooms.length === 0 && player2Rooms.length === 0) {
      console.log('  ✅ Room properly cleaned up for both players');
    } else {
      console.log('  ❌ ISSUE: Room not cleaned up!');
      console.log('    Player 1 still sees:', player1Rooms.map(r => r.room_code));
      console.log('    Player 2 still sees:', player2Rooms.map(r => r.room_code));
    }
    
    console.log('\n📍 Step 5: Player 1 >> Create Room (again)');
    await player1.click('button:has-text("Create Room")');
    await player1.waitForSelector('button:has-text("Leave Room")', { timeout: 10000 });
    
    const room2Code = await player1.evaluate(() => {
      const url = window.location.href;
      const match = url.match(/room\/([A-Z0-9]+)/);
      return match ? match[1] : null;  
    });
    
    console.log(`  🏠 Second room created: ${room2Code}`);
    
    // Wait for room list updates
    await player1.waitForTimeout(2000);
    await player2.waitForTimeout(2000);
    
    console.log(`  📊 Player 1 room list: ${player1Rooms.length} rooms`);
    console.log(`  📊 Player 2 room list: ${player2Rooms.length} rooms`);
    
    console.log('\n📍 Step 6: Player 1 >> Leave Room (again - should delete room)');
    await player1.click('button:has-text("Leave Room")');
    await player1.waitForURL('**/lobby', { timeout: 10000 });
    console.log('  ✅ Player 1 returned to lobby');
    
    // Wait for room cleanup
    await player1.waitForTimeout(3000);
    await player2.waitForTimeout(3000);
    
    console.log(`  📊 After second leave - Player 1 room list: ${player1Rooms.length} rooms`);
    console.log(`  📊 After second leave - Player 2 room list: ${player2Rooms.length} rooms`);
    
    console.log('\n📊 FINAL ANALYSIS:');
    console.log('=================');
    
    if (player1Rooms.length === 0 && player2Rooms.length === 0) {
      console.log('✅ SUCCESS: Both players see clean lobby - room cleanup working correctly');
    } else {
      console.log('❌ FAILURE: Room cleanup not working properly');
      console.log(`   Player 1 sees ${player1Rooms.length} abandoned rooms:`, player1Rooms.map(r => `${r.room_code} (host: ${r.host_name})`));
      console.log(`   Player 2 sees ${player2Rooms.length} abandoned rooms:`, player2Rooms.map(r => `${r.room_code} (host: ${r.host_name})`));
      
      console.log('\n🔍 ROOT CAUSE ANALYSIS:');
      console.log('- Rooms are being created successfully');  
      console.log('- Host can leave rooms and return to lobby');
      console.log('- But rooms are NOT being deleted from the backend');
      console.log('- This suggests our fix to prevent premature deletion broke legitimate cleanup');
    }
    
    console.log('\n🔧 Keeping browsers open for manual inspection...');
    await new Promise(() => {}); // Keep open indefinitely
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
    await browser.close();
  }
}

testHostLeaveCleanup();