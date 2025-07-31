#!/usr/bin/env node

/**
 * 🔍 **WebSocket Event Sequence Monitor**
 * 
 * FlowAnalyst Agent - Complete Event Tracing Test
 * Task: Enhanced WebSocket Event Monitoring (Tasks 4 & 5 Combined)
 * 
 * MISSION: Monitor complete WebSocket event sequence with state changes
 * - Log ALL events from game start to navigation
 * - Track phase changes and frontend state transitions
 * - Measure exact timing between events
 * - Record complete trace of events → state → navigation
 * 
 * SUCCESS CRITERIA:
 * - Complete event sequence logged with timestamps
 * - Frontend state changes tracked after each event
 * - Navigation timing measured (< 500ms expected)
 * - Definitive proof whether PhaseChanged event works
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class WebSocketEventSequenceMonitor {
  constructor() {
    this.eventLog = [];
    this.stateChanges = [];
    this.navigationEvents = [];
    this.startTime = null;
    this.gameStartTime = null;
    this.navigationTime = null;
    this.testId = `event-sequence-${Date.now()}`;
    
    // Event counters
    this.eventCounts = {
      websocket: 0,
      phase_change: 0,
      game_started: 0,
      state_changes: 0,
      navigation: 0,
      errors: 0
    };
  }

  logEvent(category, event, data = {}) {
    const timestamp = Date.now();
    const relativeTime = this.startTime ? timestamp - this.startTime : 0;
    
    const logEntry = {
      timestamp,
      relativeTime: `+${relativeTime}ms`,
      category,
      event,
      data: JSON.parse(JSON.stringify(data)), // deep clone
      testId: this.testId
    };
    
    this.eventLog.push(logEntry);
    this.eventCounts[category] = (this.eventCounts[category] || 0) + 1;
    
    console.log(`[${relativeTime.toString().padStart(6)}ms] ${category.toUpperCase()}: ${event}`, 
                data.type || data.phase || data.event || '');
  }

  async setupBrowser() {
    console.log('🚀 Starting WebSocket Event Sequence Monitor...');
    this.startTime = Date.now();
    
    this.browser = await puppeteer.launch({
      headless: false,
      devtools: true,
      args: [
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
        '--no-sandbox'
      ]
    });

    this.page = await this.browser.newPage();
    
    // Enable console logging
    this.page.on('console', (msg) => {
      const text = msg.text();
      
      // Track specific console patterns
      if (text.includes('🎮 GameService') || text.includes('🌐 NetworkService')) {
        this.logEvent('frontend', 'console_log', { message: text, type: msg.type() });
      }
      
      if (text.includes('phase_change') || text.includes('PhaseChanged')) {
        this.logEvent('phase_change', 'frontend_log', { message: text });
      }
      
      // Track navigation-related logs
      if (text.includes('navigation') || text.includes('navigate') || text.includes('game page')) {
        this.logEvent('navigation', 'frontend_log', { message: text });
      }
    });

    // Track JavaScript errors
    this.page.on('pageerror', (error) => {
      this.logEvent('errors', 'javascript_error', { 
        message: error.message,
        stack: error.stack 
      });
    });

    // Intercept WebSocket traffic
    await this.setupWebSocketInterception();
    
    console.log('✅ Browser and monitoring setup complete');
  }

  async setupWebSocketInterception() {
    await this.page.evaluateOnNewDocument(() => {
      // Store original WebSocket
      const OriginalWebSocket = window.WebSocket;
      
      // Create monitoring wrapper
      window.WebSocket = function(url, protocols) {
        const ws = new OriginalWebSocket(url, protocols);
        const wsId = 'ws-' + Math.random().toString(36).substr(2, 9);
        
        console.log(`🔌 WebSocket Created: ${wsId} -> ${url}`);
        
        // Track connection events
        ws.addEventListener('open', (event) => {
          console.log(`🔌 WebSocket Open: ${wsId}`);
          window.__WS_EVENTS__ = window.__WS_EVENTS__ || [];
          window.__WS_EVENTS__.push({
            type: 'open',
            wsId,
            url,
            timestamp: Date.now()
          });
        });
        
        ws.addEventListener('close', (event) => {
          console.log(`🔌 WebSocket Close: ${wsId} - Code: ${event.code}`);
          window.__WS_EVENTS__ = window.__WS_EVENTS__ || [];
          window.__WS_EVENTS__.push({
            type: 'close',
            wsId,
            code: event.code,
            reason: event.reason,
            timestamp: Date.now()
          });
        });
        
        ws.addEventListener('error', (event) => {
          console.log(`🔌 WebSocket Error: ${wsId}`);
          window.__WS_EVENTS__ = window.__WS_EVENTS__ || [];
          window.__WS_EVENTS__.push({
            type: 'error',
            wsId,
            timestamp: Date.now()
          });
        });
        
        // Intercept incoming messages
        ws.addEventListener('message', (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log(`📥 WebSocket Message: ${wsId} -> ${data.event || 'unknown'}`, data);
            
            window.__WS_EVENTS__ = window.__WS_EVENTS__ || [];
            window.__WS_EVENTS__.push({
              type: 'message',
              wsId,
              event: data.event,
              data: data,
              timestamp: Date.now()
            });
            
            // Special handling for critical events
            if (data.event === 'game_started') {
              console.log('🎮 CRITICAL: game_started event received!');
              window.__GAME_START_TIME__ = Date.now();
            }
            
            if (data.event === 'phase_change') {
              console.log(`🔄 CRITICAL: phase_change event received! Phase: ${data.data?.phase || 'unknown'}`);
              window.__PHASE_CHANGES__ = window.__PHASE_CHANGES__ || [];
              window.__PHASE_CHANGES__.push({
                phase: data.data?.phase,
                timestamp: Date.now(),
                data: data.data
              });
            }
            
          } catch (e) {
            console.log(`📥 WebSocket Message (raw): ${wsId}`, event.data);
          }
        });
        
        // Intercept outgoing messages
        const originalSend = ws.send;
        ws.send = function(data) {
          try {
            const parsed = JSON.parse(data);
            console.log(`📤 WebSocket Send: ${wsId} -> ${parsed.event || 'unknown'}`, parsed);
            
            window.__WS_EVENTS__ = window.__WS_EVENTS__ || [];
            window.__WS_EVENTS__.push({
              type: 'send',
              wsId,
              event: parsed.event,
              data: parsed,
              timestamp: Date.now()
            });
          } catch (e) {
            console.log(`📤 WebSocket Send (raw): ${wsId}`, data);
          }
          
          return originalSend.call(this, data);
        };
        
        return ws;
      };
      
      // Also monitor page navigation
      let currentUrl = window.location.href;
      const checkNavigation = () => {
        if (window.location.href !== currentUrl) {
          console.log(`🧭 Navigation detected: ${currentUrl} -> ${window.location.href}`);
          window.__NAVIGATION_EVENTS__ = window.__NAVIGATION_EVENTS__ || [];
          window.__NAVIGATION_EVENTS__.push({
            from: currentUrl,
            to: window.location.href,
            timestamp: Date.now()
          });
          currentUrl = window.location.href;
        }
      };
      
      // Check navigation every 100ms
      setInterval(checkNavigation, 100);
      
      // Also monitor GameService state changes
      setTimeout(() => {
        if (window.__GAME_STATE_HISTORY__) {
          const originalPush = Array.prototype.push;
          window.__GAME_STATE_HISTORY__.push = function(...items) {
            items.forEach(item => {
              console.log(`🎮 GameService State Change: ${item.reason}`, {
                phase: item.newState?.phase,
                isConnected: item.newState?.isConnected
              });
            });
            return originalPush.apply(this, items);
          };
        }
      }, 2000);
    });
  }

  async runCompleteEventSequenceTest() {
    console.log('\n🧪 Starting Complete Event Sequence Test...');
    console.log('📊 Monitoring: WebSocket events, state changes, navigation');
    
    try {
      // 1. Navigate to start page
      await this.page.goto('http://localhost:3000', { waitUntil: 'networkidle2' });
      this.logEvent('navigation', 'start_page_loaded');
      
      // 2. Enter player name and navigate to lobby
      await this.page.waitForSelector('input[placeholder*="name" i]', { timeout: 10000 });
      await this.page.type('input[placeholder*="name" i]', 'EventTester');
      
      await this.page.click('button[type="submit"]');
      await this.page.waitForNavigation({ waitUntil: 'networkidle2' });
      this.logEvent('navigation', 'lobby_page_loaded');
      
      // 3. Create room
      await this.page.waitForSelector('button:has-text("Create Room")', { timeout: 10000 });
      await this.page.click('button:has-text("Create Room")');
      
      await this.page.waitForNavigation({ waitUntil: 'networkidle2' });
      const roomUrl = this.page.url();
      const roomId = roomUrl.split('/').pop();
      this.logEvent('navigation', 'room_page_loaded', { roomId, url: roomUrl });
      
      // 4. Add bots
      console.log('🤖 Adding bots...');
      for (let i = 0; i < 3; i++) {
        await this.page.click('button:has-text("+ Add Bot")');
        await this.page.waitForTimeout(500);
        this.logEvent('websocket', 'bot_added', { botNumber: i + 1 });
      }
      
      // 5. Start monitoring for critical events
      console.log('🎯 Starting game and monitoring WebSocket events...');
      this.gameStartTime = Date.now();
      
      // Start game and monitor events
      await this.page.click('button:has-text("Start Game")');
      this.logEvent('frontend', 'start_game_clicked');
      
      // Monitor for 10 seconds to capture all events
      console.log('⏰ Monitoring events for 10 seconds...');
      for (let i = 0; i < 100; i++) {
        await this.page.waitForTimeout(100);
        
        // Check for navigation to game page
        const currentUrl = this.page.url();
        if (currentUrl.includes('/game/') && !this.navigationTime) {
          this.navigationTime = Date.now();
          const navigationDelay = this.navigationTime - this.gameStartTime;
          this.logEvent('navigation', 'game_page_reached', { 
            delay: navigationDelay, 
            url: currentUrl 
          });
          console.log(`🎯 SUCCESS! Reached game page in ${navigationDelay}ms`);
        }
        
        // Collect WebSocket events
        const wsEvents = await this.page.evaluate(() => {
          const events = window.__WS_EVENTS__ || [];
          window.__WS_EVENTS__ = []; // Clear collected events
          return events;
        });
        
        wsEvents.forEach(event => {
          this.logEvent('websocket', event.type, event);
          
          // Track specific critical events
          if (event.event === 'game_started') {
            this.logEvent('game_started', 'received', event.data);
          }
          
          if (event.event === 'phase_change') {
            this.logEvent('phase_change', 'received', {
              phase: event.data?.data?.phase,
              fullData: event.data
            });
          }
        });
        
        // Collect navigation events  
        const navEvents = await this.page.evaluate(() => {
          const events = window.__NAVIGATION_EVENTS__ || [];
          window.__NAVIGATION_EVENTS__ = []; // Clear collected events
          return events;
        });
        
        navEvents.forEach(event => {
          this.logEvent('navigation', 'url_change', event);
        });
      }
      
      console.log('✅ Event monitoring complete');
      
    } catch (error) {
      this.logEvent('errors', 'test_error', { 
        message: error.message, 
        stack: error.stack 
      });
      console.error('❌ Test failed:', error);
    }
  }

  generateDetailedReport() {
    const report = {
      testId: this.testId,
      summary: {
        totalEvents: this.eventLog.length,
        eventCounts: this.eventCounts,
        testDuration: this.eventLog.length > 0 ? 
          this.eventLog[this.eventLog.length - 1].timestamp - this.eventLog[0].timestamp : 0,
        navigationDelay: this.navigationTime && this.gameStartTime ? 
          this.navigationTime - this.gameStartTime : null
      },
      timeline: this.eventLog,
      analysis: this.analyzeEventSequence(),
      conclusions: this.drawConclusions()
    };
    
    return report;
  }

  analyzeEventSequence() {
    const analysis = {};
    
    // Find critical events
    const gameStartEvents = this.eventLog.filter(e => 
      e.category === 'game_started' || 
      (e.category === 'websocket' && e.data.event === 'game_started')
    );
    
    const phaseChangeEvents = this.eventLog.filter(e => 
      e.category === 'phase_change' || 
      (e.category === 'websocket' && e.data.event === 'phase_change')
    );
    
    const navigationEvents = this.eventLog.filter(e => 
      e.category === 'navigation' && e.event === 'game_page_reached'
    );
    
    analysis.gameStartEvents = gameStartEvents.length;
    analysis.phaseChangeEvents = phaseChangeEvents.length;
    analysis.navigationEvents = navigationEvents.length;
    
    // Calculate timing
    if (gameStartEvents.length > 0 && navigationEvents.length > 0) {
      const gameStart = gameStartEvents[0].timestamp;
      const navigation = navigationEvents[0].timestamp;
      analysis.gameStartToNavigation = navigation - gameStart;
    }
    
    // Check for phase change sequence
    analysis.phaseSequence = phaseChangeEvents.map(e => ({
      phase: e.data?.phase || e.data?.data?.phase,
      timestamp: e.timestamp,
      relativeTime: e.relativeTime
    }));
    
    // Check for errors
    const errors = this.eventLog.filter(e => e.category === 'errors');
    analysis.errors = errors.map(e => ({
      type: e.event,
      message: e.data.message,
      timestamp: e.timestamp
    }));
    
    return analysis;
  }

  drawConclusions() {
    const conclusions = [];
    
    // Check if PhaseChanged event is working
    const phaseEvents = this.eventLog.filter(e => 
      e.category === 'phase_change' || 
      (e.category === 'websocket' && e.data.event === 'phase_change')
    );
    
    if (phaseEvents.length > 0) {
      conclusions.push('✅ PhaseChanged events are being emitted by backend');
    } else {
      conclusions.push('❌ No PhaseChanged events detected - this is the problem!');
    }
    
    // Check navigation timing
    if (this.navigationTime && this.gameStartTime) {
      const delay = this.navigationTime - this.gameStartTime;
      if (delay < 500) {
        conclusions.push(`✅ Fast navigation: ${delay}ms (< 500ms target)`);
      } else if (delay < 2000) {
        conclusions.push(`⚠️ Slow navigation: ${delay}ms (> 500ms but < 2s)`);
      } else {
        conclusions.push(`❌ Very slow navigation: ${delay}ms (> 2s - likely stuck)`);
      }
    } else {
      conclusions.push('❌ Navigation to game page never occurred - user stuck on waiting page');
    }
    
    // Check for JavaScript errors
    const errors = this.eventLog.filter(e => e.category === 'errors');
    if (errors.length > 0) {
      conclusions.push(`⚠️ JavaScript errors detected: ${errors.length} errors`);
      errors.forEach(error => {
        conclusions.push(`   - ${error.data.message}`);
      });
    } else {
      conclusions.push('✅ No JavaScript errors detected');
    }
    
    // Overall assessment
    const hasPhaseEvents = phaseEvents.length > 0;
    const hasNavigation = this.navigationTime !== null;
    const hasErrors = errors.length > 0;
    
    if (hasPhaseEvents && hasNavigation && !hasErrors) {
      conclusions.push('\n🎯 CONCLUSION: PhaseChanged event fix is WORKING correctly');
    } else if (!hasPhaseEvents) {
      conclusions.push('\n🚨 CONCLUSION: PhaseChanged events not emitted - fix is NOT working');
    } else if (!hasNavigation) {
      conclusions.push('\n🚨 CONCLUSION: Navigation not occurring despite events - frontend issue');
    } else if (hasErrors) {
      conclusions.push('\n⚠️ CONCLUSION: Fix partially working but errors preventing proper operation');
    }
    
    return conclusions;
  }

  async saveReport(filename = null) {
    const report = this.generateDetailedReport();
    const reportFile = filename || `websocket-event-sequence-${this.testId}.json`;
    
    fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
    console.log(`📄 Detailed report saved: ${reportFile}`);
    
    // Also save a human-readable summary
    const summaryFile = reportFile.replace('.json', '-summary.txt');
    const summary = this.generateHumanReadableSummary(report);
    fs.writeFileSync(summaryFile, summary);
    console.log(`📄 Summary report saved: ${summaryFile}`);
    
    return { report, summaryFile, reportFile };
  }

  generateHumanReadableSummary(report) {
    let summary = '';
    summary += '🔍 WEBSOCKET EVENT SEQUENCE ANALYSIS REPORT\n';
    summary += '=' .repeat(50) + '\n\n';
    
    summary += `Test ID: ${report.testId}\n`;
    summary += `Total Events: ${report.summary.totalEvents}\n`;
    summary += `Test Duration: ${report.summary.testDuration}ms\n`;
    
    if (report.summary.navigationDelay) {
      summary += `Navigation Delay: ${report.summary.navigationDelay}ms\n`;
    } else {
      summary += `Navigation Delay: NEVER (stuck on waiting page)\n`;
    }
    
    summary += '\nEVENT COUNTS:\n';
    Object.entries(report.summary.eventCounts).forEach(([category, count]) => {
      summary += `  ${category}: ${count}\n`;
    });
    
    summary += '\nCRITICAL EVENT ANALYSIS:\n';
    summary += `  Game Start Events: ${report.analysis.gameStartEvents}\n`;
    summary += `  Phase Change Events: ${report.analysis.phaseChangeEvents}\n`;
    summary += `  Navigation Events: ${report.analysis.navigationEvents}\n`;
    
    if (report.analysis.gameStartToNavigation) {
      summary += `  Game Start → Navigation: ${report.analysis.gameStartToNavigation}ms\n`;
    }
    
    if (report.analysis.phaseSequence.length > 0) {
      summary += '\nPHASE CHANGE SEQUENCE:\n';
      report.analysis.phaseSequence.forEach(phase => {
        summary += `  ${phase.relativeTime}: Phase '${phase.phase}'\n`;
      });
    } else {
      summary += '\nPHASE CHANGE SEQUENCE: NONE DETECTED!\n';
    }
    
    if (report.analysis.errors.length > 0) {
      summary += '\nJAVASCRIPT ERRORS:\n';
      report.analysis.errors.forEach(error => {
        summary += `  ${error.type}: ${error.message}\n`;
      });
    } else {
      summary += '\nJAVASCRIPT ERRORS: None\n';
    }
    
    summary += '\nCONCLUSIONS:\n';
    report.conclusions.forEach(conclusion => {
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

// Run the test
async function main() {
  const monitor = new WebSocketEventSequenceMonitor();
  
  try {
    await monitor.setupBrowser();
    await monitor.runCompleteEventSequenceTest();
    
    const { summaryFile } = await monitor.saveReport();
    
    console.log('\n🎯 TEST COMPLETE!');
    console.log(`📊 Check the results in: ${summaryFile}`);
    
    // Print summary to console
    const report = monitor.generateDetailedReport();
    console.log('\n📋 QUICK SUMMARY:');
    report.conclusions.forEach(conclusion => {
      console.log(conclusion);
    });
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await monitor.cleanup();
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = WebSocketEventSequenceMonitor;