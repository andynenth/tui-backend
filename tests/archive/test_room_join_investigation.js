const { chromium } = require('playwright');

/**
 * ROOM JOIN INVESTIGATION TEST
 * 
 * SCENARIO TO PROVE:
 * 1. Player 1 >> join lobby
 * 2. Player 1 >> create room (4/4 players: 1 human + 3 bots)
 * 3. Player 1 >> remove bot (should become 3/4 players)
 * 4. Player 2 >> join lobby
 * 5. Player 2 >> cannot join room (THE BUG TO PROVE)
 * 
 * ROOT CAUSE HYPOTHESIS:
 * Room state synchronization issue where join validation still sees room as "full"
 * even after bot removal due to timing/async issues.
 */

class RoomJoinInvestigator {
  constructor() {
    this.evidence = {
      websocketMessages: [],
      roomStates: [],
      joinAttempts: [],
      errorMessages: [],
      timeline: []
    };
  }

  logEvent(event, data = {}) {
    const entry = {
      timestamp: new Date().toISOString(),
      event,
      ...data
    };
    this.evidence.timeline.push(entry);
    console.log(`📝 ${entry.timestamp}: ${event}`, data);
  }

  async captureWebSocketMessages(page, playerName) {
    page.on('websocket', ws => {
      ws.on('framereceived', data => {
        try {
          const parsed = JSON.parse(data.payload);
          this.evidence.websocketMessages.push({
            timestamp: new Date().toISOString(),
            player: playerName,
            direction: 'received',
            event: parsed.event,
            data: parsed.data
          });

          // Log important events
          if (['room_list_update', 'room_update', 'error', 'room_created', 'player_removed'].includes(parsed.event)) {
            console.log(`📥 ${playerName} received: ${parsed.event}`, 
              parsed.event === 'room_list_update' ? `${parsed.data?.rooms?.length || 0} rooms` :
              parsed.event === 'room_update' ? `players: ${JSON.stringify(parsed.data?.players)}` :
              parsed.event === 'error' ? parsed.data?.message :
              '');
          }
        } catch (e) {
          // Ignore parse errors
        }
      });

      ws.on('framesent', data => {
        try {
          const parsed = JSON.parse(data.payload);
          this.evidence.websocketMessages.push({
            timestamp: new Date().toISOString(),
            player: playerName,
            direction: 'sent',
            event: parsed.event,
            data: parsed.data
          });

          // Log important outgoing events
          if (['join_room', 'remove_player'].includes(parsed.event)) {
            console.log(`📤 ${playerName} sent: ${parsed.event}`, parsed.data);
          }
        } catch (e) {
          // Ignore parse errors
        }
      });
    });
  }

  async setupPlayer(browser, playerName) {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Capture WebSocket messages
    await this.captureWebSocketMessages(page, playerName);
    
    this.logEvent(`Setup ${playerName}`, { player: playerName });
    
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    const nameInput = await page.locator('input[type="text"]').first();
    await nameInput.fill(playerName);
    
    const startButton = await page.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first();
    await startButton.click();
    
    await page.waitForTimeout(2000);
    this.logEvent(`${playerName} entered lobby`);
    
    return { context, page };
  }

  async createRoom(creatorPage) {
    this.logEvent('Creator attempting room creation');
    
    const createBtn = await creatorPage.locator('button').filter({ hasText: /create/i }).first();
    await createBtn.click();
    
    // Wait for room creation and navigation
    await creatorPage.waitForTimeout(5000);
    
    this.logEvent('Room creation completed');
    
    // Try to capture room state
    try {
      const currentUrl = creatorPage.url();
      const roomIdMatch = currentUrl.match(/\/room\/([^/?]+)/);
      if (roomIdMatch) {
        const roomId = roomIdMatch[1];
        this.logEvent('Room created successfully', { roomId });
        return roomId;
      }
    } catch (error) {
      this.logEvent('Could not extract room ID', { error: error.message });
    }
    
    return null;
  }

  async removeBotFromRoom(creatorPage) {
    this.logEvent('Creator attempting bot removal');
    
    try {
      // Look for remove/kick buttons
      const removeBtns = await creatorPage.locator('button:has-text("Remove"), button:has-text("Kick")').all();
      
      if (removeBtns.length > 0) {
        this.logEvent('Found remove buttons', { count: removeBtns.length });
        await removeBtns[0].click();
        await creatorPage.waitForTimeout(2000);
        this.logEvent('Bot removal button clicked');
        return true;
      } else {
        this.logEvent('No remove buttons found');
        
        // Try alternative approaches
        const playerSlots = await creatorPage.locator('.player-slot, .seat, [class*="player"], [class*="bot"]').all();
        this.logEvent('Found player slots', { count: playerSlots.length });
        
        if (playerSlots.length > 1) {
          // Try clicking on a bot slot (skip first slot which is likely the host)
          await playerSlots[1].click();
          await creatorPage.waitForTimeout(1000);
          this.logEvent('Clicked on player slot');
        }
        
        return false;
      }
    } catch (error) {
      this.logEvent('Error during bot removal', { error: error.message });
      return false;
    }
  }

  async attemptJoinRoom(joinerPage, roomId) {
    this.logEvent('Player 2 attempting to join room', { roomId });
    
    try {
      // Look for the room in the lobby
      const roomCards = await joinerPage.locator('.lp-roomCard, [class*="room"]').all();
      this.logEvent('Found room cards in lobby', { count: roomCards.length });
      
      if (roomCards.length > 0) {
        // Try to join the first available room
        await roomCards[0].click();
        await joinerPage.waitForTimeout(3000);
        
        // Check if we're now in a room or got an error
        const currentUrl = joinerPage.url();
        if (currentUrl.includes('/room/')) {
          this.logEvent('Join successful - in room page');
          return { success: true };
        } else {
          this.logEvent('Join failed - still in lobby');
          return { success: false, reason: 'Still in lobby after click' };
        }
      } else {
        this.logEvent('No room cards found');
        return { success: false, reason: 'No rooms visible in lobby' };
      }
    } catch (error) {
      this.logEvent('Error during join attempt', { error: error.message });
      return { success: false, reason: error.message };
    }
  }

  async checkRoomState(page, player) {
    try {
      // Try to get room count from UI
      const roomCountEl = await page.locator('.lp-roomCount').first();
      const roomCountText = await roomCountEl.textContent({ timeout: 3000 });
      
      const roomCards = await page.locator('.lp-roomCard').count();
      
      const state = {
        timestamp: new Date().toISOString(),
        player,
        roomCountText,
        actualRoomCards: roomCards
      };
      
      this.evidence.roomStates.push(state);
      this.logEvent(`Room state for ${player}`, state);
      
      return state;
    } catch (error) {
      this.logEvent(`Could not check room state for ${player}`, { error: error.message });
      return null;
    }
  }

  analyzeEvidence() {
    console.log('\n🔍 EVIDENCE ANALYSIS');
    console.log('===================');
    
    // 1. Timeline Analysis
    console.log('\n📅 TIMELINE OF EVENTS:');
    this.evidence.timeline.forEach((entry, i) => {
      console.log(`${i + 1}. ${entry.timestamp}: ${entry.event}`);
    });
    
    // 2. WebSocket Message Analysis
    console.log('\n📡 WEBSOCKET MESSAGES:');
    
    const roomCreatedMsgs = this.evidence.websocketMessages.filter(m => m.event === 'room_created');
    const roomUpdateMsgs = this.evidence.websocketMessages.filter(m => m.event === 'room_update');
    const playerRemovedMsgs = this.evidence.websocketMessages.filter(m => m.event === 'player_removed');
    const errorMsgs = this.evidence.websocketMessages.filter(m => m.event === 'error');
    const joinRoomMsgs = this.evidence.websocketMessages.filter(m => m.event === 'join_room');
    
    console.log(`   🏗️ room_created: ${roomCreatedMsgs.length} messages`);
    console.log(`   🔄 room_update: ${roomUpdateMsgs.length} messages`);
    console.log(`   🚪 player_removed: ${playerRemovedMsgs.length} messages`);
    console.log(`   ❌ error: ${errorMsgs.length} messages`);
    console.log(`   🔗 join_room: ${joinRoomMsgs.length} messages`);
    
    // 3. Error Analysis
    if (errorMsgs.length > 0) {
      console.log('\n❌ ERROR MESSAGES:');
      errorMsgs.forEach((msg, i) => {
        console.log(`${i + 1}. ${msg.player}: ${msg.data?.message || 'Unknown error'}`);
        console.log(`   Type: ${msg.data?.type || 'Unknown'}`);
      });
    }
    
    // 4. Room State Analysis
    console.log('\n🏠 ROOM STATE CHANGES:');
    this.evidence.roomStates.forEach((state, i) => {
      console.log(`${i + 1}. ${state.player}: ${state.roomCountText} (${state.actualRoomCards} cards)`);
    });
    
    // 5. Timing Analysis
    const botRemovalTime = this.evidence.timeline.find(e => e.event.includes('Bot removal'))?.timestamp;
    const joinAttemptTime = this.evidence.timeline.find(e => e.event.includes('attempting to join'))?.timestamp;
    
    if (botRemovalTime && joinAttemptTime) {
      const timeDiff = new Date(joinAttemptTime) - new Date(botRemovalTime);
      console.log(`\n⏱️ TIMING: ${timeDiff}ms between bot removal and join attempt`);
    }
    
    return {
      roomCreated: roomCreatedMsgs.length > 0,
      botRemovalAttempted: this.evidence.timeline.some(e => e.event.includes('Bot removal')),
      joinAttempted: joinRoomMsgs.length > 0,
      joinSuccessful: this.evidence.timeline.some(e => e.event.includes('Join successful')),
      errorCount: errorMsgs.length,
      errors: errorMsgs.map(m => m.data?.message)
    };
  }
}

async function investigateRoomJoinIssue() {
  console.log('🔍 ROOM JOIN INVESTIGATION');
  console.log('==========================');
  console.log('🎯 Testing scenario: Player 2 cannot join room after Player 1 removes bot');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000
  });
  
  const investigator = new RoomJoinInvestigator();
  
  try {
    // Step 1: Setup Player 1 (Creator)
    console.log('\n=== STEP 1: Setup Player 1 ===');
    const { context: creatorContext, page: creatorPage } = await investigator.setupPlayer(browser, 'Player1');
    
    // Step 2: Player 1 creates room
    console.log('\n=== STEP 2: Player 1 creates room ===');
    const roomId = await investigator.createRoom(creatorPage);
    await investigator.checkRoomState(creatorPage, 'Player1');
    
    // Step 3: Player 1 removes bot
    console.log('\n=== STEP 3: Player 1 removes bot ===');
    const botRemoved = await investigator.removeBotFromRoom(creatorPage);
    
    // Wait for state to propagate
    await creatorPage.waitForTimeout(3000);
    
    // Step 4: Setup Player 2 (Joiner)
    console.log('\n=== STEP 4: Setup Player 2 ===');
    const { context: joinerContext, page: joinerPage } = await investigator.setupPlayer(browser, 'Player2');
    await investigator.checkRoomState(joinerPage, 'Player2');
    
    // Step 5: Player 2 attempts to join room
    console.log('\n=== STEP 5: Player 2 attempts to join room ===');
    const joinResult = await investigator.attemptJoinRoom(joinerPage, roomId);
    
    investigator.evidence.joinAttempts.push(joinResult);
    
    // Wait for any async operations to complete
    await joinerPage.waitForTimeout(5000);
    
    // Final state check
    await investigator.checkRoomState(joinerPage, 'Player2-Final');
    
    // Step 6: Analyze evidence
    console.log('\n=== STEP 6: Analysis ===');
    const analysis = investigator.analyzeEvidence();
    
    console.log('\n🎯 ROOT CAUSE VERDICT:');
    if (!analysis.joinSuccessful && analysis.errorCount > 0) {
      console.log('✅ BUG CONFIRMED: Player 2 cannot join room after bot removal');
      console.log('📊 Evidence:');
      console.log(`   🏗️ Room was created: ${analysis.roomCreated}`);
      console.log(`   🤖 Bot removal attempted: ${analysis.botRemovalAttempted}`);
      console.log(`   🔗 Join attempted: ${analysis.joinAttempted}`);
      console.log(`   ❌ Join failed: ${!analysis.joinSuccessful}`);
      console.log(`   💥 Errors encountered: ${analysis.errorCount}`);
      if (analysis.errors.length > 0) {
        analysis.errors.forEach(err => console.log(`      - ${err}`));
      }
      console.log('\n🔧 LIKELY ROOT CAUSE: Room state synchronization issue');
      console.log('   The room removal operation may not be fully synchronized');
      console.log('   before the join validation runs, causing stale "room full" state.');
    } else if (analysis.joinSuccessful) {
      console.log('❓ SCENARIO NOT REPRODUCED: Player 2 was able to join');
      console.log('   This could indicate timing-dependent behavior');
    } else {
      console.log('📝 INCONCLUSIVE: Unable to determine root cause from this test');
    }
    
    // Keep browsers open for manual verification
    console.log('\n⏱️ Keeping browsers open for 30 seconds for manual verification...');
    await creatorPage.waitForTimeout(30000);
    
  } catch (error) {
    console.error('❌ Investigation failed:', error);
    investigator.logEvent('Investigation failed', { error: error.message });
  } finally {
    await browser.close();
  }
}

// Run the investigation
investigateRoomJoinIssue().catch(console.error);