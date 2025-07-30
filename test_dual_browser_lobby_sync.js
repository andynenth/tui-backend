/**
 * 🤖 CLAUDE-FLOW SWARM: Dual-Browser Lobby Synchronization Test
 * 
 * Coordinated by: Researcher + Coder + Tester agents
 * Tests real-time lobby updates between two players:
 * 
 * Scenario:
 * 1. Player 1 joins lobby
 * 2. Player 2 joins lobby  
 * 3. Player 1 creates room → Player 2 should see it automatically
 * 4. Player 1 removes bot → Player 2 should see room update
 */

const { chromium } = require('playwright');

class DualBrowserLobbySync {
  constructor() {
    this.browser1 = null;
    this.browser2 = null;
    this.player1Page = null;
    this.player2Page = null;
    this.testResults = [];
  }

  async initialize() {
    console.log('🐝 SWARM COORDINATION: Initializing dual-browser test environment');
    
    // Launch browsers in parallel (swarm optimization)
    [this.browser1, this.browser2] = await Promise.all([
      chromium.launch({ headless: false, slowMo: 300 }),
      chromium.launch({ headless: false, slowMo: 300 })
    ]);

    [this.player1Page, this.player2Page] = await Promise.all([
      this.browser1.newPage(),
      this.browser2.newPage()
    ]);

    // Set up console logging for both browsers
    this.player1Page.on('console', msg => console.log(`📱 [PLAYER 1] ${msg.text()}`));
    this.player2Page.on('console', msg => console.log(`📱 [PLAYER 2] ${msg.text()}`));

    console.log('✅ Dual-browser environment ready');
  }

  async step1_PlayersJoinLobby() {
    console.log('\n🎯 STEP 1: Both players join lobby');
    console.log('=' .repeat(50));

    // Both players navigate and join lobby in parallel
    await Promise.all([
      this.setupPlayer(this.player1Page, 'Andy', 'PLAYER 1'),
      this.setupPlayer(this.player2Page, 'Alexanderium', 'PLAYER 2')
    ]);

    console.log('✅ Both players in lobby');
    return true;
  }

  async setupPlayer(page, playerName, label) {
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    await page.fill('input[placeholder*="name" i]', playerName);
    await page.click('button:has-text("Enter Lobby")');
    
    await page.waitForSelector('.lp-lobbyTitle', { timeout: 10000 });
    console.log(`✅ ${label} (${playerName}) joined lobby`);
  }

  async step2_Player1CreatesRoom() {
    console.log('\n🎯 STEP 2: Player 1 creates room, Player 2 should see it');
    console.log('=' .repeat(50));

    // Get initial room count for Player 2
    const initialP2Rooms = await this.player2Page.locator('.lp-roomCard').count();
    console.log(`📊 Player 2 initial room count: ${initialP2Rooms}`);

    // Player 1 creates room
    console.log('🖱️  Player 1: Clicking Create Room...');
    await this.player1Page.click('button:has-text("Create Room")');

    // Wait for Player 1 to navigate to room
    console.log('⏳ Waiting for Player 1 room creation...');
    await this.player1Page.waitForURL(/\/room\/\w+/, { timeout: 10000 });
    
    const roomUrl = this.player1Page.url();
    const roomId = roomUrl.match(/\/room\/(\w+)/)[1];
    console.log(`✅ Player 1 created room: ${roomId}`);

    // Now check if Player 2 sees the new room
    console.log('🔍 Checking if Player 2 sees the new room...');
    
    // Wait a moment for lobby update propagation
    await this.player2Page.waitForTimeout(2000);

    const updatedP2Rooms = await this.player2Page.locator('.lp-roomCard').count();
    console.log(`📊 Player 2 updated room count: ${updatedP2Rooms}`);

    // FIXED LOGIC: Check if Player 2 can see the specific room ID (regardless of count)
    console.log(`🔍 Looking for room "${roomId}" in Player 2's lobby...`);
    const roomVisible = await this.player2Page.locator(`.lp-roomCard:has-text("${roomId}")`).count() > 0;
    
    if (roomVisible) {
      console.log(`✅ SUCCESS: Player 2 can see room ${roomId}!`);
      
      // Get additional details about the room
      const roomCard = this.player2Page.locator(`.lp-roomCard:has-text("${roomId}")`);
      const hostName = await roomCard.locator('.lp-hostName').textContent() || 'Unknown';
      const playerCount = await roomCard.locator('.lp-roomOccupancy').textContent() || '?/?';
      
      console.log(`📋 Room details: Host=${hostName}, Players=${playerCount}`);
      
      this.testResults.push({
        test: 'Room Creation Sync',
        passed: true,
        details: `Room ${roomId} visible to Player 2. Host: ${hostName}, Players: ${playerCount}`
      });
      
      return { success: true, roomId, hostName, playerCount };
    } else {
      console.log(`❌ FAILED: Player 2 cannot see room ${roomId}`);
      
      // Debug: Show what rooms Player 2 can see
      const allRoomIds = await this.player2Page.locator('.lp-roomId').allTextContents();
      console.log(`🔍 Rooms Player 2 can see: ${allRoomIds.join(', ') || 'none'}`);
      
      this.testResults.push({
        test: 'Room Creation Sync',
        passed: false,
        details: `Room ${roomId} NOT visible to Player 2. Visible rooms: ${allRoomIds.join(', ')}`
      });
      
      return { success: false, roomId, visibleRooms: allRoomIds };
    }
  }

  async step3_Player1RemovesBot(roomId) {
    console.log('\n🎯 STEP 3: Player 1 removes bot, Player 2 should see room update (4/4 → 3/4)');
    console.log('=' .repeat(50));

    // Get initial player count from Player 2's view
    console.log('🔍 Checking Player 2\'s view of room occupancy...');
    const initialOccupancy = await this.getPlayer2RoomOccupancy(roomId);
    console.log(`📊 Player 2 sees initial occupancy: ${initialOccupancy}`);

    // Player 1 removes a bot - try multiple selectors
    console.log('🖱️  Player 1: Looking for bot removal button...');
    
    // Try different selectors for the remove bot button
    const possibleSelectors = [
      'button:has-text("Remove")',
      'button:has-text("×")', 
      'button[title*="Remove"]',
      '.remove-bot-btn',
      '.bot-remove',
      'button.remove'
    ];

    let botRemoved = false;
    for (const selector of possibleSelectors) {
      const buttons = this.player1Page.locator(selector);
      const count = await buttons.count();
      
      if (count > 0) {
        console.log(`🎯 Found ${count} button(s) with selector: ${selector}`);
        try {
          await buttons.first().click({ timeout: 5000 });
          console.log(`✅ Clicked bot removal button`);
          botRemoved = true;
          break;
        } catch (error) {
          console.log(`⚠️  Button not clickable: ${error.message}`);
        }
      }
    }

    if (!botRemoved) {
      console.log('⚠️  Could not find/click bot removal button - checking for other removal methods...');
      
      // Alternative: Look for any clickable bot-related elements
      const botElements = this.player1Page.locator('text=Bot');
      const botCount = await botElements.count();
      console.log(`🤖 Found ${botCount} bot elements`);
      
      if (botCount > 0) {
        // Try clicking on a bot element directly
        try {
          await botElements.first().click();
          console.log('✅ Clicked on bot element');
          botRemoved = true;
        } catch (error) {
          console.log(`⚠️  Could not click bot element: ${error.message}`);
        }
      }
    }

    if (!botRemoved) {
      console.log('❌ FAILED: Could not remove bot - test cannot continue');
      this.testResults.push({
        test: 'Bot Removal Sync',
        passed: false,
        details: 'Could not find or click bot removal button'
      });
      return { success: false, error: 'Bot removal button not found' };
    }

    // Wait for room update to propagate
    console.log('⏳ Waiting for room update to propagate...');
    await this.player1Page.waitForTimeout(3000);
    await this.player2Page.waitForTimeout(1000);

    // Check if Player 2 sees the occupancy change
    console.log('🔍 Checking if Player 2 sees room occupancy update...');
    const updatedOccupancy = await this.getPlayer2RoomOccupancy(roomId);
    console.log(`📊 Player 2 sees updated occupancy: ${updatedOccupancy}`);

    // Compare occupancy (e.g., "4/4" → "3/4")
    const occupancyChanged = initialOccupancy !== updatedOccupancy;
    const expectedChange = initialOccupancy === "4/4" && updatedOccupancy === "3/4";
    
    if (expectedChange) {
      console.log('✅ SUCCESS: Player 2 saw room occupancy update correctly!');
      this.testResults.push({
        test: 'Bot Removal Sync',
        passed: true,
        details: `Room occupancy updated: ${initialOccupancy} → ${updatedOccupancy}`
      });
      return { success: true, initialOccupancy, updatedOccupancy };
    } else if (occupancyChanged) {
      console.log('⚠️  PARTIAL: Player 2 saw occupancy change but not expected 4/4→3/4');
      this.testResults.push({
        test: 'Bot Removal Sync',
        passed: false,
        details: `Unexpected occupancy change: ${initialOccupancy} → ${updatedOccupancy}`
      });
      return { success: false, initialOccupancy, updatedOccupancy, reason: 'unexpected_change' };
    } else {
      console.log('❌ FAILED: Player 2 did not see room occupancy update');
      this.testResults.push({
        test: 'Bot Removal Sync',
        passed: false,
        details: `Room occupancy unchanged: ${initialOccupancy} → ${updatedOccupancy}`
      });
      return { success: false, initialOccupancy, updatedOccupancy, reason: 'no_change' };
    }
  }

  async getPlayer2RoomOccupancy(roomId) {
    try {
      // Find the room card with the specific room ID
      const roomCard = this.player2Page.locator(`.lp-roomCard:has-text("${roomId}")`);
      
      if (await roomCard.count() === 0) {
        console.log(`⚠️  Room ${roomId} not found in Player 2's view`);
        return 'not_found';
      }

      // Get the occupancy text (e.g., "4/4", "3/4")
      const occupancyElement = roomCard.locator('.lp-roomOccupancy');
      const occupancy = await occupancyElement.textContent();
      
      return occupancy?.trim() || 'unknown';
    } catch (error) {
      console.log(`⚠️  Error getting room occupancy: ${error.message}`);
      return 'error';
    }
  }

  async getBotCountInPlayer2Room(roomId) {
    try {
      // Find the room card with the specific room ID
      const roomCard = this.player2Page.locator(`.lp-roomCard:has-text("${roomId}")`);
      
      if (await roomCard.count() === 0) {
        console.log(`⚠️  Room ${roomId} not found in Player 2's view`);
        return 0;
      }

      // Count bot slots in the room (slots with "Bot" text)
      const botSlots = roomCard.locator('.lp-playerSlot:has-text("Bot")');
      const count = await botSlots.count();
      
      return count;
    } catch (error) {
      console.log(`⚠️  Error counting bots: ${error.message}`);
      return 0;
    }
  }

  async cleanup() {
    console.log('\n🧹 Cleaning up browsers...');
    if (this.browser1) await this.browser1.close();
    if (this.browser2) await this.browser2.close();
  }

  async runFullTest() {
    try {
      await this.initialize();

      const step1Result = await this.step1_PlayersJoinLobby();
      if (!step1Result) throw new Error('Step 1 failed');

      const step2Result = await this.step2_Player1CreatesRoom();
      if (!step2Result.success) {
        console.log('⚠️  Continuing despite room creation sync failure...');
      }

      const step3Result = await this.step3_Player1RemovesBot(step2Result.roomId);

      return this.generateReport();

    } catch (error) {
      console.error('💥 Test error:', error.message);
      return {
        success: false,
        error: error.message,
        results: this.testResults
      };
    } finally {
      await this.cleanup();
    }
  }

  generateReport() {
    console.log('\n🎯 SWARM TEST RESULTS:');
    console.log('=' .repeat(60));
    
    let allPassed = true;
    
    this.testResults.forEach((result, index) => {
      const status = result.passed ? '✅ PASS' : '❌ FAIL';
      console.log(`${index + 1}. ${result.test}: ${status}`);
      console.log(`   Details: ${result.details}`);
      
      if (!result.passed) allPassed = false;
    });

    const overallStatus = allPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED';
    console.log(`\n🏆 Overall Result: ${overallStatus}`);

    return {
      success: allPassed,
      results: this.testResults,
      summary: overallStatus
    };
  }
}

// Execute the swarm-coordinated test
if (require.main === module) {
  const test = new DualBrowserLobbySync();
  
  test.runFullTest()
    .then(result => {
      console.log('\n🐝 SWARM COORDINATION COMPLETE');
      process.exit(result.success ? 0 : 1);
    })
    .catch(error => {
      console.error('💥 Swarm test crashed:', error);
      process.exit(1);
    });
}

module.exports = { DualBrowserLobbySync };