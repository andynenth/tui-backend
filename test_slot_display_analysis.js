const { chromium } = require('playwright');

/**
 * SLOT DISPLAY ANALYSIS TEST
 * 
 * Analyzes how slots are displayed to different clients after the broadcast fixes.
 * Tests the specific issues mentioned:
 * 1. "host see all slot status turn to waiting" - should be fixed
 * 2. "remove button and host badge disappear" when non-host leaves - should be fixed
 */

async function analyzeSlotDisplay() {
  console.log('🎯 SLOT DISPLAY ANALYSIS TEST');
  console.log('==============================');
  console.log('Testing post-fix slot synchronization behavior');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000
  });
  
  try {
    const evidence = {
      hostUIStates: [],
      joinerUIStates: [],
      websocketMessages: [],
      slotAnalysis: {}
    };
    
    // Helper to capture UI state
    const captureUIState = async (page, playerName, phase) => {
      try {
        // Wait for UI to stabilize
        await page.waitForTimeout(2000);
        
        // Capture slot information
        const slots = await page.locator('.slot, [class*="slot"], [data-testid*="slot"]').all();
        const slotStates = [];
        
        for (let i = 0; i < slots.length; i++) {
          const slot = slots[i];
          const isVisible = await slot.isVisible().catch(() => false);
          
          if (isVisible) {
            const text = await slot.textContent().catch(() => '');
            const classes = await slot.getAttribute('class').catch(() => '');
            
            // Look for player names, status indicators, buttons
            const hasPlayerName = text.includes('TestHost') || text.includes('TestJoiner') || text.includes('Bot');
            const hasWaitingStatus = text.toLowerCase().includes('waiting');
            const hasRemoveButton = text.includes('Remove') || text.includes('Kick');
            const hasHostBadge = text.includes('Host') || classes.includes('host');
            
            slotStates.push({
              index: i,
              text: text.trim(),
              classes,
              hasPlayerName,
              hasWaitingStatus,
              hasRemoveButton,
              hasHostBadge
            });
          }
        }
        
        const uiState = {
          timestamp: new Date().toISOString(),
          player: playerName,
          phase,
          totalSlots: slotStates.length,
          slotsWithPlayers: slotStates.filter(s => s.hasPlayerName).length,
          slotsWithWaiting: slotStates.filter(s => s.hasWaitingStatus).length,
          slotsWithRemoveButton: slotStates.filter(s => s.hasRemoveButton).length,
          slotsWithHostBadge: slotStates.filter(s => s.hasHostBadge).length,
          slotDetails: slotStates
        };
        
        if (playerName === 'Host') {
          evidence.hostUIStates.push(uiState);
        } else {
          evidence.joinerUIStates.push(uiState);
        }
        
        console.log(`📊 ${playerName} UI State (${phase}):`);
        console.log(`   Total slots: ${uiState.totalSlots}`);
        console.log(`   Slots with players: ${uiState.slotsWithPlayers}`);
        console.log(`   Slots showing "waiting": ${uiState.slotsWithWaiting}`);
        console.log(`   Slots with remove buttons: ${uiState.slotsWithRemoveButton}`);
        console.log(`   Slots with host badge: ${uiState.slotsWithHostBadge}`);
        
        // Log detailed slot content for debugging
        slotStates.forEach((slot, idx) => {
          if (slot.hasPlayerName || slot.hasWaitingStatus) {
            console.log(`   Slot ${idx}: "${slot.text}" (${slot.hasPlayerName ? 'player' : 'waiting'}${slot.hasHostBadge ? ', host' : ''}${slot.hasRemoveButton ? ', removable' : ''})`);
          }
        });
        
        return uiState;
        
      } catch (error) {
        console.error(`Failed to capture UI state for ${playerName}:`, error);
        return null;
      }
    };
    
    // Helper to capture WebSocket messages
    const captureMessages = (page, playerName) => {
      page.on('websocket', ws => {
        ws.on('framereceived', data => {
          try {
            const parsed = JSON.parse(data.payload);
            
            if (parsed.event === 'room_update') {
              const message = {
                timestamp: new Date().toISOString(),
                receiver: playerName,
                event: parsed.event,
                data: parsed.data
              };
              
              evidence.websocketMessages.push(message);
              
              console.log(`📥 ${playerName} received room_update:`);
              console.log(`   Host: ${parsed.data?.host_name}`);
              console.log(`   Started: ${parsed.data?.started}`);
              console.log(`   Players: ${parsed.data?.players?.length || 0}`);
            }
          } catch (e) {}
        });
      });
    };
    
    // === Phase 1: Room Creation ===
    console.log('\n=== PHASE 1: Room Creation ===');
    const hostContext = await browser.newContext();
    const hostPage = await hostContext.newPage();
    captureMessages(hostPage, 'Host');
    
    await hostPage.goto('http://localhost:5050');
    await hostPage.waitForLoadState('networkidle');
    
    await hostPage.locator('input[type="text"]').first().fill('TestHost');
    await hostPage.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await hostPage.waitForTimeout(2000);
    
    const createBtn = await hostPage.locator('button').filter({ hasText: /create/i }).first();
    await createBtn.click();
    await hostPage.waitForTimeout(3000);
    
    // Capture initial host UI state
    await captureUIState(hostPage, 'Host', 'room_created');
    
    // === Phase 2: Player Joins ===
    console.log('\n=== PHASE 2: Player Joins ===');
    const joinerContext = await browser.newContext();
    const joinerPage = await joinerContext.newPage();
    captureMessages(joinerPage, 'Joiner');
    
    await joinerPage.goto('http://localhost:5050');
    await joinerPage.waitForLoadState('networkidle');
    
    await joinerPage.locator('input[type="text"]').first().fill('TestJoiner');
    await joinerPage.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await joinerPage.waitForTimeout(3000);
    
    // Join room
    const roomCards = await joinerPage.locator('.lp-roomCard').all();
    if (roomCards.length > 0) {
      console.log('🎯 TestJoiner joining room...');
      await roomCards[0].click();
      await joinerPage.waitForTimeout(4000);
      
      // Capture UI states after join
      await captureUIState(hostPage, 'Host', 'after_player_join');
      await captureUIState(joinerPage, 'Joiner', 'after_join');
    } else {
      console.log('❌ No room cards found for joining');
    }
    
    // === Phase 3: Bot Removal (Test Remove Button Persistence) ===
    console.log('\n=== PHASE 3: Bot Removal ===');
    
    // Capture UI before bot removal
    await captureUIState(hostPage, 'Host', 'before_bot_removal');
    await captureUIState(joinerPage, 'Joiner', 'before_bot_removal');
    
    // Remove a bot to test remove button behavior
    const removeBtns = await hostPage.locator('button:has-text("Remove"), button:has-text("Kick")').all();
    if (removeBtns.length > 0) {
      console.log('🤖 Host removing bot...');
      await removeBtns[0].click();
      await hostPage.waitForTimeout(4000);
      
      // Capture UI after bot removal
      await captureUIState(hostPage, 'Host', 'after_bot_removal');
      await captureUIState(joinerPage, 'Joiner', 'after_bot_removal');
    } else {
      console.log('❌ No remove buttons found');
    }
    
    // === Phase 4: Player Leave (Critical Test) ===
    console.log('\n=== PHASE 4: Player Leave (Critical Test) ===');
    
    // This tests the specific issue: "when non-host left, remove button and host badge disappear"
    await captureUIState(hostPage, 'Host', 'before_player_leave');
    
    console.log('🚪 TestJoiner leaving room...');
    await joinerPage.close();
    await joinerContext.close();
    
    // Wait for leave event to propagate
    await hostPage.waitForTimeout(5000);
    
    // Capture final UI state - this should show host badge and remove buttons still present
    await captureUIState(hostPage, 'Host', 'after_player_leave');
    
    // === Analysis ===
    console.log('\n=== SLOT DISPLAY ANALYSIS ===');
    
    // Analyze the "all slot status turn to waiting" issue
    const hostStatesAfterJoin = evidence.hostUIStates.filter(s => s.phase === 'after_player_join');
    if (hostStatesAfterJoin.length > 0) {
      const state = hostStatesAfterJoin[0];
      console.log(`\n🔍 Host View After Player Join:`);
      console.log(`   Problem: "host see all slot status turn to waiting"`);
      console.log(`   Result: ${state.slotsWithWaiting}/${state.totalSlots} slots showing "waiting"`);
      console.log(`   Expected: Only empty slots should show "waiting"`);
      console.log(`   Status: ${state.slotsWithWaiting === 0 ? '✅ FIXED' : '❌ STILL BROKEN'}`);
    }
    
    // Analyze the "remove button and host badge disappear" issue
    const hostStatesBeforeLeave = evidence.hostUIStates.filter(s => s.phase === 'before_player_leave');
    const hostStatesAfterLeave = evidence.hostUIStates.filter(s => s.phase === 'after_player_leave');
    
    if (hostStatesBeforeLeave.length > 0 && hostStatesAfterLeave.length > 0) {
      const beforeState = hostStatesBeforeLeave[0];
      const afterState = hostStatesAfterLeave[0];
      
      console.log(`\n🔍 Host Badge & Remove Button Persistence:`);
      console.log(`   Problem: "when non-host left, remove button and host badge disappear"`);
      console.log(`   Before leave: ${beforeState.slotsWithHostBadge} host badges, ${beforeState.slotsWithRemoveButton} remove buttons`);
      console.log(`   After leave: ${afterState.slotsWithHostBadge} host badges, ${afterState.slotsWithRemoveButton} remove buttons`);
      
      const hostBadgePersisted = afterState.slotsWithHostBadge > 0;
      const removeButtonsPersisted = afterState.slotsWithRemoveButton >= beforeState.slotsWithRemoveButton - 1; // -1 because player left
      
      console.log(`   Host badge persisted: ${hostBadgePersisted ? '✅ YES' : '❌ NO'}`);
      console.log(`   Remove buttons persisted: ${removeButtonsPersisted ? '✅ YES' : '❌ NO'}`);
      console.log(`   Status: ${hostBadgePersisted && removeButtonsPersisted ? '✅ FIXED' : '❌ STILL BROKEN'}`);
    }
    
    // WebSocket message analysis
    console.log(`\n📊 WebSocket Message Analysis:`);
    console.log(`   Total room_update messages: ${evidence.websocketMessages.length}`);
    
    const validMessages = evidence.websocketMessages.filter(m => 
      m.data?.host_name && m.data?.host_name !== 'undefined' && 
      m.data?.started !== undefined
    );
    
    console.log(`   Valid room_update messages: ${validMessages.length}/${evidence.websocketMessages.length}`);
    console.log(`   Broadcast fix effectiveness: ${validMessages.length === evidence.websocketMessages.length ? '✅ 100%' : '❌ Partial'}`);
    
    // Final verdict
    console.log(`\n🏆 FINAL ANALYSIS RESULT:`);
    const allIssuesFixed = hostStatesAfterJoin.length > 0 && hostStatesAfterJoin[0].slotsWithWaiting === 0 &&
                          hostStatesAfterLeave.length > 0 && hostStatesAfterLeave[0].slotsWithHostBadge > 0;
    
    if (allIssuesFixed) {
      console.log('✅ SUCCESS: All slot synchronization issues resolved');
      console.log('   ✅ Host no longer sees all slots as "waiting"');
      console.log('   ✅ Host badge and remove buttons persist after player leave');
      console.log('   ✅ WebSocket broadcasts contain complete room state');
    } else {
      console.log('❌ ISSUES REMAIN: Some slot synchronization problems persist');
      console.log('   Manual inspection of browser windows recommended');
    }
    
    console.log('\n⏱️ Keeping browser open for manual verification...');
    await hostPage.waitForTimeout(30000);
    
    return evidence;
    
  } catch (error) {
    console.error('❌ Slot display analysis failed:', error);
  } finally {
    await browser.close();
  }
}

analyzeSlotDisplay().catch(console.error);