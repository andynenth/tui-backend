# AI Guide: Using Playwright MCP for Testing (Updated 2025)

## Table of Contents
1. [Overview](#overview)
2. [What's New in 2025](#whats-new-in-2025)
3. [Installation & Setup](#installation--setup)
4. [Core Architecture](#core-architecture)
5. [Available MCP Tools](#available-mcp-tools)
6. [Test Structure Patterns](#test-structure-patterns)
7. [Accessibility Tree Navigation](#accessibility-tree-navigation)
8. [WebSocket Message Capture](#websocket-message-capture)
9. [Multi-Browser Testing](#multi-browser-testing)
10. [Common Testing Scenarios](#common-testing-scenarios)
11. [Debugging & Analysis](#debugging--analysis)
12. [Best Practices](#best-practices)
13. [Real-World Example](#real-world-example)
14. [Performance Optimization](#performance-optimization)
15. [Troubleshooting](#troubleshooting)

## Overview

Playwright MCP (Model Context Protocol) is a revolutionary approach to browser automation that enables AI assistants to create sophisticated browser tests using structured accessibility data instead of visual pixels. Launched by Microsoft in March 2025, it represents a paradigm shift in how AI interacts with web applications.

### Key Advantages
- **Accessibility Tree-Based**: Uses semantic web structure, not screenshots
- **LLM-Friendly**: No vision models required, operates on structured data
- **Deterministic**: Avoids ambiguity from visual approaches
- **Cross-Browser**: Supports Chromium, Firefox, WebKit, and Edge
- **Performance**: 3-5x faster than traditional screenshot-based automation

## What's New in 2025

### Major Updates
1. **Accessibility Snapshot Mode**: Default mode using browser's accessibility tree
2. **Enhanced MCP Tools**: New tools for tabs, drag-and-drop, hover, and more
3. **Vision Mode**: Optional mode for visual elements not in accessibility tree
4. **PDF Support**: Direct PDF generation from pages
5. **Multi-Tab Management**: Native support for tab operations
6. **Advanced Network Control**: Enhanced request interception and modification

### Community Growth
- ExecuteAutomation's enhanced MCP server with API testing
- CloudFlare's fork for browser rendering integration
- VS Code GitHub Copilot integration
- Growing ecosystem with 50+ community extensions

## Installation & Setup

### 1. Install Playwright MCP

```bash
# Basic installation
claude mcp add playwright npx @playwright/mcp@latest

# With specific browser
claude mcp add playwright npx @playwright/mcp@latest --browser chromium

# With headless mode
claude mcp add playwright npx @playwright/mcp@latest --headless

# With custom capabilities
claude mcp add playwright npx @playwright/mcp@latest --caps vision,pdf
```

### 2. Configuration Options

```javascript
// MCP configuration in claude_desktop_config.json
{
  "playwright": {
    "command": "npx",
    "args": ["@playwright/mcp@latest"],
    "env": {
      "PLAYWRIGHT_BROWSERS_PATH": "~/.cache/playwright",
      "PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD": "0"
    },
    "options": {
      "--allowed-origins": "http://localhost:*;https://example.com",
      "--blocked-origins": "https://malicious.com",
      "--caps": "vision,pdf",
      "--user-data-dir": "./playwright-profile"
    }
  }
}
```

### 3. Verify Installation

```bash
# Check if MCP server is running
claude mcp status

# List available tools
/mcp tools

# Test browser launch
/mcp run browser_navigate --url "https://example.com"
```

## Core Architecture

### Accessibility Tree vs Visual Mode

```javascript
// Accessibility Tree Mode (Default - Fast & Reliable)
// Uses structured DOM representation
{
  role: "button",
  name: "Submit",
  value: "",
  description: "",
  keyboardShortcut: "",
  roledescription: "",
  valuetext: "",
  disabled: false,
  expanded: false,
  focused: false,
  modal: false,
  multiline: false,
  multiselectable: false,
  readonly: false,
  required: false,
  selected: false,
  checked: false,
  pressed: false,
  level: 0,
  valuemin: 0,
  valuemax: 0,
  autocomplete: "",
  haspopup: "",
  invalid: "",
  orientation: "",
  children: []
}

// Vision Mode (Optional - For Visual Elements)
// Requires --caps vision flag
// Uses coordinate-based interactions for elements not in accessibility tree
```

## Available MCP Tools

### Navigation Tools

#### browser_navigate
Navigate to a URL with advanced options.

```javascript
// Parameters:
{
  url: "https://example.com",         // Required
  waitUntil: "networkidle",          // Optional: "load" | "domcontentloaded" | "networkidle"
  timeout: 30000,                    // Optional: Navigation timeout in ms
  referer: "https://google.com"      // Optional: Referer header
}

// Example usage:
await mcp.browser_navigate({
  url: "https://app.example.com",
  waitUntil: "networkidle"
});
```

#### browser_navigate_back / browser_navigate_forward
Navigate through browser history.

```javascript
// Go back
await mcp.browser_navigate_back();

// Go forward  
await mcp.browser_navigate_forward();
```

### Interaction Tools

#### browser_click
Click elements using accessibility references.

```javascript
// Parameters:
{
  element: "Submit button",           // Human-readable description
  ref: "button-123",                 // Exact element reference from snapshot
  button: "left",                    // Optional: "left" | "right" | "middle"
  clickCount: 1,                     // Optional: Number of clicks
  modifiers: ["Control", "Shift"]    // Optional: Keyboard modifiers
}

// Example:
await mcp.browser_click({
  element: "Login button",
  ref: "button-login-main"
});
```

#### browser_type
Type text into elements with advanced options.

```javascript
// Parameters:
{
  element: "Email input field",       // Human-readable description
  ref: "input-email",                // Element reference
  text: "user@example.com",          // Text to type
  delay: 100,                        // Optional: Delay between keystrokes
  clear: true                        // Optional: Clear field before typing
}
```

#### browser_drag
Drag and drop between elements.

```javascript
// Parameters:
{
  startElement: "Draggable item",
  startRef: "item-123",
  endElement: "Drop zone", 
  endRef: "dropzone-456",
  steps: 5                           // Optional: Number of intermediate steps
}
```

#### browser_hover
Hover over elements.

```javascript
// Parameters:
{
  element: "Menu item",
  ref: "menu-products",
  modifiers: []                      // Optional: Keyboard modifiers
}
```

#### browser_select_option
Select dropdown options.

```javascript
// Parameters:
{
  element: "Country dropdown",
  ref: "select-country",
  values: ["United States", "Canada"], // Can select multiple if multi-select
  byValue: false,                     // Optional: Select by value attribute
  byIndex: false                      // Optional: Select by index
}
```

### Content Capture Tools

#### browser_snapshot
Capture accessibility tree snapshot of current page.

```javascript
// Returns structured accessibility tree
const snapshot = await mcp.browser_snapshot();

// Example output:
{
  role: "WebArea",
  name: "Example Page",
  children: [
    {
      role: "heading",
      name: "Welcome",
      level: 1
    },
    {
      role: "button",
      name: "Get Started",
      ref: "button-start-123"
    }
  ]
}
```

#### browser_take_screenshot
Capture visual screenshots.

```javascript
// Parameters:
{
  element: "Product image",          // Optional: Specific element
  ref: "img-product-123",           // Optional: Element reference
  fullPage: false,                  // Optional: Capture full scrollable page
  clip: {                           // Optional: Specific region
    x: 0, y: 0, 
    width: 800, height: 600
  },
  type: "png",                      // Optional: "png" | "jpeg"
  quality: 90                       // Optional: JPEG quality (0-100)
}
```

### Tab Management Tools

#### browser_tab_new
Create new browser tabs.

```javascript
// Parameters:
{
  url: "https://example.com",        // Optional: URL to open
  background: false                  // Optional: Open in background
}
```

#### browser_tab_list
List all open tabs.

```javascript
// Returns:
[
  {
    id: "tab-1",
    title: "Example Page",
    url: "https://example.com",
    active: true
  },
  {
    id: "tab-2", 
    title: "Another Page",
    url: "https://another.com",
    active: false
  }
]
```

#### browser_tab_select
Switch to a specific tab.

```javascript
// Parameters:
{
  index: 1                           // Tab index (0-based)
}
```

#### browser_tab_close
Close tabs.

```javascript
// Parameters:
{
  index: 1                           // Optional: Specific tab index
}
```

### Advanced Tools

#### browser_evaluate
Execute JavaScript in page context.

```javascript
// Parameters:
{
  function: "() => document.title",   // JavaScript function as string
  element: "Product price",          // Optional: Element description
  ref: "price-123"                   // Optional: Element reference
}

// Example:
const title = await mcp.browser_evaluate({
  function: "() => document.querySelector('h1').textContent"
});
```

#### browser_wait_for
Wait for conditions.

```javascript
// Parameters:
{
  text: "Loading complete",          // Wait for text to appear
  textGone: "Loading...",           // Wait for text to disappear
  selector: ".loaded",              // Wait for element
  state: "visible",                 // Element state: "visible" | "hidden" | "attached"
  timeout: 5000                     // Timeout in ms
}
```

#### browser_press_key
Press keyboard keys.

```javascript
// Parameters:
{
  key: "Enter",                      // Key name or character
  modifiers: ["Control", "Shift"]    // Optional: Modifier keys
}
```

#### browser_file_upload
Upload files.

```javascript
// Parameters:
{
  paths: ["/path/to/file1.pdf", "/path/to/file2.jpg"],
  element: "File upload input",
  ref: "input-file-upload"
}
```

### Network Tools

#### browser_network_requests
Get all network requests.

```javascript
// Returns detailed request information
const requests = await mcp.browser_network_requests();

// Example output:
[
  {
    url: "https://api.example.com/data",
    method: "GET",
    status: 200,
    headers: {...},
    timing: {...},
    size: 1234
  }
]
```

#### browser_console_messages
Get console messages.

```javascript
// Returns all console logs, warnings, errors
const messages = await mcp.browser_console_messages();

// Example output:
[
  {
    type: "log",
    text: "Application initialized",
    timestamp: "2025-01-30T12:00:00Z"
  }
]
```

## Test Structure Patterns

### 1. MCP-Optimized Test Structure

```javascript
// Use MCP tools directly instead of Playwright API
async function testWithMCP() {
  // Initialize browser (handled by MCP server)
  
  // Navigate using MCP tool
  await mcp.browser_navigate({ 
    url: 'http://localhost:3000',
    waitUntil: 'networkidle'
  });
  
  // Get accessibility snapshot
  const snapshot = await mcp.browser_snapshot();
  
  // Find elements in snapshot
  const loginButton = findElementInSnapshot(snapshot, {
    role: 'button',
    name: /login/i
  });
  
  // Click using reference
  await mcp.browser_click({
    element: 'Login button',
    ref: loginButton.ref
  });
  
  // Type credentials
  await mcp.browser_type({
    element: 'Email input',
    ref: findElementInSnapshot(snapshot, { role: 'textbox', name: /email/i }).ref,
    text: 'user@example.com'
  });
}
```

### 2. Helper Functions for Snapshot Navigation

```javascript
// Helper to find elements in accessibility snapshot
function findElementInSnapshot(snapshot, criteria) {
  function search(node) {
    // Check if node matches criteria
    const matches = Object.entries(criteria).every(([key, value]) => {
      if (value instanceof RegExp) {
        return value.test(node[key]);
      }
      return node[key] === value;
    });
    
    if (matches) return node;
    
    // Search children
    if (node.children) {
      for (const child of node.children) {
        const found = search(child);
        if (found) return found;
      }
    }
    
    return null;
  }
  
  return search(snapshot);
}

// Helper to find multiple elements
function findAllElementsInSnapshot(snapshot, criteria) {
  const results = [];
  
  function search(node) {
    const matches = Object.entries(criteria).every(([key, value]) => {
      if (value instanceof RegExp) {
        return value.test(node[key]);
      }
      return node[key] === value;
    });
    
    if (matches) results.push(node);
    
    if (node.children) {
      node.children.forEach(child => search(child));
    }
  }
  
  search(snapshot);
  return results;
}
```

## Accessibility Tree Navigation

### Understanding the Accessibility Tree

```javascript
// Example accessibility tree structure
{
  role: "WebArea",
  name: "E-commerce Site",
  children: [
    {
      role: "navigation",
      name: "Main navigation",
      children: [
        {
          role: "link",
          name: "Home",
          ref: "nav-home-link"
        },
        {
          role: "link", 
          name: "Products",
          ref: "nav-products-link"
        }
      ]
    },
    {
      role: "main",
      children: [
        {
          role: "heading",
          level: 1,
          name: "Featured Products"
        },
        {
          role: "list",
          children: [
            {
              role: "listitem",
              children: [
                {
                  role: "article",
                  children: [
                    {
                      role: "heading",
                      level: 2,
                      name: "Product 1"
                    },
                    {
                      role: "button",
                      name: "Add to Cart",
                      ref: "add-to-cart-product-1"
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### Navigating Complex Structures

```javascript
// Navigate nested structures efficiently
async function navigateToProduct(productName) {
  const snapshot = await mcp.browser_snapshot();
  
  // Find product heading
  const productHeading = findElementInSnapshot(snapshot, {
    role: 'heading',
    name: productName
  });
  
  // Find associated "Add to Cart" button
  // Look for button in same article/container
  const article = findParentWithRole(productHeading, 'article');
  const addToCartButton = findElementInSnapshot(article, {
    role: 'button',
    name: /add to cart/i
  });
  
  // Click the button
  await mcp.browser_click({
    element: `Add to Cart button for ${productName}`,
    ref: addToCartButton.ref
  });
}

function findParentWithRole(element, role) {
  let current = element;
  while (current.parent) {
    if (current.parent.role === role) {
      return current.parent;
    }
    current = current.parent;
  }
  return null;
}
```

## WebSocket Message Capture

### Enhanced WebSocket Monitoring with MCP

```javascript
// MCP-compatible WebSocket capture
async function captureWebSocketMessagesWithMCP(playerName) {
  const messages = [];
  const startTime = Date.now();
  
  // Execute JavaScript to monitor WebSocket
  await mcp.browser_evaluate({
    function: `
      (() => {
        const originalWS = window.WebSocket;
        window.__wsMessages = [];
        
        window.WebSocket = function(...args) {
          const ws = new originalWS(...args);
          
          ws.addEventListener('open', () => {
            window.__wsMessages.push({
              type: 'connection',
              url: ws.url,
              timestamp: Date.now(),
              player: '${playerName}'
            });
          });
          
          const originalSend = ws.send;
          ws.send = function(data) {
            window.__wsMessages.push({
              type: 'sent',
              data: data,
              timestamp: Date.now(),
              player: '${playerName}'
            });
            return originalSend.call(this, data);
          };
          
          ws.addEventListener('message', (event) => {
            window.__wsMessages.push({
              type: 'received',
              data: event.data,
              timestamp: Date.now(),
              player: '${playerName}'
            });
          });
          
          return ws;
        };
      })();
    `
  });
  
  // Periodically collect messages
  const collectMessages = async () => {
    const collectedMessages = await mcp.browser_evaluate({
      function: "() => { const msgs = window.__wsMessages || []; window.__wsMessages = []; return msgs; }"
    });
    
    collectedMessages.forEach(msg => {
      try {
        const parsed = JSON.parse(msg.data);
        messages.push({
          ...msg,
          parsedData: parsed,
          relativeTime: msg.timestamp - startTime
        });
      } catch (e) {
        messages.push({
          ...msg,
          parseError: true,
          relativeTime: msg.timestamp - startTime
        });
      }
    });
  };
  
  // Set up periodic collection
  const interval = setInterval(collectMessages, 500);
  
  return {
    messages,
    stopCapture: () => clearInterval(interval),
    getAnalysis: () => analyzeWebSocketMessages(messages)
  };
}
```

### Advanced Message Analysis

```javascript
function analyzeWebSocketMessages(messages) {
  const analysis = {
    totalMessages: messages.length,
    byType: {},
    byEvent: {},
    timeline: [],
    latency: [],
    errors: []
  };
  
  // Group by type
  messages.forEach(msg => {
    analysis.byType[msg.type] = (analysis.byType[msg.type] || 0) + 1;
    
    // Group by event type if parsed
    if (msg.parsedData && msg.parsedData.event) {
      analysis.byEvent[msg.parsedData.event] = 
        (analysis.byEvent[msg.parsedData.event] || 0) + 1;
    }
    
    // Build timeline
    analysis.timeline.push({
      time: msg.relativeTime,
      type: msg.type,
      event: msg.parsedData?.event || 'raw',
      player: msg.player
    });
    
    // Track errors
    if (msg.parseError || msg.parsedData?.error) {
      analysis.errors.push(msg);
    }
  });
  
  // Calculate message latency patterns
  const sentMessages = messages.filter(m => m.type === 'sent');
  const receivedMessages = messages.filter(m => m.type === 'received');
  
  sentMessages.forEach(sent => {
    const response = receivedMessages.find(recv => 
      recv.timestamp > sent.timestamp &&
      recv.parsedData?.id === sent.parsedData?.id
    );
    
    if (response) {
      analysis.latency.push({
        request: sent.parsedData?.event,
        responseTime: response.timestamp - sent.timestamp
      });
    }
  });
  
  // Calculate statistics
  analysis.stats = {
    averageLatency: analysis.latency.length > 0 
      ? analysis.latency.reduce((sum, l) => sum + l.responseTime, 0) / analysis.latency.length
      : 0,
    messagesPerSecond: messages.length / (messages[messages.length - 1]?.relativeTime / 1000 || 1),
    errorRate: (analysis.errors.length / messages.length) * 100
  };
  
  return analysis;
}
```

## Multi-Browser Testing

### Concurrent User Testing with MCP

```javascript
async function testMultiUserWithMCP(userCount = 3) {
  const users = [];
  
  // Create user sessions
  for (let i = 0; i < userCount; i++) {
    const userName = `User${i + 1}`;
    
    // Each user gets their own tab
    await mcp.browser_tab_new();
    const tabs = await mcp.browser_tab_list();
    const tabIndex = tabs.length - 1;
    
    users.push({
      name: userName,
      tabIndex: tabIndex,
      wsCapture: null,
      actions: []
    });
  }
  
  // Initialize all users
  for (const user of users) {
    await mcp.browser_tab_select({ index: user.tabIndex });
    
    // Navigate to app
    await mcp.browser_navigate({ 
      url: 'http://localhost:3000' 
    });
    
    // Set up WebSocket capture
    user.wsCapture = await captureWebSocketMessagesWithMCP(user.name);
    
    // Enter username
    const snapshot = await mcp.browser_snapshot();
    const nameInput = findElementInSnapshot(snapshot, {
      role: 'textbox',
      name: /name|username/i
    });
    
    await mcp.browser_type({
      element: 'Username input',
      ref: nameInput.ref,
      text: user.name
    });
    
    // Click start
    const startButton = findElementInSnapshot(snapshot, {
      role: 'button',
      name: /start|enter|join/i
    });
    
    await mcp.browser_click({
      element: 'Start button',
      ref: startButton.ref
    });
    
    user.actions.push({
      action: 'joined',
      timestamp: Date.now()
    });
  }
  
  // Simulate concurrent actions
  await testConcurrentActions(users);
  
  // Analyze results
  return analyzeMultiUserTest(users);
}

async function testConcurrentActions(users) {
  // User 1 creates a room
  await mcp.browser_tab_select({ index: users[0].tabIndex });
  const snapshot1 = await mcp.browser_snapshot();
  const createButton = findElementInSnapshot(snapshot1, {
    role: 'button',
    name: /create/i
  });
  
  await mcp.browser_click({
    element: 'Create room button',
    ref: createButton.ref
  });
  
  users[0].actions.push({
    action: 'created_room',
    timestamp: Date.now()
  });
  
  // Wait for propagation
  await mcp.browser_wait_for({ time: 2000 });
  
  // Check if other users see the room
  for (let i = 1; i < users.length; i++) {
    await mcp.browser_tab_select({ index: users[i].tabIndex });
    const snapshot = await mcp.browser_snapshot();
    
    const rooms = findAllElementsInSnapshot(snapshot, {
      role: 'listitem',
      name: /room/i
    });
    
    users[i].actions.push({
      action: 'room_check',
      roomCount: rooms.length,
      timestamp: Date.now()
    });
  }
}
```

### Load Testing Pattern

```javascript
async function performLoadTest(config = {}) {
  const {
    userCount = 10,
    duration = 60000, // 1 minute
    actionsPerUser = 5,
    concurrency = 3
  } = config;
  
  const results = {
    startTime: Date.now(),
    users: [],
    errors: [],
    metrics: {}
  };
  
  // Create users in batches
  for (let batch = 0; batch < Math.ceil(userCount / concurrency); batch++) {
    const batchPromises = [];
    
    for (let i = 0; i < concurrency && (batch * concurrency + i) < userCount; i++) {
      const userIndex = batch * concurrency + i;
      batchPromises.push(createTestUser(userIndex));
    }
    
    const batchUsers = await Promise.all(batchPromises);
    results.users.push(...batchUsers);
  }
  
  // Run test actions
  const testEndTime = Date.now() + duration;
  while (Date.now() < testEndTime) {
    // Select random users for actions
    const activeUsers = selectRandomUsers(results.users, concurrency);
    
    await Promise.all(activeUsers.map(user => 
      performRandomAction(user).catch(err => {
        results.errors.push({
          user: user.name,
          error: err.message,
          timestamp: Date.now()
        });
      })
    ));
    
    // Brief pause between action batches
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  // Collect metrics
  results.metrics = await collectLoadTestMetrics(results);
  
  return results;
}

async function collectLoadTestMetrics(results) {
  // Get performance metrics from browser
  const performanceData = await mcp.browser_evaluate({
    function: `() => {
      const perf = performance.getEntriesByType('navigation')[0];
      return {
        domContentLoaded: perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
        loadComplete: perf.loadEventEnd - perf.loadEventStart,
        totalTime: perf.loadEventEnd - perf.fetchStart
      };
    }`
  });
  
  // Calculate test metrics
  const totalActions = results.users.reduce((sum, user) => 
    sum + user.actions.length, 0
  );
  
  const testDuration = Date.now() - results.startTime;
  
  return {
    performance: performanceData,
    totalUsers: results.users.length,
    totalActions: totalActions,
    actionsPerSecond: totalActions / (testDuration / 1000),
    errorRate: (results.errors.length / totalActions) * 100,
    averageResponseTime: calculateAverageResponseTime(results.users)
  };
}
```

## Common Testing Scenarios

### 1. Authentication Flow Testing

```javascript
async function testAuthenticationFlow() {
  // Navigate to login page
  await mcp.browser_navigate({ url: 'https://app.example.com/login' });
  
  // Get initial snapshot
  const loginSnapshot = await mcp.browser_snapshot();
  
  // Test invalid credentials
  const emailInput = findElementInSnapshot(loginSnapshot, {
    role: 'textbox',
    name: /email/i
  });
  
  const passwordInput = findElementInSnapshot(loginSnapshot, {
    role: 'textbox',
    name: /password/i
  });
  
  const submitButton = findElementInSnapshot(loginSnapshot, {
    role: 'button',
    name: /sign in|login/i
  });
  
  // Enter invalid credentials
  await mcp.browser_type({
    element: 'Email input',
    ref: emailInput.ref,
    text: 'invalid@example.com'
  });
  
  await mcp.browser_type({
    element: 'Password input',
    ref: passwordInput.ref,
    text: 'wrongpassword'
  });
  
  await mcp.browser_click({
    element: 'Submit button',
    ref: submitButton.ref
  });
  
  // Wait for error message
  await mcp.browser_wait_for({
    text: 'Invalid credentials',
    timeout: 5000
  });
  
  // Clear fields and try valid credentials
  await mcp.browser_type({
    element: 'Email input',
    ref: emailInput.ref,
    text: 'user@example.com',
    clear: true
  });
  
  await mcp.browser_type({
    element: 'Password input', 
    ref: passwordInput.ref,
    text: 'correctpassword',
    clear: true
  });
  
  await mcp.browser_click({
    element: 'Submit button',
    ref: submitButton.ref
  });
  
  // Verify successful login
  await mcp.browser_wait_for({
    text: 'Dashboard',
    timeout: 5000
  });
  
  // Check for auth token in localStorage
  const authToken = await mcp.browser_evaluate({
    function: "() => localStorage.getItem('authToken')"
  });
  
  return {
    success: !!authToken,
    token: authToken
  };
}
```

### 2. Form Validation Testing

```javascript
async function testFormValidation() {
  await mcp.browser_navigate({ url: 'https://app.example.com/register' });
  
  const tests = [
    {
      name: 'Empty form submission',
      actions: async () => {
        const snapshot = await mcp.browser_snapshot();
        const submitBtn = findElementInSnapshot(snapshot, {
          role: 'button',
          name: /submit|register/i
        });
        
        await mcp.browser_click({
          element: 'Submit button',
          ref: submitBtn.ref
        });
      },
      expectedErrors: ['Email is required', 'Password is required']
    },
    {
      name: 'Invalid email format',
      actions: async () => {
        const snapshot = await mcp.browser_snapshot();
        const emailInput = findElementInSnapshot(snapshot, {
          role: 'textbox',
          name: /email/i
        });
        
        await mcp.browser_type({
          element: 'Email input',
          ref: emailInput.ref,
          text: 'notanemail',
          clear: true
        });
        
        // Trigger validation by tabbing out
        await mcp.browser_press_key({ key: 'Tab' });
      },
      expectedErrors: ['Please enter a valid email']
    },
    {
      name: 'Password too short',
      actions: async () => {
        const snapshot = await mcp.browser_snapshot();
        const passwordInput = findElementInSnapshot(snapshot, {
          role: 'textbox',
          name: /password/i
        });
        
        await mcp.browser_type({
          element: 'Password input',
          ref: passwordInput.ref,
          text: '123',
          clear: true
        });
        
        await mcp.browser_press_key({ key: 'Tab' });
      },
      expectedErrors: ['Password must be at least 8 characters']
    }
  ];
  
  const results = [];
  
  for (const test of tests) {
    console.log(`Running test: ${test.name}`);
    
    // Refresh page for clean state
    await mcp.browser_navigate_refresh();
    await mcp.browser_wait_for({ state: 'domcontentloaded' });
    
    // Run test actions
    await test.actions();
    
    // Wait for validation messages
    await mcp.browser_wait_for({ time: 1000 });
    
    // Check for expected errors
    const snapshot = await mcp.browser_snapshot();
    const errorMessages = findAllElementsInSnapshot(snapshot, {
      role: 'alert'
    }).map(el => el.name);
    
    const passed = test.expectedErrors.every(expected =>
      errorMessages.some(actual => actual.includes(expected))
    );
    
    results.push({
      test: test.name,
      passed,
      expectedErrors: test.expectedErrors,
      actualErrors: errorMessages
    });
  }
  
  return results;
}
```

### 3. Responsive Design Testing

```javascript
async function testResponsiveDesign() {
  const viewports = [
    { name: 'Mobile', width: 375, height: 667 },
    { name: 'Tablet', width: 768, height: 1024 },
    { name: 'Desktop', width: 1920, height: 1080 }
  ];
  
  const results = [];
  
  for (const viewport of viewports) {
    // Resize browser
    await mcp.browser_resize({
      width: viewport.width,
      height: viewport.height
    });
    
    // Navigate to page
    await mcp.browser_navigate({ 
      url: 'https://app.example.com' 
    });
    
    // Get snapshot for this viewport
    const snapshot = await mcp.browser_snapshot();
    
    // Check mobile menu visibility
    const mobileMenu = findElementInSnapshot(snapshot, {
      role: 'button',
      name: /menu|hamburger/i
    });
    
    const desktopNav = findElementInSnapshot(snapshot, {
      role: 'navigation',
      name: /main/i
    });
    
    // Take screenshot
    const screenshot = await mcp.browser_take_screenshot({
      fullPage: true,
      type: 'png'
    });
    
    results.push({
      viewport: viewport.name,
      dimensions: `${viewport.width}x${viewport.height}`,
      hasMobileMenu: !!mobileMenu,
      hasDesktopNav: !!desktopNav,
      screenshot: screenshot,
      layoutCorrect: viewport.name === 'Mobile' ? !!mobileMenu : !!desktopNav
    });
  }
  
  return results;
}
```

### 4. Performance Testing

```javascript
async function testPagePerformance() {
  const metrics = {
    navigationStart: Date.now(),
    resources: []
  };
  
  // Enable performance monitoring
  await mcp.browser_evaluate({
    function: `() => {
      window.__perfObserver = new PerformanceObserver((list) => {
        window.__perfEntries = window.__perfEntries || [];
        window.__perfEntries.push(...list.getEntries());
      });
      window.__perfObserver.observe({ 
        entryTypes: ['navigation', 'resource', 'paint', 'largest-contentful-paint'] 
      });
    }`
  });
  
  // Navigate to page
  await mcp.browser_navigate({ 
    url: 'https://app.example.com',
    waitUntil: 'networkidle'
  });
  
  metrics.navigationEnd = Date.now();
  
  // Collect performance data
  const performanceData = await mcp.browser_evaluate({
    function: `() => {
      const nav = performance.getEntriesByType('navigation')[0];
      const paints = performance.getEntriesByType('paint');
      const lcp = performance.getEntriesByType('largest-contentful-paint')[0];
      const resources = performance.getEntriesByType('resource');
      
      return {
        navigation: {
          domContentLoaded: nav.domContentLoadedEventEnd - nav.domContentLoadedEventStart,
          loadComplete: nav.loadEventEnd - nav.loadEventStart,
          totalTime: nav.loadEventEnd - nav.fetchStart,
          domInteractive: nav.domInteractive - nav.fetchStart,
          redirectTime: nav.redirectEnd - nav.redirectStart,
          dnsTime: nav.domainLookupEnd - nav.domainLookupStart,
          tcpTime: nav.connectEnd - nav.connectStart,
          requestTime: nav.responseStart - nav.requestStart,
          responseTime: nav.responseEnd - nav.responseStart
        },
        paints: paints.map(p => ({
          name: p.name,
          startTime: p.startTime
        })),
        largestContentfulPaint: lcp ? lcp.startTime : null,
        resources: resources.map(r => ({
          name: r.name,
          type: r.initiatorType,
          duration: r.duration,
          size: r.transferSize,
          startTime: r.startTime
        })).sort((a, b) => b.duration - a.duration).slice(0, 10)
      };
    }`
  });
  
  // Calculate web vitals
  metrics.webVitals = {
    FCP: performanceData.paints.find(p => p.name === 'first-contentful-paint')?.startTime,
    LCP: performanceData.largestContentfulPaint,
    TTI: performanceData.navigation.domInteractive,
    TBT: calculateTotalBlockingTime(performanceData),
    CLS: await measureCumulativeLayoutShift()
  };
  
  // Performance analysis
  metrics.analysis = analyzePerformance(performanceData, metrics.webVitals);
  
  return metrics;
}

function analyzePerformance(data, vitals) {
  const thresholds = {
    FCP: { good: 1800, needsImprovement: 3000 },
    LCP: { good: 2500, needsImprovement: 4000 },
    TTI: { good: 3800, needsImprovement: 7300 },
    TBT: { good: 200, needsImprovement: 600 },
    CLS: { good: 0.1, needsImprovement: 0.25 }
  };
  
  const ratings = {};
  
  Object.entries(vitals).forEach(([metric, value]) => {
    if (value === null) {
      ratings[metric] = 'Not measured';
    } else if (value <= thresholds[metric].good) {
      ratings[metric] = 'Good';
    } else if (value <= thresholds[metric].needsImprovement) {
      ratings[metric] = 'Needs Improvement';
    } else {
      ratings[metric] = 'Poor';
    }
  });
  
  return {
    ratings,
    slowestResources: data.resources.slice(0, 5),
    recommendations: generatePerformanceRecommendations(data, vitals, ratings)
  };
}
```

## Debugging & Analysis

### Enhanced Debugging Tools

```javascript
// Comprehensive debugging helper
class MCPDebugger {
  constructor() {
    this.logs = [];
    this.snapshots = [];
    this.networkLog = [];
  }
  
  async captureState(label) {
    const state = {
      label,
      timestamp: Date.now(),
      snapshot: await mcp.browser_snapshot(),
      url: await mcp.browser_evaluate({ function: "() => window.location.href" }),
      cookies: await mcp.browser_evaluate({ function: "() => document.cookie" }),
      localStorage: await mcp.browser_evaluate({ 
        function: "() => Object.entries(localStorage)" 
      }),
      consoleMessages: await mcp.browser_console_messages(),
      networkRequests: await mcp.browser_network_requests()
    };
    
    this.snapshots.push(state);
    return state;
  }
  
  async traceAction(description, action) {
    const startState = await this.captureState(`Before: ${description}`);
    
    try {
      const result = await action();
      const endState = await this.captureState(`After: ${description}`);
      
      this.logs.push({
        description,
        success: true,
        result,
        startState,
        endState,
        changes: this.compareStates(startState, endState)
      });
      
      return result;
    } catch (error) {
      const errorState = await this.captureState(`Error: ${description}`);
      
      this.logs.push({
        description,
        success: false,
        error: error.message,
        startState,
        errorState
      });
      
      throw error;
    }
  }
  
  compareStates(before, after) {
    const changes = {
      urlChanged: before.url !== after.url,
      newElements: [],
      removedElements: [],
      networkActivity: after.networkRequests.length - before.networkRequests.length,
      consoleOutput: after.consoleMessages.length - before.consoleMessages.length
    };
    
    // Compare accessibility trees
    const beforeElements = this.flattenSnapshot(before.snapshot);
    const afterElements = this.flattenSnapshot(after.snapshot);
    
    afterElements.forEach(el => {
      if (!beforeElements.find(be => be.ref === el.ref)) {
        changes.newElements.push(el);
      }
    });
    
    beforeElements.forEach(el => {
      if (!afterElements.find(ae => ae.ref === el.ref)) {
        changes.removedElements.push(el);
      }
    });
    
    return changes;
  }
  
  flattenSnapshot(snapshot) {
    const elements = [];
    
    function traverse(node) {
      if (node.ref) {
        elements.push({
          ref: node.ref,
          role: node.role,
          name: node.name
        });
      }
      if (node.children) {
        node.children.forEach(traverse);
      }
    }
    
    traverse(snapshot);
    return elements;
  }
  
  generateReport() {
    return {
      summary: {
        totalActions: this.logs.length,
        successful: this.logs.filter(l => l.success).length,
        failed: this.logs.filter(l => !l.success).length
      },
      timeline: this.logs.map(log => ({
        time: log.startState.timestamp,
        action: log.description,
        success: log.success,
        changes: log.changes
      })),
      errors: this.logs.filter(l => !l.success),
      networkSummary: this.analyzeNetworkLog(),
      performanceMetrics: this.calculatePerformanceMetrics()
    };
  }
}

// Usage example
async function debugComplexScenario() {
  const debugger = new MCPDebugger();
  
  try {
    await debugger.traceAction('Navigate to login', async () => {
      await mcp.browser_navigate({ url: 'https://app.example.com/login' });
    });
    
    await debugger.traceAction('Fill login form', async () => {
      const snapshot = await mcp.browser_snapshot();
      const emailInput = findElementInSnapshot(snapshot, { role: 'textbox', name: /email/i });
      const passwordInput = findElementInSnapshot(snapshot, { role: 'textbox', name: /password/i });
      
      await mcp.browser_type({
        element: 'Email',
        ref: emailInput.ref,
        text: 'user@example.com'
      });
      
      await mcp.browser_type({
        element: 'Password',
        ref: passwordInput.ref,
        text: 'password123'
      });
    });
    
    await debugger.traceAction('Submit form', async () => {
      const snapshot = await mcp.browser_snapshot();
      const submitBtn = findElementInSnapshot(snapshot, { role: 'button', name: /submit/i });
      
      await mcp.browser_click({
        element: 'Submit button',
        ref: submitBtn.ref
      });
      
      await mcp.browser_wait_for({ text: 'Dashboard', timeout: 5000 });
    });
    
  } catch (error) {
    console.error('Test failed:', error);
  }
  
  // Generate comprehensive report
  const report = debugger.generateReport();
  console.log('Debug Report:', JSON.stringify(report, null, 2));
  
  return report;
}
```

### Visual Regression Testing

```javascript
async function performVisualRegressionTest(testName, actions) {
  const results = {
    testName,
    timestamp: Date.now(),
    screenshots: [],
    differences: []
  };
  
  // Take baseline screenshots
  for (const action of actions) {
    await action.setup();
    
    const screenshot = await mcp.browser_take_screenshot({
      fullPage: action.fullPage || false,
      element: action.element,
      ref: action.ref
    });
    
    results.screenshots.push({
      name: action.name,
      baseline: screenshot,
      timestamp: Date.now()
    });
  }
  
  // Wait and take comparison screenshots
  await new Promise(resolve => setTimeout(resolve, 100));
  
  for (let i = 0; i < actions.length; i++) {
    const action = actions[i];
    await action.setup();
    
    const screenshot = await mcp.browser_take_screenshot({
      fullPage: action.fullPage || false,
      element: action.element,
      ref: action.ref
    });
    
    results.screenshots[i].comparison = screenshot;
    
    // In real implementation, you would compare images here
    // For now, we'll check if they're identical
    results.differences.push({
      name: action.name,
      identical: results.screenshots[i].baseline === screenshot,
      diffPercentage: 0 // Would be calculated by image comparison
    });
  }
  
  return results;
}
```

## Best Practices

### 1. Accessibility-First Testing

```javascript
// Always prefer accessibility attributes over CSS selectors
// ✅ GOOD - Uses semantic roles and labels
const button = findElementInSnapshot(snapshot, {
  role: 'button',
  name: /submit/i
});

// ❌ AVOID - Relies on implementation details
const button = await page.$('.btn-primary-submit');

// ✅ GOOD - Multiple fallback strategies
const element = findElementInSnapshot(snapshot, { role: 'button', name: /save/i })
  || findElementInSnapshot(snapshot, { role: 'button', name: /submit/i })
  || findElementInSnapshot(snapshot, { ref: 'form-submit-button' });
```

### 2. Efficient Snapshot Usage

```javascript
// Cache snapshots when multiple operations on same page
async function efficientPageInteraction() {
  // Take snapshot once
  const snapshot = await mcp.browser_snapshot();
  
  // Find all elements needed
  const elements = {
    emailInput: findElementInSnapshot(snapshot, { role: 'textbox', name: /email/i }),
    passwordInput: findElementInSnapshot(snapshot, { role: 'textbox', name: /password/i }),
    submitButton: findElementInSnapshot(snapshot, { role: 'button', name: /sign in/i }),
    rememberMe: findElementInSnapshot(snapshot, { role: 'checkbox', name: /remember/i })
  };
  
  // Perform all interactions
  await mcp.browser_type({
    element: 'Email',
    ref: elements.emailInput.ref,
    text: 'user@example.com'
  });
  
  await mcp.browser_type({
    element: 'Password',
    ref: elements.passwordInput.ref,
    text: 'password123'
  });
  
  if (elements.rememberMe) {
    await mcp.browser_click({
      element: 'Remember me',
      ref: elements.rememberMe.ref
    });
  }
  
  await mcp.browser_click({
    element: 'Submit',
    ref: elements.submitButton.ref
  });
}
```

### 3. Error Handling and Recovery

```javascript
// Implement retry logic for flaky operations
async function robustClick(element, ref, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      await mcp.browser_click({ element, ref });
      return; // Success
    } catch (error) {
      console.log(`Click attempt ${attempt} failed: ${error.message}`);
      
      if (attempt === maxRetries) throw error;
      
      // Try to recover
      // Re-fetch snapshot in case DOM changed
      const newSnapshot = await mcp.browser_snapshot();
      const newElement = findElementInSnapshot(newSnapshot, { ref });
      
      if (!newElement) {
        throw new Error(`Element ${element} no longer exists`);
      }
      
      // Wait before retry with exponential backoff
      await new Promise(resolve => 
        setTimeout(resolve, Math.pow(2, attempt) * 1000)
      );
    }
  }
}
```

### 4. Test Organization

```javascript
// Use descriptive test structure
class TestSuite {
  constructor(name) {
    this.name = name;
    this.tests = [];
    this.beforeEach = null;
    this.afterEach = null;
  }
  
  addTest(name, testFn) {
    this.tests.push({ name, testFn });
  }
  
  async run() {
    const results = {
      suite: this.name,
      passed: 0,
      failed: 0,
      tests: []
    };
    
    for (const test of this.tests) {
      if (this.beforeEach) await this.beforeEach();
      
      const testResult = {
        name: test.name,
        startTime: Date.now()
      };
      
      try {
        await test.testFn();
        testResult.passed = true;
        results.passed++;
      } catch (error) {
        testResult.passed = false;
        testResult.error = error.message;
        testResult.stack = error.stack;
        results.failed++;
      }
      
      testResult.duration = Date.now() - testResult.startTime;
      results.tests.push(testResult);
      
      if (this.afterEach) await this.afterEach();
    }
    
    return results;
  }
}

// Usage
const authSuite = new TestSuite('Authentication Tests');

authSuite.beforeEach = async () => {
  await mcp.browser_navigate({ url: 'https://app.example.com/login' });
};

authSuite.addTest('Valid login', async () => {
  // Test implementation
});

authSuite.addTest('Invalid credentials', async () => {
  // Test implementation
});

const results = await authSuite.run();
```

## Real-World Example

Here's a complete example testing a real-time collaborative application:

```javascript
// Complete test for a collaborative document editor
async function testCollaborativeEditor() {
  const test = {
    name: 'Collaborative Editor Real-time Sync',
    startTime: Date.now(),
    results: {
      phases: [],
      bugs: [],
      performance: {}
    }
  };
  
  // Phase 1: Setup
  console.log('🚀 Phase 1: Setting up collaborative session...');
  
  // Create two user sessions
  const users = [
    { name: 'Alice', role: 'editor' },
    { name: 'Bob', role: 'viewer' }
  ];
  
  // Initialize users
  for (const user of users) {
    await mcp.browser_tab_new();
    const tabs = await mcp.browser_tab_list();
    user.tabIndex = tabs.length - 1;
    
    await mcp.browser_tab_select({ index: user.tabIndex });
    await mcp.browser_navigate({ url: 'https://editor.example.com' });
    
    // Login
    const snapshot = await mcp.browser_snapshot();
    const loginBtn = findElementInSnapshot(snapshot, {
      role: 'button',
      name: /sign in/i
    });
    
    await mcp.browser_click({
      element: 'Sign in button',
      ref: loginBtn.ref
    });
    
    // Enter credentials
    await mcp.browser_type({
      element: 'Email',
      ref: findElementInSnapshot(snapshot, { role: 'textbox', name: /email/i }).ref,
      text: `${user.name.toLowerCase()}@example.com`
    });
    
    await mcp.browser_type({
      element: 'Password',
      ref: findElementInSnapshot(snapshot, { role: 'textbox', name: /password/i }).ref,
      text: 'password123'
    });
    
    // Submit
    await mcp.browser_click({
      element: 'Submit',
      ref: findElementInSnapshot(snapshot, { role: 'button', name: /submit/i }).ref
    });
    
    await mcp.browser_wait_for({ text: 'Dashboard', timeout: 5000 });
    
    // Set up WebSocket monitoring
    user.wsMonitor = await captureWebSocketMessagesWithMCP(user.name);
  }
  
  test.results.phases.push({
    name: 'Setup',
    duration: Date.now() - test.startTime,
    status: 'completed'
  });
  
  // Phase 2: Create and share document
  console.log('📄 Phase 2: Creating shared document...');
  const phase2Start = Date.now();
  
  // Alice creates a document
  await mcp.browser_tab_select({ index: users[0].tabIndex });
  
  const aliceSnapshot = await mcp.browser_snapshot();
  const newDocBtn = findElementInSnapshot(aliceSnapshot, {
    role: 'button',
    name: /new document/i
  });
  
  await mcp.browser_click({
    element: 'New document',
    ref: newDocBtn.ref
  });
  
  // Wait for editor to load
  await mcp.browser_wait_for({ text: 'Untitled Document', timeout: 5000 });
  
  // Get document ID
  const docId = await mcp.browser_evaluate({
    function: "() => window.location.pathname.split('/').pop()"
  });
  
  // Type some content
  const editorSnapshot = await mcp.browser_snapshot();
  const editor = findElementInSnapshot(editorSnapshot, {
    role: 'textbox',
    name: /editor|content/i
  });
  
  await mcp.browser_type({
    element: 'Editor',
    ref: editor.ref,
    text: 'Hello, this is Alice typing in real-time!'
  });
  
  // Share with Bob
  const shareBtn = findElementInSnapshot(editorSnapshot, {
    role: 'button',
    name: /share/i
  });
  
  await mcp.browser_click({
    element: 'Share button',
    ref: shareBtn.ref
  });
  
  // Add Bob as viewer
  const emailInput = findElementInSnapshot(await mcp.browser_snapshot(), {
    role: 'textbox',
    name: /email/i
  });
  
  await mcp.browser_type({
    element: 'Share email',
    ref: emailInput.ref,
    text: 'bob@example.com'
  });
  
  await mcp.browser_press_key({ key: 'Enter' });
  
  test.results.phases.push({
    name: 'Document Creation',
    duration: Date.now() - phase2Start,
    status: 'completed',
    docId: docId
  });
  
  // Phase 3: Test real-time synchronization
  console.log('🔄 Phase 3: Testing real-time sync...');
  const phase3Start = Date.now();
  
  // Bob opens the shared document
  await mcp.browser_tab_select({ index: users[1].tabIndex });
  await mcp.browser_navigate({ url: `https://editor.example.com/doc/${docId}` });
  
  // Wait for document to load
  await mcp.browser_wait_for({ text: 'Hello, this is Alice', timeout: 5000 });
  
  // Verify Bob sees Alice's content
  const bobContent = await mcp.browser_evaluate({
    function: "() => document.querySelector('[role=\"textbox\"]').textContent"
  });
  
  const syncWorking = bobContent.includes('Hello, this is Alice');
  
  if (!syncWorking) {
    test.results.bugs.push({
      type: 'sync_failure',
      description: 'Bob did not see Alice\'s initial content',
      severity: 'critical'
    });
  }
  
  // Alice types more
  await mcp.browser_tab_select({ index: users[0].tabIndex });
  await mcp.browser_type({
    element: 'Editor',
    ref: editor.ref,
    text: '\nThis is a second line typed by Alice.'
  });
  
  // Check if Bob sees the update
  await mcp.browser_tab_select({ index: users[1].tabIndex });
  await mcp.browser_wait_for({ 
    text: 'This is a second line typed by Alice',
    timeout: 5000 
  });
  
  test.results.phases.push({
    name: 'Real-time Sync Test',
    duration: Date.now() - phase3Start,
    status: syncWorking ? 'passed' : 'failed'
  });
  
  // Phase 4: Test conflict resolution
  console.log('⚔️ Phase 4: Testing conflict resolution...');
  const phase4Start = Date.now();
  
  // Both users try to edit simultaneously
  const simultaneousEdits = await Promise.allSettled([
    (async () => {
      await mcp.browser_tab_select({ index: users[0].tabIndex });
      await mcp.browser_type({
        element: 'Editor',
        ref: editor.ref,
        text: '\nAlice adds this line.'
      });
    })(),
    (async () => {
      await mcp.browser_tab_select({ index: users[1].tabIndex });
      // Bob shouldn't be able to edit as a viewer
      try {
        const bobEditor = findElementInSnapshot(await mcp.browser_snapshot(), {
          role: 'textbox',
          name: /editor/i
        });
        await mcp.browser_type({
          element: 'Editor',
          ref: bobEditor.ref,
          text: '\nBob tries to add this line.'
        });
        
        test.results.bugs.push({
          type: 'permission_violation',
          description: 'Viewer was able to edit document',
          severity: 'high'
        });
      } catch (error) {
        // Expected - Bob shouldn't be able to edit
        console.log('✅ Correctly prevented viewer from editing');
      }
    })()
  ]);
  
  test.results.phases.push({
    name: 'Conflict Resolution',
    duration: Date.now() - phase4Start,
    status: 'completed'
  });
  
  // Phase 5: Performance analysis
  console.log('📊 Phase 5: Analyzing performance...');
  const phase5Start = Date.now();
  
  // Analyze WebSocket messages
  const aliceMessages = users[0].wsMonitor.messages;
  const bobMessages = users[1].wsMonitor.messages;
  
  const aliceAnalysis = analyzeWebSocketMessages(aliceMessages);
  const bobAnalysis = analyzeWebSocketMessages(bobMessages);
  
  test.results.performance = {
    alice: {
      totalMessages: aliceAnalysis.totalMessages,
      averageLatency: aliceAnalysis.stats.averageLatency,
      messagesPerSecond: aliceAnalysis.stats.messagesPerSecond
    },
    bob: {
      totalMessages: bobAnalysis.totalMessages,
      averageLatency: bobAnalysis.stats.averageLatency,
      messagesPerSecond: bobAnalysis.stats.messagesPerSecond
    },
    syncDelay: calculateSyncDelay(aliceMessages, bobMessages)
  };
  
  test.results.phases.push({
    name: 'Performance Analysis',
    duration: Date.now() - phase5Start,
    status: 'completed'
  });
  
  // Generate final report
  test.endTime = Date.now();
  test.totalDuration = test.endTime - test.startTime;
  
  generateTestReport(test);
  
  // Close tabs
  for (const user of users) {
    await mcp.browser_tab_select({ index: user.tabIndex });
    await mcp.browser_tab_close();
  }
  
  return test.results;
}

function calculateSyncDelay(senderMessages, receiverMessages) {
  const delays = [];
  
  senderMessages.forEach(sent => {
    if (sent.type === 'sent' && sent.parsedData?.type === 'content_update') {
      const received = receiverMessages.find(recv => 
        recv.type === 'received' &&
        recv.parsedData?.id === sent.parsedData.id &&
        recv.timestamp > sent.timestamp
      );
      
      if (received) {
        delays.push(received.timestamp - sent.timestamp);
      }
    }
  });
  
  return delays.length > 0 
    ? delays.reduce((sum, d) => sum + d, 0) / delays.length 
    : 0;
}

function generateTestReport(test) {
  const report = `
# Collaborative Editor Test Report
Generated: ${new Date().toISOString()}

## Test Summary
- **Name**: ${test.name}
- **Duration**: ${test.totalDuration}ms
- **Status**: ${test.results.bugs.length === 0 ? 'PASSED' : 'FAILED'}

## Phases
${test.results.phases.map(phase => 
  `- ${phase.name}: ${phase.status} (${phase.duration}ms)`
).join('\n')}

## Bugs Found
${test.results.bugs.length === 0 
  ? 'No bugs detected! ✅' 
  : test.results.bugs.map(bug => 
    `- **${bug.type}** (${bug.severity}): ${bug.description}`
  ).join('\n')}

## Performance Metrics
### Alice (Editor)
- Total Messages: ${test.results.performance.alice.totalMessages}
- Average Latency: ${test.results.performance.alice.averageLatency}ms
- Messages/Second: ${test.results.performance.alice.messagesPerSecond}

### Bob (Viewer)  
- Total Messages: ${test.results.performance.bob.totalMessages}
- Average Latency: ${test.results.performance.bob.averageLatency}ms
- Messages/Second: ${test.results.performance.bob.messagesPerSecond}

### Synchronization
- Average Sync Delay: ${test.results.performance.syncDelay}ms

## Recommendations
${generateRecommendations(test.results)}
`;
  
  console.log(report);
  
  // Save to file
  require('fs').writeFileSync(
    `test-report-${Date.now()}.md`,
    report
  );
}

function generateRecommendations(results) {
  const recommendations = [];
  
  if (results.performance.syncDelay > 1000) {
    recommendations.push('- Consider optimizing WebSocket message batching to reduce sync delay');
  }
  
  if (results.bugs.some(b => b.type === 'permission_violation')) {
    recommendations.push('- Review and strengthen permission checks on the server side');
  }
  
  if (results.performance.alice.messagesPerSecond > 10) {
    recommendations.push('- Implement debouncing for editor updates to reduce message frequency');
  }
  
  return recommendations.length > 0 
    ? recommendations.join('\n')
    : '- All metrics within acceptable ranges';
}

// Run the test
if (require.main === module) {
  testCollaborativeEditor().catch(console.error);
}
```

## Performance Optimization

### 1. Batch Operations

```javascript
// Batch multiple operations for better performance
async function batchOperations() {
  // ❌ Slow - Sequential operations
  await mcp.browser_type({ element: 'First name', ref: 'input-1', text: 'John' });
  await mcp.browser_type({ element: 'Last name', ref: 'input-2', text: 'Doe' });
  await mcp.browser_type({ element: 'Email', ref: 'input-3', text: 'john@example.com' });
  
  // ✅ Fast - Batch operations using evaluate
  await mcp.browser_evaluate({
    function: `() => {
      document.getElementById('input-1').value = 'John';
      document.getElementById('input-2').value = 'Doe';
      document.getElementById('input-3').value = 'john@example.com';
      
      // Trigger change events
      ['input-1', 'input-2', 'input-3'].forEach(id => {
        const event = new Event('change', { bubbles: true });
        document.getElementById(id).dispatchEvent(event);
      });
    }`
  });
}
```

### 2. Parallel Testing

```javascript
// Run independent tests in parallel
async function runParallelTests(testSuites) {
  const results = await Promise.all(
    testSuites.map(async (suite) => {
      // Each suite runs in its own tab
      await mcp.browser_tab_new();
      const tabs = await mcp.browser_tab_list();
      const tabIndex = tabs.length - 1;
      
      await mcp.browser_tab_select({ index: tabIndex });
      
      try {
        const suiteResults = await suite.run();
        return { suite: suite.name, ...suiteResults };
      } finally {
        await mcp.browser_tab_close({ index: tabIndex });
      }
    })
  );
  
  return results;
}
```

### 3. Smart Waiting

```javascript
// Implement intelligent waiting strategies
async function smartWait(conditions) {
  const waitStrategies = {
    // Wait for specific element count
    elementCount: async (selector, count) => {
      await mcp.browser_wait_for({
        function: `() => document.querySelectorAll('${selector}').length >= ${count}`
      });
    },
    
    // Wait for API response
    apiResponse: async (endpoint) => {
      await mcp.browser_evaluate({
        function: `() => {
          return new Promise(resolve => {
            const observer = new PerformanceObserver((list) => {
              for (const entry of list.getEntries()) {
                if (entry.name.includes('${endpoint}') && entry.responseEnd > 0) {
                  observer.disconnect();
                  resolve();
                }
              }
            });
            observer.observe({ entryTypes: ['resource'] });
          });
        }`
      });
    },
    
    // Wait for animation completion
    animationComplete: async (element) => {
      await mcp.browser_evaluate({
        function: `() => {
          const el = document.querySelector('${element}');
          return new Promise(resolve => {
            el.addEventListener('animationend', resolve, { once: true });
            el.addEventListener('transitionend', resolve, { once: true });
            
            // Timeout fallback
            setTimeout(resolve, 5000);
          });
        }`
      });
    }
  };
  
  // Execute appropriate strategy
  for (const [strategy, params] of Object.entries(conditions)) {
    if (waitStrategies[strategy]) {
      await waitStrategies[strategy](...params);
    }
  }
}
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Element Not Found

```javascript
// Problem: Element reference becomes stale
// Solution: Re-fetch snapshot before interaction
async function robustElementInteraction(elementCriteria, action) {
  let attempts = 0;
  const maxAttempts = 3;
  
  while (attempts < maxAttempts) {
    try {
      // Fresh snapshot for each attempt
      const snapshot = await mcp.browser_snapshot();
      const element = findElementInSnapshot(snapshot, elementCriteria);
      
      if (!element) {
        throw new Error(`Element not found: ${JSON.stringify(elementCriteria)}`);
      }
      
      await action(element);
      return; // Success
      
    } catch (error) {
      attempts++;
      console.log(`Attempt ${attempts} failed: ${error.message}`);
      
      if (attempts < maxAttempts) {
        // Wait with exponential backoff
        await new Promise(resolve => 
          setTimeout(resolve, Math.pow(2, attempts) * 1000)
        );
      } else {
        throw error;
      }
    }
  }
}
```

#### 2. WebSocket Connection Issues

```javascript
// Monitor and handle WebSocket disconnections
async function monitorWebSocketHealth() {
  await mcp.browser_evaluate({
    function: `() => {
      let reconnectAttempts = 0;
      const maxReconnects = 5;
      
      window.__wsHealthCheck = {
        connected: false,
        reconnecting: false,
        lastError: null
      };
      
      const originalWS = window.WebSocket;
      window.WebSocket = function(...args) {
        const ws = new originalWS(...args);
        
        ws.addEventListener('open', () => {
          window.__wsHealthCheck.connected = true;
          window.__wsHealthCheck.reconnecting = false;
          reconnectAttempts = 0;
        });
        
        ws.addEventListener('close', (event) => {
          window.__wsHealthCheck.connected = false;
          
          if (!event.wasClean && reconnectAttempts < maxReconnects) {
            window.__wsHealthCheck.reconnecting = true;
            reconnectAttempts++;
            
            setTimeout(() => {
              console.log('Attempting WebSocket reconnection...');
              new window.WebSocket(ws.url);
            }, Math.pow(2, reconnectAttempts) * 1000);
          }
        });
        
        ws.addEventListener('error', (error) => {
          window.__wsHealthCheck.lastError = error.message;
        });
        
        return ws;
      };
    }`
  });
}
```

#### 3. Performance Degradation

```javascript
// Detect and handle performance issues
async function monitorPerformance() {
  const performanceThresholds = {
    longTask: 50, // ms
    highMemory: 100 * 1024 * 1024, // 100MB
    slowNetwork: 3000 // ms
  };
  
  // Set up performance observer
  await mcp.browser_evaluate({
    function: `(thresholds) => {
      window.__performanceIssues = [];
      
      // Monitor long tasks
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.duration > ${performanceThresholds.longTask}) {
            window.__performanceIssues.push({
              type: 'long_task',
              duration: entry.duration,
              timestamp: Date.now()
            });
          }
        }
      });
      observer.observe({ entryTypes: ['longtask'] });
      
      // Monitor memory
      if (performance.memory) {
        setInterval(() => {
          if (performance.memory.usedJSHeapSize > ${performanceThresholds.highMemory}) {
            window.__performanceIssues.push({
              type: 'high_memory',
              usage: performance.memory.usedJSHeapSize,
              timestamp: Date.now()
            });
          }
        }, 5000);
      }
    }`
  });
  
  // Periodically check for issues
  const checkPerformance = async () => {
    const issues = await mcp.browser_evaluate({
      function: "() => window.__performanceIssues || []"
    });
    
    if (issues.length > 0) {
      console.warn('Performance issues detected:', issues);
      
      // Take corrective action
      if (issues.some(i => i.type === 'high_memory')) {
        // Clear caches, close unused tabs, etc.
        await mcp.browser_evaluate({
          function: "() => { if (window.gc) window.gc(); }"
        });
      }
    }
  };
  
  return setInterval(checkPerformance, 10000);
}
```

#### 4. Browser-Specific Issues

```javascript
// Handle browser-specific quirks
async function crossBrowserTest(testFn) {
  const browsers = ['chromium', 'firefox', 'webkit'];
  const results = {};
  
  for (const browser of browsers) {
    console.log(`Testing on ${browser}...`);
    
    try {
      // Browser-specific setup
      if (browser === 'firefox') {
        // Firefox-specific configurations
        await mcp.browser_evaluate({
          function: "() => { window.geckoProfiler?.stop(); }"
        });
      } else if (browser === 'webkit') {
        // Safari-specific configurations
        await mcp.browser_evaluate({
          function: "() => { window.webkit?.messageHandlers?.setup?.postMessage({}); }"
        });
      }
      
      // Run test
      results[browser] = await testFn();
      
    } catch (error) {
      results[browser] = {
        error: error.message,
        stack: error.stack
      };
    }
  }
  
  return results;
}
```

## Key Takeaways for AI

1. **Always use accessibility snapshots** - They're faster and more reliable than visual selectors
2. **Batch operations when possible** - Use evaluate for multiple DOM operations
3. **Cache snapshots** - Don't re-fetch unless DOM has changed
4. **Handle errors gracefully** - Implement retry logic with exponential backoff
5. **Monitor WebSocket health** - Critical for real-time applications
6. **Use semantic locators** - Prefer role and name over CSS selectors
7. **Implement smart waiting** - Wait for specific conditions, not fixed timeouts
8. **Track performance metrics** - Monitor latency, memory, and response times
9. **Test across browsers** - Handle browser-specific behaviors
10. **Generate comprehensive reports** - Include timelines, metrics, and recommendations

This updated guide provides a complete reference for AI assistants to create sophisticated browser tests using the latest Playwright MCP features and best practices for 2025.