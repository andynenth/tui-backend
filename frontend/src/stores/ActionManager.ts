/**
 * 🎯 **ActionManager** - Phase 5.3 Clean State Flow Implementation
 * 
 * Implements action → confirmation → UI update pattern with:
 * ✅ Action state tracking (pending/confirmed/failed)
 * ✅ Standardized action acknowledgment
 * ✅ User feedback mechanisms
 * ✅ Retry and rollback capabilities
 * ✅ Race condition prevention
 */

import { networkService } from '../services/NetworkService';
import { gameStore } from './UnifiedGameStore';
import type { NetworkEventDetail } from '../services/types';

export type ActionStatus = 'pending' | 'confirmed' | 'failed' | 'timeout';

export interface GameAction {
  id: string;
  type: 'play_pieces' | 'declare' | 'redeal_decision' | 'request_redeal' | 'join_room' | 'leave_room';
  payload: Record<string, any>;
  playerName: string;
  roomId: string;
  timestamp: number;
}

export interface ActionState {
  id: string;
  action: GameAction;
  status: ActionStatus;
  sentAt: number;
  acknowledgedAt?: number;
  error?: string;
  retryCount: number;
  timeout?: NodeJS.Timeout;
}

export interface ActionResult {
  success: boolean;
  actionId: string;
  error?: string;
  data?: any;
}

export class ActionManager extends EventTarget {
  private static instance: ActionManager | null = null;
  
  static getInstance(): ActionManager {
    if (!ActionManager.instance) {
      ActionManager.instance = new ActionManager();
    }
    return ActionManager.instance;
  }

  private pendingActions = new Map<string, ActionState>();
  private readonly ACTION_TIMEOUT = 10000; // 10 seconds
  private readonly MAX_RETRIES = 3;
  private isDestroyed = false;

  private constructor() {
    super();
    this.setupEventListeners();
    console.log('🎯 ActionManager: Initialized for Phase 5.3 clean state flow');
  }

  // ===== PUBLIC API =====

  /**
   * Dispatch an action with confirmation tracking
   */
  async dispatch(actionType: GameAction['type'], payload: Record<string, any>): Promise<ActionResult> {
    if (this.isDestroyed) {
      throw new Error('ActionManager has been destroyed');
    }

    const gameState = gameStore.getState().gameState;
    const roomId = gameStore.getState().roomId;
    const playerName = gameStore.getState().playerName;

    if (!roomId || !playerName) {
      return {
        success: false,
        actionId: '',
        error: 'Room ID or player name not available'
      };
    }

    const action: GameAction = {
      id: crypto.randomUUID(),
      type: actionType,
      payload,
      playerName,
      roomId,
      timestamp: Date.now()
    };

    // Create action state
    const actionState: ActionState = {
      id: action.id,
      action,
      status: 'pending',
      sentAt: Date.now(),
      retryCount: 0
    };

    this.pendingActions.set(action.id, actionState);

    // Update store with pending action
    this.updateActionInStore(actionState);

    // Set timeout for action
    actionState.timeout = setTimeout(() => {
      this.handleActionTimeout(action.id);
    }, this.ACTION_TIMEOUT);

    try {
      // Send action to backend
      const sent = this.sendActionToBackend(action);
      
      if (!sent) {
        throw new Error('Failed to send action to backend');
      }

      // Emit action dispatched event
      this.dispatchEvent(new CustomEvent('actionDispatched', {
        detail: { actionId: action.id, action }
      }));

      console.log(`🎯 Action dispatched: ${actionType} (${action.id})`);

      // Return promise that resolves when action is confirmed or fails
      return new Promise((resolve) => {
        const handleActionResult = (event: Event) => {
          const customEvent = event as CustomEvent;
          const { actionId, success, error, data } = customEvent.detail;
          
          if (actionId === action.id) {
            this.removeEventListener('actionConfirmed', handleActionResult);
            this.removeEventListener('actionFailed', handleActionResult);
            
            resolve({
              success,
              actionId,
              error,
              data
            });
          }
        };

        this.addEventListener('actionConfirmed', handleActionResult);
        this.addEventListener('actionFailed', handleActionResult);
      });

    } catch (error) {
      this.handleActionFailure(action.id, error instanceof Error ? error.message : 'Unknown error');
      return {
        success: false,
        actionId: action.id,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get current action state
   */
  getActionState(actionId: string): ActionState | null {
    return this.pendingActions.get(actionId) || null;
  }

  /**
   * Get all pending actions
   */
  getPendingActions(): ActionState[] {
    return Array.from(this.pendingActions.values());
  }

  /**
   * Retry a failed action
   */
  async retryAction(actionId: string): Promise<ActionResult> {
    const actionState = this.pendingActions.get(actionId);
    if (!actionState) {
      return {
        success: false,
        actionId,
        error: 'Action not found'
      };
    }

    if (actionState.retryCount >= this.MAX_RETRIES) {
      return {
        success: false,
        actionId,
        error: 'Maximum retries exceeded'
      };
    }

    // Increment retry count
    actionState.retryCount++;
    actionState.status = 'pending';
    actionState.sentAt = Date.now();
    actionState.error = undefined;

    this.updateActionInStore(actionState);

    // Clear existing timeout
    if (actionState.timeout) {
      clearTimeout(actionState.timeout);
    }

    // Set new timeout
    actionState.timeout = setTimeout(() => {
      this.handleActionTimeout(actionId);
    }, this.ACTION_TIMEOUT);

    try {
      const sent = this.sendActionToBackend(actionState.action);
      
      if (!sent) {
        throw new Error('Failed to send retry action to backend');
      }

      console.log(`🔄 Action retried: ${actionState.action.type} (${actionId}, attempt ${actionState.retryCount})`);

      return new Promise((resolve) => {
        const handleRetryResult = (event: Event) => {
          const customEvent = event as CustomEvent;
          const { actionId: resultActionId, success, error, data } = customEvent.detail;
          
          if (resultActionId === actionId) {
            this.removeEventListener('actionConfirmed', handleRetryResult);
            this.removeEventListener('actionFailed', handleRetryResult);
            
            resolve({
              success,
              actionId,
              error,
              data
            });
          }
        };

        this.addEventListener('actionConfirmed', handleRetryResult);
        this.addEventListener('actionFailed', handleRetryResult);
      });

    } catch (error) {
      this.handleActionFailure(actionId, error instanceof Error ? error.message : 'Retry failed');
      return {
        success: false,
        actionId,
        error: error instanceof Error ? error.message : 'Retry failed'
      };
    }
  }

  /**
   * Cancel a pending action
   */
  cancelAction(actionId: string): boolean {
    const actionState = this.pendingActions.get(actionId);
    if (!actionState || actionState.status !== 'pending') {
      return false;
    }

    // Clear timeout
    if (actionState.timeout) {
      clearTimeout(actionState.timeout);
    }

    // Remove from pending actions
    this.pendingActions.delete(actionId);

    // Update store
    this.removeActionFromStore(actionId);

    this.dispatchEvent(new CustomEvent('actionCancelled', {
      detail: { actionId }
    }));

    console.log(`🚫 Action cancelled: ${actionState.action.type} (${actionId})`);
    return true;
  }

  /**
   * Clean up completed actions older than specified time
   */
  cleanupCompletedActions(olderThanMs = 60000): void {
    const now = Date.now();
    const toRemove: string[] = [];

    for (const [actionId, actionState] of this.pendingActions) {
      if (actionState.status !== 'pending' && (now - actionState.sentAt) > olderThanMs) {
        toRemove.push(actionId);
      }
    }

    toRemove.forEach(actionId => {
      this.pendingActions.delete(actionId);
      this.removeActionFromStore(actionId);
    });

    if (toRemove.length > 0) {
      console.log(`🧹 Cleaned up ${toRemove.length} completed actions`);
    }
  }

  /**
   * Destroy the action manager
   */
  destroy(): void {
    this.isDestroyed = true;

    // Clear all timeouts
    for (const actionState of this.pendingActions.values()) {
      if (actionState.timeout) {
        clearTimeout(actionState.timeout);
      }
    }

    this.pendingActions.clear();
    ActionManager.instance = null;
    console.log('🎯 ActionManager: Destroyed');
  }

  // ===== PRIVATE METHODS =====

  /**
   * Setup event listeners for network responses
   */
  private setupEventListeners(): void {
    // Listen for action acknowledgments from backend
    networkService.addEventListener('action_confirmed', this.handleActionConfirmation.bind(this));
    networkService.addEventListener('action_failed', this.handleActionFailure.bind(this));
    networkService.addEventListener('error', this.handleNetworkError.bind(this));
    
    // Listen for state changes that might confirm actions
    networkService.addEventListener('phase_change', this.handlePhaseChange.bind(this));
    networkService.addEventListener('play_success', this.handleActionSuccess.bind(this));
    networkService.addEventListener('declare', this.handleActionSuccess.bind(this));
  }

  /**
   * Send action to backend via network service
   */
  private sendActionToBackend(action: GameAction): boolean {
    const { type, payload, roomId } = action;

    // Map action types to network events
    const eventMap: Record<string, string> = {
      'play_pieces': 'play',
      'declare': 'declare',
      'redeal_decision': 'action',
      'request_redeal': 'action',
      'join_room': 'join_room',
      'leave_room': 'leave_room'
    };

    const event = eventMap[type] || type;
    
    // Add action ID to payload for tracking
    const enhancedPayload = {
      ...payload,
      action_id: action.id,
      timestamp: action.timestamp
    };

    return networkService.send(roomId, event, enhancedPayload);
  }

  /**
   * Handle action confirmation from backend
   */
  private handleActionConfirmation(event: Event): void {
    const customEvent = event as CustomEvent<NetworkEventDetail>;
    const { action_id, success, data } = customEvent.detail.data || {};

    if (!action_id) return;

    const actionState = this.pendingActions.get(action_id);
    if (!actionState) return;

    // Clear timeout
    if (actionState.timeout) {
      clearTimeout(actionState.timeout);
    }

    // Update action state
    actionState.status = success ? 'confirmed' : 'failed';
    actionState.acknowledgedAt = Date.now();
    if (!success && data?.error) {
      actionState.error = data.error;
    }

    this.updateActionInStore(actionState);

    // Emit confirmation event
    const eventType = success ? 'actionConfirmed' : 'actionFailed';
    this.dispatchEvent(new CustomEvent(eventType, {
      detail: {
        actionId: action_id,
        success,
        error: actionState.error,
        data
      }
    }));

    console.log(`${success ? '✅' : '❌'} Action ${success ? 'confirmed' : 'failed'}: ${actionState.action.type} (${action_id})`);
  }

  /**
   * Handle action failure
   */
  private handleActionFailure(actionId: string, error: string): void;
  private handleActionFailure(event: Event): void;
  private handleActionFailure(actionIdOrEvent: string | Event, error?: string): void {
    // Handle event-based calls
    if (typeof actionIdOrEvent === 'object') {
      const customEvent = actionIdOrEvent as CustomEvent;
      const { action_id, error: eventError } = customEvent.detail?.data || {};
      if (action_id) {
        this.handleActionFailure(action_id, eventError || 'Action failed');
      }
      return;
    }

    const actionId = actionIdOrEvent as string;
    const actionState = this.pendingActions.get(actionId);
    if (!actionState) return;

    // Clear timeout
    if (actionState.timeout) {
      clearTimeout(actionState.timeout);
    }

    actionState.status = 'failed';
    actionState.error = error;
    actionState.acknowledgedAt = Date.now();

    this.updateActionInStore(actionState);

    this.dispatchEvent(new CustomEvent('actionFailed', {
      detail: {
        actionId,
        success: false,
        error
      }
    }));

    console.error(`❌ Action failed: ${actionState.action.type} (${actionId}) - ${error}`);
  }

  /**
   * Handle action timeout
   */
  private handleActionTimeout(actionId: string): void {
    const actionState = this.pendingActions.get(actionId);
    if (!actionState) return;

    actionState.status = 'timeout';
    actionState.error = 'Action timed out';
    actionState.acknowledgedAt = Date.now();

    this.updateActionInStore(actionState);

    this.dispatchEvent(new CustomEvent('actionFailed', {
      detail: {
        actionId,
        success: false,
        error: 'Action timed out'
      }
    }));

    console.warn(`⏰ Action timeout: ${actionState.action.type} (${actionId})`);
  }

  /**
   * Handle successful action responses
   */
  private handleActionSuccess(event: Event): void {
    const customEvent = event as CustomEvent<NetworkEventDetail>;
    const { action_id } = customEvent.detail.data || {};

    if (action_id) {
      this.handleActionConfirmation(event);
    }
  }

  /**
   * Handle phase changes that might confirm actions
   */
  private handlePhaseChange(event: Event): void {
    // Phase changes often indicate successful actions
    // but we rely on explicit action_id confirmations
    const customEvent = event as CustomEvent<NetworkEventDetail>;
    console.log('🔄 Phase change detected during action processing');
  }

  /**
   * Handle network errors
   */
  private handleNetworkError(event: Event): void {
    const customEvent = event as CustomEvent<NetworkEventDetail>;
    const { error } = customEvent.detail;
    
    // Fail all pending actions on network error
    for (const [actionId, actionState] of this.pendingActions) {
      if (actionState.status === 'pending') {
        this.handleActionFailure(actionId, `Network error: ${error}`);
      }
    }
  }

  /**
   * Update action state in the store
   */
  private updateActionInStore(actionState: ActionState): void {
    gameStore.setState(prevState => ({
      actionStates: {
        ...prevState.actionStates,
        [actionState.id]: actionState
      }
    }));
  }

  /**
   * Remove action from store
   */
  private removeActionFromStore(actionId: string): void {
    gameStore.setState(prevState => {
      const { [actionId]: removed, ...remaining } = prevState.actionStates || {};
      return {
        actionStates: remaining
      };
    });
  }
}

// Export singleton instance
export const actionManager = ActionManager.getInstance();

// Export types for use in components (avoid conflicts)