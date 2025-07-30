const { chromium } = require('playwright');

/**
 * EXACT SEQUENCE INVESTIGATION TEST
 * 
 * Tests the precise sequence reported by user:
 * 1. Player 1 >> join lobby
 * 2. Player 1 >> create room  
 * 3. Player 1 >> remove bot
 * 4. Player 2 >> join lobby
 * 5. Player 2 >> join room
 * 6. Player 1 >> should keep remove buttons and host badge (currently disappearing)
 */

async function testExactSequence() {
  console.log('🎯 EXACT SEQUENCE INVESTIGATION TEST');
  console.log('====================================');
  console.log('Testing the precise user-reported sequence');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 1500
  });
  
  try {
    const evidence = {
      websocketMessages: [],
      hostUIStates: [],
      sequenceSteps: [],
      criticalFindings: {}
    };
    
    // Enhanced UI state capture focusing on remove buttons and host badges
    const captureDetailedUIState = async (page, playerName, step) => {
      try {
        console.log(`\n🔍 Capturing ${playerName} UI state at step: ${step}`);
        
        await page.waitForTimeout(2000);
        
        // Take screenshot for evidence
        await page.screenshot({ 
          path: `sequence_${step.toLowerCase().replace(/\s+/g, '_')}_${playerName.toLowerCase()}.png`,
          fullPage: true
        });
        
        // Capture all page text
        const allText = await page.locator('body').textContent().catch(() => '');
        
        // Look for specific UI elements
        const removeButtons = await page.locator('button:has-text("Remove"), button:has-text("Kick")').all();
        const hostBadges = await page.locator('[class*="host"], .host-badge, :has-text("Host")').all();
        const playerElements = await page.locator('[class*="player"]').all();
        
        // Count and analyze remove buttons
        const removeButtonTexts = [];
        for (const btn of removeButtons) {
          const text = await btn.textContent().catch(() => '');
          const isVisible = await btn.isVisible().catch(() => false);
          if (isVisible && text.trim()) {
            removeButtonTexts.push(text.trim());
          }
        }
        
        // Count and analyze host badges  
        const hostBadgeTexts = [];
        for (const badge of hostBadges) {
          const text = await badge.textContent().catch(() => '');
          const isVisible = await badge.isVisible().catch(() => false);
          if (isVisible && text.includes('Host')) {
            hostBadgeTexts.push(text.trim());
          }
        }
        
        // Analyze player list content
        const playerListContent = [];
        for (const elem of playerElements) {
          const text = await elem.textContent().catch(() => '');
          const isVisible = await elem.isVisible().catch(() => false);
          if (isVisible && text.trim() && text.length < 200) { // Avoid huge text blocks
            playerListContent.push(text.trim());
          }
        }
        
        const uiState = {
          timestamp: new Date().toISOString(),
          player: playerName,
          step: step,
          removeButtonCount: removeButtonTexts.length,
          removeButtonTexts: removeButtonTexts,
          hostBadgeCount: hostBadgeTexts.length,
          hostBadgeTexts: hostBadgeTexts,
          playerElements: playerListContent.slice(0, 10), // Limit to first 10
          pageContainsHost: allText.includes('Host'),
          pageContainsRemove: allText.includes('Remove'),
          pageContainsTestHost: allText.includes('TestHost'),
          pageContainsBot: allText.includes('Bot'),
          fullPageText: allText.substring(0, 500) // First 500 chars for analysis
        };
        
        evidence.hostUIStates.push(uiState);
        
        console.log(`📊 ${playerName} UI Analysis (${step}):`);
        console.log(`   Remove buttons: ${uiState.removeButtonCount} (${uiState.removeButtonTexts.join(', ')})`);
        console.log(`   Host badges: ${uiState.hostBadgeCount} (${uiState.hostBadgeTexts.join(', ')})`);
        console.log(`   Page contains "Host": ${uiState.pageContainsHost}`);
        console.log(`   Page contains "Remove": ${uiState.pageContainsRemove}`);
        console.log(`   Player elements: ${uiState.playerElements.length}`);
        
        return uiState;
        
      } catch (error) {
        console.error(`Failed to capture UI state for ${playerName} at ${step}:`, error);
        return null;
      }
    };
    
    // WebSocket message capture with detailed analysis
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
                data: parsed.data,
                host_name: parsed.data?.host_name,
                started: parsed.data?.started,
                players: parsed.data?.players || [],
                playerCount: parsed.data?.players?.length || 0
              };
              
              evidence.websocketMessages.push(message);
              
              console.log(`📥 ${playerName} room_update:`);
              console.log(`   Host: "${message.host_name}"`);
              console.log(`   Players: ${message.playerCount}`);
              console.log(`   Started: ${message.started}`);
              if (message.players.length > 0) {
                console.log(`   Player list: ${message.players.map(p => p?.name || 'null').join(', ')}`);
              }
            }
          } catch (e) {}
        });
      });
    };
    
    // === STEP 1: Player 1 >> join lobby ===
    console.log('\n=== STEP 1: Player 1 >> join lobby ===');
    evidence.sequenceSteps.push({ step: 1, action: 'Player 1 join lobby', timestamp: new Date().toISOString() });
    
    const player1Context = await browser.newContext();
    const player1Page = await player1Context.newPage();
    captureMessages(player1Page, 'Player1');
    
    await player1Page.goto('http://localhost:5050');
    await player1Page.waitForLoadState('networkidle');
    
    await player1Page.locator('input[type="text"]').first().fill('TestHost');
    await player1Page.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await player1Page.waitForTimeout(3000);
    
    await captureDetailedUIState(player1Page, 'Player1', 'After joining lobby');
    
    // === STEP 2: Player 1 >> create room ===
    console.log('\n=== STEP 2: Player 1 >> create room ===');
    evidence.sequenceSteps.push({ step: 2, action: 'Player 1 create room', timestamp: new Date().toISOString() });
    
    const createBtn = await player1Page.locator('button').filter({ hasText: /create/i }).first();
    await createBtn.click();
    await player1Page.waitForTimeout(4000);
    
    await captureDetailedUIState(player1Page, 'Player1', 'After creating room');
    
    // === STEP 3: Player 1 >> remove bot ===
    console.log('\n=== STEP 3: Player 1 >> remove bot ===');
    evidence.sequenceSteps.push({ step: 3, action: 'Player 1 remove bot', timestamp: new Date().toISOString() });
    
    // Capture state BEFORE removing bot
    const beforeRemoval = await captureDetailedUIState(player1Page, 'Player1', 'Before bot removal');
    
    const removeButtons = await player1Page.locator('button:has-text("Remove"), button:has-text("Kick")').all();
    if (removeButtons.length > 0) {
      console.log(`🗑️ Player 1 removing bot (${removeButtons.length} remove buttons available)...`);
      await removeButtons[0].click();
      await player1Page.waitForTimeout(4000);
    } else {
      console.log('❌ No remove buttons found for Player 1');
    }
    
    // Capture state AFTER removing bot
    const afterRemoval = await captureDetailedUIState(player1Page, 'Player1', 'After bot removal');
    
    // === STEP 4: Player 2 >> join lobby ===
    console.log('\n=== STEP 4: Player 2 >> join lobby ===');
    evidence.sequenceSteps.push({ step: 4, action: 'Player 2 join lobby', timestamp: new Date().toISOString() });
    
    const player2Context = await browser.newContext();
    const player2Page = await player2Context.newPage();
    captureMessages(player2Page, 'Player2');
    
    await player2Page.goto('http://localhost:5050');
    await player2Page.waitForLoadState('networkidle');
    
    await player2Page.locator('input[type="text"]').first().fill('TestJoiner');
    await player2Page.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await player2Page.waitForTimeout(3000);
    
    await captureDetailedUIState(player2Page, 'Player2', 'After joining lobby');
    
    // === STEP 5: Player 2 >> join room ===
    console.log('\n=== STEP 5: Player 2 >> join room ===');
    evidence.sequenceSteps.push({ step: 5, action: 'Player 2 join room', timestamp: new Date().toISOString() });
    
    // Capture Player 1 state BEFORE Player 2 joins
    const beforePlayer2JoinState = await captureDetailedUIState(player1Page, 'Player1', 'Before Player 2 joins');
    
    const roomCards = await player2Page.locator('.lp-roomCard').all();
    if (roomCards.length > 0) {
      console.log('🎯 Player 2 joining room...');
      await roomCards[0].click();
      await player2Page.waitForTimeout(5000);
      
      await captureDetailedUIState(player2Page, 'Player2', 'After joining room');
    } else {
      console.log('❌ No room cards found for Player 2');
    }
    
    // === STEP 6: Critical Check - Player 1 UI State ===
    console.log('\n=== STEP 6: CRITICAL CHECK - Player 1 should keep remove buttons and host badge ===');
    evidence.sequenceSteps.push({ step: 6, action: 'Check Player 1 UI state', timestamp: new Date().toISOString() });
    
    // Wait for any updates to propagate
    await player1Page.waitForTimeout(3000);
    
    // Capture final Player 1 state
    const finalPlayer1State = await captureDetailedUIState(player1Page, 'Player1', 'After Player 2 joined');
    
    // === CRITICAL ANALYSIS ===
    console.log('\n=== CRITICAL ANALYSIS ===');
    
    // Compare UI states to identify the issue
    const beforeBotRemoval = evidence.hostUIStates.find(s => s.step === 'Before bot removal');
    const afterBotRemoval = evidence.hostUIStates.find(s => s.step === 'After bot removal');
    const beforePlayer2Join = evidence.hostUIStates.find(s => s.step === 'Before Player 2 joins');
    const afterPlayer2Join = evidence.hostUIStates.find(s => s.step === 'After Player 2 joined');
    
    console.log('\n📊 UI State Progression Analysis:');
    
    if (beforeBotRemoval && afterBotRemoval) {
      console.log(`\nBot Removal Impact:`);
      console.log(`   Before removal: ${beforeBotRemoval.removeButtonCount} remove buttons, ${beforeBotRemoval.hostBadgeCount} host badges`);
      console.log(`   After removal: ${afterBotRemoval.removeButtonCount} remove buttons, ${afterBotRemoval.hostBadgeCount} host badges`);
      console.log(`   Remove buttons change: ${afterBotRemoval.removeButtonCount - beforeBotRemoval.removeButtonCount}`);
      console.log(`   Host badges change: ${afterBotRemoval.hostBadgeCount - beforeBotRemoval.hostBadgeCount}`);
    }
    
    if (beforePlayer2Join && afterPlayer2Join) {
      console.log(`\nPlayer 2 Join Impact:`);
      console.log(`   Before Player 2 join: ${beforePlayer2Join.removeButtonCount} remove buttons, ${beforePlayer2Join.hostBadgeCount} host badges`);
      console.log(`   After Player 2 join: ${afterPlayer2Join.removeButtonCount} remove buttons, ${afterPlayer2Join.hostBadgeCount} host badges`);
      console.log(`   Remove buttons change: ${afterPlayer2Join.removeButtonCount - beforePlayer2Join.removeButtonCount}`);
      console.log(`   Host badges change: ${afterPlayer2Join.hostBadgeCount - beforePlayer2Join.hostBadgeCount}`);
      
      // This is the critical issue check
      const removeButtonsDisappeared = afterPlayer2Join.removeButtonCount < beforePlayer2Join.removeButtonCount;
      const hostBadgeDisappeared = afterPlayer2Join.hostBadgeCount < beforePlayer2Join.hostBadgeCount;
      
      console.log(`\n🎯 ISSUE VERIFICATION:`);
      console.log(`   Remove buttons disappeared: ${removeButtonsDisappeared ? '❌ YES (BUG CONFIRMED)' : '✅ NO'}`);
      console.log(`   Host badge disappeared: ${hostBadgeDisappeared ? '❌ YES (BUG CONFIRMED)' : '✅ NO'}`);
      
      evidence.criticalFindings = {
        removeButtonsDisappeared,
        hostBadgeDisappeared,
        beforeState: beforePlayer2Join,
        afterState: afterPlayer2Join
      };
    }
    
    // WebSocket message analysis
    console.log(`\n📡 WebSocket Message Analysis:`);
    console.log(`   Total room_update messages: ${evidence.websocketMessages.length}`);
    
    const messagesAfterPlayer2Join = evidence.websocketMessages.filter(m => {
      const msgTime = new Date(m.timestamp);
      const step5Time = new Date(evidence.sequenceSteps.find(s => s.step === 5)?.timestamp || 0);
      return msgTime > step5Time;
    });
    
    console.log(`   Messages after Player 2 join: ${messagesAfterPlayer2Join.length}`);
    messagesAfterPlayer2Join.forEach((msg, i) => {
      console.log(`   Message ${i + 1}: ${msg.receiver} - host="${msg.host_name}", players=${msg.playerCount}`);
    });
    
    console.log(`\n🔧 ROOT CAUSE INVESTIGATION:`);
    if (evidence.criticalFindings.removeButtonsDisappeared || evidence.criticalFindings.hostBadgeDisappeared) {
      console.log('❌ BUG CONFIRMED: UI elements disappear when Player 2 joins');
      console.log('   This suggests the room_update broadcast is not preserving complete UI state');
      console.log('   Next step: Analyze the specific WebSocket messages that cause this issue');
    } else {
      console.log('✅ BUG NOT REPRODUCED: UI elements persist correctly');
    }
    
    console.log('\n⏱️ Keeping browsers open for manual verification...');
    console.log('Screenshots saved for detailed analysis:');
    evidence.hostUIStates.forEach(state => {
      console.log(`   - sequence_${state.step.toLowerCase().replace(/\s+/g, '_')}_${state.player.toLowerCase()}.png`);
    });
    
    await player1Page.waitForTimeout(30000);
    
    return evidence;
    
  } catch (error) {
    console.error('❌ Exact sequence test failed:', error);
  } finally {
    await browser.close();
  }
}

testExactSequence().catch(console.error);