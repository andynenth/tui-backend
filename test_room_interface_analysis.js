const { chromium } = require('playwright');

/**
 * ROOM INTERFACE ANALYSIS TEST
 * 
 * More targeted analysis to find and examine the actual room slot interface
 * after the WebSocket broadcast fixes are applied.
 */

async function analyzeRoomInterface() {
  console.log('🏠 ROOM INTERFACE ANALYSIS TEST');
  console.log('================================');
  console.log('Targeted analysis of room slot interface elements');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 1500
  });
  
  try {
    const evidence = {
      interfaceElements: [],
      websocketMessages: [],
      roomStates: []
    };
    
    // Enhanced UI element detection
    const analyzeRoomInterface = async (page, playerName, phase) => {
      try {
        console.log(`\n🔍 Analyzing ${playerName} interface (${phase})...`);
        
        // Wait for page to stabilize
        await page.waitForTimeout(3000);
        
        // Take screenshot for visual debugging
        await page.screenshot({ 
          path: `room_interface_${playerName.toLowerCase()}_${phase}.png`,
          fullPage: true
        });
        
        // Look for various possible room interface elements
        const selectors = [
          // Common slot/player selectors
          '[class*="slot"]', '[data-testid*="slot"]', '.player-slot', '.room-slot',
          '[class*="player"]', '[data-testid*="player"]', '.player-card', '.player-item',
          // Room/game area selectors  
          '[class*="room"]', '[class*="game"]', '.room-container', '.game-area',
          // Table/seat selectors
          '[class*="seat"]', '[class*="table"]', '.seat', '.table-seat',
          // List/grid selectors
          '[class*="list"]', '[class*="grid"]', '.player-list', '.player-grid',
          // Button selectors
          'button:has-text("Remove")', 'button:has-text("Kick")', 'button:has-text("Add Bot")',
          // Badge/status selectors
          '[class*="host"]', '[class*="badge"]', '.host-badge', '.status-badge'
        ];
        
        const interfaceAnalysis = {
          timestamp: new Date().toISOString(),
          player: playerName,
          phase,
          foundElements: [],
          allText: '',
          buttonCount: 0,
          roomContent: {}
        };
        
        // Analyze each selector type
        for (const selector of selectors) {
          try {
            const elements = await page.locator(selector).all();
            if (elements.length > 0) {
              interfaceAnalysis.foundElements.push({
                selector,
                count: elements.length,
                texts: []
              });
              
              // Get text content from first few elements
              for (let i = 0; i < Math.min(elements.length, 3); i++) {
                const text = await elements[i].textContent().catch(() => '');
                const isVisible = await elements[i].isVisible().catch(() => false);
                if (text.trim() && isVisible) {
                  interfaceAnalysis.foundElements[interfaceAnalysis.foundElements.length - 1].texts.push(text.trim());
                }
              }
            }
          } catch (e) {
            // Selector not found, continue
          }
        }
        
        // Get all visible text on page for analysis
        const bodyText = await page.locator('body').textContent().catch(() => '');
        interfaceAnalysis.allText = bodyText;
        
        // Count all buttons
        const allButtons = await page.locator('button').all();
        interfaceAnalysis.buttonCount = allButtons.length;
        
        // Look specifically for room-related content
        const roomIndicators = [
          'TestHost', 'TestJoiner', 'Bot', 'Host', 'Remove', 'Kick', 'Add Bot', 
          'waiting', 'ready', 'playing', 'joined', 'left'
        ];
        
        for (const indicator of roomIndicators) {
          if (bodyText.toLowerCase().includes(indicator.toLowerCase())) {
            interfaceAnalysis.roomContent[indicator] = true;
          }
        }
        
        evidence.interfaceElements.push(interfaceAnalysis);
        
        // Log findings
        console.log(`📊 ${playerName} Interface Analysis (${phase}):`);
        console.log(`   Found element types: ${interfaceAnalysis.foundElements.length}`);
        console.log(`   Total buttons: ${interfaceAnalysis.buttonCount}`);
        console.log(`   Room indicators found: ${Object.keys(interfaceAnalysis.roomContent).join(', ')}`);
        
        // Log specific elements found
        interfaceAnalysis.foundElements.forEach(elem => {
          if (elem.texts.length > 0) {
            console.log(`   ${elem.selector}: ${elem.count} elements - "${elem.texts.join('", "')}""`);
          }
        });
        
        return interfaceAnalysis;
        
      } catch (error) {
        console.error(`Failed to analyze interface for ${playerName}:`, error);
        return null;
      }
    };
    
    // WebSocket message capture
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
                host_name: parsed.data?.host_name,
                started: parsed.data?.started,
                players: parsed.data?.players || [],
                playerCount: parsed.data?.players?.length || 0
              };
              
              evidence.websocketMessages.push(message);
              
              console.log(`📥 ${playerName} room_update: ${message.playerCount} players, host="${message.host_name}", started=${message.started}`);
            }
          } catch (e) {}
        });
      });
    };
    
    // === Test Sequence ===
    
    // Host creates room
    console.log('\n=== HOST CREATES ROOM ===');
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
    await hostPage.waitForTimeout(4000);
    
    await analyzeRoomInterface(hostPage, 'Host', 'room_created');
    
    // Player joins
    console.log('\n=== PLAYER JOINS ROOM ===');
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
      await joinerPage.waitForTimeout(5000);
      
      // Analyze both interfaces after join
      await analyzeRoomInterface(hostPage, 'Host', 'after_player_join');
      await analyzeRoomInterface(joinerPage, 'Joiner', 'in_room');
    } else {
      console.log('❌ No room cards found');
    }
    
    // Bot interaction test
    console.log('\n=== BOT INTERACTION TEST ===');
    const addBotButtons = await hostPage.locator('button:has-text("Add Bot"), button:has-text("Bot")').all();
    if (addBotButtons.length > 0) {
      console.log('🤖 Adding bot...');
      await addBotButtons[0].click();
      await hostPage.waitForTimeout(3000);
      
      await analyzeRoomInterface(hostPage, 'Host', 'after_bot_added');
    }
    
    const removeButtons = await hostPage.locator('button:has-text("Remove"), button:has-text("Kick")').all();
    if (removeButtons.length > 0) {
      console.log('🗑️ Removing element...');
      await removeButtons[0].click();
      await hostPage.waitForTimeout(3000);
      
      await analyzeRoomInterface(hostPage, 'Host', 'after_removal');
    }
    
    // Player leave test
    console.log('\n=== PLAYER LEAVE TEST ===');
    await analyzeRoomInterface(hostPage, 'Host', 'before_player_leave');
    
    console.log('🚪 TestJoiner leaving...');
    await joinerPage.close();
    await joinerContext.close();
    await hostPage.waitForTimeout(5000);
    
    await analyzeRoomInterface(hostPage, 'Host', 'after_player_leave');
    
    // === Final Analysis ===
    console.log('\n=== COMPREHENSIVE ANALYSIS ===');
    
    // WebSocket message analysis
    console.log(`\n📡 WebSocket Analysis:`);
    console.log(`   Total room_update messages: ${evidence.websocketMessages.length}`);
    const validMessages = evidence.websocketMessages.filter(m => m.host_name && m.host_name !== 'undefined');
    console.log(`   Messages with valid host_name: ${validMessages.length}/${evidence.websocketMessages.length}`);
    
    // Interface element analysis
    console.log(`\n🖥️ Interface Analysis:`);
    const interfacePhases = ['room_created', 'after_player_join', 'in_room', 'after_player_leave'];
    
    for (const phase of interfacePhases) {
      const phaseData = evidence.interfaceElements.filter(e => e.phase === phase);
      if (phaseData.length > 0) {
        console.log(`\n   ${phase.toUpperCase()}:`);
        phaseData.forEach(data => {
          console.log(`     ${data.player}: ${data.foundElements.length} element types, ${data.buttonCount} buttons`);
          console.log(`     Room content: ${Object.keys(data.roomContent).join(', ') || 'none'}`);
        });
      }
    }
    
    // Check for the specific issues
    const afterJoinData = evidence.interfaceElements.filter(e => e.phase === 'after_player_join' && e.player === 'Host');
    const afterLeaveData = evidence.interfaceElements.filter(e => e.phase === 'after_player_leave' && e.player === 'Host');
    
    console.log(`\n🎯 Issue Analysis:`);
    if (afterJoinData.length > 0) {
      const hasWaitingIssue = afterJoinData[0].allText.toLowerCase().includes('waiting');
      console.log(`   "All slots turn to waiting" issue: ${hasWaitingIssue ? '❌ Present' : '✅ Not detected'}`);
    }
    
    if (afterLeaveData.length > 0) {
      const hasHostContent = afterLeaveData[0].roomContent['Host'] || afterLeaveData[0].allText.toLowerCase().includes('host');
      const hasRemoveButtons = afterLeaveData[0].roomContent['Remove'] || afterLeaveData[0].allText.toLowerCase().includes('remove');
      console.log(`   Host badge after leave: ${hasHostContent ? '✅ Present' : '❌ Missing'}`);
      console.log(`   Remove buttons after leave: ${hasRemoveButtons ? '✅ Present' : '❌ Missing'}`);
    }
    
    console.log(`\n🔧 Broadcast Fix Status: ${validMessages.length === evidence.websocketMessages.length ? '✅ Working' : '❌ Issues'}`);
    
    console.log('\n⏱️ Keeping browser open for manual inspection...');
    console.log('Screenshots saved for visual analysis:');
    console.log('   - room_interface_host_room_created.png');
    console.log('   - room_interface_host_after_player_join.png'); 
    console.log('   - room_interface_joiner_in_room.png');
    console.log('   - room_interface_host_after_player_leave.png');
    
    await hostPage.waitForTimeout(30000);
    
    return evidence;
    
  } catch (error) {
    console.error('❌ Room interface analysis failed:', error);
  } finally {
    await browser.close();
  }
}

analyzeRoomInterface().catch(console.error);