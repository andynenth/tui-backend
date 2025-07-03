/**
 * 🎯 **useActionManager Hook** - Phase 5.3 Clean State Flow
 * 
 * React hook for managing game actions with confirmation flow:
 * ✅ Action dispatch with loading states
 * ✅ Automatic retry mechanisms
 * ✅ User feedback integration
 * ✅ Pending action tracking
 */

import { useState, useEffect, useCallback } from 'react';
import { actionManager, type ActionResult, type ActionState, type GameAction } from '../stores/ActionManager';
import { gameStore } from '../stores/UnifiedGameStore';

export interface ActionManagerHook {
  // Action dispatch
  dispatch: (actionType: GameAction['type'], payload: Record<string, any>) => Promise<ActionResult>;
  
  // Action state
  pendingActions: ActionState[];
  isActionPending: (actionType: GameAction['type']) => boolean;
  getActionState: (actionId: string) => ActionState | null;
  
  // Action control
  retryAction: (actionId: string) => Promise<ActionResult>;
  cancelAction: (actionId: string) => boolean;
  
  // Helper methods
  isAnyActionPending: boolean;
  lastActionResult: ActionResult | null;
}

export const useActionManager = (): ActionManagerHook => {
  const [pendingActions, setPendingActions] = useState<ActionState[]>([]);
  const [lastActionResult, setLastActionResult] = useState<ActionResult | null>(null);

  // Update pending actions when store changes
  useEffect(() => {
    const unsubscribe = gameStore.subscribe((state) => {
      const actionStates = state.actionStates || {};
      const pending = Object.values(actionStates).filter((action: any) => 
        action.status === 'pending'
      ) as ActionState[];
      setPendingActions(pending);
    });

    // Initial load
    const state = gameStore.getState();
    const actionStates = state.actionStates || {};
    const pending = Object.values(actionStates).filter((action: any) => 
      action.status === 'pending'
    ) as ActionState[];
    setPendingActions(pending);

    return unsubscribe;
  }, []);

  // Listen for action results
  useEffect(() => {
    const handleActionResult = (event: Event) => {
      const customEvent = event as CustomEvent;
      const { actionId, success, error, data } = customEvent.detail;
      
      setLastActionResult({
        success,
        actionId,
        error,
        data
      });
    };

    actionManager.addEventListener('actionConfirmed', handleActionResult);
    actionManager.addEventListener('actionFailed', handleActionResult);
    actionManager.addEventListener('actionCancelled', handleActionResult);

    return () => {
      actionManager.removeEventListener('actionConfirmed', handleActionResult);
      actionManager.removeEventListener('actionFailed', handleActionResult);
      actionManager.removeEventListener('actionCancelled', handleActionResult);
    };
  }, []);

  // Dispatch action
  const dispatch = useCallback(async (
    actionType: GameAction['type'], 
    payload: Record<string, any>
  ): Promise<ActionResult> => {
    try {
      const result = await actionManager.dispatch(actionType, payload);
      setLastActionResult(result);
      return result;
    } catch (error) {
      const errorResult: ActionResult = {
        success: false,
        actionId: '',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
      setLastActionResult(errorResult);
      return errorResult;
    }
  }, []);

  // Check if specific action type is pending
  const isActionPending = useCallback((actionType: GameAction['type']): boolean => {
    return pendingActions.some(action => action.action.type === actionType);
  }, [pendingActions]);

  // Get action state by ID
  const getActionState = useCallback((actionId: string): ActionState | null => {
    return actionManager.getActionState(actionId);
  }, []);

  // Retry action
  const retryAction = useCallback(async (actionId: string): Promise<ActionResult> => {
    try {
      const result = await actionManager.retryAction(actionId);
      setLastActionResult(result);
      return result;
    } catch (error) {
      const errorResult: ActionResult = {
        success: false,
        actionId,
        error: error instanceof Error ? error.message : 'Retry failed'
      };
      setLastActionResult(errorResult);
      return errorResult;
    }
  }, []);

  // Cancel action
  const cancelAction = useCallback((actionId: string): boolean => {
    return actionManager.cancelAction(actionId);
  }, []);

  // Check if any action is pending
  const isAnyActionPending = pendingActions.length > 0;

  return {
    dispatch,
    pendingActions,
    isActionPending,
    getActionState,
    retryAction,
    cancelAction,
    isAnyActionPending,
    lastActionResult
  };
};

// Convenience hooks for specific action types
export const useGameActions = () => {
  const { dispatch, isActionPending, lastActionResult } = useActionManager();

  return {
    // Game actions with loading states
    playPieces: useCallback(async (indices: number[]) => {
      return dispatch('play_pieces', { piece_indices: indices });
    }, [dispatch]),

    makeDeclaration: useCallback(async (value: number) => {
      return dispatch('declare', { value });
    }, [dispatch]),

    submitRedealDecision: useCallback(async (accept: boolean) => {
      return dispatch('redeal_decision', { 
        action_type: 'redeal_decision',
        accept 
      });
    }, [dispatch]),

    requestRedeal: useCallback(async () => {
      return dispatch('request_redeal', { 
        action_type: 'request_redeal' 
      });
    }, [dispatch]),

    // Loading states
    isPlayingPieces: isActionPending('play_pieces'),
    isDeclaring: isActionPending('declare'),
    isSubmittingRedeal: isActionPending('redeal_decision'),
    isRequestingRedeal: isActionPending('request_redeal'),

    // Last result
    lastActionResult
  };
};

export default useActionManager;