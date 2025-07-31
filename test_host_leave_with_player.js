const { chromium } = require('playwright');

async function testHostLeaveWithPlayer() {
  console.log('🔍 Testing Host Leave with Other Player Still in Room\n');
  
  // Launch two browsers for two players
  const browser1 = await chromium.launch({ headless: false, devtools: false });
  const browser2 = await chromium.launch({ headless: false, devtools: false });
  
  const page1 = await browser1.newPage();
  const page2 = await browser2.newPage();
  
  // Monitor WebSocket messages for both players
  const player1Messages = [];
  const player2Messages = [];
  
  page1.on('websocket', ws => {
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        player1Messages.push({timestamp: Date.now(), event: data.event, data: data.data});
        console.log(`👤 P1 RECEIVED: ${data.event}`, data.data);
      } catch (e) {}
    });
  });
  
  page2.on('websocket', ws => {
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        player2Messages.push({timestamp: Date.now(), event: data.event, data: data.data});
        console.log(`👥 P2 RECEIVED: ${data.event}`, data.data);
      } catch (e) {}
    });
  });

  try {
    console.log('📋 Test Sequence:');
    console.log('Player 1 >> Enter Lobby');
    console.log('Player 2 >> Enter Lobby');  
    console.log('Player 1 >> Create Room');
    console.log('Player 2 >> Join Room');
    console.log('Player 1 >> Leave Room');
    console.log('Expected: Room should be removed, Player 2 sent to lobby\n');
    
    // Player 1: Enter Lobby
    console.log('🟢 Player 1: Entering lobby...');
    await page1.goto('http://localhost:5050');
    await page1.fill('input[type="text"]', 'Player1');
    await page1.click('button:has-text("Enter Lobby")');
    await page1.waitForTimeout(1000);
    
    // Player 2: Enter Lobby  
    console.log('🟢 Player 2: Entering lobby...');
    await page2.goto('http://localhost:5050');
    await page2.fill('input[type="text"]', 'Player2');
    await page2.click('button:has-text("Enter Lobby")');
    await page2.waitForTimeout(1000);
    
    // Player 1: Create Room
    console.log('🏠 Player 1: Creating room...');
    await page1.click('button:has-text("Create Room")');
    await page1.waitForSelector('button:has-text("Leave Room")', { timeout: 5000 });
    await page1.waitForTimeout(1000);
    
    // Player 2: Join Room
    console.log('🚪 Player 2: Joining room...');
    await page2.click('button:has-text("Join")');
    await page2.waitForSelector('button:has-text("Leave Room")', { timeout: 5000 });
    await page2.waitForTimeout(1000);
    
    console.log('\\n📊 Current state before host leaves:');
    const p1RoomInfo = await page1.textContent('.room-info, .game-room, [data-testid="room-info"]').catch(() => 'No room info found');
    const p2RoomInfo = await page2.textContent('.room-info, .game-room, [data-testid="room-info"]').catch(() => 'No room info found');
    console.log('Player 1 sees:', p1RoomInfo);
    console.log('Player 2 sees:', p2RoomInfo);
    
    // Player 1: Leave Room (Host leaves)
    console.log('\\n🚪 Player 1 (HOST): Leaving room...');
    console.log('📡 Monitoring WebSocket events:');
    
    await page1.click('button:has-text("Leave Room")');
    await page1.waitForURL('**/lobby', { timeout: 5000 });
    
    // Wait for room cleanup events
    await page2.waitForTimeout(3000);
    
    console.log('\\n🔍 Final State Analysis:');
    
    // Check Player 1 (should be in lobby)
    const p1URL = page1.url();
    const p1InLobby = p1URL.includes('/lobby');
    console.log(`Player 1 URL: ${p1URL} (In lobby: ${p1InLobby})`);
    
    // Check Player 2 (should be redirected to lobby)
    const p2URL = page2.url();
    const p2InLobby = p2URL.includes('/lobby');
    console.log(`Player 2 URL: ${p2URL} (In lobby: ${p2InLobby})`);
    
    // Check if any rooms exist in lobby
    const lobbyRooms1 = await page1.$$eval('[data-testid="room-card"], .room-card', els => els.length).catch(() => 0);
    const lobbyRooms2 = await page2.$$eval('[data-testid="room-card"], .room-card', els => els.length).catch(() => 0);
    
    console.log(`\\n📋 Results:`);
    console.log(`✅ Player 1 in lobby: ${p1InLobby}`);
    console.log(`${p2InLobby ? '✅' : '❌'} Player 2 in lobby: ${p2InLobby}`);
    console.log(`Player 1 sees ${lobbyRooms1} rooms`);
    console.log(`Player 2 sees ${lobbyRooms2} rooms`);
    console.log(`${lobbyRooms1 === 0 && lobbyRooms2 === 0 ? '✅' : '❌'} Room properly cleaned up: ${lobbyRooms1 === 0 && lobbyRooms2 === 0}`);
    
    if (!p2InLobby) {
      console.log('\\n🚨 BUG DETECTED: Player 2 was not redirected to lobby when host left!');
    }
    
    if (lobbyRooms1 > 0 || lobbyRooms2 > 0) {
      console.log('\\n🚨 BUG DETECTED: Room was not properly cleaned up when host left!');
    }
    
    // Log key WebSocket events
    console.log('\\n📡 Key WebSocket Events:');
    console.log('Player 1 events:', player1Messages.filter(m => ['player_left_room', 'room_closed', 'host_changed'].includes(m.event)));
    console.log('Player 2 events:', player2Messages.filter(m => ['player_left_room', 'room_closed', 'host_changed', 'redirect'].includes(m.event)));
    
    setTimeout(async () => {
      await browser1.close();
      await browser2.close();
    }, 3000);
    
  } catch (error) {
    console.error('❌ Test Error:', error.message);
    await browser1.close();
    await browser2.close();
  }
}

testHostLeaveWithPlayer();