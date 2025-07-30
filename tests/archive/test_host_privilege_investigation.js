const { chromium } = require('playwright');

/**
 * HOST PRIVILEGE INVESTIGATION TEST
 * 
 * Tests two specific issues after the setup sequence:
 * 1. When non-host player leaves room, host should keep remove buttons and host badge (currently disappear)
 * 2. When host removes a player, that player should be sent to lobby (currently may not work)
 * 
 * Setup Sequence:
 * Player 1 >> join lobby
 * Player 1 >> create room
 * Player 1 >> remove bot
 * Player 2 >> join lobby  
 * Player 2 >> join room
 */

async function investigateHostPrivileges() {
  console.log('🎯 HOST PRIVILEGE INVESTIGATION TEST');
  console.log('====================================');
  console.log('Testing host privilege persistence and player removal workflow');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 1500
  });
  
  try {
    const evidence = {
      websocketMessages: [],
      player1UIStates: [],
      player2UIStates: [],
      navigationEvents: [],
      issueFindings: {}
    };
    
    // Enhanced WebSocket message capture with detailed analysis
    const captureMessages = (page, playerName) => {
      page.on('websocket', ws => {
        ws.on('framereceived', data => {
          try {
            const parsed = JSON.parse(data.payload);
            
            // Capture all room-related messages
            if (['room_update', 'player_left', 'player_removed', 'room_joined'].includes(parsed.event)) {
              const message = {
                timestamp: new Date().toISOString(),
                receiver: playerName,
                event: parsed.event,
                data: parsed.data,
                raw: parsed
              };
              
              evidence.websocketMessages.push(message);
              
              console.log(`📥 ${playerName} received ${parsed.event}:`);
              if (parsed.event === 'room_update') {
                console.log(`   Host: "${parsed.data?.host_name}"`);
                console.log(`   Players: ${parsed.data?.players?.length || 0}`);
                console.log(`   Player list: ${parsed.data?.players?.map(p => p?.name || 'null').join(', ')}`);
              } else {
                console.log(`   Data: ${JSON.stringify(parsed.data).substring(0, 100)}...`);
              }
            }
          } catch (e) {}
        });
      });
    };
    
    // Enhanced UI state capture focusing on host elements
    const captureDetailedUIState = async (page, playerName, phase) => {
      try {
        console.log(`\n🔍 Capturing ${playerName} UI state: ${phase}`);
        
        await page.waitForTimeout(2000);
        
        // Take screenshot
        await page.screenshot({ 
          path: `host_privilege_${phase.toLowerCase().replace(/\s+/g, '_')}_${playerName.toLowerCase()}.png`,
          fullPage: true
        });
        
        // Capture current URL for navigation tracking
        const currentURL = page.url();
        
        // Detect page type
        const pageType = currentURL.includes('/room/') ? 'room' : 
                        currentURL.includes('/lobby') ? 'lobby' : 'other';
        
        // Get page content
        const allText = await page.locator('body').textContent().catch(() => '');
        
        // Count UI elements
        const removeButtons = await page.locator('button:has-text("Remove"), button:has-text("Kick")').all();
        const hostBadges = await page.locator('[class*="host"], .host-badge, :has-text("Host")').all();
        const roomElements = await page.locator('[class*="room"], [class*="game"]').all();
        const lobbyElements = await page.locator('[class*="lobby"]').all();
        
        // Analyze remove buttons
        const removeButtonTexts = [];
        for (const btn of removeButtons) {
          const text = await btn.textContent().catch(() => '');
          const isVisible = await btn.isVisible().catch(() => false);
          if (isVisible && text.trim()) {
            removeButtonTexts.push(text.trim());
          }
        }
        
        // Analyze host badges
        const hostBadgeTexts = [];
        for (const badge of hostBadges) {
          const text = await badge.textContent().catch(() => '');
          const isVisible = await badge.isVisible().catch(() => false);
          if (isVisible && text.includes('Host')) {
            hostBadgeTexts.push(text.trim());
          }
        }
        
        const uiState = {
          timestamp: new Date().toISOString(),
          player: playerName,
          phase: phase,
          url: currentURL,
          pageType: pageType,
          removeButtonCount: removeButtonTexts.length,
          removeButtonTexts: removeButtonTexts,
          hostBadgeCount: hostBadgeTexts.length,
          hostBadgeTexts: hostBadgeTexts,
          inRoom: pageType === 'room',
          inLobby: pageType === 'lobby',
          pageContainsHost: allText.includes('Host'),
          pageContainsRemove: allText.includes('Remove'),
          roomElementCount: roomElements.length,
          lobbyElementCount: lobbyElements.length
        };
        
        if (playerName === 'Player1') {
          evidence.player1UIStates.push(uiState);
        } else {
          evidence.player2UIStates.push(uiState);
        }
        
        console.log(`📊 ${playerName} State (${phase}):`);
        console.log(`   URL: ${currentURL}`);
        console.log(`   Page type: ${pageType}`);
        console.log(`   Remove buttons: ${uiState.removeButtonCount}`);
        console.log(`   Host badges: ${uiState.hostBadgeCount}`);
        console.log(`   In room: ${uiState.inRoom}, In lobby: ${uiState.inLobby}`);
        
        return uiState;
        
      } catch (error) {
        console.error(`Failed to capture UI state for ${playerName} at ${phase}:`, error);
        return null;
      }
    };
    
    // Navigation event tracking
    const trackNavigation = (page, playerName) => {
      page.on('framenavigated', (frame) => {
        if (frame === page.mainFrame()) {
          const navEvent = {
            timestamp: new Date().toISOString(),
            player: playerName,
            url: frame.url(),
            type: 'navigation'
          };
          evidence.navigationEvents.push(navEvent);
          console.log(`🧭 ${playerName} navigated to: ${frame.url()}`);
        }
      });
    };
    
    // === SETUP SEQUENCE ===
    console.log('\n=== SETUP SEQUENCE ===');
    
    // Step 1: Player 1 >> join lobby
    console.log('\n--- Step 1: Player 1 >> join lobby ---');
    const player1Context = await browser.newContext();
    const player1Page = await player1Context.newPage();
    captureMessages(player1Page, 'Player1');
    trackNavigation(player1Page, 'Player1');
    
    await player1Page.goto('http://localhost:5050');
    await player1Page.waitForLoadState('networkidle');
    
    await player1Page.locator('input[type="text"]').first().fill('TestHost');
    await player1Page.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await player1Page.waitForTimeout(3000);
    
    await captureDetailedUIState(player1Page, 'Player1', 'Setup_01_Lobby');
    
    // Step 2: Player 1 >> create room
    console.log('\n--- Step 2: Player 1 >> create room ---');
    const createBtn = await player1Page.locator('button').filter({ hasText: /create/i }).first();
    await createBtn.click();
    await player1Page.waitForTimeout(4000);
    
    await captureDetailedUIState(player1Page, 'Player1', 'Setup_02_Room_Created');
    
    // Step 3: Player 1 >> remove bot
    console.log('\n--- Step 3: Player 1 >> remove bot ---');
    const removeButtons = await player1Page.locator('button:has-text("Remove"), button:has-text("Kick")').all();
    if (removeButtons.length > 0) {
      console.log(`🗑️ Player 1 removing bot (${removeButtons.length} remove buttons available)...`);
      await removeButtons[0].click();
      await player1Page.waitForTimeout(4000);
    } else {
      console.log('❌ No remove buttons found for Player 1');
    }
    
    await captureDetailedUIState(player1Page, 'Player1', 'Setup_03_Bot_Removed');
    
    // Step 4: Player 2 >> join lobby
    console.log('\n--- Step 4: Player 2 >> join lobby ---');
    const player2Context = await browser.newContext();
    const player2Page = await player2Context.newPage();
    captureMessages(player2Page, 'Player2');
    trackNavigation(player2Page, 'Player2');
    
    await player2Page.goto('http://localhost:5050');
    await player2Page.waitForLoadState('networkidle');
    
    await player2Page.locator('input[type="text"]').first().fill('TestJoiner');
    await player2Page.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await player2Page.waitForTimeout(3000);
    
    await captureDetailedUIState(player2Page, 'Player2', 'Setup_04_Lobby');
    
    // Step 5: Player 2 >> join room
    console.log('\n--- Step 5: Player 2 >> join room ---');
    const roomCards = await player2Page.locator('.lp-roomCard').all();
    if (roomCards.length > 0) {
      console.log('🎯 Player 2 joining room...');
      await roomCards[0].click();
      await player2Page.waitForTimeout(5000);
      
      await captureDetailedUIState(player1Page, 'Player1', 'Setup_05_After_P2_Joined');
      await captureDetailedUIState(player2Page, 'Player2', 'Setup_05_In_Room');
    } else {
      console.log('❌ No room cards found for Player 2');
    }
    
    // === ISSUE 1 INVESTIGATION: Non-Host Player Leave ===
    console.log('\n=== ISSUE 1: NON-HOST PLAYER LEAVE INVESTIGATION ===');
    console.log('Testing: When non-host player leaves, host should keep remove buttons and host badge');
    
    // Capture Player 1 state BEFORE Player 2 leaves
    const beforeLeaveState = await captureDetailedUIState(player1Page, 'Player1', 'Issue1_Before_P2_Leaves');
    
    console.log('🚪 Player 2 leaving room (voluntary leave)...');
    
    // Player 2 leaves by closing browser/tab (simulating voluntary leave)
    await player2Page.close();
    await player2Context.close();
    
    // Wait for leave event to propagate
    await player1Page.waitForTimeout(5000);
    
    // Capture Player 1 state AFTER Player 2 leaves
    const afterLeaveState = await captureDetailedUIState(player1Page, 'Player1', 'Issue1_After_P2_Leaves');
    
    // Analyze Issue 1
    console.log('\n📊 ISSUE 1 ANALYSIS:');
    if (beforeLeaveState && afterLeaveState) {
      const removeButtonsLost = afterLeaveState.removeButtonCount < beforeLeaveState.removeButtonCount;
      const hostBadgesLost = afterLeaveState.hostBadgeCount < beforeLeaveState.hostBadgeCount;
      
      console.log(`Before Player 2 leave: ${beforeLeaveState.removeButtonCount} remove buttons, ${beforeLeaveState.hostBadgeCount} host badges`);
      console.log(`After Player 2 leave: ${afterLeaveState.removeButtonCount} remove buttons, ${afterLeaveState.hostBadgeCount} host badges`);
      console.log(`Remove buttons lost: ${removeButtonsLost ? '❌ YES (BUG CONFIRMED)' : '✅ NO'}`);
      console.log(`Host badges lost: ${hostBadgesLost ? '❌ YES (BUG CONFIRMED)' : '✅ NO'}`);
      
      evidence.issueFindings.issue1 = {
        removeButtonsLost,
        hostBadgesLost,
        beforeState: beforeLeaveState,
        afterState: afterLeaveState,
        bugConfirmed: removeButtonsLost || hostBadgesLost
      };
    }
    
    // === ISSUE 2 INVESTIGATION: Host Remove Player ===
    console.log('\n=== ISSUE 2: HOST REMOVE PLAYER INVESTIGATION ===');
    console.log('Testing: When host removes a player, that player should be sent to lobby');
    
    // Need Player 2 back in room for this test
    console.log('🔄 Setting up Player 2 again for remove test...');
    const player2Context2 = await browser.newContext();
    const player2Page2 = await player2Context2.newPage();
    captureMessages(player2Page2, 'Player2');
    trackNavigation(player2Page2, 'Player2');
    
    await player2Page2.goto('http://localhost:5050');
    await player2Page2.waitForLoadState('networkidle');
    
    await player2Page2.locator('input[type="text"]').first().fill('TestJoiner2');
    await player2Page2.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await player2Page2.waitForTimeout(3000);
    
    // Join room again
    const roomCards2 = await player2Page2.locator('.lp-roomCard').all();
    if (roomCards2.length > 0) {
      console.log('🎯 Player 2 rejoining room for remove test...');
      await roomCards2[0].click();
      await player2Page2.waitForTimeout(5000);
      
      await captureDetailedUIState(player1Page, 'Player1', 'Issue2_Before_Remove');
      await captureDetailedUIState(player2Page2, 'Player2', 'Issue2_Before_Remove');
      
      // Player 1 (host) removes Player 2 by clicking remove button
      console.log('🗑️ Player 1 (host) removing Player 2 via remove button...');
      
      const currentRemoveButtons = await player1Page.locator('button:has-text("Remove"), button:has-text("Kick")').all();
      if (currentRemoveButtons.length > 0) {
        // Find remove button for player (not bot)
        let playerRemoveButton = null;
        for (const btn of currentRemoveButtons) {
          const parentText = await btn.locator('..').textContent().catch(() => '');
          if (parentText.includes('TestJoiner') || !parentText.includes('Bot')) {
            playerRemoveButton = btn;
            break;
          }
        }
        
        if (playerRemoveButton) {
          await playerRemoveButton.click();
          console.log('✅ Clicked remove button for player');
        } else {
          // Fallback: click first remove button
          await currentRemoveButtons[0].click();
          console.log('⚠️ Clicked first available remove button');
        }
        
        // Wait for remove action to process
        await player1Page.waitForTimeout(5000);
        
        await captureDetailedUIState(player1Page, 'Player1', 'Issue2_After_Remove');
        await captureDetailedUIState(player2Page2, 'Player2', 'Issue2_After_Remove');
        
        // Check if Player 2 was redirected to lobby
        const player2FinalURL = player2Page2.url();
        const player2InLobby = player2FinalURL.includes('/lobby') || !player2FinalURL.includes('/room/');
        
        console.log(`\n📊 ISSUE 2 ANALYSIS:`);
        console.log(`Player 2 final URL: ${player2FinalURL}`);
        console.log(`Player 2 redirected to lobby: ${player2InLobby ? '✅ YES' : '❌ NO (BUG CONFIRMED)'}`);
        
        evidence.issueFindings.issue2 = {
          player2RedirectedToLobby: player2InLobby,
          finalURL: player2FinalURL,
          bugConfirmed: !player2InLobby
        };
      } else {
        console.log('❌ No remove buttons found for remove test');
        evidence.issueFindings.issue2 = {
          player2RedirectedToLobby: false,
          finalURL: 'N/A',
          bugConfirmed: true,
          error: 'No remove buttons available'
        };
      }
    }
    
    // === COMPREHENSIVE ANALYSIS ===
    console.log('\n=== COMPREHENSIVE ANALYSIS ===');
    
    // WebSocket message analysis
    console.log(`\n📡 WebSocket Message Summary:`);
    console.log(`   Total messages: ${evidence.websocketMessages.length}`);
    
    const messagesByEvent = {};
    evidence.websocketMessages.forEach(msg => {
      messagesByEvent[msg.event] = (messagesByEvent[msg.event] || 0) + 1;
    });
    
    Object.entries(messagesByEvent).forEach(([event, count]) => {
      console.log(`   ${event}: ${count} messages`);
    });
    
    // Issue summary
    console.log(`\n🎯 FINAL ISSUE SUMMARY:`);
    
    if (evidence.issueFindings.issue1) {
      console.log(`\n   ISSUE 1 - Host UI persistence after player leave:`);
      console.log(`   Status: ${evidence.issueFindings.issue1.bugConfirmed ? '❌ BUG CONFIRMED' : '✅ WORKING'}`);
      if (evidence.issueFindings.issue1.bugConfirmed) {
        console.log(`   - Remove buttons lost: ${evidence.issueFindings.issue1.removeButtonsLost}`);
        console.log(`   - Host badges lost: ${evidence.issueFindings.issue1.hostBadgesLost}`);
      }
    }
    
    if (evidence.issueFindings.issue2) {
      console.log(`\n   ISSUE 2 - Player removal workflow:`);
      console.log(`   Status: ${evidence.issueFindings.issue2.bugConfirmed ? '❌ BUG CONFIRMED' : '✅ WORKING'}`);
      if (evidence.issueFindings.issue2.bugConfirmed) {
        console.log(`   - Player not redirected to lobby: ${!evidence.issueFindings.issue2.player2RedirectedToLobby}`);
        console.log(`   - Final URL: ${evidence.issueFindings.issue2.finalURL}`);
      }
    }
    
    console.log('\n⏱️ Keeping browsers open for manual verification...');
    console.log('Screenshots saved for analysis:');
    console.log('   - Setup sequence: Setup_01_Lobby to Setup_05_In_Room');
    console.log('   - Issue 1: Issue1_Before_P2_Leaves, Issue1_After_P2_Leaves');  
    console.log('   - Issue 2: Issue2_Before_Remove, Issue2_After_Remove');
    
    await player1Page.waitForTimeout(30000);
    
    return evidence;
    
  } catch (error) {
    console.error('❌ Host privilege investigation failed:', error);
  } finally {
    await browser.close();
  }
}

investigateHostPrivileges().catch(console.error);