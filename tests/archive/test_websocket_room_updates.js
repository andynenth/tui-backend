const { chromium } = require('playwright');

/**
 * WEBSOCKET ROOM UPDATES INVESTIGATION
 * 
 * Focuses specifically on capturing and analyzing room_update WebSocket messages
 * to identify why room state synchronization is broken.
 */

async function investigateWebSocketRoomUpdates() {
  console.log('🔍 WEBSOCKET ROOM UPDATES INVESTIGATION');
  console.log('=======================================');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000
  });
  
  try {
    const evidence = {
      allMessages: [],
      roomUpdates: [],
      playerJoins: [],
      playerLeaves: []
    };
    
    const captureMessages = (page, playerName) => {
      page.on('websocket', ws => {
        ws.on('framereceived', data => {
          try {
            const parsed = JSON.parse(data.payload);
            
            evidence.allMessages.push({
              timestamp: new Date().toISOString(),
              receiver: playerName,
              event: parsed.event,
              data: parsed.data
            });
            
            if (parsed.event === 'room_update') {
              const roomUpdate = {
                timestamp: new Date().toISOString(),
                receiver: playerName,
                room_id: parsed.data?.room_id,
                host_name: parsed.data?.host_name,
                started: parsed.data?.started,
                players: parsed.data?.players || [],
                fullData: parsed.data
              };
              
              evidence.roomUpdates.push(roomUpdate);
              
              console.log(`📥 ${playerName} room_update:`);
              console.log(`   Room ID: ${roomUpdate.room_id}`);
              console.log(`   Host: ${roomUpdate.host_name}`);
              console.log(`   Started: ${roomUpdate.started}`);
              console.log(`   Players (${roomUpdate.players.length}):`);
              roomUpdate.players.forEach((player, i) => {
                console.log(`     ${i}: ${player ? `${player.name} (${player.is_bot ? 'bot' : 'human'})` : 'null'}`);
              });
              console.log(`   Full data keys: ${Object.keys(roomUpdate.fullData || {}).join(', ')}`);
            }
            
            if (parsed.event === 'room_joined') {
              evidence.playerJoins.push({
                timestamp: new Date().toISOString(),
                receiver: playerName,
                success: parsed.data?.success,
                room_id: parsed.data?.room_id,
                seat_position: parsed.data?.seat_position,
                is_host: parsed.data?.is_host,
                fullData: parsed.data
              });
              
              console.log(`🔗 ${playerName} room_joined:`, {
                success: parsed.data?.success,
                seat_position: parsed.data?.seat_position,
                is_host: parsed.data?.is_host
              });
            }
          } catch (e) {
            // Ignore parse errors
          }
        });
      });
    };
    
    // === Setup Host ===
    console.log('\n=== Setup Host ===');
    const hostContext = await browser.newContext();
    const hostPage = await hostContext.newPage();
    captureMessages(hostPage, 'Host');
    
    await hostPage.goto('http://localhost:5050');
    await hostPage.waitForLoadState('networkidle');
    
    await hostPage.locator('input[type="text"]').first().fill('Host');
    await hostPage.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await hostPage.waitForTimeout(2000);
    
    // Create room
    const createBtn = await hostPage.locator('button').filter({ hasText: /create/i }).first();
    await createBtn.click();
    console.log('🏗️ Host created room');
    await hostPage.waitForTimeout(5000);
    
    // === Setup Joiner ===
    console.log('\n=== Setup Joiner ===');
    const joinerContext = await browser.newContext();
    const joinerPage = await joinerContext.newPage();
    captureMessages(joinerPage, 'Joiner');
    
    await joinerPage.goto('http://localhost:5050');
    await joinerPage.waitForLoadState('networkidle');
    
    await joinerPage.locator('input[type="text"]').first().fill('Joiner');
    await joinerPage.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await joinerPage.waitForTimeout(3000);
    
    // Join room
    const roomCards = await joinerPage.locator('.lp-roomCard').all();
    if (roomCards.length > 0) {
      await roomCards[0].click();
      console.log('🔗 Joiner attempting to join room');
      await joinerPage.waitForTimeout(5000);
    }
    
    // === Analysis ===
    console.log('\n=== WebSocket Message Analysis ===');
    
    console.log(`\n📊 Message Statistics:`);
    console.log(`   Total messages: ${evidence.allMessages.length}`);
    console.log(`   Room updates: ${evidence.roomUpdates.length}`);
    console.log(`   Player joins: ${evidence.playerJoins.length}`);
    
    console.log(`\n📡 All Messages by Type:`);
    const messagesByType = {};
    evidence.allMessages.forEach(msg => {
      if (!messagesByType[msg.event]) {
        messagesByType[msg.event] = [];
      }
      messagesByType[msg.event].push(msg);
    });
    
    Object.keys(messagesByType).forEach(event => {
      console.log(`   ${event}: ${messagesByType[event].length} messages`);
    });
    
    console.log(`\n🔍 Room Update Details:`);
    evidence.roomUpdates.forEach((update, i) => {
      console.log(`\n${i + 1}. ${update.receiver} at ${update.timestamp}:`);
      console.log(`   Room: ${update.room_id}, Host: ${update.host_name}, Started: ${update.started}`);
      console.log(`   Players array length: ${update.players.length}`);
      
      update.players.forEach((player, j) => {
        if (player && typeof player === 'object') {
          console.log(`     Slot ${j}: ${player.name} (${player.is_bot ? 'bot' : 'human'}, id: ${player.player_id || 'N/A'})`);
        } else {
          console.log(`     Slot ${j}: ${player}`);
        }
      });
      
      // Check for missing or malformed data
      if (!update.host_name) {
        console.log(`   ⚠️ WARNING: host_name is missing or undefined`);
      }
      if (update.players.length === 0) {
        console.log(`   ⚠️ WARNING: players array is empty`);
      }
      if (update.players.some(p => p === null || p === undefined)) {
        console.log(`   ⚠️ WARNING: players array contains null/undefined entries`);
      }
    });
    
    console.log(`\n🎯 Root Cause Analysis:`);
    
    // Check if room updates are being sent to all players
    const hostUpdates = evidence.roomUpdates.filter(u => u.receiver === 'Host');
    const joinerUpdates = evidence.roomUpdates.filter(u => u.receiver === 'Joiner');
    
    console.log(`   Host received ${hostUpdates.length} room updates`);
    console.log(`   Joiner received ${joinerUpdates.length} room updates`);
    
    if (hostUpdates.length === joinerUpdates.length) {
      console.log(`   ✅ Both players received same number of updates`);
    } else {
      console.log(`   ❌ ISSUE: Players received different numbers of updates`);
    }
    
    // Check if room updates contain correct data
    const hasValidData = evidence.roomUpdates.every(update => 
      update.room_id && 
      Array.isArray(update.players) && 
      update.players.length > 0
    );
    
    if (hasValidData) {
      console.log(`   ✅ All room updates contain valid basic data`);
    } else {
      console.log(`   ❌ ISSUE: Some room updates are missing basic data`);
    }
    
    // Check for empty or incomplete room_update messages
    const incompleteUpdates = evidence.roomUpdates.filter(update => 
      !update.host_name || 
      !update.room_id || 
      update.players.length === 0 ||
      update.players.some(p => !p || !p.name)
    );
    
    if (incompleteUpdates.length > 0) {
      console.log(`   ❌ ISSUE: ${incompleteUpdates.length} incomplete room_update messages found`);
      incompleteUpdates.forEach((update, i) => {
        console.log(`     ${i + 1}. ${update.receiver}: missing ${!update.host_name ? 'host_name ' : ''}${!update.room_id ? 'room_id ' : ''}${update.players.length === 0 ? 'players' : ''}`);
      });
    } else {
      console.log(`   ✅ All room updates appear complete`);
    }
    
    console.log('\n⏱️ Keeping browsers open for manual verification...');
    await hostPage.waitForTimeout(20000);
    
  } catch (error) {
    console.error('❌ Investigation failed:', error);
  } finally {
    await browser.close();
  }
}

investigateWebSocketRoomUpdates().catch(console.error);