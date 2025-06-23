import React from 'react';
import Button from './Button';

const PlayerSlot = ({ 
  slotId, 
  occupant, 
  isHost = false,
  isCurrentPlayer = false,
  canModify = false,
  playerName = null,
  score = null,
  onJoin,
  onAddBot,
  onRemove,
  className = ''
}) => {
  const getSlotClasses = () => {
    const baseClasses = `
      flex flex-col items-center justify-center p-4 rounded-lg border-2 min-h-[120px]
      transition-all duration-200 hover:shadow-md
    `;
    
    if (!occupant) {
      return `${baseClasses} border-dashed border-gray-300 bg-gray-50 hover:border-gray-400`;
    }
    if (isHost) {
      return `${baseClasses} border-yellow-400 bg-yellow-50 shadow-sm`;
    }
    if (isCurrentPlayer) {
      return `${baseClasses} border-blue-500 bg-blue-50 shadow-sm ring-2 ring-blue-200`;
    }
    if (occupant.is_bot || occupant.isBot) {
      return `${baseClasses} border-purple-400 bg-purple-50`;
    }
    return `${baseClasses} border-gray-400 bg-white`;
  };

  const renderSlotContent = () => {
    if (!occupant) {
      return (
        <div className="flex flex-col items-center space-y-3">
          <div className="text-sm text-gray-500 font-medium">Slot {slotId}</div>
          <div className="text-xs text-gray-400">Empty</div>
          
          <div className="flex flex-col space-y-2 w-full">
            {onJoin && (
              <Button size="sm" fullWidth onClick={() => onJoin(slotId)}>
                Join Slot
              </Button>
            )}
            {onAddBot && canModify && (
              <Button variant="outline" size="sm" fullWidth onClick={() => onAddBot(slotId)}>
                Add Bot
              </Button>
            )}
          </div>
        </div>
      );
    }

    const displayName = occupant.name || playerName || 'Unknown';
    const isBot = occupant.is_bot || occupant.isBot;

    return (
      <div className="flex flex-col items-center space-y-2 w-full">
        {/* Player info header */}
        <div className="flex items-center space-x-2">
          {isHost && <span className="text-lg" title="Host">👑</span>}
          {isBot && <span className="text-lg" title="Bot">🤖</span>}
          <div className="text-center">
            <div className="font-medium text-sm truncate max-w-[100px]" title={displayName}>
              {displayName}
            </div>
            <div className="text-xs text-gray-500">
              Slot {slotId}
            </div>
          </div>
          {isCurrentPlayer && (
            <span className="text-xs font-bold text-blue-600 bg-blue-100 px-2 py-1 rounded">
              YOU
            </span>
          )}
        </div>

        {/* Score display if available */}
        {typeof score === 'number' && (
          <div className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
            Score: {score}
          </div>
        )}
        
        {/* Action buttons for host/moderator */}
        {canModify && onRemove && !isCurrentPlayer && (
          <div className="flex flex-col space-y-1 w-full">
            <Button 
              variant="danger" 
              size="sm" 
              fullWidth
              onClick={() => onRemove(slotId)}
            >
              {isBot ? 'Remove Bot' : 'Kick Player'}
            </Button>
            {!isBot && onAddBot && (
              <Button 
                variant="ghost" 
                size="sm" 
                fullWidth
                onClick={() => onAddBot(slotId)}
              >
                Replace with Bot
              </Button>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`${getSlotClasses()} ${className}`}>
      {renderSlotContent()}
    </div>
  );
};

export default PlayerSlot;