/**
 * 🎮 **Game Components Index** - Unified exports for game-related components
 * 
 * Exports game container and remaining UI components
 */

// UI Components
export { default as WaitingUI } from './WaitingUI';
export { default as GameLayout } from './GameLayout';

// Smart Container Component
export { default as GameContainer } from './GameContainer';

// Content Components (used directly by GameContainer)
export { default as PreparationContent } from './content/PreparationContent';
export { default as DeclarationContent } from './content/DeclarationContent';
export { default as TurnContent } from './content/TurnContent';
export { default as TurnResultsContent } from './content/TurnResultsContent';
export { default as ScoringContent } from './content/ScoringContent';
export { default as GameOverContent } from './content/GameOverContent';