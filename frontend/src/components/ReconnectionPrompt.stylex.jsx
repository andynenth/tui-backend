// frontend/src/components/ReconnectionPrompt.stylex.jsx

import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, layout, shadows, motion } from '../design-system/tokens.stylex';
import { formatSessionInfo } from '../utils/sessionStorage';

// Animations
const spin = stylex.keyframes({
  '0%': {
    transform: 'rotate(0deg)',
  },
  '100%': {
    transform: 'rotate(360deg)',
  },
});

// ReconnectionPrompt styles
const styles = stylex.create({
  overlay: {
    position: 'fixed',
    inset: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 100,
    padding: spacing.md,
  },
  
  prompt: {
    backgroundColor: colors.white,
    borderRadius: layout.radiusLg,
    padding: spacing.xl,
    maxWidth: '450px',
    width: '100%',
    boxShadow: shadows.xl,
  },
  
  icon: {
    fontSize: '48px',
    textAlign: 'center',
    marginBottom: spacing.md,
  },
  
  title: {
    fontSize: typography.text2xl,
    fontWeight: typography.weightBold,
    color: colors.gray900,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  
  message: {
    fontSize: typography.textBase,
    color: colors.gray600,
    marginBottom: spacing.lg,
    textAlign: 'center',
  },
  
  info: {
    backgroundColor: colors.gray50,
    borderRadius: layout.radiusMd,
    padding: spacing.md,
    marginBottom: spacing.lg,
  },
  
  infoItem: {
    display: 'flex',
    justifyContent: 'space-between',
    paddingTop: spacing.xs,
    paddingBottom: spacing.xs,
  },
  
  infoLabel: {
    fontSize: typography.textSm,
    color: colors.gray500,
    fontWeight: typography.weightMedium,
  },
  
  infoValue: {
    fontSize: typography.textSm,
    color: colors.gray900,
    fontWeight: typography.weightMedium,
  },
  
  infoValueRecent: {
    color: colors.successDark,
  },
  
  warning: {
    fontSize: typography.textSm,
    color: colors.warningDark,
    textAlign: 'center',
    marginTop: spacing.md,
    fontWeight: typography.weightMedium,
  },
  
  error: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: '#fef2f2',
    border: `1px solid ${colors.danger}`,
    borderRadius: layout.radiusMd,
    padding: spacing.md,
    marginBottom: spacing.lg,
  },
  
  errorIcon: {
    fontSize: typography.textLg,
  },
  
  errorText: {
    fontSize: typography.textSm,
    color: colors.dangerDark,
  },
  
  actions: {
    display: 'flex',
    gap: spacing.md,
    marginTop: spacing.lg,
  },
  
  button: {
    flex: 1,
    padding: `${spacing.sm} ${spacing.lg}`,
    borderRadius: layout.radiusMd,
    fontSize: typography.textBase,
    fontWeight: typography.weightMedium,
    border: 'none',
    cursor: 'pointer',
    transition: `all ${motion.durationFast} ${motion.easeInOut}`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
  },
  
  buttonPrimary: {
    backgroundColor: colors.primary,
    color: colors.white,
    ':hover:not(:disabled)': {
      backgroundColor: colors.primaryDark,
    },
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
    },
  },
  
  buttonSecondary: {
    backgroundColor: colors.gray200,
    color: colors.gray700,
    ':hover:not(:disabled)': {
      backgroundColor: colors.gray300,
    },
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
    },
  },
  
  spinner: {
    display: 'inline-block',
    width: '16px',
    height: '16px',
    border: '2px solid rgba(255, 255, 255, 0.3)',
    borderTopColor: colors.white,
    borderRadius: '50%',
    animation: `${spin} 0.6s linear infinite`,
  },
  
  note: {
    fontSize: typography.textXs,
    color: colors.gray500,
    textAlign: 'center',
    marginTop: spacing.md,
    fontStyle: 'italic',
  },
});

/**
 * ReconnectionPrompt Component
 *
 * Displays a prompt for reconnecting to a previous game session
 * Handles both reconnection and duplicate tab scenarios
 */
const ReconnectionPrompt = ({
  sessionInfo,
  onReconnect,
  onJoinAsNew,
  isReconnecting,
  isDuplicateTab,
  error,
  className = '',
}) => {
  const formattedInfo = formatSessionInfo();

  if (!formattedInfo) return null;

  // Apply overlay styles
  const overlayProps = stylex.props(styles.overlay);
  
  // During migration, allow combining with existing CSS classes
  const combinedOverlayProps = className 
    ? { ...overlayProps, className: `${overlayProps.className || ''} ${className}`.trim() }
    : overlayProps;

  return (
    <div {...combinedOverlayProps}>
      <div {...stylex.props(styles.prompt)}>
        <div {...stylex.props(styles.icon)}>{isDuplicateTab ? '⚠️' : '🎮'}</div>

        {isDuplicateTab ? (
          <>
            <h2 {...stylex.props(styles.title)}>Game Already Open</h2>
            <p {...stylex.props(styles.message)}>
              You already have this game open in another tab.
            </p>
            <div {...stylex.props(styles.info)}>
              <div {...stylex.props(styles.infoItem)}>
                <span {...stylex.props(styles.infoLabel)}>Room:</span>
                <span {...stylex.props(styles.infoValue)}>{formattedInfo.roomId}</span>
              </div>
              <div {...stylex.props(styles.infoItem)}>
                <span {...stylex.props(styles.infoLabel)}>Player:</span>
                <span {...stylex.props(styles.infoValue)}>{formattedInfo.playerName}</span>
              </div>
            </div>
            <p {...stylex.props(styles.warning)}>
              Close this tab or switch to the existing game tab.
            </p>
            <div {...stylex.props(styles.actions)}>
              <button 
                {...stylex.props(styles.button, styles.buttonSecondary)} 
                onClick={onJoinAsNew}
              >
                Join as New Player
              </button>
            </div>
          </>
        ) : (
          <>
            <h2 {...stylex.props(styles.title)}>Welcome Back!</h2>
            <p {...stylex.props(styles.message)}>
              We found your game session. Would you like to rejoin?
            </p>

            <div {...stylex.props(styles.info)}>
              <div {...stylex.props(styles.infoItem)}>
                <span {...stylex.props(styles.infoLabel)}>Room:</span>
                <span {...stylex.props(styles.infoValue)}>{formattedInfo.roomId}</span>
              </div>
              <div {...stylex.props(styles.infoItem)}>
                <span {...stylex.props(styles.infoLabel)}>Player:</span>
                <span {...stylex.props(styles.infoValue)}>{formattedInfo.playerName}</span>
              </div>
              {formattedInfo.gamePhase && (
                <div {...stylex.props(styles.infoItem)}>
                  <span {...stylex.props(styles.infoLabel)}>Phase:</span>
                  <span {...stylex.props(styles.infoValue)}>{formattedInfo.gamePhase}</span>
                </div>
              )}
              <div {...stylex.props(styles.infoItem)}>
                <span {...stylex.props(styles.infoLabel)}>Last seen:</span>
                <span
                  {...stylex.props(
                    styles.infoValue,
                    formattedInfo.isRecent && styles.infoValueRecent
                  )}
                >
                  {formattedInfo.lastSeenText}
                </span>
              </div>
            </div>

            {error && (
              <div {...stylex.props(styles.error)}>
                <span {...stylex.props(styles.errorIcon)}>❌</span>
                <span {...stylex.props(styles.errorText)}>{error}</span>
              </div>
            )}

            <div {...stylex.props(styles.actions)}>
              <button
                {...stylex.props(styles.button, styles.buttonPrimary)}
                onClick={onReconnect}
                disabled={isReconnecting}
              >
                {isReconnecting ? (
                  <>
                    <span {...stylex.props(styles.spinner)} />
                    Reconnecting...
                  </>
                ) : (
                  'Rejoin Game'
                )}
              </button>
              <button
                {...stylex.props(styles.button, styles.buttonSecondary)}
                onClick={onJoinAsNew}
                disabled={isReconnecting}
              >
                Join as New Player
              </button>
            </div>

            <p {...stylex.props(styles.note)}>
              Your AI has been playing for you while you were away.
            </p>
          </>
        )}
      </div>
    </div>
  );
};

ReconnectionPrompt.propTypes = {
  sessionInfo: PropTypes.object,
  onReconnect: PropTypes.func.isRequired,
  onJoinAsNew: PropTypes.func.isRequired,
  isReconnecting: PropTypes.bool,
  isDuplicateTab: PropTypes.bool,
  error: PropTypes.string,
  className: PropTypes.string,
};

export default ReconnectionPrompt;