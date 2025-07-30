const fs = require('fs').promises;
const path = require('path');

class TimelineAnalyzer {
  constructor(reportPath) {
    this.reportPath = reportPath;
  }

  async analyze() {
    const data = JSON.parse(await fs.readFile(this.reportPath, 'utf-8'));
    
    console.log('🔍 WebSocket Timeline Analysis');
    console.log('==============================\n');

    this.printSummary(data.summary);
    this.printTimeline(data.timeline);
    this.analyzeWebSocketFlow(data.wsMessages);
    this.printIssues(data.analysis);
    this.generateVisualTimeline(data.timeline);
  }

  printSummary(summary) {
    console.log('📊 Summary:');
    console.log(`- Total Events: ${summary.totalEvents}`);
    console.log(`- WebSocket Messages: ${summary.totalWsMessages}`);
    console.log(`- Duration: ${summary.duration}ms`);
    console.log(`- Start Time: ${summary.startTime}\n`);
  }

  printTimeline(timeline) {
    console.log('📅 Event Timeline:');
    console.log('==================');
    
    timeline.forEach(event => {
      const marker = event.source === 'websocket' ? '🔌' : '📱';
      const time = `${event.timestamp}ms`.padEnd(8);
      console.log(`${marker} [${time}] ${event.type}`);
      
      if (event.data && typeof event.data === 'object') {
        if (event.data.type) {
          console.log(`     └─ Type: ${event.data.type}`);
        }
        if (event.data.payload) {
          console.log(`     └─ Payload: ${JSON.stringify(event.data.payload).substring(0, 100)}`);
        }
      }
    });
    console.log('');
  }

  analyzeWebSocketFlow(wsMessages) {
    console.log('🔌 WebSocket Flow Analysis:');
    console.log('==========================');
    
    // Group messages by type
    const messageTypes = {};
    wsMessages.forEach(msg => {
      if (msg.parsed?.type) {
        const type = msg.parsed.type;
        if (!messageTypes[type]) {
          messageTypes[type] = { sent: 0, received: 0, messages: [] };
        }
        messageTypes[type][msg.direction]++;
        messageTypes[type].messages.push({
          timestamp: msg.timestamp,
          direction: msg.direction,
          payload: msg.parsed.payload
        });
      }
    });

    Object.entries(messageTypes).forEach(([type, data]) => {
      console.log(`\n📨 ${type}:`);
      console.log(`   Sent: ${data.sent}, Received: ${data.received}`);
      data.messages.forEach(msg => {
        console.log(`   ${msg.direction === 'sent' ? '→' : '←'} [${msg.timestamp}ms]`);
      });
    });

    // Check for message patterns
    console.log('\n🔍 Message Patterns:');
    
    // Check if start_game was sent
    const startGameSent = wsMessages.find(m => 
      m.direction === 'sent' && m.parsed?.type === 'start_game'
    );
    console.log(`- start_game sent: ${startGameSent ? `Yes (at ${startGameSent.timestamp}ms)` : 'No'}`);
    
    // Check if game_started was received
    const gameStartedReceived = wsMessages.find(m => 
      m.direction === 'received' && m.parsed?.type === 'game_started'
    );
    console.log(`- game_started received: ${gameStartedReceived ? `Yes (at ${gameStartedReceived.timestamp}ms)` : 'No'}`);
    
    // Check response time
    if (startGameSent && gameStartedReceived) {
      const responseTime = gameStartedReceived.timestamp - startGameSent.timestamp;
      console.log(`- Response time: ${responseTime}ms`);
    }
    
    console.log('');
  }

  printIssues(analysis) {
    console.log('⚠️  Identified Issues:');
    console.log('====================');
    
    if (analysis.missingEvents.length > 0) {
      console.log('\n❌ Missing Expected Events:');
      analysis.missingEvents.forEach(event => {
        console.log(`   - ${event}`);
      });
    }
    
    if (analysis.potentialIssues.length > 0) {
      console.log('\n🔴 Potential Issues:');
      analysis.potentialIssues.forEach(issue => {
        console.log(`   - ${issue}`);
      });
    }
    
    if (analysis.stateTransitions.length > 0) {
      console.log('\n🔄 State Transitions:');
      analysis.stateTransitions.forEach(transition => {
        console.log(`   - ${transition.event} at ${transition.timestamp}ms`);
        console.log(`     Navigation followed: ${transition.hasNavigationFollowed ? 'Yes' : 'No'}`);
      });
    }
  }

  generateVisualTimeline(timeline) {
    console.log('\n📈 Visual Timeline:');
    console.log('==================');
    
    const maxTime = Math.max(...timeline.map(e => e.timestamp));
    const scale = 50; // characters wide
    
    timeline.forEach(event => {
      const position = Math.floor((event.timestamp / maxTime) * scale);
      const bar = '─'.repeat(position) + '●';
      const label = `${event.type} (${event.timestamp}ms)`;
      
      if (event.source === 'websocket') {
        console.log(`WS  ${bar} ${label}`);
      } else {
        console.log(`APP ${bar} ${label}`);
      }
    });
  }
}

// Check if report file is provided
if (process.argv.length < 3) {
  console.log('Usage: node analyze_ws_timeline.js <report-file.json>');
  console.log('\nThis will analyze a WebSocket debug report generated by test_websocket_debug.js');
  process.exit(1);
}

const reportPath = process.argv[2];

// Run analysis
const analyzer = new TimelineAnalyzer(reportPath);
analyzer.analyze().catch(console.error);