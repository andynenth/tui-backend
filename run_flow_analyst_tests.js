#!/usr/bin/env node

/**
 * 🕵️ **FlowAnalyst Agent Test Runner**
 * 
 * Enhanced WebSocket Event Monitoring and A/B Testing Suite
 * 
 * This script runs both critical tests to provide definitive evidence
 * on whether the PhaseChanged event fix actually works:
 * 
 * 1. Complete WebSocket Event Sequence Monitoring
 * 2. A/B Comparison Testing (With vs Without PhaseChanged event)
 * 
 * MISSION: Provide definitive proof of fix effectiveness
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

class FlowAnalystTestRunner {
  constructor() {
    this.testResults = {};
    this.sessionId = `flow-analyst-${Date.now()}`;
  }

  async runTest(scriptName, testName) {
    console.log(`\n🚀 Starting ${testName}...`);
    console.log(`📍 Script: ${scriptName}`);
    console.log(`⏰ Time: ${new Date().toLocaleTimeString()}`);
    
    return new Promise((resolve, reject) => {
      const child = spawn('node', [scriptName], {
        stdio: 'inherit',
        cwd: process.cwd()
      });
      
      child.on('close', (code) => {
        if (code === 0) {
          console.log(`✅ ${testName} completed successfully`);
          resolve({ success: true, exitCode: code });
        } else {
          console.log(`❌ ${testName} failed with exit code ${code}`);
          resolve({ success: false, exitCode: code });
        }
      });
      
      child.on('error', (error) => {
        console.error(`❌ ${testName} error:`, error);
        reject(error);
      });
    });
  }

  async checkPrerequisites() {
    console.log('🔍 Checking prerequisites...');
    
    // Check if test files exist
    const testFiles = [
      'test_websocket_event_sequence.js',
      'test_with_without_phase_event.js'
    ];
    
    for (const file of testFiles) {
      if (!fs.existsSync(file)) {
        throw new Error(`Test file not found: ${file}`);
      }
    }
    
    // Check if puppeteer is available
    try {
      require('puppeteer');
      console.log('✅ Puppeteer is available');
    } catch (error) {
      console.log('❌ Puppeteer not found. Installing...');
      console.log('Please run: npm install puppeteer');
      throw new Error('Puppeteer not available');
    }
    
    // Check if server is running
    console.log('🌐 Make sure the game server is running on http://localhost:3000');
    console.log('   If not, run: npm start (in frontend) and python main.py (in backend)');
    
    console.log('✅ Prerequisites check complete');
  }

  generateOverallReport() {
    const timestamp = new Date().toISOString();
    const report = {
      sessionId: this.sessionId,
      timestamp,
      testSuite: 'FlowAnalyst Enhanced WebSocket Event Monitoring and A/B Testing',
      objective: 'Determine if PhaseChanged event fix actually resolves waiting page issue',
      results: this.testResults,
      summary: this.generateSummary(),
      recommendations: this.generateRecommendations()
    };
    
    return report;
  }

  generateSummary() {
    const summary = [];
    
    if (this.testResults.eventSequence) {
      if (this.testResults.eventSequence.success) {
        summary.push('✅ WebSocket Event Sequence Monitoring completed successfully');
      } else {
        summary.push('❌ WebSocket Event Sequence Monitoring failed');
      }
    }
    
    if (this.testResults.abTest) {
      if (this.testResults.abTest.success) {
        summary.push('✅ A/B Comparison Testing completed successfully');
      } else {
        summary.push('❌ A/B Comparison Testing failed');
      }
    }
    
    return summary;
  }

  generateRecommendations() {
    const recommendations = [];
    
    recommendations.push('📊 Review the generated reports for detailed event logs');
    recommendations.push('📸 Check screenshots for visual evidence of behavior');
    recommendations.push('🔍 Look for PhaseChanged events in WebSocket logs');
    recommendations.push('⏱️ Compare navigation timing between tests');
    
    if (this.testResults.eventSequence?.success && this.testResults.abTest?.success) {
      recommendations.push('🎯 Both tests completed - you have definitive evidence');
      recommendations.push('📋 Check summary files for conclusions');
    } else {
      recommendations.push('⚠️ Some tests failed - check error logs');
      recommendations.push('🔧 Ensure game server is running and accessible');
    }
    
    return recommendations;
  }

  async run() {
    console.log('🕵️ FlowAnalyst Agent - Enhanced WebSocket Event Monitoring');
    console.log('=' .repeat(70));
    console.log('Mission: Provide definitive evidence on PhaseChanged event fix effectiveness');
    console.log('');
    console.log('Tests to run:');
    console.log('  1. Complete WebSocket Event Sequence Monitoring');
    console.log('  2. A/B Comparison Testing (With vs Without PhaseChanged event)');
    console.log('');
    
    try {
      await this.checkPrerequisites();
      
      console.log('\n📋 Starting test suite...');
      console.log('⚠️  Make sure game server is running before proceeding!');
      console.log('⏰ Total estimated time: 5-7 minutes');
      
      // Wait for user confirmation
      console.log('\nPress Enter to continue or Ctrl+C to cancel...');
      await new Promise(resolve => {
        process.stdin.once('data', resolve);
      });
      
      // Test 1: WebSocket Event Sequence Monitoring
      this.testResults.eventSequence = await this.runTest(
        './test_websocket_event_sequence.js',
        'WebSocket Event Sequence Monitoring'
      );
      
      // Wait between tests
      console.log('\n⏱️ Waiting 3 seconds between tests...');
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Test 2: A/B Comparison Testing
      this.testResults.abTest = await this.runTest(
        './test_with_without_phase_event.js',
        'A/B Comparison Testing'
      );
      
      // Generate overall report
      const report = this.generateOverallReport();
      const reportFile = `flow-analyst-report-${this.sessionId}.json`;
      fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
      
      // Generate summary
      const summaryFile = `flow-analyst-summary-${this.sessionId}.txt`;
      let summary = '';
      summary += '🕵️ FLOWANALYST AGENT - FINAL INVESTIGATION REPORT\n';
      summary += '=' .repeat(60) + '\n\n';
      summary += `Session ID: ${report.sessionId}\n`;
      summary += `Timestamp: ${report.timestamp}\n\n`;
      summary += 'MISSION: Determine if PhaseChanged event fix resolves waiting page issue\n\n';
      
      summary += 'TEST RESULTS:\n';
      summary += '-' .repeat(30) + '\n';
      report.summary.forEach(item => {
        summary += `${item}\n`;
      });
      
      summary += '\nRECOMMENDations:\n';
      summary += '-' .repeat(30) + '\n';
      report.recommendations.forEach(item => {
        summary += `${item}\n`;
      });
      
      summary += '\nNEXT STEPS:\n';
      summary += '-' .repeat(30) + '\n';
      summary += '1. Review detailed test reports:\n';
      summary += '   - websocket-event-sequence-*-summary.txt\n';
      summary += '   - ab-phase-test-*-summary.txt\n\n';
      summary += '2. Check screenshots in screenshots-* directories\n\n';
      summary += '3. Look for PhaseChanged events in WebSocket logs\n\n';
      summary += '4. Compare navigation timing and behavior differences\n\n';
      
      if (this.testResults.eventSequence?.success && this.testResults.abTest?.success) {
        summary += '🎯 INVESTIGATION COMPLETE: You now have definitive evidence!\n';
      } else {
        summary += '⚠️  Some tests failed - investigation may need repeat runs\n';
      }
      
      fs.writeFileSync(summaryFile, summary);
      
      console.log('\n🎯 FLOWANALYST INVESTIGATION COMPLETE!');
      console.log('=' .repeat(50));
      console.log(`📊 Overall report: ${reportFile}`);
      console.log(`📋 Summary: ${summaryFile}`);
      console.log('');
      console.log('FINAL EVIDENCE:');
      report.summary.forEach(item => {
        console.log(`  ${item}`);
      });
      
      console.log('');
      console.log('📁 Check these files for detailed evidence:');
      
      // List all generated files
      const files = fs.readdirSync('.')
        .filter(f => 
          f.includes('websocket-event-sequence') || 
          f.includes('ab-phase-test') ||
          f.includes('screenshots-')
        )
        .sort();
      
      files.forEach(file => {
        console.log(`   📄 ${file}`);
      });
      
    } catch (error) {
      console.error('\n❌ FlowAnalyst investigation failed:', error.message);
      console.log('\n🔧 Troubleshooting:');
      console.log('   1. Ensure the game server is running (npm start + python main.py)');
      console.log('   2. Install dependencies: npm install puppeteer');
      console.log('   3. Check that http://localhost:3000 is accessible');
      process.exit(1);
    }
  }
}

// Run the test suite
if (require.main === module) {
  const runner = new FlowAnalystTestRunner();
  runner.run().catch(console.error);
}

module.exports = FlowAnalystTestRunner;