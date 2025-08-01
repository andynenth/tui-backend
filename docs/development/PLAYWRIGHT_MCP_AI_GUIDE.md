# AI Guide: Using Playwright MCP for Testing

## Overview

Playwright MCP (Model Context Protocol) enables AI assistants to create browser tests using structured accessibility data instead of screenshots. This approach is faster, more reliable, and better suited for AI automation.

### Key Advantages
- **Accessibility Tree-Based**: Uses semantic web structure, not visual selectors
- **LLM-Friendly**: Operates on structured data, no vision models needed
- **Deterministic**: Avoids ambiguity from visual approaches
- **Cross-Browser**: Supports Chromium, Firefox, WebKit, and Edge
- **Performance**: 3-5x faster than screenshot-based automation

## Installation & Setup

```bash
# Install Playwright MCP
claude mcp add playwright npx @playwright/mcp@latest

# Verify installation
claude mcp status
```

## Server Management

### Starting the Development Server

```bash
# Kill any existing server processes
pkill -f uvicorn

# Start server in background (use & to run in background)
./start.sh &

# Use Playwright IMMEDIATELY after ./start.sh & - don't wait!
```

### ⚡ Critical: Immediate Playwright Usage

**Key Insight**: You can use Playwright MCP tools immediately after `./start.sh &` - the `&` runs the server in background, so there's no need to wait for server startup logs to complete.

```javascript
// ✅ Correct approach:
// 1. ./start.sh &
// 2. Immediately use Playwright (don't wait!)
await mcp.browser_navigate({ url: 'http://localhost:5050' });

// ❌ Wrong approach:
// 1. ./start.sh &
// 2. Wait for server logs to finish
// 3. Then use Playwright (unnecessary delay!)
```

### Browser Mode

Playwright MCP typically runs in **headless mode** (no visible browser window). The automation works perfectly in the background:
- All interactions are logged in the MCP response
- Page snapshots show current state
- Console messages are captured
- No browser window appears (normal behavior)

## Core Architecture

Playwright MCP uses the accessibility tree to understand web pages. Each element has properties like:

```javascript
{
  role: "button",
  name: "Submit",
  ref: "button-123",  // Unique reference for interactions
  disabled: false,
  children: []
}
```

## Essential MCP Tools

### Navigation
- `browser_navigate({ url, waitUntil })` - Navigate to URL
- `browser_wait_for({ text, timeout })` - Wait for conditions

### Interaction  
- `browser_click({ element, ref })` - Click elements
- `browser_type({ element, ref, text })` - Type text
- `browser_press_key({ key })` - Press keys

### Content Capture
- `browser_snapshot()` - Get accessibility tree
- `browser_console_messages()` - Get console logs

### Tabs
- `browser_tab_new()` - Create new tab
- `browser_tab_select({ index })` - Switch tabs

## Complete Workflow Example

### Server Restart + Browser Automation

```bash
# 1. Restart server
pkill -f uvicorn
./start.sh &

# 2. Immediately use Playwright (don't wait for logs!)
```

```javascript
// Navigate to application
await mcp.browser_navigate({ url: 'http://localhost:5050' });

// Click Enter Lobby button
await mcp.browser_click({
  element: 'Enter Lobby button',
  ref: 'e25'  // Reference from page snapshot
});
```

### Real Example: Liap TUI Game

```javascript
async function enterGameLobby() {
  // Navigate to game
  await mcp.browser_navigate({ url: 'http://localhost:5050' });
  
  // Game loads with TestPlayer already in name field
  // Click Enter Lobby button
  await mcp.browser_click({
    element: 'Enter Lobby button',
    ref: 'e25'
  });
  
  // Result: Now in lobby with "Game Lobby" heading
  // Page URL: http://localhost:5050/lobby
  // Shows: Available Rooms (0), Create Room, Join by ID buttons
}
```

## Basic Test Pattern

```javascript
async function testLogin() {
  // Navigate to page
  await mcp.browser_navigate({ url: 'http://localhost:3000' });
  
  // Get page structure
  const snapshot = await mcp.browser_snapshot();
  
  // Find elements by accessibility properties
  const emailInput = findElementInSnapshot(snapshot, {
    role: 'textbox',
    name: /email/i
  });
  
  const loginButton = findElementInSnapshot(snapshot, {
    role: 'button', 
    name: /login/i
  });
  
  // Interact with elements
  await mcp.browser_type({
    element: 'Email input',
    ref: emailInput.ref,
    text: 'user@example.com'
  });
  
  await mcp.browser_click({
    element: 'Login button',
    ref: loginButton.ref
  });
  
  // Wait for result
  await mcp.browser_wait_for({ text: 'Dashboard', timeout: 5000 });
}

// Helper function to find elements
function findElementInSnapshot(snapshot, criteria) {
  function search(node) {
    const matches = Object.entries(criteria).every(([key, value]) => {
      if (value instanceof RegExp) {
        return value.test(node[key]);
      }
      return node[key] === value;
    });
    
    if (matches) return node;
    
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
```

## Best Practices

### 1. Use Accessibility-First Approach
```javascript
// ✅ Good - Uses semantic roles
const button = findElementInSnapshot(snapshot, {
  role: 'button',
  name: /submit/i
});

// ❌ Avoid - CSS selectors are fragile
const button = await page.$('.btn-primary-submit');
```

### 2. Cache Snapshots for Multiple Operations
```javascript
// Take snapshot once, use for multiple elements
const snapshot = await mcp.browser_snapshot();
const email = findElementInSnapshot(snapshot, { role: 'textbox', name: /email/i });
const password = findElementInSnapshot(snapshot, { role: 'textbox', name: /password/i });
const submit = findElementInSnapshot(snapshot, { role: 'button', name: /submit/i });
```

### 3. Handle Errors Gracefully
```javascript
async function robustClick(element, ref, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      await mcp.browser_click({ element, ref });
      return; // Success
    } catch (error) {
      if (attempt === maxRetries) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
}
```

## WebSocket Monitoring

For real-time applications, monitor WebSocket messages:

```javascript
async function captureWebSocketMessages() {
  await mcp.browser_evaluate({
    function: `() => {
      window.__wsMessages = [];
      const originalWS = window.WebSocket;
      
      window.WebSocket = function(...args) {
        const ws = new originalWS(...args);
        
        ws.addEventListener('message', (event) => {
          window.__wsMessages.push({
            type: 'received',
            data: event.data,
            timestamp: Date.now()
          });
        });
        
        return ws;
      };
    }`
  });
  
  // Later, retrieve messages
  const messages = await mcp.browser_evaluate({
    function: "() => window.__wsMessages || []"
  });
  
  return messages;
}
```

## Troubleshooting

### Common Issues

#### 1. Element Not Found
- **Problem**: Element reference becomes stale after DOM changes
- **Solution**: Re-fetch snapshot before each interaction

```javascript
async function robustInteraction(elementCriteria, action) {
  const snapshot = await mcp.browser_snapshot();
  const element = findElementInSnapshot(snapshot, elementCriteria);
  
  if (!element) {
    throw new Error(`Element not found: ${JSON.stringify(elementCriteria)}`);
  }
  
  await action(element);
}
```

#### 2. Timing Issues
- **Problem**: Actions happen too fast for UI updates
- **Solution**: Use appropriate waits

```javascript
// Wait for specific text to appear
await mcp.browser_wait_for({ text: 'Loading complete', timeout: 5000 });

// Wait for animations to finish
await new Promise(resolve => setTimeout(resolve, 1000));
```

#### 3. Console Messages for Debugging
- **Best Practice**: Always check console messages for internal state

```javascript
const messages = await mcp.browser_console_messages();
console.log('Console output:', messages);
```

### Key Takeaways

1. **Accessibility First**: Use semantic roles and labels over CSS selectors
2. **Fresh Snapshots**: Re-fetch after DOM changes or animations  
3. **Generous Timeouts**: Real-time apps need time for network events
4. **Console Debugging**: Check console messages for internal application state
5. **Error Handling**: Implement retry logic for flaky operations
6. **Cache Snapshots**: When performing multiple operations on the same page
7. **Test Phases**: Break complex workflows into separate testable phases

