// frontend/src/utils/tabCommunication.js

/**
 * Tab communication utilities using BroadcastChannel API
 * Detects and prevents multiple tabs from connecting to the same game
 */

const CHANNEL_NAME = 'liap_tui_tabs';
const TAB_ID = `tab_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

class TabCommunicationManager {
  constructor() {
    this.channel = null;
    this.activeTabs = new Map();
    this.isActive = false;
    this.onDuplicateCallback = null;
    this.onTabClosedCallback = null;
  }

  /**
   * Initialize tab communication
   */
  init(roomId, playerName) {
    if (!this.isSupported()) {
      console.warn('BroadcastChannel not supported in this browser');
      return false;
    }

    try {
      this.channel = new BroadcastChannel(CHANNEL_NAME);
      this.roomId = roomId;
      this.playerName = playerName;
      this.isActive = true;

      // Set up message handler
      this.channel.onmessage = (event) => this.handleMessage(event);

      // Announce this tab
      this.sendMessage({
        type: 'TAB_OPENED',
        tabId: TAB_ID,
        roomId,
        playerName,
        timestamp: Date.now(),
      });

      // Set up cleanup on tab close
      window.addEventListener('beforeunload', () => this.cleanup());

      console.log('Tab communication initialized:', TAB_ID);
      return true;
    } catch (error) {
      console.error('Failed to initialize tab communication:', error);
      return false;
    }
  }

  /**
   * Handle messages from other tabs
   */
  handleMessage(event) {
    const { type, tabId, roomId, playerName, timestamp } = event.data;

    switch (type) {
      case 'TAB_OPENED':
        if (tabId !== TAB_ID) {
          this.activeTabs.set(tabId, { roomId, playerName, timestamp });

          // Check for duplicate session
          if (roomId === this.roomId && playerName === this.playerName) {
            console.warn('Duplicate game session detected in another tab!');

            // Notify the other tab
            this.sendMessage({
              type: 'DUPLICATE_DETECTED',
              targetTabId: tabId,
              tabId: TAB_ID,
              roomId,
              playerName,
            });

            // Trigger callback if set
            if (this.onDuplicateCallback) {
              this.onDuplicateCallback({ tabId, roomId, playerName });
            }
          }

          // Respond with our presence
          this.sendMessage({
            type: 'TAB_PRESENT',
            tabId: TAB_ID,
            roomId: this.roomId,
            playerName: this.playerName,
            timestamp: Date.now(),
          });
        }
        break;

      case 'TAB_PRESENT':
        if (tabId !== TAB_ID) {
          this.activeTabs.set(tabId, { roomId, playerName, timestamp });
        }
        break;

      case 'TAB_CLOSED':
        this.activeTabs.delete(tabId);
        if (this.onTabClosedCallback) {
          this.onTabClosedCallback({ tabId, roomId, playerName });
        }
        break;

      case 'DUPLICATE_DETECTED':
        if (event.data.targetTabId === TAB_ID && this.onDuplicateCallback) {
          this.onDuplicateCallback({
            isTarget: true,
            otherTabId: tabId,
            roomId,
            playerName,
          });
        }
        break;

      case 'REQUEST_ACTIVE_TABS':
        // Respond with our presence
        this.sendMessage({
          type: 'TAB_PRESENT',
          tabId: TAB_ID,
          roomId: this.roomId,
          playerName: this.playerName,
          timestamp: Date.now(),
        });
        break;
    }
  }

  /**
   * Send message to other tabs
   */
  sendMessage(message) {
    if (this.channel && this.isActive) {
      try {
        this.channel.postMessage(message);
      } catch (error) {
        console.error('Failed to send tab message:', error);
      }
    }
  }

  /**
   * Check if another tab has the same game session
   */
  async checkForDuplicates(roomId, playerName) {
    return new Promise((resolve) => {
      const duplicates = [];

      // Clear existing tabs first
      this.activeTabs.clear();

      // Request active tabs
      this.sendMessage({
        type: 'REQUEST_ACTIVE_TABS',
        tabId: TAB_ID,
      });

      // Wait for responses
      setTimeout(() => {
        this.activeTabs.forEach((tab, tabId) => {
          if (tab.roomId === roomId && tab.playerName === playerName) {
            duplicates.push({ tabId, ...tab });
          }
        });
        resolve(duplicates);
      }, 100);
    });
  }

  /**
   * Set callback for duplicate detection
   */
  onDuplicate(callback) {
    this.onDuplicateCallback = callback;
  }

  /**
   * Set callback for tab closed events
   */
  onTabClosed(callback) {
    this.onTabClosedCallback = callback;
  }

  /**
   * Clean up and announce tab closing
   */
  cleanup() {
    if (this.channel && this.isActive) {
      this.sendMessage({
        type: 'TAB_CLOSED',
        tabId: TAB_ID,
        roomId: this.roomId,
        playerName: this.playerName,
      });

      this.channel.close();
      this.isActive = false;
    }
  }

  /**
   * Check if BroadcastChannel is supported
   */
  isSupported() {
    return typeof BroadcastChannel !== 'undefined';
  }

  /**
   * Get current tab ID
   */
  getTabId() {
    return TAB_ID;
  }

  /**
   * Get active tabs for a specific game
   */
  getActiveGameTabs(roomId) {
    const tabs = [];
    this.activeTabs.forEach((tab, tabId) => {
      if (tab.roomId === roomId) {
        tabs.push({ tabId, ...tab });
      }
    });
    return tabs;
  }
}

// Export singleton instance
export const tabCommunication = new TabCommunicationManager();

// Also export class for testing
export default TabCommunicationManager;
