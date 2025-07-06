/**
 * Hook to integrate UnifiedGameUI with existing game state
 * 
 * This demonstrates how to use the UnifiedGameUI component
 * with your existing game manager and WebSocket connections.
 */

import { useMemo } from 'react';

export function useUnifiedGameUI(gameManager, networkManager) {
  // Map game state to UnifiedGameUI props
  const unifiedProps = useMemo(() => {
    if (!gameManager) return {};
    
    const gameState = gameManager.getState();
    const currentPhase = gameState.phase;
    const phaseData = gameState.phase_data || {};
    
    // Common props
    const commonProps = {
      phase: currentPhase,
      myHand: gameState.my_hand || [],
      players: gameState.players || [],
      roundNumber: gameState.round_number || 1,
    };
    
    // Phase-specific props
    switch (currentPhase) {
      case 'PREPARATION':
        return {
          ...commonProps,
          weakHands: phaseData.weak_hands || [],
          redealMultiplier: phaseData.redeal_multiplier || 1,
          isMyHandWeak: phaseData.is_my_hand_weak || false,
          isMyDecision: phaseData.is_my_decision || false,
          onAcceptRedeal: () => networkManager.sendAction('accept_redeal'),
          onDeclineRedeal: () => networkManager.sendAction('decline_redeal'),
        };
        
      case 'DECLARATION':
        return {
          ...commonProps,
          declarations: phaseData.declarations || {},
          currentTotal: phaseData.current_total || 0,
          isMyTurnToDeclare: phaseData.is_my_turn || false,
          validOptions: phaseData.valid_options || [],
          isLastPlayer: phaseData.is_last_player || false,
          onDeclare: (value) => networkManager.sendAction('declare', { value }),
        };
        
      case 'TURN':
        return {
          ...commonProps,
          currentTurnPlays: phaseData.current_turn_plays || [],
          requiredPieceCount: phaseData.required_piece_count || null,
          turnNumber: phaseData.turn_number || 1,
          isMyTurn: phaseData.is_my_turn || false,
          canPlayAnyCount: phaseData.can_play_any_count || false,
          currentPlayer: phaseData.current_player || '',
          onPlayPieces: (indices) => networkManager.sendAction('play_pieces', { indices }),
        };
        
      default:
        return commonProps;
    }
  }, [gameManager, networkManager]);
  
  return unifiedProps;
}

/**
 * Example usage in a component:
 * 
 * import UnifiedGameUI from './components/game/UnifiedGameUI';
 * import { useUnifiedGameUI } from './hooks/useUnifiedGameUI';
 * 
 * function GamePage() {
 *   const gameManager = useGameManager();
 *   const networkManager = useNetworkManager();
 *   const gameUIProps = useUnifiedGameUI(gameManager, networkManager);
 *   
 *   return <UnifiedGameUI {...gameUIProps} />;
 * }
 */