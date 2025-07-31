const { chromium } = require('playwright');

async function testHostLeaveWithPlayerCorrected() {
  console.log('🔍 Testing Host Leave with Other Player (Corrected)\n');
  
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
        if (['player_left_room', 'room_closed', 'host_changed', 'error'].includes(data.event)) {
          console.log(`👤 P1 RECEIVED: ${data.event}`, data.data);
        }
      } catch (e) {}
    });
  });
  
  page2.on('websocket', ws => {
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        player2Messages.push({timestamp: Date.now(), event: data.event, data: data.data});
        if (['player_left_room', 'room_closed', 'host_changed', 'error', 'redirect'].includes(data.event)) {
          console.log(`👥 P2 RECEIVED: ${data.event}`, data.data);
        }
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
    console.log('Expected: Room should be removed, Player 2 sent to lobby\\n');
    
    // Player 1: Enter Lobby and Create Room
    console.log('🟢 Player 1: Creating room...');
    await page1.goto('http://localhost:5050');
    await page1.fill('input[type="text"]', 'Player1');
    await page1.click('button:has-text("Enter Lobby")');
    await page1.waitForTimeout(1000);
    await page1.click('button:has-text("Create Room")');
    await page1.waitForSelector('button:has-text("Leave Room")', { timeout: 5000 });
    console.log('✅ Player 1 created room');
    
    // Player 2: Enter Lobby  
    console.log('🟢 Player 2: Entering lobby...');
    await page2.goto('http://localhost:5050');
    await page2.fill('input[type="text"]', 'Player2');
    await page2.click('button:has-text("Enter Lobby")');
    await page2.waitForTimeout(2000);
    
    // Player 2: Join the NEWEST room (should be Player1's)
    console.log('🚪 Player 2: Joining newest room...');
    const roomCards = await page2.$$('.lp-roomCard');
    console.log(`Found ${roomCards.length} room cards`);
    
    if (roomCards.length > 0) {
      // Find Player1's room specifically
      let player1RoomCard = null;
      for (const card of roomCards) {
        const hostName = await card.$eval('.lp-hostName', el => el.textContent).catch(() => '');
        if (hostName.includes('Player1')) {
          const occupancy = await card.$eval('.lp-roomOccupancy', el => el.textContent).catch(() => '0/4');
          console.log(`Found Player1's room with occupancy: ${occupancy}`);
          player1RoomCard = card;
          break;
        }
      }
      
      if (player1RoomCard) {
        await player1RoomCard.click();
        await page2.waitForURL('**/room/**', { timeout: 5000 });
        console.log('✅ Player 2 joined Player1\'s room');
      } else {
        throw new Error('Could not find Player1\'s room');
      }
    } else {
      throw new Error('No room cards found');
    }
    
    // Wait for both players to be stable in the room
    await page1.waitForTimeout(1000);
    await page2.waitForTimeout(1000);
    
    console.log('\\n📊 Current state before host leaves:');
    const p1URL = page1.url();
    const p2URL = page2.url();
    console.log('Player 1 URL:', p1URL);
    console.log('Player 2 URL:', p2URL);
    
    // Player 1: Leave Room (Host leaves)
    console.log('\\n🚪 Player 1 (HOST): Leaving room...');
    console.log('📡 Monitoring WebSocket events for room cleanup:');
    
    await page1.click('button:has-text("Leave Room")');
    await page1.waitForURL('**/lobby', { timeout: 5000 });
    console.log('✅ Player 1 returned to lobby');
    
    // Wait for room cleanup events and Player 2 redirection
    console.log('⏳ Waiting for room cleanup and Player 2 redirection...');
    await page2.waitForTimeout(5000);
    
    console.log('\\n🔍 Final State Analysis:');
    
    // Check final URLs
    const p1FinalURL = page1.url();
    const p2FinalURL = page2.url();
    console.log(`Player 1 final URL: ${p1FinalURL}`);
    console.log(`Player 2 final URL: ${p2FinalURL}`);
    
    const p1InLobby = p1FinalURL.includes('/lobby');
    const p2InLobby = p2FinalURL.includes('/lobby');
    
    // Check room counts in lobby
    let lobbyRooms1 = 0, lobbyRooms2 = 0;
    
    if (p1InLobby) {
      lobbyRooms1 = await page1.$$('.lp-roomCard').then(cards => cards.length);
    }
    
    if (p2InLobby) {
      lobbyRooms2 = await page2.$$('.lp-roomCard').then(cards => cards.length);
    } else {
      // If P2 not in lobby, try to get them there to check
      try {
        await page2.goto('http://localhost:5050/lobby');
        await page2.waitForTimeout(2000);
        lobbyRooms2 = await page2.$$('.lp-roomCard').then(cards => cards.length);
      } catch (e) {
        console.log('Could not navigate Player 2 to lobby for room count');
      }
    }
    
    console.log(`\\n📋 Results:`);
    console.log(`✅ Player 1 in lobby: ${p1InLobby}`);
    console.log(`${p2InLobby ? '✅' : '❌'} Player 2 in lobby: ${p2InLobby}`);
    console.log(`Player 1 sees ${lobbyRooms1} rooms in lobby`);
    console.log(`Player 2 sees ${lobbyRooms2} rooms in lobby`);
    
    // Check if the specific room was cleaned up
    const roomStillExists = lobbyRooms1 > 0 || lobbyRooms2 > 0;
    console.log(`${roomStillExists ? '❌' : '✅'} Room cleanup: ${roomStillExists ? 'Failed - rooms still exist' : 'Success - room removed'}`);
    
    // Summary
    if (p2InLobby && !roomStillExists) {
      console.log('\\n🎉 SUCCESS: Host leave functionality working correctly!');
    } else {
      console.log('\\n🚨 ISSUE DETECTED:');
      if (!p2InLobby) {
        console.log('- Player 2 was not redirected to lobby when host left');
      }
      if (roomStillExists) {
        console.log('- Room was not properly cleaned up when host left');
      }
    }
    
    // Log key events
    console.log('\\n📡 Key WebSocket Events Summary:');
    const p1KeyEvents = player1Messages.filter(m => 
      ['player_left_room', 'room_closed', 'host_changed', 'error'].includes(m.event)
    ).map(m => `${m.event}: ${JSON.stringify(m.data)}`);
    const p2KeyEvents = player2Messages.filter(m => 
      ['player_left_room', 'room_closed', 'host_changed', 'error', 'redirect'].includes(m.event)
    ).map(m => `${m.event}: ${JSON.stringify(m.data)}`);
    
    console.log('Player 1 key events:', p1KeyEvents);
    console.log('Player 2 key events:', p2KeyEvents);
    
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

testHostLeaveWithPlayerCorrected();