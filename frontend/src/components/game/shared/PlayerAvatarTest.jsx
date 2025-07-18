import React from 'react';
import PlayerAvatar from './PlayerAvatar';

/**
 * Test component for PlayerAvatar bot functionality
 * This is a temporary component for testing the bot avatar implementation
 */
const PlayerAvatarTest = () => {
  const testPlayers = [
    { name: 'Human Player', is_bot: false },
    { name: 'Bot Player', is_bot: true },
    { name: 'Thinking Bot', is_bot: true, isThinking: true },
  ];

  return (
    <div style={{ padding: '20px', backgroundColor: '#f0f0f0' }}>
      <h2>PlayerAvatar Test - Bot Indicators</h2>
      
      <div style={{ display: 'flex', gap: '20px', marginTop: '20px' }}>
        <div>
          <h3>Small Size</h3>
          {testPlayers.map((player, idx) => (
            <div key={idx} style={{ margin: '10px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <PlayerAvatar 
                name={player.name} 
                isBot={player.is_bot}
                isThinking={player.isThinking}
                size="small"
              />
              <span>{player.name}</span>
            </div>
          ))}
        </div>

        <div>
          <h3>Medium Size</h3>
          {testPlayers.map((player, idx) => (
            <div key={idx} style={{ margin: '10px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <PlayerAvatar 
                name={player.name} 
                isBot={player.is_bot}
                isThinking={player.isThinking}
                size="medium"
              />
              <span>{player.name}</span>
            </div>
          ))}
        </div>

        <div>
          <h3>Large Size</h3>
          {testPlayers.map((player, idx) => (
            <div key={idx} style={{ margin: '10px 0', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <PlayerAvatar 
                name={player.name} 
                isBot={player.is_bot}
                isThinking={player.isThinking}
                size="large"
              />
              <span>{player.name}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: '30px' }}>
        <h3>States</h3>
        <div style={{ display: 'flex', gap: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <PlayerAvatar name="Active Bot" isBot={true} className="active" size="large" />
            <span>Active State</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <PlayerAvatar name="Winner Bot" isBot={true} className="winner" size="large" />
            <span>Winner State</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlayerAvatarTest;