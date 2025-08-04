// frontend/src/components/game/shared/PlayerAvatarTest.stylex.jsx

import React from 'react';
import PlayerAvatar from './PlayerAvatar.stylex';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography } from '../../../design-system/tokens.stylex';

const styles = stylex.create({
  container: {
    padding: spacing.lg,
    backgroundColor: colors.gray100,
    minHeight: '100vh',
  },
  
  title: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.bold,
    color: colors.text,
    marginBottom: spacing.lg,
  },
  
  testGrid: {
    display: 'flex',
    gap: spacing.lg,
    marginTop: spacing.lg,
  },
  
  sizeSection: {
    flex: 1,
  },
  
  sectionTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.semibold,
    color: colors.text,
    marginBottom: spacing.md,
  },
  
  playerRow: {
    margin: `${spacing.sm} 0`,
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
  },
  
  playerLabel: {
    fontSize: typography.fontSize.base,
    color: colors.textSecondary,
  },
  
  statesSection: {
    marginTop: spacing.xl,
  },
  
  statesGrid: {
    display: 'flex',
    gap: spacing.lg,
    marginTop: spacing.md,
  },
  
  stateItem: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
  },
});

/**
 * Test component for PlayerAvatar bot functionality
 * This is a temporary component for testing the bot avatar implementation
 */
const PlayerAvatarTest = ({ className }) => {
  const testPlayers = [
    { name: 'Human Player', is_bot: false },
    { name: 'Bot Player', is_bot: true },
    { name: 'Thinking Bot', is_bot: true, isThinking: true },
  ];

  return (
    <div {...stylex.props(styles.container, className)}>
      <h2 {...stylex.props(styles.title)}>PlayerAvatar Test - Bot Indicators</h2>

      <div {...stylex.props(styles.testGrid)}>
        <div {...stylex.props(styles.sizeSection)}>
          <h3 {...stylex.props(styles.sectionTitle)}>Small Size</h3>
          {testPlayers.map((player, idx) => (
            <div
              key={idx}
              {...stylex.props(styles.playerRow)}
            >
              <PlayerAvatar
                name={player.name}
                isBot={player.is_bot}
                isThinking={player.isThinking}
                size="small"
              />
              <span {...stylex.props(styles.playerLabel)}>{player.name}</span>
            </div>
          ))}
        </div>

        <div {...stylex.props(styles.sizeSection)}>
          <h3 {...stylex.props(styles.sectionTitle)}>Medium Size</h3>
          {testPlayers.map((player, idx) => (
            <div
              key={idx}
              {...stylex.props(styles.playerRow)}
            >
              <PlayerAvatar
                name={player.name}
                isBot={player.is_bot}
                isThinking={player.isThinking}
                size="medium"
              />
              <span {...stylex.props(styles.playerLabel)}>{player.name}</span>
            </div>
          ))}
        </div>

        <div {...stylex.props(styles.sizeSection)}>
          <h3 {...stylex.props(styles.sectionTitle)}>Large Size</h3>
          {testPlayers.map((player, idx) => (
            <div
              key={idx}
              {...stylex.props(styles.playerRow)}
            >
              <PlayerAvatar
                name={player.name}
                isBot={player.is_bot}
                isThinking={player.isThinking}
                size="large"
              />
              <span {...stylex.props(styles.playerLabel)}>{player.name}</span>
            </div>
          ))}
        </div>
      </div>

      <div {...stylex.props(styles.statesSection)}>
        <h3 {...stylex.props(styles.sectionTitle)}>States</h3>
        <div {...stylex.props(styles.statesGrid)}>
          <div {...stylex.props(styles.stateItem)}>
            <PlayerAvatar
              name="Active Bot"
              isBot={true}
              className="active"
              size="large"
            />
            <span {...stylex.props(styles.playerLabel)}>Active State</span>
          </div>
          <div {...stylex.props(styles.stateItem)}>
            <PlayerAvatar
              name="Winner Bot"
              isBot={true}
              className="winner"
              size="large"
            />
            <span {...stylex.props(styles.playerLabel)}>Winner State</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlayerAvatarTest;