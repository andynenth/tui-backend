const { test, expect, chromium } = require('@playwright/test');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const BASE_URL = 'http://localhost:5050';
const ROOM_NAME = `MPRoom_${Date.now()}`;
const PLAYER_NAMES = ['Alice', 'Bob', 'Charlie', 'David'];
const SCREENSHOT_DIR = './test-screenshots-multiplayer';

test.describe('Multiplayer Lobby to Game Transition', () => {
  test.beforeAll(async () => {
    await fs.mkdir(SCREENSHOT_DIR, { recursive: true });
  });

  test('Simulate 4 real players joining and starting game', async () => {
    console.log('=== Starting Multiplayer Transition Test ===');
    
    const browser = await chromium.launch({ headless: false });
    const players = [];
    let roomCode = null;
    
    try {
      // Create 4 browser contexts (one for each player)
      for (let i = 0; i < 4; i++) {
        const context = await browser.newContext({
          viewport: { width: 1280, height: 720 }
        });
        const page = await context.newPage();
        
        // Set up WebSocket monitoring for each player
        await setupWebSocketMonitoring(page, PLAYER_NAMES[i]);
        
        players.push({ context, page, name: PLAYER_NAMES[i], events: [] });
      }
      
      // Player 1: Create room
      console.log('Player 1: Creating room...');
      const player1 = players[0];
      await player1.page.goto(BASE_URL);
      await player1.page.fill('input[placeholder="Enter your name"]', player1.name);
      await player1.page.click('button:has-text("Create Room")');
      
      // Wait for room creation and get room code
      await player1.page.waitForURL(/\/room\/.+/);
      roomCode = player1.page.url().split('/').pop();
      console.log(`Room created with code: ${roomCode}`);
      
      await player1.page.screenshot({ 
        path: path.join(SCREENSHOT_DIR, 'player1-room-created.png') 
      });
      
      // Players 2-4: Join room
      for (let i = 1; i < 4; i++) {
        console.log(`Player ${i + 1}: Joining room...`);
        const player = players[i];
        
        await player.page.goto(BASE_URL);
        await player.page.fill('input[placeholder="Enter your name"]', player.name);
        await player.page.fill('input[placeholder="Enter room code"]', roomCode);
        await player.page.click('button:has-text("Join Room")');
        
        // Wait for navigation to room
        await player.page.waitForURL(`**/room/${roomCode}`);
        await player.page.waitForTimeout(1000);
        
        await player.page.screenshot({ 
          path: path.join(SCREENSHOT_DIR, `player${i + 1}-joined.png`) 
        });
      }
      
      // Wait for all players to be visible in all contexts
      console.log('Waiting for all players to sync...');
      await Promise.all(players.map(async (player) => {
        for (const name of PLAYER_NAMES) {
          await player.page.waitForSelector(`text=${name}`, { timeout: 10000 });
        }
      }));
      
      console.log('All players synced. Taking screenshots...');
      await takeScreenshots(players, 'all-players-ready');
      
      // Player 1 (host) clicks start
      console.log('Host clicking start button...');
      const startButton = player1.page.locator('button:has-text("Start Game")');
      await expect(startButton).toBeVisible();
      await expect(startButton).toBeEnabled();
      
      // Set up monitoring for game transition
      const transitionPromises = players.map(player => 
        monitorGameTransition(player.page, player.name)
      );
      
      // Click start
      await startButton.click();
      
      // Wait for transitions with timeout
      console.log('Waiting for game transitions...');
      const results = await Promise.allSettled(transitionPromises);
      
      // Analyze results
      console.log('\n=== TRANSITION RESULTS ===');
      results.forEach((result, i) => {
        const player = players[i];
        if (result.status === 'fulfilled') {
          console.log(`${player.name}: ${result.value.success ? 'SUCCESS' : 'FAILED'}`);
          console.log(`  - Final URL: ${result.value.finalUrl}`);
          console.log(`  - Transition time: ${result.value.transitionTime}ms`);
          console.log(`  - Events received: ${result.value.eventCount}`);
        } else {
          console.log(`${player.name}: ERROR - ${result.reason}`);
        }
      });
      
      // Take final screenshots
      await takeScreenshots(players, 'final-state');
      
      // Collect and analyze WebSocket events from all players
      const allEvents = await collectAllEvents(players);
      await generateMultiplayerReport(roomCode, players, allEvents, results);
      
    } finally {
      // Clean up
      for (const player of players) {
        await player.context.close();
      }
      await browser.close();
    }
  });
});

async function setupWebSocketMonitoring(page, playerName) {
  await page.addInitScript((name) => {
    window.playerName = name;
    window.wsEvents = [];
    window.transitionDetected = false;
    
    const OriginalWebSocket = window.WebSocket;
    window.WebSocket = class WebSocket extends OriginalWebSocket {
      constructor(url, protocols) {
        super(url, protocols);
        
        this.addEventListener('message', (event) => {
          let data;
          try {
            data = JSON.parse(event.data);
          } catch (e) {
            data = event.data;
          }
          
          const eventData = {
            time: new Date().toISOString(),
            player: window.playerName,
            type: 'message',
            data: data
          };
          
          window.wsEvents.push(eventData);
          
          // Detect game_started event
          if (data.type === 'game_started') {
            window.transitionDetected = true;
            console.log(`[${window.playerName}] Game started event received!`);
          }
        });
        
        const originalSend = this.send.bind(this);
        this.send = (data) => {
          let parsedData;
          try {
            parsedData = JSON.parse(data);
          } catch (e) {
            parsedData = data;
          }
          
          window.wsEvents.push({
            time: new Date().toISOString(),
            player: window.playerName,
            type: 'send',
            data: parsedData
          });
          
          return originalSend(data);
        };
      }
    };
  }, playerName);
}

async function monitorGameTransition(page, playerName) {
  const startTime = Date.now();
  const timeout = 30000;
  
  return new Promise((resolve) => {
    const checkInterval = setInterval(async () => {
      try {
        // Check URL
        const currentUrl = page.url();
        if (currentUrl.includes('/game/')) {
          clearInterval(checkInterval);
          
          const events = await page.evaluate(() => window.wsEvents);
          resolve({
            success: true,
            player: playerName,
            finalUrl: currentUrl,
            transitionTime: Date.now() - startTime,
            eventCount: events.length,
            events: events
          });
          return;
        }
        
        // Check for transition detection
        const transitionDetected = await page.evaluate(() => window.transitionDetected);
        if (transitionDetected) {
          // Give it a bit more time to navigate
          await page.waitForTimeout(2000);
          const finalUrl = page.url();
          clearInterval(checkInterval);
          
          const events = await page.evaluate(() => window.wsEvents);
          resolve({
            success: finalUrl.includes('/game/'),
            player: playerName,
            finalUrl: finalUrl,
            transitionTime: Date.now() - startTime,
            eventCount: events.length,
            events: events,
            note: 'Game started event received'
          });
          return;
        }
        
        // Check for timeout
        if (Date.now() - startTime > timeout) {
          clearInterval(checkInterval);
          const events = await page.evaluate(() => window.wsEvents);
          resolve({
            success: false,
            player: playerName,
            finalUrl: page.url(),
            transitionTime: timeout,
            eventCount: events.length,
            events: events,
            error: 'Timeout waiting for game transition'
          });
        }
      } catch (error) {
        clearInterval(checkInterval);
        resolve({
          success: false,
          player: playerName,
          error: error.message
        });
      }
    }, 500);
  });
}

async function takeScreenshots(players, prefix) {
  await Promise.all(players.map(async (player, i) => {
    await player.page.screenshot({
      path: path.join(SCREENSHOT_DIR, `${prefix}-player${i + 1}-${player.name}.png`),
      fullPage: true
    });
  }));
}

async function collectAllEvents(players) {
  const allEvents = [];
  
  for (const player of players) {
    const events = await player.page.evaluate(() => window.wsEvents || []);
    allEvents.push(...events);
  }
  
  // Sort by timestamp
  allEvents.sort((a, b) => new Date(a.time) - new Date(b.time));
  
  return allEvents;
}

async function generateMultiplayerReport(roomCode, players, allEvents, results) {
  const report = {
    timestamp: new Date().toISOString(),
    roomCode: roomCode,
    
    summary: {
      totalPlayers: players.length,
      successfulTransitions: results.filter(r => r.status === 'fulfilled' && r.value.success).length,
      failedTransitions: results.filter(r => r.status === 'rejected' || (r.status === 'fulfilled' && !r.value.success)).length,
      totalEvents: allEvents.length
    },
    
    playerResults: results.map((result, i) => ({
      player: players[i].name,
      status: result.status,
      success: result.status === 'fulfilled' ? result.value.success : false,
      details: result.status === 'fulfilled' ? result.value : { error: result.reason }
    })),
    
    eventAnalysis: {
      byType: countEventTypes(allEvents),
      byPlayer: players.map(p => ({
        player: p.name,
        eventCount: allEvents.filter(e => e.player === p.name).length
      })),
      gameStartedEvents: allEvents.filter(e => e.data?.type === 'game_started'),
      startGameRequests: allEvents.filter(e => e.type === 'send' && e.data?.type === 'start_game')
    },
    
    issues: identifyMultiplayerIssues(results, allEvents)
  };
  
  const reportPath = path.join(SCREENSHOT_DIR, 'multiplayer-report.json');
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
  
  console.log('\n=== MULTIPLAYER TEST REPORT ===');
  console.log(`Room Code: ${report.roomCode}`);
  console.log(`Successful Transitions: ${report.summary.successfulTransitions}/${report.summary.totalPlayers}`);
  console.log(`Total Events: ${report.summary.totalEvents}`);
  
  if (report.issues.length > 0) {
    console.log('\nIdentified Issues:');
    report.issues.forEach((issue, i) => {
      console.log(`${i + 1}. ${issue}`);
    });
  }
  
  console.log(`\nFull report saved to: ${reportPath}`);
}

function countEventTypes(events) {
  const types = {};
  events.forEach(event => {
    const type = event.data?.type || event.type;
    types[type] = (types[type] || 0) + 1;
  });
  return types;
}

function identifyMultiplayerIssues(results, events) {
  const issues = [];
  
  // Check if any players failed to transition
  const failedPlayers = results.filter(r => 
    r.status === 'rejected' || (r.status === 'fulfilled' && !r.value.success)
  );
  
  if (failedPlayers.length > 0) {
    issues.push(`${failedPlayers.length} player(s) failed to transition to game page`);
  }
  
  // Check for inconsistent transitions
  const successfulResults = results.filter(r => r.status === 'fulfilled' && r.value.success);
  if (successfulResults.length > 0 && successfulResults.length < results.length) {
    issues.push('Inconsistent transitions - some players reached game page while others did not');
  }
  
  // Check for missing game_started events
  const gameStartedEvents = events.filter(e => e.data?.type === 'game_started');
  const uniquePlayers = new Set(gameStartedEvents.map(e => e.player));
  
  if (uniquePlayers.size < 4) {
    issues.push(`Only ${uniquePlayers.size}/4 players received game_started event`);
  }
  
  // Check timing issues
  if (gameStartedEvents.length > 0) {
    const firstEvent = new Date(gameStartedEvents[0].time);
    const lastEvent = new Date(gameStartedEvents[gameStartedEvents.length - 1].time);
    const timeDiff = lastEvent - firstEvent;
    
    if (timeDiff > 5000) {
      issues.push(`Large time gap (${timeDiff}ms) between first and last game_started events`);
    }
  }
  
  return issues;
}