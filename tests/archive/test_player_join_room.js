/**
 * 🤖 CLAUDE-FLOW SWARM: Player Join Room Test
 * 
 * Tests that a player can successfully join an existing room.
 * 
 * Scenario:
 * 1. Player 1 joins lobby and creates room (3/4 slots available)
 * 2. Player 2 joins lobby and sees the room
 * 3. Player 2 clicks on the room to join
 * 4. Verify Player 2 successfully enters the room
 * 5. Verify lobby shows updated occupancy (3/4 → 4/4)
 */

const { chromium } = require('playwright');

class PlayerJoinRoomTest {
  constructor() {
    this.browser1 = null;
    this.browser2 = null;
    this.player1Page = null;
    this.player2Page = null;
    this.testResults = [];
  }

  async initialize() {
    console.log('🐝 SWARM TEST: Initializing player join room test');
    
    // Launch browsers in parallel
    [this.browser1, this.browser2] = await Promise.all([
      chromium.launch({ headless: false, slowMo: 300 }),
      chromium.launch({ headless: false, slowMo: 300 })
    ]);

    [this.player1Page, this.player2Page] = await Promise.all([
      this.browser1.newPage(),
      this.browser2.newPage()
    ]);

    // Set up console logging
    this.player1Page.on('console', msg => console.log(`📱 [PLAYER 1] ${msg.text()}`));
    this.player2Page.on('console', msg => console.log(`📱 [PLAYER 2] ${msg.text()}`));

    console.log('✅ Test environment ready');
  }

  async step1_Player1CreatesRoom() {
    console.log('\n🎯 STEP 1: Player 1 creates room with available slots');
    console.log('=' .repeat(50));

    // Player 1 joins lobby and creates room
    await this.setupPlayer(this.player1Page, 'Andy', 'PLAYER 1');
    
    console.log('🖱️  Player 1: Creating room...');
    await this.player1Page.click('button:has-text("Create Room")');
    
    // Wait for room creation and navigation
    await this.player1Page.waitForURL(/\/room\/\w+/, { timeout: 10000 });
    const roomUrl = this.player1Page.url();
    const roomId = roomUrl.match(/\/room\/(\w+)/)[1];
    
    console.log(`✅ Player 1 created room: ${roomId}`);
    
    // Remove one bot to create an available slot (4/4 → 3/4)
    console.log('🤖 Player 1: Removing one bot to create available slot...');
    const removeButtons = this.player1Page.locator('button:has-text("Remove")');
    if (await removeButtons.count() > 0) {
      await removeButtons.first().click();
      await this.player1Page.waitForTimeout(1000); // Wait for room update
      console.log('✅ Bot removed - room now has available slot');
    }
    
    return { roomId, success: true };
  }

  async step2_Player2JoinsLobby() {
    console.log('\n🎯 STEP 2: Player 2 joins lobby and sees available room');
    console.log('=' .repeat(50));

    await this.setupPlayer(this.player2Page, 'Alexanderium', 'PLAYER 2');
    
    // Wait for room list to load
    await this.player2Page.waitForTimeout(2000);
    
    console.log('✅ Player 2 in lobby');
    return true;
  }

  async step3_Player2JoinsRoom(roomId) {
    console.log('\n🎯 STEP 3: Player 2 joins the available room');
    console.log('=' .repeat(50));

    // Check if Player 2 can see the room
    console.log(`🔍 Looking for room ${roomId} in Player 2's lobby...`);
    const roomCard = this.player2Page.locator(`.lp-roomCard:has-text("${roomId}")`);
    
    if (await roomCard.count() === 0) {
      console.log(`❌ FAILED: Player 2 cannot see room ${roomId}`);
      return { success: false, error: 'Room not visible' };
    }

    // Check initial occupancy
    const initialOccupancy = await roomCard.locator('.lp-roomOccupancy').textContent();
    console.log(`📊 Initial room occupancy: ${initialOccupancy}`);

    // Click on the room to join
    console.log('🖱️  Player 2: Clicking on room to join...');
    await roomCard.click();
    
    // Wait for navigation to room or error
    const result = await Promise.race([
      this.player2Page.waitForURL(/\/room\/\w+/, { timeout: 10000 }).then(() => 'SUCCESS'),
      this.player2Page.waitForSelector('[role="alert"], .error', { timeout: 10000 }).then(() => 'ERROR'),
      new Promise(resolve => setTimeout(() => resolve('TIMEOUT'), 10000))
    ]);

    if (result === 'SUCCESS') {
      const joinedUrl = this.player2Page.url();
      const joinedRoomId = joinedUrl.match(/\/room\/(\w+)/)?.[1];
      
      if (joinedRoomId === roomId) {
        console.log(`✅ SUCCESS: Player 2 joined room ${roomId}`);
        
        // Wait for room UI to load
        await this.player2Page.waitForSelector('.rp-gameContainer, .room-page', { timeout: 5000 });
        
        this.testResults.push({
          test: 'Player Join Room',
          passed: true,
          details: `Player 2 successfully joined room ${roomId}`
        });
        
        return { success: true, roomId: joinedRoomId, initialOccupancy };
        
      } else {
        console.log(`❌ FAILED: Player 2 joined wrong room ${joinedRoomId} instead of ${roomId}`);
        return { success: false, error: 'Wrong room joined' };
      }
      
    } else if (result === 'ERROR') {
      console.log('❌ FAILED: Error occurred during room join');
      return { success: false, error: 'Join error detected' };
      
    } else {
      console.log('❌ FAILED: Room join timed out');
      return { success: false, error: 'Join timeout' };
    }
  }

  async step4_VerifyLobbyUpdate(roomId, initialOccupancy) {
    console.log('\n🎯 STEP 4: Verify lobby shows updated occupancy');
    console.log('=' .repeat(50));

    // Go back to Player 1's lobby view to check occupancy
    console.log('🔄 Checking if lobby reflects Player 2 joining...');
    
    // Navigate Player 1 back to lobby (simulating another user viewing lobby)
    await this.player1Page.goto('http://localhost:5050/lobby');
    await this.player1Page.waitForSelector('.lp-lobbyTitle', { timeout: 5000 });
    
    // Wait for room list to load
    await this.player1Page.waitForTimeout(2000);
    
    // Check updated occupancy
    const roomCard = this.player1Page.locator(`.lp-roomCard:has-text("${roomId}")`);
    if (await roomCard.count() > 0) {
      const updatedOccupancy = await roomCard.locator('.lp-roomOccupancy').textContent();
      console.log(`📊 Updated room occupancy: ${initialOccupancy} → ${updatedOccupancy}`);
      
      // Expected: 3/4 → 4/4 (room should now be full)
      const occupancyIncreased = this.compareOccupancy(initialOccupancy, updatedOccupancy);
      
      if (occupancyIncreased) {
        console.log('✅ SUCCESS: Lobby shows updated occupancy after player joined');
        this.testResults.push({
          test: 'Lobby Occupancy Update',
          passed: true,
          details: `Occupancy updated: ${initialOccupancy} → ${updatedOccupancy}`
        });
        return { success: true, initialOccupancy, updatedOccupancy };
        
      } else {
        console.log('❌ FAILED: Lobby occupancy did not update');
        this.testResults.push({
          test: 'Lobby Occupancy Update',
          passed: false,
          details: `Occupancy unchanged: ${initialOccupancy} → ${updatedOccupancy}`
        });
        return { success: false, initialOccupancy, updatedOccupancy };
      }
      
    } else {
      console.log('❌ FAILED: Room not found in lobby after join');
      return { success: false, error: 'Room disappeared from lobby' };
    }
  }

  compareOccupancy(initial, updated) {
    // Extract numbers from occupancy strings like "3/4" → [3, 4]
    const parseOccupancy = (occ) => {
      const match = occ?.match(/(\d+)\/(\d+)/);
      return match ? [parseInt(match[1]), parseInt(match[2])] : [0, 0];
    };
    
    const [initialCount, initialMax] = parseOccupancy(initial);
    const [updatedCount, updatedMax] = parseOccupancy(updated);
    
    // Player count should have increased by 1
    return updatedCount === initialCount + 1 && updatedMax === initialMax;
  }

  async setupPlayer(page, playerName, label) {
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    await page.fill('input[placeholder*="name" i]', playerName);
    await page.click('button:has-text("Enter Lobby")');
    
    await page.waitForSelector('.lp-lobbyTitle', { timeout: 10000 });
    console.log(`✅ ${label} (${playerName}) joined lobby`);
  }

  async cleanup() {
    console.log('\n🧹 Cleaning up browsers...');
    if (this.browser1) await this.browser1.close();
    if (this.browser2) await this.browser2.close();
  }

  async runFullTest() {
    try {
      await this.initialize();

      const step1Result = await this.step1_Player1CreatesRoom();
      if (!step1Result.success) throw new Error('Step 1 failed');

      const step2Result = await this.step2_Player2JoinsLobby();
      if (!step2Result) throw new Error('Step 2 failed');

      const step3Result = await this.step3_Player2JoinsRoom(step1Result.roomId);
      if (!step3Result.success) {
        console.log('⚠️  Player join failed, skipping lobby update check');
        this.testResults.push({
          test: 'Player Join Room',
          passed: false,
          details: step3Result.error || 'Unknown join error'
        });
      } else {
        // Test lobby update
        await this.step4_VerifyLobbyUpdate(step1Result.roomId, step3Result.initialOccupancy);
      }

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
    console.log('\n🎯 PLAYER JOIN TEST RESULTS:');
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

// Execute the test
if (require.main === module) {
  const test = new PlayerJoinRoomTest();
  
  test.runFullTest()
    .then(result => {
      console.log('\n🐝 PLAYER JOIN TEST COMPLETE');
      process.exit(result.success ? 0 : 1);
    })
    .catch(error => {
      console.error('💥 Test crashed:', error);
      process.exit(1);
    });
}

module.exports = { PlayerJoinRoomTest };