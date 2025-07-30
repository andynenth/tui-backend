const { chromium } = require('playwright');
const fs = require('fs');

const TEST_CONFIG = {
  baseUrl: 'http://localhost:5050',
  timeout: 30000,
  headless: false,
  slowMo: 1000
};

class RoomVisibilityInvestigator {
  constructor() {
    this.evidence = {
      websocketMessages: [],
      uiScreenshots: [],
      playerCounts: [],
      filteringDecisions: [],
      timeline: []
    };
  }

  logEvidence(type, message, data = {}) {
    const timestamp = new Date().toISOString();
    const entry = {
      timestamp,
      type,
      message,
      data
    };
    
    this.evidence.timeline.push(entry);
    console.log(`🔍 [${timestamp}] ${type}: ${message}`);
    
    if (data && Object.keys(data).length > 0) {
      console.log(`   📊 Data:`, JSON.stringify(data, null, 2));
    }
  }

  async captureWebSocketMessages(page, playerName) {
    const messages = [];
    
    page.on('websocket', ws => {
      this.logEvidence('WEBSOCKET', `${playerName} connected to ${ws.url()}`);
      
      ws.on('framesent', data => {
        const timestamp = new Date().toISOString();
        const message = data.payload;
        
        try {
          const parsed = JSON.parse(message);
          messages.push({
            timestamp,
            player: playerName,
            direction: 'sent',
            message: parsed
          });
          
          if (parsed.event === 'get_rooms' || parsed.event === 'create_room') {
            this.logEvidence('WEBSOCKET_SENT', `${playerName} sent ${parsed.event}`, parsed);
          }
        } catch (e) {
          this.logEvidence('ERROR', `Failed to parse sent message for ${playerName}`, { error: e.message });
        }
      });
      
      ws.on('framereceived', data => {
        const timestamp = new Date().toISOString();
        const message = data.payload;
        
        try {
          const parsed = JSON.parse(message);
          messages.push({
            timestamp,
            player: playerName,
            direction: 'received',
            message: parsed
          });
          
          if (parsed.event === 'room_list_update') {
            const roomCount = parsed.data?.rooms?.length || 0;
            this.logEvidence('ROOM_LIST_UPDATE', `${playerName} received room_list_update`, {
              roomCount,
              rooms: parsed.data?.rooms?.map(r => ({
                room_id: r.room_id,
                player_count: r.player_count,
                max_players: r.max_players,
                host_name: r.host_name
              }))
            });
            
            // Track player counts for evidence
            this.evidence.playerCounts.push({
              timestamp,
              player: playerName,
              roomCount,
              rooms: parsed.data?.rooms || []
            });
          }
        } catch (e) {
          this.logEvidence('ERROR', `Failed to parse received message for ${playerName}`, { error: e.message });
        }
      });
    });
    
    this.evidence.websocketMessages.push({ player: playerName, messages });
    return messages;
  }

  async takeScreenshot(page, playerName, step, description) {
    const filename = `evidence_${playerName}_${step}_${Date.now()}.png`;
    const filepath = `/Users/nrw/python/tui-project/liap-tui/evidence/${filename}`;
    
    // Ensure evidence directory exists
    const dir = '/Users/nrw/python/tui-project/liap-tui/evidence';
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    await page.screenshot({ path: filepath, fullPage: true });
    
    this.evidence.uiScreenshots.push({
      player: playerName,
      step,
      description,
      filename,
      filepath
    });
    
    this.logEvidence('SCREENSHOT', `${playerName} - ${description}`, { filename });
  }

  async checkUIRoomCount(page, playerName, step) {
    try {
      const roomCountText = await page.locator('.lp-roomCount').textContent({ timeout: 5000 });
      const roomCards = await page.locator('.lp-roomCard').count();
      
      const match = roomCountText.match(/Available Rooms \((\d+)\)/);
      const displayedCount = match ? parseInt(match[1]) : 0;
      
      this.logEvidence('UI_CHECK', `${playerName} UI state at ${step}`, {
        roomCountText,
        displayedCount,
        actualRoomCards: roomCards
      });
      
      return { displayedCount, actualRoomCards };
    } catch (error) {
      this.logEvidence('ERROR', `Failed to check UI for ${playerName} at ${step}`, { error: error.message });
      return { displayedCount: 0, actualRoomCards: 0 };
    }
  }

  async enterLobby(page, playerName) {
    this.logEvidence('STEP', `${playerName} entering lobby`);
    
    await page.goto(TEST_CONFIG.baseUrl);
    await page.waitForLoadState('networkidle');
    
    const nameInput = await page.locator('input[type="text"]').first();
    await nameInput.fill(playerName);
    
    const startButton = await page.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first();
    await startButton.click();
    
    await page.waitForTimeout(3000);
    
    // Verify lobby loaded
    const lobbyElement = await page.locator('.lp-lobbyTitle').textContent();
    this.logEvidence('SUCCESS', `${playerName} entered lobby`, { lobbyTitle: lobbyElement });
    
    await this.takeScreenshot(page, playerName, 'entered_lobby', 'Successfully entered lobby');
  }

  async saveEvidence() {
    const evidenceFile = `/Users/nrw/python/tui-project/liap-tui/room_visibility_evidence_${Date.now()}.json`;
    
    const report = {
      testCompleted: new Date().toISOString(),
      summary: {
        totalWebSocketMessages: this.evidence.websocketMessages.reduce((sum, p) => sum + p.messages.length, 0),
        totalScreenshots: this.evidence.uiScreenshots.length,
        totalPlayerCountRecords: this.evidence.playerCounts.length,
        totalTimelineEntries: this.evidence.timeline.length
      },
      evidence: this.evidence
    };
    
    fs.writeFileSync(evidenceFile, JSON.stringify(report, null, 2));
    console.log(`📁 Evidence saved to: ${evidenceFile}`);
    
    return evidenceFile;
  }
}

async function investigateRoomVisibility() {
  console.log('🔍 Starting Room Visibility Investigation...');
  console.log('🎯 Hypothesis: Rooms are filtered as "full" when they have 4/4 players (including bots)');
  
  const investigator = new RoomVisibilityInvestigator();
  const browser = await chromium.launch({
    headless: TEST_CONFIG.headless,
    slowMo: TEST_CONFIG.slowMo
  });
  
  try {
    // Create separate contexts for Player 1 and Player 2
    const player1Context = await browser.newContext();
    const player2Context = await browser.newContext();
    
    const player1Page = await player1Context.newPage();
    const player2Page = await player2Context.newPage();
    
    // Set up WebSocket message capture
    const player1Messages = await investigator.captureWebSocketMessages(player1Page, 'Player1');
    const player2Messages = await investigator.captureWebSocketMessages(player2Page, 'Player2');
    
    console.log('\n=== PHASE 1: INITIAL STATE ===');
    
    investigator.logEvidence('PHASE', 'Both players enter lobby');
    
    // Both players enter lobby
    await investigator.enterLobby(player1Page, 'Player1');
    await investigator.enterLobby(player2Page, 'Player2');
    
    // Check initial room counts
    const player1Initial = await investigator.checkUIRoomCount(player1Page, 'Player1', 'initial');
    const player2Initial = await investigator.checkUIRoomCount(player2Page, 'Player2', 'initial');
    
    console.log('\n=== PHASE 2: ROOM CREATION ===');
    
    investigator.logEvidence('PHASE', 'Player1 creates room - testing if Player2 can see it');
    
    // Player 1 creates room
    const createBtn = await player1Page.locator('button').filter({ hasText: /create/i }).first();
    await createBtn.click();
    
    investigator.logEvidence('ACTION', 'Player1 clicked Create Room button');
    
    // Wait for room creation to complete
    await player1Page.waitForTimeout(4000);
    
    // Take screenshots after room creation
    await investigator.takeScreenshot(player1Page, 'Player1', 'after_create', 'After creating room');
    await investigator.takeScreenshot(player2Page, 'Player2', 'after_create', 'After Player1 created room');
    
    // Check room counts after creation
    const player1AfterCreate = await investigator.checkUIRoomCount(player1Page, 'Player1', 'after_create');
    const player2AfterCreate = await investigator.checkUIRoomCount(player2Page, 'Player2', 'after_create');
    
    console.log('\n=== PHASE 3: HYPOTHESIS TESTING ===');
    
    investigator.logEvidence('HYPOTHESIS', 'Testing if room is invisible due to 4/4 player count');
    
    // Manual refresh to ensure we have latest data
    const refreshBtn = await player2Page.locator('button[title="Refresh room list"]');
    await refreshBtn.click();
    await player2Page.waitForTimeout(2000);
    
    const player2AfterRefresh = await investigator.checkUIRoomCount(player2Page, 'Player2', 'after_refresh');
    
    // Check if Player2 can see the room
    if (player2AfterRefresh.displayedCount === 0) {
      investigator.logEvidence('EVIDENCE', '❌ CONFIRMED: Player2 cannot see newly created room', {
        hypothesis: 'Room is filtered as "full" with 4/4 players',
        player1Rooms: player1AfterCreate.displayedCount,
        player2Rooms: player2AfterRefresh.displayedCount
      });
      
      console.log('\n=== PHASE 4: BOT REMOVAL TEST ===');
      
      investigator.logEvidence('PHASE', 'Testing if removing bot makes room visible');
      
      // Navigate Player1 back to their room to remove a bot
      // This requires navigating to the room page first
      await player1Page.waitForTimeout(2000);
      
      // Check if Player1 is already in the room or needs to navigate
      try {
        const roomIdElement = await player1Page.locator('.room-id, .room-header').first().textContent({ timeout: 3000 });
        investigator.logEvidence('INFO', 'Player1 appears to be in room', { roomId: roomIdElement });
        
        // Try to remove a bot
        const removeBotButtons = await player1Page.locator('button').filter({ hasText: /remove|kick/i }).all();
        if (removeBotButtons.length > 0) {
          investigator.logEvidence('ACTION', 'Player1 attempting to remove bot');
          await removeBotButtons[0].click();
          await player1Page.waitForTimeout(2000);
          
          // Navigate back to lobby to check room visibility
          const backToLobbyBtn = await player1Page.locator('button').filter({ hasText: /lobby|back/i }).first();
          if (backToLobbyBtn) {
            await backToLobbyBtn.click();
            await player1Page.waitForTimeout(2000);
          }
        }
      } catch (error) {
        investigator.logEvidence('INFO', 'Player1 not in room page, trying different approach');
      }
      
      // Check Player2's room visibility after potential bot removal
      await player2Page.locator('button[title="Refresh room list"]').click();
      await player2Page.waitForTimeout(2000);
      
      const player2AfterBotRemoval = await investigator.checkUIRoomCount(player2Page, 'Player2', 'after_bot_removal');
      
      await investigator.takeScreenshot(player2Page, 'Player2', 'after_bot_removal', 'After bot removal attempt');
      
      if (player2AfterBotRemoval.displayedCount > 0) {
        investigator.logEvidence('EVIDENCE', '✅ CONFIRMED: Room becomes visible after bot removal', {
          beforeBotRemoval: player2AfterRefresh.displayedCount,
          afterBotRemoval: player2AfterBotRemoval.displayedCount,
          conclusion: 'Room visibility depends on player count being < max_slots'
        });
      }
    } else {
      investigator.logEvidence('SURPRISE', '🤔 Unexpected: Player2 can see the room immediately', {
        displayedCount: player2AfterRefresh.displayedCount,
        note: 'This contradicts our hypothesis - need to investigate further'
      });
    }
    
    console.log('\n=== PHASE 5: EVIDENCE ANALYSIS ===');
    
    // Analyze the WebSocket messages for filtering evidence
    const player2RoomUpdates = player2Messages.filter(m => 
      m.direction === 'received' && m.message.event === 'room_list_update'
    );
    
    investigator.logEvidence('ANALYSIS', 'WebSocket message analysis', {
      player2RoomUpdateCount: player2RoomUpdates.length,
      roomUpdates: player2RoomUpdates.map(update => ({
        timestamp: update.timestamp,
        roomCount: update.message.data?.rooms?.length || 0,
        rooms: update.message.data?.rooms?.map(r => ({
          id: r.room_id,
          players: r.player_count,
          max: r.max_players
        })) || []
      }))
    });
    
    console.log('\n=== INVESTIGATION COMPLETE ===');
    
    // Save all evidence
    const evidenceFile = await investigator.saveEvidence();
    
    // Final summary
    console.log('\n🏁 INVESTIGATION SUMMARY:');
    console.log('📊 Evidence collected:');
    console.log(`   - WebSocket messages captured`);
    console.log(`   - UI screenshots taken`);
    console.log(`   - Player count changes documented`);
    console.log(`   - Timeline of events recorded`);
    console.log(`📁 Full evidence report: ${evidenceFile}`);
    
    // Keep browsers open for manual inspection
    console.log('\n⏱️ Keeping browsers open for 20 seconds for manual inspection...');
    await player1Page.waitForTimeout(20000);
    
  } catch (error) {
    investigator.logEvidence('ERROR', 'Investigation failed', { error: error.message, stack: error.stack });
    console.error('❌ Investigation failed:', error);
  } finally {
    await browser.close();
    console.log('🏁 Investigation completed');
  }
}

// Run the investigation
if (require.main === module) {
  investigateRoomVisibility().catch(console.error);
}

module.exports = { investigateRoomVisibility };