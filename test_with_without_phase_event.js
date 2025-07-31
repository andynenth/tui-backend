#!/usr/bin/env node

/**
 * 🧪 **A/B Comparison Test: With vs Without PhaseChanged Event**
 * 
 * FlowAnalyst Agent - A/B Testing for PhaseChanged Event Fix
 * Task: A/B Comparison Testing (Task 4 from investigation plan)
 * 
 * MISSION: Compare behavior with and without PhaseChanged event emission
 * - Test A: Current implementation (PhaseChanged event enabled)
 * - Test B: Simulated original bug (PhaseChanged event disabled)
 * - Document exact differences in behavior
 * - Provide definitive proof whether fix actually works
 * 
 * SUCCESS CRITERIA:
 * - Clear behavioral difference documented
 * - Navigation timing comparison measured
 * - Side-by-side evidence with videos/screenshots
 * - Definitive answer: Does PhaseChanged event fix the waiting page issue?
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class ABPhaseEventTester {
  constructor() {
    this.testResults = {
      testA: {
        name: 'WITH PhaseChanged Event (Current Implementation)',
        events: [],
        timing: {},
        navigation: null,
        errors: [],
        screenshots: []
      },
      testB: {
        name: 'WITHOUT PhaseChanged Event (Simulated Bug)',
        events: [],
        timing: {},
        navigation: null,
        errors: [],
        screenshots: []
      }
    };
    this.testId = `ab-phase-test-${Date.now()}`;
    this.screenshotDir = `screenshots-${this.testId}`;
  }

  async setupBrowser() {
    console.log('🚀 Starting A/B PhaseChanged Event Test...');
    
    // Create screenshot directory
    if (!fs.existsSync(this.screenshotDir)) {
      fs.mkdirSync(this.screenshotDir);
    }
    
    this.browser = await puppeteer.launch({
      headless: false,
      devtools: false, // Disable devtools to reduce overhead
      args: [
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
        '--no-sandbox',
        '--window-size=1200,800'
      ]
    });

    console.log('✅ Browser setup complete');
  }

  async runTestA() {
    console.log('\n🧪 TEST A: WITH PhaseChanged Event (Current Implementation)');
    console.log('📊 This tests the current fix to see if it works');
    
    const page = await this.browser.newPage();
    const testData = this.testResults.testA;
    
    try {
      await this.setupPageMonitoring(page, 'testA');
      await this.runGameStartFlow(page, testData, 'testA');
    } catch (error) {
      testData.errors.push({
        type: 'test_error',
        message: error.message,
        timestamp: Date.now()
      });
    } finally {
      await page.close();
    }
  }

  async runTestB() {
    console.log('\n🧪 TEST B: WITHOUT PhaseChanged Event (Simulated Bug)');
    console.log('📊 This simulates the original bug by disabling phase events');
    
    const page = await this.browser.newPage();
    const testData = this.testResults.testB;
    
    try {
      // Setup page with phase event interception
      await this.setupPageMonitoring(page, 'testB');
      await this.disablePhaseChangeEvents(page);
      await this.runGameStartFlow(page, testData, 'testB');
    } catch (error) {
      testData.errors.push({
        type: 'test_error',
        message: error.message,
        timestamp: Date.now()
      });
    } finally {
      await page.close();
    }
  }

  async setupPageMonitoring(page, testName) {
    // Monitor console messages
    page.on('console', (msg) => {
      const text = msg.text();
      const testData = this.testResults[testName];
      
      if (text.includes('🎮') || text.includes('🌐') || text.includes('phase')) {
        testData.events.push({
          type: 'console',
          message: text,
          timestamp: Date.now()
        });
      }
    });

    // Monitor errors
    page.on('pageerror', (error) => {
      this.testResults[testName].errors.push({
        type: 'javascript_error',
        message: error.message,
        stack: error.stack,
        timestamp: Date.now()
      });
    });

    // Setup WebSocket monitoring
    await page.evaluateOnNewDocument(() => {
      window.__TEST_EVENTS__ = [];
      window.__GAME_START_TIME__ = null;
      window.__NAVIGATION_TIME__ = null;
      
      // Monitor WebSocket
      const OriginalWebSocket = window.WebSocket;
      window.WebSocket = function(url, protocols) {
        const ws = new OriginalWebSocket(url, protocols);
        
        ws.addEventListener('message', (event) => {
          try {
            const data = JSON.parse(event.data);
            window.__TEST_EVENTS__.push({
              type: 'ws_message',
              event: data.event,
              data: data,
              timestamp: Date.now()
            });
            
            if (data.event === 'game_started') {
              console.log('🎮 CRITICAL: game_started received');
              window.__GAME_START_TIME__ = Date.now();
            }
            
            if (data.event === 'phase_change') {
              console.log(`🔄 CRITICAL: phase_change received - Phase: ${data.data?.phase}`);
            }
          } catch (e) {
            // Ignore parse errors
          }
        });
        
        return ws;
      };
      
      // Monitor navigation
      let lastUrl = window.location.href;
      const checkNavigation = () => {
        if (window.location.href !== lastUrl) {
          const now = Date.now();
          if (window.location.href.includes('/game/') && !window.__NAVIGATION_TIME__) {
            window.__NAVIGATION_TIME__ = now;
            console.log(`🧭 Navigation to game page at ${now}`);
          }
          window.__TEST_EVENTS__.push({
            type: 'navigation',
            from: lastUrl,
            to: window.location.href,
            timestamp: now
          });
          lastUrl = window.location.href;
        }
      };
      
      setInterval(checkNavigation, 100);
    });
  }

  async disablePhaseChangeEvents(page) {
    console.log('🚫 Disabling PhaseChanged events to simulate original bug...');
    
    await page.evaluateOnNewDocument(() => {
      // Intercept and block phase_change events
      const OriginalWebSocket = window.WebSocket;
      window.WebSocket = function(url, protocols) {
        const ws = new OriginalWebSocket(url, protocols);
        
        const originalOnMessage = ws.onmessage;
        const originalAddEventListener = ws.addEventListener;
        
        // Override addEventListener to filter phase_change events
        ws.addEventListener = function(type, listener, options) {
          if (type === 'message') {
            const filteredListener = (event) => {
              try {
                const data = JSON.parse(event.data);
                
                // Block phase_change events to simulate the bug
                if (data.event === 'phase_change') {
                  console.log('🚫 BLOCKED: phase_change event (simulating bug)');
                  window.__TEST_EVENTS__.push({
                    type: 'blocked_event',
                    event: 'phase_change',
                    data: data,
                    timestamp: Date.now()
                  });
                  return; // Don't call the original listener
                }
                
                // Allow other events through
                listener(event);
              } catch (e) {
                listener(event);
              }
            };
            
            return originalAddEventListener.call(this, type, filteredListener, options);
          }
          
          return originalAddEventListener.call(this, type, listener, options);
        };
        
        // Also override direct onmessage assignment
        Object.defineProperty(ws, 'onmessage', {
          set: function(handler) {
            if (handler) {
              const filteredHandler = (event) => {
                try {
                  const data = JSON.parse(event.data);
                  
                  if (data.event === 'phase_change') {
                    console.log('🚫 BLOCKED: phase_change event via onmessage (simulating bug)');
                    window.__TEST_EVENTS__.push({
                      type: 'blocked_event',
                      event: 'phase_change',
                      data: data,
                      timestamp: Date.now()
                    });
                    return;
                  }
                  
                  handler(event);
                } catch (e) {
                  handler(event);
                }
              };
              
              originalOnMessage = filteredHandler;
            }
          },
          get: function() {
            return originalOnMessage;
          }
        });
        
        return ws;
      };
    });
  }

  async runGameStartFlow(page, testData, testName) {
    const startTime = Date.now();
    testData.timing.testStart = startTime;
    
    console.log(`📍 Running game start flow for ${testName}...`);
    
    try {
      // 1. Navigate to start page
      await page.goto('http://localhost:3000', { waitUntil: 'networkidle2' });
      await this.takeScreenshot(page, testName, '01-start-page');
      
      // 2. Enter player name
      await page.waitForSelector('input[placeholder*="name" i]', { timeout: 10000 });
      await page.type('input[placeholder*="name" i]', `ABTester-${testName}`);
      
      await page.click('button[type="submit"]');
      await page.waitForNavigation({ waitUntil: 'networkidle2' });
      await this.takeScreenshot(page, testName, '02-lobby-page');
      
      // 3. Create room
      await page.waitForSelector('button:has-text("Create Room")', { timeout: 10000 });
      await page.click('button:has-text("Create Room")');
      
      await page.waitForNavigation({ waitUntil: 'networkidle2' });
      await this.takeScreenshot(page, testName, '03-room-created');
      
      const roomUrl = page.url();
      const roomId = roomUrl.split('/').pop();
      testData.roomId = roomId;
      
      // 4. Add bots quickly
      console.log(`🤖 Adding bots for ${testName}...`);
      for (let i = 0; i < 3; i++) {
        await page.click('button:has-text("+ Add Bot")');
        await page.waitForTimeout(300);
      }
      
      await this.takeScreenshot(page, testName, '04-bots-added');
      
      // 5. Start game and monitor carefully
      console.log(`🎯 Starting game for ${testName} and monitoring...`);
      testData.timing.gameStartClick = Date.now();
      
      await page.click('button:has-text("Start Game")');
      await this.takeScreenshot(page, testName, '05-game-start-clicked');
      
      // 6. Monitor for 15 seconds to capture behavior
      console.log(`⏰ Monitoring ${testName} for 15 seconds...`);
      
      let navigationCompleted = false;
      let waitingPageDetected = false;
      
      for (let i = 0; i < 150; i++) { // 15 seconds in 100ms intervals
        await page.waitForTimeout(100);
        
        const currentUrl = page.url();
        
        // Check for navigation to game page
        if (currentUrl.includes('/game/') && !navigationCompleted) {
          navigationCompleted = true;
          testData.timing.navigationTime = Date.now();
          testData.navigation = {
            successful: true,
            delay: testData.timing.navigationTime - testData.timing.gameStartClick,
            url: currentUrl
          };
          
          console.log(`🎯 ${testName}: Navigated to game page in ${testData.navigation.delay}ms`);
          await this.takeScreenshot(page, testName, '06-game-page-reached');
        }
        
        // Check if stuck on waiting page
        if (currentUrl.includes('/game/') && !waitingPageDetected) {
          try {
            const waitingIndicator = await page.$('.waiting-dots, h1:contains("Waiting"), div:contains("Waiting")');
            if (waitingIndicator) {
              waitingPageDetected = true;
              console.log(`⏳ ${testName}: Waiting page detected`);
              await this.takeScreenshot(page, testName, '07-waiting-page-detected');
            }
          } catch (e) {
            // Ignore selector errors
          }
        }
        
        // Collect events periodically
        if (i % 10 === 0) { // Every second
          const events = await page.evaluate(() => {
            const events = window.__TEST_EVENTS__ || [];
            const gameStart = window.__GAME_START_TIME__;
            const navTime = window.__NAVIGATION_TIME__;
            window.__TEST_EVENTS__ = []; // Clear collected events
            return { events, gameStart, navTime };
          });
          
          testData.events.push(...events.events);
          
          if (events.gameStart && !testData.timing.gameStartReceived) {
            testData.timing.gameStartReceived = events.gameStart;
          }
          
          if (events.navTime && !testData.timing.frontendNavigation) {
            testData.timing.frontendNavigation = events.navTime;
          }
        }
        
        // Take periodic screenshots during critical period
        if (i === 10) await this.takeScreenshot(page, testName, '08-1-second-after');
        if (i === 30) await this.takeScreenshot(page, testName, '09-3-seconds-after');
        if (i === 50) await this.takeScreenshot(page, testName, '10-5-seconds-after');
        if (i === 100) await this.takeScreenshot(page, testName, '11-10-seconds-after');
      }
      
      // Final screenshot
      await this.takeScreenshot(page, testName, '12-final-state');
      
      // Final event collection
      const finalEvents = await page.evaluate(() => {
        const events = window.__TEST_EVENTS__ || [];
        const gameStart = window.__GAME_START_TIME__;
        const navTime = window.__NAVIGATION_TIME__;
        return { events, gameStart, navTime };
      });
      
      testData.events.push(...finalEvents.events);
      testData.timing.testEnd = Date.now();
      testData.timing.totalDuration = testData.timing.testEnd - testData.timing.testStart;
      
      // Final assessment
      if (!navigationCompleted) {
        testData.navigation = {
          successful: false,
          stuck: true,
          finalUrl: page.url()
        };
        console.log(`❌ ${testName}: Navigation FAILED - stuck on waiting page`);
      }
      
      console.log(`✅ ${testName} monitoring complete`);
      
    } catch (error) {
      console.error(`❌ ${testName} failed:`, error);
      testData.errors.push({
        type: 'flow_error',
        message: error.message,
        timestamp: Date.now()
      });
    }
  }

  async takeScreenshot(page, testName, stage) {
    try {
      const filename = `${this.screenshotDir}/${testName}-${stage}.png`;
      await page.screenshot({ 
        path: filename, 
        fullPage: false,
        clip: { x: 0, y: 0, width: 1200, height: 800 }
      });
      
      this.testResults[testName].screenshots.push({
        stage,
        filename,
        timestamp: Date.now()
      });
    } catch (error) {
      console.warn(`Failed to take screenshot: ${error.message}`);
    }
  }

  generateComparison() {
    const testA = this.testResults.testA;
    const testB = this.testResults.testB;
    
    const comparison = {
      testId: this.testId,
      timestamp: new Date().toISOString(),
      
      testA: {
        name: testA.name,
        navigation: testA.navigation,
        timing: testA.timing,
        eventCounts: this.countEvents(testA.events),
        errors: testA.errors.length,
        screenshots: testA.screenshots.length
      },
      
      testB: {
        name: testB.name,
        navigation: testB.navigation,
        timing: testB.timing,
        eventCounts: this.countEvents(testB.events),
        errors: testB.errors.length,
        screenshots: testB.screenshots.length
      },
      
      differences: this.analyzeDifferences(testA, testB),
      conclusions: this.drawConclusions(testA, testB)
    };
    
    return comparison;
  }

  countEvents(events) {
    const counts = {};
    events.forEach(event => {
      const type = event.event || event.type;
      counts[type] = (counts[type] || 0) + 1;
    });
    return counts;
  }

  analyzeDifferences(testA, testB) {
    const differences = [];
    
    // Navigation differences
    if (testA.navigation?.successful && !testB.navigation?.successful) {
      differences.push('✅ Test A navigated successfully, Test B got stuck');
    } else if (!testA.navigation?.successful && testB.navigation?.successful) {
      differences.push('⚠️ Test B navigated successfully, Test A got stuck (unexpected!)');
    } else if (testA.navigation?.successful && testB.navigation?.successful) {
      differences.push('⚠️ Both tests navigated successfully - may need stronger blocking');
    } else {
      differences.push('❌ Both tests got stuck - PhaseChanged event may not be the issue');
    }
    
    // Timing differences
    if (testA.navigation?.delay && testB.navigation?.delay) {
      const timeDiff = testB.navigation.delay - testA.navigation.delay;
      differences.push(`⏱️ Navigation timing difference: ${timeDiff}ms (B slower than A)`);
    } else if (testA.navigation?.delay && !testB.navigation?.delay) {
      differences.push(`⏱️ Test A navigated in ${testA.navigation.delay}ms, Test B never navigated`);
    }
    
    // Event differences
    const aPhaseEvents = testA.events.filter(e => e.event === 'phase_change').length;
    const bPhaseEvents = testB.events.filter(e => e.event === 'phase_change').length;
    const bBlockedEvents = testB.events.filter(e => e.type === 'blocked_event').length;
    
    differences.push(`📊 Test A received ${aPhaseEvents} phase_change events`);
    differences.push(`📊 Test B received ${bPhaseEvents} phase_change events (${bBlockedEvents} blocked)`);
    
    // Error differences
    if (testA.errors.length !== testB.errors.length) {
      differences.push(`⚠️ Error count difference: A=${testA.errors.length}, B=${testB.errors.length}`);
    }
    
    return differences;
  }

  drawConclusions(testA, testB) {
    const conclusions = [];
    
    // Main hypothesis test
    const aSuccessful = testA.navigation?.successful;
    const bSuccessful = testB.navigation?.successful;
    
    if (aSuccessful && !bSuccessful) {
      conclusions.push('🎯 HYPOTHESIS CONFIRMED: PhaseChanged event fixes the waiting page issue');
      conclusions.push('✅ Test A (with PhaseChanged) navigated successfully');
      conclusions.push('❌ Test B (without PhaseChanged) got stuck on waiting page');
      conclusions.push('📊 This proves the fix is working correctly');
    } else if (!aSuccessful && !bSuccessful) {
      conclusions.push('🤔 HYPOTHESIS UNCLEAR: Both tests failed to navigate');
      conclusions.push('⚠️ This suggests PhaseChanged event alone may not be sufficient');
      conclusions.push('🔍 Additional investigation needed - may be frontend processing issue');
    } else if (aSuccessful && bSuccessful) {
      conclusions.push('⚠️ HYPOTHESIS NOT PROVEN: Both tests navigated successfully');
      conclusions.push('🔍 Event blocking may not have been effective');
      conclusions.push('📊 Need stronger simulation of original bug');
    } else {
      conclusions.push('🚨 UNEXPECTED RESULT: Test B worked better than Test A');
      conclusions.push('⚠️ This suggests our current implementation may have issues');
    }
    
    // Event analysis
    const aPhaseEvents = testA.events.filter(e => e.event === 'phase_change').length;
    const bBlockedEvents = testB.events.filter(e => e.type === 'blocked_event').length;
    
    if (aPhaseEvents > 0) {
      conclusions.push(`✅ Test A received ${aPhaseEvents} PhaseChanged events as expected`);
    } else {
      conclusions.push('❌ Test A did not receive PhaseChanged events - backend issue');
    }
    
    if (bBlockedEvents > 0) {
      conclusions.push(`✅ Test B successfully blocked ${bBlockedEvents} PhaseChanged events`);
    } else {
      conclusions.push('⚠️ Test B event blocking may not have worked');
    }
    
    // Timing analysis
    if (testA.navigation?.delay) {
      if (testA.navigation.delay < 500) {
        conclusions.push(`⚡ Test A navigation was fast: ${testA.navigation.delay}ms`);
      } else if (testA.navigation.delay < 2000) {
        conclusions.push(`⏱️ Test A navigation was moderate: ${testA.navigation.delay}ms`);
      } else {
        conclusions.push(`🐌 Test A navigation was slow: ${testA.navigation.delay}ms`);
      }
    }
    
    // Final verdict
    if (aSuccessful && !bSuccessful && aPhaseEvents > 0 && bBlockedEvents > 0) {
      conclusions.push('\n🏆 FINAL VERDICT: PhaseChanged event fix is WORKING and EFFECTIVE');
      conclusions.push('📊 Evidence: A navigated with events, B stuck without events');
      conclusions.push('✅ The waiting page issue is resolved by the PhaseChanged event');
    } else {
      conclusions.push('\n🤔 FINAL VERDICT: Results are INCONCLUSIVE or PhaseChanged event is NOT the complete solution');
      conclusions.push('🔍 Further investigation required to identify root cause');
    }
    
    return conclusions;
  }

  async saveResults() {
    const comparison = this.generateComparison();
    
    // Save detailed JSON report
    const jsonFile = `ab-phase-test-${this.testId}.json`;
    const fullReport = {
      comparison,
      detailedResults: {
        testA: this.testResults.testA,
        testB: this.testResults.testB
      }
    };
    
    fs.writeFileSync(jsonFile, JSON.stringify(fullReport, null, 2));
    console.log(`📄 Detailed report saved: ${jsonFile}`);
    
    // Save human-readable summary
    const summaryFile = `ab-phase-test-${this.testId}-summary.txt`;
    const summary = this.generateHumanReadableSummary(comparison);
    fs.writeFileSync(summaryFile, summary);
    console.log(`📄 Summary saved: ${summaryFile}`);
    
    return { jsonFile, summaryFile, comparison };
  }

  generateHumanReadableSummary(comparison) {
    let summary = '';
    summary += '🧪 A/B COMPARISON TEST: PhaseChanged Event Fix\n';
    summary += '=' .repeat(60) + '\n\n';
    
    summary += `Test ID: ${comparison.testId}\n`;
    summary += `Timestamp: ${comparison.timestamp}\n\n`;
    
    summary += 'TEST A: WITH PhaseChanged Event (Current Implementation)\n';
    summary += '-'.repeat(50) + '\n';
    summary += `Navigation: ${comparison.testA.navigation?.successful ? 'SUCCESS' : 'FAILED'}\n`;
    if (comparison.testA.navigation?.delay) {
      summary += `Navigation Time: ${comparison.testA.navigation.delay}ms\n`;
    }
    summary += `Total Duration: ${comparison.testA.timing?.totalDuration || 'N/A'}ms\n`;
    summary += `Events Received: ${Object.keys(comparison.testA.eventCounts).length} types\n`;
    summary += `JavaScript Errors: ${comparison.testA.errors}\n`;
    summary += `Screenshots Taken: ${comparison.testA.screenshots}\n\n`;
    
    summary += 'TEST B: WITHOUT PhaseChanged Event (Simulated Bug)\n';
    summary += '-'.repeat(50) + '\n';
    summary += `Navigation: ${comparison.testB.navigation?.successful ? 'SUCCESS' : 'FAILED'}\n`;
    if (comparison.testB.navigation?.delay) {
      summary += `Navigation Time: ${comparison.testB.navigation.delay}ms\n`;
    }
    summary += `Total Duration: ${comparison.testB.timing?.totalDuration || 'N/A'}ms\n`;
    summary += `Events Received: ${Object.keys(comparison.testB.eventCounts).length} types\n`;
    summary += `JavaScript Errors: ${comparison.testB.errors}\n`;
    summary += `Screenshots Taken: ${comparison.testB.screenshots}\n\n`;
    
    summary += 'KEY DIFFERENCES:\n';
    summary += '-'.repeat(30) + '\n';
    comparison.differences.forEach(diff => {
      summary += `${diff}\n`;
    });
    
    summary += '\nCONCLUSIONS:\n';
    summary += '-'.repeat(30) + '\n';
    comparison.conclusions.forEach(conclusion => {
      summary += `${conclusion}\n`;
    });
    
    return summary;
  }

  async cleanup() {
    if (this.browser) {
      await this.browser.close();
    }
  }
}

// Run the A/B test
async function main() {
  const tester = new ABPhaseEventTester();
  
  try {
    await tester.setupBrowser();
    
    console.log('🔬 Running A/B comparison test...');
    console.log('📊 This will take approximately 3-4 minutes');
    
    await tester.runTestA();
    
    console.log('\n⏱️ Waiting 5 seconds between tests...');
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    await tester.runTestB();
    
    const { summaryFile, comparison } = await tester.saveResults();
    
    console.log('\n🎯 A/B TEST COMPLETE!');
    console.log(`📊 Check results in: ${summaryFile}`);
    console.log(`📸 Screenshots saved in: ${tester.screenshotDir}/`);
    
    // Print quick summary
    console.log('\n📋 QUICK RESULTS:');
    comparison.conclusions.forEach(conclusion => {
      console.log(conclusion);
    });
    
  } catch (error) {
    console.error('❌ A/B test failed:', error);
  } finally {
    await tester.cleanup();
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = ABPhaseEventTester;