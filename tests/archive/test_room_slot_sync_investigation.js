const { chromium } = require('playwright');

/**
 * ROOM SLOT SYNCHRONIZATION INVESTIGATION
 * 
 * ISSUES TO PROVE:
 * 1. When player joins room, other clients should see player in first available slot
 * 2. Host sees all slot status turn to "waiting" (WRONG)
 * 3. When non-host leaves, remove button and host badge disappear (WRONG)
 * 
 * This test will capture the exact WebSocket messages and UI state changes
 * to prove the root cause of these synchronization issues.
 */

class RoomSlotSyncInvestigator {
  constructor() {
    this.evidence = {
      roomUpdates: [],
      uiStates: [],
      playerJoins: [],
      playerLeaves: [],
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
          
          if (parsed.event === 'room_update') {
            this.evidence.roomUpdates.push({
              timestamp: new Date().toISOString(),
              receiver: playerName,
              players: parsed.data?.players || [],
              host_name: parsed.data?.host_name,
              started: parsed.data?.started
            });
            
            console.log(`📥 ${playerName} room_update:`, {
              players: parsed.data?.players?.map(p => p ? `${p.name}(${p.is_bot ? 'bot' : 'human'})` : 'empty'),
              host: parsed.data?.host_name
            });
          }
          
          if (parsed.event === 'room_joined') {
            this.evidence.playerJoins.push({
              timestamp: new Date().toISOString(),
              joiner: parsed.data?.player_name || 'unknown',
              success: parsed.data?.success,
              seat_position: parsed.data?.seat_position
            });
            
            console.log(`🔗 ${playerName} saw room_joined:`, parsed.data);
          }
        } catch (e) {
          // Ignore parse errors
        }
      });
    });
  }

  async captureUIState(page, playerName, step) {
    try {
      await page.waitForTimeout(1000); // Let UI settle
      
      // Capture player slots
      const slots = [];
      const slotElements = await page.locator('[class*="slot"], [class*="player"], .seat').all();
      
      for (let i = 0; i < Math.min(slotElements.length, 4); i++) {
        try {
          const slotElement = slotElements[i];
          const slotText = await slotElement.textContent();
          const isVisible = await slotElement.isVisible();
          
          // Try to find player name, bot indicator, and status
          const playerName = slotText.match(/([A-Za-z0-9]+)(?:\s|$)/)?.[1] || '';
          const isBot = slotText.toLowerCase().includes('bot');
          const isEmpty = slotText.toLowerCase().includes('empty') || playerName === '';
          const isWaiting = slotText.toLowerCase().includes('waiting');
          
          slots.push({
            index: i,
            text: slotText,
            playerName,
            isBot,
            isEmpty,
            isWaiting,
            isVisible
          });
        } catch (e) {
          slots.push({
            index: i,
            text: 'ERROR',
            error: e.message
          });
        }
      }
      
      // Capture host badge
      let hostBadge = null;
      try {
        const hostElements = await page.locator('[class*="host"], .badge').all();
        if (hostElements.length > 0) {
          const hostText = await hostElements[0].textContent();
          const hostVisible = await hostElements[0].isVisible();
          hostBadge = { text: hostText, visible: hostVisible };
        }
      } catch (e) {
        hostBadge = { error: e.message };
      }
      
      // Capture remove buttons
      const removeButtons = [];
      try {
        const removeBtns = await page.locator('button:has-text("Remove"), button:has-text("Kick")').all();
        for (let i = 0; i < removeBtns.length; i++) {
          const btnText = await removeBtns[i].textContent();
          const btnVisible = await removeBtns[i].isVisible();
          const btnEnabled = await removeBtns[i].isEnabled();
          removeButtons.push({ text: btnText, visible: btnVisible, enabled: btnEnabled });
        }
      } catch (e) {
        removeButtons.push({ error: e.message });
      }
      
      const uiState = {
        timestamp: new Date().toISOString(),
        player: playerName,
        step,
        slots,
        hostBadge,
        removeButtons,
        totalSlots: slots.length,
        totalRemoveButtons: removeButtons.length
      };
      
      this.evidence.uiStates.push(uiState);
      
      console.log(`🖥️ UI State for ${playerName} at ${step}:`);
      console.log(`   Slots: ${slots.map(s => `${s.index}:${s.playerName || 'empty'}${s.isWaiting ? '(waiting)' : ''}`).join(', ')}`);
      console.log(`   Host badge: ${hostBadge?.visible ? 'visible' : 'hidden'}`);
      console.log(`   Remove buttons: ${removeButtons.length} (${removeButtons.filter(b => b.visible).length} visible)`);
      
      return uiState;
    } catch (error) {
      console.log(`❌ Failed to capture UI state for ${playerName}:`, error.message);
      return null;
    }
  }

  async setupPlayer(browser, playerName) {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    await this.captureWebSocketMessages(page, playerName);
    
    this.logEvent(`Setup ${playerName}`);
    
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

  analyzeEvidence() {
    console.log('\n🔍 SLOT SYNCHRONIZATION ANALYSIS');
    console.log('==================================');
    
    // 1. Timeline Analysis
    console.log('\n📅 EVENT TIMELINE:');
    this.evidence.timeline.forEach((entry, i) => {
      console.log(`${i + 1}. ${entry.timestamp}: ${entry.event}`);
    });
    
    // 2. Room Update Analysis
    console.log('\n📡 ROOM UPDATE ANALYSIS:');
    console.log(`Total room_update messages: ${this.evidence.roomUpdates.length}`);
    
    this.evidence.roomUpdates.forEach((update, i) => {
      console.log(`${i + 1}. ${update.receiver}: ${update.players.length} players, host: ${update.host_name}`);
      update.players.forEach((player, j) => {
        if (player) {
          console.log(`   Slot ${j}: ${player.name} (${player.is_bot ? 'bot' : 'human'})`);
        } else {
          console.log(`   Slot ${j}: empty`);
        }
      });
    });
    
    // 3. UI State Comparison
    console.log('\n🖥️ UI STATE COMPARISON:');
    
    const uiStatesByStep = {};
    this.evidence.uiStates.forEach(state => {
      if (!uiStatesByStep[state.step]) {
        uiStatesByStep[state.step] = [];
      }
      uiStatesByStep[state.step].push(state);
    });
    
    Object.keys(uiStatesByStep).forEach(step => {
      console.log(`\n--- ${step} ---`);
      uiStatesByStep[step].forEach(state => {
        console.log(`${state.player}:`);
        state.slots.forEach(slot => {
          if (!slot.error) {
            console.log(`  Slot ${slot.index}: ${slot.playerName || 'empty'}${slot.isWaiting ? ' (waiting)' : ''}${slot.isBot ? ' (bot)' : ''}`);
          }
        });
        console.log(`  Host badge: ${state.hostBadge?.visible ? 'visible' : 'hidden'}`);
        console.log(`  Remove buttons: ${state.removeButtons.filter(b => b.visible).length}/${state.removeButtons.length}`);
      });
    });
    
    // 4. Issue Detection
    console.log('\n🚨 ISSUE DETECTION:');
    
    // Check for "waiting" status issue
    const waitingIssues = this.evidence.uiStates.filter(state => 
      state.slots.some(slot => slot.isWaiting)
    );
    
    if (waitingIssues.length > 0) {
      console.log('❌ CONFIRMED: "Waiting" status issue detected');
      waitingIssues.forEach(issue => {
        const waitingSlots = issue.slots.filter(s => s.isWaiting);
        console.log(`   ${issue.player} at ${issue.step}: ${waitingSlots.length} slots showing "waiting"`);
      });
    }
    
    // Check for host badge disappearing
    const hostBadgeIssues = this.evidence.uiStates.filter(state => 
      state.hostBadge && !state.hostBadge.visible && state.step.includes('after')
    );
    
    if (hostBadgeIssues.length > 0) {
      console.log('❌ CONFIRMED: Host badge disappearing issue detected');
      hostBadgeIssues.forEach(issue => {
        console.log(`   ${issue.player} at ${issue.step}: host badge disappeared`);
      });
    }
    
    // Check for remove button disappearing
    const removeButtonIssues = this.evidence.uiStates.filter(state => 
      state.step.includes('after') && state.removeButtons.filter(b => b.visible).length === 0
    );
    
    if (removeButtonIssues.length > 0) {
      console.log('❌ CONFIRMED: Remove button disappearing issue detected');
      removeButtonIssues.forEach(issue => {
        console.log(`   ${issue.player} at ${issue.step}: all remove buttons disappeared`);
      });
    }
    
    return {
      hasWaitingIssue: waitingIssues.length > 0,
      hasHostBadgeIssue: hostBadgeIssues.length > 0,
      hasRemoveButtonIssue: removeButtonIssues.length > 0,
      totalRoomUpdates: this.evidence.roomUpdates.length,
      totalPlayerJoins: this.evidence.playerJoins.length
    };
  }
}

async function investigateSlotSync() {
  console.log('🔍 ROOM SLOT SYNCHRONIZATION INVESTIGATION');
  console.log('==========================================');
  console.log('🎯 Issues to prove:');
  console.log('   1. Other clients should see new player in first available slot');
  console.log('   2. Host sees all slots turn to "waiting" (WRONG)');
  console.log('   3. Remove buttons and host badge disappear when non-host leaves (WRONG)');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 1500
  });
  
  const investigator = new RoomSlotSyncInvestigator();
  
  try {
    // === STEP 1: Setup Host ===
    console.log('\n=== STEP 1: Setup Host ===');
    const { context: hostContext, page: hostPage } = await investigator.setupPlayer(browser, 'Host');
    
    // Create room
    const createBtn = await hostPage.locator('button').filter({ hasText: /create/i }).first();
    await createBtn.click();
    await hostPage.waitForTimeout(5000);
    
    investigator.logEvent('Host created room');
    await investigator.captureUIState(hostPage, 'Host', 'after_room_creation');
    
    // === STEP 2: Setup Observer (to watch slot changes) ===
    console.log('\n=== STEP 2: Setup Observer ===');
    const { context: observerContext, page: observerPage } = await investigator.setupPlayer(browser, 'Observer');
    await investigator.captureUIState(observerPage, 'Observer', 'in_lobby');
    
    // === STEP 3: Observer joins room ===
    console.log('\n=== STEP 3: Observer joins room ===');
    const roomCards = await observerPage.locator('.lp-roomCard').all();
    if (roomCards.length > 0) {
      await roomCards[0].click();
      await observerPage.waitForTimeout(5000);
      investigator.logEvent('Observer joined room');
      
      // Capture UI state for both players after join
      await investigator.captureUIState(hostPage, 'Host', 'after_observer_joined');
      await investigator.captureUIState(observerPage, 'Observer', 'after_joining_room');
    }
    
    // === STEP 4: Setup Third Player ===
    console.log('\n=== STEP 4: Setup Third Player ===');
    const { context: player3Context, page: player3Page } = await investigator.setupPlayer(browser, 'Player3');
    
    // Player3 joins room
    const roomCards3 = await player3Page.locator('.lp-roomCard').all();
    if (roomCards3.length > 0) {
      await roomCards3[0].click();
      await player3Page.waitForTimeout(5000);
      investigator.logEvent('Player3 joined room');
      
      // Capture UI state for all players after third player joins
      await investigator.captureUIState(hostPage, 'Host', 'after_player3_joined');
      await investigator.captureUIState(observerPage, 'Observer', 'after_player3_joined');
      await investigator.captureUIState(player3Page, 'Player3', 'after_joining_room');
    }
    
    // === STEP 5: Non-host (Observer) leaves ===
    console.log('\n=== STEP 5: Observer leaves room ===');
    
    // Observer leaves (try to find leave button or navigate away)
    try {
      const leaveBtn = await observerPage.locator('button:has-text("Leave"), button:has-text("Exit")').first();
      await leaveBtn.click({ timeout: 3000 });
    } catch (e) {
      // If no leave button, navigate to lobby
      await observerPage.goto('http://localhost:5050/lobby');
    }
    
    await observerPage.waitForTimeout(3000);
    investigator.logEvent('Observer left room');
    
    // Capture UI state after observer leaves - THIS IS WHERE BUGS SHOULD APPEAR
    await investigator.captureUIState(hostPage, 'Host', 'after_observer_left');
    await investigator.captureUIState(player3Page, 'Player3', 'after_observer_left');
    
    // === STEP 6: Analysis ===
    console.log('\n=== STEP 6: Evidence Analysis ===');
    const analysis = investigator.analyzeEvidence();
    
    console.log('\n🏆 INVESTIGATION RESULTS:');
    if (analysis.hasWaitingIssue) {
      console.log('❌ BUG CONFIRMED: Slots showing "waiting" status incorrectly');
    }
    if (analysis.hasHostBadgeIssue) {
      console.log('❌ BUG CONFIRMED: Host badge disappears when non-host leaves');
    }
    if (analysis.hasRemoveButtonIssue) {
      console.log('❌ BUG CONFIRMED: Remove buttons disappear when non-host leaves');
    }
    
    if (!analysis.hasWaitingIssue && !analysis.hasHostBadgeIssue && !analysis.hasRemoveButtonIssue) {
      console.log('✅ No issues detected - slot synchronization working correctly');
    }
    
    console.log('\n📊 STATISTICS:');
    console.log(`   Room updates received: ${analysis.totalRoomUpdates}`);
    console.log(`   Player joins detected: ${analysis.totalPlayerJoins}`);
    console.log(`   UI states captured: ${investigator.evidence.uiStates.length}`);
    
    // Keep browsers open for manual verification
    console.log('\n⏱️ Keeping browsers open for 30 seconds for manual verification...');
    await hostPage.waitForTimeout(30000);
    
  } catch (error) {
    console.error('❌ Investigation failed:', error);
  } finally {
    await browser.close();
  }
}

investigateSlotSync().catch(console.error);